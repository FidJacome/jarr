import logging
import tomllib
from pathlib import Path

import tomli_w

from .constants import CONFIG_DIR

CONFIG_FILE = Path(CONFIG_DIR / "config.toml")

logger = logging.getLogger(__name__)


def load_config() -> dict:
    try:
        with open(CONFIG_FILE, "rb") as f:
            current_settings = tomllib.load(f)
            return current_settings
    except FileNotFoundError:
        logger.info("Couldn't find config.toml")
        return {}
    except tomllib.TOMLDecodeError as e:
        logger.error("Can't load configuration file: %s", e)
        return {}
    except OSError as e:
        logger.error("Can't load configuration file: %s", e)
        return {}


def save_config(config: dict) -> bool:
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "wb") as f:
            tomli_w.dump(config, f)
        CONFIG_FILE.chmod(0o600)
        return True
    except OSError as e:
        logger.error("Couldn't write to config.toml: %s", e)
        return False


def set_config(config: dict, *keys: str, value) -> None:
    """Changes the dictionary directly"""
    if len(keys) == 0:
        raise ValueError("The function needs at least one key to change.")

    current_pos: dict = config

    for key in keys[:-1]:
        current_pos.setdefault(key, {})
        current_pos = current_pos[key]

    current_pos[keys[-1]] = value

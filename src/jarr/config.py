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

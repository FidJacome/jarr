import logging

from ..config import CONFIG_FILE, load_config, save_config, set_config
from ..prompts import ask_token

logger = logging.getLogger(__name__)


def cmd_config_tkn() -> int:
    config = load_config()
    token = ask_token()
    if not token:
        logger.error("Can't save empty token.")
        return 1
    set_config(config, "tmdb", "token", value=token)
    return 0 if save_config(config) else 1


def cmd_config_dir(args) -> int:
    config = load_config()
    set_config(config, "default_dir", value=args.new_dir)
    return 0 if save_config(config) else 1


def cmd_config_path() -> int:
    print(f"Your configurations file is located in {CONFIG_FILE}")
    return 0

import logging

from ..config import CONFIG_FILE, load_config, save_config, set_config
from ..prompts import ask, ask_token
from ..style import dim

logger = logging.getLogger(__name__)

# Any setting whose name contains one of these words is masked by `config show`.
SECRET_WORDS = ("token", "secret", "password", "key")


def is_secret(key: str) -> bool:
    return any(word in key.lower() for word in SECRET_WORDS)


def mask(value) -> str:
    """Show only the last 4 characters, e.g. ****3456."""
    text = str(value)
    return "****" + text[-4:] if len(text) > 8 else "****"


def cmd_config_tkn(args) -> int:
    config = load_config()
    token = ask_token()
    if not token:
        return 1
    set_config(config, "tmdb", "token", value=token)
    if save_config(config):
        print("Token saved successfully")
        return 0
    return 1


def cmd_config_dir(args) -> int:
    config = load_config()
    new_dir = args.new_dir.expanduser().resolve()
    if new_dir.is_file():
        logger.error("Can't set file as default directory.")
        return 1
    if not new_dir.exists():
        print(f"{new_dir} doesn't exist.")
        if ask(f"Do you wanna create it? {dim('[y/N]')} ", ["y", "n"], "n") == "y":
            try:
                new_dir.mkdir(parents=True)
            except OSError as e:
                logger.error("Directory creation failed: %s", e)
                return 1
        else:
            raise KeyboardInterrupt
    set_config(config, "default_dir", value=new_dir.as_posix())
    if save_config(config):
        print(f"{new_dir} saved to config successfully.")
        return 0
    return 1


def cmd_config_path(args) -> int:
    print(f"Your configurations file is located in {CONFIG_FILE}")
    return 0


def cmd_config_show(args) -> int:
    config = load_config()
    if not config:
        print(f"No settings saved yet ({CONFIG_FILE} doesn't exist or is empty).")
        return 0

    def print_dict(dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                print_dict(value)
            elif is_secret(key):
                print(f"{key}: {mask(value)}")
            else:
                print(f"{key}: {value}")

    print_dict(config)
    return 0

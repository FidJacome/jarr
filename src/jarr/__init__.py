import logging

from jarr.constants import LOG_FILE

from .cli import parse_args
from .config import load_config, save_config, set_config
from .style import red

logger = logging.getLogger(__name__)


def main() -> int:
    args = parse_args()
    log_file = LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file = logging.FileHandler(log_file)
    log_file.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(f"{red('Error:')} %(message)s"))
    console.setLevel(logging.ERROR)
    logging.basicConfig(level=logging.INFO, handlers=[log_file, console])

    try:
        return args.func(args)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception:
        logger.exception("Unexpected error.")
        return 1

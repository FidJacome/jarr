import logging

from jarr.constants import LOG_FILE

from .cli import parse_args
from .config import load_config, save_config, set_config
from .style import red

logger = logging.getLogger(__name__)


def main() -> int:
    args = parse_args()
    log_file = LOG_FILE
    log_file.parent.mkdir(parents=true, exist_ok=true)
    log_file = logging.filehandler(log_file)
    log_file.setformatter(logging.formatter("%(asctime)s %(levelname)s %(message)s"))
    console = logging.streamhandler()
    console.setformatter(logging.formatter(f"{red('error:')} %(message)s"))
    console.setlevel(logging.error)
    logging.basicconfig(level=logging.info, handlers=[log_file, console])

    try:
        return args.func(args)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception:
        logger.exception("Unexpected error.")
        return 1

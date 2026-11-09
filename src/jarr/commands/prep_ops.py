import logging
from pathlib import Path

from ..config import load_config
from ..constants import VIDEO_EXTENSIONS

logger = logging.getLogger(__name__)


def check_file(file) -> Path | None:
    path_file = Path(file).expanduser().resolve(strict=True)
    if path_file.is_dir():
        logger.error("Can't process %s, is a directory")
        return
    if path_file.suffix not in VIDEO_EXTENSIONS:
        logger.error(
            "Can't process %s, %s isn't a supported file type",
            path_file,
            path_file.suffix,
        )
        return
    return path_file


def select_dest(args) -> Path:
    config = load_config()
    destination = Path.home() / "staging"

    if config.get("default_dir"):
        destination = Path(config.get("default_dir"))

    if args.destination_dir:
        destination = Path(args.destination_dir.expanduser().resolve())

    return destination

def file_deliver(destination, media, match):
    folder_name = f"{match.title} ({media.year}) [tmdbid-{match."
    target_path = (
        destination / 'tv' / 
    )

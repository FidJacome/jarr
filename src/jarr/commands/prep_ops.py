import logging
from os.path import exists
from pathlib import Path
import shutil

from ..style import short_path, yellow, dim, green
from ..prompts import ask
from ..config import load_config
from ..constants import VIDEO_EXTENSIONS

logger = logging.getLogger(__name__)


def check_file(file) -> Path | None:
    try:
        path_file = Path(file).expanduser().resolve(strict=True)
    except OSError as e:
        logger.error("Can't process %s: %s", file, e)
        return
    if path_file.is_dir():
        logger.error("Can't process %s, is a directory", path_file)
        return
    if path_file.suffix.lower() not in VIDEO_EXTENSIONS:
        logger.error(
            "Can't process %s, %s isn't a supported file type",
            path_file,
            path_file.suffix,
        )
        return
    return path_file


def select_dest(args_dir: Path, config) -> Path:
    destination = Path.home() / "staging"

    if config.get("default_dir"):
        destination = Path(config.get("default_dir"))

    if args_dir is not None:
        destination = Path(args_dir).expanduser().resolve()

    # Remember to catch a possible NotADirectoryError error in the dispatcher.
    destination.mkdir(parents=True, exist_ok=True)

    return destination


def path_constructor(destination, media, match, prompt: bool) -> Path | None:
    title = match.title.replace("/", "-")
    folder_name = f"{title} ({match.year}) [tmdbid-{match.id}]"
    target_path = (
        destination / "tv" / folder_name / f"Season {media.season:02d}"
        if media.kind == "episode"
        else destination / "movie" / folder_name
    )
    new_file_path = (
        target_path
        / f"{title} S{media.season:02d}E{media.episode:02d}{media.extension}"
        if media.kind == "episode"
        else target_path / f"{title} ({match.year}){media.extension}"
    )
    if new_file_path.exists() and prompt:
        print(yellow(f"{short_path(new_file_path)} already exists."))
        if ask(f"Overwrite it? {dim('[y/N]')} ", ["y", "n"], "n") == "n":
            print("Aborted, nothing was modified.")
            return
    return new_file_path


def deliver_file(old, new, copy: bool):
    new.parents[0].mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copy2(old, new)
        logger.info("Copied %s -> %s", old, new)
    else:
        shutil.move(old, new)
        logger.info("Moved %s -> %s", old, new)
    print(f"{green('✓')} {short_path(new)}")

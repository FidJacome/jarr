import logging
import shutil
from pathlib import Path

from ..constants import VIDEO_EXTENSIONS
from ..media import Media
from ..prompts import ask
from ..style import dim, green, short_path, yellow
from ..tmdbmatch import TMDBMatch

logger = logging.getLogger(__name__)


class UnsupportedFileError(ValueError):
    def __init__(self, path, reason):
        self.path = path
        super().__init__(f"Can't process {path}: {reason}")


def check_file(file) -> Path:
    path_file = Path(file).expanduser().resolve(strict=True)
    if path_file.suffix.lower() not in VIDEO_EXTENSIONS:
        raise UnsupportedFileError(path_file, "File type not supported.")
    if path_file.is_file():
        return path_file
    raise UnsupportedFileError(path_file, "Not a file.")


def select_dest(args_dir: Path, config) -> Path:
    destination = Path.home() / "staging"

    if config.get("default_dir"):
        destination = Path(config.get("default_dir"))

    if args_dir is not None:
        destination = Path(args_dir).expanduser().resolve()

    # Remember to catch a possible NotADirectoryError error in the dispatcher.
    destination.mkdir(parents=True, exist_ok=True)

    return destination


def media_check(media: Media) -> bool:
    if not media.title:
        return False
    if media.kind == "episode" and not (
        isinstance(media.episode, int) and isinstance(media.season, int)
    ):
        return False
    return True


def path_constructor(
    destination: Path, media: Media, match: TMDBMatch, prompt: bool = True
) -> Path | None:
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

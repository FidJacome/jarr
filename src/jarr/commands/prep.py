import logging
import os
import shutil
from pathlib import Path

from ..config import load_config, save_config, set_config
from ..constants import VIDEO_EXTENSIONS
from ..media import Media
from ..query_ops import NoMatchError, TMDB_query, TMDB_select, TMDBError
from ..style import bold, dim, green, short_path, yellow
from ..prompts import ask, ask_token

logger = logging.getLogger(__name__)


class UnsupportedFileError(ValueError):
    def __init__(self, path):
        self.path = path
        super().__init__(f"{path.suffix} is not a supported file type: {path}")


def cmd_prep(args) -> int:
    config = load_config()
    try:
        # Checks if args.file is a file, is a supported video type and it exists.
        try:
            args.file.resolve(strict=True)
            if args.file.is_dir():
                logger.error("Directory was passed, you must provide a file.")
                return 1
        except OSError as e:
            logger.error("Can't use %s file: %s", args.file, e)
            return 1

        if args.file.suffix.lower() not in VIDEO_EXTENSIONS:
            raise UnsupportedFileError(args.file)

        # TMDB Token request: ask if none is saved
        token = os.getenv("TMDB_TOKEN") or config.get("tmdb", {}).get("token")
        if not token:
            token = ask_token()
            if not token:
                return 1
            set_config(config, "tmdb", "token", value=token)
            if not save_config(config):
                logger.error("Couldn't save token.")

        # Destination path selection: typed folder > saved default > ~/staging
        destination = Path.home() / "staging"

        # saved default from config.toml
        if config.get("default_dir"):
            destination = Path(config.get("default_dir"))

        # `jarr <video> <folder>`: typed folder wins
        if args.destination_dir:
            destination = args.destination_dir.expanduser()

        # Check if destination is valid
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Can't use %s as destination directory: %s", destination, e)
            return 1

        try:
            file_path: "Path" = Path(args.file)
            file_path = file_path.resolve(strict=True)
        except FileNotFoundError:
            logger.error("File %s not found.", file_path)
            return 1
        except OSError as e:
            logger.error("Can't read %s: %s", file_path, e)
            return 1

        try:
            media: "Media" = Media.from_path(file_path)
        except KeyError as e:
            logger.error("Failed to identify: %s", e)
            return 1

        if media.kind == "episode" and not (
            isinstance(media.season, int) and isinstance(media.episode, int)
        ):
            logger.error("Couldn't detect season and episode numbers for %s", file_path)
            return 1

        year = f" ({media.year})" if media.year else ""
        kind = (
            f"TV · S{media.season:02d}E{media.episode:02d}"
            if media.kind == "episode"
            else "Movie"
        )
        print(dim(file_path.name))
        print(f"{bold(media.title)}{year}  {dim(kind)}")
        if media.year:
            answer = ask(
                f"Search TMDB? {dim('[Y]es / [l]oose (ignore year) / [n]o')} ",
                ["y", "l", "n"],
                "y",
            )
        else:
            answer = ask(f"Search TMDB? {dim('[Y]es / [n]o')} ", ["y", "n"], "y")
        if answer == "n":
            raise KeyboardInterrupt

        try:
            loose = answer == "l"
            print(dim("Searching TMDB..."))
            tmdb_results = TMDB_query(media, loose, token)
            option = TMDB_select(tmdb_results, (media.year and not loose))
            if option == "l":
                print(dim("Searching TMDB, ignoring the year..."))
                tmdb_results = TMDB_query(media, True, token)
                option = TMDB_select(tmdb_results)
            if option == 0:
                raise KeyboardInterrupt
        except TMDBError as e:
            logger.error(e)
            return 1
        except NoMatchError as e:
            logger.error(e)
            return 1

        selection = tmdb_results[option - 1]
        title = selection.title.replace("/", "-")
        folder_name = f"{title} ({selection.year}) [tmdbid-{selection.id}]"

        if media.kind == "movie":
            target_path = destination / "movie" / folder_name
            new_file_path = (
                target_path / f"{title} ({selection.year}){file_path.suffix}"
            )
        elif media.kind == "episode":
            target_path = (
                destination / "tv" / folder_name / f"Season {media.season:02d}"
            )
            new_file_path = (
                target_path
                / f"{title} S{media.season:02d}E{media.episode:02d}{file_path.suffix}"
            )

        if new_file_path.exists():
            print(yellow(f"{short_path(new_file_path)} already exists."))
            if ask(f"Overwrite it? {dim('[y/N]')} ", ["y", "n"], "n") == "n":
                print("Aborted, nothing was moved.")
                return 1

        target_path.mkdir(parents=True, exist_ok=True)
        shutil.move(file_path, new_file_path)
        logger.info("Moved %s -> %s", file_path, new_file_path)
        print(f"{green('✓')} {short_path(new_file_path)}")
        return 0
    except UnsupportedFileError:
        return 1

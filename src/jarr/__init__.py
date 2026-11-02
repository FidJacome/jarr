import getpass
import logging
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv, set_key

from .cli import parse_args
from .constants import ENV_PATH, VIDEO_EXTENSIONS
from .media import Media
from .query_ops import NoMatchError, TMDB_query, TMDB_select, TMDBError
from .style import bold, dim, green, red, short_path, yellow

logger = logging.getLogger(__name__)

LOG_FILE = (
    Path(os.getenv("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    / "jarr"
    / "jarr.log"
)


class UnsupportedFileError(ValueError):
    def __init__(self, path):
        self.path = path
        super().__init__(f"{path.suffix} is not a supported file type: {path}")


def ask(prompt: str, choices: list[str], default: str) -> str:
    while True:
        answer = input(prompt).strip().lower() or default
        if answer in choices:
            return answer
        print(yellow(f"Please answer one of: {', '.join(choices)}"))


def save_setting(key: str, value: str) -> bool:
    try:
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        set_key(ENV_PATH, key, value)
        print(f"Setting {key} set successfully.")
        return True
    except OSError as e:
        logger.error("Couldn't save %s to %s: %s", key, ENV_PATH, e)
        return False


def main() -> int:
    args = parse_args()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_file = logging.FileHandler(LOG_FILE)
    log_file.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(f"{red('Error:')} %(message)s"))
    console.setLevel(logging.ERROR)
    logging.basicConfig(level=logging.INFO, handlers=[log_file, console])

    try:
        load_dotenv(ENV_PATH)

        args.file = args.file.expanduser()
        if args.default and args.file.is_dir() and not args.destination_path:
            if save_setting("DEFAULT_DIR", args.file.resolve().as_posix()):
                return 0
            logger.error("Failed to set default directory.")
            return 1

        if args.default and args.file.is_file() and not args.destination_path:
            logger.error("Default directory cannot be empty.")
            return 1

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

        # TMDB Token request
        token = os.getenv("TMDB_TOKEN")
        if not token or args.set_token:
            token = getpass.getpass(
                dim("Please enter your TMDB API Read Access Token: ")
            ).strip()
            if not token:
                logger.error("No token entered")
                return 1
            save_setting("TMDB_TOKEN", token)

        # Destination path selection

        destination = Path.home() / "staging"

        if os.getenv("DEFAULT_DIR"):
            destination = Path(os.getenv("DEFAULT_DIR"))

        if args.destination_path:
            destination = args.destination_path.expanduser()

        # Check if destination is valid
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Can't use %s as destination directory: %s", destination, e)
            return 1

        if args.default and args.destination_path:
            save_setting("DEFAULT_DIR", destination.resolve().as_posix())

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
        answer = ask(
            f"Search TMDB? {dim('[Y]es / [l]oose (ignore year) / [n]o')} ",
            ["y", "l", "n"],
            "y",
        )
        if answer == "n":
            raise KeyboardInterrupt

        try:
            print(dim("Searching TMDB..."))
            tmdb_results = TMDB_query(media, answer == "l", token)
            option = TMDB_select(tmdb_results)
            while option == 0:
                print(dim("Searching TMDB, ignoring the year..."))
                tmdb_results = TMDB_query(media, True, token)
                option = TMDB_select(tmdb_results)
            if option == -1:
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
    except UnsupportedFileError as e:
        logger.error("%s", e)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception:
        logger.exception("Unexpected error.")
        return 1

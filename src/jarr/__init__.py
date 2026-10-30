import logging
import os
import shutil
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
from .constants import VIDEO_EXTENSIONS, TMDB_URL, SEARCH_ENDPOINTS
from .media import Media
from .tmdbmatch import TMDBMatch
from .query_ops import TMDB_query, TMDB_select, TMDBError, NoMatchError
from .style import bold, dim, red, green, yellow, short_path
logger = logging.getLogger(__name__)

USAGE = "Usage: jarr <video file>"
LOG_FILE = Path(os.getenv("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "jarr" / "jarr.log"

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

def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        return 2

    try:
        load_dotenv()
        token = os.getenv("TMDB_TOKEN")
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log_file = logging.FileHandler(LOG_FILE)
        log_file.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(f"{red('Error:')} %(message)s"))
        console.setLevel(logging.ERROR)
        logging.basicConfig(level=logging.INFO, handlers=[log_file, console])

        try:
            file_path: "Path" = Path(sys.argv[1])
            if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
                raise UnsupportedFileError(file_path)
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

        if media.kind == "episode" and not (isinstance(media.season, int) and isinstance(media.episode, int)):
            logger.error("Couldn't detect season and episode numbers for %s", file_path)
            return 1

        year = f" ({media.year})" if media.year else ""
        kind = f"TV · S{media.season:02d}E{media.episode:02d}" if media.kind == "episode" else "Movie"
        print(dim(file_path.name))
        print(f"{bold(media.title)}{year}  {dim(kind)}")
        answer = ask(f"Search TMDB? {dim('[Y]es / [l]oose (ignore year) / [n]o')} ", ["y", "l", "n"], "y")
        if answer == "n": raise KeyboardInterrupt

        try:
            print(dim("Searching TMDB..."))
            tmdb_results = TMDB_query(media, answer == "l", token)
            option = TMDB_select(tmdb_results)
            while option == 0:
                print(dim("Searching TMDB, ignoring the year..."))
                tmdb_results = TMDB_query(media, True, token)
                option = TMDB_select(tmdb_results)
            if option == -1: raise KeyboardInterrupt
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
            target_path = file_path.home() / "staging" / "movie" / folder_name
            new_file_path = target_path / f"{title} ({selection.year}){file_path.suffix}"
        elif media.kind == "episode":
            target_path = file_path.home() / "staging" / "tv" / folder_name / f"Season {media.season:02d}"
            new_file_path = target_path / f"{title} S{media.season:02d}E{media.episode:02d}{file_path.suffix}"

        if new_file_path.exists():
            print(yellow(f"{short_path(new_file_path)} already exists."))
            if ask(f"Overwrite it? {dim('[y/N]')} ", ["y", "n"], "n") == "n":
                print("Aborted, nothing was moved.")
                return 1

        target_path.mkdir(parents=True, exist_ok=True)
        shutil.move(file_path, new_file_path)
        logger.info("Moved %s -> %s", file_path, new_file_path)
        print(f"{green('✓')} {short_path(new_file_path)}")
    except UnsupportedFileError as e:
        logger.error("%s", e)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception:
        logger.exception("Unexpected error.")
        return 1

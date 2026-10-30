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
logger = logging.getLogger(__name__)

class UnsupportedFileError(ValueError):
    def __init__(self, path):
        self.path = path
        super().__init__(f"{path.suffix} is not a supported file type: {path}")

def main() -> int:
    try:
        load_dotenv()
        token = os.getenv("TMDB_TOKEN")
        logging.basicConfig(filename='jarr.log', level=logging.INFO)

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

        try:
            print(f"Looking for {media.title} in TMDB")
            tmdb_results = TMDB_query(media, False, token)
            print("If no option matches your media, input 0 to perform a \"loose\" query")
            option = TMDB_select(tmdb_results)
            while option == 0:
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
            target_path.mkdir(parents=True, exist_ok=True)
            new_file_path = shutil.move(file_path, target_path / f"{title} ({selection.year}){file_path.suffix}")
        elif media.kind == "episode":
            target_path = file_path.home() / "staging" / "tv" / folder_name / f"Season {media.season:02d}"
            target_path.mkdir(parents=True, exist_ok=True)
            new_file_path = shutil.move(file_path, target_path / f"{title} S{media.season:02d}E{media.episode:02d}{file_path.suffix}")
    except UnsupportedFileError as e:
        logger.error("%s", e)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception:
        logger.exception("Unexpected error.")
        return 1

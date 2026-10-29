import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from .constatns import VIDEO_EXTENSIONS, TMDB_URL, SEARCH_ENDPOINTS
from .media import Media
from .tmdbmatch import TMDBMatch
logger = logging.getLogger(__name__)

class UnsupportedFileError(ValueError):
    def __init__(self, path):
        self.path = path
        super().__init__(f"{path.suffix} is not a supported video type: {path}")

def main() -> int:
    load_dotenv()
    logging.basicConfig(filename='jarr.log', level=logging.INFO)
    try:
        file_path = Path(sys.argv[1])
        if file_path.suffix not in VIDEO_EXTENSIONS:
            raise UnsupportedFileError(file_path)
        file_path = file_path.resolve(strict=True)
    except FileNotFoundError:
        logger.error("File %s not found.", file_path)
        return 1
    except OSError as e:
        logger.error("Can't read %s: %s", file_path, e)
        return 1
    try:
        media = Media(file_path)
    except KeyError as e:
        logger.error("Failed to identify: %s", e)
        return 1
    try:
        url = f"{TMDB_URL}{SEARCH_ENDPOINTS[media.type]}/"
        response = requests.get(url, params={"query": media.title, "primary_release_year": media.year}).json()
        data = response.json()
        query_results = []
        for result in data.get("results")[:3]:
            query_results.append(TMDBMatch(result))

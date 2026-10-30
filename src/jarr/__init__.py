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
    try:
        load_dotenv()
        logging.basicConfig(filename='jarr.log', level=logging.INFO)

        try:
            file_path: "Path" = Path(sys.argv[1])
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
            media: "Media" = Media(file_path)
        except KeyError as e:
            logger.error("Failed to identify: %s", e)
            return 1

        try:
            url: str = f"{TMDB_URL}{SEARCH_ENDPOINTS[media.type]}/"
            response = requests.get(url, params={"query": media.title, "primary_release_year": media.year}, timeout=5).json()
            data = response.json()
            query_results: list["TMDBMatch"] = []
            for result in data.get("results")[:3]:
                query_results.append(TMDBMatch(result))
        except ConnectionError as e:
            logger.error("No internet connection: %s", e)
            return 1
        except ConnectTimeout as e:
            logger.error("Couldn't connect to TMDB: %s", e)
            return 1
        except ReadTimeout as e:
            logger.error("Response took to long: %s", e)
            return 1
        except HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Error %s: Check that your TMDB token is correct", e.response.status_code)
                return 1
            logger.error("Error %s: %s", e.response.status_code, e.response.reason)
            return 1

        print("Query returned these top matches:")
        for i, match in enumerate(query_results, start=1):
            print(f"{i}. {match}")

        while True:
            raw = input("Choose an option: ").strip()
            try:
                option = int(raw)
            except ValueError:
                print("Please enter a number.")
                continue
            if 1 <= option <= len(query_results):
                break
            print(f"Choose a number between 1 and {len(query_results)}.")

        selection = query_results[option - 1]
    except UnsupportedFileError as e:
        logger.error("%s", e)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception:
        logger.exception("Unexpectred error.")
        return 1

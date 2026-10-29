import logging
from pathlib import Path
from .parser import parse
from dotenv import load_dotenv
logger = logging.getLogger(__name__)

class UnsupportedFileError(ValueError):
    def __init__(self, path):
        self.path = path
        super().__init__(f"{path.suffix} is not a supported video type: {path}")

def main() -> int:
    load_dotenv()
    logging.basicConfig(filename='jellyfin_companion.log', level=logging.INFO)
    try:
        file_path = Path(sys.argv[1])
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
    

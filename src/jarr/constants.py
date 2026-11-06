import os
from pathlib import Path

VIDEO_EXTENSIONS = [".mkv", ".mp4", ".avi", ".m4v", ".mov", ".webm"]
TMDB_URL = "https://api.themoviedb.org/3/search/"
SEARCH_ENDPOINTS = {
    "movie": "movie",
    "episode": "tv",
}
LOG_FILE = (
    Path(os.getenv("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    / "jarr"
    / "jarr.log"
)
CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config") / "jarr"

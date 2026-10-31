from pathlib import Path

VIDEO_EXTENSIONS = [".mkv", ".mp4", ".avi", ".m4v", ".mov", ".webm"]
TMDB_URL = "https://api.themoviedb.org/3/search/"
ENV_PATH = Path(Path.home() / ".config" / "jarr" / ".env")
SEARCH_ENDPOINTS = {
    "movie": "movie",
    "episode": "tv",
}
USAGE = """Usage: jarr [OPTION] <video file>

OPTIONS:
    -h --help      : See this page
    -t --set-token : Set or change your TMDB API Read Access Token"""

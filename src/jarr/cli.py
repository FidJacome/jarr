import argparse
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="jarr", description="The Jellyfin companion CLI tool"
    )
    parser.add_argument("file", help="Video file to identify and rename")
    parser.add_argument(
        "-t",
        "--set-token",
        action="store_true",
        help="Set or change your TMDB API Read Access Token",
    )
    parser.add_argument(
        "-d",
        "--default",
        action="store_true",
        help="Set or change the default target path of output file",
    )
    parser.add_argument(
        "destination_path",
        nargs="?",
        type=Path,
        help="Change or set the directory where the tool stores the renamed file",
    )

    return parser.parse_args(argv)

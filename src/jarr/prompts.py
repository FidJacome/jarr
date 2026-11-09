import getpass
import logging

from .media import Media
from .style import dim, yellow

logger = logging.getLogger(__name__)


def ask(prompt: str, choices: list[str], default="") -> str:
    while True:
        answer = input(prompt).strip().lower() or default
        if answer in choices:
            return answer
        print(yellow(f"Please answer one of: {', '.join(choices)}"))


def ask_token() -> str | None:
    token = getpass.getpass(
        dim("Please enter your TMDB API Read Access Token: ")
    ).strip()
    if not token:
        logger.error("No token entered")
        return None
    return token


def manual_edit(media: Media) -> Media:
    new_media = Media(
        media.path,
        input("Enter media title: "),
        input("Enter media release year: "),
        (
            "movie"
            if ask(f"Enter media kind {dim('[m]ovie / [t]v ')}", ["m", "t"]) == "m"
            else "episode"
        ),
        media.extension,
    )
    if new_media.kind == "episode":
        new_media.episode = input("Enter episode #: ")
        new_media.season = input("Enter season #: ")
    return new_media

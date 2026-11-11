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


def ask_token() -> str:
    while True:
        token = getpass.getpass(
            dim("Please enter your TMDB API Read Access Token: ")
        ).strip()
        if token:
            return token
        print("Please enter a token to continue.")


def manual_edit(media: Media) -> Media:
    new_media = Media(
        media.path,
        input(f"Enter media title ({media.title}): ") or media.title,
        input(f"Enter media release year ({media.year}): ") or media.year,
        (
            "movie"
            if ask(f"Enter media kind {dim('[m]ovie / [t]v ')}", ["m", "t"]) == "m"
            else "episode"
        ),
        media.extension,
    )
    if new_media.kind == "episode":
        new_media.episode = (
            input(f"Enter episode #({media.episode}): ") or media.episode
        )
        new_media.season = input(f"Enter season #({media.season}): ") or media.episode
    return new_media

import getpass
import logging

from .style import dim, yellow

logger = logging.getLogger(__name__)


def ask(prompt: str, choices: list[str], default: str) -> str:
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

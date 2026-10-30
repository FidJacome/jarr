import os
import sys
from pathlib import Path

USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ

def _wrap(code: str):
    def style(text) -> str:
        return f"\033[{code}m{text}\033[0m" if USE_COLOR else str(text)
    return style

bold = _wrap("1")
dim = _wrap("2")
red = _wrap("31")
green = _wrap("32")
yellow = _wrap("33")
cyan = _wrap("36")

def short_path(path) -> str:
    path = Path(path)
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)

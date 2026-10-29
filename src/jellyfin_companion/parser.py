from guessit import guessit
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def identify(path: "Path"):
    abs_path: "Path" = path.resolve(strict=True)
    logger.info("Absolute path of file: %s", abs_path)
    guess: "guessit" = guessit(abs_path)
    return guess["title"] guess["year"] guess["container"] guess["type"]

def parse(path: "Path") -> tuple(str):
    abs_path: "Path" = path.resolve(strict=True)
    logger.info("Path of file passed: %s", abs_path)
    guess: "guessit" = guessit(abs_path)
    return 

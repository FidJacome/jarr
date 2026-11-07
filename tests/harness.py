"""Run jarr.main() with faked TMDB, input() and getpass(). HOME must already point at a temp dir.

Usage: harness.py '<json: {"inputs": [...], "secrets": [...], "argv": [...]}>'
"""
import builtins
import getpass
import json
import sys

cfg = json.loads(sys.argv[1])
inputs = iter(cfg.get("inputs", []))
secrets = iter(cfg.get("secrets", []))


def fake_input(prompt=""):
    val = next(inputs, None)
    if val is None:  # script ran out of answers: behave like Ctrl-D, not like a jarr crash
        raise EOFError
    print(f"{prompt}<{val}>")
    return val


def fake_getpass(prompt=""):
    val = next(secrets, None)
    if val is None:
        raise EOFError
    print(f"{prompt}<secret:{val}>")
    return val


builtins.input = fake_input
getpass.getpass = fake_getpass

import jarr  # noqa: E402  (imported after HOME is set, so CONFIG_DIR points at the temp dir)
import jarr.commands.prep  # noqa: E402
from jarr.tmdbmatch import TMDBMatch  # noqa: E402

QUERIES = []  # tokens used, one per TMDB search
LOOSE = []  # loose flag of each search, in order


def fake_query(media, loose, token):
    QUERIES.append(token)
    LOOSE.append(loose)
    if media.kind == "movie":
        return [TMDBMatch({"id": 603, "title": "The Matrix", "release_date": "1999-03-31"})]
    return [TMDBMatch({"id": 1396, "name": "Breaking Bad", "first_air_date": "2008-01-20"})]


# Patch the name cmd_prep actually calls: commands/prep.py has its own reference to TMDB_query.
jarr.commands.prep.TMDB_query = fake_query
sys.argv = ["jarr", *cfg["argv"]]
rc = jarr.main()
print(f"__TOKEN_USED__={QUERIES[-1] if QUERIES else None}")
print(f"__LOOSE__={LOOSE}")
sys.exit(rc)

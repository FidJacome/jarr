"""Scenario tests for jarr: prep, the config commands, and config.toml handling.

Each scenario runs jarr.main() in a subprocess with a throwaway HOME, fake TMDB results and
scripted input()/getpass(). Checks look at outcomes (exit code, config.toml contents, where the video
ended up), never at message wording.

  uv run tests/run_tests.py             run against the real code
  V=1 uv run tests/run_tests.py         also print output of passing scenarios
  KEEP=1 uv run tests/run_tests.py      keep the temp homes (tests/homes/) for inspection
  PYTHONPATH=<dir> uv run ...           test a different copy of the jarr package
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable  # the Python running this script (uv run -> the project venv)
MOVIE = "The.Matrix.1999.1080p.mkv"
EPISODE = "Breaking.Bad.S01E02.720p.mkv"
MOVIE_REL = "movie/The Matrix (1999) [tmdbid-603]/The Matrix (1999).mkv"
TV_REL = "tv/Breaking Bad (2008) [tmdbid-1396]/Season 01/Breaking Bad S01E02.mkv"
results, homes = [], []
(HERE / "homes").mkdir(exist_ok=True)
RUN_DIR = Path(tempfile.mkdtemp(prefix="run-", dir=HERE / "homes"))  # one per suite run


# ---------- helpers ----------

def run(home, argv, inputs=("y", "1"), secrets=(), cwd=None, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ("TMDB_TOKEN", "XDG_CONFIG_HOME", "XDG_STATE_HOME")}
    env["HOME"] = str(home)
    env.update(env_extra or {})
    cfg = {"argv": argv, "inputs": list(inputs), "secrets": list(secrets)}
    p = subprocess.run([PY, str(HERE / "harness.py"), json.dumps(cfg)], env=env,
                       cwd=cwd or home, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout + p.stderr


def setup(token=True, default=None):
    # jarr passes the last 3 path parts to guessit (home/dl/video), so the home folder's name is
    # part of what gets parsed. Random names like "jarrtest-e65_pnop" sometimes read as an episode
    # (e65), which made the suite flaky. Fixed names (home001, ...) parse cleanly; the random part
    # lives one level up, in RUN_DIR, where guessit never sees it.
    home = RUN_DIR / f"home{len(homes) + 1:03d}"
    home.mkdir()
    homes.append(home)
    (home / "dl").mkdir()
    for n in (MOVIE, EPISODE):
        (home / "dl" / n).write_text("x")
    lines = []
    if default:
        lines.append(f'default_dir = "{default}"')
    if token:
        lines.append('[tmdb]\ntoken = "tok123"')
    if lines:
        (home / ".config/jarr").mkdir(parents=True)
        (home / ".config/jarr/config.toml").write_text("\n".join(lines) + "\n")
    return home


CONFIG = ".config/jarr/config.toml"


def config_text(home):
    f = home / CONFIG
    return f.read_text() if f.is_file() else "<missing>"


def saved(home):
    """Parsed config.toml ({} if missing). A broken file makes the check fail loudly."""
    f = home / CONFIG
    return tomllib.loads(f.read_text()) if f.is_file() else {}


def saved_token(home):
    return saved(home).get("tmdb", {}).get("token")


def saved_default(home):
    return saved(home).get("default_dir")


def ok_run(rc, out):
    """Finished successfully, no crash."""
    return rc == 0 and "Traceback" not in out


def clean_fail(rc, out, home):
    """Stopped with an error message, no crash, and the video wasn't moved."""
    return rc == 1 and "Error:" in out and "Traceback" not in out and (home / "dl" / MOVIE).exists()


def check(name, ok, rc, out, home):
    results.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok or os.getenv("V"):
        detail = f"rc={rc}\n{out}--- config.toml ---\n{config_text(home)}"
        print("      " + detail.rstrip().replace("\n", "\n      "))


def section(title):
    print(f"\n== {title} ==")


# ---------- token ----------
section("token")

h = setup(token=False)
rc, out = run(h, [str(h / "dl" / MOVIE)], secrets=["  newtok  "])
check("T1 no token -> prompts, strips spaces, saves, uses it",
      ok_run(rc, out) and saved_token(h) == "newtok" and "__TOKEN_USED__=newtok" in out
      and (h / "staging" / MOVIE_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)])
check("T2 saved token -> no prompt, saved token used",
      ok_run(rc, out) and "<secret:" not in out and "__TOKEN_USED__=tok123" in out, rc, out, h)

h = setup()
run(h, ["config", "token"], secrets=["changed"])
rc, out = run(h, [str(h / "dl" / MOVIE)])
check("T3 a token set with 'config token' is used by the next run",
      ok_run(rc, out) and "<secret:" not in out and "__TOKEN_USED__=changed" in out, rc, out, h)

h = setup(token=False)
rc, out = run(h, [str(h / "dl" / MOVIE)], secrets=["   "])
check("T4 blank token -> clean error, nothing saved",
      clean_fail(rc, out, h) and saved_token(h) is None, rc, out, h)

h = setup(token=False)
rc, out = run(h, [str(h / "dl" / MOVIE)], env_extra={"TMDB_TOKEN": "fromenv"})
check("T5 TMDB_TOKEN from the shell works without a config file",
      ok_run(rc, out) and "<secret:" not in out and "__TOKEN_USED__=fromenv" in out, rc, out, h)

h = setup(token=False)
(h / ".config").write_text("i am a file")  # ~/.config unusable -> can't save anything
rc, out = run(h, [str(h / "dl" / MOVIE)], secrets=["tok"])
check("T6 token can't be saved -> still asked, error shown, run continues with it",
      ok_run(rc, out) and "<secret:" in out and "Error:" in out and "__TOKEN_USED__=tok" in out
      and (h / "staging" / MOVIE_REL).exists(), rc, out, h)

# ---------- destination choice ----------
section("destination choice")

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)])
check("D1 no path, no default -> ~/staging",
      ok_run(rc, out) and (h / "staging" / MOVIE_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE), str(h / "lib")])
check("D2 typed path -> used, NOT saved as default",
      ok_run(rc, out) and (h / "lib" / MOVIE_REL).exists() and saved_default(h) is None, rc, out, h)

h = setup(default="/nonexistent-should-not-be-used")
rc, out = run(h, [str(h / "dl" / MOVIE), str(h / "other")])
check("D3 typed path beats saved default",
      ok_run(rc, out) and (h / "other" / MOVIE_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / EPISODE), str(h / "lib")])
check("D4 episode goes to <dest>/tv/<show>/Season NN",
      ok_run(rc, out) and (h / "lib" / TV_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE), "~/lib"])
check("D5 quoted '~/lib' expands to home (no literal '~' folder)",
      ok_run(rc, out) and (h / "lib" / MOVIE_REL).exists() and not (h / "~").exists(), rc, out, h)

# ---------- prep ----------
section("prep")

h = setup()
rc, out = run(h, ["prep", str(h / "dl" / MOVIE), str(h / "lib")])
check("P1 'jarr prep <video> <folder>' works like the shortcut",
      ok_run(rc, out) and (h / "lib" / MOVIE_REL).exists() and saved_default(h) is None, rc, out, h)

h = setup()
run(h, ["config", "dir", str(h / "lib")], inputs=["y"])
rc, out = run(h, [str(h / "dl" / EPISODE)])
check("P2 a default set with 'config dir' is used on the next run",
      ok_run(rc, out) and (h / "lib" / TV_REL).exists(), rc, out, h)

h = setup()
(h / "work").mkdir()
rc, out = run(h, [str(h / "dl" / MOVIE), "rel/lib"], cwd=h / "work")
check("P3 relative destination -> resolved against the current folder",
      ok_run(rc, out) and (h / "work/rel/lib" / MOVIE_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)], inputs=["n"])
check("P4 answering 'n' to the search -> cancelled, video not moved",
      rc == 130 and "Traceback" not in out and (h / "dl" / MOVIE).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)], inputs=["y", "0"])
check("P8 '0' at Choose -> cancelled, video not moved to any match",
      rc == 130 and "Traceback" not in out and (h / "dl" / MOVIE).exists()
      and not (h / "staging" / "movie").exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)], inputs=["y", "L", "1"])
check("P9 'L' at Choose -> second search ignores the year, then the pick is moved",
      ok_run(rc, out) and "__LOOSE__=[False, True]" in out
      and (h / "staging" / MOVIE_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)], inputs=["y", "L", "L", "1"])
check("P10 only one loose search: a second 'L' is rejected, then the pick is moved",
      ok_run(rc, out) and "__LOOSE__=[False, True]" in out
      and (h / "staging" / MOVIE_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)], inputs=["l", "l", "1"])
check("P11 loose at 'Search TMDB?' -> 'l' rejected at Choose, no second search",
      ok_run(rc, out) and "__LOOSE__=[True]" in out
      and (h / "staging" / MOVIE_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / EPISODE)], inputs=["y", "l", "1"])
check("P12 no year in the filename -> 'l' rejected at Choose, no second search",
      ok_run(rc, out) and "__LOOSE__=[False]" in out
      and (h / "staging" / TV_REL).exists(), rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl" / "missing.mkv")])
check("P5 missing video -> clean error, nothing saved",
      clean_fail(rc, out, h) and saved_default(h) is None, rc, out, h)

h = setup()
rc, out = run(h, [str(h / "dl")])
check("P6 a folder instead of a video -> clean error",
      clean_fail(rc, out, h), rc, out, h)

h = setup()
rc, out = run(h, ["prep"])
check("P7 'jarr prep' with no video -> usage error",
      rc == 2 and "usage:" in out and "Traceback" not in out, rc, out, h)

# ---------- config dir ----------
section("config dir")

h = setup()
(h / "lib").mkdir()
rc, out = run(h, ["config", "dir", str(h / "lib")])
check("CD1 existing folder -> saved, no TMDB search",
      ok_run(rc, out) and saved_default(h) == f"{h}/lib" and "__TOKEN_USED__=None" in out
      and "Search TMDB" not in out, rc, out, h)

h = setup()
(h / "work").mkdir(); (h / "work/lib").mkdir()
rc, out = run(h, ["config", "dir", "lib"], cwd=h / "work")
check("CD2 relative folder -> saved as an absolute path",
      ok_run(rc, out) and saved_default(h) == f"{h}/work/lib", rc, out, h)

h = setup()
(h / "lib").mkdir()
rc, out = run(h, ["config", "dir", "~/lib"])
check("CD3 quoted '~/lib' -> saved with ~ expanded (no literal '~' folder)",
      ok_run(rc, out) and saved_default(h) == f"{h}/lib" and not (h / "~").exists(), rc, out, h)

h = setup()
rc, out = run(h, ["config", "dir", str(h / "newlib")], inputs=["y"])
check("CD4 missing folder + 'y' -> created and saved",
      ok_run(rc, out) and (h / "newlib").is_dir() and saved_default(h) == f"{h}/newlib", rc, out, h)

h = setup()
rc, out = run(h, ["config", "dir", str(h / "newlib")], inputs=["n"])
check("CD5 missing folder + 'n' -> cancelled, nothing created or saved",
      rc == 130 and "Traceback" not in out and not (h / "newlib").exists()
      and saved_default(h) is None, rc, out, h)

h = setup()
(h / "afile").write_text("x")
rc, out = run(h, ["config", "dir", str(h / "afile")])
check("CD6 a file -> clean error, nothing saved",
      rc == 1 and "Error:" in out and "Traceback" not in out and saved_default(h) is None, rc, out, h)

h = setup()
(h / "afile").write_text("x")
rc, out = run(h, ["config", "dir", str(h / "afile" / "sub")], inputs=["y"])
check("CD7 folder can't be created (under a file) -> clean error, nothing saved",
      rc == 1 and "Error:" in out and "Traceback" not in out and saved_default(h) is None, rc, out, h)

h = setup(token=False)
(h / "lib").mkdir()
rc, out = run(h, ["config", "dir", str(h / "lib")])
check("CD8 works when ~/.config/jarr doesn't exist yet",
      ok_run(rc, out) and saved_default(h) == f"{h}/lib", rc, out, h)

h = setup(token=False)
(h / "lib").mkdir()
(h / ".config").write_text("i am a file")  # ~/.config unusable -> can't save anything
rc, out = run(h, ["config", "dir", str(h / "lib")])
check("CD9 saving fails -> exit 1, not a false success",
      rc == 1 and "Error:" in out and "Traceback" not in out, rc, out, h)

h = setup()
rc, out = run(h, ["config", "dir"])
check("CD10 'jarr config dir' with no folder -> usage error, nothing saved",
      rc == 2 and "usage:" in out and "Traceback" not in out and saved_default(h) is None, rc, out, h)

# ---------- config token ----------
section("config token")

h = setup()
rc, out = run(h, ["config", "token"], secrets=["  changed  "])
check("CT1 replaces the token (spaces stripped), no TMDB search",
      ok_run(rc, out) and saved_token(h) == "changed" and "__TOKEN_USED__=None" in out
      and "Search TMDB" not in out, rc, out, h)

h = setup()
rc, out = run(h, ["config", "token"], secrets=["   "])
check("CT2 blank token -> clean error, saved token unchanged",
      rc == 1 and "Error:" in out and "Traceback" not in out and saved_token(h) == "tok123", rc, out, h)

h = setup()
rc, out = run(h, ["config", "token"])  # no answer at all: like Ctrl+D
check("CT3 prompt cancelled -> exit 130, saved token unchanged",
      rc == 130 and "Traceback" not in out and saved_token(h) == "tok123", rc, out, h)

h = setup(token=False)
(h / ".config").write_text("i am a file")
rc, out = run(h, ["config", "token"], secrets=["tok"])
check("CT4 saving fails -> exit 1, not a false success",
      rc == 1 and "Error:" in out and "Traceback" not in out, rc, out, h)

# ---------- config show / path ----------
section("config show / path")

h = setup(token=False)
(h / ".config/jarr").mkdir(parents=True)
(h / CONFIG).write_text('default_dir = "/mnt/media"\n[tmdb]\ntoken = "abcdef123456"\n')
rc, out = run(h, ["config", "show"])
check("CS1 shows the settings with the token masked",
      ok_run(rc, out) and "/mnt/media" in out and "3456" in out and "abcdef123456" not in out, rc, out, h)

h = setup(token=False)
rc, out = run(h, ["config", "show"])
check("CS2 nothing saved -> exit 0, no crash",
      ok_run(rc, out) and "Error:" not in out, rc, out, h)

h = setup(token=False)
(h / ".config/jarr").mkdir(parents=True)
(h / CONFIG).write_text("this is = = not toml\n")
rc, out = run(h, ["config", "show"])
check("CS3 broken config.toml -> error shown, no crash",
      ok_run(rc, out) and "Error:" in out, rc, out, h)

h = setup()
rc, out = run(h, ["config", "path"])
check("CS4 'config path' prints the config file's path",
      ok_run(rc, out) and str(h / CONFIG) in out, rc, out, h)

# ---------- usage ----------
section("usage")

h = setup()
rc, out = run(h, [])
check("K1 'jarr' with no arguments -> usage error, no crash",
      rc == 2 and "usage:" in out and "Traceback" not in out, rc, out, h)

h = setup()
rc, out = run(h, ["config"])
check("K2 'jarr config' with no action -> usage error",
      rc == 2 and "usage:" in out and "Traceback" not in out, rc, out, h)

h = setup()
rc, out = run(h, ["config", "token", "dir"])
check("K3 config actions can't be chained -> usage error, nothing saved",
      rc == 2 and "Traceback" not in out and saved_token(h) == "tok123", rc, out, h)

h = setup()
(h / "lib").mkdir()
rc, out = run(h, ["-d", str(h / "lib")])
check("K4 removed flags (-d) -> usage error, nothing saved",
      rc == 2 and "Traceback" not in out and saved_default(h) is None, rc, out, h)

h = setup()
rc, out = run(h, ["-t"])
check("K5 removed flags (-t) -> usage error, no prompt",
      rc == 2 and "Traceback" not in out and "<secret:" not in out, rc, out, h)

h = setup()
rc, out = run(h, ["--help"])
check("K6 '--help' -> help, not treated as a video",
      rc == 0 and "usage:" in out and "Search TMDB" not in out, rc, out, h)

h = setup()
rc, out = run(h, ["-h"])
check("K7 '-h' -> top-level help (lists the commands), not prep's",
      rc == 0 and "{prep,config}" in out and "Search TMDB" not in out, rc, out, h)


# ---------- unusable destinations ----------
section("unusable destinations")

h = setup()
(h / "afile").write_text("not a dir")
rc, out = run(h, [str(h / "dl" / MOVIE), str(h / "afile")])
check("U1 destination is a file -> clean error, video not moved",
      clean_fail(rc, out, h), rc, out, h)

h = setup()
(h / "afile").write_text("x")
rc, out = run(h, [str(h / "dl" / MOVIE), str(h / "afile" / "sub")])
check("U2 destination nested under a file -> clean error, video not moved",
      clean_fail(rc, out, h), rc, out, h)

h = setup()
(h / "afile").write_text("x")
(h / CONFIG).write_text(f'default_dir = "{h}/afile"\n[tmdb]\ntoken = "tok123"\n')
rc, out = run(h, [str(h / "dl" / MOVIE)])
check("U3 saved default points at a file -> clean error, video not moved",
      clean_fail(rc, out, h), rc, out, h)

# ---------- config.toml ----------
section("config.toml")

h = setup()
rc, out = run(h, [str(h / "dl" / MOVIE)], env_extra={"TMDB_TOKEN": "fromenv"})
check("C1 TMDB_TOKEN beats the saved token, saved one left alone",
      ok_run(rc, out) and "__TOKEN_USED__=fromenv" in out and saved_token(h) == "tok123", rc, out, h)

h = setup(token=False)
rc, out = run(h, [str(h / "dl" / MOVIE)], env_extra={"TMDB_TOKEN": "fromenv"})
check("C2 a token from TMDB_TOKEN is never written to disk",
      ok_run(rc, out) and saved_token(h) is None, rc, out, h)

h = setup(token=False)
rc, out = run(h, ["config", "token"], secrets=["tok"])
mode = (h / CONFIG).stat().st_mode & 0o777 if (h / CONFIG).is_file() else None
check("C3 config.toml is created owner-only (600)",
      ok_run(rc, out) and mode == 0o600, rc, out, h)

h = setup(default="/mnt/media")
rc, out = run(h, ["config", "token"], secrets=["changed"])
check("C4 saving the token keeps the default folder (whole file rewritten safely)",
      ok_run(rc, out) and saved_token(h) == "changed" and saved_default(h) == "/mnt/media", rc, out, h)

h = setup()
(h / "lib").mkdir()
rc, out = run(h, ["config", "dir", str(h / "lib")])
check("C5 saving the default keeps the token (whole file rewritten safely)",
      ok_run(rc, out) and saved_token(h) == "tok123" and saved_default(h) == f"{h}/lib", rc, out, h)

h = setup(token=False)
(h / ".config/jarr").mkdir(parents=True)
(h / CONFIG).write_text("this is = = not toml\n")
rc, out = run(h, [str(h / "dl" / MOVIE)], secrets=["tok"])
check("C6 broken config.toml -> error shown, treated as empty, no crash",
      ok_run(rc, out) and "Error:" in out and "<secret:" in out and saved_token(h) == "tok", rc, out, h)

h = setup(token=False)
(h / "xdg/jarr").mkdir(parents=True)
(h / "xdg/jarr/config.toml").write_text('[tmdb]\ntoken = "fromxdg"\n')
rc, out = run(h, [str(h / "dl" / MOVIE)], env_extra={"XDG_CONFIG_HOME": str(h / "xdg")})
check("C7 XDG_CONFIG_HOME is honored",
      ok_run(rc, out) and "__TOKEN_USED__=fromxdg" in out, rc, out, h)

h = setup(token=False)
(h / ".config/jarr").mkdir(parents=True)
(h / ".config/jarr/.env").write_text("TMDB_TOKEN='oldenv'\n")
rc, out = run(h, [str(h / "dl" / MOVIE)], secrets=["new"])
check("C8 an old .env is ignored (no migration, by design)",
      ok_run(rc, out) and "__TOKEN_USED__=new" in out, rc, out, h)

# ---------- summary ----------
passed = sum(ok for _, ok in results)
print(f"\n{passed}/{len(results)} passed")
if not os.getenv("KEEP"):
    shutil.rmtree(RUN_DIR, ignore_errors=True)
else:
    print(f"Kept: {RUN_DIR}")
sys.exit(0 if passed == len(results) else 1)

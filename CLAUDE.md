# CLAUDE.md

## How we work (read first)

- **Fidel is the main coder.** Claude's role is guidance, planning, code review, and occasional debugging.
- **Do not write or edit code unless explicitly asked to.** Explain, point to the file/line, suggest an approach or show
  a short illustrative snippet in chat, and let Fidel implement it.
- Editing docs such as this file or notes is fine when asked.
- Before a device switch or at the end of a session, update the **Current status** section below so the next session
  (possibly on another machine) can pick up where we left off. Commit and push it.

## Project

**Jarr** is a Jellyfin companion CLI. It identifies a video from its filename (guessit), matches it against TMDB, and
moves it into Jellyfin's recommended folder layout (`movie/Title (Year) [tmdbid-N]/...`,
`tv/Show (Year) [tmdbid-N]/Season NN/...`).

- Python ≥ 3.13, managed with **uv** (`uv sync`, `uv run jarr <video>`)
- Entry point: `jarr = "jarr:main"` → `src/jarr/__init__.py`
- Dependencies: guessit, requests, tomli-w
- Tests: `uv run tests/run_tests.py` (44 end-to-end scenarios; see Testing below)
- Practice exercises and prototypes live in a separate **private** repo, `FidJacome/jarr-practice`, cloned next to
  this one (`practice/` lessons, `prototypes/` drafts of jarr functions). Keep them out of this public repo.
- Workspace layout: `~/code/jarr-root/` (not a git repo) holds both clones, `jarr/` and `jarr-practice/`. Sessions
  are usually started from `jarr-root/`. Its own small `CLAUDE.md` just describes this layout and imports this file;
  it isn't synced, so recreate it on a new device if needed. After cloning or moving folders, run `uv sync` in
  `jarr/` (a stale venv shows up as `No module named 'jarr'`).

### Layout (`src/jarr/`)

| File | Purpose |
|---|---|
| `__init__.py` | `main()`: arg handling, token/destination logic, the identify → search → move flow |
| `cli.py` | argparse definition (`file`, `destination_path`, `-t`, `-d`) |
| `config.py` | `load_config()` / `save_config()` for `$XDG_CONFIG_HOME/jarr/config.toml` (chmod 600), `set_config(config, *keys, value)` for nested keys in memory |
| `constants.py` | Video extensions, TMDB URL, `LOG_FILE`, `CONFIG_DIR` |
| `media.py` | `Media.from_path()`: parses filename/folders into title, year, kind, season, episode |
| `query_ops.py` | `TMDB_query`, `TMDB_select`, `TMDBError`, `NoMatchError` |
| `tmdbmatch.py` | TMDB result model |
| `style.py` | Terminal color helpers and `short_path` |

### Conventions

- Logs go to `$XDG_STATE_HOME/jarr/jarr.log`; console only shows errors.
- `main()` returns exit codes (0 ok, 1 error, 130 cancelled).
- Commits: descriptive body; WIP commits list known issues so they serve as handoff notes.
- Settings: change the dict with `set_config`, then call `save_config` once and decide per caller what a failed save
  means. Priority: `TMDB_TOKEN` env var > saved token > prompt; typed folder > saved `default_dir` > `~/staging`.
  Env tokens are never written to disk.
- Releases bump `pyproject.toml` version and update the README.
- Versioning: SemVer, staying on 0.x for now (a breaking change bumps the middle number). Annotated tags; GitHub
  releases for 0.x are marked **pre-release** and get hand-written, user-facing notes.

### Testing

`tests/run_tests.py` runs each scenario through `jarr.main()` in a throwaway home (`tests/homes/`, gitignored), with
TMDB, `input()` and `getpass()` faked by `tests/harness.py`. Checks look at outcomes (exit code, `config.toml`
contents, where the video ended up), never message wording. `V=1` prints passing output too; `KEEP=1` keeps the
temp homes. Run the suite after every change to `main()`; add a scenario for each bug fixed.

## Current status

_Last updated: 2026-11-05_

**Branch:** `feature/subcommands` (pushed). v0.2.0 is the latest release.

Done on this branch:
- Settings moved from `~/.config/jarr/.env` to `config.toml` (`c963398`). `python-dotenv` and `ENV_PATH` removed.
  **No migration from `.env`** (deliberate: sole user, settings trivial to re-enter); the README has an
  "Upgrading from 0.2.0" note instead.
- Tests moved into the repo as `tests/` (`9537fdf`), 44/44 passing.

**Release decision:** no release yet. **v0.3.0 = config.toml + subcommands**, released together.

**Now: argparse lessons first** (see "argparse lesson series" below). Fidel found he can read `cli.py` but can't
write argparse from scratch (Claude wrote `cli.py` originally), so the subcommand work waits until he can.

**After that: the subcommands** (design agreed earlier, details still to plan):
- `jarr prep <video> [folder]` is the main command; `jarr <video> [folder]` stays as a shortcut for it.
- `jarr config token`, `jarr config dir <folder>`, `jarr config show` (token masked), `jarr config path`.
- `-t`/`-d` get removed. Planned layout: `cli.py` (dispatch), `commands/prep.py`, `commands/config.py`.
- Then update the tests and README, and release v0.3.0 with "Upgrading from 0.2.0" notes.

Optional improvements noted along the way:
- `save_config`: write to a temp file and `Path.replace()` it (atomic write), and create it as 0600 from the start
  (`os.open`) instead of `chmod` afterwards.
- `jarr -t` succeeds silently; a short "Token saved." message would help.

### Learning notes

- Fidel learns best with **pseudocode first** and concrete analogies (nested dicts = folder tree, `current_pos` =
  current directory), plus hand-traced tables. Introduce new concepts with a short lesson + exercise before using them.
- Lessons done: file I/O, TOML (`tomllib`/`tomli_w`), dict walking. A 5-part dictionary exercise set
  (`.get`, comprehensions, copy vs reference, `setdefault`/`get_config`, recursion/`flatten`) was handed out on
  2026-11-04; status unknown. `get_config` and `flatten` + `mask` feed into `jarr config show`.
- Lesson format that works: verify every example by actually running it and show real output; ask for written
  predictions before running; exercises are written from an empty file in `jarr-practice/practice/`.

### argparse lesson series (in progress)

| # | Topic | Exercise (in `jarr-practice/practice/`) | Status |
|---|---|---|---|
| 1 | describe vs parse (`parser` = blank form, `args` = filled form), positionals, `Namespace`, `type=`, free `--help`, exit code 2 | `argparse_1.py`: `repeat <word> <times>` | ✅ done |
| 2 | `nargs="?"` + `default` (no default → `None`), options `-s/--sep`, `store_true` flags, dashes → underscores, usage notation, `parser.error()` | `argparse_2.py`: `word [times] [-s SEP] [-u]` | ✅ done |
| 3 | `parse_args(argv=None)` + `parse_args(list)`, `if __name__ == "__main__":`, errors raise `SystemExit` (not an `Exception`), `assert`, plain vs relative imports | `test_argparse2.py` with an `exit_code(argv)` helper | ✅ done, tests pass |
| 4 | functions as values: name vs call `()`, dispatch dict, passing functions (`type=int`), "`'str' object is not callable`" | `calc.py`, see below | ⏳ handed out, **not started** |
| 5 | subcommands: `add_subparsers(dest=..., required=True)`, `add_parser`, nesting, `set_defaults(func=...)` + `args.func(args)`, the `jarr <video>` shortcut (insert `"prep"` into argv before parsing) | `subcommands.py`: jarr's CLI shape with print-only commands | not yet |

After lesson 5, Fidel writes jarr's new `cli.py` himself.

**Exercise 4 as handed out:**
- Part A, predict then run, with `def double(n): return n * 2` and `ops = {"double": double}`:
  `print(double)`, `print(double(4))`, `f = double; print(f(5))`, `print(ops["double"](3))`, `print(ops["double"])`,
  `g = double(2); print(g(2))`.
- Part B, `calc.py`: functions `add`/`sub`/`mul(a, b)` that return; `OPS = {"add": add, "sub": sub, "mul": mul}`;
  `parse_args(argv=None)` with positionals `op` (new: `choices=list(OPS)`), `a` and `b` (`type=float`); under the
  main guard, look up and call the function from `OPS`, with no `if`/`elif` on the op name. Expected:
  `add 2 3` → `5.0`, `mul 4 2.5` → `10.0`, `div 1 2` → "invalid choice".
- Bonus: add `div`, count how many lines it took; what happens with `div 1 0` and where to handle it.

Lesson 4 context: Fidel's earlier `subcommands.py` attempt (deleted/abandoned) used `set_defaults(func=print(...))`
and `prep.file`, i.e. calling instead of passing a function, and reading values from the parser instead of `args`.
Both were explained in lessons 1 and 4.

Notes from his exercises: `argparse_1.py` predicted `int("three")` → 3 (it fails); `argparse_2.py` uppercases
after joining, so the separator is uppercased too (left as a discussion point).

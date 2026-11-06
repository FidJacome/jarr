# CLAUDE.md

## How we work (read first)

- **Fidel is the main coder.** Claude's role is guidance, planning, code review, and occasional debugging.
- **Do not write or edit code unless explicitly asked to.** Explain, point to the file/line, suggest an approach or show
  a short illustrative snippet in chat, and let Fidel implement it.
- Editing docs such as this file or notes is fine when asked.
- **AI transparency rule (since 2026-11-06), for every change Claude makes in either repo (`jarr`, `jarr-practice`),
  code, tests or docs alike:**
  1. Before touching anything, commit Fidel's uncommitted work as-is (his normal git identity, a descriptive message;
     prefix `WIP:` if it's mid-task). Skip this if the tree is clean.
  2. Make the change.
  3. Commit only Claude's change with Claude as the author:
     `git commit --author="Claude <noreply@anthropic.com>" ...`. Fidel stays the committer.
  Never mix Fidel's and Claude's edits in one commit, so `git log --author=Claude` and `git blame` show exactly what
  Claude wrote. Don't push unless asked.
  The email maps to the GitHub user `claude`, so these commits count under it in Insights → Contributors once they
  reach `main`. **Merge PRs with "Create a merge commit" (or "Rebase and merge"), never "Squash and merge"**: squashing
  turns the whole PR into one commit authored by Fidel and Claude's commits drop out of the count. `Co-Authored-By`
  trailers don't count in that graph; only the author does.
- Before a device switch or at the end of a session, update the **Current status** section below so the next session
  (possibly on another machine) can pick up where we left off. Commit and push it.

## Project

**Jarr** is a Jellyfin companion CLI. It identifies a video from its filename (guessit), matches it against TMDB, and
moves it into Jellyfin's recommended folder layout (`movie/Title (Year) [tmdbid-N]/...`,
`tv/Show (Year) [tmdbid-N]/Season NN/...`).

- Python ≥ 3.13, managed with **uv** (`uv sync`, `uv run jarr <video>`)
- Entry point: `jarr = "jarr:main"` → `src/jarr/__init__.py`
- Dependencies: guessit, requests, tomli-w
- Tests: `uv run tests/run_tests.py` (53 end-to-end scenarios; see Testing below)
- Practice exercises and prototypes live in a separate **private** repo, `FidJacome/jarr-practice`, cloned next to
  this one (`practice/` lessons, `prototypes/` drafts of jarr functions). Keep them out of this public repo.
- Workspace layout: `~/code/jarr-root/` (not a git repo) holds both clones, `jarr/` and `jarr-practice/`. Sessions
  are usually started from `jarr-root/`. Its own small `CLAUDE.md` just describes this layout and imports this file;
  it isn't synced, so recreate it on a new device if needed. After cloning or moving folders, run `uv sync` in
  `jarr/` (a stale venv shows up as `No module named 'jarr'`).

### Layout (`src/jarr/`)

| File | Purpose |
|---|---|
| `__init__.py` | `main()`: logging setup, `args.func(args)`, and the catch-all for Ctrl+C (130) and unexpected errors (1) |
| `cli.py` | `parse_args()`: the subcommand tree (`prep`, `config token/dir/show/path`) and `add_default_command(argv, sub.choices)` for the `jarr <video>` shortcut |
| `commands/prep.py` | `cmd_prep(args)`: file checks, token lookup, destination choice, guessit → TMDB → move |
| `commands/config.py` | `cmd_config_tkn/dir/show/path(args)`; `SECRET_WORDS` + `is_secret()` + `mask()` for `config show` |
| `prompts.py` | `ask()` and `ask_token()`, shared by the commands |
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

_Last updated: 2026-11-06_

**v0.3.0 released (2026-11-06)**: PR #2 (`feature/subcommands` → `main`, merge commit), tag `v0.3.0`, GitHub
pre-release with user-facing notes. `main` is the current state; there's no open feature branch.

What went into v0.3.0:
- Settings moved from `~/.config/jarr/.env` to `config.toml` (`c963398`). `python-dotenv` and `ENV_PATH` removed.
  **No migration from `.env`** (deliberate: sole user, settings trivial to re-enter); the README has an
  "Upgrading from 0.2.0" note instead.
- Tests moved into the repo as `tests/` (`9537fdf`).
- **Subcommands done (2026-11-06).** Fidel wrote `cli.py`, `commands/prep.py`, `commands/config.py` and
  `prompts.py`, and reduced `main()` to a dispatcher. `-t`/`-d` are gone:
  - `jarr prep <video> [folder]`, with `jarr <video> [folder]` as a shortcut
  - `jarr config token`, `config dir <folder>` (expands `~`, resolves, offers to create a missing folder; declining
    exits 130), `config show` (secrets masked by name, e.g. `token: ****3456`), `config path`
- Claude's commits on top: the logging fix in `main()`, the test harness patching
  `jarr.commands.prep.TMDB_query` (patch where a name is *used*), `config show` masking + empty-config message,
  the test rewrite (53/53 passing) and the README Commands table.

**Release steps used (repeat for the next release):** bump `version` in `pyproject.toml` + `uv lock`; PR the feature
branch into `main` and merge with **"Create a merge commit"** (never squash, see the transparency rule); annotated
tag on the merge commit; GitHub release marked **pre-release** with hand-written user-facing notes (New / Improved /
Upgrading from the previous version).

**Next:** not decided yet. Candidates: Phase 2 (send files to the Jellyfin server), or the optional improvements
below. Start new work on a new feature branch from `main`.

Optional improvements noted along the way:
- `save_config`: write to a temp file and `Path.replace()` it (atomic write), and create it as 0600 from the start
  (`os.open`) instead of `chmod` afterwards.
- Ruff reports import-order (`I001`) in `commands/prep.py` and `media.py`; `ruff check --fix` sorts them.
- `cmd_prep` is one long function; it could be split into steps (find token, choose destination, search, move).
- **Possible flaky test:** one suite run on 2026-11-06 reported 52/53, then 42 runs in a row passed 53/53. Which
  scenario failed wasn't captured (output was cut to the last line). If it happens again, keep the full output
  (the `FAIL` block prints rc, output and config.toml) before rerunning.

### Learning notes

- Fidel learns best with **pseudocode first** and concrete analogies (nested dicts = folder tree, `current_pos` =
  current directory), plus hand-traced tables. Introduce new concepts with a short lesson + exercise before using them.
- Lessons done: file I/O, TOML (`tomllib`/`tomli_w`), dict walking. A 5-part dictionary exercise set
  (`.get`, comprehensions, copy vs reference, `setdefault`/`get_config`, recursion/`flatten`) was handed out on
  2026-11-04; status unknown. `get_config` and `flatten` + `mask` feed into `jarr config show`.
- Lesson format that works: verify every example by actually running it and show real output; ask for written
  predictions before running; exercises are written from an empty file in `jarr-practice/practice/`.

### argparse lesson series (finished 2026-11-06)

| # | Topic | Exercise (in `jarr-practice/practice/`) | Status |
|---|---|---|---|
| 1 | describe vs parse (`parser` = blank form, `args` = filled form), positionals, `Namespace`, `type=`, free `--help`, exit code 2 | `argparse_1.py`: `repeat <word> <times>` | ✅ done |
| 2 | `nargs="?"` + `default` (no default → `None`), options `-s/--sep`, `store_true` flags, dashes → underscores, usage notation, `parser.error()` | `argparse_2.py`: `word [times] [-s SEP] [-u]` | ✅ done |
| 3 | `parse_args(argv=None)` + `parse_args(list)`, `if __name__ == "__main__":`, errors raise `SystemExit` (not an `Exception`), `assert`, plain vs relative imports | `test_argparse2.py` with an `exit_code(argv)` helper | ✅ done, tests pass |
| 4 | functions as values: name vs call `()`, dispatch dict, passing functions (`type=int`), "`'str' object is not callable`" | `predict_double.py` (all predictions right), `calc.py` with an `OPS` dispatch dict + `choices=list(OPS)` | ✅ done, incl. `div` bonus |
| 5 | subcommands: `add_subparsers(dest=..., required=True)`, `add_parser`, nesting, `set_defaults` (a value each subcommand attaches to `args`; `func=` is just one such value), `args.func(args)`, `args` is flat, the `jarr <video>` shortcut | `subcommands.py` + `test_subcommands.py` | ✅ done, tests pass |

Decisions from exercise 5 that carry over to jarr's `cli.py`:
- **Shortcut:** `add_default_command(argv, commands)` returns a new list (`["prep"] + argv`), never mutates. It
  leaves the list alone if it's empty, if `argv[0]` is a known command, or if it starts with `-`. `parse_args` first
  turns `argv=None` into `sys.argv[1:]`, builds the tree, then calls `add_default_command(argv, sub.choices)`.
  Using `sub.choices` (Fidel's idea, not a hardcoded list) keeps the command list in one place. Claude had wrongly
  claimed it couldn't work; it does, because the check only has to run before *parsing*, not before *building*.
- Names used: `dest="command"` (top level), `dest="subcommand"` (under `config`), `config dir`'s argument is
  `new_dir`. Each leaf has its own `cmd_...(args)` function; `config` itself has none.
- Tests cover four groups: parsed values, `args.func is cmd_...`, `add_default_command` directly (incl. a dash in the
  filename, empty list, caller's list unchanged), and exit codes via an `exit_code(argv)` helper.

Common mistakes seen along the way, now understood: reading values from the parser instead of `args` (`prep.file`);
calling instead of passing a function (`set_defaults(func=print(...))`); reading `args.command.file` (`args` is flat);
adding `token`/`dir`/`show` as *arguments* of `config` instead of *subcommands*; `parse_args()` without `argv`;
`.insert()` on the caller's list; `"-" in x` instead of `x.startswith("-")`; comparing `Path` with `str`; calling
`parse_args(["--help"])` in a test without catching `SystemExit`. Also: `int("three")` fails, and in `calc.py` an
error message should exit non-zero (`sys.exit("msg")` → stderr, exit 1).

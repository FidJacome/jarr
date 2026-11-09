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
- Tests: `uv run tests/run_tests.py` (63 end-to-end scenarios; see Testing below)
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

_Last updated: 2026-11-09_

**Now on `feature/manual-edit` (WIP `156ebb6`, suite 0/63, see "Manual edit" below).** Batch comes after
manual edit; **0.4.0** is released once batch is done.

**`feature/options` → `main`: PR #3 merged 2026-11-09 (merge commit `bb371b2`), no release.** What it brought:
- **Choose prompt reworked** (Fidel): `l` (any case) = loose search, `0` = cancel (were `0` / `-1`).
  `TMDB_select(results, allow_loose)` returns `int | str` and only offers/accepts `l` when `allow_loose` is true.
  `prep` passes `media.year and not loose` (not a real `bool`, works by truthiness), so there's **at most one
  loose search**, none when the first search was already loose, and none without a year.
- **`-c/--copy`** (Fidel): `shutil.copy2` instead of `shutil.move`, logs "Copied".
- **Shortcut denylist** (Fidel): `add_default_command` leaves argv alone only if `argv[0]` is in
  `TOP_OPTIONS = ["-h", "--help"]`, so prep options work before the video (`jarr -c movie.mkv`). Will be removed
  with batch (see below).
- Claude's tests: P8–P12 (cancel, one loose search), P13–P16 (move vs copy, `-c` before/after the video,
  `--copy` with a folder), K7 (`-h` = top-level help). Each was checked to fail against the bug it guards.
- **Flaky suite fixed** (`e7d8c76`): `Media.from_path` passes the last 3 path parts to guessit, and the random
  temp home name was one of them; ~1 in 750 names (e.g. `jarrtest-e65_pnop`) read as an episode, so ~6% of runs
  failed. Homes are now `tests/homes/run-*/home001...`.

**Manual edit** (`feature/manual-edit`, in progress). The summary line shows guessit's reading before
"Search TMDB?", so a misread (e.g. a folder name read as an episode) is visible, but the only way out today is
cancelling. Plan: add `[e]dit` there; edit `Media` fields (kind, title, year, season/episode) with "Enter keeps
the current value", validate like `ask()`, then show the summary and ask again (a loop, a good first piece to
split out of `cmd_prep`). Switching to movie clears season/episode; removing the year hides `[l]oose`.
Keeping parent folders in guessit's input was deliberate (needed for `Show/Season 01/` layouts); the edit option
is the answer to misreads. Batch's report-at-the-end mode will reuse it.

Decided 2026-11-09:
- **Field by field** (not a menu). mnamer check skipped.
- **Also offered on "no match"**, not only at "Search TMDB?".
- **The edit returns a new `Media`**; guessit's original stays untouched so batch (and the user) can refer back
  to it.
- **No prompts inside `TMDB_query`** (Fidel first proposed calling the edit prompt from there). Reason: batch
  needs the work steps without prompts, so the caller decides what a no-match means. Fidel's WIP removes
  `NoMatchError` and returns `[]` instead.

Open questions (asked, not answered yet):
- Today `NoMatchError` was only raised on a *loose* search (`query_ops.py:56`). On a normal search with no
  results, `TMDB_query` returned `[]` and `TMDB_select` showed an empty list ("Enter a number between 0 and 0").
  Trace that: where can "no match" happen, so where must edit be offered?
- After edit → search → no match again, does the next edit start from guessit's values or the last edit?

**WIP state (`156ebb6`) and review notes (2026-11-09), to fix when resuming:**
- `prep.py:9` still imports `NoMatchError` → ImportError, `jarr` doesn't start, suite 0/63.
- `commands/prep_ops.py:38` (`file_deliver`) is unfinished → SyntaxError. It also uses `media.year`; the old
  code used the TMDB match's year (`selection.year`), and the `/` → `-` title replacement isn't there yet.
- `check_file`: `resolve(strict=True)` raises `FileNotFoundError`/`OSError` that nothing catches (the old code
  caught them); the suffix check lost `.lower()` (`movie.MKV` rejected); the directory message has `%s` but no
  argument (logging prints a "--- Logging error ---" traceback).
- `select_dest(args)` loads the config again (`cmd_prep` already has it) and takes `args`, which ties it to
  argparse; for batch, consider passing the typed folder and the config instead.
- `TMDB_query`: `if not results and loose_query == True: return []` is now redundant (an empty list already
  gives `[]`), but `data.get("results")` returning `None` would break the slice.
- `manual_edit` (in `prompts.py`): `input()` gives strings, so year/season/episode are `str` and
  `f"{media.season:02d}"` in `prep` raises ValueError; no "Enter keeps the current value" or validation yet;
  asks episode before season.

**After that: batch** (decided 2026-11-09, not started; bigger restructure, done after manual edit):
- **Its own subcommand** (`jarr batch`, `commands/batch.py`), not a prep option: it behaves differently (mostly
  unattended, few prompts). Options considered: `-r` for subfolders; multiple files and/or folders as input.
- **Separate the work from the prompts first.** Split `cmd_prep` into work steps (token, destination, parse,
  search, build target path, move/copy) and user-facing steps; prompts go to `prompts.py`. `TMDB_select` is mostly
  a prompt and probably moves there. `prep` and `batch` share the work steps instead of duplicating them.
- **Destination becomes an option, `--destination` (long form only).** Reason: with several input paths
  (`nargs="+"`), an optional positional destination can't be told apart from an input (argparse is greedy; tried
  in practice). **The `jarr <video>` shortcut gets removed** (too much upkeep). Both are breaking → **0.4.0**,
  with "Upgrading from 0.3.0" notes (shortcut, `--destination`, Choose keys).
- **Confirmation at the start** with the number of files and total size; batch therefore collects the full file
  list before processing any file (two phases). A move within one disk needs no space; across disks it's a copy +
  delete, and a copy always needs the space. Open question: how to tell whether two paths are on the same disk.
- **Picking a TMDB result without asking:** take the top result when its title and year match guessit's and no
  other result matches as well; anything else is ambiguous. Watch out for: episodes without a year (UK vs US "The
  Office"), titles that differ only in punctuation/`&`/case (exact vs cleaned-up comparison), year off by one,
  translated titles.
- **Ambiguous cases, user's choice via an option:** stop and ask right away, or finish the batch and list them at
  the end with an offer to edit each (reuses manual edit).

**v0.3.0 released (2026-11-06)**: PR #2 (`feature/subcommands` → `main`, merge commit), tag `v0.3.0`, GitHub
pre-release with user-facing notes.

What went into v0.3.0:
- Settings moved from `~/.config/jarr/.env` to `config.toml` (`c963398`). `python-dotenv` and `ENV_PATH` removed.
  **No migration from `.env`** (deliberate: sole user, settings trivial to re-enter); the README has an
  "Upgrading from 0.2.0" note instead.
- Tests moved into the repo as `tests/` (`9537fdf`).
- Subcommands: `jarr prep <video> [folder]` (shortcut `jarr <video> [folder]`), `jarr config token`,
  `config dir <folder>`, `config show` (secrets masked), `config path`. `-t`/`-d` are gone.

**Release steps used (repeat for the next release):** bump `version` in `pyproject.toml` + `uv lock`; PR the feature
branch into `main` and merge with **"Create a merge commit"** (never squash, see the transparency rule); annotated
tag on the merge commit; GitHub release marked **pre-release** with hand-written user-facing notes (New / Improved /
Upgrading from the previous version).

Optional improvements noted along the way:
- `save_config`: write to a temp file and `Path.replace()` it (atomic write), and create it as 0600 from the start
  (`os.open`) instead of `chmod` afterwards.
- Ruff reports import-order (`I001`) in `commands/prep.py` and `media.py`; `ruff check --fix` sorts them.
- `cmd_prep` is one long function; it could be split into steps (find token, choose destination, search, move).
- Test scenario numbering is out of order (P8–P16 sit before P5 in `run_tests.py`); cosmetic.
- Phase 2 (send files to the Jellyfin server) is still the big roadmap item.

### Learning notes

- **When Fidel asks for help building or fixing something, guide with questions, not pseudocode** (his request,
  2026-11-09: ready-made pseudocode left him "just translating the code you give me into python"). Make him think
  about how the system works: what a function receives and returns, which part of the code knows the information
  needed, which cases can happen, what happens today when an input is traced through the code. One or two questions
  at a time; let him propose the approach. If he's stuck, give hints that get more specific step by step;
  pseudocode only if he asks for it. Reviews ("check it") still name bugs directly (file, line, what goes wrong);
  the fix can be phrased as a question.
- Concrete analogies help (nested dicts = folder tree, `current_pos` = current directory), plus hand-traced tables.
  Introduce new concepts with a short lesson + exercise before using them.
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

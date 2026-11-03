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
- Dependencies: guessit, requests, tomli-w (python-dotenv is being phased out)

### Layout (`src/jarr/`)

| File | Purpose |
|---|---|
| `__init__.py` | `main()`: arg handling, token/destination logic, the identify → search → move flow |
| `cli.py` | argparse definition (`file`, `destination_path`, `-t`, `-d`) |
| `config.py` | `load_config()` / `save_config()` for `$XDG_CONFIG_HOME/jarr/config.toml` (chmod 600) |
| `constants.py` | Video extensions, TMDB URL, `LOG_FILE`, `CONFIG_DIR` (and legacy `ENV_PATH`) |
| `media.py` | `Media.from_path()`: parses filename/folders into title, year, kind, season, episode |
| `query_ops.py` | `TMDB_query`, `TMDB_select`, `TMDBError`, `NoMatchError` |
| `tmdbmatch.py` | TMDB result model |
| `style.py` | Terminal color helpers and `short_path` |

### Conventions

- Logs go to `$XDG_STATE_HOME/jarr/jarr.log`; console only shows errors.
- `main()` returns exit codes (0 ok, 1 error, 130 cancelled).
- Commits: descriptive body; WIP commits list known issues so they serve as handoff notes.
- Releases bump `pyproject.toml` version and update the README.

## Current status

_Last updated: 2026-11-03_

**Branch:** `feature/subcommands`. Migrating settings from `~/.config/jarr/.env` to `config.toml`. The subcommands
redesign the branch is named for hasn't been planned in detail yet.

Done: `config.py` (load/save), `LOG_FILE`/`CONFIG_DIR` moved to `constants.py`, `main()` now reads from `config.toml`.

**In progress: the `set_config(config, *keys, value)` helper** in `protoypes/set_config.py` (folder name has a typo).
It's meant to set a possibly nested key, e.g. `set_config(cfg, "tmdb", "token", value=tok)`, and then go into
`config.py`. Agreed design:
- Only modify the dict passed in; `save_config()` is called separately.
- Keep a "current position" variable starting at `config`. For each key in `keys[:-1]`, step down with
  `current = current.setdefault(key, {})`. After the loop, assign `current[keys[-1]] = value`. Plain assignment
  handles both new and existing keys, so no `.get()` check is needed.
- Raise `ValueError` on empty `keys`. Drop the unused `tomllib`/`tomli_w` imports and add type hints.
- Test cases: `{}` + `("tmdb","token")`; `{"tmdb":{"token":"old"}}` + same keys (overwrites); `{}` + `("default_dir",)`.
- The current draft still uses an undefined `i` and assigns the next key name as a value; it doesn't run yet.

Once it works, use it for items 1–3 below.

Note: `__init__.py` no longer imports `dotenv`, but `save_setting()` still calls `set_key`, so `-d <video> <folder>`
crashes with a `NameError` until item 3 is done.

Open items:
1. `setdefault()` on token/default_dir values means `-t` and `-d` can't change an existing value (assign instead).
2. A token entered during a normal run is never saved (no `save_config()` call on that path).
3. `-d <video> <folder>` still saves via the old `save_setting()` (.env).
4. Restore the `TMDB_TOKEN` env var override (it should take precedence over the saved token).
5. Remove the `dotenv` import, `ENV_PATH`, `save_setting`, and probably the `python-dotenv` dependency.
6. Update the README (it still says settings live in `.env`).

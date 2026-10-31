<div align="center">

# 🪼 Jarr

**The Jellyfin companion CLI tool**

Turn messy downloads into a clean, Jellyfin-ready library in one command.

![Python](https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white)
![uv](https://img.shields.io/badge/managed%20with-uv-DE5FE9)
![TMDB](https://img.shields.io/badge/metadata-TMDB-01B4E4?logo=themoviedatabase&logoColor=white)
![Jellyfin](https://img.shields.io/badge/for-Jellyfin-AA5CC3?logo=jellyfin&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

</div>

> [!WARNING]
> **Early development.** Jarr works, but it's still rough around the edges and things may change. Feedback and ideas are very welcome. Feel free to [open an issue](https://github.com/FidJacome/jarr/issues)!

---

## What it does

`Spider-Man.Across.the.Spider-Verse.2023.1080p.WEB-DL.x264.mkv` becomes

```
~/staging/movie/Spider-Man: Across the Spider-Verse (2023) [tmdbid-569094]/
└── Spider-Man: Across the Spider-Verse (2023).mkv
```

- **Identifies** the title, year, and movie/episode from the filename and its folders
- **Matches** it against [TMDB](https://www.themoviedb.org/) and lets you pick the right result
- **Files it** in the folder layout Jellyfin recommends, tagged with the TMDB id so Jellyfin always matches it correctly
- **Asks first**: confirms the guess before searching and never overwrites a file without your permission

## Getting started

### 1. Install

```bash
git clone https://github.com/FidJacome/jarr.git
cd jarr
uv sync
```

### 2. Add your TMDB token

Create a free account at [TMDB](https://www.themoviedb.org/), then copy your **API Read Access Token** from
[Settings → API](https://www.themoviedb.org/settings/api) into a `.env` file in the project root:

```env
TMDB_TOKEN=your_read_access_token
```

### 3. Run it

```bash
uv run jarr /path/to/video.mkv
```

## Example

```
Spider-Man.Across.the.Spider-Verse.2023.1080p.mkv
Spider-Man Across the Spider-Verse (2023)  Movie
Search TMDB? [Y]es / [l]oose (ignore year) / [n]o
Searching TMDB...

  1  Spider-Man: Across the Spider-Verse (2023)
     After reuniting with Gwen Stacy, Brooklyn's full-time, friendly neighborhood Spider-Man...
  2  Spider-Man: Across the Spider-Verse - Making Of (2023)

  0  Loose search (ignore year)    -1  Cancel
Choose: 1
✓ ~/staging/movie/Spider-Man: Across the Spider-Verse (2023) [tmdbid-569094]/Spider-Man: Across the Spider-Verse (2023).mkv
```

## Output layout

```
~/staging/
├── movie/
│   └── Movie Title (Year) [tmdbid-123]/
│       └── Movie Title (Year).mkv
└── tv/
    └── Show Title (Year) [tmdbid-456]/
        └── Season 01/
            └── Show Title S01E02.mkv
```

**Supported formats:** `.mkv` `.mp4` `.avi` `.m4v` `.mov` `.webm`

Logs are written to `~/.local/state/jarr/jarr.log`.

## 🗺️ Roadmap

### Phase 1: Identify, match, and rename

- [x] Identify the title, year, type of content, and file type from the raw filename
- [x] Query TMDB for real content matching the identified parameters
- [x] Rename the file and place it in Jellyfin's recommended folder tree

### Phase 2: Send to the media server

- [ ] Automatically move the file into the Jellyfin server

### Phase 3: Subtitles

- [ ] Identify and automatically download subtitles in the desired language

---

<div align="center">
<sub>This product uses the TMDB API but is not endorsed or certified by TMDB.</sub>
</div>

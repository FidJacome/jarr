import os

import requests
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    JSONDecodeError,
    ReadTimeout,
)

from jarr.config import save_config, set_config

from .constants import SEARCH_ENDPOINTS, TMDB_URL
from .media import Media
from .prompts import ask_token
from .style import bold, cyan, dim, yellow
from .tmdbmatch import TMDBMatch


class TMDBError(Exception):
    pass


def TMDB_query(media: "Media", loose_query: bool, config) -> list["TMDBMatch"]:
    token = os.getenv("TMDB_TOKEN") or config.get("tmdb", {}).get("token")
    if not token:
        token = ask_token()
    url: str = f"{TMDB_URL}{SEARCH_ENDPOINTS[media.kind]}"
    headers = {"accept": "application/json", "Authorization": f"Bearer {token}"}
    if media.kind == "movie":
        params = {"query": media.title, "primary_release_year": media.year}
    elif media.kind == "episode":
        params = {"query": media.title, "first_air_date_year": media.year}
    else:
        params = {"query": media.title}
    if loose_query == True:
        params = {"query": media.title}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except ConnectTimeout as e:
        raise TMDBError("Couldn't connect to TMDB") from e
    except ReadTimeout as e:
        raise TMDBError("Response took too long") from e
    except ConnectionError as e:
        raise TMDBError("No internet connection") from e
    except HTTPError as e:
        if e.response.status_code == 401:
            raise TMDBError(
                f"Error {e.response.status_code}: Check that your TMDB token is correct"
            ) from e
        raise TMDBError(f"Error {e.response.status_code}: {e.response.reason}") from e
    except JSONDecodeError as e:
        raise TMDBError("TMDB returned an invalid response") from e

    set_config(config, "tmdb", "token", value=token)
    save_config(config)

    results = data.get("results")
    if not results and loose_query == True:
        return []

    query_results: list[TMDBMatch] = []
    for result in results[:3]:
        query_results.append(TMDBMatch(result))
    return query_results


def TMDB_select(results: list["TMDBMatch"], allow_loose: bool) -> int | str:
    print()
    for i, match in enumerate(results, start=1):
        print(f"  {cyan(i)}  {bold(match.title)} {dim(f'({match.year})')}")
        if match.overview:
            overview = (
                match.overview
                if len(match.overview) <= 90
                else match.overview[:87].rstrip() + "..."
            )
            print(f"     {dim(overview)}")
    if allow_loose:
        print(f"\n  {cyan('l')}  Loose search (ignore year)    {cyan(0)}  Cancel")
    else:
        print(f"\n  {cyan(0)}  Cancel")

    while True:
        option = input(f"{bold('Choose:')} ").strip()
        try:
            option = int(option)
        except ValueError:
            pass
        if isinstance(option, str):
            option = option.lower()
        if allow_loose:
            if (
                isinstance(option, int) and 0 <= option <= len(results)
            ) or option == "l":
                break
            print(
                yellow(
                    f"Enter a number between 0 and {len(results)} or the letter l to perform a loose search."
                )
            )
        else:
            if isinstance(option, int) and 0 <= option <= len(results):
                break
            print(yellow(f"Enter a number between 0 and {len(results)}."))
    return option

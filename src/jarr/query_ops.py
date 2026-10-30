import requests
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout, HTTPError, JSONDecodeError
from .constants import TMDB_URL, SEARCH_ENDPOINTS
from .media import Media
from .tmdbmatch import TMDBMatch
from .style import bold, dim, cyan, yellow

class TMDBError(Exception):
    pass

class NoMatchError(Exception):
    pass

def TMDB_query(media: "Media", loose_query: bool, token) -> list["TMDBMatch"]:
    url: str = f"{TMDB_URL}{SEARCH_ENDPOINTS[media.kind]}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    if media.kind == "movie":
        params = {"query": media.title, "primary_release_year": media.year}
    elif media.kind == "episode":
        params = {"query": media.title, "first_air_date_year": media.year}
    else: params = {"query": media.title}
    if loose_query == True: params = {"query": media.title}

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
            raise TMDBError(f"Error {e.response.status_code}: Check that your TMDB token is correct") from e
        raise TMDBError(f"Error {e.response.status_code}: {e.response.reason}") from e
    except JSONDecodeError as e:
        raise TMDBError("TMDB returned an invalid response") from e

    results = data.get("results")
    if not results and loose_query == True:
        raise NoMatchError(f"No matches found for {media.title}")

    query_results: list["TMDBMatch"] = []
    for result in results[:3]:
        query_results.append(TMDBMatch(result))
    return query_results

def TMDB_select(results: list["TMDBMatch"]) -> int:
    print()
    for i, match in enumerate(results, start=1):
        print(f"  {cyan(i)}  {bold(match.title)} {dim(f'({match.year})')}")
        if match.overview:
            overview = match.overview if len(match.overview) <= 90 else match.overview[:87].rstrip() + "..."
            print(f"     {dim(overview)}")
    print(f"\n  {cyan(0)}  Loose search (ignore year)    {cyan(-1)}  Cancel")

    while True:
        raw = input(f"{bold('Choose:')} ").strip()
        try:
            option = int(raw)
        except ValueError:
            print(yellow("Please enter a number."))
            continue
        if -1 <= option <= len(results):
            break
        print(yellow(f"Choose a number between -1 and {len(results)}."))
    return option

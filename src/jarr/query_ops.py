import requests
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout, HTTPError, JSONDecodeError
from .constants import TMDB_URL, SEARCH_ENDPOINTS
from .media import Media
from .tmdbmatch import TMDBMatch

class TMDBError(Exception):
    pass

class NoMatchError(Exception):
    pass

def TMDB_query(media: "Media", loose_query: bool, token) -> list["TMDBMatch"]:
    url: str = f"{TMDB_URL}{SEARCH_ENDPOINTS[media.kind]}/"
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
    print("Query returned these top matches:")
    for i, match in enumerate(results, start=1):
        print(f"{i}. {match}")

    while True:
        print("Input -1 to cancel.")
        raw = input("Choose an option: ").strip()
        try:
            option = int(raw)
        except ValueError:
            print("Please enter a number.")
            continue
        if -1 <= option <= len(results):
            break
        print(f"Choose a number between -1 and {len(results)}.")
    return option

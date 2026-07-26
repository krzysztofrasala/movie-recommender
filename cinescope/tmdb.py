"""Thin client for the TMDB REST API.

Every HTTP call goes through ``_get``, so timeouts, error handling and
logging live in one place. Responses are cached with Streamlit's cache
to keep the UI responsive and API usage low. All fetchers degrade
gracefully: on any API failure they return ``None`` or an empty list.
"""

from __future__ import annotations

import datetime
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st

logger = logging.getLogger(__name__)

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
PLACEHOLDER_POSTER = "https://placehold.co/500x750/1a1a1a/666666?text=No+Poster"
REQUEST_TIMEOUT = 5
HOUR = 3_600
DAY = 86_400
DEFAULT_REGION = "PL"


def get_api_key() -> str | None:
    """TMDB API key from Streamlit secrets, falling back to the environment."""
    try:
        return st.secrets["TMDB_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("TMDB_API_KEY")


@st.cache_resource
def _session() -> requests.Session:
    """Shared HTTP session so requests reuse connections."""
    return requests.Session()


def _get(path: str, params: dict | None = None) -> dict | None:
    """GET a TMDB endpoint and return parsed JSON, or None on failure."""
    payload = dict(params or {})
    payload["api_key"] = get_api_key()
    if "language" not in payload:
        try:
            from cinescope.i18n import get_tmdb_language
            payload["language"] = get_tmdb_language()
        except Exception:
            payload["language"] = "en-US"
    try:
        response = _session().get(f"{BASE_URL}/{path}", params=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("TMDB GET /%s failed: %s", path, exc)
        return None



def poster_url(path: str | None, size: str = "w500") -> str:
    """Full image URL for a TMDB poster/profile path, with a placeholder fallback."""
    if path and isinstance(path, str):
        return f"{IMAGE_BASE_URL}/{size}{path}"
    return PLACEHOLDER_POSTER


def _movie_summary(m: dict) -> dict:
    """Normalise a TMDB movie/TV list item to the card format used by the UI."""
    return {
        "id": m["id"],
        "title": m.get("title") or m.get("name", ""),
        "year": (m.get("release_date") or m.get("first_air_date") or "")[:4],
        "rating": round(m.get("vote_average", 0), 1),
        "poster": poster_url(m.get("poster_path")),
        "overview": m.get("overview", ""),
    }


_tv_summary = _movie_summary



def _cast_details(cast: list[dict]) -> list[dict]:
    return [
        {"name": c["name"], "character": c.get("character", ""), "photo": poster_url(c.get("profile_path"))}
        for c in cast
    ]


def _first_youtube_trailer(data: dict | None) -> str | None:
    for video in (data or {}).get("results", []):
        if video.get("site") == "YouTube" and video.get("type") == "Trailer":
            return f"https://www.youtube.com/watch?v={video['key']}"
    return None


# ── Movies ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=DAY)
def fetch_movie_details(movie_id: int) -> dict | None:
    """Poster, rating and overview for a single movie."""
    d = _get(f"movie/{movie_id}", {"language": "en-US"})
    if not d:
        return None
    return {
        "poster": poster_url(d.get("poster_path")),
        "rating": round(d.get("vote_average", 0), 1),
        "overview": d.get("overview", ""),
        "id": movie_id,
    }


@st.cache_data(ttl=DAY)
def fetch_movie_extended(movie_id: int) -> dict | None:
    """Credits, genres, runtime and budget for the movie details dialog."""
    d = _get(f"movie/{movie_id}", {"language": "en-US", "append_to_response": "credits"})
    if not d:
        return None
    credits = d.get("credits", {})
    cast = credits.get("cast", [])[:8]
    return {
        "director": next((c["name"] for c in credits.get("crew", []) if c["job"] == "Director"), "Unknown"),
        "cast": [c["name"] for c in cast[:6]],
        "cast_details": _cast_details(cast),
        "genres": [g["name"] for g in d.get("genres", [])],
        "runtime": d.get("runtime") or 0,
        "budget": d.get("budget") or 0,
        "tagline": d.get("tagline", ""),
    }


@st.cache_data(ttl=DAY)
def fetch_movie_trailer(movie_id: int) -> str | None:
    return _first_youtube_trailer(_get(f"movie/{movie_id}/videos", {"language": "en-US"}))


@st.cache_data(ttl=HOUR)
def fetch_trending() -> list[dict]:
    """Raw TMDB payloads for today's 20 trending movies."""
    d = _get("trending/movie/day")
    return d.get("results", [])[:20] if d else []


@st.cache_data(ttl=HOUR)
def fetch_now_playing() -> list[dict]:
    """Raw TMDB payloads for movies currently in cinemas."""
    d = _get("movie/now_playing", {"language": "en-US"})
    return d.get("results", [])[:5] if d else []


@st.cache_data(ttl=DAY)
def fetch_movie_recommendations(movie_id: int) -> list[dict]:
    """TMDB collaborative recommendations — fallback for titles outside the local model."""
    d = _get(f"movie/{movie_id}/recommendations", {"language": "en-US"})
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


@st.cache_data(ttl=DAY)
def fetch_movie_of_the_day() -> dict | None:
    """A deterministic daily pick from TMDB's popular list."""
    d = _get("movie/popular", {"language": "en-US", "page": 1})
    results = d.get("results", []) if d else []
    if not results:
        return None
    m = results[datetime.date.today().timetuple().tm_yday % len(results)]
    return {
        "id": m["id"],
        "title": m["title"],
        "poster": poster_url(m.get("poster_path")),
        "backdrop": f"{IMAGE_BASE_URL}/w1280{m['backdrop_path']}" if m.get("backdrop_path") else None,
        "rating": round(m.get("vote_average", 0), 1),
        "overview": m.get("overview", ""),
    }


@st.cache_data(ttl=HOUR)
def fetch_top_movies(category: str = "popular") -> list[dict]:
    """Top-10 list for a TMDB movie category ('popular' or 'top_rated')."""
    d = _get(f"movie/{category}", {"language": "en-US"})
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


# ── Search ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=HOUR)
def search_movies(query: str) -> list[dict]:
    d = _get("search/movie", {"query": query, "language": "en-US"})
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


@st.cache_data(ttl=HOUR)
def search_tv(query: str) -> list[dict]:
    d = _get("search/tv", {"query": query, "language": "en-US"})
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


@st.cache_data(ttl=HOUR)
def search_person(query: str) -> list[dict]:
    d = _get("search/person", {"query": query, "language": "en-US"})
    if not d:
        return []
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "role": p.get("known_for_department", "Acting"),
            "photo": poster_url(p.get("profile_path")),
            "known_for": [k.get("title", k.get("name", "")) for k in p.get("known_for", [])[:3]],
        }
        for p in d.get("results", [])[:5]
    ]


@st.cache_data(ttl=DAY)
def fetch_person_credits(person_id: int) -> list[dict]:
    """A person's 10 most popular movie/TV credits."""
    d = _get(f"person/{person_id}/combined_credits", {"language": "en-US"})
    if not d:
        return []
    cast = sorted(d.get("cast", []), key=lambda c: c.get("popularity", 0), reverse=True)[:10]
    return [{**_movie_summary(m), "media_type": m.get("media_type", "movie")} for m in cast]


# ── TV shows ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=DAY)
def fetch_tv_extended(tv_id: int) -> dict | None:
    """Credits, seasons and status for the TV details dialog."""
    d = _get(f"tv/{tv_id}", {"language": "en-US", "append_to_response": "credits"})
    if not d:
        return None
    cast = d.get("credits", {}).get("cast", [])[:8]
    episode_runtimes = d.get("episode_run_time", [])
    return {
        "creator": ", ".join(c["name"] for c in d.get("created_by", [])) or "Unknown",
        "cast": [c["name"] for c in cast[:6]],
        "cast_details": _cast_details(cast),
        "genres": [g["name"] for g in d.get("genres", [])],
        "seasons": d.get("number_of_seasons", 0),
        "episodes": d.get("number_of_episodes", 0),
        "runtime": episode_runtimes[0] if episode_runtimes else 0,
        "tagline": d.get("tagline", ""),
        "status": d.get("status", ""),
    }


@st.cache_data(ttl=DAY)
def fetch_tv_trailer(tv_id: int) -> str | None:
    return _first_youtube_trailer(_get(f"tv/{tv_id}/videos", {"language": "en-US"}))


@st.cache_data(ttl=DAY)
def fetch_tv_recommendations(tv_id: int) -> list[dict]:
    d = _get(f"tv/{tv_id}/recommendations", {"language": "en-US"})
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


# ── Discover ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=HOUR)
def discover_by_genre(genre_id: int) -> list[dict]:
    """Most popular movies for a single genre (mood picker)."""
    d = _get("discover/movie", {"with_genres": genre_id, "sort_by": "popularity.desc", "language": "en-US"})
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


@st.cache_data(ttl=HOUR)
def discover_by_decade(start_year: int, end_year: int) -> list[dict]:
    """Most popular movies released within a decade."""
    d = _get("discover/movie", {
        "primary_release_date.gte": f"{start_year}-01-01",
        "primary_release_date.lte": f"{end_year}-12-31",
        "sort_by": "popularity.desc",
        "language": "en-US",
    })
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


@st.cache_data(ttl=HOUR)
def smart_discover(genres: tuple, year_gte: int | None, year_lte: int | None,
                   vote_gte: float | None, sort_by: str) -> list[dict]:
    """Discover movies matching filters parsed from a natural-language query."""
    params: dict = {"sort_by": sort_by, "vote_count.gte": 100, "language": "en-US"}
    if genres:
        params["with_genres"] = ",".join(str(g) for g in genres)
    if year_gte:
        params["primary_release_date.gte"] = f"{year_gte}-01-01"
    if year_lte:
        params["primary_release_date.lte"] = f"{year_lte}-12-31"
    if vote_gte:
        params["vote_average.gte"] = vote_gte
    d = _get("discover/movie", params)
    return [_movie_summary(m) for m in d.get("results", [])[:10]] if d else []


@st.cache_data(ttl=HOUR)
def filtered_discover(
    genres: tuple, 
    year_gte: int | None, 
    year_lte: int | None, 
    runtime_lte: int | None,
    vote_gte: float | None, 
    provider_ids: tuple | None,
    sort_by: str = "popularity.desc",
    primary_release_date_gte: str | None = None,
    primary_release_date_lte: str | None = None,
    with_release_type: str | None = None,
    limit: int = 20
) -> list[dict]:
    """Discover movies matching explicit global UI filters directly via TMDB."""
    params: dict = {"sort_by": sort_by, "vote_count.gte": 50, "language": "en-US"}
    
    if genres:
        params["with_genres"] = ",".join(str(g) for g in genres)
        
    if primary_release_date_gte:
        params["primary_release_date.gte"] = primary_release_date_gte
    elif year_gte:
        params["primary_release_date.gte"] = f"{year_gte}-01-01"
        
    if primary_release_date_lte:
        params["primary_release_date.lte"] = primary_release_date_lte
    elif year_lte:
        params["primary_release_date.lte"] = f"{year_lte}-12-31"
        
    if runtime_lte and runtime_lte < 300:
        params["with_runtime.lte"] = runtime_lte
        
    if vote_gte:
        params["vote_average.gte"] = vote_gte
        
    if provider_ids:
        params["with_watch_providers"] = "|".join(str(p) for p in provider_ids)
        params["watch_region"] = DEFAULT_REGION
        
    if with_release_type:
        params["with_release_type"] = with_release_type
        params["region"] = DEFAULT_REGION
        
    d = _get("discover/movie", params)
    
    if not d:
        return []
        
    results = d.get("results", [])
    valid_movies = []
    
    for m in results:
        # Require a poster path to avoid displaying empty "No Poster" cards
        if m.get("poster_path"):
            valid_movies.append(m)
            
        if len(valid_movies) == limit:
            break
            
    return valid_movies


@st.cache_data(ttl=HOUR)
def fetch_hidden_gems(genre_id: int | None, exclude_ids: tuple) -> list[dict]:
    """Highly-rated movies with modest vote counts — 'hidden gems'."""
    params: dict = {
        "sort_by": "vote_average.desc",
        "vote_count.gte": 50,
        "vote_count.lte": 900,
        "vote_average.gte": 7.2,
        "language": "en-US",
    }
    if genre_id:
        params["with_genres"] = genre_id
    d = _get("discover/movie", params)
    if not d:
        return []
    excluded = set(exclude_ids)
    return [_movie_summary(m) for m in d.get("results", []) if m["id"] not in excluded][:5]


# ── Streaming providers ────────────────────────────────────────────────────────

@st.cache_data(ttl=DAY)
def fetch_providers_list(region: str = DEFAULT_REGION) -> list[dict]:
    """Most relevant streaming providers available in ``region``."""
    d = _get("watch/providers/movie", {"watch_region": region})
    if not d:
        return []
    results = sorted(d.get("results", []), key=lambda p: p.get("display_priority", 999))
    return [
        {"id": p["provider_id"], "name": p["provider_name"], "logo": f"{IMAGE_BASE_URL}/original{p['logo_path']}"}
        for p in results[:20]
        if p.get("logo_path")
    ]


@st.cache_data(ttl=DAY)
def fetch_movie_providers(movie_id: int, region: str = DEFAULT_REGION) -> list[dict]:
    """Streaming providers for a movie in ``region``, including flatrate, rent, and buy."""
    d = _get(f"movie/{movie_id}/watch/providers")
    if not d:
        return []
    
    region_data = d.get("results", {}).get(region, {})
    providers = []
    
    # Combine flatrate, rent, and buy options
    for category in ("flatrate", "rent", "buy"):
        for p in region_data.get(category, []):
            providers.append(
                {"id": p["provider_id"], "name": p["provider_name"], "logo": f"{IMAGE_BASE_URL}/original{p['logo_path']}"}
            )
            
    # Deduplicate providers (a movie might be available to rent and buy on the same platform)
    seen = set()
    unique_providers = []
    for p in providers:
        if p["id"] not in seen and p.get("logo"):
            seen.add(p["id"])
            unique_providers.append(p)
            
    return unique_providers


def fetch_providers_batch(movie_ids: list[int], region: str = DEFAULT_REGION) -> dict[int, list[dict]]:
    """Providers for many movies in parallel; returns {movie_id: providers}."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda mid: fetch_movie_providers(mid, region), movie_ids))
    return dict(zip(movie_ids, results, strict=True))


@st.cache_data(ttl=DAY)
def fetch_movie_trailer(movie_id: int) -> str | None:
    """Fetch YouTube trailer key for a movie or TV show."""
    d = _get(f"movie/{movie_id}/videos")
    if not d or "results" not in d:
        d = _get(f"tv/{movie_id}/videos")
    if not d or "results" not in d:
        return None

    results = d.get("results", [])
    for v in results:
        if v.get("site") == "YouTube" and v.get("type") == "Trailer" and v.get("key"):
            return v.get("key")
    for v in results:
        if v.get("site") == "YouTube" and v.get("key"):
            return v.get("key")
    return None


@st.cache_data(ttl=DAY)
def search_person(query: str) -> list[dict]:
    """Search for actors or directors by name to get person ID."""
    d = _get("search/person", {"query": query})
    if not d:
        return []
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "known_for_department": p.get("known_for_department"),
            "profile_path": poster_url(p.get("profile_path")),
        }
        for p in d.get("results", [])
    ]



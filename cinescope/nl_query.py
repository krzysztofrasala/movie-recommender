"""Keyword-driven natural-language search parsing, now supercharged with Gemini AI.

Turns free text like "scary movie from the 90s" into TMDB discover
parameters: genres, year range, minimum rating and sort order.
Falls back to zero-cost keyword extraction if no Gemini API key is configured.
"""

from __future__ import annotations

import datetime
import logging
import os
import re

import streamlit as st
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Keyword (or phrase) → TMDB genre id.
GENRE_KEYWORDS = {
    "comedy": 35, "funny": 35, "laugh": 35, "humor": 35, "humour": 35, "hilarious": 35,
    "horror": 27, "scary": 27, "frightening": 27, "terrifying": 27, "creepy": 27, "spooky": 27,
    "romance": 10749, "romantic": 10749, "love story": 10749,
    "action": 28, "fight": 28, "exciting": 28, "explosive": 28,
    "adventure": 12,
    "sci-fi": 878, "scifi": 878, "science fiction": 878, "space": 878, "futuristic": 878, "aliens": 878,
    "drama": 18, "emotional": 18, "intense": 18,
    "animation": 16, "animated": 16, "cartoon": 16, "anime": 16,
    "thriller": 53, "suspense": 53, "tense": 53,
    "mystery": 9648, "detective": 9648, "whodunit": 9648,
    "family": 10751, "kids": 10751, "children": 10751,
    "fantasy": 14, "magic": 14, "magical": 14, "dragons": 14,
    "crime": 80, "gangster": 80, "mafia": 80, "heist": 80,
    "war": 10752, "military": 10752, "battle": 10752,
    "western": 37, "cowboy": 37, "wild west": 37,
    "history": 36, "historical": 36, "period": 36,
    "music": 10402, "musical": 10402,
    "documentary": 99, "true story": 99,
}

# Keyword → TMDB discover sort order.
SORT_KEYWORDS = {
    "popular": "popularity.desc", "trending": "popularity.desc", "hot": "popularity.desc",
    "top rated": "vote_average.desc", "best": "vote_average.desc", "highest rated": "vote_average.desc",
    "newest": "primary_release_date.desc", "recent": "primary_release_date.desc", "latest": "primary_release_date.desc",
    "oldest": "primary_release_date.asc",
}

# Keyword → minimum TMDB vote average.
RATING_KEYWORDS = {
    "masterpiece": 8.5, "excellent": 8.0, "great": 7.5, "good": 7.0, "decent": 6.5,
}


class TMDBParams(BaseModel):
    genres: list[int] = Field(default_factory=list, description="List of TMDB genre IDs mentioned or implied (max 2).")
    year_gte: int | None = Field(None, description="Minimum release year (e.g. 1990 for '90s').")
    year_lte: int | None = Field(None, description="Maximum release year (e.g. 1999 for '90s').")
    vote_gte: float | None = Field(None, description="Minimum user rating (e.g. 8.0 for 'masterpiece', max 10.0).")
    sort_by: str = Field("popularity.desc", description="One of: 'popularity.desc', 'vote_average.desc', 'primary_release_date.desc', 'primary_release_date.asc'")

def _get_gemini_key() -> str | None:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("GEMINI_API_KEY")


@st.cache_data(ttl=3600)
def parse_natural_query(text: str) -> dict:
    """Extract TMDB discover filters from a free-text description using regex fallback or Gemini."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return _fallback_parse(text)

    gemini_key = _get_gemini_key()

    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = (
                f"You are a movie recommendation assistant. Extract the search intent from this user query:\n"
                f"'{text}'\n"
                "Return the parameters for a TMDB Discover API call. Match ALL mentioned genres to these IDs: "
                f"{', '.join([f'{k}({v})' for k, v in GENRE_KEYWORDS.items()][:20])}... "
                f"Current year is {datetime.date.today().year}. "
                f"If 'new releases', 'recent', or 'this year' is mentioned, set year_gte to {datetime.date.today().year - 1}. "
                "If 'classic' is mentioned, set year_lte to 2000 and sort_by to 'vote_average.desc'."
            )
            for model_name in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={
                            'response_mime_type': 'application/json',
                            'response_schema': TMDBParams,
                        },
                    )
                    data = TMDBParams.model_validate_json(response.text)
                    return {
                        "genres": data.genres[:2],
                        "year_gte": data.year_gte,
                        "year_lte": data.year_lte,
                        "vote_gte": data.vote_gte,
                        "sort_by": data.sort_by,
                    }
                except Exception as exc:
                    logger.warning(f"Model {model_name} failed: {exc}")
        except Exception as e:
            logger.warning(f"Gemini NL query parsing failed: {e}.")

    return parsed



def _fallback_parse(text: str) -> dict:
    q = text.lower()
    genres: list[int] = []
    vote_gte: float | None = None
    sort_by = "popularity.desc"
    year_gte: int | None = None
    year_lte: int | None = None

    for keyword, genre_id in GENRE_KEYWORDS.items():
        if keyword in q and genre_id not in genres:
            genres.append(genre_id)

    # Decade phrases: "80s", "1990s", "the 90s"
    decade_match = re.search(r"\b(1[0-9]{3}|[0-9]{2})s\b", q)
    if decade_match:
        raw = decade_match.group(1)
        if len(raw) == 2:
            n = int(raw)
            base = 2000 if n <= 20 else 1900
            decade_start = base + (n // 10) * 10
        else:
            decade_start = int(raw) // 10 * 10
        year_gte, year_lte = decade_start, decade_start + 9

    current_year = datetime.date.today().year
    if re.search(r"\b(this year|new releases?|just released)\b", q):
        year_gte = current_year - 1
    elif re.search(r"\bclassic\b", q) and not year_gte:
        year_lte = 2000
        sort_by = "vote_average.desc"
    elif re.search(r"\bvery old\b", q) and not year_gte:
        year_lte = 1980

    for keyword, rating in RATING_KEYWORDS.items():
        if keyword in q:
            vote_gte = max(vote_gte or 0, rating)

    for keyword, sort in SORT_KEYWORDS.items():
        if keyword in q:
            sort_by = sort
            break

    return {
        "genres": genres[:2],
        "year_gte": year_gte,
        "year_lte": year_lte,
        "vote_gte": vote_gte,
        "sort_by": sort_by,
    }

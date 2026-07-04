"""Loading and filtering of the local movie dataset and similarity model."""

from __future__ import annotations

import ast
import pickle

import pandas as pd
import streamlit as st

MOVIE_DICT_FILE = "movie_dict.pkl"
SIMILARITY_FILE = "similarity.pkl"
MOVIES_CSV_FILE = "movies.csv"


class ModelLoadError(RuntimeError):
    """Raised when the pickled model files are missing or unreadable."""


def parse_genres(genres_str) -> list[str]:
    """Parse the stringified TMDB genre list stored in movies.csv."""
    try:
        return [g["name"] for g in ast.literal_eval(genres_str)]
    except (ValueError, SyntaxError, TypeError, KeyError):
        return []


@st.cache_resource
def load_model():
    """Load the movie dataframe and similarity matrix built by fetch_dataset.py."""
    try:
        with open(MOVIE_DICT_FILE, "rb") as f:
            movies = pd.DataFrame(pickle.load(f))
        with open(SIMILARITY_FILE, "rb") as f:
            similarity = pickle.load(f)
        raw = pd.read_csv(MOVIES_CSV_FILE)[["id", "genres", "release_date"]]
    except Exception as exc:
        raise ModelLoadError(str(exc)) from exc

    raw["year"] = pd.to_datetime(raw["release_date"], errors="coerce").dt.year.astype("Int64")
    raw["genres_list"] = raw["genres"].apply(parse_genres)
    raw = raw.rename(columns={"id": "movie_id"})
    movies = movies.merge(raw[["movie_id", "year", "genres_list"]], on="movie_id", how="left")
    return movies, similarity


def get_movies() -> pd.DataFrame:
    return load_model()[0]


def get_similarity():
    return load_model()[1]


@st.cache_resource
def _genre_lookup() -> dict[str, list[str]]:
    return {
        row.title: (row.genres_list[:3] if isinstance(row.genres_list, list) else [])
        for row in get_movies().itertuples()
    }


def get_local_genres(title: str) -> list[str]:
    """Genres for a movie in the local dataset (empty list if unknown)."""
    return _genre_lookup().get(title, [])


@st.cache_data
def apply_filters(genres: tuple, year_min: int, year_max: int) -> pd.DataFrame:
    """Filter the local library by genre membership and release-year range."""
    df = get_movies()
    if genres:
        df = df[df["genres_list"].apply(lambda g: isinstance(g, list) and any(x in g for x in genres))]
    return df[df["year"].notna() & (df["year"] >= year_min) & (df["year"] <= year_max)]


def all_genres() -> list[str]:
    return sorted({g for genres in get_movies()["genres_list"].dropna() for g in genres})


def year_bounds() -> tuple[int, int]:
    years = get_movies()["year"].dropna()
    return int(years.min()), int(years.max())

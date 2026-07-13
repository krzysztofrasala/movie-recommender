"""Loading and filtering of the local movie dataset and similarity model."""

from __future__ import annotations

import ast
import pickle

import numpy as np
import pandas as pd
import streamlit as st
from scipy import sparse

MOVIE_DICT_FILE = "movie_dict.pkl"
NEIGHBORS_FILE = "neighbors.pkl"
VECTORS_FILE = "vectors.npz"
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
    """Load the movie dataframe, neighbor lists and tag vectors built by fetch_dataset.py."""
    try:
        with open(MOVIE_DICT_FILE, "rb") as f:
            movies = pd.DataFrame(pickle.load(f))
        with open(NEIGHBORS_FILE, "rb") as f:
            neighbors = pickle.load(f)
            
        try:
            vectors = sparse.load_npz(VECTORS_FILE)
            is_dense = False
        except ValueError:
            # Fallback to dense numpy array if saved with np.savez
            vectors_data = np.load(VECTORS_FILE)
            vectors = vectors_data["embeddings"] if "embeddings" in vectors_data else vectors_data["arr_0"]
            is_dense = True
            
        csv_cols = ["id", "genres", "release_date"]
        raw = pd.read_csv(MOVIES_CSV_FILE)
    except Exception as exc:
        raise ModelLoadError(str(exc)) from exc

    raw["year"] = pd.to_datetime(raw.get("release_date"), errors="coerce").dt.year.astype("Int64")
    raw["genres_list"] = raw.get("genres", "[]").apply(parse_genres)
    raw = raw.rename(columns={"id": "movie_id"})
    
    # Safely get runtime and rating if they exist in the CSV (added in recent version)
    merge_cols = ["movie_id", "year", "genres_list"]
    if "runtime" in raw.columns:
        merge_cols.append("runtime")
    if "vote_average" in raw.columns:
        merge_cols.append("vote_average")
        
    movies = movies.merge(raw[merge_cols], on="movie_id", how="left")
    
    # Fill defaults for missing data
    if "runtime" not in movies.columns:
        movies["runtime"] = 0
    if "vote_average" not in movies.columns:
        movies["vote_average"] = 0.0
        
    return movies, neighbors, vectors, is_dense


def get_movies() -> pd.DataFrame:
    return load_model()[0]


def get_neighbors() -> dict[str, np.ndarray]:
    """Precomputed top-K similar movies: {'indices': (N, K) int32, 'scores': (N, K) float32}."""
    return load_model()[1]


def pair_similarity(idx1: int, idx2: int) -> float:
    """Cosine similarity between two movies' tag vectors (0..1), computed on demand."""
    _, _, vectors, is_dense = load_model()
    v1, v2 = vectors[idx1], vectors[idx2]
    
    if is_dense:
        denom = float(np.linalg.norm(v1) * np.linalg.norm(v2))
        if denom == 0.0:
            return 0.0
        return float(np.dot(v1, v2)) / denom
    else:
        denom = float(np.sqrt(v1.multiply(v1).sum()) * np.sqrt(v2.multiply(v2).sum()))
        if denom == 0.0:
            return 0.0
        return float(v1.multiply(v2).sum()) / denom


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
def apply_filters(genres: tuple, year_min: int | None = None, year_max: int | None = None, runtime_max: int | None = None, vote_min: float | None = None) -> pd.DataFrame:
    """Filter the local library by genre membership, release-year range, max runtime, and min rating."""
    df = get_movies()
    if genres:
        df = df[df["genres_list"].apply(lambda g: isinstance(g, list) and any(x in g for x in genres))]
    
    mask = pd.Series(True, index=df.index)
    if year_min is not None:
        mask &= df["year"].notna() & (df["year"] >= year_min)
    if year_max is not None:
        mask &= df["year"].notna() & (df["year"] <= year_max)
    
    if runtime_max is not None:
        mask &= (df["runtime"] > 0) & (df["runtime"] <= runtime_max)
        
    if vote_min is not None:
        mask &= (df["vote_average"] >= vote_min)
        
    return df[mask]


def all_genres() -> list[str]:
    return sorted({g for genres in get_movies()["genres_list"].dropna() for g in genres})


def year_bounds() -> tuple[int, int]:
    years = get_movies()["year"].dropna()
    return int(years.min()), int(years.max())

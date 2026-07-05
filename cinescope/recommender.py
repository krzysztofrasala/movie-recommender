"""Content-based recommendation logic on top of the local similarity model."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from cinescope import data, tmdb

TOP_N = 10
MIN_STARS_FOR_PROFILE = 3  # st.feedback stars are 0-4; >=3 means a 4-5 star rating


def recommend(title: str) -> list[dict]:
    """Top-N most similar local movies to ``title``, enriched with TMDB details."""
    movies = data.get_movies()
    neighbor_indices = data.get_neighbors()["indices"]
    idx = movies[movies["title"] == title].index[0]
    candidates = [(movies.iloc[i].movie_id, movies.iloc[i].title) for i in neighbor_indices[idx][:TOP_N]]

    def fetch_one(candidate: tuple) -> dict | None:
        movie_id, movie_title = candidate
        details = tmdb.fetch_movie_details(movie_id)
        if details:
            details["title"] = movie_title
        return details

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_one, candidates))
    return [r for r in results if r]


def more_like_this(movie_id: int, movie_title: str) -> list[dict]:
    """Local content-based recs when the title is in the dataset, TMDB fallback otherwise."""
    movies = data.get_movies()
    local = movies[movies["title"].str.lower() == movie_title.lower()]
    if local.empty:
        return tmdb.fetch_movie_recommendations(movie_id)
    return recommend(local.iloc[0]["title"])


def recommend_for_you() -> list[dict]:
    """Blend recommendations seeded by the user's highest-rated movies."""
    good = {
        movie_id: info
        for movie_id, info in st.session_state.rated_movies_info.items()
        if st.session_state.user_ratings.get(movie_id, 0) >= MIN_STARS_FOR_PROFILE
    }
    if not good:
        return []
    movies = data.get_movies()
    seen, combined = set(good.keys()), []
    for _movie_id, info in list(good.items())[:3]:
        local = movies[movies["title"].str.lower() == info["title"].lower()]
        if local.empty:
            continue
        for rec in recommend(local.iloc[0]["title"]):
            if rec["id"] not in seen:
                seen.add(rec["id"])
                combined.append(rec)
    return combined[:TOP_N]

"""Taste-DNA profiling: genre/decade affinity scores and viewer personas."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from cinescope import data

# (genres that must all rank in the user's top 3, persona) — order matters:
# more specific combinations come first.
PERSONAS = [
    (["Horror", "Thriller"],        ("🌑", "The Dark Mind",         "You thrive in psychological tension and shadowy narratives.")),
    (["Action", "Thriller"],        ("🎯", "The Adrenaline Hunter", "Nothing gets your blood pumping like high-octane cinema.")),
    (["Drama", "Romance"],          ("🌹", "The Hopeless Romantic", "You believe every great story deserves a love at its center.")),
    (["Science Fiction", "Action"], ("🚀", "The Future Voyager",    "You boldly go where no film has gone before.")),
    (["Crime", "Drama"],            ("🕵️", "The Truth Seeker",      "Obsessed with the human cost of decisions — right or wrong.")),
    (["Animation", "Family"],       ("🎠", "The Eternal Child",     "Young at heart, and that will never change.")),
    (["Comedy"],                    ("😂", "The Laughter Seeker",   "Life's too short to take too seriously.")),
    (["Science Fiction"],           ("🛸", "The Visionary",         "Fascinated by what could be, not just what is.")),
    (["Horror"],                    ("👻", "The Thrill Chaser",     "Fear is just excitement in disguise.")),
    (["Action", "Adventure"],       ("💥", "The Epic Action Fan",   "Bigger, louder, faster — bring it on.")),
    (["History", "Drama"],          ("📜", "The Time Traveler",     "Finds the present by exploring the past.")),
    (["Adventure", "Fantasy"],      ("⚔️", "The Epic Dreamer",      "Born for grand journeys and impossible worlds.")),
    (["Drama"],                     ("🎭", "The Deep Thinker",      "Every film is a window into the human condition.")),
]

FALLBACK_PERSONA = ("🎬", "The Movie Lover", "A true cinephile with eclectic taste.")

WATCHLIST_WEIGHT = 0.4  # watchlisting signals interest, but weaker than a rating


def get_taste_profile() -> tuple[dict[str, float], dict[int, float]]:
    """Aggregate genre and decade affinity scores from ratings and the watchlist."""
    genre_scores: dict[str, float] = {}
    decade_scores: dict[int, float] = {}
    movies = data.get_movies()

    for movie_id, info in st.session_state.rated_movies_info.items():
        stars = st.session_state.user_ratings.get(movie_id, 2) + 1  # feedback widget is 0-4
        weight = stars / 3.0
        for genre in data.get_local_genres(info["title"]):
            genre_scores[genre] = genre_scores.get(genre, 0) + weight
        local = movies[movies["title"].str.lower() == info["title"].lower()]
        if not local.empty:
            year = local.iloc[0].get("year")
            if pd.notna(year):
                decade = (int(year) // 10) * 10
                decade_scores[decade] = decade_scores.get(decade, 0) + weight

    for item in st.session_state.watchlist:
        for genre in data.get_local_genres(item["title"]):
            genre_scores[genre] = genre_scores.get(genre, 0) + WATCHLIST_WEIGHT

    return genre_scores, decade_scores


def assign_persona(genre_scores: dict[str, float]) -> tuple[str, str, str] | None:
    """Match the user's top genres to a named persona."""
    if not genre_scores:
        return None
    top = sorted(genre_scores, key=genre_scores.get, reverse=True)[:3]
    for genres, persona in PERSONAS:
        if all(g in top for g in genres):
            return persona
    for genres, persona in PERSONAS:
        if genres[0] in top:
            return persona
    return FALLBACK_PERSONA

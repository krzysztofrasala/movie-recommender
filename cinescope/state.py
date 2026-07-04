"""Session-state initialisation and user data (watchlist, ratings, history)."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

WATCHLIST_FILE = Path(".watchlist.json")
MAX_SEARCH_HISTORY = 10


def _load_watchlist() -> list[dict]:
    if not WATCHLIST_FILE.exists():
        return []
    try:
        return json.loads(WATCHLIST_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return []


def _save_watchlist() -> None:
    try:
        WATCHLIST_FILE.write_text(json.dumps(st.session_state.watchlist))
    except OSError:
        pass  # persistence is best-effort; the in-memory copy stays valid


def init() -> None:
    """Populate st.session_state with defaults on first run."""
    defaults = {
        "trending_index": 0,
        "recommendations": [],
        "rec_source": None,
        "user_ratings": {},
        "rated_movies_info": {},
        "search_history": [],
        "selected_person_id": None,
        "selected_person_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = _load_watchlist()


def add_to_watchlist(title: str, poster: str, rating: float) -> bool:
    """Add a movie to the watchlist. Returns False if it is already there."""
    if any(m["title"] == title for m in st.session_state.watchlist):
        return False
    st.session_state.watchlist.append({"title": title, "poster": poster, "rating": rating})
    _save_watchlist()
    return True


def remove_from_watchlist(title: str) -> None:
    st.session_state.watchlist = [m for m in st.session_state.watchlist if m["title"] != title]
    _save_watchlist()


def set_recommendations(recs: list[dict], source_title: str) -> None:
    """Store a recommendation set and remember its source in search history."""
    st.session_state.recommendations = recs
    st.session_state.rec_source = source_title
    history = [h for h in st.session_state.search_history if h != source_title]
    history.insert(0, source_title)
    st.session_state.search_history = history[:MAX_SEARCH_HISTORY]

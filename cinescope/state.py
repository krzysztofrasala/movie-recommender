"""Session-state initialisation and user data (watchlist, ratings, history).

The watchlist is per-visitor: it lives in ``st.session_state`` during a
session and is persisted to the browser's localStorage so it survives
page reloads. Nothing is written server-side, so visitors never share
each other's data — unlike a single JSON file on the server would.
"""

from __future__ import annotations

import json

import streamlit as st
from streamlit_local_storage import LocalStorage

MAX_SEARCH_HISTORY = 10

# localStorage integration keys.
_LS_COMPONENT_KEY = "cinescope_local_storage"
_WATCHLIST_ITEM = "cinescope_watchlist"


def _local_storage() -> LocalStorage:
    """Handle to the visitor's browser localStorage (mounted once per session)."""
    return LocalStorage(key=_LS_COMPONENT_KEY)


def _load_watchlist() -> list[dict]:
    """Read the watchlist from the visitor's browser localStorage."""
    try:
        raw = _local_storage().getItem(_WATCHLIST_ITEM)
    except Exception:
        return []
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []


def persist_watchlist() -> None:
    """Write the watchlist to localStorage if it changed since the last write.

    Must be called from the main script body (not from a button handler that
    triggers ``st.rerun()``): the localStorage component only runs its browser
    write when it is present in the run that is actually rendered, so a
    component mounted right before a rerun would be torn down before it fires.
    """
    signature = json.dumps(st.session_state.watchlist)
    if st.session_state.get("_watchlist_signature") == signature:
        return
    try:
        _local_storage().setItem(_WATCHLIST_ITEM, signature, key="ls_set_watchlist")
        st.session_state._watchlist_signature = signature
    except Exception:
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
    return True


def remove_from_watchlist(title: str) -> None:
    st.session_state.watchlist = [m for m in st.session_state.watchlist if m["title"] != title]


def set_recommendations(recs: list[dict], source_title: str, add_to_history: bool = True) -> None:
    """Store a recommendation set and optionally remember its source in search history."""
    st.session_state.recommendations = recs
    st.session_state.rec_source = source_title

    if add_to_history:
        history = [h for h in st.session_state.search_history if h != source_title]
        history.insert(0, source_title)
        st.session_state.search_history = history[:MAX_SEARCH_HISTORY]


def export_user_data_json() -> str:
    """Serialize the user's watchlist, ratings and rated_movies_info into JSON format."""
    payload = {
        "version": "1.0",
        "watchlist": st.session_state.get("watchlist", []),
        "user_ratings": st.session_state.get("user_ratings", {}),
        "rated_movies_info": st.session_state.get("rated_movies_info", {}),
    }
    return json.dumps(payload, indent=2)


def import_user_data_json(json_str: str) -> bool:
    """Parse JSON string and restore watchlist and user ratings. Returns True on success."""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return False
        if "watchlist" in data and isinstance(data["watchlist"], list):
            st.session_state.watchlist = data["watchlist"]
        if "user_ratings" in data and isinstance(data["user_ratings"], dict):
            parsed_ratings = {}
            for k, v in data["user_ratings"].items():
                try:
                    parsed_ratings[int(k)] = int(v)
                except ValueError:
                    parsed_ratings[k] = v
            st.session_state.user_ratings = parsed_ratings
        if "rated_movies_info" in data and isinstance(data["rated_movies_info"], dict):
            parsed_info = {}
            for k, v in data["rated_movies_info"].items():
                try:
                    parsed_info[int(k)] = v
                except ValueError:
                    parsed_info[k] = v
            st.session_state.rated_movies_info = parsed_info
        return True
    except (TypeError, ValueError, json.JSONDecodeError):
        return False


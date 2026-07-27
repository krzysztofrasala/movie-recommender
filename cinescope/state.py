"""Session-state initialisation, multi-user profiles, and user data (watchlist, ratings, history).

The watchlist and ratings are stored per-profile in ``st.session_state`` during a
session and persisted per-profile.
"""

from __future__ import annotations

import json

import streamlit as st
from streamlit_local_storage import LocalStorage

MAX_SEARCH_HISTORY = 10
DEFAULT_PROFILES = ["Krzysztof", "Partnerka", "Rodzina"]

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


def _sync_active_profile_to_session() -> None:
    active = st.session_state.get("active_profile", "Krzysztof")
    profiles = st.session_state.get("profiles", {})
    prof_data = profiles.get(active)
    if not prof_data:
        prof_data = {
            "watchlist": [],
            "user_ratings": {},
            "rated_movies_info": {},
            "search_history": [],
        }
        profiles[active] = prof_data

    st.session_state["watchlist"] = prof_data["watchlist"]
    st.session_state["user_ratings"] = prof_data["user_ratings"]
    st.session_state["rated_movies_info"] = prof_data["rated_movies_info"]
    st.session_state["search_history"] = prof_data["search_history"]


def init() -> None:
    """Populate st.session_state with defaults on first run."""
    defaults = {
        "trending_index": 0,
        "recommendations": [],
        "rec_source": None,
        "selected_person_id": None,
        "selected_person_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "profiles" not in st.session_state:
        st.session_state["profiles"] = {
            p: {
                "watchlist": _load_watchlist() if p == "Krzysztof" else [],
                "user_ratings": {},
                "rated_movies_info": {},
                "search_history": [],
            }
            for p in DEFAULT_PROFILES
        }
    if "active_profile" not in st.session_state:
        st.session_state["active_profile"] = "Krzysztof"

    _sync_active_profile_to_session()


def switch_profile(profile_name: str) -> None:
    profiles = st.session_state.get("profiles", {})
    if profile_name in profiles:
        st.session_state["active_profile"] = profile_name
        _sync_active_profile_to_session()


def add_profile(profile_name: str) -> bool:
    name = profile_name.strip()
    profiles = st.session_state.get("profiles", {})
    if not name or name in profiles:
        return False
    profiles[name] = {
        "watchlist": [],
        "user_ratings": {},
        "rated_movies_info": {},
        "search_history": [],
    }
    st.session_state["active_profile"] = name
    _sync_active_profile_to_session()
    return True


def delete_profile(profile_name: str) -> bool:
    profiles = st.session_state.get("profiles", {})
    if profile_name in profiles and len(profiles) > 1:
        del profiles[profile_name]
        st.session_state["active_profile"] = list(profiles.keys())[0]
        _sync_active_profile_to_session()
        return True
    return False


def persist_watchlist() -> None:
    """Write the active profile's watchlist to localStorage."""
    try:
        watchlist = st.session_state.get("watchlist", [])
        signature = json.dumps(watchlist)
        if st.session_state.get("_watchlist_signature") == signature:
            return
        _local_storage().setItem(_WATCHLIST_ITEM, signature, key="ls_set_watchlist")
        st.session_state["_watchlist_signature"] = signature
    except Exception:
        pass


def add_to_watchlist(title: str, poster: str, rating: float) -> bool:
    """Add a movie to the active profile's watchlist."""
    watchlist = st.session_state.get("watchlist", [])
    if any(m["title"] == title for m in watchlist):
        return False
    watchlist.append({"title": title, "poster": poster, "rating": rating})
    st.session_state["watchlist"] = watchlist
    return True


def remove_from_watchlist(title: str) -> None:
    """Remove a movie from the active profile's watchlist."""
    watchlist = [m for m in st.session_state.get("watchlist", []) if m["title"] != title]
    st.session_state["watchlist"] = watchlist
    active = st.session_state.get("active_profile")
    profiles = st.session_state.get("profiles")
    if active and profiles and active in profiles:
        profiles[active]["watchlist"] = watchlist


def set_recommendations(recs: list[dict], source_title: str, add_to_history: bool = True) -> None:
    """Store a recommendation set and optionally remember its source in active profile's history."""
    st.session_state["recommendations"] = recs
    st.session_state["rec_source"] = source_title

    if add_to_history:
        history = [h for h in st.session_state.get("search_history", []) if h != source_title]
        history.insert(0, source_title)
        st.session_state["search_history"] = history[:MAX_SEARCH_HISTORY]
        active = st.session_state.get("active_profile")
        profiles = st.session_state.get("profiles")
        if active and profiles and active in profiles:
            profiles[active]["search_history"] = st.session_state["search_history"]


def export_user_data_json() -> str:
    """Serialize all profiles into JSON format."""
    active = st.session_state.get("active_profile", "Krzysztof")
    profiles = st.session_state.get("profiles")
    if not profiles:
        profiles = {
            active: {
                "watchlist": st.session_state.get("watchlist", []),
                "user_ratings": st.session_state.get("user_ratings", {}),
                "rated_movies_info": st.session_state.get("rated_movies_info", {}),
                "search_history": st.session_state.get("search_history", []),
            }
        }

    payload = {
        "version": "2.0",
        "active_profile": active,
        "profiles": profiles,
    }
    return json.dumps(payload, indent=2)


def import_user_data_json(json_str: str) -> bool:
    """Parse JSON string and restore profiles. Returns True on success."""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return False

        def _parse_ratings(ratings_dict: dict) -> dict:
            res = {}
            for k, v in ratings_dict.items():
                try:
                    res[int(k)] = int(v) if str(v).isdigit() else v
                except ValueError:
                    res[k] = v
            return res

        def _parse_info(info_dict: dict) -> dict:
            res = {}
            for k, v in info_dict.items():
                try:
                    res[int(k)] = v
                except ValueError:
                    res[k] = v
            return res

        if "profiles" in data and isinstance(data["profiles"], dict):
            parsed_profiles = {}
            for pname, pval in data["profiles"].items():
                parsed_profiles[pname] = {
                    "watchlist": pval.get("watchlist", []),
                    "user_ratings": _parse_ratings(pval.get("user_ratings", {})),
                    "rated_movies_info": _parse_info(pval.get("rated_movies_info", {})),
                    "search_history": pval.get("search_history", []),
                }
            st.session_state["profiles"] = parsed_profiles
            if "active_profile" in data and data["active_profile"] in parsed_profiles:
                st.session_state["active_profile"] = data["active_profile"]
            else:
                st.session_state["active_profile"] = list(parsed_profiles.keys())[0]
            _sync_active_profile_to_session()
            return True
        elif "watchlist" in data:
            active = st.session_state.get("active_profile", "Krzysztof")
            if "profiles" not in st.session_state or not isinstance(st.session_state["profiles"], dict):
                st.session_state["profiles"] = {}
            st.session_state.profiles[active] = {
                "watchlist": data.get("watchlist", []),
                "user_ratings": _parse_ratings(data.get("user_ratings", {})),
                "rated_movies_info": _parse_info(data.get("rated_movies_info", {})),
                "search_history": [],
            }
            st.session_state["active_profile"] = active
            _sync_active_profile_to_session()
            return True
        return False
    except (TypeError, ValueError, json.JSONDecodeError):
        return False

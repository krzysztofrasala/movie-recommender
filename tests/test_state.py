"""Tests for state mutation helpers (watchlist, search history).

Streamlit's session_state is stubbed with a plain dict so we can test
the pure logic without spinning up a Streamlit runtime.
"""

from __future__ import annotations

import pytest

from cinescope import state


@pytest.fixture(autouse=True)
def clean_session_state(monkeypatch):
    """Replace st.session_state with a dict-like stand-in for each test."""
    class DictState(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError as exc:
                raise AttributeError(name) from exc

        def __setattr__(self, name, value):
            self[name] = value

    fake = DictState()
    fake["watchlist"] = []
    fake["search_history"] = []
    monkeypatch.setattr(state.st, "session_state", fake)
    return fake


def test_add_new_movie_returns_true(clean_session_state):
    assert state.add_to_watchlist("Inception", "poster.jpg", 8.4) is True
    assert clean_session_state["watchlist"] == [
        {"title": "Inception", "poster": "poster.jpg", "rating": 8.4},
    ]


def test_add_duplicate_returns_false_and_does_not_grow_list(clean_session_state):
    """Adding the same title twice must be idempotent."""
    state.add_to_watchlist("Inception", "p1", 8.4)
    assert state.add_to_watchlist("Inception", "p2", 8.4) is False
    assert len(clean_session_state["watchlist"]) == 1


def test_remove_from_watchlist(clean_session_state):
    state.add_to_watchlist("A", "p", 7.0)
    state.add_to_watchlist("B", "p", 7.0)
    state.remove_from_watchlist("A")
    assert [m["title"] for m in clean_session_state["watchlist"]] == ["B"]


def test_remove_missing_title_is_a_noop(clean_session_state):
    """Never raise: UI may race between clicks and reruns."""
    state.add_to_watchlist("A", "p", 7.0)
    state.remove_from_watchlist("Nonexistent")
    assert len(clean_session_state["watchlist"]) == 1


def test_set_recommendations_moves_source_to_front_of_history(clean_session_state):
    """Re-searching an old query should promote it, not duplicate it."""
    state.set_recommendations([], "Dune")
    state.set_recommendations([], "Oppenheimer")
    state.set_recommendations([], "Dune")
    assert clean_session_state["search_history"] == ["Dune", "Oppenheimer"]


def test_search_history_capped(clean_session_state):
    for i in range(state.MAX_SEARCH_HISTORY + 5):
        state.set_recommendations([], f"Movie {i}")
    assert len(clean_session_state["search_history"]) == state.MAX_SEARCH_HISTORY


def test_export_import_user_data_json(clean_session_state):
    clean_session_state["user_ratings"] = {101: 4}
    clean_session_state["rated_movies_info"] = {101: {"title": "Inception", "poster": "p.jpg"}}
    state.add_to_watchlist("Interstellar", "p2.jpg", 8.6)

    exported = state.export_user_data_json()
    assert "Inception" in exported
    assert "Interstellar" in exported

    # Clear state and restore
    clean_session_state["watchlist"] = []
    clean_session_state["user_ratings"] = {}
    clean_session_state["rated_movies_info"] = {}

    success = state.import_user_data_json(exported)
    assert success is True
    assert len(clean_session_state["watchlist"]) == 1
    assert clean_session_state["watchlist"][0]["title"] == "Interstellar"
    assert clean_session_state["user_ratings"].get(101) == 4


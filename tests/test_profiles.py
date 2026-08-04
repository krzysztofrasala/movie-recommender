"""Tests for multi-user profiles management in cinescope.state."""

from __future__ import annotations

import pytest
import streamlit as st

from cinescope import state


@pytest.fixture(autouse=True)
def mock_session_state(monkeypatch):
    store = {}
    monkeypatch.setattr(st, "session_state", store)
    return store


def test_profile_initialization():
    state.init()
    assert "profiles" in st.session_state
    assert "User" in st.session_state["profiles"]
    assert st.session_state["active_profile"] == "User"


def test_profile_switching():
    state.init()
    state.add_to_watchlist("Dune", "poster.jpg", 8.5)
    assert len(st.session_state["watchlist"]) == 1

    state.add_profile("SecondaryUser")
    state.switch_profile("SecondaryUser")
    assert st.session_state["active_profile"] == "SecondaryUser"
    assert len(st.session_state["watchlist"]) == 0

    state.add_to_watchlist("Oppenheimer", "oppen.jpg", 9.0)
    assert len(st.session_state["watchlist"]) == 1

    state.switch_profile("User")
    assert len(st.session_state["watchlist"]) == 1
    assert st.session_state["watchlist"][0]["title"] == "Dune"


def test_add_and_delete_profile():
    state.init()
    assert state.add_profile("Dzieci") is True
    assert st.session_state["active_profile"] == "Dzieci"

    # Cannot add duplicate
    assert state.add_profile("Dzieci") is False

    assert state.delete_profile("Dzieci") is True
    assert st.session_state["active_profile"] != "Dzieci"


def test_export_import_multi_profiles():
    state.init()
    state.add_profile("TestUser")
    state.add_to_watchlist("Inception", "inc.jpg", 8.8)

    json_str = state.export_user_data_json()
    assert "TestUser" in json_str

    # Clear state
    st.session_state["profiles"] = {}
    assert state.import_user_data_json(json_str) is True
    assert "TestUser" in st.session_state["profiles"]

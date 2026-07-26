"""Tests for the internationalization (i18n) module."""

from __future__ import annotations

from cinescope import i18n


def test_default_language_is_pl(monkeypatch):
    import streamlit as st
    monkeypatch.setattr(st, "session_state", {})
    assert i18n.get_lang() == "PL"
    assert i18n.get_tmdb_language() == "pl-PL"
    assert i18n.t("nav_home") == "🏠 Strona Główna"


def test_switch_language_to_en(monkeypatch):
    import streamlit as st
    monkeypatch.setattr(st, "session_state", {"lang": "EN"})
    assert i18n.get_lang() == "EN"
    assert i18n.get_tmdb_language() == "en-US"
    assert i18n.t("nav_home") == "🏠 Home"

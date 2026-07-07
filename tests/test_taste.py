"""Tests for taste-DNA persona assignment (pure function over genre scores)."""

from __future__ import annotations

from cinescope.taste import FALLBACK_PERSONA, assign_persona


def test_empty_scores_returns_none():
    """No signal → no persona (the UI shows an empty state instead)."""
    assert assign_persona({}) is None


def test_dark_mind_persona_requires_both_horror_and_thriller():
    """Combination personas need every listed genre in the top three."""
    persona = assign_persona({"Horror": 5, "Thriller": 4, "Drama": 3})
    assert persona[1] == "The Dark Mind"


def test_horror_only_falls_through_to_thrill_chaser():
    """Single-genre personas fire when no combination matches."""
    persona = assign_persona({"Horror": 10, "Drama": 1})
    assert persona[1] == "The Thrill Chaser"


def test_combination_beats_single_genre_persona():
    """PERSONAS list order is intentional: multi-genre entries win."""
    persona = assign_persona({"Horror": 5, "Thriller": 4})
    assert persona[1] == "The Dark Mind"  # not "The Thrill Chaser"


def test_unknown_genre_falls_back():
    """A genre outside PERSONAS still returns the generic movie lover."""
    persona = assign_persona({"Documentary": 3})
    assert persona == FALLBACK_PERSONA


def test_persona_shape_is_emoji_name_description():
    """UI expects a 3-tuple; guard against future refactor breaking it."""
    persona = assign_persona({"Comedy": 5})
    assert isinstance(persona, tuple) and len(persona) == 3
    emoji, name, description = persona
    assert emoji and name and description

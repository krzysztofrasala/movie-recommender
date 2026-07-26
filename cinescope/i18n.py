"""Internationalization (i18n) module for Polish (PL) and English (EN) language support."""

from __future__ import annotations

import streamlit as st

TRANSLATIONS: dict[str, dict[str, str]] = {
    "PL": {
        "app_title": "🎬 CineScope",
        "app_tagline": "Odkrywaj filmy i seriale, które pokochasz · Powered by TMDB",
        "nav_home": "🏠 Strona Główna",
        "nav_library": "📽️ Moja Biblioteka",
        "nav_search": "🔍 Szukaj & Odkrywaj Pro",
        "nav_top10": "🏆 Top 10",
        "nav_compare": "⚖️ Porównaj",
        "nav_taste": "🧬 Taste DNA",
        "nav_assistant": "💬 Asystent AI",
        "nav_roulette": "🎲 Filmowa Ruletka",
        "filter_genre": "🎭 Gatunek",
        "filter_streaming": "📺 Platformy Streamingowe",
        "filter_language": "🌐 Język / Language",
        "settings_backup": "⚙️ Ustawienia i Kopia Zapasowa",
        "export_data": "📥 Eksportuj Dane (JSON)",
        "restore_data": "📤 Przywróć Kopię Zapasową (.json)",
        "watchlist_empty": "Brak filmów na liście. Dodaj z rekomendacji!",
        "watchlist_title": "❤️ Moja Watchlista",
        "search_actor_director": "🎬 Szukaj wg Aktora lub Reżysera",
        "search_language_origin": "🌐 Język Oryginalny Produkcjonalny",
        "actor_placeholder": "np. Leonardo DiCaprio, Christopher Nolan...",
        "spin_button": "🎲 ZALOSUJ FILM / SERIAL",
        "details_button": "ℹ️ Szczegóły",
        "watch_trailer": "▶️ Obejrzyj Zwiastun",
        "find_where_to_watch": "Gdzie obejrzeć 📺",
    },
    "EN": {
        "app_title": "🎬 CineScope",
        "app_tagline": "Discover movies & shows you'll love · Powered by TMDB",
        "nav_home": "🏠 Home",
        "nav_library": "📽️ My Library",
        "nav_search": "🔍 Search & Discover Pro",
        "nav_top10": "🏆 Top 10",
        "nav_compare": "⚖️ Compare",
        "nav_taste": "🧬 Taste DNA",
        "nav_assistant": "💬 AI Assistant",
        "nav_roulette": "🎲 Movie Roulette",
        "filter_genre": "🎭 Genre",
        "filter_streaming": "📺 Streaming Platforms",
        "filter_language": "🌐 Language / Język",
        "settings_backup": "⚙️ Settings & Data Backup",
        "export_data": "📥 Export Data (JSON)",
        "restore_data": "📤 Restore Backup (.json)",
        "watchlist_empty": "No movies yet. Add some from recommendations!",
        "watchlist_title": "❤️ My Watchlist",
        "search_actor_director": "🎬 Search by Actor or Director",
        "search_language_origin": "🌐 Original Language / Country",
        "actor_placeholder": "e.g., Leonardo DiCaprio, Christopher Nolan...",
        "spin_button": "🎲 SPIN THE WHEEL",
        "details_button": "ℹ️ Details",
        "watch_trailer": "▶️ Watch Trailer",
        "find_where_to_watch": "Find where to watch 📺",
    },
}


def get_lang() -> str:
    """Get current language code ('PL' or 'EN')."""
    try:
        val = st.session_state.get("lang", "PL")
        return val if val in ("PL", "EN") else "PL"
    except Exception:
        return "PL"



def t(key: str) -> str:
    """Translate key to the active language."""
    lang = get_lang()
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["EN"].get(key, key))


def get_tmdb_language() -> str:
    """Return TMDB language code string ('pl-PL' or 'en-US')."""
    return "pl-PL" if get_lang() == "PL" else "en-US"

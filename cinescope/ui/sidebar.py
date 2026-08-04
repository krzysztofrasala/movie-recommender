"""Sidebar: user stats, search history, watchlist and ratings."""

from __future__ import annotations

import streamlit as st

from cinescope import data, i18n, state
from cinescope.i18n import t
from cinescope.recommender import recommend
from cinescope.ui.html import rating_color


def _render_stats() -> None:
    total_watchlist = len(st.session_state.watchlist)
    total_rated = len(st.session_state.rated_movies_info)
    if total_watchlist == 0 and total_rated == 0:
        return
    st.header(t("your_stats_header"))
    c1, c2 = st.columns(2)
    c1.metric(t("watchlist_metric"), total_watchlist)
    c2.metric(t("rated_metric"), total_rated)
    if total_rated > 0:
        avg = sum(st.session_state.user_ratings.values()) / total_rated
        stars = round(avg + 1)
        st.caption(f"{t('your_avg_rating')}: {'★' * stars}{'☆' * (5 - stars)}")


def _render_search_history() -> None:
    if not st.session_state.search_history:
        return
    st.markdown("---")
    st.header(t("recent_searches_header"))
    movies = data.get_movies()
    for title in st.session_state.search_history:
        if st.button(f"↩ {title}", key=f"hist_{title}", use_container_width=True):
            local = movies[movies["title"] == title]
            if not local.empty:
                with st.spinner("Loading..."):
                    state.set_recommendations(recommend(title), title)
                st.rerun()


def render_watchlist_popover() -> None:
    """Render top-header Watchlist popover drawer."""
    count = len(st.session_state.get("watchlist", []))
    label = f"❤️ Watchlista ({count})" if i18n.get_lang() == "PL" else f"❤️ Watchlist ({count})"
    with st.popover(label, use_container_width=True):
        st.markdown(f"#### {t('watchlist_title')}")
        
        total_watchlist = len(st.session_state.watchlist)
        total_rated = len(st.session_state.rated_movies_info)
        if total_watchlist > 0 or total_rated > 0:
            c1, c2 = st.columns(2)
            c1.metric(t("watchlist_metric"), total_watchlist)
            c2.metric(t("rated_metric"), total_rated)
            st.divider()

        if not st.session_state.watchlist:
            st.caption(t("watchlist_empty"))
        else:
            for item in st.session_state.watchlist:
                c1, c2, c3 = st.columns([1, 3, 1])
                with c1:
                    st.image(item["poster"], use_container_width=True)
                with c2:
                    st.markdown(f"<div style='font-size:0.85rem;font-weight:600;line-height:1.2;'>{item['title']}</div>", unsafe_allow_html=True)
                    rc = rating_color(item["rating"])
                    st.markdown(f"<div style='color:{rc};font-size:0.75rem;'>⭐ {item['rating']}/10</div>", unsafe_allow_html=True)
                with c3:
                    if st.button("✕", key=f"top_rm_{item['title']}"):
                        state.remove_from_watchlist(item["title"])
                        st.toast(f"Removed **{item['title']}**")
                        st.rerun()
            st.divider()
            if st.button("🗑️ Clear Watchlist", key="top_clear_wl", use_container_width=True):
                st.session_state.watchlist = []
                active = st.session_state.get("active_profile")
                profiles = st.session_state.get("profiles")
                if active and profiles and active in profiles:
                    profiles[active]["watchlist"] = []
                st.toast("Watchlist cleared.")
                st.rerun()


def render() -> tuple[list[str], set[int]]:
    """Render sidebar elements and return empty user settings."""
    return [], set()

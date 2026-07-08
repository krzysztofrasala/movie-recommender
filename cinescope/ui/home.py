"""Home page sections: film of the day, now playing, trending, recommendations."""

from __future__ import annotations

import streamlit as st

from cinescope import state, tmdb
from cinescope.recommender import more_like_this, recommend_for_you
from cinescope.ui.cards import render_movie_row, render_recommendations
from cinescope.ui.dialogs import show_movie_details

TRENDING_PAGE_SIZE = 5
TRENDING_MAX_INDEX = 15


def _render_film_of_the_day() -> None:
    motd = tmdb.fetch_movie_of_the_day()
    if motd and motd["backdrop"]:
        overview = motd["overview"][:240] + ("..." if len(motd["overview"]) > 240 else "")
        # Class-based markup so media queries in styles.py can adapt padding
        # and font sizes on tablet/mobile without editing inline CSS.
        st.markdown(f"""
        <div class="cs-motd-banner" style="background-image: linear-gradient(to right, rgba(5,5,5,0.97) 30%, rgba(5,5,5,0.55) 70%, rgba(5,5,5,0.1)), url({motd['backdrop']});">
            <div class="cs-motd-eyebrow">🎬 &nbsp; FILM OF THE DAY</div>
            <div class="cs-motd-title">{motd['title']}</div>
            <div class="cs-motd-rating">⭐ {motd['rating']}/10</div>
            <div class="cs-motd-overview">{overview}</div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, _ = st.columns([1, 1, 6])
        with c1:
            if st.button("🎯 Find Similar", key="motd_rec", use_container_width=True):
                with st.spinner("Loading..."):
                    state.set_recommendations(more_like_this(motd["id"], motd["title"]), motd["title"])
                st.rerun()
        with c2:
            if st.button("ℹ️ Details", key="motd_det", use_container_width=True):
                show_movie_details(motd["id"], motd["title"], motd["poster"], motd["rating"], motd["overview"])

    st.markdown("---")


def _render_now_playing(provider_ids: set | None) -> None:
    now_playing = tmdb.fetch_now_playing()
    if now_playing:
        st.subheader("🎭 Now Playing in Cinemas")
        render_movie_row(now_playing, "np", active_provider_ids=provider_ids)
        st.markdown("---")


def _render_trending(provider_ids: set | None) -> None:
    trending = tmdb.fetch_trending()
    st.subheader("🔥 Trending Today")
    if trending:
        prev_col, _, next_col = st.columns([1, 8, 1])
        with prev_col:
            if st.button("⬅️", use_container_width=True) and st.session_state.trending_index > 0:
                st.session_state.trending_index -= TRENDING_PAGE_SIZE
        with next_col:
            if st.button("➡️", use_container_width=True) and st.session_state.trending_index < TRENDING_MAX_INDEX:
                st.session_state.trending_index += TRENDING_PAGE_SIZE
        start = st.session_state.trending_index
        render_movie_row(trending[start:start + TRENDING_PAGE_SIZE], "tr", active_provider_ids=provider_ids)

    st.markdown("---")


def _render_for_you(provider_ids: set | None) -> None:
    for_you = recommend_for_you()
    if for_you:
        st.subheader("💡 Recommended For You")
        st.caption("Based on movies you rated 4–5 stars")
        render_recommendations(for_you, active_provider_ids=provider_ids, section="foryou")
        st.markdown("---")


def _render_active_recommendations(provider_ids: set | None) -> None:
    if st.session_state.recommendations:
        st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
        render_recommendations(st.session_state.recommendations, active_provider_ids=provider_ids, section="similar")
        st.markdown("---")


def render(provider_ids: set | None) -> None:
    """Render all home-page sections in order."""
    _render_film_of_the_day()
    _render_now_playing(provider_ids)
    _render_trending(provider_ids)
    _render_for_you(provider_ids)
    _render_active_recommendations(provider_ids)

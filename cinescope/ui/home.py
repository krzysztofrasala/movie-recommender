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
        st.markdown(f"""
        <div style="
            background-image: linear-gradient(to right, rgba(5,5,5,0.97) 30%, rgba(5,5,5,0.55) 70%, rgba(5,5,5,0.1)),
                              url({motd['backdrop']});
            background-size: cover; background-position: center top;
            border-radius: 16px; padding: 50px 60px; margin-bottom: 6px; min-height: 230px;
            border: 1px solid #222;
        ">
            <div style="color:#F5C518;font-size:0.72rem;font-weight:700;letter-spacing:3px;margin-bottom:12px;opacity:0.9;">
                🎬 &nbsp; FILM OF THE DAY
            </div>
            <div style="color:#fff;font-size:2.2rem;font-weight:800;margin-bottom:6px;letter-spacing:-0.5px;text-shadow:0 2px 10px rgba(0,0,0,0.5);">
                {motd['title']}
            </div>
            <div style="color:#F5C518;font-size:0.95rem;margin-bottom:16px;font-weight:700;">⭐ {motd['rating']}/10</div>
            <div style="color:#bbb;font-size:0.88rem;max-width:500px;line-height:1.65;">
                {motd['overview'][:240]}{'...' if len(motd['overview']) > 240 else ''}
            </div>
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
            if st.button("⬅️", use_container_width=True):
                if st.session_state.trending_index > 0:
                    st.session_state.trending_index -= TRENDING_PAGE_SIZE
        with next_col:
            if st.button("➡️", use_container_width=True):
                if st.session_state.trending_index < TRENDING_MAX_INDEX:
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

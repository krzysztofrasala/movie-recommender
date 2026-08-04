"""Home page sections: film of the day, now playing, trending, recommendations."""

from __future__ import annotations

import streamlit as st

from cinescope import state, tmdb
from cinescope.i18n import t
from cinescope.recommender import more_like_this, recommend_for_you
from cinescope.ui.cards import render_movie_row, render_recommendations
from cinescope.ui.dialogs import show_movie_details

TRENDING_PAGE_SIZE = 5
TRENDING_MAX_INDEX = 15


def _is_filtered(filters: dict) -> bool:
    if not filters:
        return False
    has_genre = bool(filters.get("genres"))
    has_year = filters.get("year_range") != (1900, 2026) and filters.get("year_range") is not None
    has_vote = filters.get("vote_min", 0.0) > 0.0
    has_provider = bool(filters.get("provider_ids"))
    return has_genre or has_year or has_vote or has_provider


def _render_film_of_the_day() -> None:
    motd = tmdb.fetch_movie_of_the_day()
    if motd and motd["backdrop"]:
        overview = motd["overview"][:260] + ("..." if len(motd["overview"]) > 260 else "")
        label_motd = t("film_of_day").upper()
        st.markdown(f"""
        <div class="cs-motd-banner" style="background-image: linear-gradient(to right, rgba(8,8,8,0.98) 35%, rgba(8,8,8,0.75) 65%, rgba(8,8,8,0.15)), url({motd['backdrop']});">
            <div class="cs-motd-eyebrow">🎬 &nbsp; {label_motd}</div>
            <div class="cs-motd-title">{motd['title']}</div>
            <div class="cs-motd-meta">
                <span class="cs-motd-badge">⭐ {motd['rating']}/10</span>
            </div>
            <div class="cs-motd-overview">{overview}</div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1.6, 1.6, 1.8, 3])
        with c1:
            if st.button(t("details_btn"), key="motd_det", use_container_width=True):
                show_movie_details(motd["id"], motd["title"], motd["poster"], motd["rating"], motd["overview"])
        with c2:
            if st.button(t("more_like_this_btn"), key="motd_rec", use_container_width=True):
                with st.spinner("Loading..."):
                    state.set_recommendations(more_like_this(motd["id"], motd["title"]), motd["title"])
                st.rerun()
        with c3:
            in_wl = any(m["title"] == motd["title"] for m in st.session_state.get("watchlist", []))
            if in_wl:
                st.button(t("in_watchlist_btn"), key="motd_wl", disabled=True, use_container_width=True)
            else:
                if st.button(t("add_to_watchlist_btn"), key="motd_wl", use_container_width=True):
                    if state.add_to_watchlist(motd["title"], motd["poster"], motd["rating"]):
                        st.toast(f"❤️ **{motd['title']}** added to watchlist!")
                        st.rerun()
        with c4:
            trailer_url = tmdb.fetch_movie_trailer(motd["id"])
            if trailer_url:
                st.link_button(t("watch_trailer"), trailer_url, use_container_width=True)

    st.markdown("---")


def _render_trending(filters: dict) -> None:
    head_col, nav_col = st.columns([8.5, 1.5], vertical_alignment="center")
    with head_col:
        st.subheader(t("trending_today"))

    if _is_filtered(filters):
        from cinescope.config import GENRE_NAME_TO_ID
        genre_ids = [GENRE_NAME_TO_ID[g] for g in filters.get("genres", []) if g in GENRE_NAME_TO_ID]

        trending = tmdb.filtered_discover(
            genres=tuple(genre_ids),
            year_gte=None,
            year_lte=None,
            runtime_lte=None,
            vote_gte=None,
            provider_ids=tuple(filters.get("provider_ids", [])) if filters.get("provider_ids") else None,
            sort_by="popularity.desc",
            limit=20,
        )
        if trending:
            with nav_col:
                p_col, n_col = st.columns(2)
                with p_col:
                    if st.button("⬅️", use_container_width=True, key="tr_prev_filtered") and st.session_state.trending_index > 0:
                        st.session_state.trending_index -= TRENDING_PAGE_SIZE
                        st.rerun()
                with n_col:
                    if st.button("➡️", use_container_width=True, key="tr_next_filtered") and st.session_state.trending_index < TRENDING_MAX_INDEX:
                        st.session_state.trending_index += TRENDING_PAGE_SIZE
                        st.rerun()
            start = st.session_state.trending_index
            render_movie_row(trending[start:start + TRENDING_PAGE_SIZE], "tr", filters=filters, pre_filtered=True)
        else:
            st.info("No movies match your global filters.")
    else:
        trending = tmdb.fetch_trending()
        if trending:
            with nav_col:
                p_col, n_col = st.columns(2)
                with p_col:
                    if st.button("⬅️", use_container_width=True, key="tr_prev") and st.session_state.trending_index > 0:
                        st.session_state.trending_index -= TRENDING_PAGE_SIZE
                        st.rerun()
                with n_col:
                    if st.button("➡️", use_container_width=True, key="tr_next") and st.session_state.trending_index < TRENDING_MAX_INDEX:
                        st.session_state.trending_index += TRENDING_PAGE_SIZE
                        st.rerun()
            start = st.session_state.trending_index
            render_movie_row(trending[start:start + TRENDING_PAGE_SIZE], "tr", filters=filters)

    st.markdown("---")


def _render_for_you(filters: dict) -> None:
    for_you = recommend_for_you()
    if for_you:
        st.subheader(t("recommended_for_you"))
        st.caption("Based on movies you rated 4–5 stars")
        render_recommendations(for_you, filters=filters, section="foryou")
        st.markdown("---")


def _render_active_recommendations(filters: dict) -> None:
    if st.session_state.recommendations:
        c1, c2 = st.columns([9, 1])
        with c1:
            st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
        with c2:
            if st.button(t("close_btn"), key="close_home_rec"):
                st.session_state.recommendations = []
                st.session_state.rec_source = None
                st.rerun()
        render_recommendations(st.session_state.recommendations, filters=filters, section="similar")
        st.markdown("---")


def render(filters: dict) -> None:
    """Render all home-page sections in order."""
    _render_film_of_the_day()
    _render_trending(filters)
    _render_for_you(filters)
    _render_active_recommendations(filters)

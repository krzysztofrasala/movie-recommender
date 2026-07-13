"""Sidebar: filters, user stats, search history, watchlist and ratings."""

from __future__ import annotations

import streamlit as st

from cinescope import data, state, tmdb
from cinescope.recommender import recommend
from cinescope.ui.html import rating_color


def _render_stats() -> None:
    total_watchlist = len(st.session_state.watchlist)
    total_rated = len(st.session_state.rated_movies_info)
    if total_watchlist == 0 and total_rated == 0:
        return
    st.markdown("---")
    st.header("📊 Your Stats")
    c1, c2 = st.columns(2)
    c1.metric("Watchlist", total_watchlist)
    c2.metric("Rated", total_rated)
    if total_rated > 0:
        avg = sum(st.session_state.user_ratings.values()) / total_rated
        stars = round(avg + 1)
        st.caption(f"Your avg: {'★' * stars}{'☆' * (5 - stars)}")


def _render_search_history() -> None:
    if not st.session_state.search_history:
        return
    st.markdown("---")
    st.header("🕐 Recent Searches")
    movies = data.get_movies()
    for title in st.session_state.search_history:
        if st.button(f"↩ {title}", key=f"hist_{title}", use_container_width=True):
            local = movies[movies["title"] == title]
            if not local.empty:
                with st.spinner("Loading..."):
                    state.set_recommendations(recommend(title), title)
                st.rerun()


def _render_watchlist() -> None:
    st.markdown("---")
    st.header("❤️ My Watchlist")
    if not st.session_state.watchlist:
        st.markdown(
            '<div style="color:#555;font-size:0.85rem;text-align:center;padding:20px 0;">'
            "No movies yet.<br>Add some from recommendations!</div>",
            unsafe_allow_html=True,
        )
        return
    for item in st.session_state.watchlist:
        c1, c2, c3 = st.columns([1, 4, 1])
        with c1:
            st.image(item["poster"], use_container_width=True)
        with c2:
            st.markdown(f"<div style='font-size:0.8rem;font-weight:600;line-height:1.3;'>{item['title']}</div>", unsafe_allow_html=True)
            rc = rating_color(item["rating"])
            st.markdown(f"<div style='color:{rc};font-size:0.75rem;'>⭐ {item['rating']}/10</div>", unsafe_allow_html=True)
        with c3:
            if st.button("✕", key=f"rm_{item['title']}"):
                state.remove_from_watchlist(item["title"])
                st.toast(f"Removed **{item['title']}** from watchlist.")
                st.rerun()


def _render_ratings() -> None:
    if not st.session_state.rated_movies_info:
        return
    st.markdown("---")
    st.header("⭐ Your Ratings")
    for movie_id, info in st.session_state.rated_movies_info.items():
        rating = st.session_state.user_ratings.get(movie_id, 0)
        rc = rating_color(rating * 2)
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
            f'<img src="{info["poster"]}" style="width:28px;height:42px;border-radius:4px;object-fit:cover;">'
            f'<div><div style="font-size:0.72rem;font-weight:600;color:#ddd;">{info["title"]}</div>'
            f'<div style="color:{rc};font-size:0.68rem;">{"★" * (rating + 1)}{"☆" * (4 - rating)}</div></div></div>',
            unsafe_allow_html=True,
        )


def render() -> tuple[list[str], set[int]]:
    """Render the sidebar and return (selected genres, provider ids)."""
    with st.sidebar:
        st.header("🔍 Filters")
        selected_genres = st.multiselect("Genre", data.all_genres())

        providers = tmdb.fetch_providers_list()
        provider_name_to_id = {p["name"]: p["id"] for p in providers}
        selected_provider_names = st.multiselect(
            "Streaming on",
            options=list(provider_name_to_id.keys()),
            placeholder="Any platform...",
        )
        selected_provider_ids = {provider_name_to_id[n] for n in selected_provider_names}

        _render_stats()
        _render_search_history()
        _render_watchlist()
        _render_ratings()

    return selected_genres, selected_provider_ids

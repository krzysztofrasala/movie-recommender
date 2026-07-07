"""Reusable movie card renderers for recommendation grids and home-page rows."""

from __future__ import annotations

import streamlit as st

from cinescope import state, tmdb
from cinescope.data import get_local_genres
from cinescope.recommender import more_like_this
from cinescope.ui.dialogs import show_movie_details
from cinescope.ui.html import genre_chips_html, justwatch_url, poster_html, provider_logos_html


def render_rec_card(col, item: dict, providers: list[dict] | None = None, section: str = "rec") -> None:
    """Full recommendation card: poster, genres, actions, watchlist and rating.

    ``section`` namespaces the widget keys so the same movie can appear in
    two sections on one page (e.g. "For You" and "Similar to") without a
    Streamlit duplicate-key crash.
    """
    with col:
        genres = get_local_genres(item["title"])
        st.markdown(poster_html(item["poster"], item["rating"], item["rating"] >= 8.0), unsafe_allow_html=True)
        st.markdown(f"**{item['title']}**")
        if genres:
            st.markdown(genre_chips_html(genres), unsafe_allow_html=True)
        if providers:
            st.markdown(provider_logos_html(providers), unsafe_allow_html=True)

        if st.button("ℹ️ Details", key=f"{section}_rd_{item['id']}", use_container_width=True):
            show_movie_details(item["id"], item["title"], item["poster"], item["rating"], item["overview"])
        st.link_button("Watch 📺", justwatch_url(item["title"]), use_container_width=True)

        in_watchlist = any(m["title"] == item["title"] for m in st.session_state.watchlist)
        if in_watchlist:
            st.button("❤️ In Watchlist", key=f"{section}_wl_{item['id']}", disabled=True, use_container_width=True)
        else:
            if st.button("🤍 Add to Watchlist", key=f"{section}_wl_{item['id']}", use_container_width=True):
                if state.add_to_watchlist(item["title"], item["poster"], item["rating"]):
                    st.toast(f"❤️ **{item['title']}** added to watchlist!")
                st.rerun()

        saved = st.session_state.user_ratings.get(item["id"])
        new_rating = st.feedback("stars", key=f"{section}_fb_{item['id']}")
        if new_rating is not None and new_rating != saved:
            st.session_state.user_ratings[item["id"]] = new_rating
            st.session_state.rated_movies_info[item["id"]] = {"title": item["title"], "poster": item["poster"]}


def render_recommendations(recs: list[dict], active_provider_ids: set | None = None, section: str = "rec") -> None:
    """Grid of up to 10 recommendation cards, optionally filtered by provider."""
    if not recs:
        return
    providers_map = tmdb.fetch_providers_batch([r["id"] for r in recs])
    if active_provider_ids:
        recs = [r for r in recs if any(p["id"] in active_provider_ids for p in providers_map.get(r["id"], []))]
        if not recs:
            st.info("No movies found on the selected streaming platforms. Try adjusting the filter.")
            return
    rows = [recs[:5], recs[5:10]] if len(recs) >= 6 else [recs]
    for row in rows:
        cols = st.columns(5)
        for i, item in enumerate(row):
            render_rec_card(cols[i], item, providers_map.get(item["id"]), section=section)


def render_movie_row(movie_list: list[dict], key_prefix: str, active_provider_ids: set | None = None) -> None:
    """Single row of up to 5 cards built from raw TMDB list payloads."""
    providers_map = tmdb.fetch_providers_batch([m["id"] for m in movie_list]) if active_provider_ids else {}
    if active_provider_ids:
        movie_list = [
            m for m in movie_list
            if any(p["id"] in active_provider_ids for p in providers_map.get(m.get("id"), []))
        ]
        if not movie_list:
            st.info("No movies found on the selected streaming platforms.")
            return
    n = min(5, len(movie_list))
    cols = st.columns(n)
    for idx, m in enumerate(movie_list[:5]):
        movie_id = m.get("id")
        title = m.get("title", m.get("name", ""))
        poster = tmdb.poster_url(m.get("poster_path"))
        rating = round(m.get("vote_average", 0), 1)
        overview = m.get("overview", "")
        year = m.get("release_date", m.get("first_air_date", ""))[:4]
        with cols[idx]:
            st.markdown(poster_html(poster, rating, rating >= 8.0, year), unsafe_allow_html=True)
            st.markdown(f"**{title}**")
            if active_provider_ids and providers_map.get(movie_id):
                st.markdown(provider_logos_html(providers_map[movie_id]), unsafe_allow_html=True)
            if st.button("ℹ️ Details", key=f"{key_prefix}_d_{movie_id}", use_container_width=True):
                show_movie_details(movie_id, title, poster, rating, overview)
            if st.button("🎬 More like this", key=f"{key_prefix}_m_{movie_id}", use_container_width=True):
                with st.spinner("Loading..."):
                    state.set_recommendations(more_like_this(movie_id, title), title)
                st.rerun()
            st.link_button("Watch 📺", justwatch_url(title), use_container_width=True)

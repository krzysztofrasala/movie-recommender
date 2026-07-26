"""Modal dialogs with full movie / TV show details."""

from __future__ import annotations

import streamlit as st

from cinescope import tmdb
from cinescope.ui.html import format_runtime, genre_chips_html, justwatch_url, poster_html, rating_color


def _render_cast(cast_details: list[dict]) -> None:
    st.markdown("**Cast**")
    cols = st.columns(min(len(cast_details), 8))
    for i, actor in enumerate(cast_details[:8]):
        with cols[i]:
            st.image(actor["photo"], use_container_width=True)
            st.caption(f"**{actor['name']}**")
            if actor["character"]:
                st.caption(f"*{actor['character']}*")


def _render_trailer_and_watch_link(trailer: str | None, title: str) -> None:
    if trailer:
        url = trailer if trailer.startswith("http") else f"https://www.youtube.com/watch?v={trailer}"
        st.video(url)
    st.link_button("Find where to watch 📺", justwatch_url(title), use_container_width=True)



@st.dialog("🎬 Movie Details", width="large")
def show_movie_details(movie_id: int, title: str, poster: str, rating: float, overview: str) -> None:
    ext = tmdb.fetch_movie_extended(movie_id)
    trailer = tmdb.fetch_movie_trailer(movie_id)
    rc = rating_color(rating)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(poster_html(poster, rating, rating >= 8.0), unsafe_allow_html=True)
    with col2:
        st.subheader(title)
        if ext and ext["tagline"]:
            st.caption(f"*{ext['tagline']}*")
        st.markdown(f'<span style="color:{rc};font-size:1.2rem;font-weight:800;">⭐ {rating}/10</span>', unsafe_allow_html=True)
        if ext:
            if ext["genres"]:
                st.markdown(genre_chips_html(ext["genres"]), unsafe_allow_html=True)
            cols_meta = st.columns(2)
            if ext["runtime"]:
                cols_meta[0].write(f"⏱️ {format_runtime(ext['runtime'])}")
            if ext["director"]:
                cols_meta[1].write(f"🎬 {ext['director']}")
            if ext["budget"] > 0:
                st.write(f"💰 Budget: ${ext['budget']:,}")
        st.markdown("---")
        st.write(overview)

    if ext and ext.get("cast_details"):
        _render_cast(ext["cast_details"])

    _render_trailer_and_watch_link(trailer, title)


@st.dialog("📺 TV Show Details", width="large")
def show_tv_details(tv_id: int, title: str, poster: str, rating: float, overview: str) -> None:
    ext = tmdb.fetch_tv_extended(tv_id)
    trailer = tmdb.fetch_tv_trailer(tv_id)
    rc = rating_color(rating)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(poster_html(poster, rating, rating >= 8.0), unsafe_allow_html=True)
    with col2:
        st.subheader(title)
        if ext and ext["tagline"]:
            st.caption(f"*{ext['tagline']}*")
        st.markdown(f'<span style="color:{rc};font-size:1.2rem;font-weight:800;">⭐ {rating}/10</span>', unsafe_allow_html=True)
        if ext:
            if ext["genres"]:
                st.markdown(genre_chips_html(ext["genres"]), unsafe_allow_html=True)
            if ext["seasons"]:
                st.write(f"📺 {ext['seasons']} season{'s' if ext['seasons'] != 1 else ''} · {ext['episodes']} episodes")
            if ext["runtime"]:
                st.write(f"⏱️ ~{format_runtime(ext['runtime'])} / episode")
            if ext["status"]:
                status_color = "#2ECC71" if ext["status"] == "Returning Series" else "#888"
                st.markdown(f'<span style="color:{status_color};">● {ext["status"]}</span>', unsafe_allow_html=True)
            if ext["creator"]:
                st.write(f"🎬 Created by: **{ext['creator']}**")
        st.markdown("---")
        st.write(overview)

    if ext and ext.get("cast_details"):
        _render_cast(ext["cast_details"])

    _render_trailer_and_watch_link(trailer, title)

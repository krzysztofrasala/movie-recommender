"""'Compare' tab: side-by-side comparison with a content-similarity score."""

from __future__ import annotations

import streamlit as st

from cinescope import data, tmdb
from cinescope.ui.html import format_runtime, genre_chips_html, poster_html, rating_color


def render() -> None:
    st.caption("Pick two movies to compare side by side.")
    movies = data.get_movies()

    col1, col2 = st.columns(2)
    with col1:
        movie1 = st.selectbox("First movie", movies["title"].values, key="cmp1")
    with col2:
        movie2 = st.selectbox("Second movie", movies["title"].values, key="cmp2", index=1)

    if not st.button("⚖️ Compare", use_container_width=True):
        return

    m1_id = int(movies[movies["title"] == movie1].iloc[0]["movie_id"])
    m2_id = int(movies[movies["title"] == movie2].iloc[0]["movie_id"])
    with st.spinner("Loading..."):
        det1, det2 = tmdb.fetch_movie_details(m1_id), tmdb.fetch_movie_details(m2_id)
        ext1, ext2 = tmdb.fetch_movie_extended(m1_id), tmdb.fetch_movie_extended(m2_id)
    if not (det1 and det2 and ext1 and ext2):
        return

    idx1 = movies[movies["title"] == movie1].index[0]
    idx2 = movies[movies["title"] == movie2].index[0]
    score = round(data.pair_similarity(idx1, idx2) * 100, 1)
    score_color = rating_color(score / 10)
    st.markdown(
        f'<div style="text-align:center;padding:20px;">'
        f'<div style="font-size:0.8rem;color:#888;letter-spacing:2px;margin-bottom:4px;">CONTENT SIMILARITY</div>'
        f'<div style="font-size:3rem;font-weight:900;color:{score_color};">{score}%</div>'
        f'<div style="font-size:0.8rem;color:#666;">based on genre, cast, director & keywords</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    c1, c2 = st.columns(2)
    for col, title, det, ext in [(c1, movie1, det1, ext1), (c2, movie2, det2, ext2)]:
        with col:
            st.markdown(poster_html(det["poster"], det["rating"], det["rating"] >= 8.0), unsafe_allow_html=True)
            st.subheader(title)
            if ext["tagline"]:
                st.caption(f"*{ext['tagline']}*")
            rc = rating_color(det["rating"])
            st.markdown(f'<span style="color:{rc};font-weight:800;font-size:1.1rem;">⭐ {det["rating"]}/10</span>', unsafe_allow_html=True)
            if ext["genres"]:
                st.markdown(genre_chips_html(ext["genres"]), unsafe_allow_html=True)
            if ext["runtime"]:
                st.write(f"⏱️ {format_runtime(ext['runtime'])}")
            if ext["director"]:
                st.write(f"🎬 {ext['director']}")
            if ext["budget"] > 0:
                st.write(f"💰 ${ext['budget']:,}")
            if ext.get("cast_details"):
                st.markdown("**Cast:**")
                for actor in ext["cast_details"][:4]:
                    st.caption(f"• {actor['name']}" + (f" *({actor['character']})*" if actor["character"] else ""))

    common_cast = set(ext1["cast"]) & set(ext2["cast"])
    common_genres = set(ext1["genres"]) & set(ext2["genres"])
    same_director = ext1["director"] == ext2["director"] and ext1["director"] != "Unknown"
    if common_cast or common_genres or same_director:
        st.markdown("---")
        st.subheader("🔗 What they share")
        if same_director:
            st.success(f"Same director: **{ext1['director']}**")
        if common_genres:
            st.info(f"Common genres: **{', '.join(common_genres)}**")
        if common_cast:
            st.info(f"Same actors: **{', '.join(common_cast)}**")

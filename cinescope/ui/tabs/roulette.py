"""Movie & TV Show Roulette tab for instant random picks by mood & runtime."""

from __future__ import annotations

import random
import streamlit as st

from cinescope import state, tmdb
from cinescope.config import GENRE_NAME_TO_ID
from cinescope.ui.cards import render_rec_card
from cinescope.ui.dialogs import show_movie_details


def render() -> None:
    st.header("🎲 Movie & TV Show Roulette")
    st.caption("Don't know what to watch tonight? Pick your mood & runtime and spin the wheel!")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        runtime_opt = st.selectbox(
            "⏱️ Runtime",
            ["Any duration", "⚡ <= 90 mins (Quick Watch)", "🎬 <= 105 mins", "🍿 <= 120 mins", "📽️ 120+ mins"],
        )
    with col2:
        min_rating = st.selectbox(
            "⭐ Minimum Rating",
            ["Any rating", "⭐ 7.0+", "⭐ 7.5+", "⭐ 8.0+ (Must Watch)"],
        )
    with col3:
        mood_genre = st.selectbox(
            "🎭 Mood / Genre",
            ["Any Mood", "Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance", "Thriller", "Animation"],
        )
    with col4:
        content_type = st.radio(
            "📺 Type",
            ["Movies", "TV Shows"],
            horizontal=True,
        )

    st.markdown("---")

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        spin = st.button("🎲 SPIN THE WHEEL", type="primary", use_container_width=True)

    if spin or "roulette_winner" in st.session_state:
        if spin:
            with st.spinner("🌀 Spinning the roulette wheel..."):
                # Prepare query parameters for TMDB Discover
                genre_id = GENRE_NAME_TO_ID.get(mood_genre) if mood_genre != "Any Mood" else None
                vote_min = 0.0
                if "7.0+" in min_rating:
                    vote_min = 7.0
                elif "7.5+" in min_rating:
                    vote_min = 7.5
                elif "8.0+" in min_rating:
                    vote_min = 8.0

                params: dict = {
                    "sort_by": "popularity.desc",
                    "vote_average.gte": vote_min,
                    "vote_count.gte": 50,
                    "language": "en-US",
                }
                if genre_id:
                    params["with_genres"] = genre_id

                if "90 mins" in runtime_opt:
                    params["with_runtime.lte"] = 90
                elif "105 mins" in runtime_opt:
                    params["with_runtime.lte"] = 105
                elif "120 mins" in runtime_opt:
                    params["with_runtime.lte"] = 120
                elif "120+ mins" in runtime_opt:
                    params["with_runtime.gte"] = 120

                if content_type == "TV Shows":
                    res = tmdb._get("discover/tv", params)
                else:
                    res = tmdb._get("discover/movie", params)

                items = res.get("results", []) if res else []
                if items:
                    raw_winner = random.choice(items[:15])
                    st.session_state.roulette_winner = tmdb._movie_summary(raw_winner)
                else:
                    st.session_state.roulette_winner = None


        winner = st.session_state.get("roulette_winner")
        if winner:
            st.markdown(
                """
                <div style="background:linear-gradient(135deg, #2b1e00, #141414);border:2px solid #F5C518;border-radius:16px;padding:20px;margin:20px 0;text-align:center;">
                    <div style="font-size:2.5rem;">🎉</div>
                    <div style="color:#F5C518;font-size:1.5rem;font-weight:800;">YOUR TONIGHT PICK IS READY!</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_left, col_right = st.columns([1, 2])
            with col_left:
                render_rec_card(col_left, winner, section="roulette_win")
            with col_right:
                st.subheader(winner["title"])
                st.caption(f"⭐ {winner['rating']} · {winner.get('year', '')}")
                st.write(winner.get("overview", "No description available."))
                
                trailer_key = tmdb.fetch_movie_trailer(winner["id"])
                if trailer_key:
                    st.markdown("**▶️ Trailer Preview:**")
                    st.video(f"https://www.youtube.com/watch?v={trailer_key}")
                else:
                    st.info("No video trailer available for this title.")
        else:
            st.warning("No titles found matching your exact criteria. Try broadening your filters!")

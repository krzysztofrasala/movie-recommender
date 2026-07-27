"""'Top 10' tab: ranked most-popular and top-rated charts."""

from __future__ import annotations

import streamlit as st

from cinescope import state, tmdb
from cinescope.i18n import t
from cinescope.recommender import more_like_this
from cinescope.ui.dialogs import show_movie_details
from cinescope.ui.html import poster_html, rating_color

OVERVIEW_PREVIEW_CHARS = 220


def render() -> None:
    label_popular = t("most_popular")
    label_top = t("top_rated")
    chart_type = st.radio("Chart Type", [label_popular, label_top], horizontal=True, label_visibility="collapsed", key="top_type")
    top_movies = tmdb.fetch_top_movies("popular" if chart_type == label_popular else "top_rated")
    for rank, m in enumerate(top_movies, 1):
        rank_col, poster_col, info_col = st.columns([1, 2, 6])
        with rank_col:
            st.markdown(
                f"<div style='font-size:3.5rem;font-weight:900;color:#F5C518;text-align:center;padding-top:16px;"
                f"line-height:1;text-shadow:0 0 20px rgba(245,197,24,0.4);'>{rank}</div>",
                unsafe_allow_html=True,
            )
        with poster_col:
            st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0), unsafe_allow_html=True)
        with info_col:
            rc = rating_color(m["rating"])
            st.subheader(m["title"])
            st.markdown(f'<span style="color:{rc};font-size:1rem;font-weight:700;">⭐ {m["rating"]}/10</span>', unsafe_allow_html=True)
            st.write(m["overview"][:OVERVIEW_PREVIEW_CHARS] + ("..." if len(m["overview"]) > OVERVIEW_PREVIEW_CHARS else ""))
            c1, c2 = st.columns(2)
            with c1:
                if st.button(t("details_btn"), key=f"td_{rank}_{m['id']}", use_container_width=True):
                    show_movie_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
            with c2:
                if st.button(t("more_like_this_btn"), key=f"ts_{rank}_{m['id']}", use_container_width=True):
                    with st.spinner("Loading..."):
                        state.set_recommendations(more_like_this(m["id"], m["title"]), m["title"])
                    st.rerun()
        st.divider()

    if st.session_state.recommendations:
        st.markdown("---")
        c1, c2 = st.columns([9, 1])
        with c1:
            st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
        with c2:
            if st.button(t("close_btn"), key="close_top10_rec"):
                st.session_state.recommendations = []
                st.session_state.rec_source = None
                st.rerun()
        from cinescope.ui.cards import render_recommendations
        render_recommendations(st.session_state.recommendations, section="top10_rec")

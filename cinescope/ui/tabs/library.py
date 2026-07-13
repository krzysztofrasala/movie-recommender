"""'My Library' tab: local dataset browser with mood and decade shortcuts."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from cinescope import state, tmdb
from cinescope.config import DECADES, MOODS
from cinescope.recommender import recommend

_EMPTY_FILTERS_HTML = (
    '<div style="text-align:center;padding:40px;color:#555;">'
    '<div style="font-size:3rem;">🎬</div>'
    '<div style="font-size:1.1rem;margin-top:10px;">No movies match your filters.</div>'
    '<div style="font-size:0.85rem;margin-top:6px;">Try adjusting the genre or year range.</div></div>'
)


def render(filtered: pd.DataFrame) -> None:
    if filtered.empty:
        st.markdown(_EMPTY_FILTERS_HTML, unsafe_allow_html=True)
        return

    col_input, col_button = st.columns([4, 1])
    with col_input:
        query = st.text_input("Search", placeholder="Search your library...", label_visibility="collapsed")
    with col_button:
        if st.button("🎲 Surprise Me!", use_container_width=True):
            random_title = filtered.sample(1).iloc[0]["title"]
            with st.spinner(f"Picking {random_title}..."):
                state.set_recommendations(recommend(random_title), f"{random_title} 🎲")
            st.rerun()

    st.markdown("**Pick a mood:**")
    mood_cols = st.columns(len(MOODS))
    for i, (label, genre_id) in enumerate(MOODS.items()):
        with mood_cols[i]:
            if st.button(label, use_container_width=True, key=f"mood_{genre_id}"):
                with st.spinner("Loading..."):
                    state.set_recommendations(tmdb.discover_by_genre(genre_id), label, add_to_history=False)
                st.rerun()

    st.markdown("**Browse by decade:**")
    decade_cols = st.columns(len(DECADES))
    for i, (label, (start, end)) in enumerate(DECADES.items()):
        with decade_cols[i]:
            if st.button(label, use_container_width=True, key=f"dec_{label}"):
                with st.spinner("Loading..."):
                    state.set_recommendations(tmdb.discover_by_decade(start, end), f"Best of {label}", add_to_history=False)
                st.rerun()

    st.markdown("---")
    results = filtered[filtered["title"].str.contains(query, case=False, na=False)] if query else filtered
    if results.empty:
        st.warning(f'No movies found for "{query}".')
        return

    selected = st.selectbox(f"Select a movie ({len(results)} results)", results["title"].values)
    if st.button("Get 10 Recommendations", use_container_width=True):
        with st.spinner("Finding recommendations..."):
            state.set_recommendations(recommend(selected), selected)
        st.rerun()
        
    if st.session_state.recommendations:
        st.markdown("---")
        c1, c2 = st.columns([9, 1])
        with c1:
            st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
        with c2:
            if st.button("❌ Close", key="close_lib_rec"):
                st.session_state.recommendations = []
                st.session_state.rec_source = None
                st.rerun()
        from cinescope.ui.cards import render_recommendations
        render_recommendations(st.session_state.recommendations, section="lib_rec")

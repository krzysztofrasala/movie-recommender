"""'My Library' tab: local dataset browser with mood, decade shortcuts, sorting and grid view."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

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

SORT_OPTIONS = {
    "Popularity (Default)": "default",
    "⭐ Highest Rating": "vote_desc",
    "📅 Release Year (Newest)": "year_desc",
    "⏱️ Runtime (Longest)": "runtime_desc",
    "🔤 Title (A–Z)": "title_asc",
}


def render(filtered: pd.DataFrame) -> None:
    if filtered.empty:
        st.markdown(_EMPTY_FILTERS_HTML, unsafe_allow_html=True)
        return

    col_input, col_sort, col_button = st.columns([3, 2, 1])
    with col_input:
        query = st.text_input("Search", placeholder="Search your library...", label_visibility="collapsed")
    with col_sort:
        sort_label = st.selectbox(
            "Sort by",
            list(SORT_OPTIONS.keys()),
            label_visibility="collapsed",
            key="lib_sort_select",
        )
    with col_button:
        if st.button("🎲 Surprise Me!", use_container_width=True):
            random_title = filtered.sample(1).iloc[0]["title"]
            with st.spinner(f"Picking {random_title}..."):
                state.set_recommendations(recommend(random_title), f"{random_title} 🎲")
            st.rerun()

    # Apply sorting
    sort_key = SORT_OPTIONS[sort_label]
    if sort_key == "vote_desc":
        filtered = filtered.sort_values(by="vote_average", ascending=False)
    elif sort_key == "year_desc":
        filtered = filtered.sort_values(by="year", ascending=False)
    elif sort_key == "runtime_desc":
        filtered = filtered.sort_values(by="runtime", ascending=False)
    elif sort_key == "title_asc":
        filtered = filtered.sort_values(by="title", ascending=True)

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

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"Showing **{len(results)}** movies matching criteria")
    with c2:
        view_mode = st.radio("View", ["Dropdown", "Cards Grid"], horizontal=True, label_visibility="collapsed", key="lib_view_mode")

    if view_mode == "Dropdown":
        selected = st.selectbox(f"Select a movie ({len(results)} results)", results["title"].values)
        if st.button("Get 10 Recommendations", use_container_width=True):
            with st.spinner("Finding recommendations..."):
                state.set_recommendations(recommend(selected), selected)
            st.rerun()
    else:
        # Cards Grid View
        page_size = 10
        total_pages = max(1, (len(results) + page_size - 1) // page_size)
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="lib_page_input")
        start_idx = (page - 1) * page_size
        page_movies = results.iloc[start_idx : start_idx + page_size]

        from cinescope.ui.cards import render_recommendations

        def fetch_movie_card(row):
            details = tmdb.fetch_movie_details(row.movie_id)
            if details:
                details["title"] = row.title
            return details

        with ThreadPoolExecutor(max_workers=10) as ex:
            card_items = [r for r in ex.map(fetch_movie_card, page_movies.itertuples()) if r]

        render_recommendations(card_items, section=f"lib_grid_p{page}")

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

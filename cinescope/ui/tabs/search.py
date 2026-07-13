"""'Search' tab: movies, TV shows, people and natural-language discovery."""

from __future__ import annotations

import streamlit as st

from cinescope import state, tmdb
from cinescope.nl_query import GENRE_KEYWORDS, SORT_KEYWORDS, parse_natural_query
from cinescope.recommender import more_like_this
from cinescope.ui.dialogs import show_movie_details, show_tv_details
from cinescope.ui.html import justwatch_url, poster_html

_NO_RESULTS_HTML = (
    '<div style="text-align:center;padding:30px;color:#555;">'
    '<div style="font-size:2rem;">🎬</div><div>No results found.</div></div>'
)
_NO_PEOPLE_HTML = (
    '<div style="text-align:center;padding:30px;color:#555;">'
    '<div style="font-size:2rem;">🔍</div><div>No people found.</div></div>'
)
_NO_NL_RESULTS_HTML = (
    '<div style="text-align:center;padding:30px;color:#555;">'
    '<div style="font-size:2rem;">🔍</div><div>No results found. Try different words.</div></div>'
)

_PLACEHOLDERS = {
    "🎬 Movies": "e.g. Dune, Oppenheimer...",
    "📺 TV Shows": "e.g. Breaking Bad, The Bear...",
    "🎭 People (Actors & Directors)": "e.g. Christopher Nolan, Meryl Streep...",
}


def _describe_detected_filters(parsed: dict) -> None:
    """Show the user which filters were extracted from their description."""
    detected = []
    genre_id_to_name = {v: k.title() for k, v in GENRE_KEYWORDS.items()}
    for genre_id in parsed["genres"]:
        detected.append(f"**Genre:** {genre_id_to_name.get(genre_id, str(genre_id))}")
    if parsed["year_gte"] or parsed["year_lte"]:
        gte = parsed["year_gte"] or "..."
        lte = parsed["year_lte"] or "..."
        detected.append(f"**Year:** {gte}–{lte}")
    if parsed["vote_gte"]:
        detected.append(f"**Min rating:** {parsed['vote_gte']}")
    sort_labels = {v: k.title() for k, v in SORT_KEYWORDS.items()}
    detected.append(f"**Sort:** {sort_labels.get(parsed['sort_by'], parsed['sort_by'])}")
    if detected:
        st.info("Detected: " + "  ·  ".join(detected))

    if not parsed["genres"] and not parsed["year_gte"] and not parsed["year_lte"] and not parsed["vote_gte"]:
        st.warning("No specific filters detected — showing popular results. Try adding a genre like *horror*, *comedy*, *romantic*, etc.")


def _render_nl_search() -> None:
    st.markdown("**Describe what you feel like watching** — in plain words:")
    st.caption("Try: *scary movie from the 90s* · *great comedy for the family* · *best sci-fi classic* · *romantic thriller*")
    nl_query = st.text_input(
        "Describe",
        placeholder="e.g. funny animated movie for kids, scary horror from the 80s, best romantic comedy...",
        label_visibility="collapsed",
        key="nl_q",
    )
    if not nl_query:
        return

    parsed = parse_natural_query(nl_query)
    _describe_detected_filters(parsed)

    with st.spinner("Searching..."):
        results = tmdb.smart_discover(
            tuple(parsed["genres"]),
            parsed["year_gte"],
            parsed["year_lte"],
            parsed["vote_gte"],
            parsed["sort_by"],
        )
    if not results:
        st.markdown(_NO_NL_RESULTS_HTML, unsafe_allow_html=True)
        return

    for row_start in [0, 5]:
        row = results[row_start:row_start + 5]
        if not row:
            break
        cols = st.columns(5)
        for i, m in enumerate(row):
            with cols[i]:
                st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0, m.get("year")), unsafe_allow_html=True)
                st.markdown(f"**{m['title']}**")
                if st.button("ℹ️ Details", key=f"nl_d_{row_start}_{m['id']}", use_container_width=True):
                    show_movie_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                if st.button("🎬 Similar", key=f"nl_s_{row_start}_{m['id']}", use_container_width=True):
                    with st.spinner("Loading..."):
                        state.set_recommendations(more_like_this(m["id"], m["title"]), m["title"])
                    st.rerun()
                st.link_button("Watch 📺", justwatch_url(m["title"]), use_container_width=True)


def _render_person_results(query: str) -> None:
    with st.spinner("Searching..."):
        persons = tmdb.search_person(query)
    if not persons:
        st.markdown(_NO_PEOPLE_HTML, unsafe_allow_html=True)
    else:
        for p in persons:
            c1, c2 = st.columns([1, 6])
            with c1:
                st.image(p["photo"])
            with c2:
                st.subheader(p["name"])
                st.caption(f"Known for: **{p['role']}**")
                if p["known_for"]:
                    st.caption("🎬 " + " · ".join(p["known_for"]))
                if st.button("View filmography", key=f"pf_{p['id']}"):
                    st.session_state.selected_person_id = p["id"]
                    st.session_state.selected_person_name = p["name"]
                    st.rerun()
            st.divider()

    if st.session_state.selected_person_id:
        _render_filmography()


def _render_filmography() -> None:
    with st.spinner("Loading filmography..."):
        credits = tmdb.fetch_person_credits(st.session_state.selected_person_id)
    st.subheader(f"🎬 {st.session_state.selected_person_name} — Filmography")
    if not credits:
        return
    for row in [credits[:5], credits[5:]]:
        if not row:
            break
        cols = st.columns(5)
        for i, m in enumerate(row):
            with cols[i]:
                st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0, m["year"]), unsafe_allow_html=True)
                st.markdown(f"**{m['title']}**")
                is_tv_credit = m["media_type"] == "tv"
                if st.button("ℹ️ Details", key=f"pd_{m['id']}", use_container_width=True):
                    (show_tv_details if is_tv_credit else show_movie_details)(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                if st.button("🎬 Similar", key=f"ps_{m['id']}", use_container_width=True):
                    with st.spinner("Loading..."):
                        recs = tmdb.fetch_tv_recommendations(m["id"]) if is_tv_credit else more_like_this(m["id"], m["title"])
                        state.set_recommendations(recs, m["title"])
                    st.rerun()


def _render_title_results(query: str, is_tv: bool) -> None:
    with st.spinner("Searching..."):
        results = tmdb.search_tv(query) if is_tv else tmdb.search_movies(query)
    if not results:
        st.markdown(_NO_RESULTS_HTML, unsafe_allow_html=True)
        return
    for row_start in [0, 5]:
        row = results[row_start:row_start + 5]
        if not row:
            break
        cols = st.columns(5)
        for i, m in enumerate(row):
            with cols[i]:
                st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0, m.get("year")), unsafe_allow_html=True)
                st.markdown(f"**{m['title']}**")
                if is_tv:
                    if st.button("ℹ️ Details", key=f"sr_d_{row_start}_{m['id']}", use_container_width=True):
                        show_tv_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                    if st.button("📺 Similar shows", key=f"sr_s_{row_start}_{m['id']}", use_container_width=True):
                        with st.spinner("Loading..."):
                            state.set_recommendations(tmdb.fetch_tv_recommendations(m["id"]), m["title"])
                        st.rerun()
                else:
                    if st.button("ℹ️ Details", key=f"sr_d_{row_start}_{m['id']}", use_container_width=True):
                        show_movie_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                    if st.button("🎬 Similar movies", key=f"sr_s_{row_start}_{m['id']}", use_container_width=True):
                        with st.spinner("Loading..."):
                            state.set_recommendations(more_like_this(m["id"], m["title"]), m["title"])
                        st.rerun()


def render() -> None:
    search_type = st.radio(
        "Search for:",
        ["🎬 Movies", "📺 TV Shows", "🎭 People (Actors & Directors)", "🧠 Describe It"],
        horizontal=True,
    )
    if search_type == "🧠 Describe It":
        _render_nl_search()
        return

    query = st.text_input("Search", placeholder=_PLACEHOLDERS[search_type], label_visibility="collapsed", key="tab2q")
    if not query:
        return

    if search_type == "🎭 People (Actors & Directors)":
        _render_person_results(query)
    else:
        _render_title_results(query, is_tv=search_type == "📺 TV Shows")
        
    if st.session_state.recommendations:
        st.markdown("---")
        c1, c2 = st.columns([9, 1])
        with c1:
            st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
        with c2:
            if st.button("❌ Close", key="close_search_rec"):
                st.session_state.recommendations = []
                st.session_state.rec_source = None
                st.rerun()
        from cinescope.ui.cards import render_recommendations
        render_recommendations(st.session_state.recommendations, section="search_rec")

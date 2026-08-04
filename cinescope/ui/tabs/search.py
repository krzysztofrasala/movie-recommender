"""'Search & Discover' tab: unified instant search (movies, TV, actors) & smart AI discovery."""

from __future__ import annotations

import streamlit as st

from cinescope import data, state, tmdb
from cinescope.i18n import t
from cinescope.nl_query import GENRE_ID_TO_NAME, GENRE_KEYWORDS, SORT_KEYWORDS, parse_natural_query
from cinescope.recommender import more_like_this
from cinescope.ui.cards import render_recommendations
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

LANG_OPTIONS = {
    "Any Language": None,
    "🇵🇱 Polish (Polski)": "pl",
    "🇬🇧 English (Angielski)": "en",
    "🇫🇷 French (Francuski)": "fr",
    "🇪🇸 Spanish (Hiszpański)": "es",
    "🇯🇵 Japanese (Japoński)": "ja",
    "🇩🇪 German (Niemiecki)": "de",
    "🇮🇹 Italian (Włoski)": "it",
}


def _describe_detected_filters(parsed: dict) -> None:
    """Show extracted natural language filters."""
    detected = []
    for genre_id in parsed["genres"]:
        detected.append(f"**Genre:** {GENRE_ID_TO_NAME.get(genre_id, str(genre_id))}")
    if parsed.get("with_original_language"):
        detected.append(f"**Language:** {parsed['with_original_language'].upper()}")
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


def _render_unified_search() -> None:
    """Unified search: type any title, TV show, or actor/director name."""
    query = st.text_input(
        "Search Title or Person",
        placeholder="e.g. Dune, Breaking Bad, Christopher Nolan...",
        label_visibility="collapsed",
        key="unified_q",
    )
    if not query:
        return

    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🎬 Movies", "📺 TV Shows", "🎭 People & Directors"])

    with sub_tab1:
        _render_movie_search_results(query)

    with sub_tab2:
        _render_tv_search_results(query)

    with sub_tab3:
        _render_person_search_results(query)


def _render_movie_search_results(query: str) -> None:
    with st.spinner("Searching movies..."):
        results = tmdb.search_movies(query)
    if not results:
        st.markdown(_NO_RESULTS_HTML, unsafe_allow_html=True)
        return
    for row_start in range(0, min(len(results), 10), 5):
        row = results[row_start:row_start + 5]
        cols = st.columns(5)
        for i, m in enumerate(row):
            with cols[i]:
                st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0, m.get("year")), unsafe_allow_html=True)
                st.markdown(f"**{m['title']}**")
                if st.button("ℹ️ Details", key=f"m_d_{row_start}_{m['id']}", use_container_width=True):
                    show_movie_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                if st.button("🎬 Similar", key=f"m_s_{row_start}_{m['id']}", use_container_width=True):
                    with st.spinner("Loading..."):
                        state.set_recommendations(more_like_this(m["id"], m["title"]), m["title"])
                    st.rerun()


def _render_tv_search_results(query: str) -> None:
    with st.spinner("Searching TV shows..."):
        results = tmdb.search_tv(query)
    if not results:
        st.markdown(_NO_RESULTS_HTML, unsafe_allow_html=True)
        return
    for row_start in range(0, min(len(results), 10), 5):
        row = results[row_start:row_start + 5]
        cols = st.columns(5)
        for i, m in enumerate(row):
            with cols[i]:
                st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0, m.get("year")), unsafe_allow_html=True)
                st.markdown(f"**{m['title']}**")
                if st.button("ℹ️ Details", key=f"tv_d_{row_start}_{m['id']}", use_container_width=True):
                    show_tv_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                if st.button("📺 Similar", key=f"tv_s_{row_start}_{m['id']}", use_container_width=True):
                    with st.spinner("Loading..."):
                        state.set_recommendations(tmdb.fetch_tv_recommendations(m["id"]), m["title"])
                    st.rerun()


def _render_person_search_results(query: str) -> None:
    with st.spinner("Searching people..."):
        persons = tmdb.search_person(query)
    if not persons:
        st.markdown(_NO_PEOPLE_HTML, unsafe_allow_html=True)
    else:
        for p in persons[:4]:
            c1, c2 = st.columns([1, 6])
            with c1:
                st.image(p["profile_path"])
            with c2:
                st.subheader(p["name"])
                st.caption(f"Known for: **{p.get('known_for_department', 'Film')}**")
                if st.button("View filmography", key=f"pf_{p['id']}"):
                    st.session_state.selected_person_id = p["id"]
                    st.session_state.selected_person_name = p["name"]
                    st.rerun()
            st.divider()

    if st.session_state.get("selected_person_id"):
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


def _render_smart_discovery() -> None:
    """Smart discovery: natural language AI search + expandable manual filter drawer."""
    st.markdown("**Describe what you feel like watching** — in plain words:")
    st.caption("Try: *scary movie from the 90s* · *polskie komedie* · *great family animated movie* · *romantic thriller*")

    nl_query = st.text_input(
        "Describe",
        placeholder="e.g. polskie komedie, scary horror from the 80s, best sci-fi classic...",
        label_visibility="collapsed",
        key="nl_q",
    )

    with st.expander("🎛️ Advanced Filters (Genres, Languages & Ratings)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_genres = st.multiselect("Genre", options=data.all_genres(), key="disc_genres")
        with c2:
            sel_lang_label = st.selectbox("Original Language", options=list(LANG_OPTIONS.keys()), key="disc_lang")
        with c3:
            sel_min_vote = st.selectbox("⭐ Rating Floor", ["Any Rating", "⭐ 7.0+", "⭐ 7.5+", "⭐ 8.0+"], key="disc_vote")

    if nl_query:
        parsed = parse_natural_query(nl_query)
        if sel_lang_label and LANG_OPTIONS.get(sel_lang_label):
            parsed["with_original_language"] = LANG_OPTIONS[sel_lang_label]
        if "7.0+" in sel_min_vote:
            parsed["vote_gte"] = 7.0
        elif "7.5+" in sel_min_vote:
            parsed["vote_gte"] = 7.5
        elif "8.0+" in sel_min_vote:
            parsed["vote_gte"] = 8.0

        _describe_detected_filters(parsed)

        with st.spinner("Discovering..."):
            results = tmdb.smart_discover(
                tuple(parsed["genres"]),
                parsed["year_gte"],
                parsed["year_lte"],
                parsed["vote_gte"],
                parsed["sort_by"],
                parsed.get("with_original_language"),
            )
        if not results:
            st.markdown(_NO_NL_RESULTS_HTML, unsafe_allow_html=True)
            return

        for row_start in range(0, min(len(results), 10), 5):
            row = results[row_start:row_start + 5]
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

    elif sel_genres or LANG_OPTIONS.get(sel_lang_label) or sel_min_vote != "Any Rating":
        from cinescope.config import GENRE_NAME_TO_ID
        g_ids = [GENRE_NAME_TO_ID[g] for g in sel_genres if g in GENRE_NAME_TO_ID]
        vote_val = 0.0
        if "7.0+" in sel_min_vote:
            vote_val = 7.0
        elif "7.5+" in sel_min_vote:
            vote_val = 7.5
        elif "8.0+" in sel_min_vote:
            vote_val = 8.0

        with st.spinner("Discovering..."):
            results = tmdb.smart_discover(
                tuple(g_ids),
                None, None, vote_val if vote_val > 0 else None,
                "popularity.desc",
                LANG_OPTIONS.get(sel_lang_label),
            )
        if not results:
            st.markdown(_NO_RESULTS_HTML, unsafe_allow_html=True)
            return

        for row_start in range(0, min(len(results), 10), 5):
            row = results[row_start:row_start + 5]
            cols = st.columns(5)
            for i, m in enumerate(row):
                with cols[i]:
                    st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0, m.get("year")), unsafe_allow_html=True)
                    st.markdown(f"**{m['title']}**")
                    if st.button("ℹ️ Details", key=f"md_d_{row_start}_{m['id']}", use_container_width=True):
                        show_movie_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                    if st.button("🎬 Similar", key=f"md_s_{row_start}_{m['id']}", use_container_width=True):
                        with st.spinner("Loading..."):
                            state.set_recommendations(more_like_this(m["id"], m["title"]), m["title"])
                        st.rerun()


def render() -> None:
    main_tab1, main_tab2 = st.tabs(["🔍 Search Title / Person", "🧠 Smart AI & Filters"])

    with main_tab1:
        _render_unified_search()

    with main_tab2:
        _render_smart_discovery()

    if st.session_state.get("recommendations"):
        st.markdown("---")
        c1, c2 = st.columns([9, 1])
        with c1:
            st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
        with c2:
            if st.button("❌ Close", key="close_search_rec"):
                state.clear_recommendations()
                st.rerun()
        render_recommendations(st.session_state.recommendations)

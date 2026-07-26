"""'Search' tab: movies, TV shows, people, natural-language discovery and Pro Discover filters."""

from __future__ import annotations

import streamlit as st

from cinescope import state, tmdb
from cinescope.i18n import t
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

LANG_OPTIONS = {
    "Any language / Każdy język": None,
    "🇵🇱 Polish (Polski)": "pl",
    "🇬🇧 English (Angielski)": "en",
    "🇰🇷 Korean (Koreański)": "ko",
    "🇫🇷 French (Francuski)": "fr",
    "🇪🇸 Spanish (Hiszpański)": "es",
    "🇯🇵 Japanese (Japoński)": "ja",
    "🇩🇪 German (Niemiecki)": "de",
    "🇮🇹 Italian (Włoski)": "it",
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


def _render_discover_pro() -> None:
    st.markdown("### ⚡ Discover Pro Filters")
    st.caption("Search by specific Actor/Director, Original Language, and Ratings.")

    c1, c2, c3 = st.columns(3)
    with c1:
        person_query = st.text_input(
            t("search_actor_director"),
            placeholder=t("actor_placeholder"),
            key="pro_person_q",
        )
    with c2:
        lang_label = st.selectbox(
            t("search_language_origin"),
            options=list(LANG_OPTIONS.keys()),
            key="pro_lang_select",
        )
    with c3:
        min_vote = st.selectbox(
            "⭐ Rating Floor",
            ["Any Rating", "⭐ 7.0+", "⭐ 7.5+", "⭐ 8.0+"],
            key="pro_vote_select",
        )

    person_id = None
    if person_query:
        persons = tmdb.search_person(person_query)
        if persons:
            person_id = persons[0]["id"]
            st.success(f"Matched person: **{persons[0]['name']}** ({persons[0].get('known_for_department', 'Film')})")
        else:
            st.warning(f"No actor or director found matching '{person_query}'")

    lang_code = LANG_OPTIONS.get(lang_label)
    vote_val = 0.0
    if "7.0+" in min_vote:
        vote_val = 7.0
    elif "7.5+" in min_vote:
        vote_val = 7.5
    elif "8.0+" in min_vote:
        vote_val = 8.0

    params: dict = {
        "sort_by": "popularity.desc",
        "vote_count.gte": 20,
    }
    if vote_val > 0:
        params["vote_average.gte"] = vote_val
    if lang_code:
        params["with_original_language"] = lang_code
    if person_id:
        params["with_cast"] = person_id

    with st.spinner("Discovering..."):
        res = tmdb._get("discover/movie", params)

    movies = [tmdb._movie_summary(m) for m in res.get("results", [])] if res else []
    if not movies:
        st.markdown(_NO_RESULTS_HTML, unsafe_allow_html=True)
        return

    for row_start in [0, 5]:
        row = movies[row_start:row_start + 5]
        if not row:
            break
        cols = st.columns(5)
        for i, m in enumerate(row):
            with cols[i]:
                st.markdown(poster_html(m["poster"], m["rating"], m["rating"] >= 8.0, m.get("year")), unsafe_allow_html=True)
                st.markdown(f"**{m['title']}**")
                if st.button("ℹ️ Details", key=f"pro_d_{row_start}_{m['id']}", use_container_width=True):
                    show_movie_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
                if st.button("🎬 Similar", key=f"pro_s_{row_start}_{m['id']}", use_container_width=True):
                    with st.spinner("Loading..."):
                        state.set_recommendations(more_like_this(m["id"], m["title"]), m["title"])
                    st.rerun()


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
        "Search Mode:",
        ["🎬 Movies", "📺 TV Shows", "🎭 People (Actors & Directors)", "⚡ Discover Pro (Actors, Lang)", "🧠 Describe It"],
        horizontal=True,
    )
    if search_type == "🧠 Describe It":
        _render_nl_search()
        return
    elif search_type == "⚡ Discover Pro (Actors, Lang)":
        _render_discover_pro()
        return

    query = st.text_input("Search", placeholder=_PLACEHOLDERS.get(search_type, "..."), label_visibility="collapsed", key="tab2q")
    if not query:
        return

    if search_type == "🎭 People (Actors & Directors)":
        _render_person_results(query)
    else:
        _render_title_results(query, is_tv=search_type == "📺 TV Shows")

    if st.session_state.get("recommendations"):
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

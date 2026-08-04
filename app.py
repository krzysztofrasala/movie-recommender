"""CineScope — Streamlit entry point.

Wires together the sidebar, home-page sections and feature tabs.
All application logic lives in the ``cinescope`` package.
"""

import streamlit as st

from cinescope import data, state, tmdb
from cinescope.ui import home, sidebar, styles
from cinescope.ui.tabs import assistant, compare, library, roulette, search, taste_dna, top10

from cinescope.i18n import t

_FOOTER_HTML = """
<div style="text-align:center;padding:30px 0 10px;color:#444;font-size:0.78rem;line-height:2;">
    <div style="font-size:1.1rem;font-weight:700;color:#F5C518;margin-bottom:6px;">🎬 CineScope</div>
    Discover movies & shows you'll love<br>
    Movie data & images provided by <a href="https://www.themoviedb.org" target="_blank" style="color:#F5C518;text-decoration:none;">TMDB</a>
    &nbsp;·&nbsp; Where to watch via <a href="https://www.justwatch.com" target="_blank" style="color:#F5C518;text-decoration:none;">JustWatch</a><br>
    <span style="color:#333;font-size:0.72rem;">© 2026 CineScope · Built with Streamlit</span>
</div>
"""


def _check_prerequisites() -> None:
    """Stop with a friendly message when the API key or model files are missing."""
    if tmdb.get_api_key() is None:
        st.error(
            "TMDB API key not found. Add `TMDB_API_KEY` to `.streamlit/secrets.toml` "
            "or set it as an environment variable — see the README for setup steps."
        )
        st.stop()
    try:
        data.load_model()
    except data.ModelLoadError as exc:
        st.error(
            f"Could not load the recommendation model: {exc}\n\n"
            "Run `python fetch_dataset.py` to generate the model files."
        )
        st.stop()


from cinescope import data, i18n, state, tmdb


def _render_top_header() -> None:
    head_left, head_right = st.columns([5, 6], vertical_alignment="center")
    with head_left:
        st.title(t("app_title"))
        st.caption(t("app_tagline"))
    with head_right:
        c_wl, c_prof, c_lang = st.columns([2.2, 2.2, 1.8], vertical_alignment="center")
        with c_wl:
            sidebar.render_watchlist_popover()
        with c_prof:
            profiles = list(st.session_state.profiles.keys())
            active = st.session_state.active_profile
            add_option = t("add_new_profile")
            options = profiles + [add_option]
            index = profiles.index(active) if active in profiles else 0
            selected = st.selectbox(
                t("active_profile_label"),
                options=options,
                index=index,
                label_visibility="collapsed",
                key="top_profile_select",
            )
            if selected == add_option:
                with st.popover("➕ New Profile", use_container_width=True):
                    new_name = st.text_input("Name", placeholder=t("new_profile_name_placeholder"))
                    if st.button("Create Profile", use_container_width=True, key="btn_top_create_p"):
                        if new_name and state.add_profile(new_name):
                            st.toast(t("profile_created_toast").format(name=new_name))
                            st.rerun()
                        else:
                            st.error("Profile name already exists or is empty.")
            elif selected != active:
                state.switch_profile(selected)
                st.rerun()
        with c_lang:
            current_lang = i18n.get_lang()
            index = 0 if current_lang == "PL" else 1
            selected_lang = st.radio(
                t("filter_language"),
                ["PL 🇵🇱", "EN 🇬🇧"],
                index=index,
                horizontal=True,
                label_visibility="collapsed",
                key="top_lang_radio_select",
            )
            new_lang = "PL" if "PL" in selected_lang else "EN"
            if new_lang != current_lang:
                st.session_state.lang = new_lang
                st.rerun()


def main() -> None:
    # "auto" lets Streamlit collapse the sidebar on narrow viewports so the
    # main content is visible on mobile without a manual close first.
    st.set_page_config(page_title="CineScope", layout="wide", page_icon="🎬", initial_sidebar_state="auto")
    styles.inject()
    state.init()
    _check_prerequisites()

    selected_genres, provider_ids = sidebar.render()

    _render_top_header()

    filters = {
        "genres": selected_genres,
        "provider_ids": provider_ids,
    }
    filtered = data.apply_filters(tuple(selected_genres), None, None, None, None)

    tabs = st.tabs([
        t("nav_home"), t("nav_library"), t("nav_search"),
        t("nav_top10"), t("nav_compare"), t("nav_taste"), t("nav_assistant"), t("nav_roulette")
    ])
    
    with tabs[0]:
        home.render(filters)
        
    with tabs[1]:
        library.render(filtered)
        
    with tabs[2]:
        search.render()
        
    with tabs[3]:
        top10.render()
    with tabs[4]:
        compare.render()
    with tabs[5]:
        taste_dna.render()
    with tabs[6]:
        assistant.render()
    with tabs[7]:
        roulette.render()



    st.markdown("---")
    st.markdown(_FOOTER_HTML, unsafe_allow_html=True)

    # Persist the watchlist to the browser after all mutations for this run.
    state.persist_watchlist()


if __name__ == "__main__":
    main()

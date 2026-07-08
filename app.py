"""CineScope — Streamlit entry point.

Wires together the sidebar, home-page sections and feature tabs.
All application logic lives in the ``cinescope`` package.
"""

import streamlit as st

from cinescope import data, state, tmdb
from cinescope.ui import home, sidebar, styles
from cinescope.ui.tabs import compare, library, search, taste_dna, top10

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


def main() -> None:
    # "auto" lets Streamlit collapse the sidebar on narrow viewports so the
    # main content is visible on mobile without a manual close first.
    st.set_page_config(page_title="CineScope", layout="wide", page_icon="🎬", initial_sidebar_state="auto")
    styles.inject()
    state.init()
    _check_prerequisites()

    st.title("🎬 CineScope")
    st.caption("Discover movies & shows you'll love · Powered by TMDB")

    selected_genres, year_range, provider_ids = sidebar.render()
    provider_filter = provider_ids or None
    filtered = data.apply_filters(tuple(selected_genres), year_range[0], year_range[1])

    home.render(provider_filter)

    tabs = st.tabs(["📽️ My Library", "🔍 Search Movies, TV & People", "🏆 Top 10", "⚖️ Compare", "🧬 Taste DNA"])
    with tabs[0]:
        library.render(filtered)
    with tabs[1]:
        search.render()
    with tabs[2]:
        top10.render()
    with tabs[3]:
        compare.render()
    with tabs[4]:
        taste_dna.render()

    st.markdown("---")
    st.markdown(_FOOTER_HTML, unsafe_allow_html=True)

    # Persist the watchlist to the browser after all mutations for this run.
    state.persist_watchlist()


if __name__ == "__main__":
    main()

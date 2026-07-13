"""'Taste DNA' tab: persona, genre radar, era chart and hidden gems."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from cinescope import state, tmdb
from cinescope.config import GENRE_NAME_TO_ID
from cinescope.recommender import more_like_this
from cinescope.taste import assign_persona, get_taste_profile
from cinescope.ui.dialogs import show_movie_details
from cinescope.ui.html import poster_html

_EMPTY_STATE_HTML = """
<div style="text-align:center;padding:60px 20px;">
    <div style="font-size:4rem;">🧬</div>
    <div style="font-size:1.4rem;font-weight:700;color:#F5C518;margin:16px 0 8px;">Your Taste DNA is empty</div>
    <div style="color:#666;font-size:0.95rem;">Rate some movies or add them to your watchlist<br>and come back to see your unique cinematic profile.</div>
</div>
"""


def _render_persona_banner(persona: tuple[str, str, str]) -> None:
    emoji, name, description = persona
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #F5C518;border-radius:16px;padding:28px 36px;margin-bottom:24px;display:flex;align-items:center;gap:24px;">
        <div style="font-size:3.5rem;line-height:1;">{emoji}</div>
        <div>
            <div style="color:#888;font-size:0.7rem;font-weight:700;letter-spacing:3px;margin-bottom:4px;">YOUR MOVIE PERSONA</div>
            <div style="color:#F5C518;font-size:1.8rem;font-weight:800;margin-bottom:4px;">{name}</div>
            <div style="color:#aaa;font-size:0.92rem;">{description}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_genre_radar(genre_scores: dict) -> None:
    st.subheader("🎭 Genre DNA")
    top_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:8]
    labels = [g for g, _ in top_genres]
    values = [v for _, v in top_genres]
    max_value = max(values) if values else 1
    normalised = [v / max_value for v in values]

    fig = go.Figure(go.Scatterpolar(
        r=[*normalised, normalised[0]],
        theta=[*labels, labels[0]],
        fill="toself",
        fillcolor="rgba(245,197,24,0.15)",
        line=dict(color="#F5C518", width=2),
        marker=dict(color="#F5C518", size=6),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#111",
            radialaxis=dict(visible=False, range=[0, 1]),
            angularaxis=dict(color="#666", gridcolor="#222"),
        ),
        paper_bgcolor="#0d0d0d",
        plot_bgcolor="#0d0d0d",
        margin=dict(t=20, b=20, l=40, r=40),
        height=340,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_era_chart(decade_scores: dict) -> None:
    st.subheader("📅 Era Preference")
    decades_sorted = sorted(decade_scores.items())
    labels = [f"{d}s" for d, _ in decades_sorted]
    values = [v for _, v in decades_sorted]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker=dict(
            color=values,
            colorscale=[[0, "#1a1a1a"], [0.5, "#b8860b"], [1, "#F5C518"]],
            line=dict(color="#333", width=1),
        ),
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
        textfont=dict(color="#888", size=11),
    ))
    fig.update_layout(
        paper_bgcolor="#0d0d0d",
        plot_bgcolor="#0d0d0d",
        xaxis=dict(color="#666", gridcolor="#1a1a1a", tickfont=dict(color="#aaa")),
        yaxis=dict(visible=False),
        margin=dict(t=20, b=10, l=10, r=10),
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_hidden_gems(genre_scores: dict) -> None:
    st.subheader("💎 Hidden Gems for You")
    st.caption("High-quality films that flew under the radar — matched to your taste")

    top_genre_name = sorted(genre_scores, key=genre_scores.get, reverse=True)[0] if genre_scores else None
    top_genre_id = GENRE_NAME_TO_ID.get(top_genre_name) if top_genre_name else None
    exclude_ids = tuple(int(movie_id) for movie_id in st.session_state.rated_movies_info)

    with st.spinner("Finding hidden gems..."):
        gems = tmdb.fetch_hidden_gems(top_genre_id, exclude_ids)

    if not gems:
        st.info("Rate a few movies first to get personalized Hidden Gems.")
        return

    cols = st.columns(5)
    for i, m in enumerate(gems):
        with cols[i]:
            st.markdown(poster_html(m["poster"], m["rating"], False, m.get("year")), unsafe_allow_html=True)
            st.markdown(f"**{m['title']}**")
            st.caption(f"⭐ {m['rating']} · {m.get('year', '')}")
            if st.button("ℹ️ Details", key=f"gem_d_{m['id']}", use_container_width=True):
                show_movie_details(m["id"], m["title"], m["poster"], m["rating"], m["overview"])
            if st.button("🎬 Similar", key=f"gem_s_{m['id']}", use_container_width=True):
                with st.spinner("Loading..."):
                    state.set_recommendations(more_like_this(m["id"], m["title"]), m["title"])
                st.rerun()


def render() -> None:
    genre_scores, decade_scores = get_taste_profile()
    total_rated = len(st.session_state.rated_movies_info)
    total_watchlist = len(st.session_state.watchlist)

    if not genre_scores and not decade_scores:
        st.markdown(_EMPTY_STATE_HTML, unsafe_allow_html=True)
        return

    persona = assign_persona(genre_scores)
    if persona:
        _render_persona_banner(persona)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        if genre_scores:
            _render_genre_radar(genre_scores)
    with col_right:
        if decade_scores:
            _render_era_chart(decade_scores)
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rated", total_rated)
        c2.metric("Watchlist", total_watchlist)
        if total_rated > 0:
            avg_rating = sum(st.session_state.user_ratings.values()) / total_rated
            c3.metric("Avg Stars", f"{'★' * round(avg_rating + 1)}"[:5])

    st.markdown("---")
    _render_hidden_gems(genre_scores)
    
    if st.session_state.recommendations:
        st.markdown("---")
        c1, c2 = st.columns([9, 1])
        with c1:
            st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
        with c2:
            if st.button("❌ Close", key="close_taste_rec"):
                st.session_state.recommendations = []
                st.session_state.rec_source = None
                st.rerun()
        from cinescope.ui.cards import render_recommendations
        render_recommendations(st.session_state.recommendations, section="taste_rec")

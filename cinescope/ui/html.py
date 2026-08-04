"""Small HTML/URL snippet builders shared by cards, dialogs and the sidebar."""

from __future__ import annotations

import urllib.parse

GENRE_CHIP_PALETTE = ["#1a3a5c", "#1a4a2a", "#4a1a3a", "#3a2a0a", "#0a3a4a"]


def rating_color(rating: float) -> str:
    """Traffic-light colour for a 0-10 rating."""
    if rating >= 7.5:
        return "#2ECC71"
    if rating >= 6.0:
        return "#F39C12"
    return "#E74C3C"


def format_runtime(minutes) -> str:
    """Format minutes as '2h 15m' (or '45m' under an hour)."""
    if not minutes:
        return ""
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m}m" if h else f"{m}m"


def justwatch_url(title: str) -> str:
    """JustWatch search URL for finding where to stream a title."""
    return f"https://www.justwatch.com/pl/search?q={urllib.parse.quote(title)}"


def poster_html(poster_url: str, rating: float, is_hot: bool = False, year=None) -> str:
    """Poster image with glassmorphism rating badge and optional HOT/year tags."""
    hot_badge = '<div style="position:absolute;top:8px;left:8px;background:rgba(229,9,20,0.9);color:#fff;padding:3px 9px;border-radius:12px;font-size:0.65rem;font-weight:800;letter-spacing:1px;backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.2);box-shadow:0 2px 8px rgba(0,0,0,0.4);">🔥 HOT</div>' if is_hot else ""
    year_tag = f'<div style="position:absolute;top:8px;right:8px;background:rgba(15,15,15,0.8);color:#ddd;padding:3px 8px;border-radius:10px;font-size:0.68rem;font-weight:600;backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.1);">{year}</div>' if year else ""
    rc = rating_color(rating)
    return f"""
    <div class="cs-poster-card" style="position:relative;border-radius:12px;overflow:hidden;margin-bottom:6px;box-shadow:0 4px 18px rgba(0,0,0,0.6);transition:all 0.25s cubic-bezier(0.165,0.84,0.44,1);">
        <img src="{poster_url}" style="width:100%;display:block;border-radius:12px;">
        <div style="position:absolute;bottom:8px;right:8px;background:rgba(10,10,10,0.82);color:{rc};padding:3px 10px;border-radius:12px;font-size:0.78rem;font-weight:800;backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.15);box-shadow:0 2px 8px rgba(0,0,0,0.5);">⭐ {rating}</div>
        {hot_badge}{year_tag}
    </div>"""


def provider_logos_html(providers: list[dict] | None) -> str:
    """Row of streaming-provider logos (up to 4)."""
    if not providers:
        return ""
    logos = "".join(
        f'<img src="{p["logo"]}" title="{p["name"]}" '
        f'style="width:22px;height:22px;border-radius:4px;object-fit:cover;">'
        for p in providers[:4]
    )
    return f'<div style="display:flex;gap:4px;margin:4px 0 2px 0;align-items:center;">{logos}</div>'


def genre_chips_html(genres: list[str]) -> str:
    """Row of coloured genre chips (up to 3)."""
    if not genres:
        return ""
    chips = "".join(
        f'<span style="background:{GENRE_CHIP_PALETTE[i % len(GENRE_CHIP_PALETTE)]};color:#bbb;padding:2px 9px;border-radius:12px;font-size:0.65rem;margin-right:4px;white-space:nowrap;">{g}</span>'
        for i, g in enumerate(genres[:3])
    )
    return f'<div style="margin:4px 0 8px 0;overflow:hidden;">{chips}</div>'

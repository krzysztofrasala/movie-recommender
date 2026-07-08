"""Global CSS injected once per page render."""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

h1 {
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #F5C518 0%, #FF6B35 60%, #E50914 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
}
h2, h3 {
    border-left: 4px solid #F5C518;
    padding-left: 12px;
    margin-top: 0.4rem !important;
    font-weight: 700 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    border: 1px solid #2a2a2a !important;
    background: linear-gradient(135deg, #1e1e1e, #161616) !important;
    color: #ddd !important;
    transition: all 0.18s ease !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}
.stButton > button:hover {
    border-color: #F5C518 !important;
    color: #F5C518 !important;
    background: linear-gradient(135deg, #252518, #1a1a12) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245,197,24,0.2) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }

/* ── Link buttons (Watch 📺) ── */
.stLinkButton a {
    border-radius: 8px !important;
    border: none !important;
    background: linear-gradient(135deg, #E50914, #b0060f) !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 2px 8px rgba(229,9,20,0.3) !important;
}
.stLinkButton a:hover {
    background: linear-gradient(135deg, #ff1a25, #E50914) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(229,9,20,0.45) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #222; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 22px !important;
    color: #777 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.stTabs [aria-selected="true"] {
    background: #181818 !important;
    color: #F5C518 !important;
    border-bottom: 2px solid #F5C518 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0A0A0A !important;
    border-right: 1px solid #1e1e1e !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    border-left: 3px solid #F5C518 !important;
    padding-left: 8px;
    font-size: 0.9rem !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input {
    border-radius: 8px !important;
    background: #181818 !important;
    border-color: #2a2a2a !important;
    color: #fff !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #F5C518 !important;
    box-shadow: 0 0 0 1px #F5C518 !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: #181818;
    border-radius: 10px;
    padding: 12px;
    border: 1px solid #2a2a2a;
}
[data-testid="stMetricValue"] { color: #F5C518 !important; font-weight: 800 !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; border-left: 4px solid #F5C518 !important; }

/* ── Divider ── */
hr { border-color: #1e1e1e !important; margin: 1.5rem 0 !important; }

/* ── Expander ── */
[data-testid="stExpander"] { border: 1px solid #222 !important; border-radius: 10px !important; background: #181818 !important; }

/* ── Radio ── */
[data-testid="stRadio"] label { font-size: 0.85rem !important; }

/* ── Toast ── */
[data-testid="stToast"] {
    background: #1a1a1a !important;
    border: 1px solid #F5C518 !important;
    border-radius: 10px !important;
    color: #fff !important;
}

/* ── Caption ── */
.stCaption { color: #888 !important; font-size: 0.78rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #F5C518; }

/* ── Film of the Day banner ─────────────────────────────────────────────── */
.cs-motd-banner {
    background-size: cover;
    background-position: center top;
    border-radius: 16px;
    padding: 50px 60px;
    margin-bottom: 6px;
    min-height: 230px;
    border: 1px solid #222;
}
.cs-motd-eyebrow {
    color: #F5C518;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 3px;
    margin-bottom: 12px;
    opacity: 0.9;
}
.cs-motd-title {
    color: #fff;
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 6px;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    line-height: 1.15;
}
.cs-motd-rating {
    color: #F5C518;
    font-size: 0.95rem;
    margin-bottom: 16px;
    font-weight: 700;
}
.cs-motd-overview {
    color: #bbb;
    font-size: 0.88rem;
    max-width: 500px;
    line-height: 1.65;
}

/* ── Button text: never letter-stack, never truncate to ellipsis ──────
   Streamlit's default styles clip button text with ellipsis in narrow
   columns ("Find Similar" → "Find Si..."). Let text wrap between whole
   words instead — mid-word breaks are still forbidden. */
.stButton > button p {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    word-break: keep-all;
    overflow-wrap: normal;
    hyphens: none;
    line-height: 1.15;
}
.stButton > button {
    height: auto !important;
    min-height: 38px;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}

/* ── Responsive: tablet (below 900px) ───────────────────────────────────
   Streamlit uses stHorizontalBlock as a flex row of columns. Below 900px
   we let columns wrap so 5-card grids become 2×N or 3×N instead of
   squeezing to 90px each. */
@media (max-width: 900px) {
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 12px !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: calc(50% - 8px) !important;
        flex: 1 1 calc(50% - 8px) !important;
    }
    /* Film of the Day banner shrinks with the viewport */
    .cs-motd-banner {
        padding: 32px 28px;
        min-height: 200px;
    }
    .cs-motd-title { font-size: 1.7rem; }
    /* Tab labels get a little tighter so all five fit two rows max */
    .stTabs [data-baseweb="tab"] {
        padding: 8px 12px !important;
        font-size: 0.78rem !important;
    }
    h1 { font-size: 2.2rem !important; }
}

/* ── Responsive: mobile (below 560px) ───────────────────────────────────
   Single column of cards — anything smaller than that is unreadable at
   phone widths. */
@media (max-width: 560px) {
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }
    .cs-motd-banner {
        padding: 24px 20px;
        min-height: 180px;
        background-position: right center;
    }
    .cs-motd-title { font-size: 1.4rem; }
    .cs-motd-overview { font-size: 0.82rem; max-width: 100%; }
    /* Compact H1 so it doesn't dwarf the caption below */
    h1 { font-size: 1.8rem !important; letter-spacing: -0.5px; }
    /* Modal dialogs need to fit the phone screen */
    [data-testid="stDialog"] > div { width: 96vw !important; max-width: 96vw !important; }
    /* Tabs: allow horizontal scrolling instead of stacking two rows */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto;
        flex-wrap: nowrap !important;
    }
    .stTabs [data-baseweb="tab"] {
        white-space: nowrap;
        flex-shrink: 0;
    }
}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

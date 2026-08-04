"""Global CSS injected once per page render."""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Streamlit default chrome & prompt removal ── */
header[data-testid="stHeader"] { visibility: hidden !important; height: 0 !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stToast"] { display: none !important; }

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}

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
.stTabs [data-baseweb="tab-list"] {
    gap: 6px !important;
    border-bottom: 1px solid #262626 !important;
    padding-bottom: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0 !important;
    padding: 10px 18px !important;
    color: #888 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #fff !important;
    background: rgba(255, 255, 255, 0.05) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(180deg, rgba(245, 197, 24, 0.14) 0%, rgba(245, 197, 24, 0.02) 100%) !important;
    color: #F5C518 !important;
    border-bottom: 3px solid #F5C518 !important;
    font-weight: 700 !important;
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

/* ── Custom Dark & Gold Scrollbar ── */
::-webkit-scrollbar { width: 8px !important; height: 8px !important; }
::-webkit-scrollbar-track { background: #0a0a0a !important; }
::-webkit-scrollbar-thumb { background: #262626 !important; border-radius: 4px !important; border: 2px solid #0a0a0a !important; }
::-webkit-scrollbar-thumb:hover { background: #F5C518 !important; }

/* ── Film of the Day banner ─────────────────────────────────────────────── */
.cs-motd-banner {
    background-size: cover;
    background-position: center top;
    border-radius: 16px;
    padding: 44px 50px;
    margin-bottom: 12px;
    min-height: 240px;
    border: 1px solid #2a2a2a;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.7);
}
.cs-motd-eyebrow {
    color: #F5C518;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 3px;
    margin-bottom: 10px;
    text-transform: uppercase;
}
.cs-motd-title {
    color: #fff;
    font-size: 2.6rem;
    font-weight: 900;
    margin-bottom: 8px;
    letter-spacing: -0.8px;
    text-shadow: 0 4px 16px rgba(0,0,0,0.8);
    line-height: 1.1;
}
.cs-motd-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}
.cs-motd-badge {
    background: rgba(245, 197, 24, 0.18);
    color: #F5C518;
    border: 1px solid rgba(245, 197, 24, 0.35);
    padding: 3px 12px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 700;
}
.cs-motd-overview {
    color: #ccc;
    font-size: 0.9rem;
    max-width: 580px;
    line-height: 1.6;
    text-shadow: 0 2px 8px rgba(0,0,0,0.7);
}

/* ── Column (Card) Hover Animations ── */
[data-testid="stColumn"] {
    transition: transform 0.25s cubic-bezier(0.165, 0.84, 0.44, 1), filter 0.25s ease !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:hover {
    transform: translateY(-6px) scale(1.025) !important;
    filter: drop-shadow(0 12px 24px rgba(0, 0, 0, 0.75)) drop-shadow(0 0 10px rgba(245, 197, 24, 0.2)) !important;
}

/* ── Dialog Glassmorphism ── */
[data-testid="stDialog"] > div {
    background: rgba(18, 18, 18, 0.75) !important;
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
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
    /* Segmented Radio Switcher (Language Toggle) */
    div[key="top_lang_radio_select"] [role="radiogroup"] {
        background: #141414 !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 20px !important;
        padding: 3px !important;
        gap: 4px !important;
    }
    div[key="top_lang_radio_select"] label {
        border-radius: 16px !important;
        padding: 4px 12px !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #888 !important;
        transition: all 0.2s ease !important;
    }
    div[key="top_lang_radio_select"] label:hover {
        color: #F5C518 !important;
    }
}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

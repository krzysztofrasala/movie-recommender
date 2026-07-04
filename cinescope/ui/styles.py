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
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

"""AI Assistant tab for conversational movie & TV recommendations with Gemini Tool Use & interactive cards."""

from __future__ import annotations

import os
import streamlit as st

from cinescope import recommender, tmdb
from cinescope.ui.cards import render_rec_card

POLISH_TO_ENGLISH_KEYWORDS = {
    "bliskim wschodem": "middle east",
    "bliski wschód": "middle east",
    "bliskiego wschodu": "middle east",
    "bliskim wschodzie": "middle east",
    "komedie": "comedy",
    "komedia": "comedy",
    "horror": "horror",
    "horrory": "horror",
    "akcja": "action",
    "akcji": "action",
    "dramat": "drama",
    "sensacyjny": "thriller",
    "kryminał": "crime",
    "wojenny": "war",
    "historyczny": "history",
    "animowany": "animation",
    "sci-fi": "sci-fi",
    "fantastyka": "fantasy",
}


def _get_gemini_key() -> str | None:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("GEMINI_API_KEY")


def search_movies_tool(query: str) -> list[dict]:
    """Search for movies matching a title, keyword, or description."""
    return tmdb.search_movies(query)


def search_tv_tool(query: str) -> list[dict]:
    """Search for TV shows matching a title, keyword, or description."""
    return tmdb.search_tv(query)


def get_similar_movies_tool(title: str) -> list[dict]:
    """Get recommendations similar to a specific movie title."""
    return recommender.more_like_this(0, title)


def get_trending_movies_tool() -> list[dict]:
    """Get the top trending movies right now."""
    return tmdb.fetch_trending()


def _smart_search_fallback(prompt: str) -> tuple[str, list[dict]]:
    """Intelligent fallback for when Gemini API quota is exhausted."""
    q_lower = prompt.lower()

    clean = q_lower
    for stop in [
        "znajdź mi", "znajdź", "wyszukaj mi", "wyszukaj", "szukam jakiegoś", "szukam",
        "poleć mi", "poleć", "film o", "serial o", "związany z", "w klimacie", "chcę obejrzeć",
        "daj mi", "pokaż mi", "pokaż"
    ]:
        clean = clean.replace(stop, "")
    clean = clean.strip()

    is_tv = any(w in q_lower for w in ["serial", "tv", "series", "sezon"])

    search_queries = []
    if clean:
        search_queries.append(clean)
    else:
        search_queries.append(prompt)

    # Substring / stem matching for Middle East and common Polish terms
    if any(stem in q_lower for stem in ["blisk", "wschód", "wschodzie", "wschodu", "wschodem"]):
        if "middle east" not in search_queries:
            search_queries.append("middle east")
    if any(stem in q_lower for stem in ["komed"]):
        if "comedy" not in search_queries:
            search_queries.append("comedy")
    if any(stem in q_lower for stem in ["horror"]):
        if "horror" not in search_queries:
            search_queries.append("horror")
    if any(stem in q_lower for stem in ["akcj"]):
        if "action" not in search_queries:
            search_queries.append("action")

    for pl_word, en_word in POLISH_TO_ENGLISH_KEYWORDS.items():
        if pl_word in q_lower and en_word not in search_queries:
            search_queries.append(en_word)

    collected: list[dict] = []
    seen = set()

    for q in search_queries:
        if is_tv:
            results = tmdb.search_tv(q)
            if not results:
                results = tmdb.search_movies(q)
        else:
            results = tmdb.search_movies(q)
            if not results:
                results = tmdb.search_tv(q)

        for m in results:
            if m["id"] not in seen:
                seen.add(m["id"])
                collected.append(m)

    category_type = "seriali TV" if is_tv else "filmów"
    msg = (
        f"🤖 **Znalezione propozycje {category_type} dla zapytania:** *{prompt}*\n\n"
        "<span style='color:#888;font-size:0.75rem;'>(Wyszukano w bazie TMDB — darmowy limit API Gemini wykorzystany)</span>"
    )
    return msg, collected


def render() -> None:
    from cinescope.i18n import get_lang, t
    col_h, col_c = st.columns([4, 1])
    with col_h:
        st.header(t("assistant_title"))
        st.caption(t("assistant_subtitle"))
    with col_c:
        if st.button(t("clear_chat"), key="btn_clear_chat", use_container_width=True):
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": t("chat_welcome_msg"),
                    "movies": [],
                }
            ]
            st.rerun()

    gemini_key = _get_gemini_key()
    if not gemini_key:
        st.warning("⚠️ Missing `GEMINI_API_KEY`. To use the assistant, add it in secrets.toml or set the environment variable.")
        return

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gemini_key)
    except Exception as exc:
        st.error(f"Could not initialize Gemini AI client: {exc}")
        return

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": t("chat_welcome_msg"),
                "movies": [],
            }
        ]

    # Create a scrollable container for chat history
    messages_container = st.container(height=520, border=False)

    with messages_container:
        for idx, msg in enumerate(st.session_state.chat_messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"], unsafe_allow_html=True)
                movies = msg.get("movies", [])
                if movies:
                    n = min(5, len(movies))
                    cols = st.columns(n)
                    for i, m in enumerate(movies[:n]):
                        render_rec_card(cols[i], m, section=f"chat_{idx}_{m['id']}")

    if prompt := st.chat_input(t("chat_input_placeholder")):
        st.session_state.chat_messages.append({"role": "user", "content": prompt, "movies": []})

        with messages_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Searching & analyzing..."):
                    watchlist_titles = [m["title"] for m in st.session_state.get("watchlist", [])]
                    watchlist_ctx = (
                        f"The user's Watchlist includes: {', '.join(watchlist_titles)}."
                        if watchlist_titles
                        else "The user has no movies in Watchlist yet."
                    )
                    lang_name = "Polish" if get_lang() == "PL" else "English"
                    system_prompt = (
                        "You are a friendly, knowledgeable movie & TV expert in CineScope. "
                        f"{watchlist_ctx} "
                        "Help the user discover great movies and TV shows. When asked for recommendations or searches, "
                        "use your available tools (search_movies_tool, search_tv_tool, get_similar_movies_tool, get_trending_movies_tool) "
                        "to find accurate titles. Suggest 2-5 specific titles with a short justification for each. "
                        f"Keep your tone warm and concise. Respond in {lang_name}."
                    )

                    tool_collected_movies: list[dict] = []

                    tools = [
                        search_movies_tool,
                        search_tv_tool,
                        get_similar_movies_tool,
                        get_trending_movies_tool,
                    ]

                    contents = [system_prompt]
                    for m in st.session_state.chat_messages:
                        role_prefix = "User: " if m["role"] == "user" else "Assistant: "
                        contents.append(role_prefix + m["content"])

                    MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash"]

                    response = None
                    last_error = None

                    for model_name in MODELS:
                        try:
                            config = types.GenerateContentConfig(
                                tools=tools,
                                temperature=0.7,
                            )
                            response = client.models.generate_content(
                                model=model_name,
                                contents="\n".join(contents),
                                config=config,
                            )
                            break
                        except Exception as e:
                            last_error = e


                    if response:
                        reply = response.text or "Here are my recommendations for you:"
                        if hasattr(response, "function_calls") and response.function_calls:
                            for fc in response.function_calls:
                                name = fc.name
                                args = fc.args or {}
                                if name == "search_movies_tool":
                                    res = search_movies_tool(**args)
                                    tool_collected_movies.extend(res)
                                elif name == "search_tv_tool":
                                    res = search_tv_tool(**args)
                                    tool_collected_movies.extend(res)
                                elif name == "get_similar_movies_tool":
                                    res = get_similar_movies_tool(**args)
                                    tool_collected_movies.extend(res)
                                elif name == "get_trending_movies_tool":
                                    res = get_trending_movies_tool()
                                    tool_collected_movies.extend(res)
                    else:
                        reply, tool_collected_movies = _smart_search_fallback(prompt)

                    seen_ids = set()
                    final_movies = []
                    for m in tool_collected_movies:
                        m_id = m.get("id")
                        if m_id and m_id not in seen_ids:
                            seen_ids.add(m_id)
                            final_movies.append(m)

                    st.markdown(reply, unsafe_allow_html=True)
                    if final_movies:
                        n = min(5, len(final_movies))
                        cols = st.columns(n)
                        for i, m in enumerate(final_movies[:n]):
                            render_rec_card(cols[i], m, section=f"chat_live_{m['id']}")

                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": reply, "movies": final_movies}
                    )

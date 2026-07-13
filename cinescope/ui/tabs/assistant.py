"""AI Assistant tab for conversational movie recommendations."""

import os
import streamlit as st
from cinescope import tmdb

def _get_gemini_key() -> str | None:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("GEMINI_API_KEY")

def render() -> None:
    st.header("💬 Asystent Filmowy AI")
    st.markdown("Porozmawiaj z wirtualnym doradcą, który pomoże Ci znaleźć idealny film!")
    
    gemini_key = _get_gemini_key()
    if not gemini_key:
        st.warning("⚠️ Brak klucza `GEMINI_API_KEY`. Aby korzystać z asystenta, dodaj go w ustawieniach (secrets) lub ustaw zmienną środowiskową.")
        return
        
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
    except ImportError:
        st.error("Biblioteka `google-genai` nie jest zainstalowana.")
        return

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Cześć! Jestem Twoim wirtualnym doradcą filmowym. Na co masz dzisiaj ochotę?"}
        ]

    # Create a scrollable container for the chat history
    messages_container = st.container(height=500, border=False)

    with messages_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Napisz, jakiego filmu szukasz..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display the user's message immediately in the container
        with messages_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display the assistant's thinking and response in the container
            with st.chat_message("assistant"):
                with st.spinner("Myślę..."):
                    # Budujemy kontekst (np. ulubione filmy z Watchlist)
                    watchlist_titles = [m["title"] for m in st.session_state.watchlist]
                    watchlist_ctx = f"Użytkownik ma w swojej Watchlist: {', '.join(watchlist_titles)}." if watchlist_titles else "Użytkownik nie ma jeszcze filmów w Watchlist."
                    
                    system_prompt = (
                        "Jesteś ekspertem filmowym, wirtualnym doradcą w aplikacji CineScope. "
                        "Twoim zadaniem jest pomóc użytkownikowi znaleźć idealny film do obejrzenia. "
                        f"Znasz gust użytkownika: {watchlist_ctx} "
                        "Bądź zwięzły, uprzejmy i proponuj 2-3 konkretne tytuły wraz z krótkim uzasadnieniem dlaczego pasują. "
                        "Odpowiadaj w języku polskim."
                    )
                    
                    # Przygotowujemy historię dla Gemini
                    contents = [system_prompt]
                    for m in st.session_state.chat_messages:
                        role_prefix = "User: " if m["role"] == "user" else "Assistant: "
                        contents.append(role_prefix + m["content"])
                
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents="\\n".join(contents),
                    )
                    reply = response.text
                except Exception as e:
                    reply = f"Przepraszam, wystąpił błąd podczas łączenia z AI: {e}"
                
                st.markdown(reply)
                st.session_state.chat_messages.append({"role": "assistant", "content": reply})

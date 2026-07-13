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
    st.header("💬 AI Movie Assistant")
    st.markdown("Chat with a virtual advisor who will help you find the perfect movie!")
    
    gemini_key = _get_gemini_key()
    if not gemini_key:
        st.warning("⚠️ Missing `GEMINI_API_KEY`. To use the assistant, add it in secrets.toml or set the environment variable.")
        return
        
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
    except ImportError:
        st.error("The `google-genai` library is not installed.")
        return

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hi! I'm your virtual movie advisor. What are you in the mood for today?"}
        ]

    # Create a scrollable container for the chat history
    messages_container = st.container(height=500, border=False)

    with messages_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Tell me what kind of movie you're looking for..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display the user's message immediately in the container
        with messages_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display the assistant's thinking and response in the container
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Build context (e.g. favorite movies from Watchlist)
                    watchlist_titles = [m["title"] for m in st.session_state.watchlist]
                    watchlist_ctx = f"The user has the following movies in their Watchlist: {', '.join(watchlist_titles)}." if watchlist_titles else "The user does not have any movies in their Watchlist yet."
                    
                    system_prompt = (
                        "You are a movie expert and virtual advisor in the CineScope app. "
                        "Your task is to help the user find the perfect movie to watch. "
                        f"You know the user's taste: {watchlist_ctx} "
                        "Be concise, polite, and suggest 2-3 specific titles along with a short justification of why they fit. "
                        "Respond in English."
                    )
                    
                    # Prepare history for Gemini
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
                    reply = f"Sorry, an error occurred while connecting to the AI: {e}"
                
                st.markdown(reply)
                st.session_state.chat_messages.append({"role": "assistant", "content": reply})

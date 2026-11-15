"""Version 1: Streamlit + Gemini interactive escape room."""

import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from game_config import GAME_MASTER_PROMPT, GAME_TITLE, INTRO_TEXT

load_dotenv()

st.set_page_config(page_title=f"AI Escape Room | {GAME_TITLE}", page_icon="🔐")

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
ESCAPE_MARKER = "[[ESCAPED]]"


def restart_game() -> None:
    """Start a fresh session: only dialogue is kept as the game's memory."""
    st.session_state.messages = [{"role": "assistant", "content": INTRO_TEXT}]
    st.session_state.escaped = False


def get_game_master_reply(messages: list[dict[str, str]]) -> str:
    """Send the complete player/AI conversation to the LLM.

    There is deliberately NO Python-based validation for inventory, codes,
    and unlocked objects in Version 1. The LLM manages them from dialogue.
    """
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY has not been configured.")

    # Skip our fixed introduction. The first API turn is a player's message.
    conversation = [
        types.Content(
            role="user" if message["role"] == "user" else "model",
            parts=[types.Part.from_text(text=message["content"])],
        )
        for message in messages[1:]
    ]

    client = genai.Client(api_key=API_KEY)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=conversation,
        config=types.GenerateContentConfig(
            system_instruction=GAME_MASTER_PROMPT,
            temperature=0.5,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response. Please retry.")
    return response.text.strip()


if "messages" not in st.session_state:
    restart_game()

with st.sidebar:
    st.title("🔐 Escape Room")
    st.caption("Version 1 — AI Game Master")
    st.markdown("**Goal:** Find clues, solve puzzles, and escape the locked library.")
    st.markdown("**How to play**\n\n1. Type actions in the chat.\n2. Examine objects.\n3. Solve puzzles and collect items.\n4. Unlock the exit door.")
    if st.button("🔄 Restart game", use_container_width=True):
        restart_game()
        st.rerun()
    st.divider()
    st.markdown("**Objects you can examine:**")
    st.caption("Desk · Bookshelf · Painting · Clock · Drawer · Door")
    st.caption("This is Version 1: AI tracks the game through conversation history.")

st.title("🗝️ The Locked Library")
st.write("An AI-powered escape room. Can you find your way out?")

if not API_KEY:
    st.warning(
        "Gemini API key missing. Copy `.env.example` to `.env`, "
        "add your `GEMINI_API_KEY`, then restart Streamlit."
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.escaped:
    st.success("🎉 You escaped! Congratulations! Restart to play again.")

player_action = st.chat_input(
    "What do you want to do?",
    disabled=(not API_KEY) or st.session_state.escaped,
)

if player_action:
    st.session_state.messages.append({"role": "user", "content": player_action})
    with st.chat_message("user"):
        st.markdown(player_action)

    with st.chat_message("assistant"):
        with st.spinner("The Game Master is thinking..."):
            try:
                reply = get_game_master_reply(st.session_state.messages)
            except Exception as exc:
                # Keep the player action in chat and display a safe, actionable error.
                # The user can restart, or retry with a new message after fixing setup.
                st.error(
                    f"Could not get an AI reply ({type(exc).__name__}). "
                    "Check your API key, model name, internet connection, "
                    "and API quota."
                )
                reply = None

        if reply is not None:
            escaped = ESCAPE_MARKER in reply
            clean_reply = reply.replace(ESCAPE_MARKER, "").strip()
            st.markdown(clean_reply)
            st.session_state.messages.append(
                {"role": "assistant", "content": clean_reply}
            )
            if escaped:
                st.session_state.escaped = True
                st.success("🎉 You escaped! Congratulations! Restart to play again.")

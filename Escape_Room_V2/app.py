"""Version 2: atmospheric Streamlit UI on top of the unchanged Python game engine.

The visual styling lives in assets/theme.css. The Python engine still makes
all authoritative decisions; optional Gemini narration cannot change the state.
"""

from __future__ import annotations

import html
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from engine import new_game_state, process_action
from game_config import GAME_TITLE, INTRO_TEXT, KEY_NAME
from narrator import narrate_validated_event

load_dotenv()
st.set_page_config(
    page_title=f"The Locked Library · AI Escape Room V2",
    page_icon="🗝️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
THEME_CSS = Path(__file__).resolve().parent / "assets" / "theme.css"


def apply_theme() -> None:
    """Load the local stylesheet; no external asset or API is required."""
    st.markdown(f"<style>{THEME_CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def restart_game() -> None:
    st.session_state.game = new_game_state()
    st.session_state.messages = [{"role": "assistant", "content": INTRO_TEXT}]


def status_row(label: str, done: bool, done_text: str, undone_text: str) -> str:
    """Render trusted, hard-coded labels only (never user-supplied HTML)."""
    state_class = "is-complete" if done else "is-locked"
    icon = "✦" if done else "◇"
    subtitle = done_text if done else undone_text
    return (
        f'<div class="status-row {state_class}">'
        f'<span class="status-symbol">{icon}</span>'
        f'<div class="status-copy"><strong>{html.escape(label)}</strong>'
        f'<small>{html.escape(subtitle)}</small></div>'
        f'</div>'
    )


if "game" not in st.session_state or "messages" not in st.session_state:
    restart_game()

apply_theme()
game = st.session_state.game
key_collected = KEY_NAME in game["inventory"]
final_lock_released = game["door_code_accepted"] and game["key_turned"]
progress_count = sum([game["drawer_open"], key_collected, final_lock_released])
progress_percent = round(progress_count / 3 * 100)

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-emblem">✧</div>
            <div class="brand-overline">THE ARCHIVES · CHAPTER I</div>
            <div class="brand-title">The Locked<br><em>Library</em></div>
            <div class="brand-rule"><span>✦</span></div>
            <p>One room. Three secrets. One way out.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("↻  Restart adventure", use_container_width=True, type="secondary"):
        restart_game()
        st.rerun()

    st.markdown('<div class="sidebar-section-heading">YOUR ESCAPE</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="progress-card">
            <div class="progress-meta"><span>PUZZLE PROGRESS</span><strong>{progress_count} / 3</strong></div>
            <div class="progress-track"><div class="progress-fill" style="width:{progress_percent}%"></div></div>
            <div class="progress-label">{'THE EXIT IS OPEN' if game['escaped'] else 'THE LIBRARY AWAITS'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section-heading">LOCK STATUS</div>'
        '<div class="status-panel">'
        + status_row("Desk drawer", game["drawer_open"], "Combination accepted", "Three-digit combination")
        + status_row("Brass key", key_collected, "Safely in your inventory", "Not yet collected")
        + status_row("Exit door", final_lock_released, "Both locks released", "Key + four-digit code needed")
        + '</div>',
        unsafe_allow_html=True,
    )

    inventory = (
        '<div class="inventory-item"><span>🗝</span> Brass key</div>'
        if key_collected
        else '<p class="inventory-empty">Your pockets are empty… for now.</p>'
    )
    st.markdown(
        f'<div class="sidebar-section-heading">INVENTORY</div>'
        f'<div class="inventory-panel">{inventory}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="sidebar-footnote">
            <div class="sidebar-section-heading">AVAILABLE TO EXPLORE</div>
            <div class="object-tags"><span>Desk</span><span>Bookshelf</span><span>Painting</span>
            <span>Clock</span><span>Drawer</span><span>Door</span></div>
            <p><strong>{game['actions_count']}</strong> actions taken · Type <b>help</b> for a clue</p>
            <p>Version 2 · Rules enforced by Python</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="chapter-strip"><span>✦ &nbsp; A TEXT-BASED MYSTERY</span><span>EST. MIDNIGHT · AN UNKNOWN YEAR</span></div>
    <section class="library-hero">
        <div class="hero-inner">
            <span class="hero-eyebrow">THE DOOR IS LOCKED. THE CLOCK HAS STOPPED.</span>
            <h1>The Locked <em>Library</em></h1>
            <p>The quiet is unsettling. The answers are hiding in plain sight.<br>
            Every object has a story — if you dare to look closer.</p>
            <div class="hero-divider"><span>✧</span></div>
            <div class="hero-features"><span>✦ Explore the room</span><span>✦ Uncover the clues</span>
            <span>✦ Find your way out</span></div>
        </div>
    </section>
    <div class="section-ribbon"><span>THE CHRONICLE</span><span>YOUR STORY UNFOLDS BELOW</span></div>
    """,
    unsafe_allow_html=True,
)

if not API_KEY:
    st.info(
        "Gemini narration isn't configured. The complete escape room still works "
        "using Python. Add your GEMINI_API_KEY to your local .env to enable AI atmosphere."
    )

for item in st.session_state.messages:
    role = item["role"]
    with st.chat_message(role, avatar="🕯️" if role == "assistant" else "✒️"):
        st.markdown(item["content"])
        if item.get("atmosphere"):
            st.caption(f"✧ {item['atmosphere']}")
        elif item.get("narration_error"):
            st.caption("The narrator is quiet tonight. The game still works.")

if game["escaped"]:
    st.markdown(
        """
        <section class="victory-panel">
            <span class="victory-ornament">✦ &nbsp; THE FINAL SEAL IS BROKEN &nbsp; ✦</span>
            <h2>YOU HAVE ESCAPED</h2>
            <p>The heavy oak door swings open. Cold night air brushes your face.<br>
            Behind you, the library falls silent once more.</p>
            <div class="victory-divider">✧ ✧ ✧</div>
            <span class="victory-footnote">THE END · YOUR FREEDOM IS EARNED</span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Your escape was validated by the Python game engine — not the AI.")
else:
    st.markdown(
        '<div class="input-helper">✒ &nbsp; WRITE YOUR NEXT MOVE &nbsp; '
        '<span>Try “Examine the desk” or type “help”</span></div>',
        unsafe_allow_html=True,
    )

player_text = st.chat_input(
    "What will you do next?", disabled=game["escaped"]
)
if player_text:
    # The only place player commands are processed: deterministic Python.
    st.session_state.messages.append({"role": "user", "content": player_text})
    outcome = process_action(st.session_state.game, player_text)
    reply = outcome["message"]
    message = {"role": "assistant", "content": reply}

    # Optional atmosphere cannot change the game's Python-approved result.
    if API_KEY and not outcome["escaped"] and outcome["kind"] == "info":
        try:
            with st.spinner("The library whispers..."):
                extra = narrate_validated_event(
                    reply, api_key=API_KEY, model=MODEL_NAME, escaped=outcome["escaped"]
                )
            if extra:
                message["atmosphere"] = extra
        except Exception:
            message["narration_error"] = True

    st.session_state.messages.append(message)
    # Refresh the sidebar and victory card immediately after every action.
    st.rerun()

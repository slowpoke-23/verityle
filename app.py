import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from main import MAX_ATTEMPTS, SEQUENCE_LENGTH, WORDS, new_game, score_guess

ASSETS = Path("assets")
IMAGES = ASSETS / "images"
AUDIO = ASSETS / "audio"

COLORS = {
    "green": "#35A853",
    "yellow": "#E8B923",
    "black": "#202124",
    "empty": "#DADCE0",
}

st.set_page_config(
    page_title="Verityle",
    page_icon="🙂",
    layout="wide",
)


def initialize_game():
    st.session_state.answer = new_game()
    st.session_state.guess = []
    st.session_state.history = []
    st.session_state.game_over = False
    st.session_state.won = False


if "answer" not in st.session_state:
    initialize_game()


def get_image_data(word):
    path = IMAGES / f"{word}.png"

    if not path.exists():
        return None

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_row(words, feedback=None):
    tiles = []

    for i in range(SEQUENCE_LENGTH):
        word = words[i] if i < len(words) else None
        color = feedback[i] if feedback else "empty"
        background = COLORS[color]
        content = ""

        if word:
            source = get_image_data(word)
            if source:
                content = (
                    f'<img src="{source}" '
                    'style="width:100%;height:100%;'
                    'object-fit:contain;">'
                )

        tiles.append(
            f'<div style="background:{background};'
            'aspect-ratio:1;min-width:0;'
            'border-radius:5px;overflow:hidden;'
            'display:flex;align-items:center;'
            'justify-content:center;padding:1px;'
            f'box-sizing:border-box;">{content}</div>'
        )

    st.markdown(
        '<div style="display:grid;'
        'grid-template-columns:repeat(8,minmax(0,1fr));'
        'gap:3px;width:100%;max-width:100%;'
        'box-sizing:border-box;margin:4px 0 8px 0;">'
        + "".join(tiles)
        + "</div>",
        unsafe_allow_html=True,
    )


# ---------- Styles (single block) ----------
css = """
<style>
.block-container {
    width: 100% !important;
    max-width: 900px !important;
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-left: 8px !important;
    padding-right: 8px !important;
}

h1 {
    font-size: clamp(1.5rem, 5vw, 2.5rem) !important;
}

/* Keep columns side by side, even on phones */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 6px !important;
    width: 100% !important;
}

[data-testid="stHorizontalBlock"] > [data-testid="column"],
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0 !important;
    width: 0 !important;
    flex: 1 1 0% !important;
    padding: 0 !important;
}

/* THE FIX: make every button (and its wrappers) fill its column.
   Without this, buttons shrink to their label ("Undo", " ") and
   sit at the left of a wide column, which looks like big gaps. */
[data-testid="stHorizontalBlock"] [data-testid="stElementContainer"],
[data-testid="stHorizontalBlock"] [data-testid="stButton"] {
    width: 100% !important;
    min-width: 0 !important;
}

[data-testid="stButton"] button {
    width: 100% !important;
    min-width: 0 !important;
    min-height: 44px;
}

/* Submit spans the full width (it's outside any column) */
.st-key-submit_btn,
.st-key-submit_btn [data-testid="stButton"],
.st-key-submit_btn button {
    width: 100% !important;
    min-width: 0 !important;
}

.st-key-submit_btn button {
    min-height: 48px;
}

@media screen and (max-width: 600px) {
    .block-container {
        padding-left: 4px !important;
        padding-right: 4px !important;
        padding-top: 8px !important;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 4px !important;
    }

    [data-testid="stButton"] button {
        padding: 2px !important;
        font-size: 14px !important;
    }
}
"""

# Face-image buttons
for word in WORDS:
    source = get_image_data(word)

    if source:
        css += f"""
.st-key-pick_{word} button {{
    background-image: url("{source}");
    background-position: center;
    background-repeat: no-repeat;
    background-size: contain;
    background-color: #eeeeee;
    border: 2px solid #777777;
    border-radius: 10px;
    height: clamp(70px, 22vw, 110px) !important;
    min-height: 70px !important;
    max-height: none !important;
}}
.st-key-pick_{word} button p {{
    visibility: hidden;
}}
.st-key-pick_{word} button:hover {{
    border-color: #35A853;
    background-color: #eeeeee;
}}
"""

css += "</style>"
st.markdown(css, unsafe_allow_html=True)


st.title("Verityle")

# Previous guesses remain at the top.
for guess, feedback in st.session_state.history:
    render_row(guess, feedback)

# Current guess.
if not st.session_state.game_over:
    render_row(st.session_state.guess)

    face_columns = st.columns(4, gap="small")

    for i, word in enumerate(WORDS):
        with face_columns[i]:
            if st.button(
                " ",
                key=f"pick_{word}",
                disabled=len(st.session_state.guess) >= SEQUENCE_LENGTH,
            ):
                st.session_state.guess.append(word)
                st.rerun()

    undo_col, clear_col = st.columns(2, gap="small")

    with undo_col:
        if st.button("Undo", disabled=not st.session_state.guess):
            st.session_state.guess.pop()
            st.rerun()

    with clear_col:
        if st.button("Clear", disabled=not st.session_state.guess):
            st.session_state.guess = []
            st.rerun()

    if st.button(
        "Submit",
        key="submit_btn",
        type="primary",
        disabled=len(st.session_state.guess) != SEQUENCE_LENGTH,
    ):
        guess = st.session_state.guess.copy()
        feedback = score_guess(guess, st.session_state.answer)

        st.session_state.history.append((guess, feedback))
        st.session_state.guess = []

        if guess == st.session_state.answer:
            st.session_state.won = True
            st.session_state.game_over = True
        elif len(st.session_state.history) >= MAX_ATTEMPTS:
            st.session_state.game_over = True

        st.rerun()


# Sound: phones only allow audio to start inside the tap itself, and a
# Streamlit rerun happens too late for that. So the sounds are loaded once
# into the page and played straight from the click, with no rerun involved.
def get_audio_sources():
    sources = {}

    for word in WORDS:
        path = AUDIO / f"{word}.mp3"

        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            sources[word] = f"data:audio/mpeg;base64,{encoded}"

    return sources


AUDIO_JS = """
(function () {
    if (window.__verityleAudio) return;

    var sources = __SOURCES__;
    var audios = {};

    Object.keys(sources).forEach(function (word) {
        var a = new Audio(sources[word]);
        a.preload = "auto";
        audios[word] = a;
    });
    window.__verityleAudio = audios;

    document.addEventListener("click", function (e) {
        var holder = e.target.closest && e.target.closest('[class*="st-key-pick_"]');
        if (!holder) return;

        var btn = holder.querySelector("button");
        if (btn && btn.disabled) return;

        var match = holder.className.match(/st-key-pick_([A-Za-z0-9_]+)/);
        var audio = match && audios[match[1]];
        if (!audio) return;

        audio.currentTime = 0;
        var p = audio.play();
        if (p && p.catch) p.catch(function () {});
    }, true);
})();
"""

audio_script = AUDIO_JS.replace("__SOURCES__", json.dumps(get_audio_sources()))

components.html(
    f"""
    <script>
    (function () {{
        var doc = window.parent.document;
        if (doc.getElementById("verityle-audio-script")) return;
        var s = doc.createElement("script");
        s.id = "verityle-audio-script";
        s.textContent = {json.dumps(audio_script)};
        doc.head.appendChild(s);
    }})();
    </script>
    """,
    height=0,
)


if st.session_state.game_over:
    if st.session_state.won:
        st.success("You got it!")
    else:
        st.error("Out of guesses!")
        render_row(
            st.session_state.answer,
            ["green"] * SEQUENCE_LENGTH,
        )

    if st.button("Play again", type="primary"):
        initialize_game()
        st.rerun()
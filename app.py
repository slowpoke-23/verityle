
import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from main import WORDS, SEQUENCE_LENGTH, MAX_ATTEMPTS
from main import new_game, score_guess

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

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: max(0.5rem, 2vw);
        padding-right: max(0.5rem, 2vw);
        max-width: 900px;
    }

    h1 {
        font-size: clamp(1.5rem, 5vw, 2.5rem) !important;
    }

    [data-testid="stButton"] button {
        min-height: 42px;
    }

    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.35rem;
            padding-right: 0.35rem;
        }

        [data-testid="stVerticalBlock"] {
            gap: 0.4rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def initialize_game():
    st.session_state.answer = new_game()
    st.session_state.guess = []
    st.session_state.history = []
    st.session_state.game_over = False
    st.session_state.won = False
    st.session_state.sound_data = None


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


# Style native buttons with the corresponding face images.
css = """
<style>
"""

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
            height: clamp(58px, 18vw, 90px) !important;
            min-height: 42px !important;
            max-height: 80px !important;
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


# Responsive layout for phones and computers
st.markdown("""
<style>
/* Keep the eight guess tiles in one horizontal row */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 4px !important;
    width: 100% !important;
}

[data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: 0 !important;
    width: 0 !important;
    flex: 1 1 0% !important;
    padding: 0 !important;
}

/* Let the game use the available screen width */
.block-container {
    width: 100% !important;
    max-width: 900px !important;
    padding-left: 8px !important;
    padding-right: 8px !important;
}

/* Smaller buttons and tighter spacing on phones */
@media screen and (max-width: 600px) {
    [data-testid="stHorizontalBlock"] {
        gap: 3px !important;
    }

    .block-container {
        padding-left: 4px !important;
        padding-right: 4px !important;
        padding-top: 8px !important;
    }

    [data-testid="stButton"] button {
        min-height: 36px !important;
        padding: 2px !important;
        font-size: 12px !important;
    }

    h1 {
        font-size: 24px !important;
    }
}

/* Larger controls on computers */
@media screen and (min-width: 601px) {
    [data-testid="stButton"] button {
        min-height: 44px;
    }
}


@media screen and (max-width: 600px) {
    [data-testid="stHorizontalBlock"] {
        gap: 2px !important;
    }

    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        padding-left: 1px !important;
        padding-right: 1px !important;
        min-width: 0 !important;
    }

    [data-testid="stButton"] {
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    [data-testid="stButton"] button {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        min-height: 36px !important;
        padding: 2px !important;
        margin: 0 !important;
        font-size: 12px !important;
    }

    .block-container {
        padding-left: 4px !important;
        padding-right: 4px !important;
    }
}


</style>
""", unsafe_allow_html=True)


st.title("Verityle")

# Previous guesses remain at the top.
for guess, feedback in st.session_state.history:
    render_row(guess, feedback)

# Current guess.
if not st.session_state.game_over:
    render_row(st.session_state.guess)

    face_columns = st.columns(4, gap="xxsmall")

    for i, word in enumerate(WORDS):
        with face_columns[i]:
            if st.button(
                " ",
                key=f"pick_{word}",
                use_container_width=False,
                disabled=len(st.session_state.guess) >= SEQUENCE_LENGTH,
            ):
                st.session_state.guess.append(word)

                audio_path = AUDIO / f"{word}.mp3"
                if audio_path.exists():
                    st.session_state.sound_data = (
                        base64.b64encode(
                            audio_path.read_bytes()
                        ).decode("ascii")
                    )

                st.rerun()

    left, right = st.columns(2)

    with left:
        if st.button(
            "Undo",
            disabled=not st.session_state.guess,
            use_container_width=False,
        ):
            st.session_state.guess.pop()
            st.session_state.sound_data = None
            st.rerun()

    with right:
        if st.button(
            "Clear",
            disabled=not st.session_state.guess,
            use_container_width=False,
        ):
            st.session_state.guess = []
            st.session_state.sound_data = None
            st.rerun()

    if st.button(
        "Submit",
        type="primary",
        disabled=len(st.session_state.guess) != SEQUENCE_LENGTH,
        use_container_width=False,
    ):
        guess = st.session_state.guess.copy()
        feedback = score_guess(guess, st.session_state.answer)

        st.session_state.history.append((guess, feedback))
        st.session_state.guess = []
        st.session_state.sound_data = None

        if guess == st.session_state.answer:
            st.session_state.won = True
            st.session_state.game_over = True
        elif len(st.session_state.history) >= MAX_ATTEMPTS:
            st.session_state.game_over = True

        st.rerun()


# Hidden audio: no visible player controls.
if st.session_state.sound_data:
    components.html(
        f"""
        <audio autoplay>
            <source
                src="data:audio/mpeg;base64,{st.session_state.sound_data}"
                type="audio/mpeg">
        </audio>
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

    if st.button("Play again", type="primary", use_container_width=False):
        initialize_game()
        st.rerun()

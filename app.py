import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


DAILY = "Daily"
UNLIMITED = "Unlimited"
EMOJIS = {"green": "🟩", "yellow": "🟨", "black": "⬛"}
GAME_URL = "https://verityle.streamlit.app/"

try:
    # Everyone's "today" is the same day, wherever they are.
    DAILY_TZ = ZoneInfo("America/New_York")
except ZoneInfoNotFoundError:
    DAILY_TZ = timezone.utc


def today():
    return datetime.now(DAILY_TZ).date().isoformat()


def make_game(mode):
    if mode == DAILY:
        date = today()
        answer = new_game(seed=f"verityle-{date}")
    else:
        date = None
        answer = new_game()

    return {
        "answer": answer,
        "date": date,
        "guess": [],
        "history": [],
        "game_over": False,
        "won": False,
    }


def build_share_text(game):
    attempts = len(game["history"])
    score = attempts if game["won"] else "X"
    lines = [f"Verityle {score}/{MAX_ATTEMPTS}"]

    if game["date"]:
        lines.append(game["date"])

    for _, feedback in game["history"]:
        lines.append("".join(EMOJIS[color] for color in feedback))

    lines.append("")
    lines.append(f"Play the game at {GAME_URL}")

    return "\n".join(lines)


def render_share_button(text):
    components.html(
        f"""
        <style>
            body {{ margin: 0; font-family: sans-serif; }}
            button {{
                width: 100%; height: 48px; border: 0; border-radius: 8px;
                background: #35A853; color: white; font-size: 16px;
                font-weight: 600; cursor: pointer;
            }}
            textarea {{
                display: none; width: 100%; height: 120px; margin-top: 8px;
                box-sizing: border-box; font-size: 16px;
            }}
        </style>
        <button id="share">Share</button>
        <textarea id="fallback" readonly></textarea>
        <script>
        (function () {{
            var text = {json.dumps(text)};
            var btn = document.getElementById("share");
            var box = document.getElementById("fallback");

            function legacyCopy() {{
                box.value = text;
                box.style.display = "block";
                try {{ window.frameElement.style.height = "190px"; }} catch (e) {{}}
                box.select();
                box.setSelectionRange(0, text.length);
                var ok = false;
                try {{ ok = document.execCommand("copy"); }} catch (e) {{}}
                if (ok) box.style.display = "none";
                return ok;
            }}

            btn.addEventListener("click", function () {{
                var done = function (ok) {{
                    btn.textContent = ok
                        ? "Copied!"
                        : "Press and hold the text below to copy";
                    if (ok) setTimeout(function () {{
                        btn.textContent = "Share";
                    }}, 2000);
                }};

                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).then(
                        function () {{ done(true); }},
                        function () {{ done(legacyCopy()); }}
                    );
                }} else {{
                    done(legacyCopy());
                }}
            }});
        }})();
        </script>
        """,
        height=56,
    )


if "games" not in st.session_state:
    st.session_state.games = {}


def get_game(mode):
    """Return this session's game for a mode, starting a new daily on a new day."""
    game = st.session_state.games.get(mode)

    if game is None or (mode == DAILY and game["date"] != today()):
        game = make_game(mode)
        st.session_state.games[mode] = game

    return game


# Remembers today's daily guesses in the browser, so a reload can't be used to
# replay it. See storage_component/index.html.
storage = components.declare_component(
    "verityle_storage",
    path=str(Path(__file__).parent / "storage_component"),
)


def daily_payload(game):
    """What gets saved: just the date and the guesses made so far."""
    if not game["history"]:
        return None

    return {
        "date": game["date"],
        "guesses": [guess for guess, _ in game["history"]],
    }


def restore_daily(game, stored):
    """Replay saved guesses into a fresh daily game. Ignores bad or old data."""
    if game["history"] or not isinstance(stored, dict):
        return

    if stored.get("date") != game["date"]:
        return

    guesses = stored.get("guesses")
    if not isinstance(guesses, list):
        return

    for guess in guesses[:MAX_ATTEMPTS]:
        valid = (
            isinstance(guess, list)
            and len(guess) == SEQUENCE_LENGTH
            and all(word in WORDS for word in guess)
        )
        if not valid:
            break

        game["history"].append((guess, score_guess(guess, game["answer"])))

        if guess == game["answer"]:
            game["won"] = True
            game["game_over"] = True
            break

    if len(game["history"]) >= MAX_ATTEMPTS:
        game["game_over"] = True


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
        padding-top: 3.5rem !important;
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

mode = st.radio(
    "Mode",
    [DAILY, UNLIMITED],
    horizontal=True,
    label_visibility="collapsed",
    key="mode",
)

# Load and save today's daily guesses in the browser.
daily_game = get_game(DAILY)
browser_value = storage(
    save=daily_payload(daily_game),
    default=None,
    key="verityle_storage",
)
if browser_value:
    restore_daily(daily_game, browser_value.get("stored"))

game = get_game(mode)

if mode == DAILY:
    st.caption(f"Daily puzzle for {game['date']}. Everyone gets the same one.")

# Previous guesses remain at the top.
for guess, feedback in game["history"]:
    render_row(guess, feedback)

# Current guess.
if not game["game_over"]:
    render_row(game["guess"])

    face_columns = st.columns(4, gap="small")

    for i, word in enumerate(WORDS):
        with face_columns[i]:
            if st.button(
                " ",
                key=f"pick_{word}",
                disabled=len(game["guess"]) >= SEQUENCE_LENGTH,
            ):
                game["guess"].append(word)
                st.rerun()

    undo_col, clear_col = st.columns(2, gap="small")

    with undo_col:
        if st.button("Undo", disabled=not game["guess"]):
            game["guess"].pop()
            st.rerun()

    with clear_col:
        if st.button("Clear", disabled=not game["guess"]):
            game["guess"] = []
            st.rerun()

    if st.button(
        "Submit",
        key="submit_btn",
        type="primary",
        disabled=len(game["guess"]) != SEQUENCE_LENGTH,
    ):
        guess = game["guess"].copy()
        feedback = score_guess(guess, game["answer"])

        game["history"].append((guess, feedback))
        game["guess"] = []

        if guess == game["answer"]:
            game["won"] = True
            game["game_over"] = True
        elif len(game["history"]) >= MAX_ATTEMPTS:
            game["game_over"] = True

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


if game["game_over"]:
    if game["won"]:
        st.success("You got it!")
    else:
        st.error("Out of guesses!")
        render_row(game["answer"], ["green"] * SEQUENCE_LENGTH)

    render_share_button(build_share_text(game))

    if mode == UNLIMITED:
        if st.button("Play again", type="primary"):
            st.session_state.games[UNLIMITED] = make_game(UNLIMITED)
            st.rerun()
    else:
        st.info("Come back tomorrow for a new daily puzzle, or switch to Unlimited.")
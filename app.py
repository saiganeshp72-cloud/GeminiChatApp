import os, pathlib, io, time
import streamlit as st
from dotenv import load_dotenv, dotenv_values
from google import genai
from gtts import gTTS

# ----------------- env & client -----------------
HERE = pathlib.Path(__file__).resolve().parent

# Force override so .env wins over any pre-set OS variable
load_dotenv(dotenv_path=HERE / ".env", override=True)

# Read from env; if empty also read the file directly (belt & suspenders)
API_KEY = (os.getenv("GOOGLE_API_KEY")
           or dotenv_values(HERE / ".env").get("GOOGLE_API_KEY", ""))
API_KEY = API_KEY.strip().strip('"').strip("'").lstrip("\ufeff")

st.set_page_config(page_title="Ganesh ChatBot", page_icon="💬", layout="centered")

if not API_KEY:
    st.error("GOOGLE_API_KEY not found in .env")
    st.stop()

DEFAULT_MODEL = "models/gemini-2.5-pro"  # you can switch to "models/gemini-2.5-flash"

@st.cache_resource(show_spinner=False)
def get_client(api_key: str):
    return genai.Client(api_key=api_key)

client = get_client(API_KEY)

# Quick ping (list once to warm the client)
try:
    _ = list(client.models.list())[:1]
except Exception as e:
    st.error(f"Failed to initialize Gemini client: {e}")
    st.stop()

# ----------------- TTS UI -----------------
def tts_ui():
    st.title("🔊 Text to Speech")
    st.caption("Type text → generate speech → play & download (gTTS).")

    with st.form("tts_form"):
        text = st.text_area("Enter text", height=160, placeholder="Type something to speak…")
        col1, col2, col3 = st.columns(3)
        with col1:
            lang = st.selectbox(
                "Language",
                ["en", "es", "fr", "de", "hi", "te", "ta", "zh-cn"],
                index=0
            )
        with col2:
            accent = st.selectbox(
                "Accent (tld)",
                ["com", "co.uk", "com.au", "co.in"],
                index=0,
                help="Different domains slightly change the accent."
            )
        with col3:
            slow = st.toggle("Slow speed", value=False)

        submitted = st.form_submit_button("Generate Audio 🔈")

    if submitted:
        if not text.strip():
            st.warning("Please enter some text.")
            return

        try:
            with st.spinner("Generating audio…"):
                tts = gTTS(text=text, lang=lang, slow=slow, tld=accent)
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                filename = f"tts_{lang}_{int(time.time())}.mp3"
            st.success("Done!")
            st.audio(buf, format="audio/mp3")
            st.download_button("Download MP3", data=buf, file_name=filename, mime="audio/mpeg")
            st.info("Tip: Try different Language + Accent (tld) for better pronunciation.")
        except Exception as e:
            st.error(f"TTS failed: {e}")

# ----------------- Chat UI -----------------
def chat_ui():
    st.title("💬 Ganesh ChatBot (Streamlit)")
    st.caption("Your local browser chat using Google AI Studio key")

    # ---- sidebar settings
    with st.sidebar:
        st.header("Settings")
        model = st.selectbox(
            "Model",
            options=[DEFAULT_MODEL, "models/gemini-2.5-flash"],
            index=0,
            help="These names work with your current SDK (v1beta)."
        )

        st.divider()
        st.subheader("Voice output")
        speak_enabled = st.toggle("🔊 Speak assistant replies", value=True)
        tts_lang = st.selectbox("Language", ["en", "es", "fr", "de", "hi", "te", "ta", "zh-cn"], index=0)
        tts_accent = st.selectbox("Accent (tld)", ["com", "co.uk", "com.au", "co.in"], index=0)
        tts_slow = st.toggle("Slow speed", value=False)

        if st.button("Clear chat"):
            st.session_state.history = []
            # also clear last audio
            st.session_state.pop("last_tts_audio", None)

    # ---- keep chat history in session
    if "history" not in st.session_state:
        st.session_state.history = []

    # ---- render history
    for turn in st.session_state.history:
        role = turn["role"]
        text = turn["parts"][0].get("text", "")
        with st.chat_message("assistant" if role == "model" else "user"):
            st.markdown(text)

    # ---- input bar
    prompt = st.chat_input("Type your message…")

    if prompt:
        # show user bubble immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.history.append({"role": "user", "parts": [{"text": prompt}]})

        # call Gemini with full history (v1beta style)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    resp = client.models.generate_content(
                        model=model,
                        contents=st.session_state.history
                    )
                    answer = (resp.text or "").strip()
                except Exception as e:
                    answer = f"Sorry, request failed: {e}"

                # show text answer
                st.markdown(answer)

                # optional: speak the answer
                if speak_enabled and answer:
                    try:
                        tts = gTTS(text=answer, lang=tts_lang, slow=tts_slow, tld=tts_accent)
                        buf = io.BytesIO()
                        tts.write_to_fp(buf)
                        buf.seek(0)
                        # keep a reference so the audio doesn't disappear on rerun
                        st.session_state.last_tts_audio = buf.getvalue()

                        st.audio(st.session_state.last_tts_audio, format="audio/mp3")
                        ts = int(time.time())
                        st.download_button(
                            label="Download reply as MP3",
                            data=st.session_state.last_tts_audio,
                            file_name=f"reply_{tts_lang}_{ts}.mp3",
                            mime="audio/mpeg"
                        )
                    except Exception as e:
                        st.warning(f"Could not synthesize speech: {e}")

        st.session_state.history.append({"role": "model", "parts": [{"text": answer}]})


# ----------------- Simple nav -----------------
mode = st.sidebar.radio("Navigate", ["Chat", "Text to Speech"], index=0)

if mode == "Chat":
    chat_ui()
else:
    tts_ui()

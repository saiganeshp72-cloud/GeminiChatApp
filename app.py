import os, pathlib
import streamlit as st
from dotenv import load_dotenv, dotenv_values
from google import genai

HERE = pathlib.Path(__file__).resolve().parent

# hi 
# Force override so .env wins over any pre-set OS variable
load_dotenv(dotenv_path=HERE / ".env", override=True)

# Read from env, if empty also read the file directly (belt & suspenders)
API_KEY = (os.getenv("GOOGLE_API_KEY")
           or dotenv_values(HERE / ".env").get("GOOGLE_API_KEY", ""))
API_KEY = API_KEY.strip().strip('"').strip("'").lstrip("\ufeff")

if not API_KEY:
    st.error("GOOGLE_API_KEY not found in .env")
    st.stop()

# Make the cache depend on the key so it refreshes if you change it
@st.cache_resource(show_spinner=False)
def get_client(api_key: str):
    return genai.Client(api_key=api_key)

client = get_client(API_KEY)

# Quick ping (no page_size param on new SDK)
_ = list(client.models.list())[:1]

# NOTE: your interpreter is using v1beta implicitly, so use full 'models/...' IDs
DEFAULT_MODEL = "models/gemini-2.5-pro"  # you can switch to "models/gemini-2.5-flash"

@st.cache_resource(show_spinner=False)
def get_client():
    return genai.Client(api_key=API_KEY)

client = get_client()

# ----------------- ui -----------------
st.set_page_config(page_title="Gemini Chat", page_icon="💬", layout="centered")

st.title("💬 Ganesh ChatBot (Streamlit)")
st.caption("Your local browser chat using Google AI Studio key")

# model selector (safe defaults)
with st.sidebar:
    st.header("Settings")
    model = st.selectbox(
        "Model",
        options=[DEFAULT_MODEL, "models/gemini-2.5-flash"],
        index=0,
        help="These names work with your current SDK (v1beta)."
    )
    if st.button("Clear chat"):
        st.session_state.history = []

# keep chat history in session
if "history" not in st.session_state:
    st.session_state.history = []

# render chat history
for turn in st.session_state.history:
    role = turn["role"]
    text = turn["parts"][0].get("text", "")
    with st.chat_message("assistant" if role == "model" else "user"):
        st.markdown(text)

# input bar
prompt = st.chat_input("Type your message…")

if prompt:
    # show user bubble immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append({"role": "user", "parts": [{"text": prompt}]})

    # call Gemini with full history (v1beta format)
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            resp = client.models.generate_content(
                model=model,
                contents=st.session_state.history
            )
            answer = (resp.text or "").strip()
            st.markdown(answer)
    st.session_state.history.append({"role": "model", "parts": [{"text": answer}]})

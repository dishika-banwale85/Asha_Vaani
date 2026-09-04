import os
import io
import requests
import streamlit as st
from gtts import gTTS
from groq import Groq
from dotenv import load_dotenv  # <-- Add this import

# Load the secret keys from your .env file
load_dotenv()

# --- App Configuration ---
st.set_page_config(
    page_title="Asha Vani",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)


BACKEND_URL = "http://127.0.0.1:8000"
# Securely grab the key from the environment
secure_groq_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=secure_groq_key)


# --- Helper Function for Text-to-Speech ---
def text_to_speech(text: str) -> io.BytesIO:
    clean_text = text.replace("*", "").replace("#", "").replace("-", "")
    tts = gTTS(text=clean_text, lang="hi", slow=False)
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

# --- Mobile UI Custom CSS Styling ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 5rem; max-width: 500px; }
    
    .mobile-header {
        background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        text-align: center;
    }
    .mobile-header h2 { margin: 0; font-size: 1.5rem; font-weight: 700; color: white;}
    .mobile-header p { margin: 4px 0 0 0; font-size: 0.85rem; opacity: 0.9; }
    .status-badge {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.25);
        padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; margin-top: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Top Header Section ---
st.markdown("""
    <div class="mobile-header">
        <h2>🎙️ Asha Vani</h2>
        <p>Voice & Decision Support for ASHA Workers</p>
        <span class="status-badge">🟢 Voice Enabled</span>
    </div>
""", unsafe_allow_html=True)

# --- Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# --- Render Chat History ---
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if msg["role"] == "assistant":
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

            if msg.get("log_id"):
                col1, col2, _ = st.columns([1, 1, 8])
                if col1.button("👍", key=f"up_{idx}"):
                    requests.post(f"{BACKEND_URL}/feedback", json={"log_id": msg["log_id"], "feedback": 1})
                    st.toast("Dhanyawaad!", icon="✅")
                if col2.button("👎", key=f"down_{idx}"):
                    requests.post(f"{BACKEND_URL}/feedback", json={"log_id": msg["log_id"], "feedback": -1})
                    st.toast("Feedback logged.", icon="📝")

# --- Handle New User Query ---
user_input = None
is_voice_input = False

# 1. Text Input Check
text_prompt = st.chat_input("Poochiye (Ask a question)...")
if text_prompt:
    user_input = text_prompt
    is_voice_input = False

# 2. Voice Input Check
audio_value = st.audio_input("Mic dabayein aur bolen (Tap to speak)")
if audio_value and audio_value != st.session_state.last_processed_audio:
    st.session_state.last_processed_audio = audio_value
    
    with st.spinner("Aapki aawaz sun rahe hain..."):
        try:
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.wav", audio_value.getvalue()),
                model="whisper-large-v3",
                response_format="json"
            )
            user_input = transcription.text
            is_voice_input = True
        except Exception as e:
            st.error(f"Voice recognition failed: {e}")

# --- Process the Input ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Jawab tayar ho raha hai..."):
            try:
                res = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input})
                if res.status_code == 200:
                    data = res.json()
                    bot_reply = data.get("response", "Koi jawab nahi mil saka.")
                    log_id = data.get("log_id")
                    audio_bytes = None

                    # If user spoke, generate audio BEFORE showing the text
                    if is_voice_input:
                        audio_bytes = text_to_speech(bot_reply)
                        st.markdown(bot_reply)
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                    
                    # If user typed, just show text instantly (no audio)
                    else:
                        st.markdown(bot_reply)

                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": bot_reply,
                        "log_id": log_id,
                        "audio": audio_bytes
                    })
                    st.rerun()
                else:
                    st.error("Server connection failed.")
            except Exception as e:
                st.error(f"Backend error: {e}")
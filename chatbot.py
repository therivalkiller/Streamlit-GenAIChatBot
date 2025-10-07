"""
Multi-Modal AI Chatbot - Main Entry Point
"""
from dotenv import load_dotenv
import streamlit as st

# Import custom modules
from database import init_db, load_sessions_from_db
from models import DEFAULT_MODEL
from ui_components import (
    render_sidebar, 
    render_session_header, 
    render_chat_messages, 
    render_model_selector
)
from chat_logic import process_user_message

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="Chatbot", page_icon="🤖", layout="centered")
# Hide Streamlit's default menu and footer
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .stToolbar {display: none;}
    .stDecoration {display: none;}
    .viewerBadge_container__1QSob {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


st.title("💬 Generative AI Chatbot")

# Initialize database
if "db_inited" not in st.session_state:
    init_db()
    st.session_state.db_inited = True

# Load sessions from database
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
    db_sessions = load_sessions_from_db()
    for s in db_sessions:
        st.session_state.sessions[s["id"]] = {
            "title": s["title"], 
            "created_at": s["created_at"], 
            "model_id": s["model_id"] if s["model_id"] else DEFAULT_MODEL,
            "messages": s["messages"]
        }
    st.session_state.current_session_id = next(
        iter(st.session_state.sessions.keys())
    ) if st.session_state.sessions else None

# Initialize session state variables
if "new_chat_mode" not in st.session_state:
    st.session_state.new_chat_mode = False

if "selected_model" not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL

# Render sidebar with session management
render_sidebar(st.session_state.sessions, st.session_state.current_session_id)

# Check if a session is selected
if not st.session_state.current_session_id:
    st.info("👈 Start a new chat from the sidebar (➕ New Chat).")
    st.stop()

# Get current session data
current_id = st.session_state.current_session_id
current_meta = st.session_state.sessions[current_id]

# Render session header with actions
render_session_header(current_meta, current_id)

# Render chat messages
render_chat_messages(current_meta["messages"])

# Model selector and chat input
col_model, col_input = st.columns([1, 3])

with col_model:
    st.session_state.selected_model = render_model_selector(st.session_state.selected_model)

# Chat input (kept at bottom as requested)
user_prompt = st.chat_input("Ask me anything...")

if user_prompt:
    process_user_message(
        user_prompt, 
        current_id, 
        current_meta, 
        st.session_state.selected_model
    )
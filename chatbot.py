"""
Multi-Modal AI Chatbot - Main Entry Point
"""
from dotenv import load_dotenv
import streamlit as st

# Custom modules
from database import init_db, load_sessions_from_db
from models import DEFAULT_MODEL
from ui_components import (
    render_session_controls,
    render_session_header,
    render_chat_messages,
    render_model_selector
)
from chat_logic import process_user_message

# Load environment
load_dotenv()

# Page config
st.set_page_config(page_title="Chatbot", page_icon="🤖", layout="wide")

# Optional: Custom CSS for cleaner UI
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        [data-testid="collapsedControl"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

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

# Initialize DB
if "db_inited" not in st.session_state:
    init_db()
    st.session_state.db_inited = True

# Load sessions
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
    st.session_state.current_session_id = (
        next(iter(st.session_state.sessions.keys()))
        if st.session_state.sessions else None
    )

# Init state vars
if "new_chat_mode" not in st.session_state:
    st.session_state.new_chat_mode = False

if "selected_model" not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL

# Layout: left column for session control, right column for chat
left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    render_session_controls(
        st.session_state.sessions,
        st.session_state.current_session_id
    )

with right_col:
    st.title("💬 Generative AI Chatbot")

    if not st.session_state.current_session_id:
        st.info("👈 Start a new chat from the left panel (➕ New Chat).")
        st.stop()

    # Current session
    current_id = st.session_state.current_session_id
    current_meta = st.session_state.sessions[current_id]

    # Header
    render_session_header(current_meta, current_id)

    # Messages
    render_chat_messages(current_meta["messages"])

    # Model selector and chat input
    col_model, col_input = st.columns([2, 3])
    with col_model:
        st.session_state.selected_model = render_model_selector(
            st.session_state.selected_model
        )

    user_prompt = st.chat_input("Ask me anything...")

    if user_prompt:
        process_user_message(
            user_prompt,
            current_id,
            current_meta,
            st.session_state.selected_model
        )

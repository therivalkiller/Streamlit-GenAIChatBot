"""
UI components for the chatbot interface
"""
import streamlit as st
import json
from database import create_session_in_db, delete_session_in_db, now_iso
from models import get_model_info, DEFAULT_MODEL

def render_sidebar(sessions_dict, current_session_id):
    """Render the sidebar with session management"""
    st.sidebar.title("🗂️ Chat Sessions")
    
    # New Chat button
    if st.sidebar.button("➕ New Chat"):
        st.session_state.new_chat_mode = True
        st.session_state.temp_new_title = ""
    
    # New chat creation form
    if st.session_state.new_chat_mode:
        st.sidebar.subheader("📝 Name your chat")
        st.session_state.temp_new_title = st.sidebar.text_input(
            "Enter chat title:", 
            value=st.session_state.get("temp_new_title", "")
        )
        col1, col2 = st.sidebar.columns(2)
        
        if col1.button("✅ Create"):
            title = st.session_state.temp_new_title.strip()
            if not title:
                st.sidebar.error("Please enter a non-empty title or click Skip.")
            else:
                session_id = create_session_in_db(title, st.session_state.selected_model)
                st.session_state.sessions[session_id] = {
                    "title": title, 
                    "created_at": now_iso(), 
                    "model_id": st.session_state.selected_model,
                    "messages": []
                }
                st.session_state.current_session_id = session_id
                st.session_state.new_chat_mode = False
                st.rerun()
        
        if col2.button("⏩ Skip"):
            title = now_iso()
            session_id = create_session_in_db(title, st.session_state.selected_model)
            st.session_state.sessions[session_id] = {
                "title": title, 
                "created_at": now_iso(), 
                "model_id": st.session_state.selected_model,
                "messages": []
            }
            st.session_state.current_session_id = session_id
            st.session_state.new_chat_mode = False
            st.rerun()
    
    # Previous sessions list
    if sessions_dict:
        st.sidebar.subheader("🕒 Previous Sessions")
        for sid, s in sorted(sessions_dict.items(), key=lambda kv: kv[0], reverse=True):
            if st.sidebar.button(f"{s['title']}", key=f"session_{sid}"):
                st.session_state.current_session_id = sid
                st.session_state.selected_model = s["model_id"] if s["model_id"] else DEFAULT_MODEL
                st.rerun()

def render_session_header(current_meta, current_id):
    """Render the session header with model info and actions"""
    st.subheader(f"Session: {current_meta['title']}")
    
    # Display current model
    current_model_info = get_model_info(
        current_meta["model_id"] if current_meta["model_id"] else DEFAULT_MODEL
    )
    st.caption(f"🤖 Model: **{current_model_info['developer']} - {current_model_info['id']}**")
    
    # Action buttons
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("🗑️ Delete session"):
            delete_session_in_db(current_id)
            del st.session_state.sessions[current_id]
            st.session_state.current_session_id = next(
                iter(st.session_state.sessions.keys())
            ) if st.session_state.sessions else None
            st.rerun()
    
    with col_b:
        export_obj = {
            "id": current_id,
            "title": current_meta["title"],
            "created_at": current_meta["created_at"],
            "model_id": current_meta["model_id"] if current_meta["model_id"] else DEFAULT_MODEL,
            "messages": [
                {
                    "role": m["role"], 
                    "content": m["content"], 
                    "created_at": m["created_at"] if "created_at" in m else None,
                    "model_id": m["model_id"] if "model_id" in m and m["model_id"] else DEFAULT_MODEL
                } for m in current_meta["messages"]
            ],
        }
        export_str = json.dumps(export_obj, ensure_ascii=False, indent=2)
        st.download_button(
            label="⬇️ Export JSON",
            data=export_str,
            file_name=f"chat_session_{current_id}.json",
            mime="application/json",
        )

def render_chat_messages(messages):
    """Render all chat messages"""
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "model_id" in message and message["model_id"]:
                st.caption(f"_via {message['model_id']}_")

def render_model_selector(current_model):
    """Render the model selector dropdown"""
    from models import MODELS, get_model_display_name
    
    model_options = list(MODELS.keys())
    model_labels = [get_model_display_name(m) for m in model_options]
    
    current_model_idx = model_options.index(current_model) if current_model in model_options else 0
    
    selected_label = st.selectbox(
        "Model",
        options=model_labels,
        index=current_model_idx,
        key="model_selector",
        label_visibility="collapsed"
    )
    return model_options[model_labels.index(selected_label)]
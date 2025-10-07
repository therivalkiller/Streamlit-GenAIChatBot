from dotenv import load_dotenv
import streamlit as st
from langchain_groq import ChatGroq
import sqlite3
import datetime
import json
import os
from typing import Dict, Any, List

load_dotenv()

# ---------- Config ----------
DB_PATH = "chatbot.db"

# ---------- DB helpers ----------
def now_iso() -> str:
    return datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

def get_db_conn():
    # check_same_thread=False allows Streamlit reruns to reuse connection safely in this simple app
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # enable foreign key cascade
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            seq INTEGER NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()

def create_session_in_db(title: str) -> int:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", (title, now_iso()))
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id

def delete_session_in_db(session_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def load_sessions_from_db() -> List[Dict[str, Any]]:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at FROM sessions ORDER BY id DESC")
    rows = cur.fetchall()
    sessions = []
    for r in rows:
        session_id = r["id"]
        cur.execute(
            "SELECT role, content, created_at, seq FROM messages WHERE session_id = ? ORDER BY seq",
            (session_id,),
        )
        messages = [
            {"role": m["role"], "content": m["content"], "created_at": m["created_at"], "seq": m["seq"]}
            for m in cur.fetchall()
        ]
        sessions.append({"id": session_id, "title": r["title"], "created_at": r["created_at"], "messages": messages})
    conn.close()
    return sessions

def save_message_in_db(session_id: int, role: str, content: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(seq), 0) + 1 AS nextseq FROM messages WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    nextseq = row["nextseq"] if row is not None else 1
    cur.execute(
        "INSERT INTO messages (session_id, role, content, created_at, seq) VALUES (?, ?, ?, ?, ?)",
        (session_id, role, content, now_iso(), nextseq),
    )
    conn.commit()
    conn.close()

# ---------- Streamlit app ----------
st.set_page_config(page_title="Chatbot", page_icon="🤖", layout="centered")
st.title("💬 Generative AI Chatbot")

# Initialize DB once
if "db_inited" not in st.session_state:
    init_db()
    st.session_state.db_inited = True

# Load sessions from DB into session_state (only once per session)
if "sessions" not in st.session_state:
    # sessions map: session_id -> {"title": str, "created_at": str, "messages": [ {role,content,created_at,seq} ]}
    st.session_state.sessions = {}
    db_sessions = load_sessions_from_db()
    for s in db_sessions:
        st.session_state.sessions[s["id"]] = {"title": s["title"], "created_at": s["created_at"], "messages": s["messages"]}

    # set currently active session to the newest or None
    st.session_state.current_session_id = next(iter(st.session_state.sessions.keys())) if st.session_state.sessions else None

# UI control flags
if "new_chat_mode" not in st.session_state:
    st.session_state.new_chat_mode = False

# ---------- Sidebar ----------
st.sidebar.title("🗂️ Chat Sessions")

# New chat button
if st.sidebar.button("➕ New Chat"):
    st.session_state.new_chat_mode = True
    st.session_state.temp_new_title = ""
    

# New chat inputs (title + skip)
if st.session_state.new_chat_mode:
    st.sidebar.subheader("📝 Name your chat")
    st.session_state.temp_new_title = st.sidebar.text_input("Enter chat title:", value=st.session_state.get("temp_new_title", ""))
    col1, col2 = st.sidebar.columns(2)
    if col1.button("✅ Create"):
        title = st.session_state.temp_new_title.strip()
        if not title:
            st.sidebar.error("Please enter a non-empty title or click Skip.")
        else:
            session_id = create_session_in_db(title)
            st.session_state.sessions[session_id] = {"title": title, "created_at": now_iso(), "messages": []}
            st.session_state.current_session_id = session_id
            st.session_state.new_chat_mode = False
            
    if col2.button("⏩ Skip"):
        title = now_iso()
        session_id = create_session_in_db(title)
        st.session_state.sessions[session_id] = {"title": title, "created_at": now_iso(), "messages": []}
        st.session_state.current_session_id = session_id
        st.session_state.new_chat_mode = False
        

# List previous sessions
if st.session_state.sessions:
    st.sidebar.subheader("🕒 Previous Sessions")
    # show sessions newest-first
    for sid, s in sorted(st.session_state.sessions.items(), key=lambda kv: kv[0], reverse=True):
        if st.sidebar.button(f"{s['title']}", key=f"session_{sid}"):
            st.session_state.current_session_id = sid
            

# ---------- Main area ----------
if not st.session_state.current_session_id:
    st.info("👈 Start a new chat from the sidebar (➕ New Chat).")
    st.stop()

current_id = st.session_state.current_session_id
current_meta = st.session_state.sessions[current_id]
st.subheader(f"Session: {current_meta['title']}")

# small controls: export / delete
col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("🗑️ Delete session"):
        delete_session_in_db(current_id)
        del st.session_state.sessions[current_id]
        # pick a fallback session if any
        st.session_state.current_session_id = next(iter(st.session_state.sessions.keys())) if st.session_state.sessions else None
        
with col_b:
    # prepare export content
    export_obj = {
        "id": current_id,
        "title": current_meta["title"],
        "created_at": current_meta["created_at"],
        "messages": [
            {"role": m["role"], "content": m["content"], "created_at": m.get("created_at")} for m in current_meta["messages"]
        ],
    }
    export_str = json.dumps(export_obj, ensure_ascii=False, indent=2)
    st.download_button(
        label="⬇️ Export JSON",
        data=export_str,
        file_name=f"chat_session_{current_id}.json",
        mime="application/json",
    )

# Display chat history
for message in current_meta["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LLM Initialization ---
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.1,
)

# --- Input box ---
user_prompt = st.chat_input("Ask me anything...")

if user_prompt:
    # display user message immediately
    st.chat_message("user").markdown(user_prompt)
    # persist user message
    save_message_in_db(current_id, "user", user_prompt)
    # append to session_state
    seq = len(current_meta["messages"]) + 1
    current_meta["messages"].append({"role": "user", "content": user_prompt, "created_at": now_iso(), "seq": seq})

    # prepare messages for LLM: only role & content
    messages_for_llm = [{"role": "system", "content": "You're a helpful assistant."}] + [
        {"role": m["role"], "content": m["content"]} for m in current_meta["messages"]
    ]

    # get response from LLM
    with st.spinner("Thinking..."):
        response = llm.invoke(input=messages_for_llm)
    assistant_response = response.content

    # display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)

    # save assistant response
    save_message_in_db(current_id, "assistant", assistant_response)
    seq = len(current_meta["messages"]) + 1
    current_meta["messages"].append({"role": "assistant", "content": assistant_response, "created_at": now_iso(), "seq": seq})

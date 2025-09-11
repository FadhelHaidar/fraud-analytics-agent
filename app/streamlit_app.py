import json
import time
from typing import List, Dict

import streamlit as st
import requests

# =============================
# Enhanced Streamlit Chat Client
# Talks to FastAPI POST /chat
# Shows chunks and SQL in dropdowns
# =============================

DEFAULT_BACKEND_URL = "http://localhost:8000/chat"  # change if your API runs elsewhere
HISTORY_CAP = 50  # keep only last N messages to avoid oversized payloads

st.set_page_config(page_title="LangGraph Agent", page_icon="🤖", layout="centered")

# --- Session state ---
if "messages" not in st.session_state:
    # Each message: {"role": "user"|"assistant", "content": str, "chunks": list, "sql": list}
    st.session_state.messages = []
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND_URL

# --- Top bar: title + clear ---
left, right = st.columns([1, 0.15])
with left:
    st.title("🤖 LangGraph Agent Chat")
with right:
    if st.button("🧹 Clear", help="Clear conversation"):
        st.session_state.messages = []
        st.toast("Chat cleared", icon="🧹")

# --- Tiny settings (collapsed by default) ---
with st.expander("Settings", expanded=False):
    st.session_state.backend_url = st.text_input(
        "Backend URL", value=st.session_state.backend_url, help="FastAPI POST /chat endpoint"
    )

# --- Helper function to render chunks ---
def render_chunks(chunks: List[Dict], message_idx: int):
    """Render chunks in an expandable section"""
    if not chunks:
        return
    
    with st.expander(f"📄 View Chunks ({len(chunks)} items)", expanded=False):
        for i, chunk in enumerate(chunks):
            st.subheader(f"Chunk {i+1}")
            if isinstance(chunk, dict):
                # Pretty print the chunk as JSON
                st.json(chunk)
            else:
                # If it's just text or other format
                st.text(str(chunk))
            if i < len(chunks) - 1:
                st.divider()

# --- Helper function to render SQL ---
def render_sql(sql_queries: List[str], message_idx: int):
    """Render SQL queries in an expandable section"""
    if not sql_queries:
        return
    
    with st.expander(f"🗄️ View SQL ({len(sql_queries)} queries)", expanded=False):
        for i, query in enumerate(sql_queries):
            st.subheader(f"Query {i+1}")
            st.code(query, language="sql")
            if i < len(sql_queries) - 1:
                st.divider()

# --- Render previous messages ---
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        # Show chunks and SQL for assistant messages
        if msg["role"] == "assistant":
            # Optional: if latency metadata stored previously
            if "latency" in msg:
                st.caption(f"Latency: {msg['latency']:.2f}s")
            
            # Render chunks if available
            if msg.get("chunks"):
                render_chunks(msg["chunks"], idx)
            
            # Render SQL if available
            if msg.get("sql"):
                render_sql(msg["sql"], idx)

# --- Chat input ---
user_input = st.chat_input("Type your question…")

def post_chat(query: str, history: List[Dict[str, str]]) -> Dict:
    """
    Call backend /chat. Returns dict with 'response', 'chunks', 'sql' on success.
    Raises requests.RequestException on HTTP / network errors.
    Raises json.JSONDecodeError if non-JSON returned.
    """
    # Only send role and content for history to match API expectations
    clean_history = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    payload = {"query": query, "chat_history": clean_history}
    resp = requests.post(st.session_state.backend_url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

if user_input:
    # Snapshot history BEFORE adding the user message (per your API contract)
    history_before = st.session_state.messages[-HISTORY_CAP:].copy()

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Assistant placeholder + call
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            t0 = time.time()
            try:
                data = post_chat(user_input, history_before)
                assistant_text = data.get("response") or "(empty response)"
                chunks = data.get("chunks", [])
                sql_queries = data.get("sql", [])
                latency = time.time() - t0

                # ✅ Save BEFORE rendering so a rerun redraws it
                assistant_message = {
                    "role": "assistant", 
                    "content": assistant_text, 
                    "latency": latency,
                    "chunks": chunks,
                    "sql": sql_queries
                }
                st.session_state.messages.append(assistant_message)

                # Now render from the just-saved state
                st.write(assistant_text)
                st.caption(f"Latency: {latency:.2f}s")
                
                # Render chunks and SQL immediately
                current_idx = len(st.session_state.messages) - 1
                render_chunks(chunks, current_idx)
                render_sql(sql_queries, current_idx)

            except requests.RequestException as e:
                st.error(f"Request error: {e}")
            except json.JSONDecodeError:
                st.error("Non-JSON response from backend")
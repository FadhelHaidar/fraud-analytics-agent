import json
import time
from typing import List, Dict

import streamlit as st
import requests

# =============================
# Minimal Streamlit Chat Client
# Talks to FastAPI POST /chat
# =============================

DEFAULT_BACKEND_URL = "http://localhost:8000/chat"  # change if your API runs elsewhere
HISTORY_CAP = 50  # keep only last N messages to avoid oversized payloads

st.set_page_config(page_title="LangGraph Agent", page_icon="🤖", layout="centered")

# --- Session state ---
if "messages" not in st.session_state:
    # Each message: {"role": "user"|"assistant", "content": str}
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

# --- Render previous messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # Optional: if latency metadata stored previously
        if "latency" in msg:
            st.caption(f"Latency: {msg['latency']:.2f}s")

# --- Chat input ---
user_input = st.chat_input("Type your question…")

def post_chat(query: str, history: List[Dict[str, str]]) -> Dict:
    """
    Call backend /chat. Returns dict with 'response' on success.
    Raises requests.RequestException on HTTP / network errors.
    Raises json.JSONDecodeError if non-JSON returned.
    """
    payload = {"query": query, "chat_history": history}
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
                latency = time.time() - t0

                # ✅ Save BEFORE rendering so a rerun redraws it
                st.session_state.messages.append(
                    {"role": "assistant", "content": assistant_text, "latency": latency}
                )

                # Now render from the just-saved state
                st.write(assistant_text)
                st.caption(f"Latency: {latency:.2f}s")

            except requests.RequestException as e:
                st.error(f"Request error: {e}")
            except json.JSONDecodeError:
                st.error("Non-JSON response from backend")

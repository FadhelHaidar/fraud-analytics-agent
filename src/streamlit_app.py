
import json
import time
from typing import List, Dict, Optional

import streamlit as st
import requests

# =============================
# Enhanced Streamlit Chat Client
# Talks to FastAPI POST /chat
# Shows chunks and SQL in dropdowns
# Adds per-message evaluation via POST /eval
# =============================

DEFAULT_BACKEND_URL = "http://localhost:8000/chat"  # change if your API runs elsewhere
HISTORY_CAP = 50  # keep only last N messages to avoid oversized payloads

st.set_page_config(page_title="LangGraph Agent", page_icon="🤖", layout="centered")

# --- Session state ---
if "messages" not in st.session_state:
    # Each message: {"role": "user"|"assistant", "content": str, "chunks": list, "sql": list, "latency": float, "eval_score": Optional[float]}
    st.session_state.messages = []
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND_URL

def _eval_url_from_backend(backend_url: str) -> str:
    # If user set /chat, swap to /eval. Otherwise just replace safely.
    if backend_url.endswith("/chat"):
        return backend_url[:-5] + "/eval"
    # fallback: naive replace (covers trailing slashes too)
    return backend_url.replace("/chat", "/eval").rstrip("/")

# --- Top bar: title + clear ---
left, right = st.columns([1, 0.25])
with left:
    st.title("🤖 LangGraph Agent Chat")
with right:
    if st.button("🧹 Clear", help="Clear conversation"):
        st.session_state.messages = []
        st.toast("Chat cleared", icon="🧹")

# --- Tiny settings (collapsed by default) ---
with st.expander("Settings", expanded=False):
    st.session_state.backend_url = st.text_input(
        "Backend URL (POST /chat)",
        value=st.session_state.backend_url,
        help="FastAPI POST /chat endpoint",
    )
    st.caption(f"Eval endpoint will be inferred as: {_eval_url_from_backend(st.session_state.backend_url)}")

# --- Helper: render chunks ---
def render_chunks(chunks: List[Dict], message_idx: int):
    if not chunks:
        return
    with st.expander(f"📄 View Chunks ({len(chunks)} items)", expanded=False):
        for i, chunk in enumerate(chunks):
            st.subheader(f"Chunk {i+1}")
            if isinstance(chunk, dict):
                st.json(chunk)
            else:
                st.text(str(chunk))
            if i < len(chunks) - 1:
                st.divider()

# --- Helper: render SQL ---
def render_sql(sql_queries: List[str], message_idx: int):
    if not sql_queries:
        return
    with st.expander(f"🗄️ View SQL ({len(sql_queries)} queries)", expanded=False):
        for i, query in enumerate(sql_queries):
            st.subheader(f"Query {i+1}")
            st.code(query, language="sql")
            if i < len(sql_queries) - 1:
                st.divider()

# --- Helper: find the nearest previous user query for a given assistant message index ---
def find_prev_user_query(idx: int) -> Optional[str]:
    # Walk backward to find the last 'user' message before idx
    for j in range(idx - 1, -1, -1):
        msg = st.session_state.messages[j]
        if msg.get("role") == "user":
            return msg.get("content", "")
    return None

# --- Backend calls ---
def post_chat(query: str, history: List[Dict[str, str]]) -> Dict:
    """
    Call backend /chat. Returns dict with 'response', 'chunks', 'sql' on success.
    Raises requests.RequestException on HTTP / network errors.
    Raises json.JSONDecodeError if non-JSON returned.
    """
    clean_history = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    payload = {"query": query, "chat_history": clean_history}
    resp = requests.post(st.session_state.backend_url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

def post_eval(user_query: str, assistant_text: str, chunks: List, sql: List) -> Dict:
    """
    Call backend /eval with ChatResponse-like payload.
    Returns JSON with {"score": <number>}
    """
    eval_url = _eval_url_from_backend(st.session_state.backend_url)
    payload = {
        "user_query": user_query,
        "response": assistant_text,
        "chunks": chunks or [],
        "sql": sql or [],
        "error": None,
    }
    resp = requests.post(eval_url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

# --- Renderer for existing messages (with Evaluate buttons on assistant messages) ---
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

        if msg["role"] == "assistant":
            # optional latency
            if "latency" in msg:
                st.caption(f"Latency: {msg['latency']:.2f}s")

            # chunks & sql
            if msg.get("chunks"):
                render_chunks(msg["chunks"], idx)
            if msg.get("sql"):
                render_sql(msg["sql"], idx)

            # Evaluate controls
            prev_query = find_prev_user_query(idx) or ""
            eval_cols = st.columns([0.25, 0.75])
            with eval_cols[0]:
                if st.button("✅ Evaluate", key=f"eval-btn-{idx}", help="Evaluate this assistant message against the last user query"):
                    try:
                        with st.spinner("Scoring…"):
                            result = post_eval(
                                user_query=prev_query,
                                assistant_text=msg.get("content", ""),
                                chunks=msg.get("chunks", []),
                                sql=msg.get("sql", []),
                            )
                        score = result.get("score", None)
                        # save it onto the message so it persists across reruns
                        st.session_state.messages[idx]["eval_score"] = score
                        st.toast("Evaluation complete", icon="✅")
                    except requests.RequestException as e:
                        st.error(f"Eval request error: {e}")
                    except json.JSONDecodeError:
                        st.error("Non-JSON response from eval endpoint")

            with eval_cols[1]:
                score = msg.get("eval_score", None)
                if score is not None:
                    st.success(f"Score: {score}")
                else:
                    st.caption("No score yet. Click **Evaluate** to compute.")

# --- Chat input ---
user_input = st.chat_input("Type your question…")

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
                    "sql": sql_queries,
                    # placeholder for future eval score
                    "eval_score": None,
                }
                st.session_state.messages.append(assistant_message)

                # Now render from the just-saved state
                st.write(assistant_text)
                st.caption(f"Latency: {latency:.2f}s")

                # Render chunks and SQL immediately
                current_idx = len(st.session_state.messages) - 1
                render_chunks(chunks, current_idx)
                render_sql(sql_queries, current_idx)

                # Immediate evaluate control for the fresh assistant message
                prev_query = find_prev_user_query(current_idx) or ""
                eval_cols = st.columns([0.25, 0.75])
                with eval_cols[0]:
                    if st.button("✅ Evaluate", key=f"eval-btn-{current_idx}", help="Evaluate this assistant message against the last user query"):
                        try:
                            with st.spinner("Scoring…"):
                                result = post_eval(
                                    user_query=prev_query,
                                    assistant_text=assistant_text,
                                    chunks=chunks,
                                    sql=sql_queries,
                                )
                            score = result.get("score", None)
                            st.session_state.messages[current_idx]["eval_score"] = score
                            st.toast("Evaluation complete", icon="✅")
                        except requests.RequestException as e:
                            st.error(f"Eval request error: {e}")
                        except json.JSONDecodeError:
                            st.error("Non-JSON response from eval endpoint")

                with eval_cols[1]:
                    score = st.session_state.messages[current_idx].get("eval_score", None)
                    if score is not None:
                        st.success(f"Score: {score}")
                    else:
                        st.caption("No score yet. Click **Evaluate** to compute.")

            except requests.RequestException as e:
                st.error(f"Request error: {e}")
            except json.JSONDecodeError:
                st.error("Non-JSON response from backend")

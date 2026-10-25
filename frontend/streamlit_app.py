import os
import requests
import streamlit as st

# ==========================================
# Page Configuration & Modern Aesthetics
# ==========================================
st.set_page_config(
    page_title="ChatBuddy — AI with Memory",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished, modern chat look
st.markdown(
    """
    <style>
    /* Main container styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 900px;
    }
    
    /* Header badge styling */
    .chat-header-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        background: rgba(14, 165, 233, 0.15);
        color: #0284c7;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    /* Welcome card */
    .welcome-card {
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: linear-gradient(135deg, rgba(248, 250, 252, 0.8) 0%, rgba(241, 245, 249, 0.8) 100%);
        margin-bottom: 2rem;
    }

    /* Conversation sidebar list items */
    .conv-item {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# Session State Initialization
# ==========================================
if "api_url" not in st.session_state:
    st.session_state.api_url = os.getenv("API_URL", "http://127.0.0.1:8000")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "conversation_title" not in st.session_state:
    st.session_state.conversation_title = "New Chat"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "use_streaming" not in st.session_state:
    st.session_state.use_streaming = True


# ==========================================
# Helper Functions: Backend API Communication
# ==========================================
def check_api_health(base_url: str) -> bool:
    """Checks if the FastAPI backend is online and responding."""
    try:
        r = requests.get(f"{base_url}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def fetch_conversations(base_url: str) -> list[dict]:
    """Retrieves all existing conversations from the database."""
    try:
        r = requests.get(f"{base_url}/conversations", timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.sidebar.error(f"Failed to fetch conversations: {e}")
    return []


def fetch_conversation_messages(base_url: str, conv_id: int) -> list[dict]:
    """Retrieves full message history for a specific conversation."""
    try:
        r = requests.get(f"{base_url}/conversations/{conv_id}/messages", timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Failed to load messages: {e}")
    return []


def delete_conversation_api(base_url: str, conv_id: int) -> bool:
    """Deletes a conversation by ID."""
    try:
        r = requests.delete(f"{base_url}/conversations/{conv_id}", timeout=4)
        return r.status_code == 200
    except Exception:
        return False


def reset_to_new_chat():
    """Resets session state to begin a fresh conversation."""
    st.session_state.conversation_id = None
    st.session_state.conversation_title = "New Chat"
    st.session_state.messages = []


def load_conversation(conv_id: int, title: str):
    """Loads past conversation messages into active view."""
    st.session_state.conversation_id = conv_id
    st.session_state.conversation_title = title
    history = fetch_conversation_messages(st.session_state.api_url, conv_id)
    st.session_state.messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
    ]


# ==========================================
# Sidebar: Navigation & Session Management
# ==========================================
with st.sidebar:
    st.title("🤖 ChatBuddy")
    st.caption("AI Assistant with Persistent PostgreSQL Memory")

    # New Chat Action Button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        reset_to_new_chat()
        st.rerun()

    st.divider()

    # Backend Connection Status Check
    is_online = check_api_health(st.session_state.api_url)
    if is_online:
        st.sidebar.caption("🟢 Backend: **Connected**")
    else:
        st.sidebar.caption("🔴 Backend: **Disconnected** (Check FastAPI server)")

    st.subheader("Recent Conversations")

    # Fetch and list conversations from database
    conversations = fetch_conversations(st.session_state.api_url)

    if not conversations:
        st.info("No past conversations yet. Start typing to begin your first chat!")
    else:
        for conv in conversations:
            col1, col2 = st.columns([0.82, 0.18])
            is_active = (st.session_state.conversation_id == conv["id"])
            btn_label = f"{'💬' if not is_active else '👉'} {conv['title']}"
            
            with col1:
                if st.button(
                    btn_label,
                    key=f"conv_{conv['id']}",
                    use_container_width=True,
                    disabled=is_active,
                ):
                    load_conversation(conv["id"], conv["title"])
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}", help="Delete chat"):
                    delete_conversation_api(st.session_state.api_url, conv["id"])
                    if st.session_state.conversation_id == conv["id"]:
                        reset_to_new_chat()
                    st.rerun()

    st.divider()

    # Settings Expander
    with st.expander("⚙️ Settings"):
        st.session_state.use_streaming = st.toggle("Token Streaming", value=st.session_state.use_streaming)
        st.session_state.api_url = st.text_input("FastAPI URL", value=st.session_state.api_url)


# ==========================================
# Main Chat View
# ==========================================
header_col1, header_col2 = st.columns([0.75, 0.25])
with header_col1:
    st.title(st.session_state.conversation_title)
with header_col2:
    if st.session_state.conversation_id is not None:
        st.markdown(
            f"<div style='text-align: right; padding-top: 15px;'><span class='chat-header-badge'>Thread #{st.session_state.conversation_id}</span></div>",
            unsafe_allow_html=True,
        )

# If no messages yet, show introductory onboarding card
if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-card">
            <h3>👋 Welcome to ChatBuddy!</h3>
            <p>Every message is durably stored in <b>PostgreSQL</b> with a sliding memory window, powered by the <b>Google Gemini API</b> and <b>FastAPI</b>.</p>
            <ul>
                <li>🧠 <b>Continuous Memory:</b> Past conversation context is preserved across turns.</li>
                <li>⚡ <b>Real-Time Streaming:</b> Instant tokens delivered as they generate.</li>
                <li>🗂️ <b>Multi-Session Isolation:</b> Switch threads freely without context crossover.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Render existing conversation messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ==========================================
# Chat Input & Response Handling
# ==========================================
user_prompt = st.chat_input("Type your message here...")

if user_prompt:
    if not is_online:
        st.error("Cannot reach the FastAPI backend. Please make sure `uvicorn backend.main:app` is running!")
        st.stop()

    # 1. Display and record user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    payload = {
        "conversation_id": st.session_state.conversation_id,
        "message": user_prompt,
    }

    # 2. Generate and stream/display Assistant Response
    with st.chat_message("assistant"):
        if st.session_state.use_streaming:
            placeholder = st.empty()
            try:
                # 1. Visual loading indicator while backend & Gemini process prompt
                with st.spinner("Thinking..."):
                    response = requests.post(
                        f"{st.session_state.api_url}/chat/stream",
                        json=payload,
                        stream=True,
                        timeout=(10, 180),
                    )

                if response.status_code == 200:
                    server_conv_id = response.headers.get("X-Conversation-Id")
                    is_new_thread = (st.session_state.conversation_id is None)

                    if server_conv_id:
                        st.session_state.conversation_id = int(server_conv_id)
                        if st.session_state.conversation_title == "New Chat":
                            st.session_state.conversation_title = (
                                (user_prompt[:25] + "...") if len(user_prompt) > 25 else user_prompt
                            )

                    # 2. Generator with chunk_size=1 to avoid requests' default 10KB buffer!
                    def stream_generator():
                        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                            if chunk:
                                yield chunk

                    # 3. Stream text progressively to UI
                    full_response = placeholder.write_stream(stream_generator())
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                    # Rerun only for the first message to refresh the sidebar thread title
                    if is_new_thread:
                        st.rerun()

                else:
                    err_msg = f"Error {response.status_code}: {response.text}"
                    placeholder.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})

            except Exception as e:
                err_msg = f"Connection failed: {e}"
                placeholder.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})

        else:
            # Fallback to standard buffered endpoint
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{st.session_state.api_url}/chat",
                        json=payload,
                        timeout=60,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.conversation_id = data.get("conversation_id", st.session_state.conversation_id)
                        reply = data.get("assistant_response", "")
                        st.markdown(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        st.rerun()
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

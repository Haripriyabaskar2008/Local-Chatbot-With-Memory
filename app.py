
import streamlit as st
import sqlite3
import uuid
from datetime import datetime
from google import genai
from google.genai import types

# =====================================
# 1. CONFIGURATION
# =====================================

st.set_page_config(
    page_title="Local BOT",
    page_icon="🤖",
    layout="wide"
)

APP_NAME = "Local BOT"
MODEL_NAME = "gemini-3.8-flash"
DATABASE = "local_bot.db"

SYSTEM_INSTRUCTION = """
You are Local BOT, a friendly personal AI assistant.

USER INFORMATION:
- Full name: Haripriya
- Preferred name: HP

YOUR IDENTITY:
- Your name is Local BOT.
- If asked your name, say you are Local BOT.

INSTRUCTIONS:
- Be friendly and natural.
- Understand Tamil, English and Tanglish.
- Give clear and direct answers.
- Remember useful details from the conversation history.
- Do not invent memories.
- Avoid unnecessarily long answers.
"""

# =====================================
# 2. DATABASE
# =====================================

def get_connection():
    return sqlite3.connect(
        DATABASE,
        check_same_thread=False,
        timeout=10
    )


def create_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)


def save_message(session_id, role, content):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO messages
            (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            session_id,
            role,
            content,
            datetime.now().isoformat(timespec="seconds")
        ))


def get_history(session_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,)).fetchall()

    return rows


def clear_history(session_id):
    with get_connection() as conn:
        conn.execute("""
            DELETE FROM messages
            WHERE session_id = ?
        """, (session_id,))


# =====================================
# 3. GEMINI CLIENT
# =====================================

@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None


# =====================================
# 4. STREAMING RESPONSE
# =====================================

def generate_response(client, session_id):

    history = get_history(session_id)

    # Use only the latest 10 messages
    recent_history = history[-10:]

    conversation = []

    for role, content in recent_history:

        gemini_role = (
            "user" if role == "user" else "model"
        )

        conversation.append(
            types.Content(
                role=gemini_role,
                parts=[
                    types.Part.from_text(text=content)
                ]
            )
        )

    response = client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=conversation,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            max_output_tokens=500,
            temperature=0.7
        )
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text


# =====================================
# 5. INITIALIZATION
# =====================================

create_database()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

session_id = st.session_state.session_id

api_key = get_api_key()

if not api_key:
    st.error(
        "Gemini API key missing. "
        "Please configure GEMINI_API_KEY in Streamlit Secrets."
    )
    st.stop()

try:
    client = get_gemini_client(api_key)

except Exception as error:
    st.error(f"Gemini connection failed: {error}")
    st.stop()


# =====================================
# 6. SIDEBAR
# =====================================

with st.sidebar:

    st.title("🤖 Local BOT")

    st.caption("Your Personal AI Assistant")

    st.divider()

    st.subheader("User Profile")

    st.write("Name: Haripriya")
    st.write("Preferred name: HP")

    st.divider()

    st.subheader("Memory")

    st.caption("Conversation history is stored in SQLite.")

    if st.button(
        "Clear Conversation",
        use_container_width=True
    ):
        clear_history(session_id)
        st.rerun()

    st.divider()

    st.caption("Powered by Google Gemini")
    st.caption("Built with Python and Streamlit")


# =====================================
# 7. MAIN CHAT
# =====================================

st.title("🤖 Local BOT")

st.write(
    "Hello HP! Welcome back. "
    "I'm Local BOT. How can I help you?"
)

st.divider()


# =====================================
# 8. DISPLAY HISTORY
# =====================================

history = get_history(session_id)

for role, content in history:

    with st.chat_message(role):
        st.markdown(content)


# =====================================
# 9. USER INPUT
# =====================================

user_message = st.chat_input(
    "Message Local BOT..."
)

if user_message:

    # Save user message
    save_message(
        session_id,
        "user",
        user_message
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_message)

    # Generate streaming response
    with st.chat_message("assistant"):

        try:

            with st.spinner("Local BOT is thinking..."):

                answer = st.write_stream(
                    generate_response(
                        client,
                        session_id
                    )
                )

            if answer:
                save_message(
                    session_id,
                    "assistant",
                    answer
                )
            else:
                st.warning("No response received. Please try again.")

        except Exception as error:

            st.error(
                f"Something went wrong: {error}"
            )

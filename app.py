
import streamlit as st
import sqlite3
import uuid
import os
from datetime import datetime
from google import genai
from google.genai import types

# ---------------- CONFIGURATION ----------------

st.set_page_config(
    page_title="Local BOT",
    page_icon="🤖",
    layout="wide"
)

DB_NAME = "local_bot.db"
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
You are Local BOT, a friendly and intelligent personal AI assistant.
Answer clearly and naturally.
Remember useful details from the conversation history provided.
If you do not know something, say so honestly.
Do not invent personal information about the user.
"""

# ---------------- DATABASE ----------------

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_message(session_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        session_id,
        role,
        content,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_history(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))

    messages = cursor.fetchall()
    conn.close()

    return messages


def clear_history(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM messages WHERE session_id = ?",
        (session_id,)
    )

    conn.commit()
    conn.close()


# ---------------- GEMINI ----------------

def get_gemini_client():
    api_key = None

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        st.error("Gemini API key not found. Configure it in Streamlit Secrets.")
        st.stop()

    return genai.Client(api_key=api_key)


def generate_response(client, session_id, user_message):
    history = get_history(session_id)

    conversation = []

    # Keep recent context to control token usage
    for role, content in history[-20:]:
        speaker = "User" if role == "user" else "Local BOT"
        conversation.append(f"{speaker}: {content}")

    conversation.append(f"User: {user_message}")
    conversation.append("Local BOT:")

    prompt = "\n\n".join(conversation)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
            max_output_tokens=1500
        )
    )

    return response.text or "I couldn't generate a response. Please try again."


# ---------------- INITIALIZATION ----------------

create_database()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "client" not in st.session_state:
    st.session_state.client = get_gemini_client()

session_id = st.session_state.session_id
client = st.session_state.client

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("🤖 Local BOT")
    st.caption("Your personal AI chatbot")

    st.divider()

    st.subheader("Memory")

    st.write("Your current conversation is stored in the app database.")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        clear_history(session_id)
        st.rerun()

    st.divider()

    st.caption("Powered by Google Gemini")
    st.caption("Built with Streamlit and Python")

# ---------------- MAIN INTERFACE ----------------

st.title("🤖 Local BOT")
st.write("Hello! I'm your personal AI assistant. How can I help you today?")

st.divider()

# Display previous messages
history = get_history(session_id)

for role, content in history:
    with st.chat_message(role):
        st.markdown(content)

# Chat input
user_message = st.chat_input("Ask Local BOT anything...")

if user_message:
    # Save user message
    save_message(session_id, "user", user_message)

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Local BOT is thinking..."):
            try:
                answer = generate_response(
                    client,
                    session_id,
                    user_message
                )

                st.markdown(answer)

                save_message(
                    session_id,
                    "assistant",
                    answer
                )

            except Exception as error:
                st.error(f"Something went wrong: {error}")


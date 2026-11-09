
import streamlit as st
import sqlite3
import uuid
from datetime import datetime
from google import genai
from google.genai import types

# ==========================================
# 1. APP CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Local BOT",
    page_icon="🤖",
    layout="wide"
)

APP_NAME = "Local BOT"
MODEL_NAME = "gemini-3.8-flash"
DATABASE = "local_bot.db"

SYSTEM_INSTRUCTION = """
You are Local BOT, a friendly, intelligent personal AI assistant.

USER PROFILE:
- User's full name is Haripriya.
- Preferred name: HP.

YOUR IDENTITY:
- Your name is Local BOT.
- If the user asks your name, introduce yourself as Local BOT.
- Address the user as HP when appropriate.

BEHAVIOUR:
- Be friendly, natural and helpful.
- Understand Tamil, English and Tanglish.
- Remember information from the conversation history provided.
- Use previous messages to understand follow-up questions.
- Do not invent memories or claim to remember information that is not provided.
- Give clear and useful answers.
"""

# ==========================================
# 2. DATABASE
# ==========================================

def get_connection():
    return sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_message(session_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages
        (session_id, role, content, timestamp)
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

    history = cursor.fetchall()
    conn.close()

    return history


def clear_history(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE session_id = ?
    """, (session_id,))

    conn.commit()
    conn.close()


# ==========================================
# 3. GEMINI CLIENT
# ==========================================

@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None


def generate_response(client, session_id):

    history = get_history(session_id)

    # Keep the latest 30 messages as conversation context
    recent_history = history[-30:]

    conversation = []

    for role, content in recent_history:

        if role == "user":
            gemini_role = "user"
        else:
            gemini_role = "model"

        conversation.append(
            types.Content(
                role=gemini_role,
                parts=[
                    types.Part.from_text(text=content)
                ]
            )
        )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=conversation,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION
        )
    )

    if response.text:
        return response.text

    return "I couldn't generate a response. Please try again."


# ==========================================
# 4. INITIALIZATION
# ==========================================

create_database()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

session_id = st.session_state.session_id

api_key = get_api_key()

# ==========================================
# 5. SIDEBAR
# ==========================================

with st.sidebar:

    st.title("🤖 Local BOT")

    st.caption("Your personal AI assistant")

    st.divider()

    st.subheader("👤 User Profile")

    st.write("Name: Haripriya")
    st.write("Preferred name: HP")

    st.divider()

    st.subheader("🧠 Memory")

    st.write("Conversation history is saved in the database.")

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True
    ):

        clear_history(session_id)
        st.rerun()

    st.divider()

    st.caption("AI Model: Gemini 3.8 Flash")
    st.caption("Built using Python and Streamlit")


# ==========================================
# 6. MAIN CHAT INTERFACE
# ==========================================

st.title("🤖 Local BOT")

st.write(
    "Hello HP! Welcome back. "
    "I'm Local BOT. What would you like to talk about?"
)

st.divider()

# Check API key
if not api_key:

    st.error(
        "Gemini API key is missing. "
        "Please configure GEMINI_API_KEY in Streamlit Secrets."
    )

    st.stop()

# Initialize Gemini
try:
    client = get_gemini_client(api_key)

except Exception as error:

    st.error(f"Gemini connection failed: {error}")
    st.stop()


# ==========================================
# 7. DISPLAY CHAT HISTORY
# ==========================================

history = get_history(session_id)

for role, content in history:

    with st.chat_message(role):
        st.markdown(content)


# ==========================================
# 8. USER INPUT AND AI RESPONSE
# ==========================================

user_message = st.chat_input(
    "Message Local BOT..."
)

if user_message:

    # Save user's message
    save_message(
        session_id,
        "user",
        user_message
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_message)

    # Generate AI response
    with st.chat_message("assistant"):

        with st.spinner("Local BOT is thinking..."):

            try:

                answer = generate_response(
                    client,
                    session_id
                )

                st.markdown(answer)

                # Save assistant response
                save_message(
                    session_id,
                    "assistant",
                    answer
                )

            except Exception as error:

                st.error(
                    f"Something went wrong: {error}"
                )

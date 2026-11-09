
import streamlit as st
import requests

from database import (
    initialize_database,
    create_chat,
    get_all_chats,
    get_chat,
    save_chat,
    delete_chat,
    get_all_memories,
    delete_memory
)

from memory import (
    extract_memories,
    get_memory_context
)


# --------------------------------
# CONFIGURATION
# --------------------------------

OLLAMA_URL = "http://localhost:11434"

st.set_page_config(
    page_title="Local BOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_database()


# --------------------------------
# CUSTOM DESIGN
# --------------------------------

st.markdown("""
<style>

.stApp {
    background: #101114;
    color: #ffffff;
}

[data-testid="stSidebar"] {
    background: #191b22;
}

.main-title {
    font-size: 36px;
    font-weight: 700;
    color: #ffffff;
}

.subtitle {
    color: #9ca3af;
    font-size: 14px;
}

.stChatMessage {
    border-radius: 15px;
}

div.stButton > button {
    border-radius: 10px;
    border: 1px solid #363944;
}

div[data-testid="stChatInput"] {
    border-radius: 15px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------
# SESSION STATE
# --------------------------------

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    st.session_state.model = "llama3.2:3b"


# --------------------------------
# OLLAMA CONNECTION
# --------------------------------

def get_models():

    try:

        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=3
        )

        response.raise_for_status()

        models = response.json().get("models", [])

        return [model["name"] for model in models]

    except requests.RequestException:
        return []


def generate_response(messages, model):

    memory_context = get_memory_context()

    system_prompt = f"""
You are Local BOT, a friendly personal AI assistant.

You have access to the user's saved memories.

Use them when they are relevant to the question.

Do not invent personal information.

Be helpful, natural and conversational.

SAVED MEMORIES:

{memory_context}
"""

    conversation = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    conversation.extend(messages[-20:])

    try:

        with requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": conversation,
                "stream": True
            },
            stream=True,
            timeout=(10, 600)
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines():

                if not line:
                    continue

                import json

                data = json.loads(line)

                content = data.get(
                    "message", {}
                ).get("content", "")

                if content:
                    yield content

                if data.get("done"):
                    break

    except requests.RequestException as error:

        raise RuntimeError(
            "Cannot connect to Ollama. "
            "Please make sure Ollama is running."
        ) from error


# --------------------------------
# SIDEBAR
# --------------------------------

with st.sidebar:

    st.title("🤖 Local BOT")

    st.caption("Your personal AI assistant")

    st.divider()

    # Model selection

    models = get_models()

    if models:

        selected_model = st.selectbox(
            "AI Model",
            models,
            index=(
                models.index(st.session_state.model)
                if st.session_state.model in models
                else 0
            )
        )

        st.session_state.model = selected_model

    else:

        st.error("Ollama is not connected.")

        st.caption(
            "Start Ollama and download a model."
        )

    st.divider()

    # New Chat

    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        st.session_state.chat_id = create_chat()
        st.session_state.messages = []

        st.rerun()

    st.subheader("Chat History")

    chats = get_all_chats()

    for chat in chats:

        col1, col2 = st.columns([5, 1])

        with col1:

            title = chat["title"]

            if len(title) > 25:
                title = title[:25] + "..."

            if st.button(
                title,
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):

                selected_chat = get_chat(chat["id"])

                st.session_state.chat_id = chat["id"]

                st.session_state.messages = (
                    selected_chat["messages"]
                    if selected_chat
                    else []
                )

                st.rerun()

        with col2:

            if st.button(
                "🗑️",
                key=f"delete_{chat['id']}"
            ):

                delete_chat(chat["id"])

                if st.session_state.chat_id == chat["id"]:
                    st.session_state.chat_id = None
                    st.session_state.messages = []

                st.rerun()

    st.divider()

    # Memory section

    with st.expander("🧠 My Memory"):

        memories = get_all_memories()

        if memories:

            for item in memories:

                st.write(f"• {item['content']}")

                if st.button(
                    "Delete",
                    key=f"mem_{item['id']}"
                ):

                    delete_memory(item["id"])
                    st.rerun()

        else:

            st.caption("No memories saved yet.")

    st.divider()

    st.caption("Powered by Ollama + SQLite")
    st.caption("100% Local AI")


# --------------------------------
# MAIN PAGE
# --------------------------------

st.markdown(
    '<div class="main-title">Local BOT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'A chatbot that remembers your conversations.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# --------------------------------
# CREATE FIRST CHAT
# --------------------------------

if st.session_state.chat_id is None:

    st.session_state.chat_id = create_chat()

    st.session_state.messages = []


# --------------------------------
# WELCOME SCREEN
# --------------------------------

if not st.session_state.messages:

    st.markdown(
        "<h3 style='text-align:center;'>"
        "Hello! Welcome to Local BOT 👋"
        "</h3>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#999;'>"
        "Ask me anything. I'll remember useful things "
        "you share with me."
        "</p>",
        unsafe_allow_html=True
    )


# --------------------------------
# DISPLAY MESSAGES
# --------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# --------------------------------
# CHAT INPUT
# --------------------------------

user_input = st.chat_input(
    "Message Local BOT..."
)


if user_input:

    # Save user message in session

    user_message = {
        "role": "user",
        "content": user_input
    }

    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant response

    with st.chat_message("assistant"):

        try:

            response = st.write_stream(
                generate_response(
                    st.session_state.messages,
                    st.session_state.model
                )
            )

            assistant_message = {
                "role": "assistant",
                "content": response
            }

            st.session_state.messages.append(
                assistant_message
            )

            # Extract long-term memory

            extract_memories(
                user_input,
                st.session_state.model
            )

            # Create chat title

            current_chat = get_chat(
                st.session_state.chat_id
            )

            if current_chat["title"] == "New Chat":

                title = user_input[:40]

            else:

                title = current_chat["title"]

            # Save all conversations

            save_chat(
                st.session_state.chat_id,
                st.session_state.messages,
                title
            )

        except Exception as error:

            st.error(str(error))

            st.session_state.messages.pop()

    st.rerun()

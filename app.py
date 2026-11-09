
import streamlit as st
import uuid
import json
from datetime import datetime, timezone
from groq import Groq
from supabase import create_client



st.set_page_config(
    page_title="Local BOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)



st.markdown("""
<style>
    .stApp {
        background-color: #101114;
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background-color: #18191f;
    }

    .main-title {
        font-size: 35px;
        font-weight: 700;
        color: #ffffff;
    }

    .subtitle {
        color: #9ca3af;
        font-size: 14px;
    }

    .stChatMessage {
        border-radius: 14px;
    }

    div.stButton > button {
        border-radius: 9px;
        border: 1px solid #353945;
    }

    .memory-card {
        background: #20232b;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)



try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
    APP_PASSWORD = st.secrets["APP_PASSWORD"]

except Exception:
    st.error("Configuration missing. Please configure Streamlit Secrets.")
    st.stop()

MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:

    st.title("🤖 Local BOT")
    st.caption("Your personal AI assistant with memory")

    password = st.text_input(
        "Enter your password",
        type="password"
    )

    if st.button("Login", use_container_width=True):

        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

# ----------------------------------
# SESSION STATE
# ----------------------------------

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


def get_chats():

    response = (
        supabase.table("chats")
        .select("*")
        .order("updated_at", desc=True)
        .execute()
    )

    return response.data


def create_chat():

    chat_id = str(uuid.uuid4())

    data = {
        "id": chat_id,
        "title": "New Chat",
        "messages": [],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    supabase.table("chats").insert(data).execute()

    return chat_id


def get_chat(chat_id):

    response = (
        supabase.table("chats")
        .select("*")
        .eq("id", chat_id)
        .single()
        .execute()
    )

    return response.data


def save_chat(chat_id, messages, title=None):

    data = {
        "id": chat_id,
        "messages": messages,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    if title:
        data["title"] = title

    supabase.table("chats").upsert(data).execute()


def delete_chat(chat_id):

    supabase.table("chats").delete().eq(
        "id", chat_id
    ).execute()



def get_memories():

    response = (
        supabase.table("memories")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


def save_memory(memory):

    memory = memory.strip()

    if not memory:
        return

    existing = (
        supabase.table("memories")
        .select("id")
        .eq("content", memory)
        .limit(1)
        .execute()
    )

    if not existing.data:

        supabase.table("memories").insert({
            "content": memory
        }).execute()


def delete_memory(memory_id):

    supabase.table("memories").delete().eq(
        "id", memory_id
    ).execute()


def extract_memories(user_message):

    prompt = f"""
Extract stable, useful facts explicitly shared by the user.

Remember things like:
- Preferences
- Interests
- Goals
- Ongoing projects
- Long-term plans

Do not save passwords, API keys, financial credentials,
medical information, or other sensitive personal details.

Only extract information from the USER MESSAGE.
Do not invent facts.

Return one short fact per line.
If there is nothing useful, return NONE.

USER MESSAGE:
{user_message}
"""

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=250
        )

        result = response.choices[0].message.content.strip()

        if result.upper() == "NONE":
            return

        for line in result.splitlines():

            fact = line.strip().lstrip("-•* ").strip()

            if fact and fact.upper() != "NONE":
                save_memory(fact)

    except Exception:
        pass




def generate_response(messages):

    memories = get_memories()

    memory_text = "\n".join(
        [item["content"] for item in memories]
    )

    system_prompt = f"""
You are Local BOT, a friendly personal AI assistant.

Your responsibilities:
1. Answer clearly and accurately.
2. Remember the user's saved preferences and facts.
3. Use relevant memories when answering.
4. Maintain conversation context.
5. Never pretend to know information that is not available.
6. Be natural and conversational.

SAVED USER MEMORIES:

{memory_text if memory_text else "No saved memories yet."}
"""

    conversation = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    conversation.extend(messages[-20:])

    stream = client.chat.completions.create(
        model=MODEL,
        messages=conversation,
        temperature=0.7,
        max_tokens=2048,
        stream=True
    )

    for chunk in stream:

        content = chunk.choices[0].delta.content

        if content:
            yield content



with st.sidebar:

    st.title("🤖 Local BOT")

    st.caption("Your personal AI assistant")

    if st.button("+ New Chat", use_container_width=True):

        new_id = create_chat()

        st.session_state.chat_id = new_id
        st.session_state.messages = []

        st.rerun()

    st.divider()

    st.subheader("Chat History")

    chats = get_chats()

    if chats:

        for chat in chats:

            col1, col2 = st.columns([5, 1])

            with col1:

                label = chat.get("title") or "New Chat"

                if len(label) > 24:
                    label = label[:24] + "..."

                if st.button(
                    label,
                    key=f"open_{chat['id']}",
                    use_container_width=True
                ):

                    selected = get_chat(chat["id"])

                    st.session_state.chat_id = chat["id"]
                    st.session_state.messages = selected["messages"]

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

    else:

        st.caption("No conversations yet.")

    st.divider()

    # MEMORY DISPLAY

    with st.expander("🧠 Saved Memory"):

        memories = get_memories()

        if memories:

            for memory in memories:

                st.write("•", memory["content"])

                if st.button(
                    "Delete",
                    key=f"memory_{memory['id']}"
                ):

                    delete_memory(memory["id"])
                    st.rerun()

        else:

            st.caption("Nothing remembered yet.")

    st.divider()

    if st.button("Logout", use_container_width=True):

        st.session_state.authenticated = False
        st.session_state.chat_id = None
        st.session_state.messages = []

        st.rerun()

    st.caption("Local BOT | AI with Memory")



st.markdown(
    '<div class="main-title">Local BOT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">A personal chatbot that remembers what matters.</div>',
    unsafe_allow_html=True
)

st.divider()

if st.session_state.chat_id is None:

    st.session_state.chat_id = create_chat()
    st.session_state.messages = []

# Display chat history

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----------------------------------
# USER INPUT
# ----------------------------------

user_input = st.chat_input("Message Local BOT...")

if user_input:

    # Save user message

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Display user message

    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response

    with st.chat_message("assistant"):

        try:

            response = st.write_stream(
                generate_response(
                    st.session_state.messages
                )
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            # Create title from first user message

            current_chat = get_chat(
                st.session_state.chat_id
            )

            title = current_chat.get("title")

            if title == "New Chat":

                title = user_input[:45]

            # Save conversation

            save_chat(
                st.session_state.chat_id,
                st.session_state.messages,
                title
            )

            # Extract long-term memories

            extract_memories(user_input)

        except Exception as e:

            st.error(f"Something went wrong: {e}")

            st.session_state.messages.pop()

    st.rerun()

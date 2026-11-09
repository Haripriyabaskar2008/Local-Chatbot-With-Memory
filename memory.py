
import requests
from database import add_memory, get_all_memories

OLLAMA_URL = "http://localhost:11434"


def extract_memories(user_message, model):

    prompt = f"""
You are a memory extraction system.

Extract only useful, stable facts explicitly shared
by the user.

Examples:
- User likes Python programming.
- User is learning machine learning.
- User prefers short explanations.

Rules:
1. Extract only facts stated by the user.
2. Do not invent information.
3. Ignore temporary questions and casual conversation.
4. Do not save passwords, API keys or credentials.
5. Do not save sensitive health, financial or other
   private information.
6. Return each fact on a separate line.
7. If nothing is useful, return exactly NONE.

USER MESSAGE:
{user_message}
"""

    try:

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()["response"].strip()

        if result.upper() == "NONE":
            return

        for line in result.splitlines():

            fact = line.strip().lstrip("-•* ").strip()

            if fact and fact.upper() != "NONE":
                add_memory(fact)

    except requests.RequestException:
        return

    except (ValueError, KeyError, TypeError):
        return


def get_memory_context():

    memories = get_all_memories()

    if not memories:
        return "No saved memories."

    return "\n".join(
        f"- {item['content']}"
        for item in memories
    )

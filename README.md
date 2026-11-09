# Local-Chatbot-With-Memory
# Local BOT

**Local BOT** is an AI-powered personal chatbot built using Python, Streamlit, and Google's Gemini API. It provides an interactive chat interface with conversation history and contextual memory.

APP LINK:
https://local-chatbot-with-memory-juwptmetmpzyj4qbqkipdr.streamlit.app/

APP SCREENSHOTS:
<img width="959" height="416" alt="Screenshot 2026-11-09 142112" src="https://github.com/user-attachments/assets/581d6135-d863-4502-9a9e-396a51f52bde" />


## Features

- **AI-Powered Conversations:** Generates intelligent responses using Google Gemini.
- **Conversation Memory:** Stores chat messages using SQLite and uses previous messages as context.
- **Personalized Interaction:** Recognizes the user's name and preferred name.
- **Chat History:** Displays previous messages within the current session.
- **Clear Conversation:** Allows users to delete their current conversation.
- **Web Interface:** Simple and interactive interface developed using Streamlit.
- **Cloud Deployment:** Hosted using Streamlit Community Cloud.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Streamlit | User interface |
| Google Gemini API | AI response generation |
| SQLite | Conversation storage |
| Google Gen AI SDK | Gemini integration |
| GitHub | Version control |
| Streamlit Community Cloud | Deployment |

## Project Structure

```text
Local-BOT/
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Local-BOT.git
```

### 2. Navigate to the Project Folder

```bash
cd Local-BOT
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini API Key

Obtain a Gemini API key from Google AI Studio:

https://aistudio.google.com/apikey

Create a `.streamlit/secrets.toml` file and add:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Never commit API keys or secrets to GitHub.

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

## Deployment

Local BOT can be deployed using Streamlit Community Cloud.

1. Push the project to GitHub.
2. Open https://share.streamlit.io/
3. Connect your GitHub repository.
4. Select `app.py` as the main file.
5. Add `GEMINI_API_KEY` under App Settings → Secrets.
6. Deploy the application.

## Memory and Data Storage

Local BOT uses SQLite to store conversation messages, including:

- Session ID
- Message role
- Message content
- Timestamp

The stored conversation history is retrieved and supplied to Gemini as context to support follow-up questions.

**Note:** The current SQLite implementation uses local application storage. Streamlit Community Cloud does not guarantee persistence of local files across restarts or redeployments. Persistent long-term memory requires an external database.

## Future Improvements

- Permanent memory using Supabase.
- Multiple conversation sessions.
- Chat history management.
- User authentication.
- Improved memory retrieval.
- Personalized AI responses.

## Author

**HARI PRIYA.B**

 Bsc Computer Science with Artificial Intelligence


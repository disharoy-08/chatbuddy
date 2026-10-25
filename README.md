# 🤖 ChatBuddy: Full-Stack AI Chatbot with Persistent Memory

A production-ready, multi-turn AI chat application with durable conversation memory, sliding-window context management, and isolated multi-session support. Built with **FastAPI**, **Streamlit**, **PostgreSQL**, **SQLAlchemy**, and the **Google Gemini API**.

---

## 🛠️ Architecture & Tech Stack

| Component | Choice | Purpose |
| :--- | :--- | :--- |
| **Frontend** | [Streamlit](https://streamlit.io/) | Interactive web chat interface with multi-session management |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | REST API, conversational routing, and business logic |
| **Primary Database** | [PostgreSQL](https://www.postgresql.org/) | Durable relational storage for conversations and messages *(SQLite supported for lightweight local dev)* |
| **Python Database Layer** | [SQLAlchemy](https://www.sqlalchemy.org/) | Object-Relational Mapping (ORM), schema definitions, and queries |
| **LLM Provider** | [Google Gemini API](https://ai.google.dev/) | Multi-turn reasoning, conversational intelligence, and response generation |
| **Later Enhancement** | [Redis](https://redis.io/) | Caching, rate limiting, and temporary session state |

---

## 📐 System Architecture & Flow

```mermaid
graph LR
    User([User]) <--> UI[Streamlit Frontend]
    UI <-->|HTTP / REST| API[FastAPI Backend]
    API <-->|SQLAlchemy ORM| DB[(PostgreSQL Database)]
    API <-->|Prompt + Context Window| LLM[Google Gemini API]
    API -.->|Planned Cache| Redis[(Redis Cache)]
```

### Context Pipeline
1. **User sends message** via Streamlit UI.
2. **FastAPI receives request** at `/chat` with `conversation_id`.
3. **Context Retrieval**: Backend queries SQLAlchemy for the last $N$ messages for that specific `conversation_id`.
4. **LLM Invocation**: Message history + new query are sent to the Gemini API.
5. **Persistence**: Both user message and AI response are committed to PostgreSQL.
6. **Isolated Display**: Streamlit renders the response ensuring zero context leakage across conversations.

### 🔄 Application Startup & Database Initialization Flow

When the FastAPI server starts, it executes an automated database verification and initialization lifecycle:

```mermaid
flowchart TD
    A[FastAPI Server Starts] --> B[Check Database Reachability]
    B -- Reachable --> C{Check Required Tables Exist?}
    B -- Unreachable --> D[Log Connection Error & Halt Startup]
    C -- Tables Exist --> E[Keep Unchanged & Continue Startup]
    C -- Tables Missing --> F[Create Missing Tables & Continue Startup]
    E --> G[FastAPI Ready to Accept Requests]
    F --> G
```

- **Database Reachability Check**: Tests connectivity against the configured database (`DATABASE_URL`).
- **Table Inspection**: Checks if required tables (`conversations`, `messages`) already exist.
  - **If tables exist**: Keeps them unchanged and continues startup.
  - **If tables are missing**: Creates only the missing tables and continues startup.

---

## 🚀 Implementation Roadmap

- [x] **Stage 1 — Basic FastAPI `/chat` Endpoint**  
  Set up FastAPI app, define Pydantic request/response schemas, and verify a stateless `/chat` endpoint connecting directly to Gemini API.
- [x] **Stage 2 — In-Memory Conversational History**  
  Implement a temporary in-memory dictionary to test multi-turn context retention and observe how LLM context affects response quality.
- [x] **Stage 3 — PostgreSQL & SQLAlchemy Integration**  
  Configure database connections, define SQLAlchemy models (`Conversation`, `Message`), and implement the startup lifecycle (reachability check + auto-creation of missing tables).
- [x] **Stage 4 — Persistent Multi-Turn Conversations**  
  Store every inbound user prompt and outbound model response in PostgreSQL; retrieve past history when returning to an existing conversation.
- [x] **Stage 5 — Configurable Sliding Window ($N$ Messages)**  
  Implement a dynamic limit to pass only the last $N$ messages as context to the Gemini API, preventing context bloat and managing token costs.
- [x] **Stage 6 — Streamlit UI & Conversation Isolation**  
  Build the Streamlit chat frontend with conversation selection/creation sidebar, verify session isolation, thinking spinner, and real-time token streaming.
- [ ] **Stage 7 (Enhancement) — Redis Caching & Rate Limiting**  
  Integrate Redis for fast session retrieval, caching frequent queries, and rate limiting requests.

---

## 🗄️ Database Schema Design

The database uses a clean, two-table relational structure optimized for chat sessions and history tracking.

```mermaid
erDiagram
    conversations ||--o{ messages : "has many"

    conversations {
        UUID id PK "Unique conversation ID"
        VARCHAR title "Chat title"
        TIMESTAMP created_at "When the chat was created"
    }

    messages {
        UUID id PK "Unique message ID"
        UUID conversation_id FK "Which conversation it belongs to"
        VARCHAR role "user or assistant"
        TEXT content "Message text"
        TIMESTAMP created_at "When the message was created"
    }
```

### Table 1: `conversations`
*One row per chat session.*

| Column | Type | Purpose |
| :--- | :--- | :--- |
| `id` | `UUID` / `INTEGER` (PK) | Unique conversation ID |
| `title` | `VARCHAR(255)` | Chat title (e.g. "Python Async Guide") |
| `created_at` | `TIMESTAMP` | When the chat was created |

### Table 2: `messages`
*Multiple messages belong to one conversation.*

| Column | Type | Purpose |
| :--- | :--- | :--- |
| `id` | `UUID` / `INTEGER` (PK) | Unique message ID |
| `conversation_id` | `UUID` / `INTEGER` (FK) | Which conversation it belongs to (`REFERENCES conversations(id)`) |
| `role` | `VARCHAR(20)` | `user` or `assistant` |
| `content` | `TEXT` | Message text |
| `created_at` | `TIMESTAMP` | When the message was created |

> 💡 Detailed schema definitions, constraints, and DBML code can be found in [`docs/database/schema.md`](file:///d:/Code/python_code/python_rag_ai/chat-with-memory/docs/database/schema.md).

---

## 📂 Project Structure

```text
chat-with-memory/
├── backend/
│   ├── routers/
│   │   ├── chat.py             # Chat & real-time streaming endpoints (/chat, /chat/stream)
│   │   └── conversations.py    # History endpoints (list, get messages, delete)
│   ├── services/
│   │   └── chat_service.py     # Gemini client, sliding-window context & stream logic
│   ├── database.py             # SQLAlchemy engine, sessionmaker & auto-provisioning
│   ├── models.py               # DeclarativeBase models (Conversation, Message)
│   ├── schemas.py              # Pydantic schemas (ChatRequest)
│   └── main.py                 # FastAPI app entrypoint & lifespan management
├── frontend/
│   └── streamlit_app.py        # Streamlit multi-session UI with real-time streaming
├── docs/
│   └── database/
│       └── schema.md           # Database ER diagram & data dictionary
├── .env.example                # Sample environment variables
├── .gitignore                  # Git ignore rules (includes __pycache__ & *.pyc)
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- **PostgreSQL** installed locally or running via Docker *(or SQLite fallback)*
- **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/disharoy-08/chatbuddy.git
cd chatbuddy

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

*(Key libraries: `fastapi`, `uvicorn`, `streamlit`, `sqlalchemy`, `psycopg2-binary`, `google-genai`, `python-dotenv`, `pydantic`)*

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update your credentials in `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash

# PostgreSQL connection string:
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/chatbuddy
# (Alternative lightweight SQLite for quick testing):
# DATABASE_URL=sqlite:///./chatbuddy.db

# Configurable memory window:
CONTEXT_WINDOW_LIMIT=10
```

---

## 🖥️ Running the Application

### 1. Start the FastAPI Backend

```bash
uvicorn backend.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 2. Start the Streamlit Frontend

In a separate terminal (with virtual environment activated):

```bash
streamlit run frontend/streamlit_app.py
```
- Streamlit UI: `http://localhost:8501`

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status and greeting |
| `GET` | `/health` | API health check |
| `POST` | `/chat` | Send a message, get buffered Gemini response, and persist to history |
| `POST` | `/chat/stream` | Stream tokens in real-time with `X-Conversation-Id` header |
| `GET` | `/conversations` | List all active conversation threads (newest first) |
| `GET` | `/conversations/{id}/messages` | Retrieve full chronological message history for a conversation |
| `DELETE` | `/conversations/{id}` | Delete a conversation and cascade-delete its messages |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

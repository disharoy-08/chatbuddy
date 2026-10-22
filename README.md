# 🤖 ChatBuddy: Python AI Chat with Memory & Streaming

A modular, multi-turn AI chatbot built in Python using the Google Gemini API. This project demonstrates how to handle conversational state, implement sliding-window memory management, stream real-time responses, and benchmark latency metrics like **Time to First Token (TTFT)**.

---

## 📌 Project Overview

Building production-ready conversational AI requires more than sending simple prompts to an LLM. This project walks through building a robust command-line chat assistant from scratch with full control over memory retention, streaming tokens, and latency profiling.

### Key Highlights
- **Interactive Multi-turn Chat**: Continuous conversation loop with context persistence.
- **Sliding-Window Memory**: Configurable memory threshold ($N$ messages) to optimize prompt token usage and manage context limits.
- **Real-Time Token Streaming**: Immediate output delivery as tokens are generated.
- **Performance Profiling**: Measurement of Time to First Token (TTFT) and total response generation latency.

---

## 🚀 Implementation Plan

This project is built across 6 structured steps:

- [x] **Step 1 — Create the Project**  
  Initialize project structure, virtual environment (`.venv`), and dependencies (`google-genai` or `google-generativeai`, `python-dotenv`).
- [ ] **Step 2 — Build a Basic Chatbot**  
  Implement the standard REPL loop to accept user input and return responses from the Gemini model.
- [ ] **Step 3 — Add Conversation Memory**  
  Maintain user and assistant dialogue history to enable coherent multi-turn conversations.
- [ ] **Step 4 — Limit Memory (Sliding Window)**  
  Restrict history to the last $N$ turns to prevent context window overflow and analyze trade-offs of forgotten context.
- [ ] **Step 5 — Add Streaming**  
  Upgrade from buffered responses to real-time chunked streaming for responsive UX.
- [ ] **Step 6 — Measure Performance**  
  Track, calculate, and log **Time to First Token (TTFT)** and **Total Elapsed Time** for performance analysis.

---

## 📂 Project Structure

```text
chat-with-memory/
├── .venv/                  # Virtual environment
├── .env                    # Environment variables (API keys - gitignored)
├── .env.example            # Example environment configuration
├── .gitignore              # Ignored files
├── main.py                 # Core chatbot application entrypoint
├── requirements.txt        # Python package dependencies
└── README.md               # Project documentation
```

---

## 🛠️ Prerequisites & Setup

### 1. Prerequisites
- Python **3.10+**
- A **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/disharoy-08/chatbuddy.git
cd chatbuddy

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (cmd):
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

*(Or install directly: `pip install google-genai python-dotenv`)*

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 💻 Usage

Run the chatbot:

```bash
python main.py
```

### Special Commands
- Type `exit` or `quit` to end the session.
- Type `clear` to reset conversation history.

---

## 📊 Performance Metrics Explained

| Metric | Description | Why It Matters |
| :--- | :--- | :--- |
| **TTFT (Time to First Token)** | Latency between sending the request and receiving the first stream chunk. | Measures perceived speed and UI responsiveness. |
| **Total Response Time** | Elapsed duration from request dispatch until the final token is rendered. | Measures overall throughput and generation time. |
| **Memory Window ($N$)** | The maximum number of past conversation turns retained in memory. | Balances context coherence with token cost and latency. |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

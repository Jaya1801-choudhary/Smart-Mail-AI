# 📧 Smart Mail AI: Autonomous Email Management & Scheduling Assistant

Smart Mail AI is an intelligent, agentic workflow automation tool designed to eliminate manual administrative fatigue. By leveraging the **Llama-3 Large Language Model** (via Groq) and the **Model Context Protocol (MCP)**, this system autonomously fetches emails, categorizes them, drafts contextual replies, and seamlessly schedules meetings via Google Workspace APIs.

## ✨ Key Features
* **AI Categorization:** Automatically classifies unread emails into Priority, Normal, or Spam.
* **Autonomous Drafting:** Generates highly accurate, context-aware draft replies using Groq's high-speed Llama-3 inference.
* **Calendar Sync & Scheduling:** Extracts time parameters using natural language processing and books conflict-free slots on Google Calendar.
* **Human-in-the-Loop:** A clean, responsive Streamlit dashboard for reviewing, editing, and approving all AI actions.
* **Secure Audit Logging:** All processed emails and dispatched drafts are permanently logged in a local, lightweight SQLite database.
* **Enterprise Security:** Secure, token-based Google OAuth 2.0 authentication ensures no raw passwords are ever stored.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **Backend:** Python 3.10+
* **Database:** SQLite (via SQLAlchemy)
* **AI/LLM:** Llama-3.3 (via Groq API)
* **Integrations:** Google Gmail API (v1), Google Calendar API (v3)
* **Architecture:** Model Context Protocol (MCP) for tool execution

## 🚀 Installation & Setup

**1. Clone the repository:**
```bash
git clone [https://github.com/your-username/smartmail-ai.git](https://github.com/your-username/smartmail-ai.git)
cd smartmail-ai

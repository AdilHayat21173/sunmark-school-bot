# Sunmark School Chatbot

This repository contains the code for a question‑answering chatbot built around the content of [Sunmarke School](https://www.sunmarke.com/). It uses a **retrieval‑augmented generation (RAG)** pipeline, a small FastAPI backend, a React/Vite frontend, and a graph‑based orchestration layer to intelligently route user queries.



[The system was developed while following a Loom demo](https://www.loom.com/share/ab6f6142235743cd875e6d6943ba86ab)


---

## 🔍 Overview

1. **Scrape** the public pages of the Sunmarke website and produce a JSON document collection (`src/rags/school_data.json`).
2. **Clean** the scraped data if necessary and optionally save as `school_data_cleaned.json`.
3. **Build a FAISS vectorstore** using Hugging Face embeddings. This becomes the knowledge base for school-specific queries.
4. **Run a LangGraph workflow** that routes each incoming question to one of three datasources:
   - *Vectorstore* (our local school content)
   - *Web search* (via Tavily) for up‑to‑date facts or general topics
   - *Chat* (freeform conversation)
5. **Adapt**: the graph grades retrieved documents, rewrites queries when retrieval fails, and grades the final LLM generation for relevance/hallucination.
6. **API & frontend** layer provide authentication, session management, and a simple chat UI.

---

## 📁 Folder Structure

```text
.
├── Api/                  # FastAPI backend (auth, chat, users, database)
├── src/                  # Core Python code
│   ├── edges/            # Decision logic used by the state graph
│   ├── graphs/           # LangGraph workflow definitions
│   ├── llms/             # LLM wrapper (Groq) and helpers
│   ├── nodes/            # Functions executed at each graph node
│   ├── prompts/          # Prompt templates for routing, grading, RAG, etc.
│   ├── rags/             # RAG helpers (vectorstore creation/load, data files)
│   ├── route/            # Chains for routing, rewriting, grading, answer generation
│   └── states/           # State model used by LangGraph
├── web/                  # React/Vite frontend application
├── main.py               # Minimal CLI entry‑point to exercise the graph
├── requirements.txt      # Python dependencies
└── README.md             # ← you are reading this
```

Below is a high‑level description of each major directory:

### `src/rags`
- `school_data.json` – scraped records; each entry has `id`, `url`, `section`, `subsection`, and `content`.
- `rag.py` – functions to create or load a FAISS index using `sentence-transformers/all-MiniLM-L6-v2` embeddings and a `RecursiveCharacterTextSplitter`.

### `src/graphs`
- `graph.py` – builds a `StateGraph` with nodes like `retrieve`, `generate`, `grade_documents`, `transform_query`, etc.  It compiles to `app` used both by `main.py` and the API.

### `src/nodes/Node.py`
Implements the logic executed at each graph node:
- **retrieve** – fetch top‑k documents from the vectorstore.
- **grade_documents** – run a binary classifier prompt to filter irrelevants.
- **transform_query** – rewrite the question when retrieval fails.
- **generate** – call the RAG chain and optionally append a web search summary for AI‑related questions.
- **chat** – direct LLM call for casual conversation.
- **web_search** – invoke the Tavily search tool and normalise output.

### `src/Edges/Edge.py`
Contains simple mapping functions used to decide which edge to follow in the graph. For example, the `route_question` edge reads the output of a three‑way router LLM.

### `src/route`
Defines reusable LangChain chains and prompts:
- `routerprompt.py` – describes when to send a query to each datasource.
- `rewriteprompt.py` – prompt to rewrite questions for better retrieval.
- `reposnse.py` – the RAG prompt and post‑processing helper.
- `Grade*` modules – binary graders for document relevance, answer quality, and hallucination.
- `websearch.py` – configures the Tavily web search tool.

### `src/llms`
`Groqllm` wrapper bathes the Groq Chat model (currently `openai/gpt-oss-120b`) and exposes a simple `get_llm()`/`invoke()` API.

### `Api`
Standard FastAPI application with:
- user registration/login via JWT (`auth.py`),
- chat session creation and message history (`chat.py`),
- SQLAlchemy models (`models.py`) and DB utilities.

### `web`
Basic React frontend demonstrating chat interactions; uses environment variable `VITE_API_BASE_URL` to point at the backend.

---

## 🛠 Setup & Installation

> Tested on Windows with Python 3.11 and Node 20.

1. **Clone and enter the repo**
   ```bash
   git clone https://github.com/AdilHayat21173/sunmark-school-bot.git
   cd sunmark-school-bot
   ```

2. **Python dependencies**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment variables** (create a `.env` file at the repo root)
   ```env
   GROQ_API_KEY=<your groq key>
   TAVILY_API_KEY=<your tavily key>
   DATABASE_URL=sqlite:///./db.sqlite3      # or your PostgreSQL URL
   CORS_ORIGINS=http://localhost:5173      # frontend origin
   ```

4. **(Optional) build vectorstore**
   If you have updated or cleaned the scraped JSON, force a rebuild:
   ```python
   from src.rags.rag import get_vectorstore
   get_vectorstore(force_recreate=True)
   ```
   The index lives in `src/rags/sunmarke_faiss_index/`.

5. **Run the backend**
   ```bash
   uvicorn Api.main:app --reload
   ```
   The API will listen on `http://127.0.0.1:8000` by default.

6. **Run the frontend**
   ```bash
   cd web
   npm install
   npm run dev
   ```
   Visit `http://localhost:5173` and create an account to start chatting.

7. **CLI demo**
   ```bash
   python main.py
   ```
   Displays the graph state for a hard‑coded question.

---

## 📦 Data Scraping

The first step of the pipeline is scraping the Sunmarke website. The repository does **not** include an automated crawler, but the JSON file format is simple and can be populated by any script or manual process. Each record should look like:

```json
{
  "id": 1,
  "url": "https://www.sunmarke.com/about/",
  "section": "About",
  "subsection": "Mission, Vision, Values",
  "content": "<plain text extracted from the page>"
}
```

After obtaining the raw dump, you can optionally run your own cleaning passes and save the output as `school_data_cleaned.json`. The RAG module will prefer the cleaned file.

> **Tip:** use `requests` + `beautifulsoup4` to fetch and parse each page. Ensure that the `content` field is plain text (stripped of HTML).

Once the JSON is ready, rebuild the vectorstore (see setup step 4) so that new content is indexed.

---

## 🚀 Retrieval‑Augmented Generation (RAG)

The RAG machinery is implemented in `src/rags/rag.py` and wrapped by the `retrieve`/`generate` nodes in `src/nodes/Node.py`:

- Documents are split into 500‑token chunks using `RecursiveCharacterTextSplitter`.
- Embeddings are created with `sentence-transformers/all-MiniLM-L6-v2` (cpu) and stored in a FAISS index.
- The index is saved locally and re‑loaded on startup to avoid recomputing.

When a user question is routed to the vectorstore, the graph fetches the top‑1 chunk and passes it as context to a prompt defined in `src/route/reposnse.py`.

### Adaptive behaviour
The graph is designed to adapt when the retrieval chain fails:
1. After retrieval the `grade_documents` node runs a binary grader. If the returned chunk is unrelated, it is dropped.
2. `decide_to_generate` edge (see `src/Edges/Edge.py`) inspects the filtered list. If no documents remain it transitions to `transform_query`.
3. `transform_query` calls an LLM prompt that rewrites the question for better semantic match, then loops back to `retrieve`.
4. Once a generation is produced, another grader (`grade_generation_v_documents_and_question`) ensures the final answer is useful. If not, the cycle continues with a rewritten question.

This loop allows the system to iteratively refine the user query until the vectorstore can provide supporting facts or the chain gives up.

### Web search augmentation
If the question contains “AI” or “artificial intelligence”, the `generate` node also queries the Tavily web search tool and appends a second summary to the answer. This ensures up‑to‑date information when discussing fast‑moving topics.

---

## 🧠 Routing & Grading

- **Routing**: a structured LLM (`RouteQuery` in `src/route/route.py`) decides between `vectorstore`, `web_search` and `chat` based on a prompt describing heuristics for Sunmarke topics.
- **Grading**: three graders give binary (`yes`/`no`) scores:
  - document relevance (`Grade`)
  - answer‑question correspondence (`GradeAnswer`)
  - hallucination detection (`GradeHallucinations`)

These graders are used in the graph to filter documents and to decide when to rewrite or regenerate.

---

## 🧩 API & Frontend

The `/Api` folder contains a minimal FastAPI service that provides:
- user registration/login with JWT
- chat session creation and history storage (SQLAlchemy + SQLite/Postgres)
- a `/chat/{session_id}` endpoint that invokes the LangGraph `app` and returns the generated response

### 🗄️ Database & Authentication Details

- **User model**: each user is identified by email (used as the username in `models.User`).
- **Signup flow**: if an email is not already present in the database, the frontend prompts the visitor to register via `/register` before they can access the chatbot. The API returns a JWT token upon successful registration or login.
- **Session tracking**: when a logged‑in user clicks "New Chat" (or equivalent), the frontend calls `/chat/session` which creates a `ChatSession` record associated with the user's ID. This allows users to manage multiple independent conversations.
- **Message history**: all messages (user + assistant) are stored in the `Message` table and linked to a session. When the frontend loads a session, it requests `/chat/{session_id}/messages` and renders the previous exchange. This means each user sees only their own chats sorted by session, and different Gmail accounts are kept entirely separate.
- **Access control**: every chat endpoint depends on `oauth2.get_current_user()` which validates the JWT and ensures users can only read or append to their own sessions. Unauthorized access returns a 404 or 401.

The React frontend in `/web` communicates with these endpoints using helper functions in `web/src/api.js`. It supports creating sessions, listing past messages, and sending new messages.

> See `web/src/App.jsx` for a simple UI implementation.

---

## 📝 Loom Recording
For a walk‑through of the project and how to use it, watch the demo:

https://www.loom.com/share/ab6f6142235743cd875e6d6943ba86ab

---

## 💡 Tips & Next Steps

- **Extending to other websites**: replace `school_data.json` with data from the new domain and rebuild the vectorstore. Adjust the router prompt accordingly.
- **Scaling**: switch FAISS to a disk‑based index or use an external vector database. Increase `k` in retrieval for broader context.
- **Security**: add rate limiting and sanitise user inputs before passing to the LLM.
- **Improved scraping**: integrate a crawler library (e.g., `scrapy`) and automate periodic refreshes.

---

This README should give you all the context needed to understand, run, and modify the Sunmark School chatbot project. Happy coding! 🧑‍💻✨


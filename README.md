# LAWDECODE (Phase 7)

> **AI-Powered Legal Document Intelligence & Multi-Agent Analysis Platform**

LAWDECODE is an open, modular legal-tech platform engineered to assist individuals, legal practitioners, and businesses in deciphering dense legal documentation, identifying liabilities, researching relevant statutes and precedents, and generating actionable legal summaries.

---

## Phase 7 Overview

This repository contains **Phase 7** of LAWDECODE — a runnable local legal-information workflow featuring:
1. **Python FastAPI Backend**: High-performance asynchronous REST API.
2. **Google Gemini API Integration**: Gemini-only LLM integration reading keys strictly from `.env` without hardcoded credentials.
3. **Interactive Web Interface**: Single-page application for submitting legal queries, testing model outputs, and viewing agent pipeline statuses.
4. **Three-Agent Workflow**: Agent 1 (understanding), Agent 2 (research), and Agent 3 (final analysis).
5. **Local Tools and Memory**: Calculator, date/deadline, legal-text tools, plus local SQLite interaction memory.
6. **ReAct Workflow**: Gemini selects tools only when needed; concise workflow events remain visible while chain-of-thought stays private.
7. **Modular Multi-Agent Structure**: Standardized directory structure for autonomous agents:
   - `agents/legal_understanding_agent/` (Deconstruction & legalese simplification)
   - `agents/legal_research_agent/` (Statutory frameworks & case law research)
   - `agents/legal_analysis_agent/` (Risk assessment & strategic recommendations)
8. **Formatted Terminal Output**: Real-time console logs formatted for verification.
9. **Portable Local Setup**: Portable across Windows, macOS, and Linux without cloud databases or hardcoded paths.

---

## Architecture & Project Structure

```text
LawDecode/
├── agents/                           # Modular Multi-Agent System
│   ├── legal_understanding_agent/    # Agent 1: Parsing & legalese clarification
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── legal_research_agent/         # Agent 2: Precedents & statutory research
│   │   ├── __init__.py
│   │   └── agent.py
│   └── legal_analysis_agent/         # Agent 3: Risk assessment & recommendations
│       ├── __init__.py
│       └── agent.py
├── api/                              # REST API Layer
│   ├── __init__.py
│   └── routes.py                     # /api/health, /api/agents, /api/analyze
├── core/                             # Core Application Logic & Services
│   ├── __init__.py
│   ├── config.py                     # Environment and settings configuration
│   └── gemini_service.py             # Google Gemini API client & terminal logger
├── frontend/                         # Interactive User Interface
│   ├── index.html                    # Single-page application HTML
│   ├── style.css                     # Modern legal-tech CSS styling
│   └── app.js                        # Client-side API interactions
├── tools/                            # Calculator, date/deadline, and legal text tools
├── memory/                            # Local SQLite memory store (database ignored)
├── screenshots/                       # Optional project screenshots
├── .env.example                      # Template for environment configuration
├── .gitignore                        # Git exclusion rules (ignores .env, cache, etc.)
├── main.py                           # FastAPI application entrypoint
├── README.md                         # Project documentation
└── requirements.txt                  # Python package dependencies
```

---

## Prerequisites

- **Python 3.10+**
- **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

---

## Quickstart Guide

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/LawDecode.git
cd LawDecode
```

### 2. Create and Activate a Virtual Environment

- **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  *(Or use the Python launcher: `py -3.12 -m venv .venv`)*

- **On macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuring Gemini

> ⚠️ **IMPORTANT NOTICE FOR EVALUATORS & COLLABORATORS**
> 
> This project contains **NO hardcoded API keys**. 
> Anyone cloning or evaluating this repository must provide their **own valid Gemini API key** in a local `.env` file.
> The `.env` file is intentionally excluded from version control via `.gitignore` to protect credentials.

### Step-by-Step `.env` Setup:

1. In the root directory of the project, create a new file named `.env` by copying the provided `.env.example`:

   - **Windows:**
     ```cmd
     copy .env.example .env
     ```
   - **Linux / macOS:**
     ```bash
     cp .env.example .env
     ```

2. Open `.env` in any text editor and replace `your_gemini_api_key_here` with your actual API key:

  ```env
  GEMINI_API_KEY=your_key_here
  GEMINI_MODEL=gemini-3.5-flash-lite
  ```

3. Save the `.env` file.

> **Note:** If you run the project without setting an API key, the application will still launch cleanly. The web page and terminal will guide you on creating the `.env` file with clear instructions.
>
> **Quota note:** Gemini API keys are tied to a Google Cloud project. Replacing a key from the same project does not reset that project's model quota. If the API returns `429 RESOURCE_EXHAUSTED`, wait for the provider reset or use a key from a project with available quota and billing enabled.

The application uses Gemini only. Replacing `GEMINI_API_KEY` in `.env` with another valid Gemini key does not require source-code changes.

## How the Workflow Works

```text
User Query
  ↓
Retrieve relevant local SQLite memory
  ↓
Agent 1: Observe and understand the query
  ↓
Gemini decides whether a local tool is needed
  ↓
Execute selected tool, if any
  ↓
Agent 1 continues with the tool result
  ↓
Agent 2: Legal research
  ↓
Agent 3: Final legal analysis
  ↓
Save completed interaction to local SQLite memory
```

The ReAct workflow exposes concise status events such as `Agent 1 started`, `Tool selected`, `Tool completed`, and `Final analysis generated`. Internal chain-of-thought is not displayed.

### Available Local Tools

- **Calculator Tool**: Safe arithmetic and percentage calculations.
- **Date/Deadline Tool**: Date differences and deadline calculations.
- **Legal Text Tool**: Extracts and organizes important clauses from supplied text.

Tools are selected only when Gemini decides they are relevant. No external dataset, RAG system, vector database, or cloud database is used.

### Local Memory

Completed interactions are stored in `memory/lawdecode.sqlite3`. The database contains the query, all three agent outputs, final analysis, and timestamp. It is local to the machine and ignored by Git. Relevant previous interactions are retrieved before a new query and provided as context to the agents.

---

## Running the Application

Start the FastAPI application with either of the following commands:

### Option A: Direct Python Execution
```bash
python main.py
```
On Windows, activate the project environment first:
```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

### Option B: Using Uvicorn Directly
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## Accessing the Application

Once started, open your web browser to:

- **Web Interface:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative API Docs (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Terminal Verification Output

Every time an analysis query is submitted through the webpage or API, the backend outputs a structured terminal log:

```text
==================================================
LAWDECODE
=========

MEMORY: Retrieved 1 previous interactions
Agent 1 started
Tool selected: Legal Text Tool
Tool completed: Legal Text Tool
Agent 1 completed
Agent 2 started
Agent 2 completed
Agent 3 started
Agent 3 completed
Final analysis generated

Test Input:
Explain the standard scope and typical exceptions for confidentiality obligations in an NDA.

Final Analysis:
The analysis is displayed in the web interface and terminal...
==================================================
```

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the LAWDECODE single page web application |
| `GET` | `/api/health` | Diagnostic endpoint checking server health and API key presence |
| `GET` | `/api/agents` | Lists the three active agents |
| `POST` | `/api/analyze` | Runs memory retrieval, ReAct tool selection, and the three-agent Gemini workflow |

## Screenshots

Place screenshots in `screenshots/` before pushing to GitHub. For example:

```markdown
![LAWDECODE interface](screenshots/lawdecode-interface.png)
```

---

## Local Data and GitHub Safety

The local `.env` file and `memory/lawdecode.sqlite3` database are ignored by Git. Commit `.env.example`, never `.env`, and never commit real keys or generated local data. Virtual environments, caches, logs, and temporary files are also ignored.

## Legal Disclaimer

LAWDECODE provides general legal information for educational and analytical purposes. It is not a substitute for advice from a qualified lawyer. Results may be incomplete or incorrect and should be reviewed against the applicable contract, jurisdiction, and facts.

## Future Roadmap

- **Future:** Additional local-only improvements may be added without introducing cloud databases, RAG, or vector storage unless explicitly requested.

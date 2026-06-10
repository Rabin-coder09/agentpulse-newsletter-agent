# ⚡ AgentPulse — Autonomous Newsletter Agent

> A fully autonomous, multi-agent AI pipeline that researches, writes, critiques, improves, and publishes a professional HTML newsletter — end to end — from a single function call.

![Pipeline](https://img.shields.io/badge/Pipeline-LangGraph-6366f1?style=flat-square)
![LLM](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3%2070B-f59e0b?style=flat-square)
![Search](https://img.shields.io/badge/Search-Tavily-34d399?style=flat-square)
![Backend](https://img.shields.io/badge/Backend-FastAPI-06b6d4?style=flat-square)
![Frontend](https://img.shields.io/badge/Frontend-React-61dafb?style=flat-square)

---
## Website
Website link: https://agentpulse-our3.onrender.com/ui

---

## 🎯 Assignment Objective

Build a mini autonomous AI agent that acts as a "Newsletter Agent" — receiving a plain English goal and autonomously handling all research, writing, self-review, and publishing steps without human intervention.

---

## 🏗️ Architecture

```
Goal Input (plain English)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│                  LangGraph State Machine               │
│                                                       │
│  🧠 Planner ──► 🔍 Researcher ──► 📝 Summarizer       │
│                                         │             │
│                                         ▼             │
│  📤 Publisher ◄── 🚀 Improver ◄── 🔎 Critic ◄── ✍️ Writer │
│                                                       │
│  [HITL Mode: Human Approval gate between Critic → Improver] │
└───────────────────────────────────────────────────────┘
        │
        ▼
  HTML Newsletter saved to outputs/
  + Simulated send log with subscriber stats
```

Each node is an independent agent with its own system prompt and responsibility. State flows through all nodes via a typed `NewsletterState` object.

---

## ✨ Features

### Core (Assignment Requirements)
| Requirement | Implementation |
|---|---|
| Plain English goal input | Single `run_newsletter_agent(goal)` call |
| Web research | Tavily Search API — 5 parallel queries, 8+ results each |
| Summarize top articles | LLM-powered curation of top 6 stories with insights |
| Generate clean newsletter | Full HTML with inline CSS, category badges, Editor's Pick |
| Simulate send | Logged send report with subject, recipients, open rate |
| Multi-step reasoning | 7-node LangGraph pipeline: Plan → Research → Summarize → Write → Critique → Improve → Publish |
| Tool use (3+) | Tavily Search, LLM Summarizer, HTML Generator, Memory Store |
| Self-reflection / critique | Dedicated Critic node scores 5 dimensions /10 and suggests improvements |
| Fully autonomous | One function call runs the entire pipeline |
| Human-in-the-Loop toggle | HITL mode pauses after critique for human approval (approve / edit / reject) |

### Bonus Features
- 📊 **Analytics Dashboard** — quality scores, word counts, reading time across all runs
- 📁 **Newsletter History** — persistent JSON memory of all past runs with metadata
- 🌐 **Multi-topic Support** — 5 preset topics + custom input (AI Agents, Cybersecurity, Startups, Web3, Healthcare)
- ⬇️ **Download Button** — one-click HTML download from the UI
- 📈 **Live Pipeline Visualization** — each step lights up in real-time as the agent progresses
- 🔄 **Streaming Job Status** — React frontend polls every 1.5s for live updates
- 🎨 **Professional Dark UI** — 3-column layout with stats, preview iframe, send report

---

## 🤖 Agent Pipeline — Node by Node

### 1. 🧠 Planner
Analyzes the goal and generates a strategic research plan with 5 targeted search queries. Returns structured JSON with plan + queries.

### 2. 🔍 Researcher  
Executes all 5 search queries via Tavily, collects 8 results per query, deduplicates by URL, and returns up to 12 unique articles.

### 3. 📝 Summarizer
Sends all articles to the LLM and curates the **top 6 most important stories**, each with: title, 2-3 sentence summary, key insight, source URL, and category tag (Research / Tools / Industry / Product / Policy).

### 4. ✍️ Writer
Generates a complete, visually polished **HTML newsletter** with:
- Dark header with newsletter name and date
- Article cards with rank badges, category pills, Editor's Pick highlight
- Key insight boxes per story
- Engaging intro paragraph
- Footer with unsubscribe link
- Subject line generated separately

### 5. 🔎 Critic (Self-Reflection)
Evaluates the draft newsletter on 5 dimensions:
- Headlines quality
- Content depth
- Structure & flow
- HTML/Visual design
- Call-to-action

Scores each /10 and lists **3 specific improvements**.

### 6. *(HITL only)* 🙋 Human Review
In Human-in-the-Loop mode, the agent pauses here and presents the draft + critique to the user. User can `approve`, `edit`, or `reject`.

### 7. 🚀 Improver
Takes the original draft + critique and applies all suggested improvements. Produces a higher-quality final version.

### 8. 📤 Publisher
Saves the final newsletter as a timestamped HTML file in `outputs/`, logs the simulated send (subject line, recipient count, timestamp, open rate), and records the run in persistent memory.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph (StateGraph) |
| LLM | Groq — LLaMA 3.3 70B Versatile |
| Web Search | Tavily Search API |
| Backend API | FastAPI + Uvicorn |
| Frontend | React 18 (CDN, no build step) |
| State Management | TypedDict + Annotated reducers |
| Persistence | JSON file (outputs/newsletter_history.json) |
| Environment | Python 3.11, conda |

---

## 📁 Project Structure

```
newsletter_agent_app/
├── .env                          # API keys (not committed)
├── run.py                        # Server launcher + auto browser open
├── src/
│   ├── agent.py                  # Full LangGraph pipeline + memory system
│   └── api.py                    # FastAPI backend (jobs, status, analytics)
├── templates/
│   └── index.html                # React frontend (single file, no build)
└── outputs/
    ├── newsletter_YYYYMMDD_HHMMSS.html   # Generated newsletters
    └── newsletter_history.json           # Persistent run memory
```

---

## 🚀 Setup & Run

### Prerequisites
- [Anaconda](https://www.anaconda.com/) or Miniconda
- [Groq API key](https://console.groq.com) (free)
- [Tavily API key](https://app.tavily.com) (free, 1000 searches/month)

### Installation

```bash
# 1. Create environment
conda create -n newsletter_agent python=3.11 -y
conda activate newsletter_agent

# 2. Install dependencies
pip install langgraph langchain langchain-groq langchain-community \
            tavily-python fastapi uvicorn python-dotenv jinja2 aiofiles

# 3. Create .env file in project root
echo "GROQ_API_KEY=your_key_here" > .env
echo "TAVILY_API_KEY=your_key_here" >> .env

# 4. Run
python run.py
```

### Access
| URL | Description |
|---|---|
| http://localhost:8000/ui | Main UI |
| http://localhost:8000/docs | FastAPI Swagger docs |
| http://localhost:8000/analytics | Analytics JSON |
| http://localhost:8000/history | History JSON |

---

## 💻 Usage

### Option 1 — Web UI
1. Open `http://localhost:8000/ui`
2. Select a topic or enter a custom goal
3. Choose **Fully Auto** or **Human-in-Loop** mode
4. Click **🚀 Run Newsletter Agent**
5. Watch the pipeline execute live
6. Download the HTML newsletter when complete

### Option 2 — Python (single function call)
```python
from src.agent import run_newsletter_agent

# Fully autonomous
result = run_newsletter_agent(
    goal="Create a weekly newsletter on latest AI agent news.",
    mode="auto"   # or "hitl" for Human-in-the-Loop
)

print(result["subject_line"])
print(result["send_log"])
# Newsletter saved to outputs/
```

---

## 📊 Output Example

```
╔══════════════════════════════════════════════════════╗
║           📧 NEWSLETTER SEND SIMULATION              ║
╠══════════════════════════════════════════════════════╣
║ Status    : ✅ SENT SUCCESSFULLY                     ║
║ Subject   : The 2025 AI Agent Index: Transparency... ║
║ Recipients: 1,247 subscribers                        ║
║ Sent At   : 2026-06-09 00:23:57                      ║
║ Open Rate : ~42% (estimated)                         ║
╚══════════════════════════════════════════════════════╝
```

Generated newsletters are saved as standalone HTML files with full inline CSS — ready to send via any email platform.

---

## 🔑 Key Design Decisions

**Why LangGraph over plain LangChain?**  
LangGraph gives explicit control over the agent's state machine — each node is isolated, the graph is inspectable, and conditional edges make the HITL toggle clean and maintainable.

**Why Groq?**  
Groq's LPU inference delivers sub-second token generation, making the full 7-step pipeline complete in ~90 seconds instead of 5+ minutes with slower APIs.

**Why a separate Critic node instead of self-editing?**  
Separating evaluation from generation improves output quality. The Critic uses a different prompt perspective (harsh editor vs. creative writer), which produces more actionable feedback.

**Why FastAPI + background tasks?**  
The agent pipeline takes 60-120 seconds. Running it as a background job with polling lets the UI stay responsive and show live progress without blocking.

---

## 📝 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/ui` | GET | Serve React frontend |
| `/run` | POST | Start agent job, returns `job_id` |
| `/status/{job_id}` | GET | Poll job status + logs |
| `/analytics` | GET | Aggregated stats across all runs |
| `/history` | GET | Full newsletter history |
| `/health` | GET | Health check |

**POST /run body:**
```json
{
  "goal": "Create a weekly newsletter on latest AI agent news.",
  "mode": "auto"
}
```

---

## 🏆 What Makes This Stand Out

1. **True agentic behavior** — not a sequential script. LangGraph's state machine means each node can fail independently, retry, or branch based on conditions.
2. **Self-improvement loop** — the Critic → Improver cycle means every newsletter is evaluated and enhanced before publishing, not just generated once.
3. **Production-grade patterns** — background jobs, job store, polling API, persistent memory — mirrors how real AI products are built.
4. **Zero-dependency frontend** — React via CDN, no npm, no build step. Runs anywhere instantly.
5. **Multi-topic flexibility** — the same pipeline works for any newsletter topic without code changes.

---

## 👤 Author

Built as part of AI Developer Internship Assignment  

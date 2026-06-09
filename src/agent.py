import os
import sys
import json
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Optional
import operator

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# ─────────────────────────────────────────────
# LLM + Tools
# ─────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

search_tool = TavilySearchResults(
    max_results=8,
    api_key=os.getenv("TAVILY_API_KEY")
)

# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class NewsletterState(TypedDict):
    goal: str
    mode: str  # "auto" or "hitl"
    plan: str
    search_queries: List[str]
    raw_articles: List[dict]
    summaries: List[dict]
    newsletter_draft: str
    critique: str
    improved_newsletter: str
    final_newsletter: str
    subject_line: str
    send_log: str
    current_step: str
    human_approval: Optional[str]
    steps_log: Annotated[List[str], operator.add]

# ─────────────────────────────────────────────
# Node 1: Planner
# ─────────────────────────────────────────────
def planner_node(state: NewsletterState) -> dict:
    print("\n🧠 [PLANNER] Creating research plan...")
    
    response = llm.invoke([
        SystemMessage(content="""You are a senior newsletter strategist. 
        Given a goal, create a detailed execution plan and 5 specific search queries 
        to find the most relevant and latest news. 
        Respond in this exact JSON format:
        {
            "plan": "step by step plan here",
            "search_queries": ["query1", "query2", "query3", "query4", "query5"]
        }
        Return ONLY the JSON, no extra text."""),
        HumanMessage(content=f"Goal: {state['goal']}")
    ])
    
    try:
        clean = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean)
        plan = data.get("plan", "")
        queries = data.get("search_queries", [])
    except:
        plan = response.content
        queries = [
            "latest AI agent news 2025",
            "AI autonomous agents breakthrough 2025",
            "LangChain LangGraph updates 2025",
            "OpenAI GPT agents news 2025",
            "AI agent frameworks comparison 2025"
        ]
    
    return {
        "plan": plan,
        "search_queries": queries,
        "current_step": "planned",
        "steps_log": [f"✅ PLANNER: Created plan with {len(queries)} search queries"]
    }

# ─────────────────────────────────────────────
# Node 2: Researcher
# ─────────────────────────────────────────────
def researcher_node(state: NewsletterState) -> dict:
    print("\n🔍 [RESEARCHER] Searching the web...")
    
    all_articles = []
    for query in state["search_queries"]:
        try:
            results = search_tool.invoke(query)
            for r in results:
                if isinstance(r, dict):
                    all_articles.append({
                        "title": r.get("title", "No title"),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:800],
                        "query": query
                    })
        except Exception as e:
            print(f"  ⚠️ Search error for '{query}': {e}")
    
    # Deduplicate by URL
    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    
    print(f"  Found {len(unique)} unique articles")
    return {
        "raw_articles": unique[:12],
        "current_step": "researched",
        "steps_log": [f"✅ RESEARCHER: Found {len(unique)} unique articles across {len(state['search_queries'])} queries"]
    }

# ─────────────────────────────────────────────
# Node 3: Summarizer
# ─────────────────────────────────────────────
def summarizer_node(state: NewsletterState) -> dict:
    print("\n📝 [SUMMARIZER] Summarizing articles...")
    
    articles_text = "\n\n".join([
        f"Title: {a['title']}\nURL: {a['url']}\nContent: {a['content']}"
        for a in state["raw_articles"]
    ])
    
    response = llm.invoke([
        SystemMessage(content="""You are an expert AI news curator. 
        From the provided articles, select and summarize the TOP 6 most important, 
        interesting, and relevant stories about AI agents.
        
        Return ONLY a JSON array in this format:
        [
          {
            "rank": 1,
            "title": "Catchy headline",
            "summary": "2-3 sentence engaging summary",
            "key_insight": "One powerful takeaway",
            "url": "source url",
            "category": "one of: Research/Tools/Industry/Product/Policy"
          }
        ]
        Return ONLY valid JSON array, no extra text."""),
        HumanMessage(content=f"Articles to analyze:\n{articles_text}")
    ])
    
    try:
        clean = response.content.strip().replace("```json", "").replace("```", "")
        summaries = json.loads(clean)
    except:
        summaries = [
            {
                "rank": i+1,
                "title": a["title"],
                "summary": a["content"][:200],
                "key_insight": "Important development in AI agents space",
                "url": a["url"],
                "category": "Research"
            }
            for i, a in enumerate(state["raw_articles"][:6])
        ]
    
    return {
        "summaries": summaries,
        "current_step": "summarized",
        "steps_log": [f"✅ SUMMARIZER: Curated top {len(summaries)} stories"]
    }

# ─────────────────────────────────────────────
# Node 4: Writer
# ─────────────────────────────────────────────
def writer_node(state: NewsletterState) -> dict:
    print("\n✍️  [WRITER] Generating newsletter...")
    
    summaries_text = json.dumps(state["summaries"], indent=2)
    today = datetime.now().strftime("%B %d, %Y")
    
    response = llm.invoke([
        SystemMessage(content=f"""You are a world-class tech newsletter writer (like Morning Brew or TLDR).
        Write a stunning, professional HTML newsletter about AI agents.
        
        Requirements:
        - Use inline CSS for beautiful styling (dark header, clean cards, modern fonts)
        - Include: header with logo emoji + title + date, intro paragraph, 
          6 article cards with category badges, key insight boxes, 
          footer with unsubscribe link
        - Make it visually stunning with colors: #0f172a (dark), #6366f1 (purple accent), #f8fafc (light)
        - Each article card must show: rank badge, category, title, summary, key insight, read more link
        - Add a "Editor's Pick" badge on rank #1
        - Write an engaging intro (2-3 sentences) about the week in AI agents
        - Today's date: {today}
        - Newsletter name: "AgentPulse Weekly"
        
        Return ONLY the complete HTML, nothing else."""),
        HumanMessage(content=f"Stories to feature:\n{summaries_text}")
    ])
    
    subject_resp = llm.invoke([
        SystemMessage(content="Write a single compelling email subject line for this AI newsletter. Return ONLY the subject line, nothing else."),
        HumanMessage(content=f"Newsletter preview: {state['summaries'][0]['title'] if state['summaries'] else 'AI Agent News'}")
    ])
    
    return {
        "newsletter_draft": response.content,
        "subject_line": subject_resp.content.strip(),
        "current_step": "drafted",
        "steps_log": ["✅ WRITER: Generated full HTML newsletter draft"]
    }

# ─────────────────────────────────────────────
# Node 5: Critic (Self-Reflection)
# ─────────────────────────────────────────────
def critic_node(state: NewsletterState) -> dict:
    print("\n🔎 [CRITIC] Self-evaluating newsletter...")
    
    response = llm.invoke([
        SystemMessage(content="""You are a harsh but fair newsletter editor. 
        Review this newsletter draft and provide specific critique.
        
        Evaluate on:
        1. Headline quality (catchy? clear?)
        2. Content depth (insightful? not superficial?)
        3. Structure & flow (easy to scan?)
        4. HTML/Visual design (professional?)
        5. Call-to-action (engaging?)
        
        Give a score /10 for each. Then list 3 specific improvements.
        Be concise. Format:
        SCORES:
        - Headlines: X/10
        - Content: X/10  
        - Structure: X/10
        - Design: X/10
        - CTA: X/10
        
        TOP 3 IMPROVEMENTS:
        1. ...
        2. ...
        3. ..."""),
        HumanMessage(content=f"Newsletter to review:\n{state['newsletter_draft'][:3000]}")
    ])
    
    return {
        "critique": response.content,
        "current_step": "critiqued",
        "steps_log": [f"✅ CRITIC: Self-reflection complete — improvements identified"]
    }

# ─────────────────────────────────────────────
# Node 6: Improver
# ─────────────────────────────────────────────
def improver_node(state: NewsletterState) -> dict:
    print("\n🚀 [IMPROVER] Applying improvements...")
    
    response = llm.invoke([
        SystemMessage(content="""You are a senior newsletter editor. 
        Take the original newsletter HTML and the critique, then produce an improved version.
        Apply ALL suggested improvements while keeping the full HTML structure intact.
        Make headlines more punchy, deepen insights, improve visual hierarchy.
        Return ONLY the improved complete HTML."""),
        HumanMessage(content=f"""
Original Newsletter:
{state['newsletter_draft']}

Critique & Improvements to apply:
{state['critique']}
        """)
    ])
    
    return {
        "improved_newsletter": response.content,
        "current_step": "improved",
        "steps_log": ["✅ IMPROVER: Applied all critique suggestions — newsletter enhanced"]
    }

# ─────────────────────────────────────────────
# Node 7: Publisher
# ─────────────────────────────────────────────
def publisher_node(state: NewsletterState) -> dict:
    print("\n📤 [PUBLISHER] Publishing newsletter...")
    
    final = state.get("improved_newsletter") or state.get("newsletter_draft", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/newsletter_{timestamp}.html"
    
    os.makedirs("outputs", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final)
    
    send_log = f"""
╔══════════════════════════════════════════════════╗
║           📧 NEWSLETTER SEND SIMULATION          ║
╠══════════════════════════════════════════════════╣
║ Status    : ✅ SENT SUCCESSFULLY                 ║
║ Subject   : {state['subject_line'][:45]:<45} ║
║ Recipients: 1,247 subscribers                    ║
║ Sent At   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<45} ║
║ File      : {filename:<45} ║
║ Open Rate : ~42% (estimated)                     ║
╚══════════════════════════════════════════════════╝
    """.strip()
    
    print(send_log)
    # Save to memory
    save_to_memory({**state, "final_newsletter": final})
    return {
        "final_newsletter": final,
        "send_log": send_log,
        "current_step": "published",
        "steps_log": [f"✅ PUBLISHER: Newsletter saved to {filename} and simulated send complete"]
    }

# ─────────────────────────────────────────────
# Human-in-the-Loop Check
# ─────────────────────────────────────────────
def should_get_approval(state: NewsletterState) -> str:
    if state.get("mode") == "hitl":
        return "wait_for_approval"
    return "improver"

def approval_node(state: NewsletterState) -> dict:
    print("\n⏸️  [HUMAN-IN-THE-LOOP] Waiting for human approval...")
    print("\n--- DRAFT PREVIEW (first 500 chars) ---")
    print(state["newsletter_draft"][:500])
    print("\n--- CRITIQUE ---")
    print(state["critique"])
    
    approval = input("\n✋ Approve newsletter? (yes/edit/reject): ").strip().lower()
    
    return {
        "human_approval": approval,
        "steps_log": [f"✅ HUMAN REVIEW: Decision = '{approval}'"]
    }

def after_approval(state: NewsletterState) -> str:
    approval = state.get("human_approval", "yes")
    if approval == "reject":
        return END
    return "improver"

# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────
def build_graph():
    g = StateGraph(NewsletterState)
    
    g.add_node("planner", planner_node)
    g.add_node("researcher", researcher_node)
    g.add_node("summarizer", summarizer_node)
    g.add_node("writer", writer_node)
    g.add_node("critic", critic_node)
    g.add_node("wait_for_approval", approval_node)
    g.add_node("improver", improver_node)
    g.add_node("publisher", publisher_node)
    
    g.set_entry_point("planner")
    g.add_edge("planner", "researcher")
    g.add_edge("researcher", "summarizer")
    g.add_edge("summarizer", "writer")
    g.add_edge("writer", "critic")
    g.add_conditional_edges("critic", should_get_approval, {
        "wait_for_approval": "wait_for_approval",
        "improver": "improver"
    })
    g.add_conditional_edges("wait_for_approval", after_approval, {
        "improver": "improver",
        END: END
    })
    g.add_edge("improver", "publisher")
    g.add_edge("publisher", END)
    
    return g.compile()

# ─────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────
def run_newsletter_agent(goal: str, mode: str = "auto") -> dict:
    graph = build_graph()
    
    initial_state = NewsletterState(
        goal=goal,
        mode=mode,
        plan="",
        search_queries=[],
        raw_articles=[],
        summaries=[],
        newsletter_draft="",
        critique="",
        improved_newsletter="",
        final_newsletter="",
        subject_line="",
        send_log="",
        current_step="init",
        human_approval=None,
        steps_log=[]
    )
    
    print(f"\n🚀 Starting Newsletter Agent in '{mode.upper()}' mode...")
    print(f"📋 Goal: {goal}\n")
    
    result = graph.invoke(initial_state)
    
    print("\n\n📊 AGENT EXECUTION SUMMARY:")
    for log in result["steps_log"]:
        print(f"  {log}")
    
    return result


if __name__ == "__main__":
    result = run_newsletter_agent(
        goal="Create a weekly newsletter on latest AI agent news and send it to our subscribers.",
        mode="auto"
    )

# ─────────────────────────────────────────────
# Newsletter Memory System
# ─────────────────────────────────────────────
import json
from datetime import datetime

MEMORY_FILE = "outputs/newsletter_history.json"

def save_to_memory(result: dict):
    os.makedirs("outputs", exist_ok=True)
    history = load_memory()
    
    entry = {
        "id": str(uuid.uuid4())[:8] if 'uuid' in sys.modules else datetime.now().strftime("%H%M%S"),
        "timestamp": datetime.now().isoformat(),
        "subject_line": result.get("subject_line", ""),
        "goal": result.get("goal", ""),
        "mode": result.get("mode", "auto"),
        "articles_found": len(result.get("raw_articles", [])),
        "stories_featured": len(result.get("summaries", [])),
        "word_count": len(result.get("final_newsletter", "").split()),
        "reading_time": max(1, len(result.get("final_newsletter", "").split()) // 200),
        "critique_score": extract_avg_score(result.get("critique", "")),
        "filename": f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    }
    
    history.insert(0, entry)
    history = history[:20]  # keep last 20
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    
    return entry

def load_memory() -> list:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def extract_avg_score(critique: str) -> float:
    import re
    scores = re.findall(r'(\d+(?:\.\d+)?)/10', critique)
    if scores:
        return round(sum(float(s) for s in scores) / len(scores), 1)
    return 0.0    
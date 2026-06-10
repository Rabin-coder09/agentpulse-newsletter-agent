import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import uuid
from typing import Optional
import json

from agent import run_newsletter_agent

app = FastAPI(title="Newsletter Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs = {}

class AgentRequest(BaseModel):
    goal: str
    mode: str = "auto"  # "auto" or "hitl"

class JobStatus(BaseModel):
    job_id: str
    status: str
    steps_log: list = []
    send_log: str = ""
    subject_line: str = ""
    newsletter_preview: str = ""
    error: Optional[str] = None


def run_agent_job(job_id: str, goal: str, mode: str):
    try:
        jobs[job_id]["status"] = "running"
        import agent as agent_module

        original_planner = agent_module.planner_node
        original_researcher = agent_module.researcher_node
        original_summarizer = agent_module.summarizer_node
        original_writer = agent_module.writer_node
        original_critic = agent_module.critic_node
        original_improver = agent_module.improver_node
        original_publisher = agent_module.publisher_node

        def patched(fn, step_name):
            def wrapper(state):
                jobs[job_id]["steps_log"].append(f"⏳ Running: {step_name}...")
                result = fn(state)
                # Remove running log, add done log
                logs = jobs[job_id]["steps_log"]
                logs = [l for l in logs if l != f"⏳ Running: {step_name}..."]
                logs.append(f"✅ {step_name}: Complete")
                jobs[job_id]["steps_log"] = logs
                return result
            return wrapper

        agent_module.planner_node = patched(original_planner, "Planner")
        agent_module.researcher_node = patched(original_researcher, "Researcher")
        agent_module.summarizer_node = patched(original_summarizer, "Summarizer")
        agent_module.writer_node = patched(original_writer, "Writer")
        agent_module.critic_node = patched(original_critic, "Critic")
        agent_module.improver_node = patched(original_improver, "Improver")
        agent_module.publisher_node = patched(original_publisher, "Publisher")

        result = agent_module.run_newsletter_agent(goal=goal, mode=mode)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["steps_log"] = result.get("steps_log", jobs[job_id]["steps_log"])
        jobs[job_id]["send_log"] = result.get("send_log", "")
        jobs[job_id]["subject_line"] = result.get("subject_line", "")
        jobs[job_id]["newsletter_preview"] = result.get("final_newsletter", "")[:8000]

        agent_module.planner_node = original_planner
        agent_module.researcher_node = original_researcher
        agent_module.summarizer_node = original_summarizer
        agent_module.writer_node = original_writer
        agent_module.critic_node = original_critic
        agent_module.improver_node = original_improver
        agent_module.publisher_node = original_publisher

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"❌ Job {job_id} failed: {e}")

from fastapi.responses import FileResponse

@app.get("/ui")
async def serve_ui():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
    )

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/ui")

@app.post("/run", response_model=JobStatus)
async def run_agent(req: AgentRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "steps_log": [],
        "send_log": "",
        "subject_line": "",
        "newsletter_preview": "",
        "error": None
    }
    background_tasks.add_task(run_agent_job, job_id, req.goal, req.mode)
    return JobStatus(job_id=job_id, status="queued")


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JobStatus(job_id=job_id, status="not_found")
    return JobStatus(**job)


@app.get("/jobs")
async def list_jobs():
    return list(jobs.values())


@app.get("/health")
async def health():
    return {"status": "ok", "message": "Newsletter Agent API is running"}

from agent import load_memory, save_to_memory

@app.get("/history")
async def get_history():
    return load_memory()

@app.get("/analytics")
async def get_analytics():
    history = load_memory()
    if not history:
        return {"total_runs": 0}
    
    total = len(history)
    avg_score = round(sum(h.get("critique_score", 0) for h in history) / total, 1)
    avg_words = round(sum(h.get("word_count", 0) for h in history) / total)
    avg_reading = round(sum(h.get("reading_time", 0) for h in history) / total)
    total_articles = sum(h.get("articles_found", 0) for h in history)
    
    return {
        "total_runs": total,
        "avg_quality_score": avg_score,
        "avg_word_count": avg_words,
        "avg_reading_time_mins": avg_reading,
        "total_articles_researched": total_articles,
        "last_run": history[0]["timestamp"] if history else None,
        "history": history
    }
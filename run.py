import uvicorn
import os
import sys
import webbrowser
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000/ui")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════╗
║         ⚡ AgentPulse Newsletter Agent               ║
║         Autonomous AI Newsletter Generator           ║
╠══════════════════════════════════════════════════════╣
║  Backend API  : http://localhost:8000                ║
║  Frontend UI  : http://localhost:8000/ui             ║
║  API Docs     : http://localhost:8000/docs           ║
╚══════════════════════════════════════════════════════╝
    """)
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
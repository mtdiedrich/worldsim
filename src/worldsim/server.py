"""FastAPI backend server."""

import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, responses
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from worldsim.engine import new_run, step, get_summary_state, write_output
from worldsim.config import N_TICKS, RUN_SEED

logger = logging.getLogger(__name__)

# Module-level state
CURRENT_RUN = None

# FastAPI app
app = FastAPI(title="Worldsim")

# Enable CORS for localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class RunRequest(BaseModel):
    seed: int = RUN_SEED
    ticks: int = N_TICKS


class StepResponse(BaseModel):
    tick: int
    status: str
    new_events: list


# Routes

@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    web_dir = Path(__file__).parent / "web"
    index_file = web_dir / "index.html"
    
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    return responses.HTMLResponse(content=content)


@app.post("/api/run")
async def api_start_run(request: RunRequest):
    """Start a new simulation run."""
    global CURRENT_RUN
    
    CURRENT_RUN = new_run(run_seed=request.seed, n_ticks=request.ticks)
    
    return {
        "ok": True,
        "tick": CURRENT_RUN["tick"],
    }


@app.post("/api/step")
async def api_step():
    """Advance the current run by one tick."""
    global CURRENT_RUN
    
    if CURRENT_RUN is None:
        raise HTTPException(status_code=400, detail="No run in progress. Call /api/run first.")
    
    step(CURRENT_RUN)
    
    new_events = CURRENT_RUN.get("new_events", [])
    
    return {
        "tick": CURRENT_RUN["tick"],
        "status": CURRENT_RUN["status"],
        "new_events": new_events,
    }


@app.get("/api/state")
async def api_get_state():
    """Get the current simulation state summary."""
    global CURRENT_RUN
    
    if CURRENT_RUN is None:
        raise HTTPException(status_code=400, detail="No run in progress.")
    
    return get_summary_state(CURRENT_RUN)


@app.get("/api/history")
async def api_get_history():
    """Get the full event log."""
    global CURRENT_RUN
    
    if CURRENT_RUN is None:
        raise HTTPException(status_code=400, detail="No run in progress.")
    
    return {
        "events": CURRENT_RUN["world"]["event_log"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

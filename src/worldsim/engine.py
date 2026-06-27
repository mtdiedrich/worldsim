"""Simulation engine - tick-based evolution."""

import random
import copy
import json
from pathlib import Path
from worldsim.config import RUN_SEED, N_TICKS
from worldsim.seeds import get_initial_world, CULTURE_SEEDS
from worldsim.memory import create_empty_memory, update_memory
from worldsim.view import build_filtered_view
from worldsim.agent import run_agent
from worldsim.arbiter import resolve
from worldsim.economy import apply_economy, maybe_random_event


def new_run(run_seed: int = RUN_SEED, n_ticks: int = N_TICKS) -> dict:
    """
    Initialize a new simulation run.
    
    Args:
        run_seed: Seed for RNG
        n_ticks: Number of ticks to simulate
        
    Returns:
        run_state dict
    """
    random.seed(run_seed)
    
    world = get_initial_world()
    memory = {}
    for culture_id in world["cultures"].keys():
        memory[culture_id] = create_empty_memory(culture_id)
    
    return {
        "world": world,
        "memory": memory,
        "tick": 0,
        "n_ticks": n_ticks,
        "status": "idle",
        "error_message": None,
        "run_seed": run_seed,
    }


def step(run_state: dict) -> dict:
    """
    Execute one tick of the simulation.
    
    Args:
        run_state: Current run state (modified in place)
        
    Returns:
        Updated run_state
    """
    if run_state["status"] == "error":
        return run_state
    
    if run_state["tick"] >= run_state["n_ticks"]:
        run_state["status"] = "complete"
        return run_state
    
    try:
        world = run_state["world"]
        memory = run_state["memory"]
        
        # Increment tick
        run_state["tick"] += 1
        world["tick"] = run_state["tick"]
        
        # Run economy (production, consumption, growth, starvation) and random events
        tick_events = apply_economy(world)
        tick_events += maybe_random_event(world)
        world["event_log"].extend(tick_events)
        
        # Collect actions from each culture
        collected_actions = []
        for culture_id in sorted(world["cultures"].keys()):
            view = build_filtered_view(world, culture_id)
            seed_cfg = CULTURE_SEEDS[culture_id]
            action = run_agent(seed_cfg, memory[culture_id], view)
            
            # Update memory with beliefs
            memory[culture_id] = update_memory(
                memory[culture_id],
                events=[],
                beliefs=action.get("beliefs")
            )
            
            collected_actions.append(action)
        
        # Resolve actions into world changes
        new_world, events = resolve(world, collected_actions)
        world.update(new_world)
        world["event_log"].extend(events)
        
        # All events this tick: economy/world events + action events
        all_tick_events = tick_events + events
        
        # Feed all events back into memory
        for culture_id in world["cultures"]:
            relevant = [e for e in all_tick_events if culture_id in e["involved"]]
            memory[culture_id] = update_memory(
                memory[culture_id],
                events=relevant,
                beliefs=None
            )
        
        run_state["status"] = "running" if run_state["tick"] < run_state["n_ticks"] else "complete"
        
        # Store new events for this tick (for API response)
        run_state["new_events"] = all_tick_events
        
        return run_state
    
    except Exception as e:
        run_state["status"] = "error"
        run_state["error_message"] = str(e)
        return run_state


def get_summary_state(run_state: dict) -> dict:
    """
    Get a summary of current state for the API/UI.
    
    Returns dict with tick, status, cultures summary, regions summary, event count.
    """
    world = run_state["world"]
    
    cultures_summary = {}
    for culture_id, culture in world["cultures"].items():
        cultures_summary[culture_id] = {
            "name": culture["name"],
            "population": culture["population"],
            "resources": copy.copy(culture["resources"]),
            "tech_count": len(culture["tech"]),
            "relations": copy.copy(culture["relations"]),
        }
    
    regions_summary = {}
    for region_id, region in world["regions"].items():
        regions_summary[region_id] = {
            "name": region["name"],
            "occupant": region["occupant"],
            "resources": copy.copy(region["resources"]),
        }
    
    return {
        "tick": run_state["tick"],
        "status": run_state["status"],
        "cultures": cultures_summary,
        "regions": regions_summary,
        "event_count": len(world["event_log"]),
    }


def write_output(run_state: dict, output_dir: str = "out") -> None:
    """Write final outputs to disk."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    world = run_state["world"]
    tick = run_state["tick"]
    
    # Write final world state
    final_file = output_path / "final.json"
    with open(final_file, "w", encoding="utf-8") as f:
        json.dump(world, f, indent=2)
    
    # Write event log as markdown history
    history_file = output_path / "history.md"
    with open(history_file, "w", encoding="utf-8") as f:
        current_tick = 0
        for event in world["event_log"]:
            if event["tick"] != current_tick:
                current_tick = event["tick"]
                f.write(f"\n## Tick {current_tick}\n\n")
            f.write(f"- {event.get('narrative') or event['description']}\n")

"""Simulation engine - tick-based evolution."""

import random
import copy
import json
from pathlib import Path
from worldsim.config import RUN_SEED, N_TICKS, YEARS_PER_TICK
from worldsim.seeds import get_initial_world, CULTURE_SEEDS
from worldsim.memory import create_empty_memory
from worldsim.chronicler import chronicle
from worldsim.dynamics import run_dynamics


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
        # runtime registry of culture seeds; grows as the Chronicler births new peoples
        "seeds": copy.deepcopy(CULTURE_SEEDS),
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
        world["year"] = run_state["tick"] * YEARS_PER_TICK

        seeds = run_state["seeds"]

        # The structural engine advances the world: carrying capacity, population,
        # the secular cycle, asabiyya, expansion/conquest, diffusion, shocks, and
        # the fracturing of overstrained realms into new peoples.
        struct_events, newborns = run_dynamics(world, seeds, memory)

        # The Chronicler names the newborn peoples and narrates the human texture.
        narration = chronicle(world, seeds, memory, struct_events, newborns)

        all_tick_events = struct_events + narration
        world["event_log"].extend(all_tick_events)

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

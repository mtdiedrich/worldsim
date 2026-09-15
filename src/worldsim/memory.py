"""Memory management for cultures."""

from worldsim.config import MEMORY_WINDOW


def create_empty_memory(culture_id: str) -> dict:
    """Create an empty memory structure for a culture."""
    return {
        "recent_events": [],
        "beliefs": "",
    }


def update_memory(memory: dict, events: list, beliefs: str = None) -> dict:
    """
    Update a culture's memory with new events and/or beliefs.
    
    Args:
        memory: The current memory dict
        events: List of event dicts to add
        beliefs: New beliefs string (if not None, replaces current)
        
    Returns:
        Updated memory dict
    """
    if beliefs is not None:
        memory["beliefs"] = beliefs
    
    # Add event descriptions to recent_events
    for event in events:
        memory["recent_events"].append(event.get("narrative") or event["description"])
    
    # Keep only the last MEMORY_WINDOW events
    memory["recent_events"] = memory["recent_events"][-MEMORY_WINDOW:]
    
    return memory

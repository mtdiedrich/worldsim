"""Tests for memory module."""

from worldsim.memory import create_empty_memory, update_memory
from worldsim.config import MEMORY_WINDOW


def test_create_empty_memory():
    """Test creating an empty memory structure."""
    memory = create_empty_memory("saltborn")
    
    assert "recent_events" in memory
    assert "beliefs" in memory
    assert memory["recent_events"] == []
    assert memory["beliefs"] == ""


def test_update_memory_with_beliefs():
    """Test updating memory with new beliefs."""
    memory = create_empty_memory("saltborn")
    new_beliefs = "We should expand"
    
    updated = update_memory(memory, events=[], beliefs=new_beliefs)
    
    assert updated["beliefs"] == new_beliefs


def test_update_memory_with_events():
    """Test updating memory with events."""
    memory = create_empty_memory("saltborn")
    
    events = [
        {"description": "Event 1", "involved": ["saltborn"]},
        {"description": "Event 2", "involved": ["saltborn"]},
    ]
    
    updated = update_memory(memory, events=events, beliefs=None)
    
    assert len(updated["recent_events"]) == 2
    assert updated["recent_events"][0] == "Event 1"
    assert updated["recent_events"][1] == "Event 2"


def test_update_memory_keeps_window():
    """Test that memory only keeps last MEMORY_WINDOW events."""
    memory = create_empty_memory("saltborn")
    
    # Add more than MEMORY_WINDOW events
    events = [
        {"description": f"Event {i}", "involved": ["saltborn"]}
        for i in range(MEMORY_WINDOW + 5)
    ]
    
    updated = update_memory(memory, events=events, beliefs=None)
    
    # Should only keep last MEMORY_WINDOW
    assert len(updated["recent_events"]) == MEMORY_WINDOW
    
    # Should be the last ones
    assert "Event 5" in updated["recent_events"]
    assert "Event 12" in updated["recent_events"]
    assert "Event 0" not in updated["recent_events"]


def test_update_memory_both_beliefs_and_events():
    """Test updating both beliefs and events at once."""
    memory = create_empty_memory("saltborn")
    
    events = [
        {"description": "Event 1", "involved": ["saltborn"]},
        {"description": "Event 2", "involved": ["saltborn"]},
    ]
    new_beliefs = "New worldview"
    
    updated = update_memory(memory, events=events, beliefs=new_beliefs)
    
    assert updated["beliefs"] == new_beliefs
    assert len(updated["recent_events"]) == 2
    assert updated["recent_events"][0] == "Event 1"


def test_update_memory_preserves_old_events():
    """Test that update_memory preserves old events up to window."""
    memory = create_empty_memory("saltborn")
    
    # First update with 3 events
    events1 = [
        {"description": "Event A", "involved": ["saltborn"]},
        {"description": "Event B", "involved": ["saltborn"]},
        {"description": "Event C", "involved": ["saltborn"]},
    ]
    memory = update_memory(memory, events=events1, beliefs=None)
    
    # Second update with 3 more events
    events2 = [
        {"description": "Event D", "involved": ["saltborn"]},
        {"description": "Event E", "involved": ["saltborn"]},
        {"description": "Event F", "involved": ["saltborn"]},
    ]
    memory = update_memory(memory, events=events2, beliefs=None)
    
    # Should have all 6 events (still within MEMORY_WINDOW of 8)
    assert len(memory["recent_events"]) == 6
    assert memory["recent_events"][0] == "Event A"
    assert memory["recent_events"][5] == "Event F"

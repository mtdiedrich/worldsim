"""Tests for economy module."""

import random
from worldsim.economy import apply_economy, maybe_random_event
from worldsim.seeds import get_initial_world


def _world_with_culture_food(food_saltborn, food_ashfolk):
    world = get_initial_world()
    world["tick"] = 1
    world["cultures"]["saltborn"]["resources"]["food"] = food_saltborn
    world["cultures"]["ashfolk"]["resources"]["food"] = food_ashfolk
    return world


def test_apply_economy_production():
    """Test that occupied regions yield resources each tick."""
    world = get_initial_world()
    world["tick"] = 1
    world["cultures"]["saltborn"]["resources"]["food"] = 0
    
    events = apply_economy(world)
    
    # Coast yields food: 9; saltborn's food should be 9 - consumption
    # population=1000, FOOD_PER_POP=100 → eats 10; starts with 0, gets +9 → deficit 1
    # So famine should fire
    assert any(e["type"] == "famine" for e in events)


def test_apply_economy_well_fed_growth():
    """Test population grows when well-fed."""
    world = get_initial_world()
    world["tick"] = 1
    world["cultures"]["saltborn"]["resources"]["food"] = 500
    world["cultures"]["saltborn"]["population"] = 2000  # large enough for growth >= 10
    initial_pop = world["cultures"]["saltborn"]["population"]
    
    events = apply_economy(world)
    
    # Population should have grown
    assert world["cultures"]["saltborn"]["population"] > initial_pop


def test_apply_economy_famine():
    """Test starvation fires when food is insufficient."""
    world = get_initial_world()
    world["tick"] = 1
    # Give zero food — region yield (9) will not cover food needs for pop 1000
    world["cultures"]["saltborn"]["resources"]["food"] = 0
    # Remove all regions from saltborn so no yield
    world["regions"]["coast"]["occupant"] = None
    initial_pop = world["cultures"]["saltborn"]["population"]
    
    events = apply_economy(world)
    
    # Should have a famine event
    assert any(e["type"] == "famine" for e in events)
    
    # Population should have decreased
    assert world["cultures"]["saltborn"]["population"] < initial_pop


def test_apply_economy_event_has_narrative():
    """Test that economy events have the narrative field."""
    world = get_initial_world()
    world["tick"] = 1
    # Force famine
    world["cultures"]["saltborn"]["resources"]["food"] = 0
    world["regions"]["coast"]["occupant"] = None
    
    events = apply_economy(world)
    
    for event in events:
        assert "narrative" in event
        assert "description" in event


def test_maybe_random_event_returns_events_or_empty():
    """Test that maybe_random_event returns a list (possibly empty)."""
    random.seed(42)
    world = get_initial_world()
    world["tick"] = 1
    
    result = maybe_random_event(world)
    
    assert isinstance(result, list)


def test_maybe_random_event_types():
    """Test that random events are of known types."""
    # Run many times to trigger events
    world = get_initial_world()
    world["tick"] = 1
    
    known_types = {"world_blight", "world_rich_vein", "world_plague", "world_windfall"}
    seen_types = set()
    
    random.seed(1)
    for _ in range(100):
        events = maybe_random_event(world)
        for e in events:
            seen_types.add(e["type"])
    
    # All seen types should be known
    assert seen_types.issubset(known_types)
    # Should have seen at least some events
    assert len(seen_types) > 0


def test_maybe_random_event_has_narrative():
    """Test that random events include the narrative field."""
    random.seed(5)  # Seed that reliably produces an event quickly
    world = get_initial_world()
    world["tick"] = 1
    
    # Force an event by trying multiple seeds
    for seed in range(20):
        random.seed(seed)
        events = maybe_random_event(world)
        if events:
            assert "narrative" in events[0]
            assert "description" in events[0]
            break

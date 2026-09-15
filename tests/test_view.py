"""Tests for view module."""

from worldsim.view import build_filtered_view
from worldsim.seeds import get_initial_world


def test_filtered_view_structure():
    """Test that filtered view has all required fields."""
    world = get_initial_world()
    view = build_filtered_view(world, "saltborn")
    
    required_fields = ["tick", "culture", "regions", "other_cultures", "recent_events"]
    for field in required_fields:
        assert field in view, f"Missing {field} in view"


def test_filtered_view_culture_info():
    """Test that culture sees its own full info."""
    world = get_initial_world()
    view = build_filtered_view(world, "saltborn")
    
    culture_view = view["culture"]
    assert culture_view["id"] == "saltborn"
    assert culture_view["name"] == "The Saltborn"
    assert culture_view["population"] == 1000
    assert "food" in culture_view["resources"]
    assert "ore" in culture_view["resources"]
    assert "wealth" in culture_view["resources"]
    assert "tech" in culture_view
    assert isinstance(culture_view["tech"], list)
    assert "relations" in culture_view


def test_filtered_view_sees_occupied_regions():
    """Test that culture sees regions it occupies."""
    world = get_initial_world()
    view = build_filtered_view(world, "saltborn")
    
    regions = view["regions"]
    assert "coast" in regions  # Saltborn occupies coast


def test_filtered_view_sees_adjacent_regions():
    """Test that culture sees adjacent regions."""
    world = get_initial_world()
    view = build_filtered_view(world, "saltborn")
    
    regions = view["regions"]
    assert "lowland" in regions  # Adjacent to coast


def test_filtered_view_asymmetry():
    """Test that filtered view is asymmetric - Saltborn doesn't see Ashfolk's resources."""
    world = get_initial_world()
    view = build_filtered_view(world, "saltborn")
    
    regions = view["regions"]
    # Ashfolk's home region (highland) is not adjacent to coast, so not visible
    assert "highland" not in regions


def test_filtered_view_other_cultures_limited_info():
    """Test that other cultures show only limited information."""
    world = get_initial_world()
    
    # Move Ashfolk to an adjacent region so they're visible
    world["regions"]["pass"]["occupant"] = "ashfolk"
    
    view = build_filtered_view(world, "saltborn")
    
    other_cultures = view["other_cultures"]
    
    if "ashfolk" in other_cultures:
        ashfolk_view = other_cultures["ashfolk"]
        
        # Should have name and home_region
        assert "name" in ashfolk_view
        assert "home_region" in ashfolk_view
        
        # Should have relations toward this culture
        assert "relations" in ashfolk_view
        
        # Should NOT have population, resources, tech
        assert "population" not in ashfolk_view
        assert "resources" not in ashfolk_view
        assert "tech" not in ashfolk_view


def test_filtered_view_recent_events():
    """Test that view includes recent events."""
    world = get_initial_world()
    
    # Add some events
    for i in range(10):
        world["event_log"].append({
            "tick": i,
            "type": "test",
            "description": f"Event {i}",
            "involved": ["saltborn"],
        })
    
    view = build_filtered_view(world, "saltborn")
    
    # Should only have last 5 events
    assert len(view["recent_events"]) == 5
    
    # Should be the last 5
    descriptions = [e["description"] for e in view["recent_events"]]
    assert "Event 5" in descriptions
    assert "Event 9" in descriptions


def test_filtered_view_tick():
    """Test that tick is in the view."""
    world = get_initial_world()
    world["tick"] = 5
    
    view = build_filtered_view(world, "saltborn")
    
    assert view["tick"] == 5

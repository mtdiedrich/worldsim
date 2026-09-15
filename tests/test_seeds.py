"""Tests for seeds module."""

from worldsim.seeds import CULTURE_SEEDS, INITIAL_WORLD, get_initial_world


def test_culture_seeds_exist():
    """Verify both cultures are defined."""
    assert len(CULTURE_SEEDS) == 2
    assert "saltborn" in CULTURE_SEEDS
    assert "ashfolk" in CULTURE_SEEDS


def test_culture_seed_structure():
    """Verify each culture seed has all required fields."""
    required_fields = [
        "id", "name", "values", "goals", "taboos", 
        "blind_spots", "false_beliefs", "founding_trauma"
    ]
    
    for culture_id, seed in CULTURE_SEEDS.items():
        for field in required_fields:
            assert field in seed, f"Missing {field} in {culture_id}"


def test_initial_world_structure():
    """Verify initial world has correct structure."""
    assert "tick" in INITIAL_WORLD
    assert "regions" in INITIAL_WORLD
    assert "cultures" in INITIAL_WORLD
    assert "event_log" in INITIAL_WORLD
    
    assert INITIAL_WORLD["tick"] == 0
    assert len(INITIAL_WORLD["event_log"]) == 0


def test_initial_world_regions():
    """Verify initial world has four regions."""
    regions = INITIAL_WORLD["regions"]
    assert len(regions) == 4
    
    expected_regions = ["coast", "lowland", "pass", "highland"]
    for region_name in expected_regions:
        assert region_name in regions


def test_initial_world_region_structure():
    """Verify each region has required fields."""
    required_fields = ["name", "terrain", "resources", "occupant", "adjacent"]
    
    for region_id, region in INITIAL_WORLD["regions"].items():
        for field in required_fields:
            assert field in region, f"Missing {field} in region {region_id}"
        
        # Check resources has all types
        for resource in ["food", "ore", "wealth"]:
            assert resource in region["resources"]


def test_initial_world_cultures():
    """Verify initial world has two cultures."""
    cultures = INITIAL_WORLD["cultures"]
    assert len(cultures) == 2
    assert "saltborn" in cultures
    assert "ashfolk" in cultures


def test_initial_world_culture_structure():
    """Verify each culture has required fields."""
    required_fields = [
        "name", "home_region", "population", "resources", "tech", "relations"
    ]
    
    for culture_id, culture in INITIAL_WORLD["cultures"].items():
        for field in required_fields:
            assert field in culture, f"Missing {field} in culture {culture_id}"
        
        # Check resources has all types
        for resource in ["food", "ore", "wealth"]:
            assert resource in culture["resources"]


def test_initial_world_adjacency():
    """Verify region adjacency is correct."""
    regions = INITIAL_WORLD["regions"]
    
    # coast should be adjacent to lowland
    assert "lowland" in regions["coast"]["adjacent"]
    
    # lowland should be adjacent to coast and pass
    assert "coast" in regions["lowland"]["adjacent"]
    assert "pass" in regions["lowland"]["adjacent"]
    
    # pass should be adjacent to lowland and highland
    assert "lowland" in regions["pass"]["adjacent"]
    assert "highland" in regions["pass"]["adjacent"]
    
    # highland should be adjacent to pass only
    assert "pass" in regions["highland"]["adjacent"]


def test_initial_world_occupancy():
    """Verify initial occupancy is correct."""
    regions = INITIAL_WORLD["regions"]
    
    # Saltborn occupies coast
    assert regions["coast"]["occupant"] == "saltborn"
    
    # Ashfolk occupies highland
    assert regions["highland"]["occupant"] == "ashfolk"
    
    # Lowland and pass are unoccupied
    assert regions["lowland"]["occupant"] is None
    assert regions["pass"]["occupant"] is None


def test_get_initial_world_returns_copy():
    """Verify get_initial_world returns a deep copy."""
    world1 = get_initial_world()
    world2 = get_initial_world()
    
    # They should have the same content
    assert world1["tick"] == world2["tick"]
    assert len(world1["regions"]) == len(world2["regions"])
    
    # But they should be different objects
    assert world1 is not world2
    assert world1["regions"] is not world2["regions"]
    
    # Modifying one should not affect the other
    world1["tick"] = 99
    assert world2["tick"] == 0

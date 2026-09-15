"""Tests for arbiter module."""

import random
from worldsim.arbiter import resolve, strength, roll
from worldsim.seeds import get_initial_world
from worldsim.config import MIN_RELATION, MAX_RELATION


def test_strength_calculation():
    """Test culture strength calculation."""
    culture = {
        "population": 1000,
        "tech": ["tech1", "tech2"],
    }
    
    # strength = population/100 + 2*tech_count = 1000/100 + 2*2 = 10 + 4 = 14
    assert strength(culture) == 14.0


def test_roll_range():
    """Test that dice rolls are in the correct range."""
    random.seed(42)
    
    for _ in range(100):
        r = roll()
        assert 0.6 <= r <= 1.4


def test_resolve_hold_no_change():
    """Test that hold action causes no change."""
    world = get_initial_world()
    original_pop = world["cultures"]["saltborn"]["population"]
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    assert new_world["cultures"]["saltborn"]["population"] == original_pop
    assert len(events) == 0


def test_resolve_innovate_success():
    """Test successful innovation."""
    random.seed(42)
    world = get_initial_world()
    world["cultures"]["saltborn"]["resources"]["ore"] = 10
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "innovate", "target": None, "amount": 0, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Ore should be reduced by 5
    assert new_world["cultures"]["saltborn"]["resources"]["ore"] == 5
    
    # Should have an event
    assert len(events) > 0
    
    # Check if tech was added (depends on random roll)
    if any(e["type"] == "innovate_success" for e in events):
        assert len(new_world["cultures"]["saltborn"]["tech"]) > 0


def test_resolve_innovate_insufficient_ore():
    """Test innovation fails with insufficient ore."""
    world = get_initial_world()
    world["cultures"]["saltborn"]["resources"]["ore"] = 2  # Less than 5
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "innovate", "target": None, "amount": 0, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Ore should not change
    assert new_world["cultures"]["saltborn"]["resources"]["ore"] == 2
    
    # Should have a failure event
    assert len(events) > 0
    assert any("lacked ore" in e["description"] for e in events)


def test_resolve_build():
    """Test building improvement."""
    world = get_initial_world()
    world["cultures"]["saltborn"]["resources"]["wealth"] = 100
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "build", "target": None, "amount": 60, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Wealth should be reduced by 60
    assert new_world["cultures"]["saltborn"]["resources"]["wealth"] == 40
    
    # Food in home region should be increased by 60//2 = 30
    assert new_world["regions"]["coast"]["resources"]["food"] == (300 + 30)


def test_resolve_trade_mutual():
    """Test mutual trade between cultures."""
    random.seed(42)
    world = get_initial_world()
    world["cultures"]["saltborn"]["resources"]["wealth"] = 100
    world["cultures"]["ashfolk"]["resources"]["wealth"] = 50
    initial_salt_wealth = world["cultures"]["saltborn"]["resources"]["wealth"]
    initial_ash_wealth = world["cultures"]["ashfolk"]["resources"]["wealth"]
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "trade", "target": "ashfolk", "amount": 40, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "trade", "target": "saltborn", "amount": 30, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Wealth should be swapped
    salt_wealth = new_world["cultures"]["saltborn"]["resources"]["wealth"]
    ash_wealth = new_world["cultures"]["ashfolk"]["resources"]["wealth"]
    
    # Saltborn: lost 40, gained 30 = 100 - 40 + 30 = 90
    assert salt_wealth == 90
    
    # Ashfolk: lost 30, gained 40 = 50 - 30 + 40 = 60
    assert ash_wealth == 60
    
    # Relations should improve by 8
    assert new_world["cultures"]["saltborn"]["relations"]["ashfolk"] == 8
    assert new_world["cultures"]["ashfolk"]["relations"]["saltborn"] == 8
    
    # Should have a trade event
    assert any(e["type"] == "trade_mutual" for e in events)


def test_resolve_trade_one_sided():
    """Test one-sided trade offer."""
    world = get_initial_world()
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "trade", "target": "ashfolk", "amount": 40, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Relations should improve by 2 for one-sided
    assert new_world["cultures"]["saltborn"]["relations"]["ashfolk"] == 2
    
    # Should have an overture event
    assert any(e["type"] == "trade_overture" for e in events)


def test_resolve_attack_attacker_wins():
    """Test attack where attacker has advantage."""
    random.seed(99)  # Seed for controlled rolls
    world = get_initial_world()
    
    # Give Saltborn much stronger position
    world["cultures"]["saltborn"]["population"] = 2000
    world["cultures"]["saltborn"]["tech"] = ["tech1", "tech2", "tech3"]
    
    # Move Ashfolk to adjacent region
    world["regions"]["lowland"]["occupant"] = "ashfolk"
    world["regions"]["highland"]["occupant"] = None
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "attack", "target": "ashfolk", "amount": 0, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Should have casualties (15% of Ashfolk population)
    ash_pop = new_world["cultures"]["ashfolk"]["population"]
    assert ash_pop < 1000
    
    # Attacker gains wealth
    salt_wealth = new_world["cultures"]["saltborn"]["resources"]["wealth"]
    assert salt_wealth == 120  # +20


def test_resolve_migrate():
    """Test settling an adjacent empty region (v2: claim with flat food cost, no pop movement)."""
    world = get_initial_world()
    initial_pop = world["cultures"]["saltborn"]["population"]
    initial_food = world["cultures"]["saltborn"]["resources"]["food"]
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "migrate", "target": "lowland", "amount": 200, "note": "expand"}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Population unchanged (v2: migration no longer moves population)
    assert new_world["cultures"]["saltborn"]["population"] == initial_pop
    
    # Lowland occupied by Saltborn
    assert new_world["regions"]["lowland"]["occupant"] == "saltborn"
    
    # Food cost: flat 5
    assert new_world["cultures"]["saltborn"]["resources"]["food"] == (initial_food - 5)


def test_resolve_relations_clamped():
    """Test that relations are clamped to [-100, 100]."""
    world = get_initial_world()
    
    # Manually set relations beyond bounds
    world["cultures"]["saltborn"]["relations"]["ashfolk"] = 200
    world["cultures"]["ashfolk"]["relations"]["saltborn"] = -200
    
    actions = [
        {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
        {
            "culture_id": "ashfolk",
            "beliefs": "test",
            "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}],
        },
    ]
    
    new_world, events = resolve(world, actions)
    
    # Relations should be clamped
    assert new_world["cultures"]["saltborn"]["relations"]["ashfolk"] == MAX_RELATION
    assert new_world["cultures"]["ashfolk"]["relations"]["saltborn"] == MIN_RELATION

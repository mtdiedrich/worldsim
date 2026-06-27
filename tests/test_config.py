"""Tests for config module."""

from worldsim.config import (
    MODEL, MAX_RETRIES, N_TICKS, RUN_SEED, RESOURCES, 
    ACTION_TYPES, MIN_RELATION, MAX_RELATION, MEMORY_WINDOW
)


def test_config_constants_exist():
    """Verify all required config constants are defined."""
    assert MODEL is not None
    assert MAX_RETRIES >= 0
    assert N_TICKS > 0
    assert RUN_SEED >= 0
    assert len(RESOURCES) == 3
    assert "food" in RESOURCES
    assert "ore" in RESOURCES
    assert "wealth" in RESOURCES


def test_config_action_types():
    """Verify all action types are defined."""
    expected_types = ["trade", "migrate", "attack", "innovate", "build", "diplomacy", "hold"]
    assert len(ACTION_TYPES) == len(expected_types)
    for action_type in expected_types:
        assert action_type in ACTION_TYPES


def test_config_relations():
    """Verify relation bounds are correct."""
    assert MIN_RELATION == -100
    assert MAX_RELATION == 100


def test_config_memory():
    """Verify memory configuration."""
    assert MEMORY_WINDOW == 8

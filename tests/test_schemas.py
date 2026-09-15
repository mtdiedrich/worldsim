"""Tests for schemas module."""

from worldsim.schemas import validate_action, make_fallback_action


def test_validate_action_valid_basic():
    """Test validation of a basic valid action."""
    action = {
        "culture_id": "saltborn",
        "beliefs": "We should trade",
        "actions": [
            {"type": "trade", "target": "ashfolk", "amount": 50, "note": "friendly trade"}
        ]
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert is_valid
    assert error == ""


def test_validate_action_culture_id_mismatch():
    """Test validation fails on culture_id mismatch."""
    action = {
        "culture_id": "saltborn",
        "beliefs": "test",
        "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}]
    }
    
    is_valid, error = validate_action(action, "ashfolk")
    assert not is_valid
    assert "mismatch" in error


def test_validate_action_truncates_beliefs():
    """Test that long beliefs are truncated."""
    long_beliefs = "x" * 1000
    action = {
        "culture_id": "saltborn",
        "beliefs": long_beliefs,
        "actions": [{"type": "hold", "target": None, "amount": 0, "note": ""}]
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert is_valid
    assert len(action["beliefs"]) == 600  # Truncated to MAX_BELIEFS_CHARS


def test_validate_action_empty_actions_becomes_hold():
    """Test that empty actions becomes a single hold action."""
    action = {
        "culture_id": "saltborn",
        "beliefs": "test",
        "actions": []
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert is_valid
    assert len(action["actions"]) == 1
    assert action["actions"][0]["type"] == "hold"


def test_validate_action_missing_actions_becomes_hold():
    """Test that missing actions becomes a single hold action."""
    action = {
        "culture_id": "saltborn",
        "beliefs": "test",
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert is_valid
    assert len(action["actions"]) == 1
    assert action["actions"][0]["type"] == "hold"


def test_validate_action_too_many_actions():
    """Test validation fails for > 3 actions."""
    action = {
        "culture_id": "saltborn",
        "beliefs": "test",
        "actions": [
            {"type": "hold", "target": None, "amount": 0, "note": ""},
            {"type": "hold", "target": None, "amount": 0, "note": ""},
            {"type": "hold", "target": None, "amount": 0, "note": ""},
            {"type": "hold", "target": None, "amount": 0, "note": ""},
        ]
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert not is_valid
    assert "1-3" in error


def test_validate_action_invalid_type():
    """Test validation fails for invalid action type."""
    action = {
        "culture_id": "saltborn",
        "beliefs": "test",
        "actions": [
            {"type": "invalid_action", "target": None, "amount": 0, "note": ""}
        ]
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert not is_valid
    assert "invalid type" in error


def test_validate_action_negative_amount():
    """Test validation fails for negative amount."""
    action = {
        "culture_id": "saltborn",
        "beliefs": "test",
        "actions": [
            {"type": "trade", "target": "ashfolk", "amount": -5, "note": ""}
        ]
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert not is_valid
    assert "non-negative" in error


def test_validate_action_truncates_note():
    """Test that long notes are truncated."""
    long_note = "x" * 200
    action = {
        "culture_id": "saltborn",
        "beliefs": "test",
        "actions": [
            {"type": "trade", "target": "ashfolk", "amount": 50, "note": long_note}
        ]
    }
    
    is_valid, error = validate_action(action, "saltborn")
    assert is_valid
    assert len(action["actions"][0]["note"]) == 120  # Truncated to MAX_NOTE_CHARS


def test_validate_action_all_valid_types():
    """Test validation accepts all valid action types."""
    valid_types = ["trade", "migrate", "attack", "innovate", "build", "diplomacy", "hold"]
    
    for action_type in valid_types:
        action = {
            "culture_id": "saltborn",
            "beliefs": "test",
            "actions": [
                {"type": action_type, "target": "target", "amount": 10, "note": "test"}
            ]
        }
        is_valid, error = validate_action(action, "saltborn")
        assert is_valid, f"Failed for type {action_type}: {error}"


def test_make_fallback_action():
    """Test fallback action creation."""
    fallback = make_fallback_action("saltborn", "old beliefs")
    
    assert fallback["culture_id"] == "saltborn"
    assert fallback["beliefs"] == "old beliefs"
    assert len(fallback["actions"]) == 1
    assert fallback["actions"][0]["type"] == "hold"
    assert fallback["actions"][0]["target"] is None
    assert fallback["actions"][0]["amount"] == 0
    assert fallback["actions"][0]["note"] == "fallback"

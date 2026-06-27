"""Validation schemas for actions."""

from worldsim.config import ACTION_TYPES, MAX_BELIEFS_CHARS, MAX_NOTE_CHARS


def validate_action(obj: dict, expected_culture_id: str) -> tuple[bool, str]:
    """
    Validate an action object returned by the agent.
    
    Args:
        obj: The action object to validate
        expected_culture_id: The expected culture_id
        
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(obj, dict):
        return False, "Action must be a dict"

    # Check culture_id
    if obj.get("culture_id") != expected_culture_id:
        return False, f"culture_id mismatch: expected {expected_culture_id}"

    # Check beliefs (truncate if too long)
    beliefs = obj.get("beliefs", "")
    if not isinstance(beliefs, str):
        return False, "beliefs must be a string"
    if len(beliefs) > MAX_BELIEFS_CHARS:
        obj["beliefs"] = beliefs[:MAX_BELIEFS_CHARS]

    # Check actions list
    actions = obj.get("actions", [])
    if not isinstance(actions, list):
        return False, "actions must be a list"
    
    if len(actions) == 0:
        # Empty actions becomes one 'hold'
        obj["actions"] = [
            {"type": "hold", "target": None, "amount": 0, "note": ""}
        ]
        return True, ""
    
    if len(actions) > 3:
        return False, f"actions must have 1-3 items, got {len(actions)}"

    # Validate each action
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            return False, f"action {i} must be a dict"

        # Check type
        action_type = action.get("type")
        if action_type not in ACTION_TYPES:
            return False, f"action {i}: invalid type '{action_type}'"

        # Check target (string or null)
        target = action.get("target")
        if target is not None and not isinstance(target, str):
            return False, f"action {i}: target must be string or null"

        # Check amount (integer >= 0)
        amount = action.get("amount", 0)
        if not isinstance(amount, int) or amount < 0:
            return False, f"action {i}: amount must be non-negative integer"

        # Check note (string, <= MAX_NOTE_CHARS)
        note = action.get("note", "")
        if not isinstance(note, str):
            return False, f"action {i}: note must be string"
        if len(note) > MAX_NOTE_CHARS:
            action["note"] = note[:MAX_NOTE_CHARS]

    return True, ""


def make_fallback_action(culture_id: str, beliefs: str) -> dict:
    """
    Create a fallback 'hold' action when LLM response is invalid.
    
    Args:
        culture_id: The culture's ID
        beliefs: The current beliefs string
        
    Returns:
        A valid hold action
    """
    return {
        "culture_id": culture_id,
        "beliefs": beliefs,
        "actions": [
            {
                "type": "hold",
                "target": None,
                "amount": 0,
                "note": "fallback",
            }
        ],
    }

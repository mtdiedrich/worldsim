"""Agent execution."""

import json
import time
import logging
from worldsim.llm import call_llm
from worldsim.prompts import AGENT_SYSTEM_TEMPLATE, AGENT_USER_TEMPLATE
from worldsim.schemas import validate_action, make_fallback_action
from worldsim.config import MAX_RETRIES

logger = logging.getLogger(__name__)


def run_agent(seed: dict, memory: dict, filtered_view: dict) -> dict:
    """
    Run one culture's agent for one tick.
    
    Args:
        seed: Culture seed (from CULTURE_SEEDS)
        memory: Culture's current memory
        filtered_view: Filtered world view for this culture
        
    Returns:
        Validated action dict, or fallback hold action on failure
    """
    culture_id = seed["id"]
    
    # Build system prompt
    system_prompt = AGENT_SYSTEM_TEMPLATE.format(
        id=seed["id"],
        name=seed["name"],
        values=seed["values"],
        goals=", ".join(seed["goals"]),
        taboos=", ".join(seed["taboos"]),
        blind_spots=", ".join(seed["blind_spots"]),
        false_beliefs=", ".join(seed["false_beliefs"]),
        founding_trauma=seed["founding_trauma"],
    )
    
    # Build user prompt
    recent_events_str = (
        "\n".join(memory.get("recent_events", []))
        if memory.get("recent_events")
        else "(no recent events)"
    )
    
    user_prompt = AGENT_USER_TEMPLATE.format(
        tick=filtered_view["tick"],
        year=filtered_view.get("year", filtered_view["tick"]),
        filtered_view_json=json.dumps(filtered_view, indent=2),
        recent_events=recent_events_str,
        beliefs=memory.get("beliefs", "(no standing beliefs)"),
        name_hint=seed["name"],
    )
    
    # Try to get a valid action from the LLM
    for attempt in range(MAX_RETRIES + 1):
        try:
            # Call the LLM
            response_text = call_llm(system_prompt, user_prompt)
            
            # Strip whitespace and remove markdown fences if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            action = json.loads(response_text)
            
            # Validate
            is_valid, error_msg = validate_action(action, culture_id)
            if is_valid:
                return action
            
            # Invalid response - retry if we have attempts left
            if attempt < MAX_RETRIES:
                retry_user_prompt = (
                    f"Your previous output was invalid: {error_msg}. "
                    f"Output ONLY the JSON object.\n\n" + user_prompt
                )
                user_prompt = retry_user_prompt
            else:
                # Out of retries - log and use fallback
                logger.error(
                    f"Agent {culture_id} failed validation after {MAX_RETRIES} retries: {error_msg}"
                )
                return make_fallback_action(culture_id, memory.get("beliefs", ""))
        
        except (json.JSONDecodeError, ValueError) as e:
            # JSON parsing error - retry if we have attempts left
            if attempt < MAX_RETRIES:
                retry_user_prompt = (
                    f"Your previous output was invalid: {str(e)}. "
                    f"Output ONLY the JSON object.\n\n" + user_prompt
                )
                user_prompt = retry_user_prompt
            else:
                # Out of retries - log and use fallback
                logger.error(
                    f"Agent {culture_id} produced invalid JSON after {MAX_RETRIES} retries: {str(e)}"
                )
                return make_fallback_action(culture_id, memory.get("beliefs", ""))
        
        except Exception as e:
            # API error or other issue - retry with short delay
            if attempt < MAX_RETRIES:
                logger.warning(f"Agent {culture_id} API call failed (attempt {attempt + 1}): {str(e)}")
                time.sleep(2)
            else:
                logger.error(f"Agent {culture_id} failed after {MAX_RETRIES} retries: {str(e)}")
                return make_fallback_action(culture_id, memory.get("beliefs", ""))
    
    # Fallback (should not reach here, but just in case)
    return make_fallback_action(culture_id, memory.get("beliefs", ""))

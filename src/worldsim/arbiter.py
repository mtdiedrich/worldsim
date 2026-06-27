"""Deterministic action resolution."""

import random
import copy
from worldsim.config import MIN_RELATION, MAX_RELATION


def roll() -> float:
    """Roll dice for combat/events. Returns value between 0.6 and 1.4."""
    return random.uniform(0.6, 1.4)


def strength(culture: dict) -> float:
    """Calculate culture strength: population/100 + 2*tech_count."""
    return culture["population"] / 100.0 + 2.0 * len(culture["tech"])


def make_event(world: dict, ev_type: str, mechanical: str, involved: list, reason: str = "") -> dict:
    """Build an event. `narrative` = mechanical text + the agent's stated reason."""
    narrative = mechanical if not reason else f'{mechanical} — "{reason}"'
    return {
        "tick": world["tick"],
        "type": ev_type,
        "description": mechanical,
        "narrative": narrative,
        "involved": involved,
        "reason": reason,
    }


def resolve(world: dict, actions: list) -> tuple[dict, list]:
    """
    Resolve all actions for a tick into world state changes.
    
    Args:
        world: Current world state
        actions: List of validated action dicts
        
    Returns:
        (new_world, events) tuple
    """
    # Deep copy the world so we don't mutate the original
    new_world = copy.deepcopy(world)
    events = []
    
    # Group actions by type for deterministic processing order
    action_type_order = ["attack", "migrate", "trade", "diplomacy", "build", "innovate", "hold"]
    
    # Collect actions by type
    actions_by_type = {action_type: [] for action_type in action_type_order}
    for action in actions:
        for sub_action in action["actions"]:
            action_type = sub_action["type"]
            actions_by_type[action_type].append({
                "culture_id": action["culture_id"],
                "type": action_type,
                "target": sub_action.get("target"),
                "amount": sub_action.get("amount", 0),
                "note": sub_action.get("note", ""),
            })
    
    # Track processed mutual actions to avoid double-processing
    processed_trades = set()
    processed_diplomacy = set()
    
    # Process actions in type order, within type by sorted culture_id
    for action_type in action_type_order:
        type_actions = sorted(
            actions_by_type[action_type],
            key=lambda a: a["culture_id"]
        )
        
        for action in type_actions:
            if action_type == "hold":
                _resolve_hold(new_world, action, events)
            elif action_type == "innovate":
                _resolve_innovate(new_world, action, events)
            elif action_type == "build":
                _resolve_build(new_world, action, events)
            elif action_type == "trade":
                _resolve_trade(new_world, action, events, type_actions, processed_trades)
            elif action_type == "diplomacy":
                _resolve_diplomacy(new_world, action, events, type_actions, processed_diplomacy)
            elif action_type == "migrate":
                _resolve_migrate(new_world, action, events)
            elif action_type == "attack":
                _resolve_attack(new_world, action, events)
    
    # Clamp all relations to [MIN_RELATION, MAX_RELATION]
    for culture in new_world["cultures"].values():
        for other_id in culture["relations"]:
            culture["relations"][other_id] = max(
                MIN_RELATION, min(MAX_RELATION, culture["relations"][other_id])
            )
    
    # Clamp populations >= 0 and resources >= 0
    for culture in new_world["cultures"].values():
        culture["population"] = max(0, culture["population"])
        for resource in culture["resources"]:
            culture["resources"][resource] = max(0, culture["resources"][resource])
    
    for region in new_world["regions"].values():
        for resource in region["resources"]:
            region["resources"][resource] = max(0, region["resources"][resource])
    
    return new_world, events


def _resolve_hold(world: dict, action: dict, events: list) -> None:
    """Hold action - no change, no event."""
    pass


def _resolve_innovate(world: dict, action: dict, events: list) -> None:
    """Innovate: cost 5 ore, 40% success chance, generates tech."""
    culture_id = action["culture_id"]
    culture = world["cultures"][culture_id]
    
    if culture["resources"]["ore"] < 5:
        events.append(make_event(
            world, "innovate_failed",
            f"{culture['name']} tried to innovate, lacked ore.",
            [culture_id], reason=action["note"],
        ))
        return
    
    # Subtract ore cost
    culture["resources"]["ore"] -= 5
    
    # Roll for success
    if random.random() < 0.4:
        # Success
        tech_token = f"tech_{world['tick']}_{culture_id}"
        culture["tech"].append(tech_token)
        events.append(make_event(
            world, "innovate_success",
            f"{culture['name']} successfully innovated: {tech_token}.",
            [culture_id], reason=action["note"],
        ))
    else:
        # Failure
        events.append(make_event(
            world, "innovate_failed",
            f"{culture['name']}'s research stalled.",
            [culture_id], reason=action["note"],
        ))


def _resolve_build(world: dict, action: dict, events: list) -> None:
    """Build: spend wealth to improve food in home region."""
    culture_id = action["culture_id"]
    culture = world["cultures"][culture_id]
    home_region_id = culture["home_region"]
    home_region = world["regions"][home_region_id]
    
    # Amount capped at available wealth
    amount = min(action["amount"], culture["resources"]["wealth"])
    
    if amount == 0:
        return
    
    # Subtract wealth
    culture["resources"]["wealth"] -= amount
    
    # Add half the amount as food improvement
    improvement = amount // 2
    home_region["resources"]["food"] += improvement
    
    events.append(make_event(
        world, "build",
        f"{culture['name']} spent {amount} wealth to improve {home_region['name']}, adding {improvement} food.",
        [culture_id], reason=action["note"],
    ))


def _resolve_trade(world: dict, action: dict, events: list, all_trade_actions: list, processed_trades: set) -> None:
    """Trade: mutual wealth exchange with relation boost."""
    culture_id = action["culture_id"]
    target_id = action["target"]
    amount = action["amount"]
    
    if not target_id or target_id not in world["cultures"]:
        return  # Invalid target, ignored
    
    if target_id == culture_id:
        return  # Can't trade with yourself
    
    # Check if this trade pair has already been processed
    trade_pair = tuple(sorted([culture_id, target_id]))
    if trade_pair in processed_trades:
        return
    
    culture = world["cultures"][culture_id]
    target = world["cultures"][target_id]
    
    # Check if target also issued a trade targeting us
    mutual_trade = None
    for other_action in all_trade_actions:
        if (other_action["culture_id"] == target_id and 
            other_action["target"] == culture_id):
            mutual_trade = other_action
            break
    
    if mutual_trade:
        # Mark this trade pair as processed
        processed_trades.add(trade_pair)
        
        # Mutual trade - exchange wealth
        our_offer = min(amount, culture["resources"]["wealth"])
        their_offer = min(mutual_trade["amount"], target["resources"]["wealth"])
        
        culture["resources"]["wealth"] -= our_offer
        target["resources"]["wealth"] -= their_offer
        
        culture["resources"]["wealth"] += their_offer
        target["resources"]["wealth"] += our_offer
        
        # Boost relations
        culture["relations"][target_id] += 8
        target["relations"][culture_id] += 8
        
        events.append(make_event(
            world, "trade_mutual",
            f"{culture['name']} and {target['name']} traded; each exchanged wealth. Relations improved.",
            [culture_id, target_id], reason=action["note"],
        ))
    else:
        # One-sided trade offer - goodwill only
        culture["relations"][target_id] += 2
        # Passive warming: target also notices the overture
        if culture_id in world["cultures"][target_id]["relations"]:
            world["cultures"][target_id]["relations"][culture_id] += 1
        
        events.append(make_event(
            world, "trade_overture",
            f"{culture['name']} offered to trade with {target['name']}, but the offer was ignored.",
            [culture_id, target_id], reason=action["note"],
        ))


def _resolve_diplomacy(world: dict, action: dict, events: list, all_diplomacy_actions: list, processed_diplomacy: set) -> None:
    """Diplomacy: mutual relation boost, one-sided smaller boost."""
    culture_id = action["culture_id"]
    target_id = action["target"]
    
    if not target_id or target_id not in world["cultures"]:
        return  # Invalid target
    
    if target_id == culture_id:
        return  # Can't diplomacy with yourself
    
    # Check if this diplomacy pair has already been processed
    diplomacy_pair = tuple(sorted([culture_id, target_id]))
    if diplomacy_pair in processed_diplomacy:
        return
    
    culture = world["cultures"][culture_id]
    target = world["cultures"][target_id]
    
    # Check if target also issued diplomacy targeting us
    mutual_diplomacy = None
    for other_action in all_diplomacy_actions:
        if (other_action["culture_id"] == target_id and 
            other_action["target"] == culture_id):
            mutual_diplomacy = other_action
            break
    
    if mutual_diplomacy:
        # Mark this diplomacy pair as processed
        processed_diplomacy.add(diplomacy_pair)
        
        # Mutual diplomacy
        culture["relations"][target_id] += 15
        target["relations"][culture_id] += 15
        
        events.append(make_event(
            world, "diplomacy_mutual",
            f"{culture['name']} and {target['name']} engaged in mutual diplomacy. Relations improved significantly.",
            [culture_id, target_id], reason=action["note"],
        ))
    else:
        # One-sided diplomacy
        culture["relations"][target_id] += 5
        # Passive warming: target also notices the gesture
        if culture_id in world["cultures"][target_id]["relations"]:
            world["cultures"][target_id]["relations"][culture_id] += 2
        
        events.append(make_event(
            world, "diplomacy_one_sided",
            f"{culture['name']} reached out diplomatically to {target['name']}.",
            [culture_id, target_id], reason=action["note"],
        ))


def _resolve_migrate(world: dict, action: dict, events: list) -> None:
    """Migrate: move population to adjacent or home region."""
    culture_id = action["culture_id"]
    target_region_id = action["target"]
    amount = action["amount"]
    
    if not target_region_id or target_region_id not in world["regions"]:
        return  # Invalid target region
    
    culture = world["cultures"][culture_id]
    home_region_id = culture["home_region"]
    home_region = world["regions"][home_region_id]
    target_region = world["regions"][target_region_id]
    
    # Check if target is adjacent or the home region
    is_valid_target = (
        target_region_id == home_region_id or
        target_region_id in home_region["adjacent"]
    )
    
    if not is_valid_target:
        events.append(make_event(
            world, "migrate_invalid",
            f"{culture['name']} could not migrate to {target_region['name']}: not adjacent.",
            [culture_id], reason=action["note"],
        ))
        return
    
    # Check if target is occupied by another culture
    if target_region["occupant"] and target_region["occupant"] != culture_id:
        events.append(make_event(
            world, "migrate_blocked",
            f"{culture['name']} was blocked at the border by {world['cultures'][target_region['occupant']]['name']}.",
            [culture_id, target_region["occupant"]], reason=action["note"],
        ))
        return
    
    # Claim the region. No population is moved; occupying it grants its yield from now on.
    SETTLE_FOOD_COST = 5
    if culture["resources"]["food"] < SETTLE_FOOD_COST:
        events.append(make_event(
            world, "migrate_failed",
            f"{culture['name']} lacked the food to settle {target_region['name']}.",
            [culture_id], reason=action["note"],
        ))
        return
    culture["resources"]["food"] -= SETTLE_FOOD_COST
    target_region["occupant"] = culture_id
    events.append(make_event(
        world, "migrate",
        f"{culture['name']} settled {target_region['name']}, claiming its yield.",
        [culture_id], reason=action["note"],
    ))


def _resolve_attack(world: dict, action: dict, events: list) -> None:
    """Attack: combat between cultures."""
    attacker_id = action["culture_id"]
    defender_id = action["target"]
    
    if not defender_id or defender_id not in world["cultures"]:
        return  # Invalid target
    
    if defender_id == attacker_id:
        return  # Can't attack yourself
    
    attacker = world["cultures"][attacker_id]
    defender = world["cultures"][defender_id]
    
    # Find defender's region (must be adjacent to attacker)
    defender_region = None
    for region_id, region in world["regions"].items():
        if region["occupant"] == defender_id:
            # Check if adjacent to any attacker-occupied region
            for att_region_id, att_region in world["regions"].items():
                if att_region["occupant"] == attacker_id:
                    if region_id in att_region["adjacent"]:
                        defender_region = region_id
                        break
            if defender_region:
                break
    
    if not defender_region:
        events.append(make_event(
            world, "attack_out_of_range",
            f"{attacker['name']} could not reach {defender['name']} in combat.",
            [attacker_id, defender_id], reason=action["note"],
        ))
        return
    
    # Calculate strengths
    att_strength = strength(attacker)
    def_strength = strength(defender)
    
    # Roll dice
    att_roll = roll()
    def_roll = roll()
    
    att_total = att_strength * att_roll
    def_total = def_strength * def_roll
    
    if att_total > def_total:
        # Attacker wins
        casualties = round(defender["population"] * 0.15)
        defender["population"] -= casualties
        attacker["resources"]["wealth"] += 20
        
        attacker["relations"][defender_id] -= 30
        defender["relations"][attacker_id] -= 30
        
        # Seize the contested region
        world["regions"][defender_region]["occupant"] = attacker_id
        seized_name = world["regions"][defender_region]["name"]
        
        events.append(make_event(
            world, "attack_success",
            f"{attacker['name']} raided {defender['name']}; rolled {att_total:.2f} vs {def_total:.2f}; "
            f"{defender['name']} lost {casualties} people and {seized_name} fell to {attacker['name']}.",
            [attacker_id, defender_id], reason=action["note"],
        ))
    else:
        # Defender wins or tied
        casualties = round(attacker["population"] * 0.10)
        attacker["population"] -= casualties
        
        attacker["relations"][defender_id] -= 30
        defender["relations"][attacker_id] -= 30
        
        events.append(make_event(
            world, "attack_failure",
            f"{attacker['name']} attacked {defender['name']}; rolled {att_total:.2f} vs {def_total:.2f}; {attacker['name']} lost {casualties} people.",
            [attacker_id, defender_id], reason=action["note"],
        ))

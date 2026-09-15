"""Deterministic action resolution."""

import random
import copy
from worldsim.config import (
    MIN_RELATION, MAX_RELATION, SETTLE_FOOD_COST, FOUND_WEALTH_COST, SUBJUGATE_STRENGTH_RATIO,
)


def roll() -> float:
    """Roll dice for combat/events. Returns value between 0.6 and 1.4."""
    return random.uniform(0.6, 1.4)


def _region_count(world: dict, culture_id: str) -> int:
    return sum(1 for r in world["regions"].values() if r["occupant"] == culture_id)


def strength(culture: dict, world: dict) -> float:
    """Military strength: population (in thousands) + tech + territory.

    Population dominates, but veteran tech and a broad territorial base both
    matter at the margin, so a small advanced empire can punch above its size.
    """
    cid = next((k for k, v in world["cultures"].items() if v is culture), None)
    regions = _region_count(world, cid) if cid else 1
    return culture["population"] / 1000.0 + 3.0 * len(culture["tech"]) + 2.0 * regions


def reachable_regions(world: dict, culture_id: str) -> set:
    """Regions a culture can act into: held + land-adjacent, plus (if sea-capable
    and holding a coast) any coastal region — overseas reach like Normandy's."""
    regions = world["regions"]
    held = [rid for rid, r in regions.items() if r["occupant"] == culture_id]
    reach = set(held)
    for rid in held:
        reach.update(regions[rid].get("adjacent", []))
    culture = world["cultures"].get(culture_id, {})
    if "sea" in culture.get("reach", ["land"]) and any(regions[rid].get("coastal") for rid in held):
        reach.update(rid for rid, r in regions.items() if r.get("coastal"))
    return reach


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
    action_type_order = ["attack", "subjugate", "migrate", "trade", "marry",
                         "diplomacy", "build", "innovate", "found", "hold"]
    
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
    processed_marriages = set()
    
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
            elif action_type == "found":
                _resolve_found(new_world, action, events)
            elif action_type == "subjugate":
                _resolve_subjugate(new_world, action, events)
            elif action_type == "marry":
                _resolve_marry(new_world, action, events, type_actions, processed_marriages)
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
    
    INNOVATE_ORE_COST = 40
    name = (action.get("name") or action.get("note") or "a new art").strip()[:80]
    desc = (action.get("note") or "").strip()

    if culture["resources"]["ore"] < INNOVATE_ORE_COST:
        events.append(make_event(
            world, "innovate_failed",
            f"{culture['name']} sought to develop {name} but lacked the ore to fund the work.",
            [culture_id], reason=desc,
        ))
        return

    culture["resources"]["ore"] -= INNOVATE_ORE_COST

    # Roll for success. A real, named advance is recorded on success.
    if random.random() < 0.45:
        culture["tech"].append({"name": name, "description": desc, "tick": world["tick"]})
        events.append(make_event(
            world, "innovate_success",
            f"{culture['name']} mastered {name}.",
            [culture_id], reason=desc,
        ))
    else:
        events.append(make_event(
            world, "innovate_failed",
            f"{culture['name']}'s pursuit of {name} came to nothing this generation.",
            [culture_id], reason=desc,
        ))


def _resolve_found(world: dict, action: dict, events: list) -> None:
    """Found a lasting institution, festival, cult, or law — authored by the culture."""
    culture_id = action["culture_id"]
    culture = world["cultures"][culture_id]
    name = (action.get("name") or action.get("note") or "a new custom").strip()[:80]
    desc = (action.get("note") or "").strip()

    # Founding a lasting institution takes resources; a poor realm cannot.
    if culture["resources"].get("wealth", 0) < FOUND_WEALTH_COST:
        return
    culture["resources"]["wealth"] -= FOUND_WEALTH_COST

    culture.setdefault("institutions", []).append(
        {"name": name, "description": desc, "tick": world["tick"]}
    )
    events.append(make_event(
        world, "found",
        f"{culture['name']} established {name}.",
        [culture_id], reason=desc,
    ))


def _resolve_subjugate(world: dict, action: dict, events: list) -> None:
    """Force a reachable, weaker neighbour into tributary vassalage."""
    actor_id = action["culture_id"]
    target_id = action["target"]
    if not target_id or target_id not in world["cultures"] or target_id == actor_id:
        return
    actor = world["cultures"][actor_id]
    target = world["cultures"][target_id]
    if target.get("fallen") or target["population"] <= 0:
        return
    # must be able to reach the target's land
    reach = reachable_regions(world, actor_id)
    if not any(r["occupant"] == target_id and rid in reach for rid, r in world["regions"].items()):
        events.append(make_event(
            world, "subjugate_failed",
            f"{actor['name']} could not bring its power to bear on {target['name']}.",
            [actor_id, target_id], reason=action["note"],
        ))
        return
    if target.get("overlord") == actor_id:
        return  # already a vassal
    if strength(actor, world) >= SUBJUGATE_STRENGTH_RATIO * strength(target, world):
        target["overlord"] = actor_id
        if target_id not in actor.setdefault("tributaries", []):
            actor["tributaries"].append(target_id)
        actor["relations"][target_id] = actor["relations"].get(target_id, 0) + 5
        target["relations"][actor_id] = target["relations"].get(actor_id, 0) - 20
        events.append(make_event(
            world, "subjugate",
            f"{actor['name']} reduced {target['name']} to a tributary, exacting submission and tribute.",
            [actor_id, target_id], reason=action["note"],
        ))
    else:
        target["relations"][actor_id] = target["relations"].get(actor_id, 0) - 10
        events.append(make_event(
            world, "subjugate_failed",
            f"{actor['name']} demanded the submission of {target['name']}, who defied them.",
            [actor_id, target_id], reason=action["note"],
        ))


def _resolve_marry(world: dict, action: dict, events: list, all_marry_actions: list, processed: set) -> None:
    """A dynastic marriage: a binding alliance when both houses seek it the same generation."""
    actor_id = action["culture_id"]
    target_id = action["target"]
    if not target_id or target_id not in world["cultures"] or target_id == actor_id:
        return
    pair = tuple(sorted([actor_id, target_id]))
    if pair in processed:
        return
    actor = world["cultures"][actor_id]
    target = world["cultures"][target_id]
    mutual = any(o["culture_id"] == target_id and o["target"] == actor_id for o in all_marry_actions)
    if mutual:
        processed.add(pair)
        if target_id not in actor.setdefault("marriages", []):
            actor["marriages"].append(target_id)
        if actor_id not in target.setdefault("marriages", []):
            target["marriages"].append(actor_id)
        actor["relations"][target_id] = actor["relations"].get(target_id, 0) + 25
        target["relations"][actor_id] = target["relations"].get(actor_id, 0) + 25
        events.append(make_event(
            world, "marriage",
            f"The ruling houses of {actor['name']} and {target['name']} were joined in marriage, binding the dynasties.",
            [actor_id, target_id], reason=action["note"],
        ))
    else:
        actor["relations"][target_id] = actor["relations"].get(target_id, 0) + 5
        if actor_id in target.get("relations", {}):
            target["relations"][actor_id] = target["relations"].get(actor_id, 0) + 3
        events.append(make_event(
            world, "betrothal_offer",
            f"{actor['name']} offered a marriage-alliance to {target['name']}.",
            [actor_id, target_id], reason=action["note"],
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

    # Permanent infrastructure: raise the home region's food yield (irrigation,
    # terraces, granaries). 20 wealth buys +1 food per tick, forever.
    improvement = amount // 20
    if improvement <= 0:
        return
    home_region.setdefault("yield", {}).setdefault("food", 0)
    home_region["yield"]["food"] += improvement

    events.append(make_event(
        world, "build",
        f"{culture['name']} raised great works in {home_region['name']}, lifting its food yield by {improvement} (spent {amount} wealth).",
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

        # Mutual trade enriches BOTH sides (gains from exchange): each keeps its
        # own wealth and gains a profit equal to the smaller of the two offers.
        volume = min(amount, mutual_trade["amount"])
        profit = max(1, volume // 2)
        culture["resources"]["wealth"] += profit
        target["resources"]["wealth"] += profit
        # The flow of goods also feeds cities: a little food on both sides.
        culture["resources"]["food"] += profit
        target["resources"]["food"] += profit

        culture["relations"][target_id] += 8
        target["relations"][culture_id] += 8

        events.append(make_event(
            world, "trade_mutual",
            f"{culture['name']} and {target['name']} opened a rich trade (volume {volume}); both prospered (+{profit} wealth, +{profit} food). Relations warmed.",
            [culture_id, target_id], reason=action["note"],
        ))
    elif amount > 0:
        # No partner this turn: the merchants sell on the open market instead,
        # converting wealth into food (a lifeline for wealthy, hungry peoples).
        spent = min(amount, culture["resources"]["wealth"])
        culture["resources"]["wealth"] -= spent
        culture["resources"]["food"] += spent
        culture["relations"][target_id] += 2
        if culture_id in world["cultures"][target_id]["relations"]:
            world["cultures"][target_id]["relations"][culture_id] += 1
        events.append(make_event(
            world, "trade_market",
            f"{target['name']} did not answer {culture['name']}'s offer, so its caravans sold abroad, turning {spent} wealth into {spent} food.",
            [culture_id, target_id], reason=action["note"],
        ))
    else:
        # A bare gesture with nothing offered: goodwill only.
        culture["relations"][target_id] += 2
        if culture_id in world["cultures"][target_id]["relations"]:
            world["cultures"][target_id]["relations"][culture_id] += 1
        events.append(make_event(
            world, "trade_overture",
            f"{culture['name']} made overtures of trade to {target['name']}.",
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
    target_region = world["regions"][target_region_id]

    # Valid if the target is within the culture's reach (held, land-adjacent, or
    # overseas if sea-capable). An empire expands from its whole frontier.
    is_valid_target = target_region_id in reachable_regions(world, culture_id)

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
    if culture["resources"]["food"] < SETTLE_FOOD_COST:
        events.append(make_event(
            world, "migrate_failed",
            f"{culture['name']} lacked the food to settle {target_region['name']}.",
            [culture_id], reason=action["note"],
        ))
        return
    culture["resources"]["food"] -= SETTLE_FOOD_COST
    target_region["occupant"] = culture_id
    target_region["populace"] = culture_id  # settlers become the people of this land
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
    
    # Find a defender-held region the attacker can reach (by land, or across the
    # water to a coastal province if sea-capable).
    reach = reachable_regions(world, attacker_id)
    defender_region = next(
        (rid for rid, r in world["regions"].items()
         if r["occupant"] == defender_id and rid in reach),
        None,
    )

    if not defender_region:
        events.append(make_event(
            world, "attack_out_of_range",
            f"{attacker['name']} could not reach {defender['name']} in combat.",
            [attacker_id, defender_id], reason=action["note"],
        ))
        return
    
    # Mobilizing a generation for war is costly whatever the outcome.
    WAR_FOOD_COST = 40
    attacker["resources"]["food"] = max(0, attacker["resources"]["food"] - WAR_FOOD_COST)

    # Calculate strengths
    att_strength = strength(attacker, world)
    def_strength = strength(defender, world)
    
    # Roll dice
    att_roll = roll()
    def_roll = roll()
    
    att_total = att_strength * att_roll
    def_total = def_strength * def_roll
    
    if att_total > def_total:
        # Attacker wins: casualties, plunder, and the contested region changes hands.
        casualties = round(defender["population"] * 0.15)
        defender["population"] -= casualties
        loot = round(defender["resources"]["wealth"] * 0.25)
        defender["resources"]["wealth"] -= loot
        attacker["resources"]["wealth"] += loot

        attacker["relations"][defender_id] -= 30
        defender["relations"][attacker_id] -= 30

        # Seize the contested region
        world["regions"][defender_region]["occupant"] = attacker_id
        seized_name = world["regions"][defender_region]["name"]

        events.append(make_event(
            world, "attack_success",
            f"{attacker['name']} stormed {defender['name']} (rolled {att_total:.2f} vs {def_total:.2f}): "
            f"{casualties:,} slain, {loot:,} wealth plundered, and {seized_name} fell to {attacker['name']}.",
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

"""Per-tick economy: production, consumption, population growth, starvation, random events."""

import math
import random
from worldsim.config import (
    FOOD_PER_POP, GROWTH_DIVISOR, STARVE_FRACTION, GROWTH_EVENT_MIN, RANDOM_EVENT_CHANCE
)
from worldsim.arbiter import make_event


def _regions_of(world: dict, culture_id: str) -> list:
    return [r for r in world["regions"].values() if r["occupant"] == culture_id]


def apply_economy(world: dict) -> list:
    """Run one tick of economy. Mutates `world`. Returns a list of events."""
    events = []
    for culture_id in sorted(world["cultures"].keys()):
        culture = world["cultures"][culture_id]
        my_regions = _regions_of(world, culture_id)

        # Collapse: a civilization that has lost all its land is broken. Mark it
        # once, as a remnant people with no homeland — they will dwindle.
        if not my_regions and not culture.get("fallen"):
            culture["fallen"] = True
            events.append(make_event(
                world, "collapse",
                f"{culture['name']} has lost its last land and fallen — a scattered, homeless remnant.",
                [culture_id],
            ))

        # 1. Production: every occupied region yields resources to its occupant.
        for region in my_regions:
            for res, amt in region.get("yield", {}).items():
                culture["resources"][res] = culture["resources"].get(res, 0) + amt

        # 2. Consumption: population eats food.
        eaten = math.ceil(culture["population"] / FOOD_PER_POP)
        food = culture["resources"]["food"]
        if food >= eaten:
            culture["resources"]["food"] = food - eaten
            # 3. Growth: well-fed populations grow.
            growth = culture["population"] // GROWTH_DIVISOR
            if growth > 0:
                culture["population"] += growth
            if growth >= GROWTH_EVENT_MIN:
                events.append(make_event(
                    world, "growth",
                    f"{culture['name']} flourished, growing by {growth:,} to {culture['population']:,}.",
                    [culture_id],
                ))
        else:
            # 4. Starvation: a hungry population loses a fraction of its people.
            deaths = round(culture["population"] * STARVE_FRACTION)
            culture["resources"]["food"] = 0
            culture["population"] = max(0, culture["population"] - deaths)
            held = ", ".join(r["name"] for r in _regions_of(world, culture_id)) or "no land"
            events.append(make_event(
                world, "famine",
                f"Famine gripped {culture['name']}; {deaths:,} starved (now {culture['population']:,}). They hold {held}.",
                [culture_id],
            ))

    return events


def maybe_random_event(world: dict) -> list:
    """With probability RANDOM_EVENT_CHANCE, apply one random world event. Returns events."""
    if random.random() >= RANDOM_EVENT_CHANCE:
        return []

    culture_ids = sorted(world["cultures"].keys())
    target_id = random.choice(culture_ids)
    culture = world["cultures"][target_id]
    kind = random.choice([
        "blight", "rich_vein", "plague", "windfall",
        "prophet", "good_harvest", "earthquake",
    ])

    if kind == "blight":
        lost = culture["resources"]["food"] // 3
        culture["resources"]["food"] -= lost
        text = f"A blight rotted the granaries of {culture['name']}; {lost:,} food spoiled."
    elif kind == "rich_vein":
        culture["resources"]["ore"] += 200
        text = f"Miners of {culture['name']} struck a vast ore lode (+200 ore)."
    elif kind == "plague":
        deaths = round(culture["population"] * 0.12)
        culture["population"] = max(0, culture["population"] - deaths)
        text = f"A plague swept through {culture['name']}; {deaths:,} perished."
    elif kind == "windfall":
        culture["resources"]["wealth"] += 250
        text = f"A golden age of commerce enriched {culture['name']} (+250 wealth)."
    elif kind == "prophet":
        culture["resources"]["wealth"] += 80
        text = f"A prophet arose among {culture['name']}, kindling fervor and unity."
    elif kind == "good_harvest":
        culture["resources"]["food"] += 200
        text = f"Bountiful rains blessed {culture['name']} with a great harvest (+200 food)."
    else:  # earthquake
        deaths = round(culture["population"] * 0.06)
        culture["population"] = max(0, culture["population"] - deaths)
        culture["resources"]["wealth"] = max(0, culture["resources"]["wealth"] - 60)
        text = f"An earthquake shattered the cities of {culture['name']}; {deaths:,} died."

    return [make_event(world, f"world_{kind}", text, [target_id])]

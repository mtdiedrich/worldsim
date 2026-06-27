"""Per-tick economy: production, consumption, population growth, starvation, random events."""

import math
import random
from worldsim.config import (
    FOOD_PER_POP, GROWTH_DIVISOR, STARVE_DEATHS_PER_FOOD, RANDOM_EVENT_CHANCE
)
from worldsim.arbiter import make_event


def apply_economy(world: dict) -> list:
    """Run one tick of economy. Mutates `world`. Returns a list of events."""
    events = []
    for culture_id in sorted(world["cultures"].keys()):
        culture = world["cultures"][culture_id]

        # 1. Production: every occupied region yields resources to its occupant.
        for region in world["regions"].values():
            if region["occupant"] == culture_id:
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
            if growth >= 10:
                events.append(make_event(
                    world, "growth",
                    f"{culture['name']} grew by {growth} to {culture['population']} (well-fed).",
                    [culture_id],
                ))
        else:
            # 4. Starvation: deficit kills people.
            deficit = eaten - food
            deaths = deficit * STARVE_DEATHS_PER_FOOD
            culture["resources"]["food"] = 0
            culture["population"] = max(0, culture["population"] - deaths)
            events.append(make_event(
                world, "famine",
                f"{culture['name']} starved: short {deficit} food, {deaths} died (population {culture['population']}).",
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
    kind = random.choice(["blight", "rich_vein", "plague", "windfall"])

    if kind == "blight":
        lost = culture["resources"]["food"] // 3
        culture["resources"]["food"] -= lost
        text = f"A blight struck {culture['name']}; {lost} food spoiled."
    elif kind == "rich_vein":
        culture["resources"]["ore"] += 25
        text = f"{culture['name']} struck a rich ore vein (+25 ore)."
    elif kind == "plague":
        deaths = round(culture["population"] * 0.08)
        culture["population"] = max(0, culture["population"] - deaths)
        text = f"A plague swept {culture['name']}; {deaths} died."
    else:  # windfall
        culture["resources"]["wealth"] += 30
        text = f"A windfall enriched {culture['name']} (+30 wealth)."

    return [make_event(world, f"world_{kind}", text, [target_id])]

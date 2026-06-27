"""Hardcoded seeds and initial world state for v1."""

import copy

# Culture seeds - hardcoded for v1
CULTURE_SEEDS = {
    "saltborn": {
        "id": "saltborn",
        "name": "The Saltborn",
        "values": "Wealth is moral proof. Hospitality is sacred; a guest cannot be harmed.",
        "goals": ["control salt and ore trade", "convert neighbors into debtors"],
        "taboos": ["spilling a guest's blood", "burying the dead in soil (they entomb in salt)"],
        "blind_spots": ["assume everyone can be bought", "underrate religious motives"],
        "false_beliefs": ["believe the Ashfolk worship them as sea-gods"],
        "founding_trauma": "a famine broke only when they opened the salt mine; scarcity haunts them",
    },
    "ashfolk": {
        "id": "ashfolk",
        "name": "The Ashfolk",
        "values": "Ancestors watch and judge. Land is borrowed from the dead, never owned.",
        "goals": ["keep ancestral highlands unsettled by outsiders", "spread the ash-rite"],
        "taboos": ["selling land", "writing the names of the dead"],
        "blind_spots": ["distrust all coin offers as bribery", "slow to form alliances"],
        "false_beliefs": ["believe Saltborn salt-tombs trap and torment souls"],
        "founding_trauma": "an outside lord once sold their burial mountain; they exiled and burned him",
    },
}

# Initial world state
INITIAL_WORLD = {
    "tick": 0,
    "regions": {
        "coast": {
            "name": "Coast",
            "terrain": "salt-marsh",
            "resources": {"food": 300, "ore": 100, "wealth": 0},
            "yield": {"food": 9, "ore": 2, "wealth": 4},
            "occupant": "saltborn",
            "adjacent": ["lowland"],
        },
        "lowland": {
            "name": "Lowland",
            "terrain": "grassland",
            "resources": {"food": 200, "ore": 0, "wealth": 0},
            "yield": {"food": 7, "ore": 0, "wealth": 1},
            "occupant": None,
            "adjacent": ["coast", "pass"],
        },
        "pass": {
            "name": "Pass",
            "terrain": "mountain-pass",
            "resources": {"food": 50, "ore": 150, "wealth": 0},
            "yield": {"food": 1, "ore": 7, "wealth": 0},
            "occupant": None,
            "adjacent": ["lowland", "highland"],
        },
        "highland": {
            "name": "Highland",
            "terrain": "volcanic-plateau",
            "resources": {"food": 100, "ore": 200, "wealth": 0},
            "yield": {"food": 3, "ore": 9, "wealth": 0},
            "occupant": "ashfolk",
            "adjacent": ["pass"],
        },
    },
    "cultures": {
        "saltborn": {
            "name": "The Saltborn",
            "home_region": "coast",
            "population": 1000,
            "resources": {"food": 80, "ore": 50, "wealth": 100},
            "tech": [],
            "relations": {"ashfolk": 0},
        },
        "ashfolk": {
            "name": "The Ashfolk",
            "home_region": "highland",
            "population": 1000,
            "resources": {"food": 80, "ore": 50, "wealth": 100},
            "tech": [],
            "relations": {"saltborn": 0},
        },
    },
    "event_log": [],
}


def get_initial_world():
    """Return a deep copy of the initial world state."""
    return copy.deepcopy(INITIAL_WORLD)

"""Hardcoded seeds and initial world state.

A continent of eighteen regions across many biomes, contested by six
civilizations. Each culture starts on its capital region; the open regions
between them are the ground they will expand into and fight over. Seeds are
asymmetric on purpose — different material bases, cosmologies, kinship, taboos,
and founding wounds — so they diverge instead of converging on one median culture.
"""

import copy

# ---------------------------------------------------------------------------
# Culture seeds
# ---------------------------------------------------------------------------
CULTURE_SEEDS = {
    "meskar": {
        "id": "meskar",
        "name": "The Meskar Dominion",
        "values": "Order is sacred. The river feeds all; the canal-law binds all. The God-Steward owns the harvest and lends it back.",
        "goals": ["control the river valley and its grain", "make every neighbor a tributary of the canal", "record all things in the great ledgers"],
        "taboos": ["leaving a death unrecorded", "letting flood-water run unmeasured", "a steward who eats before the granary is sealed"],
        "blind_spots": ["mistake mobile peoples for bandits to be administered", "believe anything outside the ledger does not truly exist"],
        "false_beliefs": ["believe the steppe nomads are a leaderless rabble who will scatter at a show of order"],
        "founding_trauma": "the First Flood that drowned the old capital; only counting and canals saved them, so to them measurement is survival",
    },
    "vael": {
        "id": "vael",
        "name": "The Vael Horde",
        "values": "Freedom is the open horizon. Kinship is blood and oath, not borders. A people who plant roots become slaves to the soil.",
        "goals": ["keep the grass-sea unfenced", "raid the settled for horses, grain, and glory", "bind the clans through marriage and feud"],
        "taboos": ["building a permanent wall", "writing a living person's name (it cages the soul)", "breaking guest-bread then drawing a blade"],
        "blind_spots": ["see fortified settlement as weakness, not strength", "cannot imagine loyalty to a place rather than a kin-line"],
        "false_beliefs": ["believe the Meskar ledgers are a kind of dark sorcery that steals the names of the dead"],
        "founding_trauma": "a generation penned in a river-lord's labor camps; they broke out and swore never again to be fenced",
    },
    "qadir": {
        "id": "qadir",
        "name": "The Qadir Caravanate",
        "values": "The Salt Road is holy. A debt is a sacred bond. There is one God beyond all idols, and the desert is His proof.",
        "goals": ["monopolize salt, spice, and the long-distance trade", "convert the coast and valley to the One Faith", "buy what cannot be conquered"],
        "taboos": ["breaking a sworn contract", "depicting God or the saints in any image", "leaving a traveler to die of thirst, even an enemy"],
        "blind_spots": ["assume every people has a price and every faith is a market", "underrate ancestor-worshippers as superstitious primitives"],
        "false_beliefs": ["believe the jungle cities secretly hunger for the One Faith and merely await a worthy missionary"],
        "founding_trauma": "a century of thirst-wars over the last wells, ended only when the prophet-merchant unified the caravans under one creed and one ledger of debts",
    },
    "vorr": {
        "id": "vorr",
        "name": "The Vorrand Hierophancy",
        "values": "The dead rule from the gold-veined deeps. The living are stewards of the ancestors' mountain. Metal is congealed prayer.",
        "goals": ["keep the gold-hills inviolate", "forge the finest weapons and reliquaries in the world", "make neighbors kneel to the ancestor-cult"],
        "taboos": ["selling ancestral gold to outsiders", "burying the dead anywhere but the mountain", "letting an unconsecrated foot touch the high tombs"],
        "blind_spots": ["distrust all coin and trade as soul-corrupting", "slow and proud, contemptuous of faster peoples"],
        "false_beliefs": ["believe their mountain is the literal center and summit of the world, and all rivers flow down from the ancestors' will"],
        "founding_trauma": "grave-robbers from the lowlands once cracked the high tombs; the Vorrand walled the mountain in zealous dread and now trust no outsider near the dead",
    },
    "ixil": {
        "id": "ixil",
        "name": "The Ixil City-Weave",
        "values": "Time turns in cycles of blood and rain. The gods must be fed or the sun will not rise. Each city is a jealous flower of the same vine.",
        "goals": ["secure captives and tribute for the rites", "keep the calendar and feed the sun", "play rival cities and outsiders against each other"],
        "taboos": ["letting a feast-day pass without offering", "a king who has taken no captive", "felling the heart-tree of a city"],
        "blind_spots": ["read every gift and treaty as a move in a ritual contest", "fractious — the cities can rarely act as one"],
        "false_beliefs": ["believe the pale desert and mountain peoples are bloodless ghosts whose deaths would not even please the gods"],
        "founding_trauma": "a great drought when the sun 'refused' the harvest; only mass offering 'restored' it, searing into them that the gods demand blood or the world ends",
    },
    "tirnes": {
        "id": "tirnes",
        "name": "The Tirnesh Thalassocracy",
        "values": "The sea is the only road that cannot be taxed by lords. A contract outranks a crown. Knowledge of currents, coins, and stars is power.",
        "goals": ["control every harbor and sea-lane", "grow rich as the indispensable middleman", "keep any single land-power from growing too strong"],
        "taboos": ["defaulting on a posted bond", "harming a guest under the harbor-peace", "revealing the secret sea-charts to a foreigner"],
        "blind_spots": ["assume sea power is decisive and inland affairs are sideshows", "trust ink and ledgers over loyalty"],
        "false_beliefs": ["believe no inland empire can ever truly threaten an island that commands the waves"],
        "founding_trauma": "their first city was burned by a jealous mainland king; they took to the islands and swore that walls of water and gold would guard them where stone had failed",
    },
}

# ---------------------------------------------------------------------------
# Geography: 18 regions in a connected graph across the continent.
#   resources = descriptive richness the agents perceive (flavor)
#   yield     = what the region produces each tick for its occupant (mechanics)
# ---------------------------------------------------------------------------
def _region(name, terrain, resources, yld, occupant, adjacent):
    return {
        "name": name,
        "terrain": terrain,
        "resources": resources,
        "yield": yld,
        "occupant": occupant,
        "adjacent": adjacent,
    }


_REGIONS = {
    # --- the river west ---
    "silt_delta":   _region("Silt Delta", "river-delta",       {"food": 350, "ore": 20, "wealth": 80},  {"food": 35, "ore": 2, "wealth": 8},  "meskar", ["reed_marsh", "white_sound"]),
    "reed_marsh":   _region("Reed Marshes", "marsh",            {"food": 180, "ore": 0,  "wealth": 20},  {"food": 18, "ore": 0, "wealth": 2},  "meskar", ["silt_delta", "river_valley"]),
    "river_valley": _region("The Long Valley", "river-plain",   {"food": 400, "ore": 30, "wealth": 50},  {"food": 40, "ore": 3, "wealth": 5},  "meskar", ["reed_marsh", "floodplain", "great_lake"]),
    "floodplain":   _region("The Floodplain", "alluvial-plain", {"food": 300, "ore": 0,  "wealth": 20},  {"food": 30, "ore": 0, "wealth": 2},  None,     ["river_valley", "high_steppe", "great_lake"]),
    # --- the northern grass and forest ---
    "grass_sea":    _region("The Grass Sea", "steppe",          {"food": 140, "ore": 20, "wealth": 30},  {"food": 14, "ore": 2, "wealth": 3},  "vael",   ["high_steppe", "pine_marches"]),
    "high_steppe":  _region("The High Steppe", "steppe",        {"food": 120, "ore": 30, "wealth": 20},  {"food": 12, "ore": 3, "wealth": 2},  None,     ["grass_sea", "floodplain", "pine_marches", "red_mesa"]),
    "pine_marches": _region("The Pine Marches", "boreal-forest",{"food": 160, "ore": 120,"wealth": 20},  {"food": 16, "ore": 12,"wealth": 2},  None,     ["grass_sea", "high_steppe", "frostmark"]),
    "frostmark":    _region("The Frostmark", "tundra",          {"food": 40,  "ore": 60, "wealth": 10},  {"food": 4,  "ore": 6, "wealth": 1},  None,     ["pine_marches"]),
    # --- the central desert and ore heart ---
    "salt_pan":     _region("The Salt Pans", "salt-desert",     {"food": 30,  "ore": 50, "wealth": 200}, {"food": 3,  "ore": 5, "wealth": 20}, "qadir",  ["red_mesa", "bone_waste", "great_lake"]),
    "red_mesa":     _region("The Red Mesa", "ore-plateau",      {"food": 60,  "ore": 180,"wealth": 40},  {"food": 6,  "ore": 18,"wealth": 4},  None,     ["high_steppe", "salt_pan", "gold_hills", "great_lake"]),
    "gold_hills":   _region("The Gold Hills", "ore-highland",   {"food": 80,  "ore": 220,"wealth": 180}, {"food": 8,  "ore": 22,"wealth": 18}, "vorr",   ["red_mesa", "bone_waste"]),
    "bone_waste":   _region("The Bone Wastes", "desert",        {"food": 20,  "ore": 40, "wealth": 20},  {"food": 2,  "ore": 4, "wealth": 2},  None,     ["salt_pan", "gold_hills", "ash_coast"]),
    "great_lake":   _region("Greatlake Shore", "lakeshore",     {"food": 280, "ore": 20, "wealth": 40},  {"food": 28, "ore": 2, "wealth": 4},  None,     ["river_valley", "floodplain", "salt_pan", "red_mesa", "sun_jungle"]),
    # --- the southern jungle and coast ---
    "sun_jungle":   _region("The Sun Jungle", "rainforest",     {"food": 260, "ore": 40, "wealth": 60},  {"food": 26, "ore": 4, "wealth": 6},  "ixil",   ["ash_coast", "great_lake"]),
    "ash_coast":    _region("The Ash Coast", "volcanic-coast",  {"food": 100, "ore": 140,"wealth": 30},  {"food": 10, "ore": 14,"wealth": 3},  None,     ["bone_waste", "sun_jungle", "pearl_harbor"]),
    "pearl_harbor": _region("Pearl Harbour", "coast",           {"food": 120, "ore": 20, "wealth": 220}, {"food": 12, "ore": 2, "wealth": 22}, "tirnes", ["ash_coast", "coral_isles", "white_sound"]),
    "coral_isles":  _region("The Coral Isles", "archipelago",   {"food": 90,  "ore": 0,  "wealth": 140}, {"food": 9,  "ore": 0, "wealth": 14}, None,     ["pearl_harbor"]),
    "white_sound":  _region("The White Sound", "strait-coast",  {"food": 110, "ore": 10, "wealth": 80},  {"food": 11, "ore": 1, "wealth": 8},  None,     ["silt_delta", "pearl_harbor"]),
}


# Founding rulers and starting profiles. Deliberately asymmetric in size, wealth,
# and reach — an empire, a duchy, a horde, a merchant republic — so trajectories diverge.
# Starting populations sit near each home region's geographic carrying capacity.
# cohesion: old empires start lower, young frontier/steppe peoples higher.
# culture_vec: a point in identity-space; distance between vectors drives frontier tension.
_PROFILES = {
    "meskar": {"home": "silt_delta",  "pop": 58000, "cohesion": 0.45, "vec": [0.8, 0.2, 0.1],
               "ruler": "God-Steward Vesmer III", "house": "House Vesmar", "reach": ["land"]},
    "vael":   {"home": "grass_sea",   "pop": 15000, "cohesion": 0.72, "vec": [0.1, 0.9, 0.3],
               "ruler": "Khagan Tarkan Bturhan", "house": "the Bturhan Kin", "reach": ["land"]},
    "qadir":  {"home": "salt_pan",    "pop": 13000, "cohesion": 0.66, "vec": [0.5, 0.3, 0.9],
               "ruler": "Sayyid Idris al-Qadir", "house": "House al-Qadir", "reach": ["land"]},
    "vorr":   {"home": "gold_hills",  "pop": 18000, "cohesion": 0.60, "vec": [0.2, 0.7, 0.6],
               "ruler": "Hierophant Vorrak-Suln", "house": "the Tomb-Convocation", "reach": ["land"]},
    "ixil":   {"home": "sun_jungle",  "pop": 30000, "cohesion": 0.50, "vec": [0.9, 0.5, 0.4],
               "ruler": "Speaker Ixchel of the Nine Cities", "house": "the City-Weave", "reach": ["land"]},
    "tirnes": {"home": "pearl_harbor","pop": 22000, "cohesion": 0.55, "vec": [0.3, 0.1, 0.8],
               "ruler": "Doge Aurel Castaine", "house": "House Castaine", "reach": ["land", "sea"]},
}

# coastal regions can be reached across water by a sea-capable power
_COASTAL = {"silt_delta", "white_sound", "pearl_harbor", "coral_isles", "ash_coast"}


def _initial_culture(cid, others):
    p = _PROFILES[cid]
    return {
        "name": CULTURE_SEEDS[cid]["name"],
        "home_region": p["home"],
        "population": p["pop"],
        "ruler": p["ruler"],
        "house": p["house"],
        "reach": list(p["reach"]),
        # --- cliodynamic state variables ---
        "tech_level": 0.0,         # scalar; raised by innovation, spread by diffusion
        "cohesion": p["cohesion"], # asabiyya, [0,1]
        "elites": int(p["pop"] * 0.02),
        "instability": 0.0,
        "culture_vec": list(p["vec"]),
        "k": 0.0,                  # last computed carrying capacity (filled each tick)
        "k_ratio": 0.0,            # last N/K
        # --- identity / flavour carried by the Chronicler ---
        "tech": [],           # named advances the Chronicler attaches
        "institutions": [],   # named festivals/cults/laws
        "religion": None,
        "parent": None,
        "born_tick": 0,
        "fallen": False,
        "relations": {o: 0 for o in others},
    }


_IDS = list(CULTURE_SEEDS.keys())

INITIAL_WORLD = {
    "tick": 0,
    "year": 0,
    "regions": _REGIONS,
    "cultures": {
        cid: _initial_culture(cid, [o for o in _IDS if o != cid])
        for cid in _IDS
    },
    "event_log": [],
}


def get_initial_world():
    """Return a deep copy of the initial world state.

    Sets each region's `populace` (the people who live there) equal to its
    initial `occupant` (the ruler). The two diverge when a region is conquered:
    a foreign ruler over a native populace is what breeds rebellion.
    """
    world = copy.deepcopy(INITIAL_WORLD)
    for rid, region in world["regions"].items():
        region["populace"] = region["occupant"]
        region["coastal"] = rid in _COASTAL
    return world

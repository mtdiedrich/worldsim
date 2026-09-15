"""Dynastic clock: rulers age and die; tributaries pay overlords.

Python keeps the demographic clock honest (rulers are mortal) and the money of
vassalage flowing. The *human* details of who succeeds — an able heir, a contested
throne, a regency for a child, a foreign house inheriting — are authored by the
Chronicler. This module only guarantees a realm is never left permanently kingless.
"""

import random

from worldsim.arbiter import make_event, strength
from worldsim.config import (
    YEARS_PER_TICK, RULER_DEATH_AGE, RULER_VIOLENCE_CHANCE,
    RULER_START_AGE, TRIBUTE_FRACTION,
)

_GIVEN_NAMES = [
    "Aldric", "Berenga", "Casimir", "Dragomir", "Eudokia", "Ferran", "Gizela",
    "Halvard", "Ingrith", "Jovan", "Khadira", "Leofric", "Mstislav", "Nadira",
    "Orseo", "Pelagia", "Radomir", "Sabela", "Tervel", "Ulan", "Vesmer",
    "Wulfric", "Yaromir", "Zorica",
]
_ORDINALS = ["", " II", " III", " IV", " V"]


def _heir_name(rng):
    return rng.choice(_GIVEN_NAMES) + rng.choice(_ORDINALS)


def advance_rulers(world):
    """Age every living ruler one generation and roll for death. Returns events.

    A death sets `pending_succession` on the culture and vacates the throne; the
    Chronicler (or the fallback below) will seat a successor this same generation.
    """
    events = []
    for cid, c in sorted(world["cultures"].items()):
        if c.get("fallen") or c["population"] <= 0 or not c.get("ruler"):
            continue
        c["ruler_age"] = c.get("ruler_age", RULER_START_AGE) + YEARS_PER_TICK
        age = c["ruler_age"]
        p = RULER_VIOLENCE_CHANCE
        if age >= RULER_DEATH_AGE:
            p += min(0.85, (age - RULER_DEATH_AGE) / 30.0 + 0.2)
        if random.random() < p:
            reign = max(0, world.get("tick", 0) - c.get("reign_start", 0)) * YEARS_PER_TICK
            c["pending_succession"] = {"ruler": c["ruler"], "house": c.get("house"), "age": age}
            events.append(make_event(
                world, "death",
                f"{c['ruler']} of {c['name']} died at {age} after {reign} years; "
                f"the throne of {c.get('house', 'the realm')} falls vacant.",
                [cid],
            ))
            c["ruler"] = None
    return events


def resolve_pending_successions(world):
    """Fallback: seat an uncontested heir wherever the Chronicler left one vacant."""
    rng = random
    events = []
    for cid, c in sorted(world["cultures"].items()):
        ps = c.get("pending_succession")
        if not ps:
            continue
        if c.get("fallen") or c["population"] <= 0:
            c.pop("pending_succession", None)
            continue
        house = c.get("house") or ps.get("house") or "the realm"
        heir = _heir_name(rng)
        c["ruler"] = heir
        c["ruler_age"] = RULER_START_AGE
        c["reign_start"] = world.get("tick", 0)
        c.pop("pending_succession", None)
        events.append(make_event(
            world, "succession",
            f"{heir} of {house} took up the rule of {c['name']} without dispute.",
            [cid],
        ))
    return events


def collect_tribute(world):
    """Tributaries send a share of their wealth to their overlord. Returns events."""
    events = []
    for cid, c in sorted(world["cultures"].items()):
        overlord_id = c.get("overlord")
        if not overlord_id:
            continue
        overlord = world["cultures"].get(overlord_id)
        # break the bond if the overlord is gone or has fallen
        if not overlord or overlord.get("fallen") or overlord["population"] <= 0:
            c["overlord"] = None
            continue
        if c.get("fallen") or c["population"] <= 0:
            continue
        tribute = round(c["resources"].get("wealth", 0) * TRIBUTE_FRACTION)
        if tribute <= 0:
            continue
        c["resources"]["wealth"] -= tribute
        overlord["resources"]["wealth"] = overlord["resources"].get("wealth", 0) + tribute
        if overlord_id not in c.get("relations", {}):
            continue
        events.append(make_event(
            world, "tribute",
            f"{c['name']} rendered {tribute} wealth in tribute to {overlord['name']}.",
            [cid, overlord_id],
        ))
    return events

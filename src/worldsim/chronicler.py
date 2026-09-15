"""The Chronicler: narrator of a world it does not steer.

The cliodynamics engine decides what happens and why — who grows, who fractures,
who conquers whom, when plague strikes. The Chronicler only clothes that skeleton:
it names the peoples the engine births, and supplies the specific human color the
structural state implies — a heresy born in a collapse, a festival in a golden age,
the named art behind a wave of innovation, a faith spreading down the trade-roads.

It authors identity and prose. It does not move armies, settle land, or birth or
kill peoples — those are the engine's. So it can never corrupt the world's structure.
"""

import json
import re
import logging

from worldsim.llm import call_llm
from worldsim.config import CHRONICLER_MODEL, CHRONICLER_MAX_TOKENS
from worldsim.arbiter import make_event

logger = logging.getLogger(__name__)


CHRONICLER_SYSTEM = """You are the Chronicler of a living world — its impartial historian.
The age's structural events have ALREADY happened: populations rose and fell, realms expanded,
fractured, conquered, starved, or were struck by plague. You do not change any of that. Your task:

1. NAME the peoples just born from upheaval. Each newborn is a provisional breakaway with no name yet.
   Give it a name, a first ruler, a ruling house, and a one-line ethos — in keeping with its origin
   (who it broke from, the land it holds, the troubles that bore it).

2. CHRONICLE the human texture the structural facts imply, grounded in the SPECIFIC peoples and events given:
   - a heresy or prophetic movement born in a collapse or famine (give it a name and a grievance)
   - a festival, game, school, law-code, or monument arising in a prosperous, growing realm (name it)
   - the named art or craft behind a wave of innovation
   - a faith arising and spreading along contact

HARD RULES:
- Ground every line in the SPECIFIC facts given (named peoples, regions, the events of THIS generation). Never generic fantasy.
- Do NOT invent conquests, migrations, births, or deaths — only the engine does those. You narrate and name.
- Be concrete and specific. 0 to 4 chronicle entries; most generations are quiet. Always name every newborn listed.

Output ONLY a JSON object, no prose, no fences:
{
  "namings": [
    {"id": "<provisional id given to you>", "name": "The ...", "ruler": "<name and title>",
     "house": "<dynasty/line>", "ethos": "<one line on who they are>", "religion": "<name or null>"}
  ],
  "chronicle": [
    {"kind": "event", "text": "<concrete happening>", "involved": ["<culture_id>", ...]},
    {"kind": "religion", "founder": "<culture_id>", "name": "<faith name>", "text": "<its rise>",
     "spreads_to": ["<culture_id>", ...]}
  ]
}"""


def _slug(text, fallback="folk"):
    s = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return (s or fallback)[:24]


def _living(world):
    return {cid: c for cid, c in world["cultures"].items() if not c.get("fallen")}


def _report(world, tick_events, newborns):
    regions = world["regions"]
    lines = []
    for cid, c in sorted(_living(world).items()):
        held = [rid for rid, r in regions.items() if r["occupant"] == cid]
        foreign_ruled = [rid for rid in held if regions[rid].get("populace") not in (cid, None)]
        under_yoke = [rid for rid, r in regions.items()
                      if r.get("populace") == cid and r["occupant"] not in (cid, None)]
        ratio = c.get("k_ratio", 0.0)
        cond = ("STRAINED (over capacity)" if ratio > 1.05
                else "PROSPERING (room to grow)" if ratio < 0.6 else "settled")
        instab = c.get("instability", 0.0)
        mood = "ON THE BRINK" if instab > 0.7 else ("restive" if instab > 0.35 else "stable")
        lines.append(
            f"- {cid} ({c['name']}): ruler {c.get('ruler')}, house {c.get('house')}; "
            f"pop {c['population']:,}, {cond}, {mood} (instability {instab:.2f}, cohesion {c.get('cohesion', 0):.2f}, tech {c.get('tech_level', 0):.1f}); "
            f"holds {held}; rules foreign folk in {foreign_ruled or 'none'}; "
            f"its people under foreign rule in {under_yoke or 'none'}; religion {c.get('religion')}"
        )
    notable = [e for e in tick_events if e["type"] in (
        "conquest", "fragmentation", "time_of_troubles", "famine", "plague",
        "climate", "innovation", "extinction", "settle")]
    deeds = "\n".join(f"  * {e['description']}" for e in notable) or "  * (a quiet generation)"

    nb_lines = []
    for cid in newborns:
        c = world["cultures"].get(cid, {})
        nb_lines.append(
            f"  * id={cid}: broke away from {c.get('parent')}, holds "
            f"{[r for r in world['regions'] if world['regions'][r]['occupant'] == cid]}, pop {c.get('population', 0):,}"
        )
    nb = "\n".join(nb_lines) or "  * (none this generation)"

    return (
        "STATE OF THE WORLD:\n" + "\n".join(lines) +
        "\n\nTHIS GENERATION'S STRUCTURAL EVENTS:\n" + deeds +
        "\n\nNEWBORN PEOPLES NEEDING A NAME:\n" + nb
    )


def chronicle(world, seeds, memory, tick_events, newborns):
    """Name newborns and narrate the generation. Mutates world/seeds. Never raises."""
    try:
        report = _report(world, tick_events, newborns)
        user = (f"The year is {world.get('year')}, generation {world.get('tick')}.\n\n"
                f"{report}\n\nName the newborns and chronicle this generation as the JSON object.")
        raw = call_llm(CHRONICLER_SYSTEM, user,
                       max_tokens=CHRONICLER_MAX_TOKENS, model=CHRONICLER_MODEL).strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1] if "```" in raw else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip("` \n")
        data = json.loads(raw)
    except Exception as e:
        logger.warning(f"Chronicler produced nothing usable: {e}")
        data = {}

    events = []

    # 1. name the newborns
    for naming in (data.get("namings", []) if isinstance(data, dict) else []):
        try:
            cid = naming.get("id")
            c = world["cultures"].get(cid)
            if not c:
                continue
            if naming.get("name"):
                c["name"] = str(naming["name"])[:80]
            if naming.get("ruler"):
                c["ruler"] = str(naming["ruler"])[:80]
            if naming.get("house"):
                c["house"] = str(naming["house"])[:60]
            if naming.get("ethos"):
                c["ethos"] = str(naming["ethos"])[:200]
            if naming.get("religion"):
                c["religion"] = str(naming["religion"])[:60]
            c.pop("needs_naming", None)
            if cid in seeds:
                seeds[cid]["name"] = c["name"]
            events.append(make_event(
                world, "founding_people",
                f"The breakaway people took a name: {c['name']}, under {c['ruler']} of {c['house']}.",
                [cid]))
        except Exception as e:
            logger.warning(f"Chronicler naming skipped: {e}")

    # any newborn the Chronicler ignored still needs a non-provisional identity
    for cid in newborns:
        c = world["cultures"].get(cid)
        if c and c.get("needs_naming"):
            c.pop("needs_naming", None)

    # 2. narrate
    for entry in (data.get("chronicle", []) if isinstance(data, dict) else []):
        try:
            kind = entry.get("kind")
            if kind == "event":
                events.append(make_event(
                    world, "chronicle", entry.get("text", "").strip(),
                    [i for i in entry.get("involved", []) if i in world["cultures"]]))
            elif kind == "religion":
                founder = entry.get("founder")
                name = (entry.get("name") or "").strip()
                if founder in world["cultures"] and name:
                    world["cultures"][founder]["religion"] = name
                    converts = [founder]
                    fvec = world["cultures"][founder].get("culture_vec")
                    for other in entry.get("spreads_to", []):
                        oc = world["cultures"].get(other)
                        if not oc:
                            continue
                        oc["religion"] = name
                        # shared faith draws cultures together (lowers future frontier tension)
                        if fvec and oc.get("culture_vec"):
                            oc["culture_vec"] = [o + 0.1 * (f - o)
                                                 for o, f in zip(oc["culture_vec"], fvec)]
                        if founder in oc.get("relations", {}):
                            oc["relations"][founder] += 10
                            world["cultures"][founder]["relations"][other] = \
                                world["cultures"][founder]["relations"].get(other, 0) + 10
                        converts.append(other)
                    events.append(make_event(
                        world, "religion",
                        entry.get("text", "").strip() or f"The faith of {name} arose among {world['cultures'][founder]['name']}.",
                        converts))
        except Exception as e:
            logger.warning(f"Chronicler entry skipped: {e}")

    return events

"""The cliodynamics engine: history as the exhaust of structural loops.

No society "decides" anything here. Geography sets carrying capacity; population
runs against it (Malthus); surplus feeds elites whose overproduction breeds
instability (the secular cycle); cohesion builds on hard frontiers and decays in
fat imperial cores (asabiyya); power = cohesion x mass x tech drives expansion and
conquest; technology diffuses along contact; plague and climate deal shocks. Rise
and fall fall out of the loops. The Chronicler (separate) only names and narrates
what this produces.
"""

import math
import random

from worldsim.arbiter import make_event
from worldsim.memory import create_empty_memory
from worldsim.config import (
    K_PER_FOOD, TRADE_K_FACTOR, TECH_K_BONUS, POP_GROWTH, STARVE_RATE, EXTINCT_POP,
    ELITE_SHARE_0, ELITE_GROWTH, ELITE_OVERPRODUCE, INSTAB_GAIN, INSTAB_DECAY,
    COLLAPSE_THRESHOLD, ASAB_GAIN, ASAB_DECAY, ASAB_STRIFE_DECAY,
    EXPANSION_HUNGER, COHESION_EXPAND, CONQUEST_EDGE, DIFFUSE_RATE, INNOVATE_CHANCE,
    PLAGUE_CHANCE, CLIMATE_CHANCE,
)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _living(world):
    return [cid for cid, c in world["cultures"].items()
            if not c.get("fallen") and c["population"] > 0]


def _regions_of(world, cid):
    return [rid for rid, r in world["regions"].items() if r["occupant"] == cid]


def _region_k(region):
    y = region.get("yield", {})
    return (y.get("food", 0) + TRADE_K_FACTOR * y.get("wealth", 0)) * K_PER_FOOD


def carrying_capacity(world, cid):
    c = world["cultures"][cid]
    base = sum(_region_k(world["regions"][rid]) for rid in _regions_of(world, cid))
    return base * (1.0 + TECH_K_BONUS * c.get("tech_level", 0.0))


def reachable(world, cid):
    """Regions a polity can act into: held + land-adjacent, plus coastal if sea-capable."""
    regions = world["regions"]
    held = _regions_of(world, cid)
    reach = set(held)
    for rid in held:
        reach.update(regions[rid].get("adjacent", []))
    c = world["cultures"][cid]
    if "sea" in c.get("reach", ["land"]) and any(regions[rid].get("coastal") for rid in held):
        reach.update(rid for rid, r in regions.items() if r.get("coastal"))
    return reach


def foreign_neighbours(world, cid):
    """Other living polities whose land borders this one's reach."""
    reach = reachable(world, cid)
    out = set()
    for rid in reach:
        occ = world["regions"][rid]["occupant"]
        if occ and occ != cid and not world["cultures"].get(occ, {}).get("fallen"):
            out.add(occ)
    return out


def culture_distance(a, b):
    va, vb = a.get("culture_vec", [0, 0, 0]), b.get("culture_vec", [0, 0, 0])
    d = math.sqrt(sum((x - y) ** 2 for x, y in zip(va, vb)))
    return min(1.0, d / 1.4)  # normalise: max distance in unit cube ~1.73


def power(world, cid):
    c = world["cultures"][cid]
    return c.get("cohesion", 0.4) * (c["population"] / 1000.0) * (1.0 + 0.3 * c.get("tech_level", 0.0))


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


# --------------------------------------------------------------------------- #
# loops
# --------------------------------------------------------------------------- #
def population_step(world):
    """Malthusian population against geographic carrying capacity."""
    events = []
    for cid in _living(world):
        c = world["cultures"][cid]
        K = carrying_capacity(world, cid)
        N = c["population"]
        c["k"] = K
        if K <= 0:  # landless: a people without ground bleeds away
            deaths = round(N * STARVE_RATE)
            c["population"] = max(0, N - deaths)
            c["k_ratio"] = 9.9
            continue
        ratio = N / K
        # logistic growth toward K
        N2 = N + POP_GROWTH * N * (1.0 - ratio)
        if N2 > K:  # overshoot is paid in famine
            N2 = N2 - STARVE_RATE * (N2 - K)
        N2 = max(0, round(N2))
        c["population"] = N2
        c["k_ratio"] = N2 / K if K else 9.9
        if ratio > 1.15 and N2 < N:
            events.append(make_event(
                world, "famine",
                f"{c['name']} outgrew its land (folk {N2:,} against a capacity of {round(K):,}); the surplus people starved.",
                [cid]))
    return events


def secular_step(world):
    """Elites overproduce; pressure builds toward collapse (handled in fragment_step)."""
    for cid in _living(world):
        c = world["cultures"][cid]
        N = max(1, c["population"])
        ratio = c.get("k_ratio", 0.0)
        surplus = max(0.0, 1.0 - ratio)
        # elites multiply in good times and keep multiplying even in bad (overproduction)
        E = c.get("elites", N * ELITE_SHARE_0)
        E = E * (1.0 + ELITE_GROWTH * surplus + ELITE_OVERPRODUCE)
        E = min(E, N * 0.25)
        c["elites"] = E
        elite_pressure = (E / N) / ELITE_SHARE_0          # >1 == more elites per head than healthy
        pressure = ratio + 0.5 * max(0.0, elite_pressure - 1.0)
        W = c.get("instability", 0.0)
        if pressure > 1.0:
            W += INSTAB_GAIN * (pressure - 1.0)
        else:
            W = max(0.0, W - INSTAB_DECAY)
        c["instability"] = W
    return []


def asabiyya_step(world):
    """Cohesion rises on hard, alien, threatening frontiers; decays with size and strife."""
    for cid in _living(world):
        c = world["cultures"][cid]
        A = c.get("cohesion", 0.4)
        fi = 0.0
        for oid in foreign_neighbours(world, cid):
            dist = culture_distance(c, world["cultures"][oid])
            threat = power(world, oid) / max(0.1, power(world, cid))
            fi += dist * (0.5 + 0.5 * min(2.0, threat))
        size = len(_regions_of(world, cid))
        gain = ASAB_GAIN * min(1.0, fi) * (1.0 - A)
        decay = ASAB_DECAY * (1.0 + 0.25 * size) + ASAB_STRIFE_DECAY * c.get("instability", 0.0)
        c["cohesion"] = _clamp(A + gain - decay, 0.03, 1.0)
    return []


def expansion_step(world):
    """Power and land-hunger drive settlement and conquest. One move per polity."""
    events = []
    for cid in sorted(_living(world), key=lambda x: -power(world, x)):
        c = world["cultures"][cid]
        ratio = c.get("k_ratio", 0.0)
        hungry = ratio > EXPANSION_HUNGER
        martial = c.get("cohesion", 0) > COHESION_EXPAND
        if not (hungry or martial):
            continue
        reach = reachable(world, cid)
        targets = [rid for rid in reach if world["regions"][rid]["occupant"] != cid]
        if not targets:
            continue
        empty = [rid for rid in targets if world["regions"][rid]["occupant"] is None]
        if empty and hungry:
            best = max(empty, key=lambda r: _region_k(world["regions"][r]))
            world["regions"][best]["occupant"] = cid
            world["regions"][best]["populace"] = cid
            events.append(make_event(
                world, "settle",
                f"Land-hungry {c['name']} spread into {world['regions'][best]['name']}.",
                [cid]))
            continue
        # else attempt conquest of the weakest reachable enemy region
        enemy = [(rid, world["regions"][rid]["occupant"]) for rid in targets
                 if world["regions"][rid]["occupant"]]
        enemy = [(rid, oid) for rid, oid in enemy if not world["cultures"].get(oid, {}).get("fallen")]
        if not enemy:
            continue
        rid, defender_id = min(enemy, key=lambda t: power(world, t[1]))
        atk, dfn = power(world, cid), power(world, defender_id)
        defender = world["cultures"][defender_id]
        if atk > CONQUEST_EDGE * max(0.1, dfn):
            # seize the region; populace stays (foreign rule -> future rebellion fuel)
            world["regions"][rid]["occupant"] = cid
            loss_d = round(defender["population"] * 0.10)
            loss_a = round(c["population"] * 0.04)
            defender["population"] = max(0, defender["population"] - loss_d)
            c["population"] = max(0, c["population"] - loss_a)
            c["instability"] = c.get("instability", 0) + 0.10  # overstretch
            c["cohesion"] = _clamp(c.get("cohesion", 0.4) - 0.03, 0.03, 1.0)
            c["relations"][defender_id] = c["relations"].get(defender_id, 0) - 30
            defender["relations"][cid] = defender["relations"].get(cid, 0) - 30
            events.append(make_event(
                world, "conquest",
                f"{c['name']} conquered {world['regions'][rid]['name']} from {defender['name']} "
                f"({loss_d:,} of the defenders fell).",
                [cid, defender_id]))
        else:
            events.append(make_event(
                world, "war_repelled",
                f"{c['name']} assailed {defender['name']} at {world['regions'][rid]['name']} but was thrown back.",
                [cid, defender_id]))
    return events


def diffusion_step(world):
    """Technology spreads from advanced neighbours; innovation bubbles up in big, settled polities."""
    events = []
    new_levels = {}
    for cid in _living(world):
        c = world["cultures"][cid]
        T = c.get("tech_level", 0.0)
        neigh_T = [world["cultures"][o].get("tech_level", 0.0) for o in foreign_neighbours(world, cid)]
        target = max([T] + neigh_T)
        T2 = T + DIFFUSE_RATE * (target - T)
        # endogenous innovation, likelier in larger, more settled societies
        scale = min(1.0, c["population"] / 60000.0)
        if random.random() < INNOVATE_CHANCE * (0.4 + scale):
            T2 += 1.0
            events.append(make_event(
                world, "innovation",
                f"A new art took root among {c['name']} (their craft deepened).",
                [cid]))
        new_levels[cid] = T2
    for cid, T in new_levels.items():
        world["cultures"][cid]["tech_level"] = T
    return events


def shocks_step(world):
    """Plague (spreads on contact) and climate swings (move carrying capacity)."""
    events = []
    living = _living(world)
    if not living:
        return events
    if random.random() < PLAGUE_CHANCE:
        # a plague favours the well-connected
        victim = max(living, key=lambda c: len(foreign_neighbours(world, c)) + 1)
        vc = world["cultures"][victim]
        dead = round(vc["population"] * 0.18)
        vc["population"] = max(0, vc["population"] - dead)
        hit = [victim]
        for oid in foreign_neighbours(world, victim):
            oc = world["cultures"][oid]
            d2 = round(oc["population"] * 0.09)
            oc["population"] = max(0, oc["population"] - d2)
            hit.append(oid)
        events.append(make_event(
            world, "plague",
            f"A pestilence broke out among {vc['name']} ({dead:,} dead) and ran down the trade-roads to its neighbours.",
            hit))
    if random.random() < CLIMATE_CHANCE:
        # a climate swing raises or lowers a region's yield for good
        rid = random.choice(list(world["regions"].keys()))
        region = world["regions"][rid]
        good = random.random() < 0.5
        delta = 4 if good else -4
        region["yield"]["food"] = max(0, region["yield"].get("food", 0) + delta)
        occ = region["occupant"]
        events.append(make_event(
            world, "climate",
            (f"A run of fertile years enriched {region['name']}." if good
             else f"The climate turned against {region['name']}; its fields withered."),
            [occ] if occ else []))
    return events


def fragment_step(world, seeds, memory):
    """The secular cycle's payoff: high instability fractures a polity. Population
    crashes, elites are purged, and peripheral provinces break away as new peoples.
    Returns (events, newborn_ids) — newborns are provisional, for the Chronicler to name."""
    events = []
    newborns = []
    for cid in list(_living(world)):
        c = world["cultures"][cid]
        if c.get("instability", 0.0) < COLLAPSE_THRESHOLD:
            continue
        held = _regions_of(world, cid)
        N = c["population"]
        crash = round(N * 0.22)
        c["population"] = max(0, N - crash)
        c["elites"] = c.get("elites", 0) * 0.5
        c["instability"] = c.get("instability", 0) * 0.35
        c["cohesion"] = _clamp(c.get("cohesion", 0.4) - 0.18, 0.03, 1.0)

        if len(held) > 1:
            # peripheral regions break away (prefer foreign-populace and capital-distant)
            cap = c["home_region"]
            periphery = sorted(
                [r for r in held if r != cap],
                key=lambda r: (world["regions"][r].get("populace") == cid, r != cap),
            )
            take = periphery[: max(1, len(periphery) // 2)]
            if take:
                share = round(c["population"] * (len(take) / max(1, len(held))))
                c["population"] = max(0, c["population"] - share)
                new_id = _spawn_successor(world, seeds, memory, parent=cid,
                                          regions=take, population=max(1000, share))
                newborns.append(new_id)
                events.append(make_event(
                    world, "fragmentation",
                    f"{c['name']} fell into a time of troubles: {crash:,} dead, the realm convulsed, "
                    f"and its outer provinces broke away.",
                    [cid, new_id]))
                continue
        events.append(make_event(
            world, "time_of_troubles",
            f"{c['name']} was wracked by civil strife; {crash:,} perished before order was restored.",
            [cid]))
    return events, newborns


def extinction_step(world):
    """Peoples with no land and too few souls pass out of history."""
    events = []
    for cid, c in world["cultures"].items():
        if c.get("fallen"):
            continue
        if c["population"] <= EXTINCT_POP and not _regions_of(world, cid):
            c["fallen"] = True
            events.append(make_event(
                world, "extinction",
                f"{c['name']} dwindled to nothing and passed out of all memory.",
                [cid]))
    return events


# --------------------------------------------------------------------------- #
# successor creation
# --------------------------------------------------------------------------- #
def _spawn_successor(world, seeds, memory, parent, regions, population):
    """Create a provisional breakaway polity holding `regions`. The Chronicler names it."""
    base = f"succ{world.get('tick', 0)}_{parent}"
    cid = base
    n = 2
    while cid in world["cultures"]:
        cid = f"{base}_{n}"
        n += 1
    pc = world["cultures"][parent]
    # mutate the parent's culture vector so the child is recognizably its own
    vec = [_clamp(v + random.uniform(-0.25, 0.25), 0.0, 1.0) for v in pc.get("culture_vec", [0.5, 0.5, 0.5])]
    others = list(world["cultures"].keys())
    world["cultures"][cid] = {
        "name": f"the breakaway of {world['regions'][regions[0]]['name']}",
        "home_region": regions[0],
        "population": population,
        "ruler": "an unnamed first leader",
        "house": "a new line",
        "reach": list(pc.get("reach", ["land"])),
        "tech_level": pc.get("tech_level", 0.0),
        "cohesion": 0.7,            # newborn successor states are fiercely cohesive
        "elites": int(population * 0.02),
        "instability": 0.0,
        "culture_vec": vec,
        "k": 0.0, "k_ratio": 0.0,
        "tech": [], "institutions": [], "religion": pc.get("religion"),
        "parent": parent,
        "born_tick": world.get("tick", 0),
        "fallen": False,
        "needs_naming": True,       # flag for the Chronicler
        "relations": {o: 0 for o in others},
    }
    for o in others:
        world["cultures"][o]["relations"][cid] = 0
    world["cultures"][cid]["relations"][parent] = -50
    world["cultures"][parent]["relations"][cid] = -30
    for rid in regions:
        world["regions"][rid]["occupant"] = cid
        world["regions"][rid]["populace"] = cid
    seeds[cid] = {"id": cid, "name": world["cultures"][cid]["name"]}
    memory[cid] = create_empty_memory(cid)
    return cid


# --------------------------------------------------------------------------- #
# the generation
# --------------------------------------------------------------------------- #
def run_dynamics(world, seeds, memory):
    """Advance the structural world one generation. Returns (events, newborn_ids)."""
    events = []
    events += population_step(world)
    events += secular_step(world)
    events += asabiyya_step(world)
    events += expansion_step(world)
    events += diffusion_step(world)
    events += shocks_step(world)
    frag_events, newborns = fragment_step(world, seeds, memory)
    events += frag_events
    events += extinction_step(world)
    return events, newborns

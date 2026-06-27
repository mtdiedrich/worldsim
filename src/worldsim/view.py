"""Build filtered views of the world for each culture."""

import copy


def build_filtered_view(world: dict, culture_id: str) -> dict:
    """
    Build a filtered view of the world that a culture can see.
    
    The agent sees:
    - Its own full culture record
    - Records of regions it occupies + adjacent regions
    - Limited info about other cultures in visible regions
    - Last 5 global events
    - Current tick
    
    Args:
        world: Full world state
        culture_id: The culture to build a view for
        
    Returns:
        Filtered view dict
    """
    culture = world["cultures"][culture_id]
    home_region = culture["home_region"]
    
    # Find all regions this culture occupies
    occupied_regions = {home_region}
    for region_id, region in world["regions"].items():
        if region.get("occupant") == culture_id:
            occupied_regions.add(region_id)
    
    # Find adjacent regions (adjacent to any occupied region)
    visible_regions = set(occupied_regions)
    for region_id in occupied_regions:
        region = world["regions"][region_id]
        for adj_id in region.get("adjacent", []):
            visible_regions.add(adj_id)
    
    # Build visible regions dict
    visible_regions_dict = {}
    for region_id in visible_regions:
        region = world["regions"][region_id]
        visible_regions_dict[region_id] = {
            "name": region["name"],
            "terrain": region["terrain"],
            "resources": copy.copy(region["resources"]),
            "occupant": region["occupant"],
            "adjacent": region["adjacent"],
        }
    
    # Build visible cultures dict (other cultures in visible regions)
    visible_cultures = {}
    for region_id in visible_regions:
        region = world["regions"][region_id]
        occupant = region.get("occupant")
        if occupant and occupant != culture_id:
            if occupant not in visible_cultures:
                other_culture = world["cultures"][occupant]
                visible_cultures[occupant] = {
                    "name": other_culture["name"],
                    "home_region": other_culture["home_region"],
                    "relations": other_culture["relations"].get(culture_id, 0),
                }
    
    # Get last 5 events
    recent_events = world["event_log"][-5:] if world["event_log"] else []
    
    return {
        "tick": world["tick"],
        "culture": {
            "id": culture["id"] if "id" in culture else culture_id,
            "name": culture["name"],
            "home_region": culture["home_region"],
            "population": culture["population"],
            "resources": copy.copy(culture["resources"]),
            "tech": copy.copy(culture["tech"]),
            "relations": copy.copy(culture["relations"]),
        },
        "regions": visible_regions_dict,
        "other_cultures": visible_cultures,
        "recent_events": [
            {
                "tick": e["tick"],
                "type": e["type"],
                "description": e["description"],
                "involved": e["involved"],
            }
            for e in recent_events
        ],
    }

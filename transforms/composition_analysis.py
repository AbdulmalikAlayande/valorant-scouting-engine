"""
Extracts team composition patterns and agent synergies.
Answers: "What comps do they run?" and "What should we expect?"
"""

from collections import Counter
from typing import Dict, Any, List

from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def extract_default_comps(series_state_data: Dict[str, Any],
                          top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Extract the team's most-used agent compositions.

    Args:
        series_state_data: Output from ingest_series_state()
        top_n: Number of top compositions to return (default 3)

    Returns:
        [
            {
                "composition": ["jett", "raze", "omen", "cypher", "sova"],
                "games": 5,
                "wins": 4,
                "win_rate": 0.80,
                "maps": ["Ascent", "Haven"]
            },
            ...
        ]
    """
    if not series_state_data or not series_state_data.get('series'):
        _logger.warning("No series state data for composition extraction")
        return []

    series = series_state_data['series']
    compositions_data = series.get('compositions', [])

    if not compositions_data:
        _logger.warning("No compositions data in series state")
        return []

    # Group compositions and calculate win rates
    comp_stats = {}

    for comp_entry in compositions_data:
        team_name = comp_entry.get('team_name')
        map_name = comp_entry.get('map_name')
        composition = tuple(sorted(comp_entry.get('composition', [])))  # Sort for consistency
        count = comp_entry.get('count', 0)

        # Create a unique key for this comp
        comp_key = composition

        if comp_key not in comp_stats:
            comp_stats[comp_key] = {
                "composition": list(composition),
                "games": 0,
                "wins": 0,  # We don't have win data in the current structure
                "maps": []
            }

        comp_stats[comp_key]["games"] += count
        if map_name and map_name not in comp_stats[comp_key]["maps"]:
            comp_stats[comp_key]["maps"].append(map_name)

    # Convert to list and sort by frequency
    comps_list = list(comp_stats.values())
    comps_list.sort(key=lambda c: c['games'], reverse=True)

    # Add win rates (placeholder - would need game outcomes)
    for comp in comps_list:
        comp['win_rate'] = 0.0  # Not available without game outcome data
        comp['note'] = "Win rate calculation requires game outcome data"

    return comps_list[:top_n]


def calculate_comp_win_rates(series_state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculate win rates for each composition.

    NOTE: This requires cross-referencing with game outcomes,
    which is not directly available in the series_state structure.

    Args:
        series_state_data: Output from ingest_series_state()

    Returns:
        List of compositions with win rates
    """
    # This would require analyzing individual games and their outcomes
    # Current series_state structure provides compositions but not outcomes per comp

    _logger.warning("Comp win rate calculation requires game outcome data - not implemented")

    return []


def identify_agent_synergies(series_state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify which agents are frequently picked together.

    Args:
        series_state_data: Output from ingest_series_state()

    Returns:
        [
            {
                "agent_pair": ["jett", "omen"],
                "games_together": 12,
                "synergy_score": 0.85 # How often they appear together
            },
            ...
        ]
    """
    if not series_state_data or not series_state_data.get('series'):
        _logger.warning("No series state data for synergy analysis")
        return []

    series = series_state_data['series']
    compositions_data = series.get('compositions', [])

    if not compositions_data:
        return []

    # Count agent pairs
    pair_counts = Counter()
    total_games_per_agent = Counter()

    for comp_entry in compositions_data:
        composition = comp_entry.get('composition', [])
        count = comp_entry.get('count', 1)

        # Count each agent appearance
        for agent in composition:
            total_games_per_agent[agent] += count

        # Count each unique pair
        for i, agent1 in enumerate(composition):
            for agent2 in composition[i + 1:]:
                pair = tuple(sorted([agent1, agent2]))
                pair_counts[pair] += count

    # Calculate synergy scores
    synergies = []
    for (agent1, agent2), games_together in pair_counts.most_common(10):
        # Synergy = how often they appear together / min(games of agent1, games of agent2)
        min_games = min(total_games_per_agent[agent1], total_games_per_agent[agent2])
        synergy_score = games_together / min_games if min_games > 0 else 0.0

        synergies.append({
            "agent_pair": [agent1, agent2],
            "games_together": games_together,
            "synergy_score": round(synergy_score, 3)
        })

    return synergies


def get_agent_pick_rates(series_state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get overall agent pick rates for the team.

    Args:
        series_state_data: Output from ingest_series_state()

    Returns:
        [
            {
                "agent": "jett",
                "games": 15,
                "pick_rate": 0.75 # % of games this agent was picked
            },
            ...
        ]
        Sorted by pick rate descending
    """
    if not series_state_data or not series_state_data.get('series'):
        _logger.warning("No series state data for agent pick rates")
        return []

    series = series_state_data['series']
    agent_picks_data = series.get('agent_picks', [])

    if not agent_picks_data:
        _logger.warning("No agent picks data in series state")
        return []

    # Sort by pick rate
    sorted_picks = sorted(agent_picks_data, key=lambda a: a.get('pick_rate_pct', 0), reverse=True)

    # Format output
    pick_rates = []
    for agent_data in sorted_picks:
        pick_rates.append({
            "agent": agent_data.get('agent'),
            "games": agent_data.get('count', 0),
            "pick_rate": agent_data.get('pick_rate_pct', 0.0) / 100
        })

    return pick_rates


def identify_map_specific_comps(series_state_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identify which compositions are used on which maps.

    Args:
        series_state_data: Output from ingest_series_state()

    Returns:
        {
            "Ascent": [
                {
                    "composition": ["jett", "omen", ...],
                    "games": 5
                }
            ],
            "Bind": [...]
        }
    """
    if not series_state_data or not series_state_data.get('series'):
        _logger.warning("No series state data for map-specific comps")
        return {}

    series = series_state_data['series']
    compositions_data = series.get('compositions', [])

    if not compositions_data:
        return {}

    # Group by map
    map_comps = {}

    for comp_entry in compositions_data:
        map_name = comp_entry.get('map_name')
        if not map_name:
            continue

        composition = comp_entry.get('composition', [])
        count = comp_entry.get('count', 0)

        if map_name not in map_comps:
            map_comps[map_name] = []

        map_comps[map_name].append({
            "composition": composition,
            "games": count
        })

    # Sort each map's comps by frequency
    for map_name in map_comps:
        map_comps[map_name].sort(key=lambda c: c['games'], reverse=True)

    return map_comps


def get_composition_analysis_summary(series_state_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function: Get ALL composition metrics in one call.

    Args:
        series_state_data: Output from ingest_series_state()

    Returns:
        Dict containing all composition analysis metrics
    """
    return {
        "default_comps": extract_default_comps(series_state_data),
        "agent_pick_rates": get_agent_pick_rates(series_state_data),
        "agent_synergies": identify_agent_synergies(series_state_data),
        "map_specific_comps": identify_map_specific_comps(series_state_data)
    }

"""
Extracts map-specific performance metrics for veto strategy.
Answers: "Which maps should we ban/pick?"
"""

from typing import Dict, Any, List, Optional
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def calculate_map_win_rates(team_game_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculate win rates per map.

    Args:
        team_game_stats: Output from ingest_team_game_statistics()

    Returns:
        [
            {
                "map_name": "Ascent",

                "games": 12,

                "wins": 10,

                "losses": 2,

                "win_rate": 0.83

            },

            ...
        ]

        Sorted by win_rate descending (best maps first)
    """
    if not team_game_stats or not team_game_stats.get('records'):
        _logger.warning("No team game stats for map win rate calculation")
        return []

    # NOTE: team_game_stats might contain mixed record types. i.e., ONE aggregated record or MULTIPLE map-specific records
    # I need to handle both cases, And I did that by filtering out records missing 'map_filter' as they represent global
    # aggregates rather than specific map data.

    records = team_game_stats['records']
    map_stats = []

    for record in records:
        map_filter = record.get('map_filter')
        if not map_filter:
            # This is an aggregated record (all maps combined)
            # Can't break it down by map from this
            continue

        game_count = record.get('game_count', 0)
        games_won = record.get('games_won', 0)
        games_lost = game_count - games_won
        win_rate = record.get('game_win_rate', 0.0) / 100

        map_stats.append({
            "map_name": map_filter,
            "games": game_count,
            "wins": games_won,
            "losses": games_lost,
            "win_rate": round(win_rate, 3)
        })

    # Sort by win_rate descending (best maps first)
    map_stats.sort(key=lambda x: x['win_rate'], reverse=True)

    return map_stats


def identify_veto_strategy(map_win_rates: List[Dict[str, Any]],
                           min_games: int = 3) -> Dict[str, Any]:
    """
    Identify which maps to ban/pick based on performance.

    Args:
        map_win_rates: Output from calculate_map_win_rates()
        min_games: Minimum games on a map to consider it (default 3)

    Returns:
        {
            "stronghold": {
                "map_name": "Ascent",
                "win_rate": 0.83,
                "games": 12,
                "recommendation": "Pick this map"
            },
            "permaban": {
                "map_name": "Icebox",
                "win_rate": 0.30,
                "games": 10,
                "recommendation": "Ban this map"
            },
            "playable_maps": ["Ascent", "Bind", "Haven"],
            "avoid_maps": ["Icebox", "Breeze"]
        }
    """
    if not map_win_rates:
        _logger.warning("No map win rates provided for veto strategy")
        return {
            "stronghold": None,
            "permaban": None,
            "playable_maps": [],
            "avoid_maps": []
        }

    # Filter maps with enough games
    significant_maps = [m for m in map_win_rates if m['games'] >= min_games]

    if not significant_maps:
        _logger.warning(f"No maps with >= {min_games} games played")
        return {
            "stronghold": None,
            "permaban": None,
            "playable_maps": [],
            "avoid_maps": [],
            "note": f"Need at least {min_games} games per map for analysis"
        }

    # Stronghold = best win rate
    stronghold = significant_maps[0]  # Already sorted descending

    # Permaban = worst win rate
    permaban = significant_maps[-1]

    # Playable maps = win rate >= 50%
    playable_maps = [m['map_name'] for m in significant_maps if m['win_rate'] >= 0.50]

    # Avoid maps = win rate < 50%
    avoid_maps = [m['map_name'] for m in significant_maps if m['win_rate'] < 0.50]

    return {
        "stronghold": {
            "map_name": stronghold['map_name'],
            "win_rate": stronghold['win_rate'],
            "games": stronghold['games'],
            "recommendation": f"Pick {stronghold['map_name']} ({stronghold['win_rate'] * 100:.1f}% WR)"
        },
        "permaban": {
            "map_name": permaban['map_name'],
            "win_rate": permaban['win_rate'],
            "games": permaban['games'],
            "recommendation": f"Ban {permaban['map_name']} ({permaban['win_rate'] * 100:.1f}% WR)"
        },
        "playable_maps": playable_maps,
        "avoid_maps": avoid_maps
    }


def extract_map_side_performance(team_game_stats: Dict[str, Any],
                                 map_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract attack/defense performance on a specific map.

    NOTE: This requires fetching team_game_stats with a map_filter set.
    The current ingestion doesn't provide side-split per map.

    Args:
        team_game_stats: Output from ingest_team_game_statistics(map_filter="Ascent")
        map_name: Name of the map (for validation)

    Returns:
        {
            "map_name": "Ascent",
            "attack_wr": 0.45,
            "defense_wr": 0.75,
            "side_bias": "defense"
        }
    """
    if not team_game_stats or not team_game_stats.get('records'):
        _logger.warning("No team game stats for map side performance")
        return {
            "map_name": map_name or "unknown",
            "attack_wr": 0.0,
            "defense_wr": 0.0,
            "side_bias": "unknown",
            "note": "Data not available - need map-specific query"
        }

    record = team_game_stats['records'][0]

    # GRID Stats Feed doesn't provide attack/defense split at game level
    # This would require analyzing Series State data (round-by-round)
    # For now, returning placeholder

    return {
        "map_name": record.get('map_filter', map_name or "unknown"),
        "attack_wr": 0.0,  # Not available in current data
        "defense_wr": 0.0,  # Not available in current data
        "side_bias": "unknown",
        "note": "Side-split data not available from Stats Feed API - requires Series State analysis"
    }


def get_map_pool_depth(map_win_rates: List[Dict[str, Any]],
                       threshold: float = 0.45) -> Dict[str, Any]:
    """
    Analyze how many maps a team is competitive on.

    Args:
        map_win_rates: Output from calculate_map_win_rates()
        threshold: Minimum win rate to consider "competitive" (default 0.45 = 45%)

    Returns:
        {
            "competitive_maps": 5,
            "total_maps_played": 7,
            "pool_depth": "strong", # "strong" (5+), "average" (3-4), "weak" (1-2)
            "one_trick_risk": False # True if only 1-2 competitive maps
        }
    """
    if not map_win_rates:
        return {
            "competitive_maps": 0,
            "total_maps_played": 0,
            "pool_depth": "unknown",
            "one_trick_risk": True
        }

    total_maps = len(map_win_rates)
    competitive_maps = len([m for m in map_win_rates if m['win_rate'] >= threshold])

    # Determine pool depth category
    if competitive_maps >= 5:
        pool_depth = "strong"
    elif competitive_maps >= 3:
        pool_depth = "average"
    else:
        pool_depth = "weak"

    one_trick_risk = competitive_maps <= 2

    return {
        "competitive_maps": competitive_maps,
        "total_maps_played": total_maps,
        "pool_depth": pool_depth,
        "one_trick_risk": one_trick_risk,
        "threshold_used": threshold
    }


def get_map_analysis_summary(team_game_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function: Get ALL map-level metrics in one call.

    Args:
        team_game_stats: Output from ingest_team_game_statistics()

    Returns:
        Dict containing all map analysis metrics
    """
    map_win_rates = calculate_map_win_rates(team_game_stats)

    return {
        "map_win_rates": map_win_rates,
        "veto_strategy": identify_veto_strategy(map_win_rates),
        "map_pool_depth": get_map_pool_depth(map_win_rates)
    }

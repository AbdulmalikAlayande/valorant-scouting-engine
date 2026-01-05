"""
Extracts player-level metrics for Micro analysis.
Answers: "Who do we target?" and "Who is their star player?"
"""

from typing import Dict, Any, List, Optional
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


# ============================================================================
# MICRO-LEVEL ANALYSIS (Individual Player Performance)
# ============================================================================

def identify_star_player(player_stats_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Identify the primary carry/star player.

    Criteria:
    - Highest K/D ratio
    - Highest kills per game
    - Highest first kill percentage

    Args:
        player_stats_list: List of outputs from ingest_player_statistics()

    Returns:
        {
            "player_id": "2512",
            "nickname": "TenZ",
            "kd_ratio": 1.45,
            "kills_per_game": 18.2,
            "first_kill_pct": 0.32,
            "games_played": 25,
            "reason": "Highest K/D and kills per game"
        }
        or None if no valid data
    """
    if not player_stats_list:
        _logger.warning("No player stats provided for star player identification")
        return None

    valid_players = []

    for player_data in player_stats_list:
        if not player_data.get('records') or not player_data['records']:
            continue

        record = player_data['records'][0]

        # Extract combat metrics
        combat = record.get('combat', {})
        games_data = record.get('games', {})

        kills_data = combat.get('kills', {})
        deaths_data = combat.get('deaths', {})

        kills_total = kills_data.get('total', 0)
        deaths_total = deaths_data.get('total', 1)  # Avoid division by zero
        kills_avg = kills_data.get('avg', 0.0)

        games_count = games_data.get('count', 0)
        first_kill_pct = games_data.get('first_kill_percentage', 0.0)

        # Calculate K/D
        kd_ratio = round(kills_total / deaths_total, 2) if deaths_total > 0 else 0.0

        # Only consider players with significant data
        if games_count < 3:
            continue

        valid_players.append({
            "player_id": record.get('player_id'),
            "nickname": None,  # Not available in current data structure
            "kd_ratio": kd_ratio,
            "kills_per_game": round(kills_avg, 2),
            "first_kill_pct": first_kill_pct / 100,
            "games_played": games_count
        })

    if not valid_players:
        _logger.warning("No valid player data for star identification")
        return None

    # Sort by K/D ratio (primary), then kills per game (secondary)
    valid_players.sort(key=lambda p: (p['kd_ratio'], p['kills_per_game']), reverse=True)

    star = valid_players[0]
    star['reason'] = "Highest K/D and kills per game"

    return star


def identify_weak_link(player_stats_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Identify the weakest performer (potential target).

    Criteria:
    - Lowest K/D ratio
    - Highest isolated death rate (deaths without contributing)
    - Lowest consistency

    Args:
        player_stats_list: List of outputs from ingest_player_statistics()

    Returns:
        {
            "player_id": "9876",
            "nickname": "PlayerX",
            "kd_ratio": 0.78,
            "deaths_per_game": 14.5,
            "games_played": 20,
            "reason": "Lowest K/D and highest deaths per game"
        }
        or None if no valid data
    """
    if not player_stats_list:
        _logger.warning("No player stats provided for weak link identification")
        return None

    valid_players = []

    for player_data in player_stats_list:
        if not player_data.get('records') or not player_data['records']:
            continue

        record = player_data['records'][0]

        # Extract combat metrics
        combat = record.get('combat', {})
        games_data = record.get('games', {})

        kills_data = combat.get('kills', {})
        deaths_data = combat.get('deaths', {})

        kills_total = kills_data.get('total', 0)
        deaths_total = deaths_data.get('total', 1)
        deaths_avg = deaths_data.get('avg', 0.0)

        games_count = games_data.get('count', 0)

        # Calculate K/D
        kd_ratio = round(kills_total / deaths_total, 2) if deaths_total > 0 else 0.0

        # Only consider players with significant data
        if games_count < 3:
            continue

        valid_players.append({
            "player_id": record.get('player_id'),
            "nickname": None,
            "kd_ratio": kd_ratio,
            "deaths_per_game": round(deaths_avg, 2),
            "games_played": games_count
        })

    if not valid_players:
        _logger.warning("No valid player data for weak link identification")
        return None

    # Sort by K/D ratio ascending (worst first)
    valid_players.sort(key=lambda p: p['kd_ratio'])

    weak_link = valid_players[0]
    weak_link['reason'] = "Lowest K/D and highest deaths per game"

    return weak_link


def extract_agent_pools(player_stats_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract each player's agent pool (top 2-3 most played agents).

    Args:
        player_stats_list: List of outputs from ingest_player_statistics()

    Returns:
        [
            {
                "player_id": "2512",
                "nickname": "TenZ",
                "top_agents": [
                    {"agent": "Jett", "games": 18, "percentage": 0.72},
                    {"agent": "Reyna", "games": 5, "percentage": 0.20}
                ],
                "agent_pool_size": 2,
                "specialist": True  # True if >70% on one agent
            },
            ...
        ]
    """
    if not player_stats_list:
        _logger.warning("No player stats provided for agent pool extraction")
        return []

    player_agent_pools = []

    for player_data in player_stats_list:
        if not player_data.get('records') or not player_data['records']:
            continue

        record = player_data['records'][0]
        player_id = record.get('player_id')

        # Extract agent data from raw response
        # Note: The ingestion doesn't currently parse character data
        # We need to extract it from the raw field
        raw_data = record.get('raw', {})
        game_data = raw_data.get('game', {})

        # This would require parsing the GRID API structure
        # For now, return placeholder structure
        player_agent_pools.append({
            "player_id": player_id,
            "nickname": None,
            "top_agents": [],  # Need to parse from raw data
            "agent_pool_size": 0,
            "specialist": False,
            "note": "Agent pool extraction needs raw data parsing"
        })

    return player_agent_pools


def calculate_player_impact_score(player_stats: Dict[str, Any]) -> float:
    """
    Calculate an overall "impact score" for a player.

    Formula: (K/D * 0.4) + (First Kill % * 0.3) + (Win Rate * 0.3)

    Args:
        player_stats: Single player's stats from ingest_player_statistics()

    Returns:
        Impact score (0.0 to 1.0+)
    """
    if not player_stats.get('records') or not player_stats['records']:
        return 0.0

    record = player_stats['records'][0]

    # Extract metrics
    combat = record.get('combat', {})
    games_data = record.get('games', {})

    kills = combat.get('kills', {}).get('total', 0)
    deaths = combat.get('deaths', {}).get('total', 1)
    kd_ratio = kills / deaths if deaths > 0 else 0.0

    first_kill_pct = games_data.get('first_kill_percentage', 0.0) / 100
    win_rate = games_data.get('win_rate', 0.0) / 100

    # Normalize K/D to 0-1 scale (1.0 K/D = 0.5, 2.0 K/D = 1.0)
    normalized_kd = min(kd_ratio / 2.0, 1.0)

    # Calculate weighted score
    impact_score = (normalized_kd * 0.4) + (first_kill_pct * 0.3) + (win_rate * 0.3)

    return round(impact_score, 3)


def rank_players_by_performance(player_stats_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank all players by overall performance.

    Args:
        player_stats_list: List of outputs from ingest_player_statistics()

    Returns:
        List of player rankings with metrics
        [
            {
                "rank": 1,
                "player_id": "2512",
                "kd_ratio": 1.45,
                "impact_score": 0.82,
                "tier": "star"
            },
            ...
        ]
        Tiers: "star" (top 20%), "average" (middle 60%), "weak" (bottom 20%)
    """
    if not player_stats_list:
        return []

    ranked = []

    for player_data in player_stats_list:
        if not player_data.get('records') or not player_data['records']:
            continue

        record = player_data['records'][0]
        player_id = record.get('player_id')

        combat = record.get('combat', {})
        kills = combat.get('kills', {}).get('total', 0)
        deaths = combat.get('deaths', {}).get('total', 1)
        kd_ratio = round(kills / deaths, 2) if deaths > 0 else 0.0

        impact = calculate_player_impact_score(player_data)

        ranked.append({
            "player_id": player_id,
            "kd_ratio": kd_ratio,
            "impact_score": impact
        })

    # Sort by impact score descending
    ranked.sort(key=lambda p: p['impact_score'], reverse=True)

    # Add rank and tier
    total_players = len(ranked)
    for i, player in enumerate(ranked, start=1):
        player['rank'] = i

        # Determine tier
        if i <= max(1, total_players * 0.2):
            player['tier'] = "star"
        elif i > total_players * 0.8:
            player['tier'] = "weak"
        else:
            player['tier'] = "average"

    return ranked


def get_player_analysis_summary(player_stats_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function: Get ALL player-level metrics in one call.

    Args:
        player_stats_list: List of outputs from ingest_player_statistics()

    Returns:
        Dict containing all player analysis metrics
    """
    return {
        "star_player": identify_star_player(player_stats_list),
        "weak_link": identify_weak_link(player_stats_list),
        "agent_pools": extract_agent_pools(player_stats_list),
        "player_rankings": rank_players_by_performance(player_stats_list)
    }

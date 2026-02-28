"""
Extracts player-level metrics for Micro analysis.
Answers: "Who do we target?" and "Who is their star player?"
"""

import pandas as pd
import numpy as np
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
from typing import Dict, Any, List, Optional
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)

# VALORANT Roles Mapping (Lowercase keys for easier lookup)
AGENT_ROLES = {
    "jett": "Duelist",
    "reyna": "Duelist",
    "phoenix": "Duelist",
    "raze": "Duelist",
    "yoru": "Duelist",
    "neon": "Duelist",
    "iso": "Duelist",
    "sova": "Initiator",
    "breach": "Initiator",
    "skye": "Initiator",
    "kay/o": "Initiator",
    "fade": "Initiator",
    "gekko": "Initiator",
    "brimstone": "Controller",
    "viper": "Controller",
    "omen": "Controller",
    "astra": "Controller",
    "harbor": "Controller",
    "clove": "Controller",
    "killjoy": "Sentinel",
    "cypher": "Sentinel",
    "sage": "Sentinel",
    "chamber": "Sentinel",
    "deadlock": "Sentinel",
    "vyse": "Sentinel"
}

ROLE_WEIGHTS = {
    "Duelist": {"kd": 0.25, "adr": 0.25, "fk": 0.40, "win": 0.10}, # Meta: High entry impact + sustained damage
    "Initiator": {"kd": 0.15, "adr": 0.30, "assist": 0.40, "win": 0.15}, # Meta: Utility conversion and trade damage
    "Controller": {"kd": 0.15, "adr": 0.20, "assist": 0.35, "win": 0.30}, # Meta: Survival and clutch utility
    "Sentinel": {"kd": 0.25, "adr": 0.15, "assist": 0.15, "win": 0.45}, # Meta: Site anchoring and round conversion
    "Unknown": {"kd": 0.25, "adr": 0.25, "assist": 0.25, "win": 0.25}
}

# ============================================================================
# UTILITY: DATA CONVERSION
# ============================================================================

def player_stats_to_df(player_stats_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of player stats to a Pandas DataFrame for analysis.
    """
    flattened_data = []
    for player_data in player_stats_list:
        if not player_data.get('records'):
            continue
        
        record = player_data['records'][0]
        combat = record.get('combat', {})
        games = record.get('games', {})
        
        # Identify most played agent and role
        raw_game = record.get('raw', {}).get('game', {})
        unit_kills = raw_game.get('unitKills', [])
        
        # In GRID VALORANT data, unitKills often lists agents
        top_agent = "Unknown"
        top_agent_count = 0
        for unit in unit_kills:
            name = unit.get('unitName')
            count = unit.get('count', {}).get('sum', 0)
            if count > top_agent_count:
                top_agent = name
                top_agent_count = count
        
        role = AGENT_ROLES.get(top_agent.lower(), "Unknown")
        
        row = {
            "player_id": player_data.get('player_id'),
            "role": role,
            "top_agent": top_agent,
            "kills": combat.get('kills', {}).get('total', 0),
            "deaths": combat.get('deaths', {}).get('total', 1),
            "assists": combat.get('kill_assists_given', {}).get('total', 0),
            "adr": combat.get('damage_dealt', {}).get('avg', 0.0),
            "first_kill_pct": games.get('first_kill_percentage', 0.0) / 100,
            "win_rate": games.get('win_rate', 0.0) / 100,
            "games_count": games.get('count', 0)
        }
        row["kd_ratio"] = row["kills"] / row["deaths"] if row["deaths"] > 0 else row["kills"]
        flattened_data.append(row)
    
    return pd.DataFrame(flattened_data)

# ============================================================================
# MICRO-LEVEL ANALYSIS (Individual Player Performance)
# ============================================================================

def calculate_elite_impact_score(row: pd.Series) -> float:
    """
    Calculate an elite impact score based on player role and advanced metrics.
    """
    role = row.get('role', 'Unknown')
    weights = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS['Unknown'])
    
    # Normalize metrics (relative to typical professional benchmarks)
    # K/D: 1.0 is average, 1.5 is elite
    norm_kd = min(row['kd_ratio'] / 1.5, 1.2)
    
    # ADR: 130 is average, 170 is elite
    norm_adr = min(row['adr'] / 170.0, 1.2)
    
    # Normalize win rate: 50% is 0.5, 100% is 1.0 (clamped to 1.2 for consistency)
    norm_win = min(row['win_rate'] / 0.5, 1.2) * 0.5 # Scale it back so 50% = 0.5, 100% = 1.0
    
    score = 0.0
    if role == "Duelist":
        # Duelists focus on kills and opening rounds
        norm_fk = min(row['first_kill_pct'] / 0.20, 1.2)
        score = (norm_kd * weights['kd']) + (norm_adr * weights['adr']) + (norm_fk * weights['fk']) + (norm_win * weights['win'])
    else:
        # Others focus on utility/assists and survival
        # Assist per round benchmark: 0.35
        assists_per_game = row['assists'] / max(row['games_count'], 1)
        # Normalize assists (assuming ~20 rounds per game)
        # 0.35 assists per round = 7 assists per game
        norm_assist = min(assists_per_game / 7.0, 1.2)
        score = (norm_kd * weights['kd']) + (norm_adr * weights['adr']) + (norm_assist * weights['assist']) + (norm_win * weights['win'])
        
    return round(score, 3)

def identify_star_player(player_stats_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Identify the primary carry/star player using advanced metrics.
    """
    if not player_stats_list:
        return None

    df = player_stats_to_df(player_stats_list)
    if df.empty:
        return None
    
    # Calculate elite scores for all players
    df['impact_score'] = df.apply(calculate_elite_impact_score, axis=1)
    
    # Sort by impact score
    df = df.sort_values(by='impact_score', ascending=False)
    star_row = df.iloc[0]
    
    return {
        "player_id": star_row['player_id'],
        "role": star_row['role'],
        "top_agent": star_row['top_agent'],
        "kd_ratio": round(float(star_row['kd_ratio']), 2),
        "adr": round(float(star_row['adr']), 1),
        "impact_score": float(star_row['impact_score']),
        "games_played": int(star_row['games_count']),
        "reason": f"Highest role-adjusted impact score ({star_row['impact_score']}) as {star_row['role']}"
    }

def identify_weak_link(player_stats_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Identify the weakest performer using advanced metrics.
    """
    if not player_stats_list:
        return None

    df = player_stats_to_df(player_stats_list)
    if df.empty:
        return None
    
    df['impact_score'] = df.apply(calculate_elite_impact_score, axis=1)
    
    # Filter for players with enough games
    df_filtered = df[df['games_count'] >= 2]
    if df_filtered.empty:
        df_filtered = df

    df_filtered = df_filtered.sort_values(by='impact_score', ascending=True)
    weak_row = df_filtered.iloc[0]
    
    return {
        "player_id": weak_row['player_id'],
        "role": weak_row['role'],
        "kd_ratio": round(float(weak_row['kd_ratio']), 2),
        "adr": round(float(weak_row['adr']), 1),
        "impact_score": float(weak_row['impact_score']),
        "reason": f"Lowest role-adjusted impact score ({weak_row['impact_score']})"
    }


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
                "specialist": True # True if >70% on one agent
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
            "note": "Agent pool extraction needs raw data parsing",
            "game_data": game_data if game_data else {}
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

import pandas as pd
from typing import List, Dict, Any
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def aggregate_player_performance(player_stats_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Business Value: Identifies the "star" players and the "weak links".
    What: Aggregates normalized player statistics into a DataFrame.
    Why: Foundation for calculating K/D, Combat Score, and Impact metrics.
    """
    if not player_stats_list:
        _logger.warning("No player stats provided for aggregation.")
        return pd.DataFrame()

    records = []
    for player_data in player_stats_list:
        # Expecting normalized data from ingest/fetch_stats.py:ingest_player_statistics
        if "records" in player_data and player_data["records"]:
            record = player_data["records"][0]

            # Extract metrics from normalized structure
            combat = record.get("combat", {})
            kills = combat.get("kills", {}).get("total", 0)
            deaths = combat.get("deaths", {}).get("total", 0)

            # Calculate K/D ratio
            kd = round(kills / deaths, 2) if deaths > 0 else float(kills)

            player_summary = {
                "player_id": record.get("player_id"),
                "total_games": record.get("games", {}).get("count", 0),
                "kills": kills,
                "deaths": deaths,
                "kd_ratio": kd,
                "first_kill_pct": record.get("games", {}).get("first_kill_percentage", 0.0),
                "avg_plants": record.get("objectives", {}).get("plant_avg", 0.0),
                "avg_defuses": record.get("objectives", {}).get("defuse_avg", 0.0)
            }
            records.append(player_summary)

    return pd.DataFrame(records)


def map_player_to_agents(player_stats_list: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Business Value: Critical for prepping counters (e.g., "Ban Jett if TenZ plays it").
    What: Identifies signature agents for each player.
    Why: Helps coaches understand the opponent's agent pool depth.
    """
    signature_agents = {}

    for player_data in player_stats_list:
        player_id = player_data.get("player_id")
        raw_data = player_data.get("records", [{}])[0].get("raw", {})

        # In GRID Stats Feed, character picks are often in game.players.characters
        # However, the normalized ingestion might already have top_agents if we add it there.
        # For now, we'll look into the raw 'game' data if available
        game_data = raw_data.get("game", {})
        characters = game_data.get("players", {}).get("characters", [])

        picks = []
        for char in characters:
            agent_name = char.get("character", {}).get("name")
            if agent_name:
                picks.append(agent_name)

        signature_agents[player_id] = picks[:3]  # Top 3 agents

    return signature_agents


def identify_high_impact_threats(player_metrics: pd.DataFrame) -> List[str]:
    """
    Business Value: "Target [Player] first" - Actionable tactical advice.
    What: Flags players with statistical outliers (e.g., high K/D or high First Blood).
    Why: Pinpoints who the coach needs to build a counter-strategy against.
    """
    if player_metrics.empty:
        return []

    threats = []

    # 1. High K/D Threat
    high_kd = player_metrics[player_metrics['kd_ratio'] > 1.2]
    for _, row in high_kd.iterrows():
        threats.append(f"🔥 High Frag Threat: Player {row['player_id']} (K/D: {row['kd_ratio']})")

    # 2. Aggressive Entry Threat (First Bloods)
    aggressive = player_metrics[player_metrics['first_kill_pct'] > 20.0]
    for _, row in aggressive.iterrows():
        threats.append(f"⚡ Aggressive Opener: Player {row['player_id']} (First Blood: {row['first_kill_pct']}%)")

    # 3. Objective Specialist
    specialists = player_metrics[player_metrics['avg_plants'] > 1.5]
    for _, row in specialists.iterrows():
        threats.append(f"📍 Spike Specialist: Player {row['player_id']} (Avg Plants: {row['avg_plants']})")

    return threats

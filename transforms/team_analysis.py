"""
Extracts team-level metrics for Macro and Mid-Game analysis.

Each function is MODULAR - does ONE thing, returns a consistent structure.
Can be used by multiple handlers (full report, map analysis, etc.)
"""

import pandas as pd
from typing import Dict, Any, List

from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


# ============================================================================
# MACRO-LEVEL ANALYSIS (Pre-Game Strategy)
# ============================================================================

def extract_pistol_round_wr(team_stats: Dict[str, Any], team_match_details: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract pistol round win rate by attack/defense.
    If team_match_details is provided, calculates ACTUAL pistol round performance.
    Otherwise, uses attack/defense win rates as a proxy.
    """
    if not team_stats or not team_stats.get('records'):
        return {
            "overall": 0.0,
            "attack": 0.0,
            "defense": 0.0,
            "data_quality": "missing"
        }

    record = team_stats['records'][0]

    # GRID doesn't provide pistol-specific data
    # Using attack/defense win rates as proxy
    return {
        "overall": record.get('game_win_rate', 0.0) / 100,  # Convert percentage to decimal
        "attack": record.get('attack_win_rate', 0.0) / 100,
        "defense": record.get('defense_win_rate', 0.0) / 100,
        "data_quality": "proxy",  # Flag for future improvement
        "note": "Using attack/defense WR as proxy - GRID doesn't provide pistol-specific data"
    }


def calculate_overall_win_rates(team_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate overall performance metrics.

    Args:
        team_stats: Output from ingest_team_statistics()

    Returns:
        {
            "series": {"count": 10, "won": 7, "win_rate": 0.70},
            "games": {"count": 25, "won": 18, "win_rate": 0.72},
            "current_streak": {"type": "win", "count": 3}
        }
    """
    if not team_stats or not team_stats.get('records'):
        _logger.warning("No team stats records for win rate calculation")
        return {
            "series": {"count": 0, "won": 0, "win_rate": 0.0},
            "games": {"count": 0, "won": 0, "win_rate": 0.0},
            "current_streak": {"type": "none", "count": 0}
        }

    record = team_stats['records'][0]

    return {
        "series": {
            "count": record.get('total_series', 0),
            "won": record.get('series_won', 0),
            "win_rate": record.get('series_win_rate', 0.0) / 100
        },
        "games": {
            "count": record.get('total_games', 0),
            "won": record.get('games_won', 0),
            "win_rate": record.get('game_win_rate', 0.0) / 100
        },
        "current_streak": {
            "type": "win" if record.get('win_streak_current', 0) > 0 else "loss",
            "count": abs(record.get('win_streak_current', 0)),
            "max": record.get('win_streak_max', 0)
        }
    }


# ============================================================================
# MID-GAME ANALYSIS (Execution & Tendencies)
# ============================================================================

def extract_side_balance(team_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze attack vs defense performance.
    Answers: "Do they favor attacking or defending?"

    Args:
        team_stats: Output from ingest_team_statistics()

    Returns:
        {
            "attack": {
                "rounds": 120,
                "wins": 54,
                "win_rate": 0.45
            },
            "defense": {
                "rounds": 130,
                "wins": 91,
                "win_rate": 0.70
            },
            "bias": "defense",  # "attack", "defense", or "balanced"
            "bias_strength": 0.25  # Difference in win rates
        }
    """
    if not team_stats or not team_stats.get('records'):
        _logger.warning("No team stats records for side balance analysis")
        return {
            "attack": {"rounds": 0, "wins": 0, "win_rate": 0.0},
            "defense": {"rounds": 0, "wins": 0, "win_rate": 0.0},
            "bias": "unknown",
            "bias_strength": 0.0
        }

    record = team_stats['records'][0]

    attack_rounds = record.get('attack_rounds', 0)
    attack_wins = record.get('attack_wins', 0)
    attack_wr = record.get('attack_win_rate', 0.0) / 100

    defense_rounds = record.get('defense_rounds', 0)
    defense_wins = record.get('defense_wins', 0)
    defense_wr = record.get('defense_win_rate', 0.0) / 100

    # Determine bias (>10% difference is significant)
    bias_strength = abs(attack_wr - defense_wr)

    if bias_strength < 0.10:
        bias = "balanced"
    elif attack_wr > defense_wr:
        bias = "attack"
    else:
        bias = "defense"

    return {
        "attack": {
            "rounds": attack_rounds,
            "wins": attack_wins,
            "win_rate": attack_wr
        },
        "defense": {
            "rounds": defense_rounds,
            "wins": defense_wins,
            "win_rate": defense_wr
        },
        "bias": bias,
        "bias_strength": round(bias_strength, 3)
    }


def extract_objective_control(team_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract spike plant/defuse success rates.
    Answers: "How good are they at objectives?"

    Args:
        team_stats: Output from ingest_team_statistics()

    Returns:
        {
            "spike_plants": {
                "avg_per_game": 4.2,
                "total": 105
            },
            "spike_defuses": {
                "avg_per_game": 1.8,
                "total": 45
            },
            "bomb_explosions": {
                "avg_per_game": 2.1,
                "total": 52
            },
            "plant_success_rate": 0.49  # explosions / plants
        }
    """
    if not team_stats or not team_stats.get('records'):
        _logger.warning("No team stats records for objective control analysis")
        return {
            "spike_plants": {"avg_per_game": 0.0, "total": 0},
            "spike_defuses": {"avg_per_game": 0.0, "total": 0},
            "bomb_explosions": {"avg_per_game": 0.0, "total": 0},
            "plant_success_rate": 0.0
        }

    record = team_stats['records'][0]
    total_games = record.get('total_games', 1)  # Avoid division by zero

    plants_avg = record.get('spikes_planted_avg', 0.0)
    defuses_avg = record.get('spikes_defused_avg', 0.0)
    explosions_avg = record.get('bomb_explosions_avg', 0.0)

    # Calculate totals (avg * games)
    plants_total = int(plants_avg * total_games)
    explosions_total = int(explosions_avg * total_games)

    # Plant success rate = explosions / plants
    plant_success_rate = (explosions_total / plants_total) if plants_total > 0 else 0.0

    return {
        "spike_plants": {
            "avg_per_game": round(plants_avg, 2),
            "total": plants_total
        },
        "spike_defuses": {
            "avg_per_game": round(defuses_avg, 2),
            "total": int(defuses_avg * total_games)
        },
        "bomb_explosions": {
            "avg_per_game": round(explosions_avg, 2),
            "total": explosions_total
        },
        "plant_success_rate": round(plant_success_rate, 3)
    }


def extract_combat_metrics(team_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract team-level combat performance.

    Args:
        team_stats: Output from ingest_team_statistics()

    Returns:
        {
            "kd_ratio": 1.24,
            "kills_per_game": 13.2,
            "deaths_per_game": 10.6,
            "first_bloods_pct": 0.58  # % of games they got first kill
        }
    """
    if not team_stats or not team_stats.get('records'):
        _logger.warning("No team stats records for combat metrics")
        return {
            "kd_ratio": 0.0,
            "kills_per_game": 0.0,
            "deaths_per_game": 0.0,
            "first_bloods_pct": 0.0
        }

    record = team_stats['records'][0]

    return {
        "kd_ratio": record.get('kd_ratio', 0.0),
        "kills_per_game": record.get('kills_avg', 0.0),
        "deaths_per_game": record.get('deaths_avg', 0.0),
        "first_bloods_pct": record.get('first_bloods_percentage', 0.0) / 100
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_team_stats_input(team_stats: Dict[str, Any]) -> bool:
    """
    Validate that team_stats has the expected structure.

    Returns:
        True if valid, False otherwise
    """
    if not team_stats:
        _logger.error("team_stats is None")
        return False

    if not isinstance(team_stats, dict):
        _logger.error(f"team_stats is not a dict: {type(team_stats)}")
        return False

    if 'records' not in team_stats:
        _logger.error("team_stats missing 'records' key")
        return False

    if not team_stats['records']:
        _logger.error("team_stats 'records' is empty")
        return False

    return True


def get_team_analysis_summary(team_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function: Get ALL team-level metrics in one call.
    Used by Full Scouting Report handler.

    Args:
        team_stats: Output from ingest_team_statistics()

    Returns:
        Dict containing all team analysis metrics
    """
    if not validate_team_stats_input(team_stats):
        _logger.error("Invalid team_stats input")
        return {}

    return {
        "win_rates": calculate_overall_win_rates(team_stats),
        "pistol_rounds": extract_pistol_round_wr(team_stats),
        "side_balance": extract_side_balance(team_stats),
        "objective_control": extract_objective_control(team_stats),
        "combat_metrics": extract_combat_metrics(team_stats)
    }

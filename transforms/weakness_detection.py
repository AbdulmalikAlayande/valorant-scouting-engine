"""
Identifies exploitable patterns and weaknesses in team performance.
Answers: "How can we exploit them?"
"""

from typing import Dict, Any

from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


# ============================================================================
# EARLY GAME WEAKNESSES
# ============================================================================

def detect_early_aggression(team_game_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect if a team is aggressive early (first bloods).

    High first blood % = aggressive openers
    Low first blood % = passive/reactive

    Args:
        team_game_stats: Output from ingest_team_game_statistics()

    Returns:
        {
            "first_blood_rate": 0.58,
            "aggression_level": "high", # "high" (>55%), "medium" (45-55%), "low" (<45%)
            "exploitable": True,
            "counter_strategy": "Play passive early, wait for their aggression"
        }
    """
    if not team_game_stats or not team_game_stats.get('records'):
        _logger.warning("No team game stats for early aggression detection")
        return {
            "first_blood_rate": 0.0,
            "aggression_level": "unknown",
            "exploitable": False,
            "counter_strategy": "Insufficient data"
        }

    record = team_game_stats['records'][0]
    first_blood_pct = record.get('first_bloods_percentage', 0.0) / 100

    # Determine aggression level
    if first_blood_pct > 0.55:
        aggression_level = "high"
        exploitable = True
        counter_strategy = "Play passive early rounds - let them over-extend, then trade"
    elif first_blood_pct >= 0.45:
        aggression_level = "medium"
        exploitable = False
        counter_strategy = "Balanced approach - match their tempo"
    else:
        aggression_level = "low"
        exploitable = True
        counter_strategy = "Apply early pressure - they're reactive, force them to adapt"

    return {
        "first_blood_rate": round(first_blood_pct, 3),
        "aggression_level": aggression_level,
        "exploitable": exploitable,
        "counter_strategy": counter_strategy
    }


# ============================================================================
# ECONOMY MANAGEMENT WEAKNESSES
# ============================================================================

def detect_economy_patterns(team_game_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze economy management patterns.

    High avg_money = conservative (save often)
    Low avg_money = aggressive (force buys)

    Args:
        team_game_stats: Output from ingest_team_game_statistics()

    Returns:
        {
            "avg_money": 9870.0,
            "avg_net_worth": 12500.0,
            "economy_style": "conservative", # "conservative", "balanced", "aggressive"
            "force_buy_tendency": "low",
            "exploitable": True,
            "counter_strategy": "Force eco rounds - they'll save, you can snowball"
        }
    """
    if not team_game_stats or not team_game_stats.get('records'):
        _logger.warning("No team game stats for economy pattern detection")
        return {
            "avg_money": 0.0,
            "avg_net_worth": 0.0,
            "economy_style": "unknown",
            "force_buy_tendency": "unknown",
            "exploitable": False,
            "counter_strategy": "Insufficient data"
        }

    record = team_game_stats['records'][0]
    avg_money = record.get('avg_money', 0.0)
    avg_net_worth = record.get('avg_net_worth', 0.0)

    # VALORANT economy thresholds
    # Full buy: ~3900 credits (armor and rifle)
    # Eco: <2000 credits

    # Determine economy style based on avg money
    if avg_money > 3000:
        economy_style = "conservative"
        force_buy_tendency = "low"
        exploitable = True
        counter_strategy = "Force eco rounds - they'll save, allowing you to snowball economy"
    elif avg_money >= 2000:
        economy_style = "balanced"
        force_buy_tendency = "medium"
        exploitable = False
        counter_strategy = "Standard economy play - no clear pattern to exploit"
    else:
        economy_style = "aggressive"
        force_buy_tendency = "high"
        exploitable = True
        counter_strategy = "Play disciplined - they force buy often, punish their weak buys"

    return {
        "avg_money": round(avg_money, 2),
        "avg_net_worth": round(avg_net_worth, 2),
        "economy_style": economy_style,
        "force_buy_tendency": force_buy_tendency,
        "exploitable": exploitable,
        "counter_strategy": counter_strategy
    }


# ============================================================================
# OBJECTIVE CONTROL WEAKNESSES
# ============================================================================

def detect_plant_defuse_weaknesses(team_game_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify weaknesses in spike plant/defuse execution.

    Args:
        team_game_stats: Output from ingest_team_game_statistics()

    Returns:
        {
            "plant_success_rate": 0.49,  # explosions / plants
            "defuse_success_rate": 0.35,  # defuses / begin defuses
            "plant_weakness": True,
            "defuse_weakness": True,
            "counter_strategies": [
                "Apply post-plant pressure - low explosion rate",
                "Fake plants - low defuse completion rate"
            ]
        }
    """
    if not team_game_stats or not team_game_stats.get('records'):
        _logger.warning("No team game stats for objective weakness detection")
        return {
            "plant_success_rate": 0.0,
            "defuse_success_rate": 0.0,
            "plant_weakness": False,
            "defuse_weakness": False,
            "counter_strategies": []
        }

    record = team_game_stats['records'][0]

    # Plant metrics
    plants_total = record.get('plant_bomb_total', 0)
    explosions_total = record.get('explode_bomb_total', 0)
    plant_success_rate = (explosions_total / plants_total) if plants_total > 0 else 0.0

    # Defuse metrics
    begin_defuse_total = record.get('begin_defuse_total', 0)
    defuses_total = record.get('defuse_bomb_total', 0)
    defuse_success_rate = (defuses_total / begin_defuse_total) if begin_defuse_total > 0 else 0.0

    counter_strategies = []

    # Plant weakness (explosion rate < 50%)
    plant_weakness = plant_success_rate < 0.50
    if plant_weakness:
        counter_strategies.append(
            f"Apply post-plant pressure - they only convert {plant_success_rate * 100:.1f}% of plants"
        )

    # Defuse weakness (completion rate < 40%)
    defuse_weakness = defuse_success_rate < 0.40
    if defuse_weakness:
        counter_strategies.append(
            f"Fake plants and force defuses - they only complete {defuse_success_rate * 100:.1f}% of defuses"
        )

    return {
        "plant_success_rate": round(plant_success_rate, 3),
        "defuse_success_rate": round(defuse_success_rate, 3),
        "plant_weakness": plant_weakness,
        "defuse_weakness": defuse_weakness,
        "counter_strategies": counter_strategies
    }


# ============================================================================
# SIDE-SPECIFIC WEAKNESSES
# ============================================================================

def detect_side_weaknesses(team_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify if a team is weaker on attack or defense.

    Args:
        team_stats: Output from ingest_team_statistics()

    Returns:
        {
            "weak_side": "attack", # or "defense" or "balanced"
            "attack_wr": 0.45,
            "defense_wr": 0.70,
            "weakness_severity": "high", # Difference > 20%
            "counter_strategy": "Pick maps favoring attack side - exploit their weak attack"
        }
    """
    if not team_stats or not team_stats.get('records'):
        _logger.warning("No team stats for side weakness detection")
        return {
            "weak_side": "unknown",
            "attack_wr": 0.0,
            "defense_wr": 0.0,
            "weakness_severity": "unknown",
            "counter_strategy": "Insufficient data"
        }

    record = team_stats['records'][0]

    attack_wr = record.get('attack_win_rate', 0.0) / 100
    defense_wr = record.get('defense_win_rate', 0.0) / 100

    diff = abs(attack_wr - defense_wr)

    # Determine the weak side
    if diff < 0.10:
        weak_side = "balanced"
        weakness_severity = "none"
        counter_strategy = "No clear side weakness - standard approach"
    elif attack_wr < defense_wr:
        weak_side = "attack"
        weakness_severity = "high" if diff > 0.20 else "medium"
        counter_strategy = f"Pick maps favoring attack side - they struggle on attack ({attack_wr * 100:.1f}% WR)"
    else:
        weak_side = "defense"
        weakness_severity = "high" if diff > 0.20 else "medium"
        counter_strategy = f"Pick maps favoring defense side - they struggle on defense ({defense_wr * 100:.1f}% WR)"

    return {
        "weak_side": weak_side,
        "attack_wr": round(attack_wr, 3),
        "defense_wr": round(defense_wr, 3),
        "weakness_severity": weakness_severity,
        "counter_strategy": counter_strategy
    }


# ============================================================================
# CONSISTENCY ANALYSIS
# ============================================================================

def detect_consistency_issues(team_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify if a team has consistency/streak issues.

    Args:
        team_stats: Output from ingest_team_statistics()

    Returns:
        {
            "current_streak": {"type": "win", "count": 3},
            "max_streak": 5,
            "consistency": "streaky", # or "consistent"
            "exploitable": True,
            "counter_strategy": "Apply early pressure - they're on a hot streak"
        }
    """
    if not team_stats or not team_stats.get('records'):
        _logger.warning("No team stats for consistency detection")
        return {
            "current_streak": {"type": "none", "count": 0},
            "max_streak": 0,
            "consistency": "unknown",
            "exploitable": False,
            "counter_strategy": "Insufficient data"
        }

    record = team_stats['records'][0]

    current_streak = record.get('win_streak_current', 0)
    max_streak = record.get('win_streak_max', 0)

    # Determine if streaky (max streak > 5 is considered streaky)
    is_streaky = max_streak > 5
    consistency = "streaky" if is_streaky else "consistent"

    # Determine current momentum
    if current_streak > 3:
        streak_type = "win"
        exploitable = True
        counter_strategy = f"Apply early pressure - they're hot ({current_streak} win streak). Disrupt momentum."
    elif current_streak < -3:
        streak_type = "loss"
        exploitable = True
        counter_strategy = f"Capitalize on poor form - they're cold ({abs(current_streak)} loss streak)"
    else:
        streak_type = "neutral"
        exploitable = False
        counter_strategy = "No clear momentum pattern"

    return {
        "current_streak": {
            "type": streak_type,
            "count": abs(current_streak)
        },
        "max_streak": max_streak,
        "consistency": consistency,
        "exploitable": exploitable,
        "counter_strategy": counter_strategy
    }


# ============================================================================
# AGGREGATOR FUNCTION
# ============================================================================

def get_weakness_detection_summary(
        team_stats: Dict[str, Any],
        team_game_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function: Get ALL weakness detections in one call.

    Args:
        team_stats: Output from ingest_team_statistics()
        team_game_stats: Output from ingest_team_game_statistics()

    Returns:
        Dict containing all weakness analysis
    """
    return {
        "early_aggression": detect_early_aggression(team_game_stats),
        "economy_patterns": detect_economy_patterns(team_game_stats),
        "objective_weaknesses": detect_plant_defuse_weaknesses(team_game_stats),
        "side_weaknesses": detect_side_weaknesses(team_stats),
        "consistency_issues": detect_consistency_issues(team_stats)
    }

"""
Identifies exploitable patterns and weaknesses in team performance.
Answers: "How can we exploit them?"
"""

from typing import Dict, Any, List, Optional
import numpy as np

from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)

# Global Contextual Benchmarks (Typical Professional VALORANT averages)
BENCHMARKS = {
    "first_blood_rate": 0.50,
    "first_death_rate": 0.50,
    "win_rate": 0.50,
    "pistol_win_rate": 0.50,
    "attack_win_rate": 0.48,
    "defense_win_rate": 0.52,
    "clutch_win_rate": 0.15, # 1vX situations
}

# ============================================================================
# EARLY GAME WEAKNESSES
# ============================================================================

def detect_early_aggression(team_game_stats: Dict[str, Any], team_stats: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Detect if a team is aggressive early (first bloods) and if it's DISCIPLINED.
    Disciplined Aggression = High First Blood % AND High Win % when FB occurs.
    Feeding = High First Death % or Low Win % when FB occurs.
    """
    if not team_game_stats or not team_game_stats.get('records'):
        return {
            "first_blood_rate": 0.0,
            "aggression_style": "unknown",
            "exploitable": False,
            "counter_strategy": "Insufficient data"
        }

    record = team_game_stats['records'][0]
    # First blood percentage in GRID is rounds where the team got the first kill
    fb_pct = record.get('first_bloods_percentage', 0.0) / 100
    
    # We also need First Death if available, or we use first_bloods_percentage of opponent
    # For now, let's look at the correlation between FB and Win Rate if we had match details
    # Since we are in weakness_detection (aggregated), we use the benchmarks.
    
    diff = fb_pct - BENCHMARKS["first_blood_rate"]
    
    if diff > 0.08:
        aggression_level = "High Aggression"
        if team_stats and (team_stats['records'][0].get('game_win_rate', 0) / 100) > 0.55:
            style = "Disciplined Aggression"
            exploitable = True
            counter = "Play for the trade - don't take 1v1 duels, use utility to stop their initial hit"
        else:
            style = "High Risk / Feeding"
            exploitable = True
            counter = "Punish over-extensions - hold passive angles and wait for them to dry-peek"
    elif diff < -0.08:
        style = "Passive / Reactive"
        exploitable = True
        counter = "Take map control early - they will concede space, use it to set up traps"
    else:
        style = "Balanced"
        exploitable = False
        counter = "Match their tempo - no clear early game bias"

    return {
        "first_blood_rate": round(fb_pct, 3),
        "deviation_from_pro_avg": round(diff, 3),
        "aggression_style": style,
        "exploitable": exploitable,
        "counter_strategy": counter
    }


# ============================================================================
# ECONOMY MANAGEMENT WEAKNESSES
# ============================================================================

def analyze_force_buy_efficiency(team_match_details: List[Dict[str, Any]], team_name: str) -> Dict[str, Any]:
    """
    Determine how dangerous a team is on Force Buys (Low Economy).
    """
    # This requires round-by-round economy which isn't in Stats Feed but in Series State
    # For now, we look at 'Scrappy' factor: Win Rate in rounds where they lost the previous round
    # and didn't have a massive bank.
    
    # Placeholder for elite logic: In a real scenario, we'd check winType: Elimination
    # and cross-reference with previous round's outcome.
    
    return {
        "force_buy_win_rate": "Data Pending",
        "scrappiness_rating": "Medium",
        "advice": "Don't underestimate their half-buys; they play aggressively when broke"
    }

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

def detect_recurring_tells(team_match_details: List[Dict[str, Any]], team_name: str) -> List[Dict[str, Any]]:
    """
    Identify predictable habits or 'tells' from match details using specialized heuristics.
    """
    if not team_match_details or not team_name:
        return []
    
    tells = []
    
    # 1. Anti-Eco Vulnerability (Round 2 after winning Round 1)
    round_2_results = []
    for match in team_match_details:
        for game in match.get('games', []):
            segments = sorted(game.get('segments', []), key=lambda x: x.get('sequence_number', 0))
            if len(segments) < 2:
                continue
                
            round_1_win = False
            for st in segments[0].get('teams', []):
                if st.get('name') == team_name and st.get('won'):
                    round_1_win = True
            
            if round_1_win:
                for st in segments[1].get('teams', []):
                    if st.get('name') == team_name:
                        round_2_results.append(st.get('won'))
    
    if round_2_results and len(round_2_results) >= 3:
        wr = sum(round_2_results) / len(round_2_results)
        if wr < 0.70: # Professional teams should win >80% of anti-ecos
            tells.append({
                "name": "Anti-Eco Vulnerability",
                "description": f"Team struggles to convert Round 2 after winning Pistol ({wr*100:.1f}% WR)",
                "exploit": "Always force-buy against them after losing pistol; they are vulnerable to scrappy buys."
            })

    # 2. Eco-Round Aggression ("The Tell")
    # Detect if they push aggressively on eco rounds (indicated by high FB rate in Round 2 after loss)
    eco_fb_attempts = 0
    eco_fb_success = 0
    for match in team_match_details:
        for game in match.get('games', []):
            segments = sorted(game.get('segments', []), key=lambda x: x.get('sequence_number', 0))
            if len(segments) < 2: continue
            
            round_1_loss = False
            for st in segments[0].get('teams', []):
                if st.get('name') == team_name and not st.get('won'):
                    round_1_loss = True
            
            if round_1_loss:
                for st in segments[1].get('teams', []):
                    if st.get('name') == team_name:
                        eco_fb_attempts += 1
                        if st.get('first_kill'):
                            eco_fb_success += 1
    
    if eco_fb_attempts >= 3:
        fb_rate = eco_fb_success / eco_fb_attempts
        if fb_rate > 0.5:
            tells.append({
                "name": "Aggressive Eco Push",
                "description": f"Consistently goes for First Bloods on Eco rounds ({fb_rate*100:.1f}% FB rate).",
                "exploit": "Expect an aggressive push or dry-peek on their eco rounds. Play passive and use utility to stall."
            })

    # 3. Bonus Round Conversion
    bonus_results = []
    for match in team_match_details:
        for game in match.get('games', []):
            segments = sorted(game.get('segments', []), key=lambda x: x.get('sequence_number', 0))
            if len(segments) < 3: continue
            
            won_first_two = True
            for i in range(2):
                won_round = False
                for st in segments[i].get('teams', []):
                    if st.get('name') == team_name and st.get('won'):
                        won_round = True
                if not won_round: won_first_two = False
            
            if won_first_two:
                for st in segments[2].get('teams', []):
                    if st.get('name') == team_name:
                        bonus_results.append(st.get('won'))
    
    if bonus_results and len(bonus_results) >= 2:
        bonus_wr = sum(bonus_results) / len(bonus_results)
        if bonus_wr < 0.25:
            tells.append({
                "name": "Weak Bonus Conversions",
                "description": f"Low win rate on Round 3 (Bonus) after 2-0 start ({bonus_wr*100:.1f}%).",
                "exploit": "Play standard on your full-buy Round 3; they often play too loosely or lack utility depth here."
            })

    # 4. Ultimate Usage Efficiency (Placeholder for future expansion)
    # If we had ult data, we'd add it here.

    return tells


def get_weakness_detection_summary(
    team_stats: Dict[str, Any], 
    team_game_stats: Dict[str, Any],
    team_match_details: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get a comprehensive summary of team weaknesses.
    """
    team_name = team_stats.get('team_name')
    
    summary = {
        "early_aggression": detect_early_aggression(team_game_stats, team_stats),
        "economy_patterns": detect_economy_patterns(team_game_stats),
        "objective_weaknesses": detect_plant_defuse_weaknesses(team_game_stats),
        "side_weaknesses": detect_side_weaknesses(team_stats),
        "consistency_issues": detect_consistency_issues(team_stats)
    }
    
    if team_match_details and team_name:
        summary["tactical_economy"] = analyze_force_buy_efficiency(team_match_details, team_name)
        summary["recurring_tells"] = detect_recurring_tells(team_match_details, team_name)
        
    return summary

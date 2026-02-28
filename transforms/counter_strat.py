
"""
The 'Brain' of the scouting engine.
Maps our team's (or typical counter) strengths against the opponent's specific weaknesses.
"""

from typing import Dict, Any, List
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)

def generate_counter_strat(
    opponent_analysis: Dict[str, Any],
    opponent_weaknesses: Dict[str, Any],
    our_team_analysis: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate a high-level game plan based on the opponent's profile.
    """
    game_plan = []
    map_veto = []
    
    # 1. Map Veto Logic
    opp_maps = opponent_analysis.get('win_rates', {}).get('games', {}) # This would ideally be map-specific
    # Placeholder: In a real scenario, we'd compare map-by-map
    
    # 2. Tactical Exploitation
    aggression = opponent_weaknesses.get('early_aggression', {})
    if aggression.get('aggression_style') == "High Risk / Feeding":
        game_plan.append("CONTEST EARLY: The opponent takes high-risk duels. Hold crossfires and punish their dry-peeks.")
    elif aggression.get('aggression_style') == "Disciplined Aggression":
        game_plan.append("UTILITY FIRST: They are good at opening rounds. Use smokes and flashes to deny their preferred entry paths.")
    elif aggression.get('aggression_style') == "Passive / Reactive":
        game_plan.append("EARLY MAP CONTROL: They concede space. Take Orbs and map control early to squeeze them into sites.")

    # 3. Economy Counter
    pistols = opponent_analysis.get('pistol_rounds', {})
    if pistols.get('overall', 0) > 0.60:
        game_plan.append("PISTOL PREP: They are deadly on pistols. Consider an unorthodox stack or aggressive push to disrupt their default.")

    # 4. Win Reason Counter
    reasons = opponent_analysis.get('win_reasons', {})
    if reasons.get('primary_method') == 'Elimination':
        game_plan.append("BOG THEM DOWN: They win by out-aiming. Force them into post-plant situations where utility matters more than raw aim.")

    return {
        "recommended_game_plan": game_plan,
        "map_veto_advice": "Focus on banning their high-win-rate maps (Icebox/Bind) and picking maps where their pistol WR is low.",
        "anti_strat_focus": aggression.get('aggression_style', 'Standard')
    }

"""
Rather than just raw stats, this module converts
numbers into English "Actionable Insights."
"""

from typing import List, Dict, Any
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)

def generate_how_to_win(team_analysis: Dict[str, Any], player_analysis: List[str]) -> List[str]:
    """
    Business Value: The "Brain" of the system. Converts data into strategy.
    What: Synthesizes team and player findings into prioritized "How to Win" bullets.
    Why: This is what the winning submission requirements (Actionable Insights) demand.
    """
    insights = []

    # 1. Map Strategy (Macro)
    if "insights" in team_analysis:
        # Prioritize map recommendations
        insights.extend(team_analysis["insights"])

    # 2. Player Threats (Micro)
    if player_analysis:
        # Add top player-specific threats
        insights.extend(player_analysis[:3])

    # 3. Dynamic Tactical Advice
    # Example logic: if momentum is hot, suggest disrupting flow
    if team_analysis.get("momentum") == "hot":
        insights.append("🌊 High Momentum Alert: Opponent is on a win streak. Recommend early tactical timeouts if they start strong.")
    
    # 4. Role-based Advice (if we have it)
    # This could be expanded as more data is ingested

    return insights


def format_actionable_bullets(insights: List[str]) -> List[str]:
    """
    Business Value: Ensures the coach gets a clean, scannable report.
    What: Cleans and prioritizes the top 5 insights.
    Why: "Report-first design" for professional use.
    """
    # Filter out empty or redundant insights
    clean_insights = [i.strip() for i in insights if i and len(i) > 5]
    
    # Prioritize: Map Veto > Player Threats > Tactical
    # (Simple prioritization for now: Map Veto usually starts with emoji/symbol)
    priority_insights = sorted(clean_insights, key=lambda x: (
        0 if "✓" in x or "⚠" in x else 1
    ))

    return priority_insights[:5] # Top 5 Actionable Insights

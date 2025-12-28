from models.report import AgentPick, MapPerformance
from typing import Dict, Any, List

def analyze_team_stats(stats_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms raw GRID teamStatistics into a structured format for the scouting report.
    """
    team_stats = stats_data.get("teamStatistics", {})
    if not team_stats:
        return {}

    series_stats = team_stats.get("series", {})
    game_stats = team_stats.get("game", {})
    
    total_matches = series_stats.get("count", 0)
    win_rate = series_stats.get("won", {}).get("percentage", 0.0)
    
    # Process Top Agents
    top_agents = []
    players_data = game_stats.get("players", {})
    if players_data:
        characters = players_data.get("characters", [])
        # Sort by pick rate descending and take top 5
        sorted_chars = sorted(characters, key=lambda x: x.get("percentage", 0), reverse=True)[:5]
        for char in sorted_chars:
            top_agents.append(AgentPick(
                agent=char["character"]["name"],
                pick_count=char["count"],
                pick_rate=char["percentage"]
            ))

    # Actionable Insights (Logic-based)
    insights = []
    if win_rate > 70:
        insights.append(f"Highly dominant team ({win_rate}% win rate). Recommend aggressive map bans.")
    elif win_rate < 40:
        insights.append(f"Struggling team ({win_rate}% win rate). Exploit their lack of coordination.")

    # Objective-based insights
    objectives = game_stats.get("objectives", [])
    for obj in objectives:
        if obj["type"] == "PISTOL_ROUND" and obj.get("completedFirst", {}).get("percentage", 0) > 60:
            insights.append("Strong pistol round performance. Prepare for early aggression.")

    return {
        "total_matches": total_matches,
        "win_rate": win_rate,
        "top_agents": top_agents,
        "actionable_insights": insights,
        "map_performance": [] # To be populated by more granular analysis if available
    }

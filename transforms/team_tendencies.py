from models.report import AgentPick, MapPerformance
from models.teams import Team, TeamStats
from models.stats import SideStats, ObjectiveStats, BaseGameStats, TeamGameStatistics, TeamStatistics, WinStreak
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
    
    # Process win rate from the list of BooleanOccurrenceStatistic
    win_rate = 0.0
    won_stats = series_stats.get("won", [])
    if isinstance(won_stats, list):
        for stat in won_stats:
            if stat.get("value") is True:
                win_rate = stat.get("percentage", 0.0)
                break
    elif isinstance(won_stats, dict):
        win_rate = won_stats.get("percentage", 0.0)
    
    # Process Top Agents
    top_agents = []
    player_agg_data = game_stats.get("players", {})
    if player_agg_data:
        characters = player_agg_data.get("characters", [])
        if isinstance(characters, list):
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
    elif win_rate > 0 and win_rate < 40:
        insights.append(f"Struggling team ({win_rate}% win rate). Exploit their lack of coordination.")

    # Objective-based insights
    objectives = game_stats.get("objectives", [])
    if isinstance(objectives, list):
        for obj in objectives:
            completed_first = obj.get("completedFirst", [])
            # Find the percentage where value is true
            perc = 0.0
            if isinstance(completed_first, list):
                for stat in completed_first:
                    if stat.get("value") is True:
                        perc = stat.get("percentage", 0.0)
                        break
            
            if obj["type"] == "PISTOL_ROUND" and perc > 60:
                insights.append("Strong pistol round performance. Prepare for early aggression.")

    # Process map performance if available (requires more granular data)
    map_performance_list = []
    # From the teamStatistics query, we don't have per-map stats in the fragment used.
    # But if we were to add them, they would be processed here.

    return {
        "total_matches": int(total_matches),
        "win_rate": float(win_rate),
        "top_agents": top_agents,
        "actionable_insights": insights,
        "map_performance": map_performance_list
    }

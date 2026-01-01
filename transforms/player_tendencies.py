from typing import Dict, Any, List
from models.stats import SideStats, ObjectiveStats, BaseGameStats, TeamGameStatistics, TeamStatistics, WinStreak

def analyze_player_stats(player_data: Dict[str, Any]) -> Dict[str, Any]:

    player_stats = player_data.get("playerStatistics", {})
    if not player_stats:
        return {}

    game_stats = player_stats.get("game", {})
    
    kills_avg = game_stats.get("kills", {}).get("avg", 0.0)
    deaths_avg = game_stats.get("deaths", {}).get("avg", 0.0)
    kd_ratio = kills_avg / deaths_avg if deaths_avg > 0 else kills_avg
    
    # Process top agents for player
    top_agents = []
    characters = game_stats.get("characters", [])
    sorted_chars = sorted(characters, key=lambda x: x.get("percentage", 0), reverse=True)[:3]
    for char in sorted_chars:
        top_agents.append({
            "agent": char["character"]["name"],
            "pick_rate": char["percentage"]
        })

    return {
        "player_id": player_stats.get("id"),
        "kills_avg": round(kills_avg, 2),
        "deaths_avg": round(deaths_avg, 2),
        "kd_ratio": round(kd_ratio, 2),
        "top_agents": top_agents
    }

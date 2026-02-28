import sys
import os
import json
import pandas as pd

from transforms.player_analysis import get_player_analysis_summary, generate_performance_chart

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def create_mock_player(player_id, agent, kills, deaths, assists, damage_avg, win_rate, first_kill_pct):
    return {
        "player_id": player_id,
        "records": [{
            "player_id": player_id,
            "combat": {
                "kills": {"total": kills, "avg": kills / 5},
                "deaths": {"total": deaths, "avg": deaths / 5},
                "kill_assists_given": {"total": assists, "avg": assists / 5},
                "damage_dealt": {"total": damage_avg * 5, "avg": damage_avg},
            },
            "games": {
                "count": 5,
                "win_rate": win_rate * 100,
                "first_kill_percentage": first_kill_pct * 100
            },
            "raw": {
                "game": {
                    "unitKills": [
                        {"unitName": agent, "count": {"sum": 5}}
                    ]
                }
            }
        }]
    }


def test_elite_analysis():
    print("--- Starting Elite Player Analysis Test ---")

    # Mock data for a team
    team_stats = [
        create_mock_player("StarDuelist", "Jett", 100, 60, 10, 165.0, 0.6, 0.25),  # High impact Duelist
        create_mock_player("SolidSupport", "Omen", 65, 60, 45, 125.0, 0.6, 0.05),  # Strong Controller
        create_mock_player("Anchor", "Cypher", 70, 55, 15, 135.0, 0.6, 0.08),  # Good Sentinel
        create_mock_player("Initiator", "Sova", 60, 65, 55, 140.0, 0.6, 0.05),  # Impact Initiator
        create_mock_player("Struggler", "Reyna", 55, 80, 5, 110.0, 0.6, 0.15),  # Weak Duelist
    ]

    summary = get_player_analysis_summary(team_stats)

    print("\nStar Player:")
    print(json.dumps(summary['star_player'], indent=2))

    print("\nTarget (Weak) Player:")
    print(json.dumps(summary['target_player'], indent=2))

    print("\nRankings:")
    for rank in summary['rankings']:
        print(
            f"#{rank['rank']} {rank['player_id']} ({rank['role']}) - Score: {rank['impact_score']} - Tier: {rank['tier']}")

    # Test chart generation (if matplotlib is available)
    chart_path = "test_player_performance.png"
    result_path = generate_performance_chart(team_stats, chart_path)
    if result_path:
        print(f"\nPerformance chart generated: {result_path}")
    else:
        print("\nPerformance chart generation skipped (matplotlib missing)")


if __name__ == "__main__":
    test_elite_analysis()

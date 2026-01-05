
import pandas as pd
from transforms.player_analysis import (
    aggregate_player_performance, 
    map_player_to_agents, 
    identify_high_impact_threats
)

def test_player_tendencies():
    print("Testing Player Tendencies...")

    # Mock normalized player stats (matching ingest_player_statistics output)
    mock_player_1 = {
        "player_id": "2512",
        "records": [{
            "player_id": "2512",
            "games": {"count": 10, "first_kill_percentage": 25.0},
            "combat": {
                "kills": {"total": 200},
                "deaths": {"total": 150}
            },
            "objectives": {
                "plant_avg": 2.0,
                "defuse_avg": 0.5
            },
            "raw": {
                "game": {
                    "players": {
                        "characters": [
                            {"character": {"name": "Jett"}},
                            {"character": {"name": "Raze"}},
                            {"character": {"name": "Phoenix"}}
                        ]
                    }
                }
            }
        }]
    }

    mock_player_2 = {
        "player_id": "9999",
        "records": [{
            "player_id": "9999",
            "games": {"count": 10, "first_kill_percentage": 5.0},
            "combat": {
                "kills": {"total": 120},
                "deaths": {"total": 150}
            },
            "objectives": {
                "plant_avg": 0.5,
                "defuse_avg": 1.2
            },
            "raw": {
                "game": {
                    "players": {
                        "characters": [
                            {"character": {"name": "Omen"}},
                            {"character": {"name": "Brimstone"}}
                        ]
                    }
                }
            }
        }]
    }

    player_stats_list = [mock_player_1, mock_player_2]

    # 1. Test Aggregation
    df_performance = aggregate_player_performance(player_stats_list)
    print("\nPlayer Performance DataFrame:")
    print(df_performance)

    # 2. Test Agent Mapping
    agents = map_player_to_agents(player_stats_list)
    print("\nSignature Agents:")
    print(agents)

    # 3. Test Threat Identification
    threats = identify_high_impact_threats(df_performance)
    print("\nIdentified Threats:")
    for t in threats:
        print(f" - {t}")

if __name__ == "__main__":
    test_player_tendencies()

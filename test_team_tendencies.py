
import pandas as pd
from transforms.team_tendencies import calculate_win_rates, analyze_map_veto_strategy, detect_strategic_trends

def test_team_tendencies():
    print("Testing Team Tendencies...")

    # Mock data for game statistics (multiple maps)
    mock_game_stats = {
        "records": [
            {
                "team_id": "1079", 
                "map_filter": "Ascent", 
                "game_count": 10, 
                "game_win_rate": 80.0,
                "attack_win_rate": 85.0,
                "defense_win_rate": 75.0
            },
            {
                "team_id": "1079", 
                "map_filter": "Haven", 
                "game_count": 8, 
                "game_win_rate": 62.5,
                "attack_win_rate": 40.0,
                "defense_win_rate": 85.0
            },
            {
                "team_id": "1079", 
                "map_filter": "Icebox", 
                "game_count": 3, 
                "game_win_rate": 33.3,
                "attack_win_rate": 30.0,
                "defense_win_rate": 36.6
            },
        ]
    }

    df_win_rates = calculate_win_rates(mock_game_stats)
    print("\nWin Rates DataFrame:")
    print(df_win_rates)

    veto_strategy = analyze_map_veto_strategy(df_win_rates)
    print("\nVeto Strategy:")
    print(veto_strategy)

    # Mock data for series (recent form)
    mock_series_data = {
        "team_id": "1079",
        "series": [
            {"start_time": "2024-01-01T10:00:00Z", "teams": [{"team_id": "1079", "won": True}, {"team_id": "999", "won": False}]},
            {"start_time": "2024-01-02T10:00:00Z", "teams": [{"team_id": "1079", "won": True}, {"team_id": "999", "won": False}]},
            {"start_time": "2024-01-03T10:00:00Z", "teams": [{"team_id": "1079", "won": False}, {"team_id": "999", "won": True}]},
            {"start_time": "2024-01-04T10:00:00Z", "teams": [{"team_id": "1079", "won": True}, {"team_id": "999", "won": False}]},
            {"start_time": "2024-01-05T10:00:00Z", "teams": [{"team_id": "1079", "won": True}, {"team_id": "999", "won": False}]},
        ]
    }

    trends = detect_strategic_trends(mock_series_data)
    print("\nStrategic Trends:")
    print(trends)

if __name__ == "__main__":
    test_team_tendencies()

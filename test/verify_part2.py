
import json
import os
from typing import Dict, Any, List
import pandas as pd

from transforms.team_analysis import get_team_analysis_summary, extract_pistol_round_wr, analyze_win_reasons

def test_tactical_precision():
    print("--- Starting Tactical Precision (Part 2) Test ---")
    
    # Mock team_stats
    team_stats = {
        "team_name": "Cloud9",
        "records": [{
            "total_series": 10,
            "series_win_rate": 70.0,
            "total_games": 25,
            "game_win_rate": 65.0,
            "attack_win_rate": 60.0,
            "defense_win_rate": 70.0
        }]
    }
    
    # Mock match_details with segments (rounds)
    match_details = [{
        "game_id": "game1",
        "games": [{
            "sequence_number": 1,
            "segments": [
                # Pistol Round 1 (Attack) - WON
                {
                    "sequence_number": 1,
                    "teams": [
                        {"name": "Cloud9", "won": True, "side": "attack", "win_type": "Elimination"},
                        {"name": "Opponent", "won": False, "side": "defense"}
                    ]
                },
                # Round 2 - WON
                {
                    "sequence_number": 2,
                    "teams": [
                        {"name": "Cloud9", "won": True, "side": "attack", "win_type": "BombExploded"},
                        {"name": "Opponent", "won": False, "side": "defense"}
                    ]
                },
                # Pistol Round 13 (Defense) - LOST
                {
                    "sequence_number": 13,
                    "teams": [
                        {"name": "Cloud9", "won": False, "side": "defense"},
                        {"name": "Opponent", "won": True, "side": "attack", "win_type": "Elimination"}
                    ]
                }
            ]
        }]
    }]
    
    print("\n1. Testing Pistol Round Extraction (High Fidelity):")
    pistols = extract_pistol_round_wr(team_stats, match_details)
    print(json.dumps(pistols, indent=2))
    assert pistols['data_quality'] == 'high'
    assert pistols['overall'] == 0.5 # 1 win, 1 loss
    assert pistols['attack'] == 1.0
    assert pistols['defense'] == 0.0
    
    print("\n2. Testing Win Reasons Analysis:")
    reasons = analyze_win_reasons(match_details, "Cloud9")
    print(json.dumps(reasons, indent=2))
    assert reasons['primary_method'] in ['Elimination', 'BombExploded']
    assert reasons['sample_size'] == 2
    
    print("\n3. Testing Full Team Summary with Match Details:")
    summary = get_team_analysis_summary(team_stats, match_details)
    print("Summary keys:", summary.keys())
    assert "win_reasons" in summary
    assert "clutch_performance" in summary
    assert summary['pistol_rounds']['data_quality'] == 'high'

    print("\n4. Testing Fallback to Proxy (No Match Details):")
    fallback = extract_pistol_round_wr(team_stats, None)
    print(json.dumps(fallback, indent=2))
    assert fallback['data_quality'] == 'proxy'
    assert fallback['overall'] == 0.65

    print("\n✅ Part 2 Tactical Precision Verification Successful!")

if __name__ == "__main__":
    test_tactical_precision()

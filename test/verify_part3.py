
import json
from typing import Dict, Any, List
from transforms.weakness_detection import get_weakness_detection_summary, detect_early_aggression

def test_contextual_intelligence():
    print("--- Starting Contextual Intelligence (Part 3) Test ---")
    
    # Mock data
    team_stats = {
        "records": [{
            "game_win_rate": 60.0 # Pro avg is 50
        }]
    }
    
    # Case 1: Disciplined Aggression (High FB, High Win Rate)
    game_stats_disciplined = {
        "records": [{
            "first_bloods_percentage": 65.0 # Benchmark is 50.0
        }]
    }
    
    print("\n1. Testing Disciplined Aggression Detection:")
    weakness_disciplined = detect_early_aggression(game_stats_disciplined, team_stats)
    print(json.dumps(weakness_disciplined, indent=2))
    assert weakness_disciplined['aggression_style'] == "Disciplined Aggression"
    assert weakness_disciplined['deviation_from_pro_avg'] > 0
    
    # Case 2: High Risk / Feeding (High FB, Low Win Rate)
    team_stats_weak = {"records": [{"game_win_rate": 40.0}]}
    print("\n2. Testing Feeding Detection:")
    weakness_feeding = detect_early_aggression(game_stats_disciplined, team_stats_weak)
    print(json.dumps(weakness_feeding, indent=2))
    assert weakness_feeding['aggression_style'] == "High Risk / Feeding"
    
    # Case 3: Passive / Reactive
    game_stats_passive = {
        "records": [{
            "first_bloods_percentage": 35.0
        }]
    }
    print("\n3. Testing Passive Detection:")
    weakness_passive = detect_early_aggression(game_stats_passive, team_stats)
    print(json.dumps(weakness_passive, indent=2))
    assert weakness_passive['aggression_style'] == "Passive / Reactive"
    assert "Take map control early" in weakness_passive['counter_strategy']

    print("\n✅ Part 3 Contextual Intelligence Verification Successful!")

if __name__ == "__main__":
    test_contextual_intelligence()


import sys
import os
from datetime import datetime
from pydantic import ValidationError

# Add project root to path
sys.path.append(os.getcwd())

from models.report import ScoutingReport
from jobs.report_generator import finalize_report

def test_full_report_alignment():
    print("Testing Full Report alignment...")
    report_data = {
        "team_id": "team-123",
        "team_name": "Test Team",
        "report_type": "full",
        "macro_analysis": {
            "win_rates": [{"map": "Haven", "wr": 0.6}],
            "recurring_tells": [{"name": "Eco Push", "description": "Pushes A"}]
        },
        "mid_game_analysis": {
            "side_balance": {"atk": 0.5, "def": 0.5},
            "retake_efficiency": {"success": 0.4}
        },
        "micro_analysis": {
            "star_player": {"player_name": "TenZ", "impact_score": 0.9},
            "role_distribution": {"Duelist": 1}
        },
        "actionable_insights": ["Keep doing what you are doing"],
        "time_window": "LAST_6_MONTHS"
    }
    
    # This should NOT raise an exception with our new finalize_report
    try:
        finalize_report(1, report_data)
        print("✅ Full Report finalized successfully")
    except Exception as e:
        print(f"❌ Full Report failed: {e}")

def test_player_report_alignment():
    print("\nTesting Player Report alignment...")
    # Player report might have extra fields or fewer fields than a full report
    report_data = {
        "player_id": "player-456",
        "player_name": "Aspas",
        "report_type": "player_performance",
        "micro_analysis": {
            "star_player": {"player_name": "Aspas", "impact_score": 0.95},
            "agent_pools": [{"agent": "Jett", "matches": 10}]
        },
        "win_rate": 0.75,
        "meta": {"status": "success"}
    }
    
    try:
        finalize_report(2, report_data)
        print("✅ Player Report finalized successfully (filtered via finalize_report)")
    except Exception as e:
        print(f"❌ Player Report failed: {e}")

def test_agent_report_alignment():
    print("\nTesting Agent Report alignment...")
    report_data = {
        "team_name": "Liquid",
        "report_type": "agent_performance",
        "micro_analysis": {
            "agent_pools": [{"player_id": "team", "top_agents": [{"agent_name": "Yoru", "proficiency": "High"}]}]
        },
        "actionable_insights": ["Liquid is good at Yoru"],
        "meta": {"status": "success"}
    }
    
    try:
        finalize_report(3, report_data)
        print("✅ Agent Report finalized successfully")
    except Exception as e:
        print(f"❌ Agent Report failed: {e}")

if __name__ == "__main__":
    # Mock the database upsert to avoid DB dependency in this test
    import jobs.report_generator
    jobs.report_generator.upsert_scouting_report = lambda x: print(f"   [Mock DB] Storing report for {x.get('report_request_id')}")
    
    test_full_report_alignment()
    test_player_report_alignment()
    test_agent_report_alignment()

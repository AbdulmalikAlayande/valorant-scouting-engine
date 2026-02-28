import asyncio
import json
from transforms.insight_generator import generate_90_5_60_report
from models.report import ScoutingReport

async def test_synthesis():
    print("Testing 90-5-60 Report Synthesis...")
    
    # Mock raw data
    raw_data = {
        "team_name": "Team Liquid",
        "report_type": "full",
        "win_rate": 0.65,
        "macro_analysis": {
            "win_rates": [{"map": "Ascent", "win_rate": 0.80}],
            "recurring_tells": [{"name": "Aggressive Eco", "exploit": "Play passive"}]
        },
        "micro_analysis": {
            "star_player": {"player_name": "nAts", "kd": 1.2}
        }
    }
    
    try:
        synthesized = await generate_90_5_60_report(raw_data)
        
        print("\n--- LAYER A: FLASH CARD ---")
        print(json.dumps(synthesized['flash_card'], indent=2))
        
        print("\n--- LAYER B: COACH READ ---")
        print(json.dumps(synthesized['coach_read'], indent=2))
        
        # Validate with ScoutingReport model
        report_data = {**raw_data, **synthesized, "report_request_id": 1}
        report = ScoutingReport(**report_data)
        print("\n✅ ScoutingReport Model Validation Passed")
        
    except Exception as e:
        print(f"\n❌ Synthesis Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_synthesis())

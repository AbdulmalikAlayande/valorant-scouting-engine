
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock environment variables before importing anything that uses settings
os.environ["GRID_API_KEY"] = "mock_key"
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["GRID_STATS_API"] = "http://mock"
os.environ["GRID_QUERY_API"] = "http://mock"
os.environ["GRID_SERIES_STATE_API"] = "http://mock"
os.environ["GEMINI_API_KEY"] = "mock"

from jobs.handler_functions import (
    handle_generate_map_analysis,
    handle_detect_and_exploit_weaknesses,
    handle_composition_analysis
)

def test_handlers_smoke():
    print("--- Starting Handler Smoke Tests ---")
    
    # Mocking ingestion functions to avoid real API calls
    with patch('jobs.handler_functions.ingest_team_by_name') as mock_team, \
         patch('jobs.handler_functions.ingest_team_game_statistics') as mock_game_stats, \
         patch('jobs.handler_functions.ingest_team_statistics') as mock_team_stats, \
         patch('jobs.handler_functions.ingest_team_recent_series') as mock_series, \
         patch('jobs.handler_functions.ingest_series_state') as mock_state:
        
        # Setup mock team
        mock_team_obj = MagicMock()
        mock_team_obj.id = "1079"
        mock_team_obj.name = "Cloud9"
        mock_team.return_value = mock_team_obj
        
        # Setup other mocks with empty/base data
        mock_game_stats.return_value = {"records": [], "meta": {}}
        mock_team_stats.return_value = {"records": [], "meta": {}}
        mock_series.return_value = {"series": []}
        mock_state.return_value = {"series": None}
        
        print("\nTesting handle_generate_map_analysis...")
        map_report = handle_generate_map_analysis("Cloud9", "Ascent", "LAST_3_MONTHS")
        print(f"Map report status: {map_report.get('meta', {}).get('status')}")
        assert map_report['team_name'] == "Cloud9"
        
        print("\nTesting handle_detect_and_exploit_weaknesses...")
        weakness_report = handle_detect_and_exploit_weaknesses("Cloud9", 5, "LAST_3_MONTHS")
        print(f"Weakness report status: {weakness_report.get('meta', {}).get('status')}")
        assert weakness_report['team_name'] == "Cloud9"
        
        print("\nTesting handle_composition_analysis...")
        comp_report = handle_composition_analysis("Cloud9")
        print(f"Composition report status: {comp_report.get('meta', {}).get('status')}")
        assert comp_report['team_name'] == "Cloud9"

    print("\n✅ All handler smoke tests passed!")

if __name__ == "__main__":
    test_handlers_smoke()

import time
import json
import logging
from typing import Dict, Any, List
from storage.db import get_db_cursor
from storage.upsert import update_report_request_status, upsert_scouting_report
from clients.domain.stats import get_team_stats, player_stats
from transforms.team_tendencies import analyze_team_stats
from transforms.player_tendencies import analyze_player_stats

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_pending_reports():
    """
    Main loop to poll for pending report requests and process them.
    """
    logger.info("Starting report generation worker...")
    
    while True:
        try:
            with get_db_cursor() as cursor:
                # Find one pending request
                cursor.execute("""
                    SELECT id, team_id, team_name, time_window 
                    FROM report_requests 
                    WHERE status = 'pending' 
                    ORDER BY created_at ASC 
                    LIMIT 1
                """)
                request = cursor.fetchone()
            
            if request:
                process_request(request)
            else:
                # No pending requests, sleep for a bit
                time.sleep(10)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(10)

def process_request(request: Dict[str, Any]):
    """
    Processes a single report request.
    """
    request_id = request['id']
    team_id = request['team_id']
    team_name = request['team_name']
    time_window = request.get('time_window', 'LAST_3_MONTHS')
    
    logger.info(f"Processing report for {team_name} (ID: {team_id})...")
    
    try:
        # 1. Update status to 'processing'
        update_report_request_status(request_id, 'processing')
        
        # 2. Fetch Team Stats from GRID
        # timeWindow in GRID Stats Feed is usually like LAST_3_MONTHS, LAST_YEAR etc.
        filter_ = {"timeWindow": time_window}
        raw_team_stats = get_team_stats(team_id=team_id, filter_=filter_)
        
        # 3. Analyze Team Tendencies
        analyzed_team = analyze_team_stats(raw_team_stats)
        
        # 4. Fetch and Analyze Player Tendencies (Optional for MVP, but good for "Competitive")
        # In a real scenario, we'd get player IDs from the team info or team stats
        # For now, let's extract them from the team stats if available
        # game -> players -> characters gives us aggregate but not individual player IDs easily without another query
        # Let's keep it simple for now and focus on team-wide insights as per team_tendencies
        
        # 5. Prepare final report data for DB
        report_data = {
            "report_request_id": request_id,
            "team_id": team_id,
            "team_name": team_name,
            "total_matches": analyzed_team.get("total_matches", 0),
            "total_games": analyzed_team.get("total_matches", 0), # Simplified
            "win_rate": analyzed_team.get("win_rate", 0.0),
            "current_streak": 0, # Could be extracted from stats if added to fragment
            "top_agents": json.dumps([agent.dict() for agent in analyzed_team.get("top_agents", [])]),
            "map_performance": json.dumps(analyzed_team.get("map_performance", [])),
            "player_stats": json.dumps([]), # Placeholder
            "actionable_insights": json.dumps(analyzed_team.get("actionable_insights", [])),
            "time_window": time_window
        }
        
        # 6. Save report to DB
        upsert_scouting_report(report_data)
        
        # 7. Update status to 'completed'
        update_report_request_status(request_id, 'completed')
        logger.info(f"Successfully generated report for {team_name}")
        
    except Exception as e:
        logger.error(f"Failed to process report for {team_name}: {e}")
        update_report_request_status(request_id, 'failed', error_message=str(e))

if __name__ == "__main__":
    process_pending_reports()

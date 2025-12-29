import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from storage.upsert import create_report_request
from storage.db import test_connection, get_db_cursor
from jobs.generate_report import process_request
import json

def verify_flow():
    print("🔍 Starting Verification Flow...")
    
    # 1. Test DB Connection
    if not test_connection():
        print("❌ Database connection failed. Make sure PostgreSQL is running.")
        return

    # 2. Create a dummy request
    # Team ID 53625 is Team Liquid in VALORANT
    team_id = "53625"
    team_name = "Team Liquid"
    # Try a different time window or no filter if results are empty
    time_window = "LAST_YEAR" 
    print(f"📝 Creating report request for {team_name} (ID: {team_id}) with {time_window}... ")
    
    try:
        request_id = create_report_request(team_id, team_name, time_window=time_window)
        print(f"✅ Request created with ID: {request_id}")

        # 3. Process the request manually (simulating the worker picking it up)
        print("⚙️ Processing request...")
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM report_requests WHERE id = %s", (request_id,))
            request = cursor.fetchone()
        
        if request:
            process_request(request)
            
            # 4. Verify the results in DB
            print("📊 Verifying results in database...")
            with get_db_cursor() as cursor:
                cursor.execute("SELECT * FROM scouting_reports WHERE report_request_id = %s", (request_id,))
                report = cursor.fetchone()
                
                cursor.execute("SELECT status, error_message FROM report_requests WHERE id = %s", (request_id,))
                status = cursor.fetchone()

            if report:
                print("✅ Scouting Report found in database!")
                print(f"   Win Rate: {report['win_rate']}%")
                print(f"   Total Matches: {report['total_matches']}")
                print(f"   Insights: {report['actionable_insights']}")
            else:
                print("❌ Scouting Report NOT found in database.")
            
            print(f"📌 Request Status: {status['status']}")
            if status['error_message']:
                print(f"⚠️ Error Message: {status['error_message']}")

    except Exception as e:
        print(f"💥 Verification failed with error: {e}")

if __name__ == "__main__":
    verify_flow()

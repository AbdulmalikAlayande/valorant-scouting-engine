
import sys
import os
import asyncio
from typing import Dict, Any

# Add project root to path
sys.path.append(os.getcwd())

from storage.upsert import create_report_request, update_report_request_status
from storage.db import get_db_cursor
from jobs.prompt_router import GeneralPromptRouter
from jobs.report_generator import finalize_report
from transforms.insight_generator import generate_90_5_60_report
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)

async def run_single_job_integration(request_id: int):
    """
    Simulates the logic inside poll_and_process_reports for a single job.
    """
    _logger.info(f"Starting integration check for request {request_id}")
    router = GeneralPromptRouter()
    
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, user_prompt FROM report_requests WHERE id = %s", (request_id,))
        job = cursor.fetchone()
    
    if not job:
        print(f"❌ Job {request_id} not found")
        return

    user_prompt = job['user_prompt']
    print(f"Picked up job {request_id}: '{user_prompt}'")
    
    update_report_request_status(request_id, 'PROCESSING')
    
    try:
        print("Routing prompt through LLM...")
        result = await router.resolve_user_prompt(user_prompt)
        
        if result and isinstance(result, dict):
            report_data = result.get('output') or result.get('response')
            
            if report_data and isinstance(report_data, dict):
                # Check for errors in report_data
                if 'error' in report_data:
                    raise ValueError(report_data['error'])

                # Apply same logic as in report_generator.py
                if 'report_type' not in report_data:
                    if 'player_name' in report_data:
                        report_data['report_type'] = 'player_performance'
                    elif 'map_name' in report_data:
                        report_data['report_type'] = 'map'
                    elif 'team_name_2' in report_data:
                        report_data['report_type'] = 'h2h'
                    else:
                        report_data['report_type'] = 'full'
                
                full_context = {**report_data}
                if 'detailed_analysis' in report_data:
                    full_context.update(report_data['detailed_analysis'])
                
                print("Synthesizing 90-5-60 report...")
                synthesized_report = await generate_90_5_60_report(full_context)
                report_data.update(synthesized_report)
                
                report_data['report_request_id'] = request_id
                print("Finalizing report and storing in DB...")
                finalize_report(request_id, report_data)
                
                update_report_request_status(request_id, 'COMPLETED')
                print(f"✅ Job {request_id} completed successfully")
            else:
                print("❌ Handler returned invalid report structure")
        else:
            print("❌ Router returned invalid result")
            
    except Exception as e:
        print(f"💥 Job {request_id} Failed: {e}")
        update_report_request_status(request_id, 'FAILED', error_message=str(e))

async def main():
    # 1. Create a request
    # NRG vs Cloud9 comparison
    user_prompt = "Scout Team NRG vs Cloud9 in the Last Year"
    
    print(f"Creating request for: {user_prompt}")
    # Fix: create_report_request only takes user_prompt
    request_id = create_report_request(
        user_prompt=user_prompt
    )
    
    # 2. Run processing
    await run_single_job_integration(request_id)
    
    # 3. Verify
    with get_db_cursor() as cursor:
        cursor.execute("SELECT status, error_message FROM report_requests WHERE id = %s", (request_id,))
        req = cursor.fetchone()
        cursor.execute("SELECT count(*) FROM scouting_reports WHERE report_request_id = %s", (request_id,))
        report_count = cursor.fetchone()['count']
        
    print(f"\nSummary:")
    print(f"Status: {req['status']}")
    if req['error_message']:
        print(f"Error: {req['error_message']}")
    print(f"Reports in DB: {report_count}")

if __name__ == "__main__":
    asyncio.run(main())

# storage/upsert.py
from config.globalutilitylogger import get_logger
from storage.db import get_db_cursor
from psycopg2.extras import Json
from typing import Dict, Any

_logger = get_logger(__name__)

def upsert_team(team_id: str, team_name: str, **extra_fields):
    """
    Insert or update a team record.

    Args:
        team_id: GRID team ID
        team_name: Team name
        **extra_fields: logo_url, color_primary, etc.

    Returns:
        team_id (the database primary key)

    Usage:
        upsert_team("53625", "Team Liquid", logo_url="https://...")
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
                INSERT INTO teams (team_id, team_name, logo_url, color_primary, updated_at)
                VALUES (%(team_id)s, %(team_name)s, %(logo_url)s, %(color_primary)s, NOW())
                ON CONFLICT (team_id)
                    DO UPDATE SET team_name    = EXCLUDED.team_name,
                                 logo_url      = EXCLUDED.logo_url,
                                 color_primary = EXCLUDED.color_primary,
                                 updated_at    = NOW()
                RETURNING id
            """,
            {
                'team_id': team_id,
                'team_name': team_name,
                'logo_url': extra_fields.get('logo_url'),
                'color_primary': extra_fields.get('color_primary')
            }
        )

        result = cursor.fetchone()
        return result['id']


def upsert_match(match_data: Dict[str, Any]):
    """
    Insert or update a match record.

    Args:
        match_data: Dict with keys:
            - series_id (required)
            - team_id (required)
            - team_name
            - opponent_id
            - opponent_name
            - map_name
            - won
            - kills
            - deaths
            - assists
            - played_at

    Returns:
        match database ID

    Usage:
        upsert_match({
            'series_id': '2629390',
            'team_id': '53625',
            'team_name': 'Team Liquid',
            'won': True,
            'kills': 245,
            'deaths': 180
        })
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
                INSERT INTO matches (series_id, team_id, team_fk_id, team_name,
                                    opponent_id, opponent_fk_id, opponent_name,
                                    map_name, won, kills, deaths, assists, played_at)
                VALUES (%(series_id)s, %(team_id)s, 
                        get_or_create_team_fk(%(team_id)s, %(team_name)s), 
                        %(team_name)s, %(opponent_id)s,
                        get_or_create_team_fk(%(opponent_id)s, %(opponent_name)s),
                       %(map_name)s, %(won)s, %(kills)s, %(deaths)s, %(assists)s, %(played_at)s)
                ON CONFLICT (series_id)
                    DO UPDATE SET team_name    = EXCLUDED.team_name,
                                 opponent_name = EXCLUDED.opponent_name,
                                 won           = EXCLUDED.won,
                                 kills         = EXCLUDED.kills,
                                 deaths        = EXCLUDED.deaths,
                                 assists       = EXCLUDED.assists
                RETURNING id
            """,
            match_data
        )

        result = cursor.fetchone()
        return result['id']


def upsert_scouting_report(report_data: Dict[str, Any]):
    """
    Insert or update a scouting report.

    Args:
        report_data: Dict with keys:
            - report_request_id
            - team_id
            - team_name
            - total_matches
            - total_games
            - win_rate
            - current_streak
            - top_agents (JSON)
            - map_performance (JSON)
            - player_stats (JSON)
            - actionable_insights (JSON)
            - time_window

    Returns:
        report database ID

    Usage:
        upsert_scouting_report({
            'team_id': '53625',
            'team_name': 'Team Liquid',
            'total_matches': 10,
            'win_rate': 70.0,
            'top_agents': [{'agent': 'Jett', 'pick_rate': 0.80}]
        })
    """
    with get_db_cursor() as cursor:
        # Check if exists
        cursor.execute("SELECT id FROM scouting_reports WHERE report_request_id = %s", (report_data.get('report_request_id'),))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                           UPDATE scouting_reports SET
                               total_matches       = %(total_matches)s,
                               total_games         = %(total_games)s,
                               win_rate            = %(win_rate)s,
                               current_streak      = %(current_streak)s,
                               top_agents          = %(top_agents)s,
                               map_performance     = %(map_performance)s,
                               player_stats        = %(player_stats)s,
                               actionable_insights = %(actionable_insights)s,
                               created_at          = NOW()
                           WHERE report_request_id = %(report_request_id)s
                           RETURNING id
                           """, {
                               'report_request_id': report_data.get('report_request_id'),
                               'total_matches': report_data.get('total_matches', 0),
                               'total_games': report_data.get('total_games', 0),
                               'win_rate': report_data.get('win_rate', 0.0),
                               'current_streak': report_data.get('current_streak', 0),
                               'top_agents': Json(report_data.get('top_agents', [])),
                               'map_performance': Json(report_data.get('map_performance', {})),
                               'player_stats': Json(report_data.get('player_stats', [])),
                               'actionable_insights': Json(report_data.get('actionable_insights', [])),
                           })
        else:
            cursor.execute("""
                           INSERT INTO scouting_reports (report_request_id, team_id, team_name,
                                                         total_matches, total_games, win_rate, current_streak,
                                                         top_agents, map_performance, player_stats, actionable_insights,
                                                         time_window)
                           VALUES (%(report_request_id)s, %(team_id)s, %(team_name)s,
                                   %(total_matches)s, %(total_games)s, %(win_rate)s, %(current_streak)s,
                                   %(top_agents)s, %(map_performance)s, %(player_stats)s, %(actionable_insights)s,
                                   %(time_window)s)
                           RETURNING id
                           """, {
                               'report_request_id': report_data.get('report_request_id'),
                               'team_id': report_data['team_id'],
                               'team_name': report_data['team_name'],
                               'total_matches': report_data.get('total_matches', 0),
                               'total_games': report_data.get('total_games', 0),
                               'win_rate': report_data.get('win_rate', 0.0),
                               'current_streak': report_data.get('current_streak', 0),
                               'top_agents': Json(report_data.get('top_agents', [])),
                               'map_performance': Json(report_data.get('map_performance', {})),
                               'player_stats': Json(report_data.get('player_stats', [])),
                               'actionable_insights': Json(report_data.get('actionable_insights', [])),
                               'time_window': report_data.get('time_window', 'LAST_3_MONTHS')
                           })

        result = cursor.fetchone()
        return result['id']


# storage/upsert.py (UPDATE THIS FUNCTION)

def create_report_request(user_prompt: str) -> int:
    """
    Create a new report generation request with a natural language prompt.

    Args:
        user_prompt: Natural language prompt (e.g., "How does Team Liquid perform on Ascent?")

    Returns:
        request_id for tracking

    Usage:
        request_id = create_report_request("Generate scouting report for Team Liquid")
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
                       INSERT INTO report_requests (user_prompt, status)
                       VALUES (%s, 'pending')
                       RETURNING id
                       """, (user_prompt,))

        result = cursor.fetchone()
        _logger.info(f"Report creation result: {result}")
        _logger.info(f"Report creation result ID: {result['id']}")
        return result['id']


def update_report_request_status(request_id: str, status: str, error_message: str = None):
    """
    Update the status of a report request.

    Why this exists:
    - Python updates status as it processes
    - Java can check status to know when done

    Statuses:
        - 'pending': Waiting to be processed
        - 'processing': Python is working on it
        - 'completed': Report ready
        - 'failed': Something went wrong

    Usage:
        update_report_request_status(123, 'processing')
        # ... do work ...
        update_report_request_status(123, 'completed')
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
                       UPDATE report_requests
                       SET status        = %s,
                           error_message = %s,
                           completed_at  = CASE WHEN %s IN ('completed', 'failed') THEN NOW() ELSE completed_at END
                       WHERE id = %s
                       """, (status, error_message, status, request_id))


if __name__ == "__main__":
    # Test upsert functions
    print("🧪 Testing upsert functions...")

    # Test 1: Upsert team
    print("\n1. Testing upsert_team...")
    team_id = upsert_team("53625", "Team Liquid", logo_url="https://example.com/logo.png")
    print(f"✅ Team inserted/updated with ID: {team_id}")

    # # Test 2: Create a report request
    # print("\n2. Testing create_report_request...")
    # request_id = create_report_request("53625", "Team Liquid")
    # print(f"✅ Report request created with ID: {request_id}")
    #
    # # Test 3: Update status
    # print("\n3. Testing update_report_request_status...")
    # update_report_request_status(request_id, 'processing')
    # print(f"✅ Status updated to 'processing'")

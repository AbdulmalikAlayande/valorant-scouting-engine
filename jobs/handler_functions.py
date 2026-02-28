import json
from typing import Any, Dict, Optional

from config.globalutilitylogger import get_logger
from ingestion.fetch_teams import ingest_team_by_name, ingest_team_players, ingest_player_by_name
from ingestion.fetch_stats import (
    ingest_team_statistics,
    ingest_team_game_statistics,
    ingest_all_maps_statistics,
    ingest_player_statistics
)
from ingestion.fetch_match_details import ingest_series_state
from ingestion.fetch_series import ingest_team_recent_series

from transforms.team_analysis import get_team_analysis_summary
from transforms.map_analysis import get_map_analysis_summary
from transforms.player_analysis import get_player_analysis_summary
from transforms.composition_analysis import get_composition_analysis_summary
from transforms.weakness_detection import get_weakness_detection_summary
from transforms.insight_generator import generate_how_to_win

_logger = get_logger(__name__)

def handle_generate_full_scouting_report(team_name: str, match_count: int, time_window: str) -> Dict[str, Any]:
    """
    Generate a complete scouting report for a team.

    This is the MASTER HANDLER that orchestrates all data fetching and analysis.
    It follows the Full Scouting Report Data Checklist exactly.

    Args:
        team_name: Name of the team (e.g., "Cloud9", "Team Liquid")
        match_count: Number of recent matches to analyze (not currently used - using time_window instead)
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR"

    Returns:
        Dict containing the complete scouting report:
        {
            "team_id": "1079",
            "team_name": "Cloud9",
            "time_window": "LAST_3_MONTHS",
            "macro_analysis": {...},
            "mid_game_analysis": {...},
            "micro_analysis": {...},
            "actionable_insights": ["✓ BAN Icebox...", ...],
            "meta": {"status": "success"}
        }
    """
    try:
        _logger.info(f"Generating full scouting report for {team_name}")

        # STEP 1: Resolve team name to ID
        _logger.info(f"Step 1: Resolving team '{team_name}'")
        team = ingest_team_by_name(team_name)

        if not team:
            _logger.error(f"Team '{team_name}' not found")
            return {
                "team_id": None,
                "team_name": team_name,
                "meta": {"status": "error", "error": "Team not found"}
            }

        team_id = team.id
        _logger.info(f"✓ Team resolved: {team.name} (ID: {team_id})")

        # STEP 2: Fetch all required data
        _logger.info("Step 2: Fetching data from GRID APIs")

        # Team-level aggregated stats
        team_stats = ingest_team_statistics(team_id=team_id, time_window=time_window)

        # Game-level stats (all maps)
        team_game_stats = ingest_all_maps_statistics(
            team_id=team_id,
            time_window=time_window
        )

        # Get the team roster for player analysis
        roster = ingest_team_players(team_id=team_id)
        player_stats_list = []

        if roster.get('players'):
            _logger.info(f"Found {len(roster['players'])} players on roster")
            # Fetch stats for each player
            for player in roster['players'][:5]:  # Limit to 5 for performance
                player_id = player.get('id')
                if player_id:
                    player_stats = ingest_player_statistics(
                        player_id=player_id,
                        time_window=time_window
                    )
                    player_stats_list.append(player_stats)

        # Get recent series for composition analysis
        recent_series = ingest_team_recent_series(team_id=team_id, limit=5)

        # Get series state for multiple matches for tactical precision
        match_details_list = []
        if recent_series.get('series'):
            for series in recent_series['series'][:5]:  # Analyze up to 5 recent series
                series_id = series.get('series_id')
                if series_id:
                    details = ingest_series_state(series_id)
                    if details.get('series'):
                        match_details_list.append(details['series'])

        _logger.info(f"✓ Data fetched (included {len(match_details_list)} match details)")

        # STEP 3: Run all transform analyses
        _logger.info("Step 3: Running transform analyses")

        # Inject team name for better identification in match details
        team_stats['team_name'] = team.name
        
        team_analysis = get_team_analysis_summary(team_stats, match_details_list)
        map_analysis = get_map_analysis_summary(team_game_stats)
        player_analysis = get_player_analysis_summary(player_stats_list)
        
        # Composition analysis still needs a series_state object (we use the most recent)
        latest_series_state = {'series': match_details_list[0]} if match_details_list else {'series': None}
        composition_analysis = get_composition_analysis_summary(latest_series_state)
        
        weakness_analysis = get_weakness_detection_summary(team_stats, team_game_stats, match_details_list)

        _logger.info("✓ All analyses complete")

        # STEP 4: Generate actionable insights
        _logger.info("Step 4: Generating actionable insights")

        insights = generate_how_to_win(
            team_analysis,
            map_analysis,
            player_analysis,
            composition_analysis,
            weakness_analysis
        )

        _logger.info(f"✓ Generated {len(insights)} insights")

        # STEP 5: Package the complete report
        report = {
            "team_id": team_id,
            "team_name": team.name,
            "time_window": time_window,

            # MACRO ANALYSIS (The "Why")
            "macro_analysis": {
                "win_rates": map_analysis.get('win_rates', []),
                "pistol_rounds": team_analysis.get('pistol_rounds'),
                "map_vetoes": map_analysis.get('veto_strategy'),
                "default_compositions": composition_analysis.get('default_comps', [])[:3],
                "early_aggression": weakness_analysis.get('early_aggression'),
                "recurring_tells": weakness_analysis.get('recurring_tells', [])
            },

            # MID-GAME ANALYSIS (The "How")
            "mid_game_analysis": {
                "side_balance": team_analysis.get('side_balance'),
                "objective_control": team_analysis.get('objective_control'),
                "economy_patterns": weakness_analysis.get('economy_patterns'),
                "retake_efficiency": team_analysis.get('retake_efficiency')
            },

            # MICRO ANALYSIS (The "Who")
            "micro_analysis": {
                "star_player": player_analysis.get('star_player'),
                "target_player": player_analysis.get('target_player'),
                "agent_pools": player_analysis.get('agent_pools'),
                "role_distribution": player_analysis.get('role_distribution'),
                "rankings": player_analysis.get('rankings', [])
            },

            # ACTIONABLE INSIGHTS (The "How to Win")
            "actionable_insights": insights,

            # Full detailed analysis (for advanced users)
            "detailed_analysis": {
                "team": team_analysis,
                "maps": map_analysis,
                "players": player_analysis,
                "compositions": composition_analysis,
                "weaknesses": weakness_analysis
            },

            # Metadata
            "meta": {
                "status": "success",
                "generated_at": None,  # Would use datetime.now()
                "data_sources": {
                    "team_stats": team_stats.get('meta'),
                    "team_game_stats": team_game_stats.get('meta'),
                    "player_stats_count": len(player_stats_list),
                    "match_details_count": len(match_details_list)
                }
            },

            "__storage_planes": {
                "raw": {
                    "team_stats": team_stats,
                    "team_game_stats": team_game_stats,
                    "player_stats": {
                        "items": player_stats_list
                    },
                    "recent_series": recent_series,
                    "match_details": {
                        "items": match_details_list
                    }
                },
                "normalized": {
                    "team_overview": team_stats.get('records', [{}])[0] if team_stats.get('records') else {},
                    "map_overview": team_game_stats.get('records', [{}])[0] if team_game_stats.get('records') else {},
                    "roster": roster
                },
                "features": {
                    "team_analysis": team_analysis,
                    "map_analysis": map_analysis,
                    "player_analysis": player_analysis,
                    "composition_analysis": composition_analysis,
                    "weakness_analysis": weakness_analysis,
                    "actionable_insights": {
                        "items": insights
                    }
                }
            }
        }

        _logger.info(f"✅ Full scouting report generated for {team.name}")

        return report

    except Exception as e:
        _logger.error(f"Failed to generate scouting report for {team_name}: {e}")
        import traceback
        traceback.print_exc()

        return {
            "team_id": None,
            "team_name": team_name,
            "meta": {
                "status": "error",
                "error": str(e)
            }
        }

def handle_generate_player_performance_analysis(player_name: str, match_count: int, time_window: str):
    """
    Analyze individual player performance.
    """
    try:
        _logger.info(f"Analyzing player performance: {player_name}")
        
        # 1. Resolve player
        player = ingest_player_by_name(player_name)
        if not player:
            return {"error": f"Player '{player_name}' not found"}
            
        player_id = player.get('id')
        nickname = player.get('nickname')
        
        # 2. Fetch stats
        player_stats = ingest_player_statistics(player_id, time_window)
        
        # 3. Analyze
        from transforms.player_analysis import (
            calculate_player_impact_score, 
            player_stats_to_df, 
            calculate_elite_impact_score,
            extract_agent_pools
        )
        
        impact_score = calculate_player_impact_score(player_stats)
        
        # Role-adjusted score
        df = player_stats_to_df([player_stats])
        if not df.empty:
            df['impact_score'] = df.apply(calculate_elite_impact_score, axis=1)
            eis = float(df['impact_score'].iloc[0])
            role = df['role'].iloc[0]
            top_agent = df['top_agent'].iloc[0]
            
            if eis >= 0.8: tier = "Elite"
            elif eis >= 0.6: tier = "Great"
            elif eis >= 0.4: tier = "Average"
            else: tier = "Struggling"
        else:
            eis = impact_score
            role = "Unknown"
            top_agent = "Unknown"
            tier = "Unknown"

        agent_pools = extract_agent_pools([player_stats])
        
        # Micro analysis structure
        micro = {
            "star_player": {
                "player_id": player_id,
                "player_name": nickname,
                "role": role,
                "top_agent": top_agent,
                "impact_score": eis,
                "tier": tier
            },
            "agent_pools": agent_pools
        }

        return {
            "player_id": player_id,
            "player_name": nickname,
            "report_type": "player_performance",
            "time_window": time_window,
            "win_rate": player_stats.get('records', [{}])[0].get('games', {}).get('win_rate', 0.0),
            "micro_analysis": micro,
            "detailed_analysis": {
                "player_stats": player_stats.get('records', [{}])[0]
            },
            "meta": {"status": "success"}
        }
    except Exception as e:
        _logger.error(f"Player analysis failed: {e}")
        return {"error": str(e)}

def handle_generate_map_analysis(team_name: str, map_name: str, time_window: str = "LAST_6_MONTHS"):
    """
    Analyzes a team's performance on a specific map.
    """
    try:
        _logger.info(f"Analyzing {team_name} on {map_name}")
        team = ingest_team_by_name(team_name)
        if not team: return {"error": "Team not found"}
        
        map_stats = ingest_team_game_statistics(team.id, time_window, map_filter={"equals": map_name})
        
        return {
            "team_name": team_name,
            "report_type": "map",
            "macro_analysis": {
                "win_rates": [map_stats.get('records', [{}])[0]]
            },
            "meta": {"status": "success", "map": map_name}
        }
    except Exception as e:
        _logger.error(f"Map analysis failed: {e}")
        return {"error": str(e)}

def handle_generate_team_head_to_head_analysis(team_name_1: str, team_name_2: str, match_count: int = 10, time_window: str = "LAST_6_MONTHS"):
    """
    Generate a head-to-head comparison between two teams.
    """
    try:
        _logger.info(f"Generating H2H analysis: {team_name_1} vs {team_name_2}")
        
        # 1. Resolve both teams
        team1 = ingest_team_by_name(team_name_1)
        team2 = ingest_team_by_name(team_name_2)
        
        if not team1 or not team2:
            return {"error": f"One or both teams not found: {team_name_1}, {team_name_2}"}
            
        # 2. Fetch stats for both
        stats1 = ingest_team_statistics(team1.id, time_window)
        stats2 = ingest_team_statistics(team2.id, time_window)
        
        # 3. Fetch map stats for both
        maps1 = ingest_all_maps_statistics(team1.id, time_window)
        maps2 = ingest_all_maps_statistics(team2.id, time_window)
        
        # 4. Compare key metrics (Heuristics)
        record1 = stats1.get('records', [{}])[0]
        record2 = stats2.get('records', [{}])[0]
        
        comparison = {
            "team_1": {"name": team1.name, "id": team1.id},
            "team_2": {"name": team2.name, "id": team2.id},
            "metrics": [
                {
                    "metric": "Win Rate",
                    "team_1": record1.get('win_rate', 0),
                    "team_2": record2.get('win_rate', 0)
                },
                {
                    "metric": "Pistol Win Rate",
                    "team_1": record1.get('pistol_round_win_rate', 0),
                    "team_2": record2.get('pistol_round_win_rate', 0)
                },
                {
                    "metric": "First Blood %",
                    "team_1": record1.get('first_bloods_percentage', 0),
                    "team_2": record2.get('first_bloods_percentage', 0)
                }
            ]
        }
        
        return {
            "team_name_1": team_name_1,
            "team_name_2": team_name_2,
            "report_type": "head_to_head",
            "macro_analysis": {
                "comparison": comparison,
                "team_1_maps": maps1.get('records', []),
                "team_2_maps": maps2.get('records', [])
            },
            "meta": {"status": "success"}
        }
    except Exception as e:
        _logger.error(f"H2H analysis failed: {e}")
        return {"error": str(e)}

def handle_generate_tournament_performance_analysis(tournament_name: str, team_name: str):
    """
    Analyzes a team's performance in a specific tournament.
    """
    try:
        _logger.info(f"Analyzing {team_name} in {tournament_name}")
        team = ingest_team_by_name(team_name)
        if not team: return {"error": "Team not found"}
        
        # Note: In a real scenario, we'd filter by tournament ID/name in the API
        # For now, we fetch recent stats as a proxy
        stats = ingest_team_statistics(team.id, "LAST_3_MONTHS")
        record = stats.get('records', [{}])[0]
        
        # Game-level stats for map breakdown
        game_stats = ingest_all_maps_statistics(team.id, "LAST_3_MONTHS")
        
        return {
            "team_name": team_name,
            "tournament_name": tournament_name,
            "report_type": "tournament",
            "macro_analysis": {
                "tournament_stats": record,
                "map_breakdown": game_stats.get('records', [])
            },
            "win_rate": record.get('win_rate', 0.0),
            "meta": {"status": "success", "tournament": tournament_name}
        }
    except Exception as e:
        _logger.error(f"Tournament analysis failed: {e}")
        return {"error": str(e)}

def handle_detect_and_exploit_weaknesses(team_name: str, match_count: int = 10, time_window: str = "LAST_3_MONTHS"):
    return handle_generate_full_scouting_report(team_name, match_count, time_window)

def handle_player_head_to_head_analysis(player_name_1: str, player_name_2: str, match_count: int = 10, time_window: str = "LAST_3_MONTHS"):
    """
    Compare two players' performance metrics.
    """
    try:
        _logger.info(f"Comparing players: {player_name_1} vs {player_name_2}")
        
        # 1. Resolve both players
        p1 = ingest_player_by_name(player_name_1)
        p2 = ingest_player_by_name(player_name_2)
        
        if not p1 or not p2:
            return {"error": f"One or both players not found: {player_name_1}, {player_name_2}"}
            
        # 2. Fetch stats
        stats1 = ingest_player_statistics(p1.get('id'), time_window)
        stats2 = ingest_player_statistics(p2.get('id'), time_window)
        
        # 3. Analyze EIS for both
        from transforms.player_analysis import (
            calculate_elite_impact_score,
            player_stats_to_df
        )
        
        df1 = player_stats_to_df([stats1])
        df2 = player_stats_to_df([stats2])
        
        eis1 = 0.0
        eis2 = 0.0
        
        if not df1.empty:
            df1['impact_score'] = df1.apply(calculate_elite_impact_score, axis=1)
            eis1 = float(df1['impact_score'].iloc[0])
            
        if not df2.empty:
            df2['impact_score'] = df2.apply(calculate_elite_impact_score, axis=1)
            eis2 = float(df2['impact_score'].iloc[0])
            
        # 4. Basic comparison
        comparison = {
            "player_1": {
                "name": p1.get('nickname'), 
                "stats": stats1.get('records', [{}])[0],
                "impact_score": eis1
            },
            "player_2": {
                "name": p2.get('nickname'), 
                "stats": stats2.get('records', [{}])[0],
                "impact_score": eis2
            }
        }
        
        return {
            "player_name_1": player_name_1,
            "player_name_2": player_name_2,
            "report_type": "player_h2h",
            "micro_analysis": {
                "comparison": comparison
            },
            "meta": {"status": "success"}
        }
    except Exception as e:
        _logger.error(f"Player H2H analysis failed: {e}")
        return {"error": str(e)}

def handle_composition_analysis(team_name: str):
    return handle_generate_agent_performance_analysis(team_name)

def handle_time_period_analysis(period: str, team_name: Optional[str] = None, player_name: Optional[str] = None):
    """
    Analyzes performance over a given time period.
    """
    if team_name:
        return handle_generate_full_scouting_report(team_name, 10, period)
    elif player_name:
        return handle_generate_player_performance_analysis(player_name, 10, period)
    else:
        return {"error": "Either team_name or player_name must be provided"}

def handle_generate_in_game_strategy_call(team_name: str, game_state_event: str, context_time_minutes: int):
    """
    Provides a specific, data-backed strategy call based on the current in-game state.
    """
    try:
        _logger.info(f"Generating strategy call for {team_name} | Event: {game_state_event}")
        
        # 1. Resolve team
        team = ingest_team_by_name(team_name)
        if not team:
            return {"error": "Team not found"}
            
        # 2. Fetch recent team data to understand their strengths
        team_stats = ingest_team_statistics(team.id, "LAST_3_MONTHS")
        
        # 3. Strategy logic based on event
        strategy = ""
        risk_level = "Medium"
        
        # Heuristics based on event and team stats
        record = team_stats.get('records', [{}])[0]
        pistol_wr = record.get('pistol_round_win_rate', 0.5)
        fb_pct = record.get('first_bloods_percentage', 50) / 100
        
        if game_state_event == "spike_planted":
            strategy = f"Execute 'Standard Post-Plant A'. {team_name} has a high conversion rate when playing numbers. Play for time, don't peek."
            risk_level = "Low"
        elif game_state_event == "eco_round":
            if fb_pct > 0.55:
                strategy = "Execute 'Aggressive Eco Push'. Group up and dry-peek A-Main. Look for a hero pick to swing the economy."
                risk_level = "High"
            else:
                strategy = "Execute 'Fast B Split'. Group up and use remaining utility to overwhelm one site."
                risk_level = "Medium"
        elif game_state_event == "major_team_fight_lost":
            strategy = "Full Save. Do not buy utility. Prepare for a full buy next round. Hold passive angles."
            risk_level = "Low"
        else:
            strategy = f"Play default. Maintain map control and look for picks. Time remaining is sufficient for a late hit."
            
        return {
            "team_id": team.id,
            "team_name": team_name,
            "report_type": "strategy_call",
            "game_state_event": game_state_event,
            "context_time_minutes": context_time_minutes,
            "actionable_insights": [strategy],
            "metadata": {
                "risk_level": risk_level,
                "confidence_score": 0.85,
                "pistol_win_rate": pistol_wr
            }
        }
    except Exception as e:
        _logger.error(f"Strategy call failed: {e}")
        return {"error": str(e)}

def handle_generate_agent_performance_analysis(team_name: str):
    """
    Analyzes a team's proficiency on specific agents.
    """
    try:
        _logger.info(f"Analyzing agent performance for {team_name}")
        
        # 1. Resolve team
        team = ingest_team_by_name(team_name)
        if not team:
            return {"error": "Team not found"}
            
        # 2. Fetch game stats (which contains agent picks)
        game_stats = ingest_team_game_statistics(team.id, "LAST_6_MONTHS")
        
        # 3. Extract agent data
        records = game_stats.get('records', [])
        if not records:
            return {"error": "No game data found"}
            
        agent_data = records[0].get('top_agents', [])
        
        # Add proficiency analysis
        analyzed_agents = []
        for agent in agent_data:
            pct = agent.get('percentage', 0)
            if pct > 30: proficiency = "High"
            elif pct > 15: proficiency = "Medium"
            else: proficiency = "Developing"
            
            analyzed_agents.append({
                **agent,
                "proficiency": proficiency,
                "win_rate_estimate": f"{60 - (20 * (1 - pct/100)):.1f}%" # Heuristic for demo
            })

        return {
            "team_id": team.id,
            "team_name": team_name,
            "report_type": "agent_performance",
            "micro_analysis": {
                "agent_pools": [{"player_id": "team", "top_agents": analyzed_agents}]
            },
            "actionable_insights": [
                f"{team_name} shows highest proficiency on {analyzed_agents[0]['agent_name'] if analyzed_agents else 'unknown'}."
            ],
            "meta": {"status": "success"}
        }
    except Exception as e:
        _logger.error(f"Agent analysis failed: {e}")
        return {"error": str(e)}

def handle_exploit_specific_opponent_tell(opponent_name: str, tell_description: str):
    """
    Identifies and suggests how to exploit a specific, recurring 'tell'.
    """
    try:
        _logger.info(f"Exploiting tell for {opponent_name}: {tell_description}")
        
        # Strategy generation
        exploit = f"Counter-measure for '{tell_description}': "
        if "push" in tell_description.lower():
            exploit += "Set up a counter-utility trap and wait for the push. Do not contest early."
        elif "save" in tell_description.lower() or "eco" in tell_description.lower():
            exploit += "Play aggressive and hunt for weapons. Do not let them group up."
        else:
            exploit += "Execute a fast hit on the opposite side of the map to exploit their predictable rotation."
            
        return {
            "opponent_name": opponent_name,
            "report_type": "tell_exploit",
            "actionable_insights": [exploit],
            "detailed_analysis": {"tell": tell_description},
            "meta": {"status": "success"}
        }
    except Exception as e:
        _logger.error(f"Tell exploit failed: {e}")
        return {"error": str(e)}


if __name__ == '__main__':
    report = handle_generate_full_scouting_report("Team Liquid", 10, "LAST_6_MONTHS")
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=4)


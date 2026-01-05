"""
Ingestion Layer Output Validator
=================================
"""

import json
from pathlib import Path
from ingestion.fetch_teams import ingest_team_by_name
from ingestion.fetch_stats import (
    ingest_team_statistics,
    ingest_team_game_statistics,
    ingest_player_statistics
)
from ingestion.fetch_match_details import ingest_series_state
from ingestion.fetch_series import ingest_team_recent_series

OUTPUT_DIR = Path(__file__).parent / "ingestion_output_samples"
OUTPUT_DIR.mkdir(exist_ok=True)


def validate_team_statistics():
    """Validate team-level aggregated stats (Stats Feed API)"""
    print("\n🔍 Testing: ingest_team_statistics()")

    result = ingest_team_statistics(
        team_id="1079",  # Cloud9 VALORANT team
        time_window="LAST_6_MONTHS"
    )

    # Save full output
    with open(OUTPUT_DIR / "team_statistics_output.json", "w") as f:
        json.dump(result, f, indent=2)

    # Print structure
    print("✅ Output structure:")
    print(f"  - Keys: {list(result.keys())}")
    print(f"  - Meta status: {result.get('meta', {}).get('status')}")
    print(f"  - Records count: {len(result.get('records', []))}")

    if result.get('records'):
        record = result['records'][0]
        print(f"  - Record keys: {list(record.keys())}")
        print(f"  - Total games: {record.get('total_games')}")
        print(f"  - Game win rate: {record.get('game_win_rate')}")
        print(f"  - Attack win rate: {record.get('attack_win_rate')}")
        print(f"  - Defense win rate: {record.get('defense_win_rate')}")

    return result


def validate_team_game_statistics():
    """Validate game-level stats (map-specific)"""
    print("\n🔍 Testing: ingest_team_game_statistics()")

    result = ingest_team_game_statistics(
        team_id="1079",
        time_window="LAST_6_MONTHS",
        map_filter=None,  # All maps
        opponent_team_ids=["79", "94"]
    )

    with open(OUTPUT_DIR / "team_game_statistics_output.json", "w") as f:
        json.dump(result, f, indent=2)

    print("✅ Output structure:")
    print(f"  - Keys: {list(result.keys())}")
    print(f"  - Meta status: {result.get('meta', {}).get('status')}")
    print(f"  - Records count: {len(result.get('records', []))}")

    if result.get('records'):
        record = result['records'][0]
        print(f"  - Record keys: {list(record.keys())}")
        print(f"  - Game count: {record.get('game_count')}")
        print(f"  - Top agents: {record.get('top_agents', [])[:3]}")
        print(f"  - Avg money: {record.get('avg_money')}")

    return result


def validate_player_statistics():
    """Validate player-level stats"""
    print("\n🔍 Testing: ingest_player_statistics()")

    # First get a team roster to find a player ID
    team = ingest_team_by_name("Cloud9")
    print(f"  - Team ID: {team.id if team else 'Not found'}")

    # For now, use a known player ID (you'll need to get this from the roster)
    result = ingest_player_statistics(
        player_id="2512",
        time_window="LAST_3_MONTHS"
    )

    with open(OUTPUT_DIR / "player_statistics_output.json", "w") as f:
        json.dump(result, f, indent=2)

    print("✅ Output structure:")
    print(f"  - Keys: {list(result.keys())}")
    print(f"  - Meta status: {result.get('meta', {}).get('status')}")
    print(f"  - Records count: {len(result.get('records', []))}")

    if result.get('records'):
        record = result['records'][0]
        print(f"  - Record keys: {list(record.keys())}")
        print(f"  - Player ID: {record.get('player_id')}")
        print(f"  - Games count: {record.get('games', {}).get('count')}")
        print(
            f"  - Combat K/D: {record.get('combat', {}).get('kills', {}).get('total')} / {record.get('combat', {}).get('deaths', {}).get('total')}")

    return result


def validate_series_state():
    """Validate series state (composition data)"""
    print("\n🔍 Testing: ingest_series_state()")

    # First get a recent series ID
    recent_series = ingest_team_recent_series(
        team_id="1079",
        limit=1
    )

    if not recent_series.get('series'):
        print("❌ No recent series found")
        return None

    series_id = recent_series['series'][0]['series_id']
    print(f"  - Using series ID: {series_id}")

    result = ingest_series_state(series_id=series_id)

    with open(OUTPUT_DIR / "series_state_output.json", "w") as f:
        json.dump(result, f, indent=2)

    print("✅ Output structure:")
    print(f"  - Keys: {list(result.keys())}")
    print(f"  - Meta status: {result.get('meta', {}).get('status')}")

    if result.get('series'):
        series = result['series']
        print(f"  - Series keys: {list(series.keys())}")
        print(f"  - Games count: {len(series.get('games', []))}")
        print(f"  - Agent picks: {len(series.get('agent_picks', []))} agents")
        print(f"  - Compositions: {len(series.get('compositions', []))} unique comps")

    return result


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("INGESTION OUTPUT VALIDATION")
    print("=" * 60)

    try:
        # Test each ingestion function
        team_stats = validate_team_statistics()
        team_game_stats = validate_team_game_statistics()
        player_stats = validate_player_statistics()
        series_state = validate_series_state()

        print("\n" + "=" * 60)
        print("✅ ALL VALIDATIONS COMPLETE")
        print(f"📁 Output samples saved to: {OUTPUT_DIR}")
        print("=" * 60)

        # Create summary
        summary = {
            "team_statistics": {
                "status": team_stats.get('meta', {}).get('status') if team_stats else "failed",
                "records": len(team_stats.get('records', [])) if team_stats else 0
            },
            "team_game_statistics": {
                "status": team_game_stats.get('meta', {}).get('status') if team_game_stats else "failed",
                "records": len(team_game_stats.get('records', [])) if team_game_stats else 0
            },
            "player_statistics": {
                "status": player_stats.get('meta', {}).get('status') if player_stats else "failed",
                "records": len(player_stats.get('records', [])) if player_stats else 0
            },
            "series_state": {
                "status": series_state.get('meta', {}).get('status') if series_state else "failed",
                "games": len(series_state.get('series', {}).get('games', [])) if series_state else 0
            }
        }

        with open(OUTPUT_DIR / "validation_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()

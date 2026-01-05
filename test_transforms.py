"""
Transform Module Integration Test
==================================
Tests that all transform modules work with real GRID data.
"""

import json
from pathlib import Path
from ingestion.fetch_stats import (
    ingest_team_statistics,
    ingest_team_game_statistics,
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

OUTPUT_DIR = Path(__file__).parent / "transform_test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def test_team_analysis():
    """Test team_analysis.py with real data"""
    print("\n" + "=" * 60)
    print("TEST 1: Team Analysis")
    print("=" * 60)

    # Fetch data
    print("Fetching team statistics...")
    team_stats = ingest_team_statistics(team_id="1079", time_window="LAST_6_MONTHS")

    # Run analysis
    print("Running team analysis...")
    analysis = get_team_analysis_summary(team_stats)

    # Save output
    with open(OUTPUT_DIR / "team_analysis_output.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    print("\n✅ Team Analysis Results:")
    print(f"  - Overall game WR: {analysis['win_rates']['games']['win_rate']:.1%}")
    print(f"  - Attack WR: {analysis['side_balance']['attack']['win_rate']:.1%}")
    print(f"  - Defense WR: {analysis['side_balance']['defense']['win_rate']:.1%}")
    print(f"  - Side bias: {analysis['side_balance']['bias']}")
    print(f"  - K/D ratio: {analysis['combat_metrics']['kd_ratio']:.2f}")

    return analysis


def test_map_analysis():
    """Test map_analysis.py with real data"""
    print("\n" + "=" * 60)
    print("TEST 2: Map Analysis")
    print("=" * 60)

    # Fetch data
    print("Fetching team game statistics...")
    team_game_stats = ingest_team_game_statistics(
        team_id="1079",
        time_window="LAST_6_MONTHS"
    )

    # Run analysis
    print("Running map analysis...")
    analysis = get_map_analysis_summary(team_game_stats)

    # Save output
    with open(OUTPUT_DIR / "map_analysis_output.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    print("\n✅ Map Analysis Results:")
    veto = analysis.get('veto_strategy', {})
    if veto.get('stronghold'):
        print(f"  - Stronghold: {veto['stronghold']['map_name']} ({veto['stronghold']['win_rate']:.1%})")
    if veto.get('permaban'):
        print(f"  - Permaban: {veto['permaban']['map_name']} ({veto['permaban']['win_rate']:.1%})")

    pool = analysis.get('map_pool_depth', {})
    print(f"  - Competitive maps: {pool.get('competitive_maps', 0)}/{pool.get('total_maps_played', 0)}")

    return analysis


def test_player_analysis():
    """Test player_analysis.py with real data"""
    print("\n" + "=" * 60)
    print("TEST 3: Player Analysis")
    print("=" * 60)

    # For this test, I'll use a single player
    # In real handler, we'd fetch all team players
    print("Fetching player statistics...")
    player_stats = ingest_player_statistics(
        player_id="2512",
        time_window="LAST_6_MONTHS"
    )

    # Run analysis
    print("Running player analysis...")
    analysis = get_player_analysis_summary([player_stats])

    # Save output
    with open(OUTPUT_DIR / "player_analysis_output.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    print("\n✅ Player Analysis Results:")
    star = analysis.get('star_player')
    if star:
        print(f"  - Star player: {star.get('player_id')} (K/D: {star.get('kd_ratio')})")

    weak = analysis.get('weak_link')
    if weak:
        print(f"  - Weak link: {weak.get('player_id')} (K/D: {weak.get('kd_ratio')})")

    return analysis


def test_composition_analysis():
    """Test composition_analysis.py with real data"""
    print("\n" + "=" * 60)
    print("TEST 4: Composition Analysis")
    print("=" * 60)

    # Get a recent series
    print("Fetching recent series...")
    recent_series = ingest_team_recent_series(team_id="1079", limit=1)

    if not recent_series.get('series'):
        print("⚠️  No recent series found - skipping composition analysis")
        return {}

    series_id = recent_series['series'][0]['series_id']

    # Fetch series state
    print(f"Fetching series state for {series_id}...")
    series_state = ingest_series_state(series_id)

    if not series_state.get('series'):
        print("⚠️  No series state data - skipping composition analysis")
        return {}

    # Run analysis
    print("Running composition analysis...")
    analysis = get_composition_analysis_summary(series_state)

    # Save output
    with open(OUTPUT_DIR / "composition_analysis_output.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    print("\n✅ Composition Analysis Results:")
    comps = analysis.get('default_comps', [])
    if comps:
        top_comp = comps[0]
        print(f"  - Top comp: {', '.join(top_comp['composition'][:5])}")
        print(f"  - Used in {top_comp['games']} games")

    picks = analysis.get('agent_pick_rates', [])
    if picks:
        top_3 = picks[:3]
        print(f"  - Top 3 agents: {', '.join([f"{p['agent']} ({p['pick_rate']:.0%})" for p in top_3])}")

    return analysis


def test_weakness_detection():
    """Test weakness_detection.py with real data"""
    print("\n" + "=" * 60)
    print("TEST 5: Weakness Detection")
    print("=" * 60)

    # Fetch data
    print("Fetching team statistics and game statistics...")
    team_stats = ingest_team_statistics(team_id="1079", time_window="LAST_3_MONTHS")
    team_game_stats = ingest_team_game_statistics(team_id="1079", time_window="LAST_3_MONTHS")

    # Run analysis
    print("Running weakness detection...")
    analysis = get_weakness_detection_summary(team_stats, team_game_stats)

    # Save output
    with open(OUTPUT_DIR / "weakness_detection_output.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    print("\n✅ Weakness Detection Results:")

    early_agg = analysis.get('early_aggression', {})
    print(f"  - Aggression level: {early_agg.get('aggression_level')}")
    print(f"  - Exploitable: {early_agg.get('exploitable')}")

    economy = analysis.get('economy_patterns', {})
    print(f"  - Economy style: {economy.get('economy_style')}")

    side_weak = analysis.get('side_weaknesses', {})
    print(f"  - Weak side: {side_weak.get('weak_side')}")

    return analysis


def test_insight_generator():
    """Test insight_generator.py - the final synthesis"""
    print("\n" + "=" * 60)
    print("TEST 6: Insight Generation (THE BRAIN)")
    print("=" * 60)

    print("Running ALL analyses and generating insights...")

    # Fetch all data
    team_stats = ingest_team_statistics(team_id="1079", time_window="LAST_3_MONTHS")
    team_game_stats = ingest_team_game_statistics(team_id="1079", time_window="LAST_3_MONTHS")
    player_stats = ingest_player_statistics(player_id="2512", time_window="LAST_3_MONTHS")

    # Get a series for composition
    recent_series = ingest_team_recent_series(team_id="1079", limit=1)
    if recent_series.get('series'):
        series_id = recent_series['series'][0]['series_id']
        series_state = ingest_series_state(series_id)
    else:
        series_state = {'series': None}

    # Run all analyses
    team_analysis = get_team_analysis_summary(team_stats)
    map_analysis = get_map_analysis_summary(team_game_stats)
    player_analysis = get_player_analysis_summary([player_stats])
    composition_analysis = get_composition_analysis_summary(series_state)
    weakness_analysis = get_weakness_detection_summary(team_stats, team_game_stats)

    # Generate insights
    insights = generate_how_to_win(
        team_analysis,
        map_analysis,
        player_analysis,
        composition_analysis,
        weakness_analysis
    )

    # Save output
    with open(OUTPUT_DIR / "insights_output.json", "w") as f:
        json.dump({"insights": insights}, f, indent=2)

    # Print insights
    print("\n✅ GENERATED INSIGHTS (How to Win):")
    print("=" * 60)
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")
    print("=" * 60)

    return insights


def main():
    """Run all tests"""
    print("=" * 60)
    print("TRANSFORM MODULE INTEGRATION TEST")
    print("Testing with Cloud9 VALORANT (Team ID: 1079)")
    print("=" * 60)

    try:
        # Run all tests
        test_team_analysis()
        test_map_analysis()
        test_player_analysis()
        test_composition_analysis()
        test_weakness_detection()
        test_insight_generator()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print(f"📁 Outputs saved to: {OUTPUT_DIR}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()

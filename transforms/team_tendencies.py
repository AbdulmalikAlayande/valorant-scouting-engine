from typing import Any

import pandas as pd
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def calculate_win_rates(team_game_stats: dict) -> pd.DataFrame:
    """
    Business Value: Determines map pool depth and comfort zones.
    What: Computes overall win rate and map-specific win rates, including side dominance.
    Why: Vital for the "Map Performance" section of the report.
    """
    if not team_game_stats or "records" not in team_game_stats:
        _logger.warning("No team game stats records provided.")
        return pd.DataFrame()

    records = team_game_stats.get("records", [])
    if not records:
        return pd.DataFrame()

    # Create a DataFrame from the records
    df = pd.DataFrame(records)
    
    # We want to ensure we have a 'game_win_rate' column
    if 'game_win_rate' not in df.columns:
        _logger.warning("Column 'game_win_rate' missing from game stats records.")
        return df

    # In professional scouting, we also look at side-dominance
    # Calculate side-based performance if data is available
    if 'attack_win_rate' in df.columns and 'defense_win_rate' in df.columns:
        df['side_bias'] = df['attack_win_rate'] - df['defense_win_rate']
        # Bias > 10% means Attack-heavy, < -10% means Defense-heavy
    
    return df

def analyze_map_veto_strategy(map_stats: pd.DataFrame):
    """
    Business Value: Direct advice for the pick/ban phase.
    What: Identifies the team's "Permaban" and "Stronghold" and generates insights.
    Why: Provides the first "Actionable Insight" for coaches.
    """
    if map_stats.empty:
        return {"permaban": None, "stronghold": None, "insights": []}
    
    insights = []
    
    # Sort by play count and win rate
    significant_maps = map_stats[map_stats['game_count'] >= 3]
    if significant_maps.empty:
        significant_maps = map_stats # Fallback to all maps
        
    sorted_stats = significant_maps.sort_values(by=['game_win_rate', 'game_count'], ascending=False)
    
    stronghold = sorted_stats.iloc[0].to_dict() if not sorted_stats.empty else None
    if stronghold:
        insights.append(f"✓ Stronghold: {stronghold['map_filter']} ({stronghold['game_win_rate']:.1f}% win rate over {stronghold['game_count']} games).")
        if 'side_bias' in stronghold:
            bias = stronghold['side_bias']
            if bias > 10:
                insights.append(f"  - Note: Highly dominant on Attack side for {stronghold['map_filter']}. Recommend picking Attack-heavy maps to counter.")
            elif bias < -10:
                insights.append(f"  - Note: Highly dominant on Defense side for {stronghold['map_filter']}. Recommend picking Defense-heavy maps to counter.")

    # Permaban: least games played or lowest win rate?
    permaban_candidates = map_stats.sort_values(by=['game_win_rate', 'game_count'], ascending=True)
    permaban = permaban_candidates.iloc[0].to_dict() if not permaban_candidates.empty else None
    if permaban:
        insights.append(f"⚠ Permaban Candidate: {permaban['map_filter']} ({permaban['game_win_rate']:.1f}% win rate). Recommend picking against them here.")
    
    # Form Factor Insights (if map_stats contains recent form data)
    # Note: strategic trends are handled by detect_strategic_trends, 
    # but we could add a summary here if desired.

    return {
        "stronghold": stronghold.get("map_filter") if stronghold else None,
        "stronghold_wr": stronghold.get("game_win_rate") if stronghold else None,
        "permaban": permaban.get("map_filter") if permaban else None,
        "permaban_wr": permaban.get("game_win_rate") if permaban else None,
        "insights": insights
    }

def detect_strategic_trends(team_series_data: dict):
    """
    Business Value: Understanding current momentum (Form Factor).
    What: Analyzes match history to find win/loss streaks and form.
    Why: Helps coaches understand if the opponent is peaking or crashing.
    """
    if not team_series_data or "series" not in team_series_data:
        return {"momentum": "unknown", "recent_form": []}

    series_list = team_series_data.get("series", [])
    if not series_list:
        return {"momentum": "unknown", "recent_form": []}

    df = pd.DataFrame(series_list)
    # Sort by time
    df['start_time'] = pd.to_datetime(df['start_time'])
    df = df.sort_values('start_time', ascending=True)

    # Calculate form (last 5 games)
    recent_series = df.tail(5)
    
    # Extract 'W' or 'L' based on the 'won' status in series teams
    form = []
    team_id = team_series_data.get("team_id")
    
    for _, row in recent_series.iterrows():
        teams = row.get("teams", [])
        for t in teams:
            if t.get("team_id") == team_id:
                form.append("W" if t.get("won") else "L")
                break

    # Determine momentum
    momentum = "stable"
    if len(form) >= 3:
        if all(x == "W" for x in form[-3:]):
            momentum = "hot"
        elif all(x == "L" for x in form[-3:]):
            momentum = "cold"
    elif len(form) > 0:
        if form[-1] == "W":
            momentum = "rising"
        else:
            momentum = "shaky"

    return {
        "momentum": momentum,
        "recent_form": form,
        "win_streak": (form[::-1] + ["L"]).index("L") if "L" in form else len(form),
        "loss_streak": (form[::-1] + ["W"]).index("W") if "W" in form else len(form)
    }

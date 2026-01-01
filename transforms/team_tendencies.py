import pandas as pd
from ingest.fetch_stats import ingest_team_statistics, ingest_team_game_statistics
from ingest.fetch_series import ingest_team_recent_series, ingest_series_by_time_range
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def calculate_win_rates(team_game_stats):
    """
    What: Computes overall win rate and map-specific win rates.
    Why: Vital for the "Map Performance" section of the report.
    """
    if team_game_stats is None:
        _logger.info("No team game stats provided.")
        return

    dataframe = pd.json_normalize(team_game_stats)
    print(dataframe.head(10))
    _logger.info(dataframe.head(10))


def analyze_map_veto_strategy(map_status):
    """
    What: Identifies the team's "Permaban" (least played/lowest win rate) and "Stronghold" (most played/highest win rate).
    Why: Provides the first "Actionable Insight" for coaches: what to ban and what to pick.
    """
    pass

def detect_strategic_trends(game_strategies):
    """
    What: Analyzes match history to find win/loss streaks and form. And/Or recent games for shifts in strategy (e.g., more aggressive play, new compositions).
    Why: Helps coaches understand if the opponent is currently on an upswing or struggling. And Supports the "Recent Trends" section and offers insights into evolving team tactics.
    """
    pass


if __name__ == '__main__':
    statistics = ingest_team_game_statistics(team_id="1079", time_window="LAST_YEAR")
    calculate_win_rates(statistics)

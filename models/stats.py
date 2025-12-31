"""
Data models for team statistics from GRID API.

These models provide type safety, validation, and clear structure for:
1. TeamStatistics - Overall team stats (series and games)
2. TeamGameStatistics - Per-game/map statistics
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AgentPick:
    """Agent pick data with count and percentage."""
    agent_id: str
    agent_name: str
    count: int
    percentage: float


@dataclass
class WinStreak:
    """Win streak information."""
    max: int
    current: int


@dataclass
class SideStats:
    """Statistics for attack or defense side."""
    rounds: int
    wins: int
    win_rate: float


@dataclass
class ObjectiveStats:
    """Statistics for a specific objective type."""
    count_sum: int
    count_avg: float
    completed_first_percentage: float = 0.0


# Base class with shared game-level fields
@dataclass(kw_only=True)
class BaseGameStats:
    """Shared game-level statistics fields."""

    # Combat stats
    kills_total: int
    kills_avg: float
    kills_min: int = 0
    kills_max: int = 0

    deaths_total: int
    deaths_avg: float
    deaths_min: int = 0
    deaths_max: int = 0

    assists_total: int
    assists_avg: float

    kd_ratio: float

    # First bloods
    first_bloods_percentage: float

    # Economy
    avg_net_worth: float
    avg_spend: float = 0.0  # Called 'money' in game stats
    avg_inventory_value: float = 0.0  # Only in game stats


@dataclass(kw_only=True)
class TeamStatistics(BaseGameStats):
    """
    Overall team statistics including series and game-level data.

    This represents the full team performance over a time window,
    including both series wins/losses and aggregate game statistics.
    """

    # Identifiers
    team_id: str
    time_window: str
    aggregated_series_ids: List[str] = field(default_factory=list)

    # Series-level metrics
    total_series: int = 0
    series_won: int = 0
    series_win_rate: float = 0.0

    # Game-level metrics
    total_games: int = 0
    games_won: int = 0
    game_win_rate: float = 0.0
    win_streak_max: int = 0
    win_streak_current: int = 0

    # VALORANT-specific objectives
    spikes_planted_avg: float = 0.0
    spikes_defused_avg: float = 0.0
    bomb_explosions_avg: float = 0.0
    ultimate_orbs_avg: float = 0.0

    # Side split statistics
    attack_rounds: int = 0
    attack_wins: int = 0
    attack_win_rate: float = 0.0

    defense_rounds: int = 0
    defense_wins: int = 0
    defense_win_rate: float = 0.0

    @property
    def series_loss_count(self) -> int:
        """Calculate series losses."""
        return self.total_series - self.series_won

    @property
    def games_lost(self) -> int:
        """Calculate games lost."""
        return self.total_games - self.games_won

    @property
    def attack_side_stats(self) -> SideStats:
        """Get attack side as structured object."""
        return SideStats(
            rounds=self.attack_rounds,
            wins=self.attack_wins,
            win_rate=self.attack_win_rate
        )

    @property
    def defense_side_stats(self) -> SideStats:
        """Get defense side as structured object."""
        return SideStats(
            rounds=self.defense_rounds,
            wins=self.defense_wins,
            win_rate=self.defense_win_rate
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "team_id": self.team_id,
            "time_window": self.time_window,
            "aggregated_series_ids": self.aggregated_series_ids,
            "series": {
                "total": self.total_series,
                "won": self.series_won,
                "lost": self.series_loss_count,
                "win_rate": self.series_win_rate,
            },
            "games": {
                "total": self.total_games,
                "won": self.games_won,
                "lost": self.games_lost,
                "win_rate": self.game_win_rate,
                "win_streak_max": self.win_streak_max,
                "win_streak_current": self.win_streak_current,
            },
            "combat": {
                "kills": {
                    "total": self.kills_total,
                    "avg": self.kills_avg,
                    "min": self.kills_min,
                    "max": self.kills_max,
                },
                "deaths": {
                    "total": self.deaths_total,
                    "avg": self.deaths_avg,
                    "min": self.deaths_min,
                    "max": self.deaths_max,
                },
                "assists": {
                    "total": self.assists_total,
                    "avg": self.assists_avg,
                },
                "kd_ratio": self.kd_ratio,
                "first_bloods_percentage": self.first_bloods_percentage,
            },
            "objectives": {
                "spikes_planted_avg": self.spikes_planted_avg,
                "spikes_defused_avg": self.spikes_defused_avg,
                "bomb_explosions_avg": self.bomb_explosions_avg,
                "ultimate_orbs_avg": self.ultimate_orbs_avg,
            },
            "economy": {
                "avg_net_worth": self.avg_net_worth,
                "avg_spend": self.avg_spend,
            },
            "sides": {
                "attack": {
                    "rounds": self.attack_rounds,
                    "wins": self.attack_wins,
                    "win_rate": self.attack_win_rate,
                },
                "defense": {
                    "rounds": self.defense_rounds,
                    "wins": self.defense_wins,
                    "win_rate": self.defense_win_rate,
                },
            },
        }


@dataclass(kw_only=True)
class TeamGameStatistics(BaseGameStats):
    """
    Per-game/map team statistics.

    This represents game-level performance data, useful for:
    - Map-specific analysis
    - Agent composition trends
    - Objective success rates
    """

    # Identifiers
    team_id: str
    time_window: str
    map_filter: Optional[str] = None

    # Game count and wins
    game_count: int = 0
    games_won: int = 0
    game_win_rate: float = 0.0
    win_streak_max: int = 0
    win_streak_current: int = 0

    # Mistakes
    teamkills_total: int = 0
    selfkills_total: int = 0

    # Score
    score_total: int = 0
    score_avg: float = 0.0

    # Objectives - Plant
    plant_bomb_total: int = 0
    plant_bomb_avg: float = 0.0
    plant_bomb_first_percentage: float = 0.0

    # Objectives - Defuse
    defuse_bomb_total: int = 0
    defuse_bomb_avg: float = 0.0
    defuse_bomb_first_percentage: float = 0.0

    begin_defuse_total: int = 0
    begin_defuse_avg: float = 0.0

    stop_defuse_total: int = 0
    stop_defuse_avg: float = 0.0

    reach_defuse_checkpoint_total: int = 0
    reach_defuse_checkpoint_avg: float = 0.0

    # Objectives - Explode
    explode_bomb_total: int = 0
    explode_bomb_avg: float = 0.0
    explode_bomb_first_percentage: float = 0.0

    # Objectives - Ultimate orbs
    capture_ultimate_orb_total: int = 0
    capture_ultimate_orb_avg: float = 0.0

    # Agent picks
    top_agents: List[AgentPick] = field(default_factory=list)
    total_unique_agents: int = 0

    # Duration
    avg_game_duration_seconds: float = 0.0

    @property
    def games_lost(self) -> int:
        """Calculate games lost."""
        return self.game_count - self.games_won

    @property
    def most_picked_agent(self) -> Optional[str]:
        """Get the most picked agent name."""
        if self.top_agents:
            return self.top_agents[0].agent_name
        return None

    @property
    def avg_game_duration_minutes(self) -> float:
        """Get average game duration in minutes."""
        return self.avg_game_duration_seconds / 60.0

    @property
    def plant_success_rate(self) -> float:
        """Calculate spike plant success rate (plants that exploded)."""
        if self.plant_bomb_total == 0:
            return 0.0
        return (self.explode_bomb_total / self.plant_bomb_total) * 100.0

    @property
    def defuse_success_rate(self) -> float:
        """Calculate defuse success rate (defuses completed / defuses begun)."""
        if self.begin_defuse_total == 0:
            return 0.0
        return (self.defuse_bomb_total / self.begin_defuse_total) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "team_id": self.team_id,
            "time_window": self.time_window,
            "map_filter": self.map_filter,
            "games": {
                "count": self.game_count,
                "won": self.games_won,
                "lost": self.games_lost,
                "win_rate": self.game_win_rate,
                "win_streak_max": self.win_streak_max,
                "win_streak_current": self.win_streak_current,
                "avg_duration_minutes": self.avg_game_duration_minutes,
            },
            "combat": {
                "kills": {
                    "total": self.kills_total,
                    "avg": self.kills_avg,
                    "min": self.kills_min,
                    "max": self.kills_max,
                },
                "deaths": {
                    "total": self.deaths_total,
                    "avg": self.deaths_avg,
                    "min": self.deaths_min,
                    "max": self.deaths_max,
                },
                "assists": {
                    "total": self.assists_total,
                    "avg": self.assists_avg,
                },
                "kd_ratio": self.kd_ratio,
                "first_bloods_percentage": self.first_bloods_percentage,
            },
            "mistakes": {
                "teamkills": self.teamkills_total,
                "selfkills": self.selfkills_total,
            },
            "score": {
                "total": self.score_total,
                "avg": self.score_avg,
            },
            "economy": {
                "avg_money": self.avg_spend,
                "avg_inventory_value": self.avg_inventory_value,
                "avg_net_worth": self.avg_net_worth,
            },
            "objectives": {
                "plant": {
                    "total": self.plant_bomb_total,
                    "avg": self.plant_bomb_avg,
                    "first_percentage": self.plant_bomb_first_percentage,
                    "success_rate": self.plant_success_rate,
                },
                "defuse": {
                    "total": self.defuse_bomb_total,
                    "avg": self.defuse_bomb_avg,
                    "first_percentage": self.defuse_bomb_first_percentage,
                    "success_rate": self.defuse_success_rate,
                    "begun": self.begin_defuse_total,
                    "stopped": self.stop_defuse_total,
                    "checkpoint_reached": self.reach_defuse_checkpoint_total,
                },
                "explode": {
                    "total": self.explode_bomb_total,
                    "avg": self.explode_bomb_avg,
                    "first_percentage": self.explode_bomb_first_percentage,
                },
                "ultimate_orbs": {
                    "total": self.capture_ultimate_orb_total,
                    "avg": self.capture_ultimate_orb_avg,
                },
            },
            "agents": {
                "most_picked": self.most_picked_agent,
                "unique_count": self.total_unique_agents,
                "top_5": [
                    {
                        "name": agent.agent_name,
                        "count": agent.count,
                        "percentage": agent.percentage,
                    }
                    for agent in self.top_agents
                ],
            },
        }


# Factory functions to create models from ingestion data
def create_team_statistics_from_ingest(ingest_data: Dict[str, Any]) -> Optional[TeamStatistics]:
    """
    Create a TeamStatistics model from an ingestion result.

    Args:
        ingest_data: Result from ingest_team_statistics()

    Returns:
        TeamStatistics instance or None if no records
    """
    if not ingest_data.get("records"):
        return None

    record = ingest_data["records"][0]

    return TeamStatistics(
        # Identifiers
        team_id=record["team_id"],
        time_window=record["time_window"],
        aggregated_series_ids=record.get("aggregated_series_ids", []),

        # Series metrics
        total_series=record.get("total_series", 0),
        series_won=record.get("series_won", 0),
        series_win_rate=record.get("series_win_rate", 0.0),

        # Game metrics
        total_games=record.get("total_games", 0),
        games_won=record.get("games_won", 0),
        game_win_rate=record.get("game_win_rate", 0.0),
        win_streak_max=record.get("win_streak_max", 0),
        win_streak_current=record.get("win_streak_current", 0),

        # Combat
        kills_total=record.get("kills_total", 0),
        kills_avg=record.get("kills_avg", 0.0),
        kills_min=record.get("kills_min", 0),
        kills_max=record.get("kills_max", 0),
        deaths_total=record.get("deaths_total", 0),
        deaths_avg=record.get("deaths_avg", 0.0),
        deaths_min=record.get("deaths_min", 0),
        deaths_max=record.get("deaths_max", 0),
        assists_total=record.get("assists_total", 0),
        assists_avg=record.get("assists_avg", 0.0),
        kd_ratio=record.get("kd_ratio", 0.0),
        first_bloods_percentage=record.get("first_bloods_percentage", 0.0),

        # Objectives
        spikes_planted_avg=record.get("spikes_planted_avg", 0.0),
        spikes_defused_avg=record.get("spikes_defused_avg", 0.0),
        bomb_explosions_avg=record.get("bomb_explosions_avg", 0.0),
        ultimate_orbs_avg=record.get("ultimate_orbs_avg", 0.0),

        # Economy
        avg_net_worth=record.get("avg_net_worth", 0.0),
        avg_spend=record.get("avg_spend", 0.0),

        # Sides
        attack_rounds=record.get("attack_rounds", 0),
        attack_wins=record.get("attack_wins", 0),
        attack_win_rate=record.get("attack_win_rate", 0.0),
        defense_rounds=record.get("defense_rounds", 0),
        defense_wins=record.get("defense_wins", 0),
        defense_win_rate=record.get("defense_win_rate", 0.0),
    )


def create_team_game_statistics_from_ingest(ingest_data: Dict[str, Any]) -> Optional[TeamGameStatistics]:
    """
    Create a TeamGameStatistics model from an ingestion result.

    Args:
        ingest_data: Result from ingest_team_game_statistics()

    Returns:
        TeamGameStatistics instance or None if no records
    """
    if not ingest_data.get("records"):
        return None

    record = ingest_data["records"][0]

    # Convert agent picks dicts to AgentPick objects
    top_agents = [
        AgentPick(
            agent_id=agent["agent_id"],
            agent_name=agent["agent_name"],
            count=agent["count"],
            percentage=agent["percentage"]
        )
        for agent in record.get("top_agents", [])
    ]

    return TeamGameStatistics(
        # Identifiers
        team_id=record["team_id"],
        time_window=record["time_window"],
        map_filter=record.get("map_filter"),

        # Game metrics
        game_count=record.get("game_count", 0),
        games_won=record.get("games_won", 0),
        game_win_rate=record.get("game_win_rate", 0.0),
        win_streak_max=record.get("win_streak_max", 0),
        win_streak_current=record.get("win_streak_current", 0),

        # Combat
        kills_total=record.get("kills_total", 0),
        kills_avg=record.get("kills_avg", 0.0),
        kills_min=record.get("kills_min", 0),
        kills_max=record.get("kills_max", 0),
        deaths_total=record.get("deaths_total", 0),
        deaths_avg=record.get("deaths_avg", 0.0),
        deaths_min=record.get("deaths_min", 0),
        deaths_max=record.get("deaths_max", 0),
        assists_total=record.get("assists_total", 0),
        assists_avg=record.get("assists_avg", 0.0),
        kd_ratio=record.get("kd_ratio", 0.0),
        first_bloods_percentage=record.get("first_bloods_percentage", 0.0),

        # Mistakes
        teamkills_total=record.get("teamkills_total", 0),
        selfkills_total=record.get("selfkills_total", 0),

        # Score
        score_total=record.get("score_total", 0),
        score_avg=record.get("score_avg", 0.0),

        # Economy
        avg_spend=record.get("avg_money", 0.0),
        avg_inventory_value=record.get("avg_inventory_value", 0.0),
        avg_net_worth=record.get("avg_net_worth", 0.0),

        # Objectives
        plant_bomb_total=record.get("plant_bomb_total", 0),
        plant_bomb_avg=record.get("plant_bomb_avg", 0.0),
        plant_bomb_first_percentage=record.get("plant_bomb_first_percentage", 0.0),
        defuse_bomb_total=record.get("defuse_bomb_total", 0),
        defuse_bomb_avg=record.get("defuse_bomb_avg", 0.0),
        defuse_bomb_first_percentage=record.get("defuse_bomb_first_percentage", 0.0),
        begin_defuse_total=record.get("begin_defuse_total", 0),
        begin_defuse_avg=record.get("begin_defuse_avg", 0.0),
        stop_defuse_total=record.get("stop_defuse_total", 0),
        stop_defuse_avg=record.get("stop_defuse_avg", 0.0),
        reach_defuse_checkpoint_total=record.get("reach_defuse_checkpoint_total", 0),
        reach_defuse_checkpoint_avg=record.get("reach_defuse_checkpoint_avg", 0.0),
        explode_bomb_total=record.get("explode_bomb_total", 0),
        explode_bomb_avg=record.get("explode_bomb_avg", 0.0),
        explode_bomb_first_percentage=record.get("explode_bomb_first_percentage", 0.0),
        capture_ultimate_orb_total=record.get("capture_ultimate_orb_total", 0),
        capture_ultimate_orb_avg=record.get("capture_ultimate_orb_avg", 0.0),

        # Agents
        top_agents=top_agents,
        total_unique_agents=record.get("total_unique_agents", 0),

        # Duration
        avg_game_duration_seconds=record.get("avg_game_duration_seconds", 0.0),
    )

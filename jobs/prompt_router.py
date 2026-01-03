from config.settings import GEMINI_MODEL, GEMINI_API_KEY

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider(api_key=GEMINI_API_KEY)
model = GoogleModel(GEMINI_MODEL, provider=provider)
agent = Agent(model)

popular_esports_teams = [
    "NRG", "Fnatic", "DRX", "G2 Esports", "Paper Rex", "MIBR", "Team Heretics", "Rex Regum Qeon",
    "Xi Lai Gaming", "Team Liquid", "Bilibili Gaming", "T1", "GIANTX", "Dragon Ranger Gaming",
    "Sentinels", "Edward Gaming", "Talon Esports", "NONGSHIM REDFORCE", "Gen.G", "BBL Esports",
    "Cloud9", "Wolves Esports", "Leviatán Esports", "100 Thieves", "NAVI", "Trace Esports", "KRÜ Esports",
    "2GAME Esports", "Evil Geniuses", "Team Vitality", "NOVA Esports", "FunPlus Phoenix", "TYLOO GAMING",
    "Karmine Corp", "FUT Esports", "BOOM Esports", "TITAN Esports Club", "ALL GAMERS", "ZETA DIVISION"
]
valorant_maps = [
    "Abyss", "Ascent", "Bind", "Breeze", "Corrode", "Fracture", "Haven", "Icebox",
    "Lotus", "Pearl", "Split", "Sunset", "District", "Drift", "Glitch", "Kasbah", "Piazza"
]

class ScoutingReportTool(BaseModel):
    """Generates a full scouting report for a team."""
    team_name: str = Field(..., description=f"The name of the esports team (e.g., 'NRG', 'Team Liquid', 'Sentinels' e.t.c)")
    match_count: int = Field(10, description="Number of recent matches to analyze")
    time_window: str = Field("LAST_3_MONTHS", description="Time period: 'LAST_MONTH', 'LAST_3_MONTHS', or 'LAST_YEAR'")

class PlayerAnalysisTool(BaseModel):
    """Analyzes a player's performance"""
    player_name: str = Field(..., description="The name of the player")

class TournamentPerformanceAnalysisTool(BaseModel):
    """Analyzes a team's performance in a specific tournament."""
    tournament_name: str = Field(..., description="The name of the tournament")
    team_name: str = Field(..., description="The name of the esports team")

class MapAnalysisTool(BaseModel):
    """Analyzes a team's performance on a specific map."""
    team_name: str = Field(..., description="The name of the esports team")
    map_name: str = Field(..., description="The specific map name (e.g., 'Ascent', 'Bind', 'Haven')")

class TeamHeadToHeadAnalysisTool(BaseModel):
    """Analyzes a team's performance against another team."""
    team_name_1: str = Field(..., description="The name of the first esports team")
    team_name_2: str = Field(..., description="The name of the second esports team")
    match_count: int = Field(10, description="Number of recent matches to analyze")
    time_window: str = Field("LAST_3_MONTHS", description="Time period: 'LAST_MONTH', 'LAST_3_MONTHS', 'LAST_6_MONTHS', or 'LAST_YEAR'")

class PlayerHeadToHeadAnalysisTool(BaseModel):
    """Analyzes a player's performance against another player."""
    player_name_1: str = Field(..., description="The name of the first player")
    player_name_2: str = Field(..., description="The name of the second player")
    match_count: int = Field(10, description="Number of recent matches to analyze")
    time_window: str = Field("LAST_3_MONTHS", description="Time period: 'LAST_MONTH', 'LAST_3_MONTHS', 'LAST_6_MONTHS', or 'LAST_YEAR'")

class TimePeriodAnalysisTool(BaseModel):
    """Analyzes performance for a specific team or player over a given time period."""
    period: str = Field(..., description="The time period: 'LAST_MONTH', 'LAST_3_MONTHS', 'LAST_6_MONTHS', or 'LAST_YEAR'")
    team_name: Optional[str] = Field(None, description="The name of the esports team (optional if player name provided)")
    player_name: Optional[str] = Field(None, description="The name of the player (optional if team name provided)")

class WeaknessDetectionAnalysisTool(BaseModel):
    """Detects and exploits weaknesses in a team's performance."""
    team_name: str = Field(..., description="The name of the esports team")
    match_count: int = Field(10, description="Number of recent matches to analyze")
    time_window: str = Field("LAST_3_MONTHS", description="Time period: 'LAST_MONTH', 'LAST_3_MONTHS', 'LAST_6_MONTHS', or 'LAST_YEAR'")

class CompositionAnalysisTool(BaseModel):
    """Identifies a team's most successful agent or champion lineups and suggests counters."""
    team_name: str = Field(..., description="The name of the esports team")

class InGameStrategyCallTool(BaseModel):
    """Provides a specific, data-backed strategy call based on the current in-game state."""
    team_name: str = Field(..., description="The team currently playing that needs advice")
    game_state_event: str = Field(..., description="The critical event occurring: 'baron_available', 'spike_planted', 'major_team_fight_lost', 'eco_round'")
    context_time_minutes: int = Field(..., description="The current timestamp in the game (e.g., 22 minutes)")

class ExploitSpecificOpponentTellTool(BaseModel):
    """Identifies and suggests how to exploit a specific, recurring 'tell' or predictable habit of an opposing player or team."""
    opponent_name: str = Field(..., description="The name of the opponent team or player exhibiting the 'tell'")
    tell_description: str = Field(..., description="A description of the habit or pattern the user suspects (e.g., 'Player X always pushes B on eco round', 'They always start topside')")


class GeneralPromptRouter:
    """

    """
    _popular_esports_teams: List[str] = popular_esports_teams
    _valorant_maps: List[str] = valorant_maps

    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        A function to convert natural language prompts into structured query data.
        :param prompt:
        :return:
            Dict[str, Any]:
        """


from config.globalutilitylogger import get_logger
from config.settings import GEMINI_MODEL, GEMINI_API_KEY
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from jobs.handler_functions import (
    handle_generate_full_scouting_report, handle_generate_map_analysis, handle_generate_player_performance_analysis,
    handle_generate_team_head_to_head_analysis, handle_generate_tournament_performance_analysis,
    handle_detect_and_exploit_weaknesses, handle_player_head_to_head_analysis, handle_composition_analysis,
    handle_generate_in_game_strategy_call, handle_exploit_specific_opponent_tell, handle_time_period_analysis,
    handle_generate_agent_performance_analysis
)

_logger = get_logger(__name__)

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
    match_count: Optional[int] = Field(10, description="Number of recent matches to analyze")
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
    time_window: str = Field("LAST_6_MONTHS", description="Time period: 'LAST_MONTH', 'LAST_3_MONTHS', 'LAST_6_MONTHS', or 'LAST_YEAR'")

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
    def __init__(self):
        self.popular_esports_teams: List[str] = popular_esports_teams
        self.valorant_maps: List[str] = valorant_maps
        self.provider = GoogleProvider(api_key=GEMINI_API_KEY)
        self.model = GoogleModel(GEMINI_MODEL, provider=self.provider)
        self.agent = Agent(self.model, system_prompt="""
            You are an expert esports analyst specializing in VALORANT. Your task is to interpret user prompts and 
            determine the most appropriate analysis tool to use based on the content of the prompt. You have access to 
            a variety of tools, each designed for specific types of analysis. When processing a prompt, carefully analyze 
            the request to identify key elements such as team names, player names, match counts, time windows, map names, 
            tournaments, and specific analysis needs.
            Use the following guidelines to select the appropriate tool:
            1. If the prompt requests a comprehensive report on a team's recent performance, use the ScoutingReportTool.
            2. For prompts focused on individual player performance, select the Player
            3. For tournament-specific performance analysis, use the TournamentPerformanceAnalysisTool.
            4. For map-specific performance analysis, use the MapAnalysisTool.
            5. For head-to-head team comparisons, use the TeamHeadToHeadAnalysisTool.
            6. For head-to-head player comparisons, use the PlayerHeadToHeadAnalysisTool.
            7. For time period-specific performance analysis, use the TimePeriodAnalysisTool.
            8. For identifying weaknesses in a team's performance, use the WeaknessDetectionAnalysisTool.
            9. For analyzing team compositions and suggesting counters, use the CompositionAnalysisTool.
            10. For in-game strategy advice based on current game events, use the InGameStrategyCallTool.
            11. For exploiting specific opponent habits or 'tells', use the ExploitSpecificOpponentTellTool.
            Always ensure that the selected tool aligns closely with the user's request and that all necessary parameters are extracted accurately.
        """)
        self._register_tools()

    def _register_tools(self):
        """
        Register all analysis handler functions as AI tools with the agent.
        :return:
        """

        @self.agent.tool
        def register_weakness_detection_tools(ctx: RunContext, tool_input: WeaknessDetectionAnalysisTool) -> Dict[str, Any]:
            return handle_detect_and_exploit_weaknesses(
                team_name=tool_input.team_name,
                match_count=tool_input.match_count,
                time_window=tool_input.time_window
            )

        @self.agent.tool
        def register_scouting_report_tool(ctx: RunContext, tool_input: ScoutingReportTool) -> Dict[str, Any]:
            return handle_generate_full_scouting_report(
                team_name=tool_input.team_name,
                match_count=tool_input.match_count,
                time_window=tool_input.time_window
            )

        @self.agent.tool
        def register_map_analysis_tool(ctx: RunContext, tool_input: MapAnalysisTool) -> Dict[str, Any]:
            return handle_generate_map_analysis(
                team_name=tool_input.team_name,
                map_name=tool_input.map_name,
                time_window=tool_input.time_window
            )

        @self.agent.tool
        def register_player_analysis_tool(ctx: RunContext, tool_input: PlayerAnalysisTool) -> Dict[str, Any]:
            return handle_generate_player_performance_analysis(
                player_name=tool_input.player_name,
                match_count=10,
                time_window=tool_input.time_window
            )

        @self.agent.tool
        def register_team_head_to_head_tool(ctx: RunContext, tool_input: TeamHeadToHeadAnalysisTool) -> Dict[str, Any]:
            return handle_generate_team_head_to_head_analysis(
                team_name_1=tool_input.team_name_1,
                team_name_2=tool_input.team_name_2,
                match_count=tool_input.match_count,
                time_window=tool_input.time_window
            )

        @self.agent.tool
        def register_tournament_performance_tool(ctx: RunContext, tool_input: TournamentPerformanceAnalysisTool) -> Dict[str, Any]:
            return handle_generate_tournament_performance_analysis(
                tournament_name=tool_input.tournament_name,
                team_name=tool_input.team_name
            )

        @self.agent.tool
        def register_player_head_to_head_tool(ctx: RunContext, tool_input: PlayerHeadToHeadAnalysisTool) -> Dict[str, Any]:
            return handle_player_head_to_head_analysis(
                player_name_1=tool_input.player_name_1,
                player_name_2=tool_input.player_name_2,
                match_count=tool_input.match_count,
                time_window=tool_input.time_window
            )

        @self.agent.tool
        def register_time_period_analysis_tool(ctx: RunContext, tool_input: TimePeriodAnalysisTool) -> Dict[str, Any]:
            return handle_time_period_analysis(
                period=tool_input.period,
                team_name=tool_input.team_name,
                player_name=tool_input.player_name
            )

        @self.agent.tool
        def register_composition_analysis_tool(ctx: RunContext, tool_input: CompositionAnalysisTool) -> Dict[str, Any]:
            return handle_composition_analysis(
                team_name=tool_input.team_name
            )

        @self.agent.tool
        def register_agent_performance_analysis_tool(ctx: RunContext, tool_input: CompositionAnalysisTool) -> Dict[str, Any]:
            return handle_generate_agent_performance_analysis(
                team_name=tool_input.team_name
            )

        @self.agent.tool
        def register_in_game_strategy_call_tool(ctx: RunContext, tool_input: InGameStrategyCallTool) -> Dict[str, Any]:
            return handle_generate_in_game_strategy_call(
                team_name=tool_input.team_name,
                game_state_event=tool_input.game_state_event,
                context_time_minutes=tool_input.context_time_minutes
            )

        @self.agent.tool
        def register_exploit_specific_opponent_tell_tool(ctx: RunContext, tool_input: ExploitSpecificOpponentTellTool) -> Dict[str, Any]:
            return handle_exploit_specific_opponent_tell(
                opponent_name=tool_input.opponent_name,
                tell_description=tool_input.tell_description
            )

        @self.agent.tool
        def handle_invalid_tool(ctx: RunContext, tool_input: BaseModel) -> Dict[str, Any]:
            return {"error": f"Invalid tool input: {tool_input}"}

    async def resolve_user_prompt(self, user_prompt: str):
        result = await self.agent.run(user_prompt)
        _logger.info(f"result.response: {result.response}")
        _logger.info(f"result.output: {result.output}")
        return {"response": result.response, "output": result.output}

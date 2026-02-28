"""
Converts raw analysis numbers into actionable "How to Win" insights.

This is the "Brain" - takes all transform outputs and synthesizes them
into English recommendations that coaches can actually use.
"""

from typing import Dict, Any, List, Optional
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from config.globalutilitylogger import get_logger
from config.settings import GEMINI_MODEL, GEMINI_API_KEY
from models.report import InsightObject, FlashCard, CoachRead, AnalystAppendix
from transforms.counter_strat import generate_counter_strat

_logger = get_logger(__name__)

class InsightSynthesizerAgent:
    """
    LLM-powered agent that translates raw tactical truths into the 90-5-60 framework.
    """
    def __init__(self):
        self.provider = GoogleProvider(api_key=GEMINI_API_KEY)
        self.model = GoogleModel(GEMINI_MODEL, provider=self.provider)
        self.agent = Agent(
            self.model,
            result_type=CoachRead,
            system_prompt=(
                "You are an expert VALORANT tactical analyst and copywriter. "
                "Your task is to take raw statistical analysis and 'tells' and "
                "synthesize them into a structured tactical playbook (90-second read). "
                "Follow these rules strictly:\n"
                "1. Use crisp, coach-friendly, imperative language (e.g., 'Punish', 'Execute', 'Ban').\n"
                "2. Each insight must follow the Claim -> Action -> Evidence structure.\n"
                "3. No section or justification should exceed 3 lines.\n"
                "4. Be specific—mention map names, players, and exact numbers from the data.\n"
                "5. Focus on what we should DO, not just what they did."
            )
        )

    async def synthesize_coach_read(self, raw_data: Dict[str, Any]) -> CoachRead:
        """
        Translates raw dicts into Layer B (Coach Read).
        """
        _logger.info("Synthesizing Coach Read (Layer B) via LLM")
        
        prompt = f"Analyze the following raw tactical data and generate 3-5 high-impact insights. Output ONLY valid JSON matching the CoachRead schema:\n{raw_data}"
        result = await self.agent.run(prompt)
        
        if isinstance(result.data, CoachRead):
            return result.data
            
        # Fallback for manual parsing
        content = result.data if result.data else result.output
        if isinstance(content, dict):
            return CoachRead.model_validate(content)
            
        import re
        try:
            if isinstance(content, str):
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    return CoachRead.model_validate_json(match.group())
                return CoachRead.model_validate_json(content)
            return CoachRead.model_validate(content)
        except Exception as e:
            _logger.error(f"Failed to parse CoachRead: {e}. Content snippet: {str(content)[:500]}...")
            return CoachRead(insights=[])

class FlashCardAgent:
    """
    Specialized agent for the 15-second Flash Card (Layer A).
    """
    def __init__(self):
        self.provider = GoogleProvider(api_key=GEMINI_API_KEY)
        self.model = GoogleModel(GEMINI_MODEL, provider=self.provider)
        self.agent = Agent(
            self.model,
            result_type=FlashCard,
            system_prompt=(
                "You are a Head Coach's tactical assistant. Create a 15-second 'Flash Card' "
                "for the upcoming match. This is for instant decision-making 'above the fold'.\n"
                "Rules:\n"
                "1. Game Plan: Exactly 3 actionable bullets.\n"
                "2. Veto: 1 clear recommendation with a 1-line justification.\n"
                "3. Patterns: 1-2 high-confidence behaviors to exploit or avoid.\n"
                "4. Risk: 1-2 critical flags that could ruin the plan."
            )
        )

    async def synthesize_flash_card(self, coach_read: CoachRead) -> FlashCard:
        """
        Distills Layer B into Layer A (Flash Card).
        """
        _logger.info("Synthesizing Flash Card (Layer A) via LLM")
        
        # Specific instruction to avoid wrapping in 'flash_card' key
        prompt = (
            f"Distill these tactical insights into a 15-second Flash Card. "
            f"You MUST return a JSON object with keys: game_plan (list of 3 strings), veto_recommendation (string), punish_patterns (list), risk_flags (list). "
            f"Do NOT wrap it in a 'flash_card' key.\n\n"
            f"INSIGHTS:\n{coach_read.model_dump_json()}"
        )
        result = await self.agent.run(prompt)
        
        if isinstance(result.data, FlashCard):
            return result.data
            
        # Fallback for manual parsing
        content = result.data if result.data else result.output
        if isinstance(content, dict):
            # Try to unwrap if LLM wrapped it anyway
            if "flash_card" in content and len(content) == 1:
                content = content["flash_card"]
            return FlashCard.model_validate(content)
            
        import re
        import json
        try:
            if isinstance(content, str):
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    json_str = match.group()
                    data = json.loads(json_str)
                    if "flash_card" in data and len(data) == 1:
                        data = data["flash_card"]
                    return FlashCard.model_validate(data)
                return FlashCard.model_validate_json(content)
            return FlashCard.model_validate(content)
        except Exception as e:
            _logger.error(f"Failed to parse FlashCard: {e}. Content snippet: {str(content)[:500]}...")
            return FlashCard(game_plan=[], veto_recommendation="N/A", punish_patterns=[], risk_flags=[])

async def generate_90_5_60_report(raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the synthesis of a full 90-5-60 structured report.
    """
    synthesizer = InsightSynthesizerAgent()
    flash_card_agent = FlashCardAgent()

    # 1. Layer B: Coach Read (90s)
    coach_read = await synthesizer.synthesize_coach_read(raw_analysis)
    
    # Apply hard caps and filtering
    coach_read.insights = rank_and_filter_insights(coach_read.insights)
    
    # 2. Layer A: Flash Card (15s)
    flash_card = await flash_card_agent.synthesize_flash_card(coach_read)
    
    # 3. Layer C: Analyst Appendix (5-60m)
    appendix = AnalystAppendix(raw_data=raw_analysis)

    return {
        "flash_card": flash_card.model_dump(),
        "coach_read": coach_read.model_dump(),
        "analyst_appendix": appendix.model_dump(),
        "actionable_insights": [i.recommendation for i in coach_read.insights]
    }

def rank_and_filter_insights(insights: List[InsightObject]) -> List[InsightObject]:
    """
    Ranks and filters insights based on the 90-5-60 rules.
    - Max 5 primary actions
    - Sort by priority score
    """
    # Sort by priority descending
    # Recalculate priority to ensure formula is applied
    for i in insights:
        if i.priority == 0.0:
            i.priority = calculate_priority(i)
            
    sorted_insights = sorted(insights, key=lambda x: x.priority, reverse=True)
    
    # Throttling
    filtered = sorted_insights[:5]
    
    _logger.info(f"Filtered {len(insights)} insights down to {len(filtered)}")
    return filtered

def calculate_priority(insight: InsightObject) -> float:
    """
    Calculates the final priority score using the 90-5-60 formula.
    priority_score = impact × confidence × freshness × sample_quality
    """
    return (
        insight.impact_score * 
        insight.confidence_score * 
        insight.freshness * 
        insight.sample_quality
    )

def generate_map_veto_insights(map_analysis: Dict[str, Any]) -> List[str]:
    """
    Generate map ban/pick recommendations.

    Args:
        map_analysis: Output from map_analysis.get_map_analysis_summary()

    Returns:
        List of actionable insights like:
        - "✓ BAN Icebox (30% WR over 10 games)"
        - "✓ PICK Ascent (83% WR - their strongest map)"
    """
    insights = []

    veto = map_analysis.get('veto_strategy', {})

    # Permaban recommendation
    permaban = veto.get('permaban')
    if permaban:
        insights.append(
            f"✓ BAN {permaban['map_name']} "
            f"({permaban['win_rate']*100:.1f}% WR over {permaban['games']} games)"
        )

    # Stronghold recommendation
    stronghold = veto.get('stronghold')
    if stronghold:
        insights.append(
            f"✓ PICK {stronghold['map_name']} if possible "
            f"({stronghold['win_rate']*100:.1f}% WR - their strongest)"
        )

    # Map pool depth warning
    pool_depth = map_analysis.get('map_pool_depth', {})
    if pool_depth.get('one_trick_risk'):
        insights.append(
            f"⚠ LIMITED MAP POOL: Only {pool_depth['competitive_maps']} competitive maps "
            f"- force them onto uncomfortable maps"
        )

    return insights


def generate_player_targeting_insights(player_analysis: Dict[str, Any]) -> List[str]:
    """
    Generate player-specific counter-strategies.

    Args:
        player_analysis: Output from player_analysis.get_player_analysis_summary()

    Returns:
        List of insights like:
        - "🎯 TARGET Player X (0.78 K/D - weakest link)"
        - "⚡ WATCH Player Y (1.45 K/D, 32% first blood rate)"
    """
    insights = []

    # Star player warning
    star = player_analysis.get('star_player')
    if star and star.get('kd_ratio') is not None:
        first_kill_pct = star.get('first_kill_pct', 0)
        insights.append(
            f"⚡ WATCH {star.get('player_id', 'Star Player')} "
            f"({star['kd_ratio']} K/D, {first_kill_pct*100:.1f}% first blood rate) "
            f"- high impact player"
        )

    # Weak link target
    weak_link = player_analysis.get('weak_link')
    if weak_link and weak_link.get('kd_ratio') is not None:
        insights.append(
            f"🎯 TARGET {weak_link.get('player_id', 'Weak Link')} "
            f"({weak_link['kd_ratio']} K/D) "
            f"- exploit their inconsistency"
        )

    return insights


def generate_composition_insights(composition_analysis: Dict[str, Any]) -> List[str]:
    """
    Generate comp/agent-related insights.

    Args:
        composition_analysis: Output from composition_analysis.get_composition_analysis_summary()

    Returns:
        List of insights about expected comps and counters
    """
    insights = []

    # Default comp expectation
    default_comps = composition_analysis.get('default_comps', [])
    if default_comps:
        top_comp = default_comps[0]
        comp_str = ", ".join(top_comp['composition'][:5])  # Show the first 5 agents
        insights.append(
            f"🔮 EXPECT composition: {comp_str} "
            f"(used in {top_comp['games']} games)"
        )

    # Top agent picks
    agent_picks = composition_analysis.get('agent_pick_rates', [])
    if agent_picks:
        top_3_agents = agent_picks[:3]
        agent_str = ", ".join([f"{a['agent']} ({a['pick_rate']*100:.0f}%)" for a in top_3_agents])
        insights.append(
            f"📊 POPULAR AGENTS: {agent_str}"
        )

    return insights


def generate_weakness_exploitation_insights(weakness_analysis: Dict[str, Any]) -> List[str]:
    """
    Generate exploitable weakness insights.

    Args:
        weakness_analysis: Output from weakness_detection.get_weakness_detection_summary()

    Returns:
        List of actionable exploitation strategies
    """
    insights = []

    # Early aggression exploitation
    early_agg = weakness_analysis.get('early_aggression', {})
    if early_agg.get('exploitable'):
        insights.append(f"💥 {early_agg['counter_strategy']}")

    # Economy exploitation
    economy = weakness_analysis.get('economy_patterns', {})
    if economy.get('exploitable'):
        insights.append(f"💰 {economy['counter_strategy']}")

    # Objective weaknesses
    objective_weak = weakness_analysis.get('objective_weaknesses', {})
    for strategy in objective_weak.get('counter_strategies', []):
        insights.append(f"🎯 {strategy}")

    # Side weaknesses
    side_weak = weakness_analysis.get('side_weaknesses', {})
    if side_weak.get('weak_side') != 'balanced':
        insights.append(f"⚔️ {side_weak['counter_strategy']}")

    # Consistency issues
    consistency = weakness_analysis.get('consistency_issues', {})
    if consistency.get('exploitable'):
        insights.append(f"📈 {consistency['counter_strategy']}")

    return insights


def generate_team_overview_insights(team_analysis: Dict[str, Any]) -> List[str]:
    """
    Generate high-level team performance insights.
    """
    insights = []

    # Pistol performance
    pistols = team_analysis.get('pistol_rounds', {})
    if pistols.get('overall', 0) > 0.65:
        qual = "ELITE" if pistols.get('data_quality') == 'high' else "Strong"
        insights.append(f"🔫 {qual} PISTOL ROUNDS: {pistols['overall']*100:.1f}% win rate. Expect them to jump ahead early in halves.")
    elif pistols.get('overall', 0) < 0.40:
        insights.append(f"🔫 WEAK PISTOLS: {pistols['overall']*100:.1f}% win rate. Opportunity to build economic momentum early.")

    # Win Reasons
    win_reasons = team_analysis.get('win_reasons', {})
    if win_reasons.get('primary_method') == 'Elimination':
        dist = win_reasons.get('distribution', {}).get('Elimination', 0)
        if dist > 0.8:
            insights.append(f"⚔️ PURE AIMERS: {dist*100:.0f}% of round wins come from eliminations. Avoid raw aim duels; use utility.")
    elif win_reasons.get('primary_method') == 'BombExploded':
        insights.append(f"💣 POST-PLANT KINGS: High bomb explosion rate. Focus on preventing the plant or fast retakes.")

    win_rates = team_analysis.get('win_rates', {})
    games = win_rates.get('games', {})

    # Overall performance
    if games.get('win_rate', 0) > 0.60:
        insights.append(
            f"⚠️ STRONG OPPONENT: {games['win_rate']*100:.1f}% game win rate "
            f"({games['won']}-{games['count']-games['won']} record)"
        )
    elif games.get('win_rate', 0) < 0.40:
        insights.append(
            f"✓ FAVORABLE MATCHUP: {games['win_rate']*100:.1f}% game win rate "
            f"({games['won']}-{games['count']-games['won']} record)"
        )

    # Current form
    current_streak = win_rates.get('current_streak', {})
    if current_streak.get('count', 0) > 3:
        streak_type = current_streak['type']
        insights.append(
            f"📊 MOMENTUM: On a {current_streak['count']}-game {streak_type} streak"
        )

    # Combat performance
    combat = team_analysis.get('combat_metrics', {})
    if combat.get('kd_ratio', 0) > 1.2:
        insights.append(
            f"🔫 HIGH FIREPOWER: {combat['kd_ratio']:.2f} team K/D ratio"
        )

    return insights


def prioritize_insights(insights: List[str]) -> List[str]:
    """
    Prioritize insights by impact.

    Priority order:
    1. Map veto (✓ BAN/PICK)
    2. Player targeting (🎯 TARGET, ⚡ WATCH)
    3. Weakness exploitation (💥💰🎯⚔️)
    4. Team overview (⚠️📊)
    5. Composition (🔮📊)

    Args:
        insights: Unordered list of insights

    Returns:
        Ordered list (most important first)
    """
    priority_symbols = ['✓', '🎯', '⚡', '💥', '💰', '⚔️', '⚠️', '📊', '🔮']

    def get_priority(insight: str) -> int:
        """Lower number = higher priority"""
        for i, symbol in enumerate(priority_symbols):
            if insight.startswith(symbol):
                return i
        return len(priority_symbols)  # Unknown symbols go last

    return sorted(insights, key=get_priority)


def format_actionable_bullets(insights: List[str], max_insights: int = 10) -> List[str]:
    """
    Format and limit insights to the most important ones.

    Args:
        insights: List of all generated insights
        max_insights: Maximum number to return (default 10)

    Returns:
        Top N most important insights, formatted
    """
    if not insights:
        return ["⚠️ Insufficient data to generate insights"]

    # Remove duplicates while preserving order
    seen = set()
    unique_insights = []
    for insight in insights:
        if insight not in seen:
            seen.add(insight)
            unique_insights.append(insight)

    # Prioritize
    prioritized = prioritize_insights(unique_insights)

    # Limit to max
    return prioritized[:max_insights]


def generate_how_to_win(
    team_analysis: Dict[str, Any],
    map_analysis: Dict[str, Any],
    player_analysis: Dict[str, Any],
    composition_analysis: Dict[str, Any],
    weakness_analysis: Dict[str, Any]
) -> List[str]:
    """
    Master function: Generate complete "How to Win" insights.

    This combines ALL analysis outputs into a prioritized list of
    actionable recommendations.

    Args:
        team_analysis: Output from team_analysis.get_team_analysis_summary()
        map_analysis: Output from map_analysis.get_map_analysis_summary()
        player_analysis: Output from player_analysis.get_player_analysis_summary()
        composition_analysis: Output from composition_analysis.get_composition_analysis_summary()
        weakness_analysis: Output from weakness_detection.get_weakness_detection_summary()

    Returns:
        List of prioritized, actionable insights (max 10)
    """
    _logger.info("Generating 'How to Win' insights")

    all_insights = []

    # Generate insights from each category
    all_insights.extend(generate_map_veto_insights(map_analysis))
    all_insights.extend(generate_player_targeting_insights(player_analysis))
    all_insights.extend(generate_weakness_exploitation_insights(weakness_analysis))
    all_insights.extend(generate_composition_insights(composition_analysis))
    all_insights.extend(generate_team_overview_insights(team_analysis))

    # Format and prioritize
    formatted = format_actionable_bullets(all_insights, max_insights=10)

    _logger.info(f"Generated {len(formatted)} actionable insights")

    return formatted

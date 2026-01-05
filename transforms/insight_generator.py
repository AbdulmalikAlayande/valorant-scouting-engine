"""
Converts raw analysis numbers into actionable "How to Win" insights.

This is the "Brain" - takes all transform outputs and synthesizes them
into English recommendations that coaches can actually use.
"""

from typing import Dict, Any, List
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


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
    if star:
        insights.append(
            f"⚡ WATCH {star.get('player_id', 'Star Player')} "
            f"({star['kd_ratio']} K/D, {star['first_kill_pct']*100:.1f}% first blood rate) "
            f"- high impact player"
        )

    # Weak link target
    weak_link = player_analysis.get('weak_link')
    if weak_link:
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

    Args:
        team_analysis: Output from team_analysis.get_team_analysis_summary()

    Returns:
        List of overview insights
    """
    insights = []

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

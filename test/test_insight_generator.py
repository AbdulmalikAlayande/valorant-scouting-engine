
from transforms.insight_generator import generate_how_to_win, format_actionable_bullets

def test_insight_generator():
    print("Testing Insight Generator...")

    # Mock team analysis (from team_analysis.py output)
    team_analysis = {
        "stronghold": "Ascent",
        "permaban": "Icebox",
        "momentum": "hot",
        "insights": [
            "✓ Stronghold: Ascent (80.0% win rate over 10 games).",
            "⚠ Permaban Candidate: Icebox (33.3% win rate). Recommend picking against them here."
        ]
    }

    # Mock player threats (from player_analysis.py output)
    player_threats = [
        "🔥 High Frag Threat: Player 2512 (K/D: 1.33)",
        "⚡ Aggressive Opener: Player 2512 (First Blood: 25.0%)",
        "📍 Spike Specialist: Player 2512 (Avg Plants: 2.0)"
    ]

    # 1. Test Insight Synthesis
    raw_insights = generate_how_to_win(team_analysis, player_threats)
    print("\nRaw Insights:")
    for i in raw_insights:
        print(f" - {i}")

    # 2. Test Formatting and Prioritization
    final_report = format_actionable_bullets(raw_insights)
    print("\nFinal Actionable Report (Top 5):")
    for i, insight in enumerate(final_report, 1):
        print(f"{i}. {insight}")


if __name__ == "__main__":
    test_insight_generator()

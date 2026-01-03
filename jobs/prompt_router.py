from typing import Dict, Any
from google.genai import client

class GeneralPromptRouter:
    """
    A general rule-based prompt router that directs prompts to appropriate handlers based on their content.
    """

    _popular_esports_teams = [
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

    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        A function to converty natural language prompts into structured query data.
        :param prompt:
        :return:
            Dict[str, Any]:
        """

        if ("report" in prompt.lower() or "scouting report" in prompt.lower() or "generate report" in prompt.lower()) and "team" in prompt.lower():
            return self.handle_full_team_report(prompt)

        if ("report" in prompt.lower() or "scouting report" in prompt.lower() or "generate report" in prompt.lower()) and any(team.lower() in prompt.lower() for team in self._popular_esports_teams):
            return self.handle_full_team_report(prompt)

        if ((any(team.lower() in prompt.lower() for team in self._popular_esports_teams) or "team" in prompt.lower()) and
                ("head to head" in prompt.lower() or "vs" in prompt.lower() or "versus" in prompt.lower())):
            return self.handle_team_head_to_head_report(prompt)

        if (any(map_name in prompt.lower() for map_name in self.valorant_maps)) and (any(team.lower() in prompt.lower() for team in self._popular_esports_teams) or "team" in prompt.lower()):
            return self.handle_map_specific_team_report(prompt)

        return {}

    def handle_full_team_report(self, prompt: str) -> Dict[str, Any]:
        pass

    def handle_team_head_to_head_report(self, prompt: str) -> Dict[str, Any]:
        pass

    def handle_map_specific_team_report(self, prompt: str) -> Dict[str, Any]:
        pass

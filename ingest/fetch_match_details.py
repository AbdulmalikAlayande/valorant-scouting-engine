from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from clients.domain.match import get_series_state
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def ingest_series_state(series_id: str) -> Dict[str, Any]:
    """
    Fetch and normalize a detailed series state (Series State API).

    This module is primarily used to support:
    - agent picks / composition analysis (by game, by team)
    - quick per-game breakdowns (map, sides, scorelines)
    - player-level stat stubs for downstream transforms

    Notes:
    - The current GraphQL query shape (seriesstate.graphql) does not include
      round-by-round events; we expose "rounds" as an empty list for now to keep
      the contract stable for future expansion.
    """
    series_id = _require_non_empty(series_id, "series_id")

    try:
        raw = get_series_state(series_id=series_id)

        if not raw or not isinstance(raw, dict):
            _logger.warning(f"No series state found for series_id: {series_id}")
            return {
                "series_id": series_id,
                "series": None,
                "meta": {"kind": "series_state", "status": "not_found"},
            }

        normalized = _normalize_series_state(series_id=series_id, series_state=raw)

        games_count = len(normalized.get("games", []))
        teams_count = len(normalized.get("teams", []))
        _logger.info(
            f"Ingested series state series_id={series_id}: teams={teams_count}, games={games_count}"
        )

        return {
            "series_id": series_id,
            "series": normalized,
            "meta": {
                "kind": "series_state",
                "status": "ok",
                "game_count": games_count,
                "team_count": teams_count,
            },
        }

    except Exception as e:
        _logger.error(f"Failed ingest_series_state series_id={series_id}: {e}")
        return {
            "series_id": series_id,
            "series": None,
            "meta": {"kind": "series_state", "status": "error", "error": str(e)},
        }


def ingest_game_details(series_id: str, game_id: str) -> Dict[str, Any]:
    """
    Fetch and normalize a single game's details within a series.

    For now, this is derived by fetching the series state and selecting the
    requested game. This is sufficient for:
    - map / score / side info
    - per-player kills/deaths and agent played
    - per-team agent composition (5 agents list)
    """
    series_id = _require_non_empty(series_id, "series_id")
    game_id = _require_non_empty(game_id, "game_id")

    try:
        raw = get_series_state(series_id=series_id)
        if not raw or not isinstance(raw, dict):
            _logger.warning(
                f"No series state found when fetching game details series_id={series_id}, game_id={game_id}"
            )
            return {
                "series_id": series_id,
                "game_id": game_id,
                "game": None,
                "meta": {"kind": "game_details", "status": "not_found"},
            }

        normalized_series = _normalize_series_state(series_id=series_id, series_state=raw)
        games = normalized_series.get("games", [])
        game = next((g for g in games if g.get("game_id") == game_id), None)

        if not game:
            return {
                "series_id": series_id,
                "game_id": game_id,
                "game": None,
                "meta": {"kind": "game_details", "status": "not_found"},
            }

        return {
            "series_id": series_id,
            "game_id": game_id,
            "game": game,
            "meta": {"kind": "game_details", "status": "ok"},
        }

    except Exception as e:
        _logger.error(
            f"Failed ingest_game_details series_id={series_id}, game_id={game_id}: {e}"
        )
        return {
            "series_id": series_id,
            "game_id": game_id,
            "game": None,
            "meta": {"kind": "game_details", "status": "error", "error": str(e)},
        }


# -------------------------
# Normalization helpers
# -------------------------


def _require_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_series_state(series_id: str, series_state: Dict[str, Any]) -> Dict[str, Any]:
    # series_state is the node returned by clients.domain.match.get_series_state
    # For our client it returns data.get("series", {}) but the actual Series State
    # API query returns a "seriesState" node. We defensively accept either of them.
    series_node = _safe_dict(series_state.get("seriesState") or series_state)

    teams = _normalize_series_teams(_safe_list(series_node.get("teams")))
    games = _normalize_games(_safe_list(series_node.get("games")))

    # Derived aggregates that are useful for scouting report transforms
    agent_picks = _aggregate_agent_picks(games)
    compositions = _aggregate_compositions(games)

    return {
        "series_id": series_id,
        "format": series_node.get("format"),
        "started": series_node.get("started"),
        "finished": series_node.get("finished"),
        "valid": series_node.get("valid"),
        "teams": teams,
        "games": games,
        # Not currently available in query response; keep stable container for future expansion.
        "rounds": [],
        # Derived
        "agent_picks": agent_picks,
        "compositions": compositions,
    }


def _normalize_series_teams(teams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []

    for t in teams:
        t = _safe_dict(t)
        objectives = []
        for obj in _safe_list(t.get("objectives")):
            obj = _safe_dict(obj)
            objectives.append(
                {
                    "id": obj.get("id"),
                    "type": obj.get("type"),
                    "completion_count": obj.get("completionCount"),
                }
            )

        weapon_kills = []
        for wk in _safe_list(t.get("weaponKills")):
            wk = _safe_dict(wk)
            weapon_kills.append(
                {
                    "id": wk.get("id"),
                    "weapon_name": wk.get("weaponName"),
                    "count": wk.get("count", 0),
                }
            )

        multikills = []
        for mk in _safe_list(t.get("multikills")):
            mk = _safe_dict(mk)
            multikills.append(
                {
                    "id": mk.get("id"),
                    "number_of_kills": mk.get("numberOfKills"),
                    "count": mk.get("count", 0),
                }
            )

        players = []
        for p in _safe_list(t.get("players")):
            p = _safe_dict(p)
            players.append(
                {
                    "player_id": p.get("id"),
                    "name": p.get("name"),
                    "kills": p.get("kills", 0),
                    "deaths": p.get("deaths", 0),
                }
            )

        normalized.append(
            {
                "team_id": t.get("id"),
                "name": t.get("name"),
                "score": t.get("score"),
                "won": t.get("won"),
                "kills": t.get("kills", 0),
                "deaths": t.get("deaths", 0),
                "teamkills": t.get("teamkills"),
                "selfkills": t.get("selfkills"),
                "structures_destroyed": t.get("structuresDestroyed"),
                "structures_captured": t.get("structuresCaptured"),
                "objectives": objectives,
                "weapon_kills": weapon_kills,
                "multikills": multikills,
                "players": players,
            }
        )

    return normalized


def _normalize_games(games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_games: List[Dict[str, Any]] = []

    for g in games:
        g = _safe_dict(g)
        map_node = _safe_dict(g.get("map"))
        bounds = _safe_dict(map_node.get("bounds"))
        bounds_min = _safe_dict(bounds.get("min"))
        bounds_max = _safe_dict(bounds.get("max"))

        teams_out = []
        for team in _safe_list(g.get("teams")):
            team = _safe_dict(team)
            players_out = []
            agents_for_comp = []

            for p in _safe_list(team.get("players")):
                p = _safe_dict(p)
                character = _safe_dict(p.get("character"))
                agent_name = character.get("name")

                if isinstance(agent_name, str) and agent_name.strip():
                    agents_for_comp.append(agent_name.strip().lower())

                pos = _safe_dict(p.get("position"))
                players_out.append(
                    {
                        "name": p.get("name"),
                        "kills": p.get("kills", 0),
                        "deaths": p.get("deaths", 0),
                        "agent": agent_name,
                        "net_worth": p.get("netWorth"),
                        "money": p.get("money"),
                        "position": {"x": pos.get("x"), "y": pos.get("y")},
                    }
                )

            comp_tuple = _canonical_comp_tuple(agents_for_comp)

            teams_out.append(
                {
                    "name": team.get("name"),
                    "side": team.get("side"),
                    "won": team.get("won"),
                    "score": team.get("score"),
                    "players": players_out,
                    "composition": list(comp_tuple) if comp_tuple else [],
                }
            )

        normalized_games.append(
            {
                "game_id": g.get("id"),
                "sequence_number": g.get("sequenceNumber"),
                "started": g.get("started"),
                "paused": g.get("paused"),
                "finished": g.get("finished"),
                "map": {
                    "name": map_node.get("name"),
                    "bounds": {
                        "min": {"x": bounds_min.get("x"), "y": bounds_min.get("y")},
                        "max": {"x": bounds_max.get("x"), "y": bounds_max.get("y")},
                    },
                },
                "teams": teams_out,
            }
        )

    return normalized_games


def _canonical_comp_tuple(agent_names: List[str]) -> Tuple[str, ...]:
    """
    A canonical representation of a 5-agent comp. We:
    - lowercase
    - drop empties
    - sort
    """
    cleaned = [a.strip().lower() for a in agent_names if isinstance(a, str) and a.strip()]
    if not cleaned:
        return tuple()
    return tuple(sorted(cleaned))


def _aggregate_agent_picks(games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counter: Counter[str] = Counter()

    for g in games:
        for t in _safe_list(_safe_dict(g).get("teams")):
            for p in _safe_list(_safe_dict(t).get("players")):
                agent = _safe_dict(p).get("agent")
                if isinstance(agent, str) and agent.strip():
                    counter[agent.strip().lower()] += 1

    total = sum(counter.values()) or 0
    picks = []
    for agent_name, count in counter.most_common():
        pct = round((count / total) * 100, 2) if total else 0.0
        picks.append({"agent": agent_name, "count": count, "pick_rate_pct": pct})
    return picks


def _aggregate_compositions(games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Counts compositions by team_name + map_name (useful for "what comps do they run on X map?").
    """
    comp_counts: Dict[Tuple[Optional[str], Optional[str], Tuple[str, ...]], int] = defaultdict(int)

    for g in games:
        g = _safe_dict(g)
        map_name = _safe_dict(g.get("map")).get("name")

        for t in _safe_list(g.get("teams")):
            t = _safe_dict(t)
            team_name = t.get("name")
            comp = _canonical_comp_tuple(_safe_list(t.get("composition")))
            if comp:
                comp_counts[(team_name, map_name, comp)] += 1

    out = []
    for (team_name, map_name, comp), count in sorted(
            comp_counts.items(), key=lambda kv: kv[1], reverse=True
    ):
        out.append(
            {
                "team_name": team_name,
                "map_name": map_name,
                "composition": list(comp),
                "count": count,
            }
        )
    return out

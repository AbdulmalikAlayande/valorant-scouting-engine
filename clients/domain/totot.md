## GameSelection

- The selection of games played by a team.

Field	Type				Description
filter		GameStateFilter	The game data points filter criteria.
first		Int				The number of games that should be selected.
orderBy	[GameOrder!]		The order the games should be returned.

---

## GameStateFilter	

- The filter to apply to a game selection.

Field			Type								Description
map				MapFilter							Filter by map.
teams			GameTeamStateFilter				Filter by participating teams.
titleVersion		TitleVersionFilter					Filter by title version.
segments		SegmentStateFilter				Filter by segment state data points.
tournamentIds		IdFilter							Use tournament id instead
tournament		TeamGameStatisticsTournamentFilter	Filter by tournament data points.
timeWindow		TimeRangeFilter					Use startedAt filter instead
startedAt			DateTimeFilter					Filter by start date and time. This can be specified once in filter hierarchy and is mutually exclusive with tournamentIds filter.
and				[GameStateFilter!]					The list of filters to apply together with the current one by the AND logical operator.
or				[GameStateFilter!]					The list of filters to apply together with the current one by the OR logical operator.

---

## GameStatisticsFilter

- The game statistics selection filter.

Field		Type							Description
tournament	GameStatisticsTournamentFilter	Filter by tournament data points.
startedAt		DateTimeFilter				Filter by start date.
version		GameStatisticsVersionFilter		Filter by game version.

---

## GameStatisticsTournamentFilter

- Filter game statistics by tournament data points.

Field			Type		Description
id				IdFilter	Filter by tournament IDs.
includeChildren	Boolean!	Include child tournaments in the filter.

---

## GameStatisticsVersionFilter

- Filter by game version ID.

Field	Type				Description
id		IdFilter			None

---

## GameTeamStateFilter

- Filter by team game state.

Field		Type					Description
id			IdFilter				Filter by team ID.
side			StringFilter			Filter by team side.
objectives	ObjectiveFilter			Filter by objective.
players		GamePlayerStateFilter	Filter by player.
firstKill		BooleanFilter			Filter by first kill.

---

## IdFilter

- ID filter for entity identifiers.

Field	Type		Description
in		[ID!]		Array of IDs to look for.

---

## MapFilter

- Filter by map.
Field	Type				Description
name	StringFilter		Filter by map name.

---

## ObjectiveFilter

- Filter by objective.

Field	Type				Description
type				StringFilter		Filter by objective type.
completedFirst	BooleanFilter		Filter by completed first data point.

---

## PlayerStatisticsFilter

- The player statistics selection filter.

Field			Type							Description
tournamentIds		IdFilter						Use tournament id instead
tournament		PlayerStatisticsTournamentFilter	Filter by tournament data points.
timeWindow		TimeRangeFilter				Use startedAt filter instead
startedAt			DateTimeFilter				Filter by start date and time.

---

## TeamGameStatisticsTournamentFilter

- Filter team game statistics by tournament data points.

Field			Type				Description
id				IdFilter			Filter by tournament IDs.
includeChildren	Boolean!			Include child tournaments in the filter.
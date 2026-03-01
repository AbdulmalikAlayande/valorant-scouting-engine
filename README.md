# Stratigen Scouting Engine

**Stratigen Scouting Engine** is the core analytical powerhouse of the Stratigen AI platform. It is a high-performance, asynchronous Python worker designed to ingest professional esports data, perform complex tactical transformations, and generate LLM-augmented scouting reports for elite organizations.

While the broader Stratigen AI platform includes web dashboards and integration bots, this **engine** focuses strictly on the data pipeline: from raw GRID API streams to actionable strategic intelligence.

Currently, the engine is optimized for **VALORANT** (Hackathon Demo), with a modular architecture ready for **League of Legends** and other titles.

---

## System Architecture

The engine operates on a **Job-Worker** pattern using PostgreSQL as a persistent queue:

1. Job Acquisition: The engine polls the `report_requests` table for new natural language prompts.
2. Semantic Routing: Prompts are analyzed by a Pydantic AI agent (Gemini 2.5) to determine the required analysis tools.
3. Data Ingestion: Multi-stage fetching from the GRID Stats Feed (GraphQL) to collect team, player, map, and series-level data.
4. Transformation Layer: Raw data is processed through mathematical models (for example Elite Impact Score) and tactical heuristics.
5. Insight Generation: The LLM synthesizes raw data and transform results into "How to Win" actionable insights.
6. Persistence: The finalized `ScoutingReport` is serialized and stored back in the database for the frontend/API to consume.

---

## Features

### 1. LLM-Powered Semantic Routing
Unlike existing static tools, Stratigen AI understands natural language. Using Pydantic AI and Gemini, it interprets complex coaching prompts like "How do we exploit Liquid's defensive setups on Haven?" and automatically routes them to the correct analysis modules.

### 2. Elite Impact Score (EIS)
Our proprietary mathematical model goes beyond simple K/D. The EIS provides a role-adjusted performance metric that evaluates players based on their primary tactical responsibilities:
- Duelists: weighted for First Bloods (FK%) and Entry Impact.
- Initiators: weighted for Assist Conversion and ADR.
- Controllers/Sentinels: weighted for Utility Efficiency, Assists, and Survival.

The model normalizes performance against professional benchmarks, allowing scouts to identify star players and weak links with mathematical precision.

### 3. Comprehensive Data Checklist
Every full scouting report covers:
- Macro: map win rates, veto strategies, and pistol round conversion.
- Mid-Game: objective control (spikes/orbs) and economy patterns.
- Micro: star player identification, weak-link detection, and agent pool depth.

## Core Engine Modules

### 1. Ingestion Layer (`/ingestion`)
Handles all external communication with the GRID API.
- GraphQL client: optimized queries for `seriesState`, `playerStatistics`, and `teamGameStatistics`.
- Normalization: converts nested GRID responses into flat typed dictionaries for transforms.
- Title agnostic: modular fetchers that can be extended from VALORANT to LoL/CS2.

### 2. Analysis Transforms (`/transforms`)
The tactical analysis core where raw stats become tactical data.
- `player_analysis.py`: Elite Impact Score implementation.
- `map_analysis.py`: veto strategy logic and map win-rate normalization.
- `weakness_detection.py`: heuristics to identify recurring tactical patterns.
- `composition_analysis.py`: agent synergy and counter-pick analysis.

### 3. Intelligence Layer (`/jobs`)
Orchestrates the LLM and the workflow.
- `prompt_router.py`: maps user intent to specific Python handlers.
- `handler_functions.py`: orchestrates ingestion + transforms per report type.

---

## Directory Structure

```text
scouting-engine/
├── clients/            # Low-level GraphQL & GRID API clients
├── config/             # Global settings, logging, and constants
├── ingestion/          # Data fetching and normalization logic
├── jobs/               # Polling loop, Prompt Routing, and Task Handlers
├── models/             # Pydantic data models for internal typing
├── storage/            # Database scripts and CRUD operations
├── transforms/         # Tactical analysis logic and mathematical models
├── main.py             # Worker process control (on/off/status/once)
├── scoutingtool.toml   # Engine metadata and configuration
└── README.md
```

---

## Technical Architecture

- Data Source: GRID Data Consumer API (GraphQL) for real-time and historical match data.
- Intelligence: Pydantic AI + Google Gemini for reasoning and synthesis.
- Backend: Python 3.13 async worker (`asyncio`) for high-throughput polling.
- Output Layer: standardized JSON report schema for API consumption.
- Database: PostgreSQL for job queue and report persistence.

---

## Getting Started

### Prerequisites
- Python 3.13+
- GRID API Key
- Google Gemini API Key
- PostgreSQL instance

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pipenv install
   ```
3. Configure environment in `.env`:
   ```env
   GRID_API_KEY=your_key
   GEMINI_API_KEY=your_key
   DATABASE_URL=your_db_connection_string
   ```

## Worker Control (Cleaner Entry Point)

From `scouting-engine` root, use `main.py` as the single control point:

```bash
# Start worker in background (default)
python main.py on

# Start worker in foreground (attached)
python main.py on --foreground

# Stop worker
python main.py off

# Check worker status
python main.py status

# Process one job and exit (debug/manual run)
python main.py once
```

Backwards-compatible entry still works:

```bash
python -m jobs.report_generator
```

Notes:
- PID file: `logs/worker.pid`
- Background logs: `logs/worker.stdout.log`, `logs/worker.stderr.log`
- Ensure DB schema is applied before starting worker.

---

## Developer Guide: Extending the Engine

### 1. Add a New Analysis Tool
1. Define a tool model in `jobs/prompt_router.py`.
2. Add a handler in `jobs/handler_functions.py`.
3. Register it in `GeneralPromptRouter` via `@self.agent.tool`.

### 2. Add a New Transform
1. Create a transform file in `transforms/`.
2. Import it in `jobs/handler_functions.py`.
3. Include the result in the final report payload.

---

## Roadmap

- [x] Phase 1 (Hackathon): full VALORANT integration, LLM routing, EIS.
- [x] Phase 2: orchestration and retryable job lifecycle.
- [x] Phase 3: storage-plane separation and idempotent persistence.
- [x] Phase 4: typed feature registry + report composer + contract validation.
- [ ] Phase 5: real-time status delivery, scale tuning, SLO enforcement.

---

## License
Confidential - Internal Development.

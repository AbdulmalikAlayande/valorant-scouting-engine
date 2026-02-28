# Stratigen Scouting Engine

**Stratigen Scouting Engine** is the core analytical powerhouse of the Stratigen AI platform. It is a high-performance, asynchronous Python worker designed to ingest professional esports data, perform complex tactical transformations, and generate LLM-augmented scouting reports for elite organizations.

While the broader Stratigen AI platform includes web dashboards and integration bots, this **engine** focuses strictly on the data pipeline: from raw GRID API streams to actionable strategic intelligence.

Currently, the engine is optimized for **VALORANT** (Hackathon Demo), with a modular architecture ready for **League of Legends** and other titles.

---

## 🏗 System Architecture

The engine operates on a **Job-Worker** pattern using PostgreSQL as a persistent queue:

1.  **Job Acquisition**: The engine polls the `report_requests` table for new natural language prompts.
2.  **Semantic Routing**: Prompts are analyzed by a **Pydantic AI** agent (Gemini 2.5) to determine the required analysis tools.
3.  **Data Ingestion**: Multi-stage fetching from the **GRID Stats Feed** (GraphQL) to collect team, player, map, and series-level data.
4.  **Transformation Layer**: Raw data is processed through mathematical models (e.g., Elite Impact Score) and tactical heuristics.
5.  **Insight Generation**: The LLM synthesizes raw data and transform results into "How to Win" actionable insights.
6.  **Persistence**: The finalized `ScoutingReport` is serialized and stored back in the database for the frontend/API to consume.

---

## Features

### 1. LLM-Powered Semantic Routing
Unlike existing static tools, Stratigen AI understands natural language. Using **Pydantic AI** and **Gemini**, it interprets complex coaching prompts like *"How do we exploit Liquid's defensive setups on Haven?"* and automatically routes them to the correct analysis modules.

### 2. Elite Impact Score (EIS)
Our proprietary mathematical model goes beyond simple K/D. The **EIS** provides a role-adjusted performance metric that evaluates players based on their primary tactical responsibilities:
- **Duelists**: Weighted for **First Bloods (FK%)** and Entry Impact.
- **Initiators**: Weighted for **Assist Conversion** and ADR.
- **Controllers/Sentinels**: Weighted for **Utility Efficiency**, Assists, and Survival.

The model normalizes performance against professional benchmarks, allowing scouts to identify "Star Players" and "Weak Links" with mathematical precision.

### 3. Comprehensive Data Checklist
Every full scouting report covers:
- **Macro**: Map win rates, veto strategies, and pistol round conversion.
- **Mid-Game**: Objective control (Spikes/Orbs) and economy patterns.
- **Micro**: Star player identification, weak-link detection, and agent pool depth.

## 🧩 Core Engine Modules

### 1. Ingestion Layer (`/ingestion`)
Handles all external communication with the **GRID API**.
- **GraphQL Client**: Optimized queries for `seriesState`, `playerStatistics`, and `teamGameStatistics`.
- **Normalization**: Converts deeply nested GRID responses into flat, typed Python dictionaries for the transform layer.
- **Title Agnostic**: Modular fetchers that can be extended from VALORANT to LoL/CS2 by updating GraphQL fragments.

### 2. Analysis Transforms (`/transforms`)
The "Brain" of the engine where raw stats become tactical data.
- **`player_analysis.py`**: Implementation of the **Elite Impact Score (EIS)**.
- **`map_analysis.py`**: Veto strategy logic and map win-rate normalization.
- **`weakness_detection.py`**: Heuristics to identify predictable patterns (e.g., eco-round failures, early aggression vulnerabilities).
- **`composition_analysis.py`**: Analysis of agent synergies and counter-pick recommendations.

### 3. Intelligence Layer (`/jobs`)
Orchestrates the LLM and the workflow.
- **`prompt_router.py`**: Uses Pydantic AI to map user intent to specific Python handlers.
- **`handler_functions.py`**: Master orchestrators that chain ingestion and transforms to fulfill a specific report type.

---

## 📂 Directory Structure

```text
scouting-engine/
├── clients/            # Low-level GraphQL & GRID API clients
├── config/             # Global settings, logging, and constants
├── ingestion/          # Data fetching and normalization logic
├── jobs/               # Polling loop, Prompt Routing, and Task Handlers
├── models/             # Pydantic data models for internal typing
├── storage/            # Database scripts and CRUD operations
├── transforms/         # Tactical analysis logic and mathematical models
├── scoutingtool.toml   # Engine metadata and configuration
└── README.md           # You are here
```

---

## Technical Architecture

- **Data Source**: Deep integration with the **GRID Data Consumer API** (GraphQL) for real-time and historical professional match data.
- **Intelligence**: **Pydantic AI** + **Google Gemini** for reasoning and insight generation.
- **Backend**: Python 3.13 asynchronous worker using `asyncio` for high-throughput polling.
- **Output Layer**: Standardized JSON report schema designed for REST API consumption (FastAPI).
- **Database**: PostgreSQL handles the job queue (Polling Strategy) and report persistence.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.13+
- GRID API Key
- Google Gemini API Key
- PostgreSQL Instance

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pipenv install
   ```
3. Configure your environment in `.env`:
   ```env
   GRID_API_KEY=your_key
   GEMINI_API_KEY=your_key
   DATABASE_URL=your_db_connection_string
   ```

### Running the Engine
The engine runs as a background worker. It will poll your PostgreSQL database for any report requests with a `pending` status.

```bash
# Start the analysis worker
python -m jobs.report_generator
```

*Note: Ensure your database has the schema defined in `storage/scripts.sql` before running.*

---

## 🛠 Developer Guide: Extending the Engine

Stratigen is designed to be highly extensible. Here is how you can add new capabilities:

### 1. Adding a New Analysis Tool
If you want to support a new type of query (e.g., "Analyze economy across maps"), follow these steps:
1.  **Define a Tool Model**: Add a new Pydantic model in `jobs/prompt_router.py` to define the parameters the LLM should extract.
2.  **Create a Handler**: Add a new function in `jobs/handler_functions.py` to orchestrate the data fetching and transformation.
3.  **Register with Agent**: Add the tool to the `GeneralPromptRouter` class using the `@self.agent.tool` decorator.

### 2. Creating a New Transform
If you have a new mathematical model or tactical heuristic:
1.  Create a new file in `transforms/` (e.g., `clutch_analysis.py`).
2.  Import it into `jobs/handler_functions.py`.
3.  Include the new transform result in the final `report` dictionary.

---

## Roadmap

- [x] **Phase 1 (Hackathon)**: Full VALORANT Integration, LLM Routing, EIS Model.
- [ ] **Phase 2 (Post-Demo)**: League of Legends Support (Jungle pathing, Objective priority analysis).
- [ ] **Phase 3**: Standalone SaaS Dashboard & Internal API for Team Bots (Discord/Slack).

---

## License
Confidential - Internal Development.
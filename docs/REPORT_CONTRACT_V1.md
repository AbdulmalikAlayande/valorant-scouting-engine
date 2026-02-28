# ReportContract v1 (Frozen)

Contract version: `scouting-report.v1`

This contract is the worker-to-API payload contract for persisted report artifacts (`report_artifacts.report_json`) and finalized scouting reports.

## Canonical Sources
- Runtime model: `models/report_contract.py` (`ReportContractV1`)
- Schema: `docs/report_contract_v1.schema.json`
- Composer metadata injection: `composer/report_composer.py`

## Required Top-Level Fields
- `report_type`
- `metadata`

## Metadata Requirements
`metadata` must contain:
- `contract_version` = `scouting-report.v1`
- `feature_version` (current worker default `features-v2`)
- `composer_version` (current `report-composer.v1`)
- `feature_producer_versions` (map of producer name -> producer version)
- `lineage` object including `contract`, `feature_version`, `feature_producers`, `composer`

## Supported Report Types
- `full`
- `map`
- `player_performance`
- `h2h`
- `head_to_head`
- `tournament`
- `strategy_call`
- `agent_performance`
- `tell_exploit`
- `player_h2h`

## report_specific Typed Contract Kinds
- `map` -> `map`
- `player_performance` -> `player_performance`
- `h2h` / `head_to_head` -> `head_to_head`
- `tournament` -> `tournament`
- `strategy_call` -> `strategy_call`
- `agent_performance` -> `agent_performance`
- `tell_exploit` -> `tell_exploit`
- `player_h2h` -> `player_h2h`
- `full` -> `generic`

Worker boundary enforcement:
- Pre-persist validation enforces report type support + typed `report_specific` presence for typed report families.
- Pre-finalize validation enforces `ReportContractV1` model compliance.

## Job State / Status Mapping (API Handshake)

### Internal Worker Job Table (`report_jobs`)
- `state`: `QUEUED | RUNNING | COMPLETED | FAILED`
- `current_stage`: `INGESTING | FEATURIZING | SYNTHESIZING | COMPOSING | READY | FAILED`

### Request Table (`report_requests.status`)
- `PENDING | PROCESSING | COMPLETED | FAILED`

### Mapping Rules
1. Claim job:
- `report_jobs.state` -> `RUNNING`
- `report_jobs.current_stage` -> `INGESTING`
- `report_requests.status` -> `PROCESSING`

2. Pipeline stage updates:
- FEATURIZING, SYNTHESIZING, COMPOSING are reflected only in `report_jobs.current_stage`

3. Success terminal:
- `report_jobs.state` -> `COMPLETED`
- `report_jobs.current_stage` -> `READY`
- `report_requests.status` -> `COMPLETED`

4. Retryable failure:
- `report_jobs.state` -> `QUEUED`
- `report_jobs.current_stage` -> `INGESTING`
- `report_requests.status` -> `PENDING`

5. Non-retryable / exhausted failure:
- `report_jobs.state` -> `FAILED`
- `report_jobs.current_stage` -> `FAILED`
- `report_requests.status` -> `FAILED`

## Error Taxonomy Codes
- `RETRYABLE_PROVIDER`
- `RETRYABLE_INFRA`
- `NON_RETRYABLE_CONTRACT`
- `NON_RETRYABLE_AUTH`
- `NON_RETRYABLE_CONFIG`
- `NON_RETRYABLE_DATA`

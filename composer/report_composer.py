import copy
from typing import Any, Dict, Optional

from models.feature_bundle import FeatureBundle
from models.report_contract import REPORT_CONTRACT_VERSION


def compose_report(
    base_report: Dict[str, Any],
    feature_bundle: FeatureBundle,
    synthesized_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    report = copy.deepcopy(base_report) if isinstance(base_report, dict) else {}

    storage_planes = report.get("__storage_planes")
    if not isinstance(storage_planes, dict):
        storage_planes = {}

    report.update(feature_bundle.to_analysis_payload())

    if isinstance(synthesized_report, dict):
        report.update(synthesized_report)

    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    metadata["contract_version"] = REPORT_CONTRACT_VERSION
    metadata["feature_version"] = feature_bundle.feature_version
    metadata["feature_producer_versions"] = feature_bundle.producer_versions
    metadata["composer_version"] = "report-composer.v1"

    lineage = metadata.get("lineage")
    if not isinstance(lineage, dict):
        lineage = {}

    lineage["contract"] = REPORT_CONTRACT_VERSION
    lineage["feature_version"] = feature_bundle.feature_version
    lineage["feature_producers"] = feature_bundle.producer_versions
    lineage["composer"] = "report-composer.v1"

    metadata["lineage"] = lineage
    report["metadata"] = metadata

    storage_planes["features"] = feature_bundle.to_feature_plane_payloads()
    report["__storage_planes"] = storage_planes

    return report

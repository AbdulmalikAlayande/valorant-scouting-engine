import unittest

from models.feature_bundle import FeatureBundle, ReportSpecificFeature, MapReportContractFeature
from models.report_contract import (
    REPORT_CONTRACT_VERSION,
    validate_pre_finalize_contract,
    validate_pre_persist_contract,
)


class ReportContractValidationTests(unittest.TestCase):
    def test_pre_persist_rejects_missing_typed_contract(self):
        report_data = {"report_type": "map", "map_name": "Bind"}
        bundle = FeatureBundle(report_specific=ReportSpecificFeature(kind="generic"))

        with self.assertRaises(ValueError):
            validate_pre_persist_contract(report_data, bundle)

    def test_pre_persist_accepts_matching_typed_contract(self):
        report_data = {"report_type": "map", "map_name": "Bind"}
        bundle = FeatureBundle(
            report_specific=ReportSpecificFeature(
                kind="map",
                map_report=MapReportContractFeature(map_name="Bind"),
            )
        )

        validate_pre_persist_contract(report_data, bundle)

    def test_pre_finalize_requires_contract_metadata_fields(self):
        with self.assertRaises(Exception):
            validate_pre_finalize_contract(
                {
                    "report_type": "full",
                    "metadata": {},
                }
            )

    def test_pre_finalize_accepts_report_contract_v1_shape(self):
        validate_pre_finalize_contract(
            {
                "report_type": "full",
                "report_request_id": 1,
                "macro_analysis": {},
                "mid_game_analysis": {},
                "micro_analysis": {},
                "actionable_insights": [],
                "detailed_analysis": {},
                "metadata": {
                    "contract_version": REPORT_CONTRACT_VERSION,
                    "feature_version": "features-v2",
                    "composer_version": "report-composer.v1",
                    "feature_producer_versions": {},
                    "lineage": {},
                },
            }
        )


if __name__ == "__main__":
    unittest.main()

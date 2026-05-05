# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Unit tests for the deployment context engineering feature:
  - _deployment_failure_patterns.py  (pattern matching based on KuduLite error codes)
  - _deployment_context_engine.py    (context building & formatting)
"""

import unittest
from unittest.mock import MagicMock, patch

from azure.cli.command_modules.appservice._deployment_failure_patterns import (
    DEPLOYMENT_FAILURE_PATTERNS,
    get_failure_pattern,
    match_failure_pattern,
)
from azure.cli.command_modules.appservice._deployment_context_engine import (
    build_enriched_error_context,
    format_enriched_error_message,
    raise_enriched_deployment_error,
    extract_status_code_from_message,
    EnrichedDeploymentError,
    _determine_deployment_type,
)


def _make_mock_params(**overrides):
    """Create a minimal mock OneDeployParams object."""
    params = MagicMock()
    params.cmd = MagicMock()
    params.cmd.cli_ctx = MagicMock()
    params.resource_group_name = overrides.get("resource_group_name", "test-rg")
    params.webapp_name = overrides.get("webapp_name", "test-app")
    params.slot = overrides.get("slot", None)
    params.src_url = overrides.get("src_url", None)
    params.src_path = overrides.get("src_path", "app.zip")
    params.artifact_type = overrides.get("artifact_type", "zip")
    params.is_async_deployment = overrides.get("is_async_deployment", None)
    params.timeout = overrides.get("timeout", None)
    params.track_status = overrides.get("track_status", True)
    params.enable_kudu_warmup = overrides.get("enable_kudu_warmup", True)
    params.is_linux_webapp = overrides.get("is_linux_webapp", True)
    params.is_functionapp = overrides.get("is_functionapp", False)
    return params


# ---------------------------------------------------------------------------
# Tests for _deployment_failure_patterns
# ---------------------------------------------------------------------------
class TestDeploymentFailurePatterns(unittest.TestCase):
    """Tests for the KuduLite failure pattern definitions and lookup functions."""

    def test_all_patterns_have_required_keys(self):
        required_keys = {"errorCode", "stage", "suggestedFixes"}
        for pattern in DEPLOYMENT_FAILURE_PATTERNS:
            with self.subTest(errorCode=pattern["errorCode"]):
                self.assertTrue(required_keys.issubset(pattern.keys()))
                self.assertIsInstance(pattern["suggestedFixes"], list)
                self.assertGreater(len(pattern["suggestedFixes"]), 0)

    def test_no_pattern_has_common_causes(self):
        """Design review: commonCauses should not be present in any pattern."""
        for pattern in DEPLOYMENT_FAILURE_PATTERNS:
            with self.subTest(errorCode=pattern["errorCode"]):
                self.assertNotIn("commonCauses", pattern)

    def test_pattern_count(self):
        self.assertEqual(len(DEPLOYMENT_FAILURE_PATTERNS), 10)

    def test_get_failure_pattern_found(self):
        pattern = get_failure_pattern("DeploymentInProgress")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern["errorCode"], "DeploymentInProgress")
        self.assertEqual(pattern["stage"], "Deployment")

    def test_get_failure_pattern_not_found(self):
        self.assertIsNone(get_failure_pattern("NonExistentCode"))

    # --- match_failure_pattern: 400 Bad Request patterns ---
    def test_match_400_generic(self):
        p = match_failure_pattern(status_code=400, error_message="Deployment Failed. something broke")
        self.assertEqual(p["errorCode"], "DeploymentFailed")

    def test_match_400_invalid_type(self):
        p = match_failure_pattern(status_code=400, error_message="type='foo' not recognized")
        self.assertEqual(p["errorCode"], "InvalidArtifactType")

    def test_match_400_artifact_stack_mismatch(self):
        p = match_failure_pattern(status_code=400,
                                  error_message="Artifact type = 'war' cannot be deployed to stack = 'NODE'")
        self.assertEqual(p["errorCode"], "ArtifactStackMismatch")

    def test_match_400_missing_path(self):
        p = match_failure_pattern(status_code=400, error_message="Path must be defined for type='lib'")
        self.assertEqual(p["errorCode"], "MissingDeployPath")

    def test_match_400_invalid_path_trailing_slash(self):
        p = match_failure_pattern(status_code=400, error_message="Path cannot end with a '/'")
        self.assertEqual(p["errorCode"], "InvalidDeployPath")

    def test_match_400_invalid_path_traversal(self):
        p = match_failure_pattern(status_code=400,
                                  error_message="Path cannot contain '..' Please provide an absolute path.")
        self.assertEqual(p["errorCode"], "InvalidDeployPath")

    def test_match_400_invalid_package_uri(self):
        p = match_failure_pattern(status_code=400,
                                  error_message="Invalid packageUrl in the JSON request")
        self.assertEqual(p["errorCode"], "InvalidPackageUri")

    def test_match_400_clean_deploy_forbidden(self):
        p = match_failure_pattern(status_code=400,
                                  error_message="Clean deployments cannot be performed in the requested directory")
        self.assertEqual(p["errorCode"], "CleanDeployForbidden")

    def test_match_400_unsupported_artifact_type(self):
        p = match_failure_pattern(status_code=400, error_message="Artifact type 'foo' not supported")
        self.assertEqual(p["errorCode"], "UnsupportedArtifactType")

    def test_match_400_unmatched_falls_through_to_generic(self):
        """400 errors that don't match a specific pattern fall back to DeploymentFailed."""
        p = match_failure_pattern(status_code=400, error_message="No file uploaded")
        self.assertEqual(p["errorCode"], "DeploymentFailed")

    # --- match_failure_pattern: 409 Conflict ---
    def test_match_409_deployment_in_progress(self):
        p = match_failure_pattern(status_code=409,
                                  error_message="There is a deployment currently in progress")
        self.assertEqual(p["errorCode"], "DeploymentInProgress")

    def test_match_409_run_from_zip(self):
        p = match_failure_pattern(status_code=409,
                                  error_message="Run-From-Zip is set to a remote URL using WEBSITE_RUN_FROM_PACKAGE")
        self.assertEqual(p["errorCode"], "RunFromRemoteZipConfigured")

    def test_match_409_generic(self):
        p = match_failure_pattern(status_code=409, error_message="some conflict")
        self.assertEqual(p["errorCode"], "DeploymentInProgress")

    def test_match_no_match(self):
        p = match_failure_pattern(status_code=200, error_message="all good")
        self.assertIsNone(p)


# ---------------------------------------------------------------------------
# Tests for _deployment_context_engine
# ---------------------------------------------------------------------------
class TestDeploymentContextEngine(unittest.TestCase):
    """Tests for the context builder and formatter."""

    def _patch_app_metadata(self):
        """Patch the metadata fetching functions to avoid real API calls."""
        patcher_runtime = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_runtime",
            return_value="PYTHON|3.11"
        )
        patcher_region_sku = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_region_and_plan_sku",
            return_value=("Central India", "B1")
        )
        self.mock_runtime = patcher_runtime.start()
        self.mock_region_sku = patcher_region_sku.start()
        self.addCleanup(patcher_runtime.stop)
        self.addCleanup(patcher_region_sku.stop)

    def test_determine_deployment_type_zip(self):
        params = _make_mock_params(artifact_type="zip", src_url=None)
        self.assertEqual(_determine_deployment_type(params), "ZipDeploy")

    def test_determine_deployment_type_url(self):
        params = _make_mock_params(src_url="https://example.com/app.zip")
        self.assertEqual(_determine_deployment_type(params), "OneDeploy (URL-based)")

    def test_determine_deployment_type_war(self):
        params = _make_mock_params(artifact_type="war", src_url=None)
        self.assertEqual(_determine_deployment_type(params), "WarDeploy")

    def test_determine_deployment_type_kwargs_zip(self):
        """kwargs-only calling convention (no params object)."""
        self.assertEqual(_determine_deployment_type(artifact_type="zip"), "ZipDeploy")

    def test_determine_deployment_type_kwargs_url(self):
        self.assertEqual(
            _determine_deployment_type(src_url="https://example.com/app.zip"),
            "OneDeploy (URL-based)"
        )

    def test_determine_deployment_type_kwargs_override(self):
        """Explicit kwargs should override params values."""
        params = _make_mock_params(artifact_type="war", src_url=None)
        self.assertEqual(
            _determine_deployment_type(params, artifact_type="jar"),
            "JarDeploy"
        )

    def test_build_context_with_known_pattern(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=409,
            error_message="There is a deployment currently in progress. Please try again."
        )
        self.assertEqual(ctx["errorCode"], "DeploymentInProgress")
        self.assertEqual(ctx["stage"], "Deployment")
        self.assertEqual(ctx["runtime"], "PYTHON|3.11")
        self.assertEqual(ctx["region"], "Central India")
        self.assertEqual(ctx["planSku"], "B1")
        self.assertEqual(ctx["deploymentType"], "ZipDeploy")
        self.assertNotIn("commonCauses", ctx)
        self.assertIn("suggestedFixes", ctx)

    def test_build_context_with_unknown_error(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=599, error_message="Something weird"
        )
        self.assertEqual(ctx["errorCode"], "HTTP_599")
        self.assertIn("rawError", ctx)
        self.assertNotIn("commonCauses", ctx)

    def test_build_context_includes_last_known_step(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=409, last_known_step="ZipExtract started",
            error_message="There is a deployment currently in progress."
        )
        self.assertEqual(ctx["lastKnownStep"], "ZipExtract started")

    def test_build_context_includes_kudu_status(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=500, kudu_status="500",
            error_message="Internal error"
        )
        self.assertEqual(ctx["kuduStatus"], "500")

    def test_format_error_message_contains_key_sections(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=409,
            error_message="There is a deployment currently in progress."
        )
        msg = format_enriched_error_message(ctx)

        self.assertIn("DEPLOYMENT FAILED", msg)
        self.assertIn("DeploymentInProgress", msg)
        self.assertIn("Deployment", msg)
        self.assertNotIn("Common Causes:", msg)
        self.assertIn("Suggested Fixes:", msg)
        self.assertIn("GitHub Copilot Chat", msg)
        # Should NOT have duplicate YAML block
        self.assertNotIn("--- COPILOT CONTEXT ---", msg)
        self.assertNotIn("--- END CONTEXT ---", msg)

    def test_raise_enriched_deployment_error(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        with self.assertRaises(EnrichedDeploymentError) as cm:
            raise_enriched_deployment_error(
                params, status_code=409,
                error_message="There is a deployment currently in progress."
            )
        self.assertIn("DeploymentInProgress", str(cm.exception))
        self.assertIn("DEPLOYMENT FAILED", str(cm.exception))

    def test_raise_enriched_deployment_error_kwargs_only(self):
        """Call raise_enriched_deployment_error with kwargs instead of params."""
        self._patch_app_metadata()
        mock_cmd = MagicMock()
        mock_cmd.cli_ctx = MagicMock()
        with self.assertRaises(EnrichedDeploymentError) as cm:
            raise_enriched_deployment_error(
                cmd=mock_cmd,
                resource_group_name="test-rg",
                webapp_name="test-app",
                artifact_type="zip",
                status_code=400,
                error_message="Artifact type = 'war' cannot be deployed to stack = 'NODE'"
            )
        self.assertIn("ArtifactStackMismatch", str(cm.exception))
        self.assertIn("DEPLOYMENT FAILED", str(cm.exception))
        self.assertIn("ZipDeploy", str(cm.exception))

    def test_build_context_kwargs_only(self):
        """Call build_enriched_error_context with kwargs instead of params."""
        self._patch_app_metadata()
        mock_cmd = MagicMock()
        mock_cmd.cli_ctx = MagicMock()
        ctx = build_enriched_error_context(
            cmd=mock_cmd,
            resource_group_name="test-rg",
            webapp_name="test-app",
            artifact_type="zip",
            status_code=409,
            error_message="There is a deployment currently in progress."
        )
        self.assertEqual(ctx["errorCode"], "DeploymentInProgress")
        self.assertEqual(ctx["deploymentType"], "ZipDeploy")

    def test_format_includes_extra_diagnostics(self):
        """Verify that lastKnownStep and kuduStatus appear in the formatted message when present."""
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=500,
            error_message="Deploy error",
            last_known_step="ZipExtract started", kudu_status="500"
        )
        msg = format_enriched_error_message(ctx)
        self.assertIn("Last Step   : ZipExtract started", msg)
        self.assertIn("Kudu Status : 500", msg)


# ---------------------------------------------------------------------------
# Integration-level test: verify the full error flow
# ---------------------------------------------------------------------------
class TestDeploymentErrorFlow(unittest.TestCase):
    """End-to-end tests simulating real Kudu deployment failures."""

    def _patch_app_metadata(self):
        patcher_runtime = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_runtime",
            return_value="NODE|18"
        )
        patcher_region_sku = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_region_and_plan_sku",
            return_value=("East US", "P1V2")
        )
        self.mock_runtime = patcher_runtime.start()
        self.mock_region_sku = patcher_region_sku.start()
        self.addCleanup(patcher_runtime.stop)
        self.addCleanup(patcher_region_sku.stop)

    def test_conflict_deployment_in_progress(self):
        """Simulate a 409 Conflict — deployment lock held."""
        self._patch_app_metadata()
        params = _make_mock_params(artifact_type="zip")
        with self.assertRaises(EnrichedDeploymentError) as cm:
            raise_enriched_deployment_error(
                params, status_code=409,
                error_message="There is a deployment currently in progress. Please try again when it completes.",
                kudu_status="409"
            )
        error_msg = str(cm.exception)
        self.assertIn("DeploymentInProgress", error_msg)
        self.assertIn("NODE|18", error_msg)
        self.assertIn("P1V2", error_msg)
        self.assertIn("Wait for the current deployment to complete", error_msg)

    def test_400_artifact_stack_mismatch_scenario(self):
        """Simulate a 400 artifact/stack mismatch."""
        self._patch_app_metadata()
        params = _make_mock_params(artifact_type="war")
        with self.assertRaises(EnrichedDeploymentError) as cm:
            raise_enriched_deployment_error(
                params, status_code=400,
                error_message="Artifact type = 'war' cannot be deployed to stack = 'NODE'"
            )
        error_msg = str(cm.exception)
        self.assertIn("ArtifactStackMismatch", error_msg)
        self.assertIn("Ensure the artifact type matches", error_msg)

    def test_generic_400_scenario(self):
        """Simulate a generic 400 deployment failure."""
        self._patch_app_metadata()
        params = _make_mock_params()
        with self.assertRaises(EnrichedDeploymentError) as cm:
            raise_enriched_deployment_error(
                params, status_code=400,
                error_message="Something unexpected went wrong during deployment"
            )
        error_msg = str(cm.exception)
        self.assertIn("DeploymentFailed", error_msg)

    def test_unknown_status_code_scenario(self):
        """Simulate an error with a status code that has no matching pattern."""
        self._patch_app_metadata()
        params = _make_mock_params()
        with self.assertRaises(EnrichedDeploymentError) as cm:
            raise_enriched_deployment_error(
                params, status_code=503,
                error_message="Service Unavailable"
            )
        error_msg = str(cm.exception)
        self.assertIn("HTTP_503", error_msg)


# ---------------------------------------------------------------------------
# Tests for extract_status_code_from_message
# ---------------------------------------------------------------------------
class TestExtractStatusCode(unittest.TestCase):
    """Tests for the status code extraction helper."""

    # --- True positives: should extract the correct status code ---
    def test_status_code_colon_format(self):
        self.assertEqual(extract_status_code_from_message("Status Code: 400, Details: ..."), 400)

    def test_status_code_no_space(self):
        self.assertEqual(extract_status_code_from_message("StatusCode:504"), 504)

    def test_parenthesized_format(self):
        self.assertEqual(extract_status_code_from_message("Bad Request(400)"), 400)

    def test_http_prefix(self):
        self.assertEqual(extract_status_code_from_message("HTTP 504 Gateway Timeout"), 504)

    def test_code_with_reason_phrase(self):
        self.assertEqual(extract_status_code_from_message("400 Bad Request"), 400)

    def test_403_forbidden(self):
        self.assertEqual(extract_status_code_from_message("403 Forbidden"), 403)

    def test_500_internal(self):
        self.assertEqual(extract_status_code_from_message("500 Internal Server Error"), 500)

    def test_429_too_many(self):
        self.assertEqual(extract_status_code_from_message("429 Too Many Requests"), 429)

    # --- False positives: should NOT extract a status code ---
    def test_port_number_443(self):
        self.assertIsNone(extract_status_code_from_message("Connected on port 443"))

    def test_exit_code_500(self):
        self.assertIsNone(extract_status_code_from_message("deployed 500 files successfully"))

    def test_timeout_milliseconds(self):
        self.assertIsNone(extract_status_code_from_message("timeout after 500 ms"))

    def test_app_name_with_numbers(self):
        self.assertIsNone(extract_status_code_from_message("app-400-test failed to deploy"))

    def test_empty_message(self):
        self.assertIsNone(extract_status_code_from_message(""))

    def test_none_message(self):
        self.assertIsNone(extract_status_code_from_message(None))

    def test_no_status_code(self):
        self.assertIsNone(extract_status_code_from_message("something went wrong"))

    # --- Edge case: 200-range should NOT be extracted ---
    def test_200_not_extracted(self):
        self.assertIsNone(extract_status_code_from_message("Status Code: 200"))


if __name__ == '__main__':
    unittest.main()

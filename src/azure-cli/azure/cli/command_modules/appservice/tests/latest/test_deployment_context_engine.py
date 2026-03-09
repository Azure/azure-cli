# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Unit tests for the deployment context engineering feature:
  - _deployment_failure_patterns.py  (pattern matching)
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
    """Tests for the failure pattern definitions and lookup functions."""

    def test_all_patterns_have_required_keys(self):
        required_keys = {"errorCode", "stage", "commonCauses", "suggestedFixes"}
        for pattern in DEPLOYMENT_FAILURE_PATTERNS:
            with self.subTest(errorCode=pattern["errorCode"]):
                self.assertTrue(required_keys.issubset(pattern.keys()))
                self.assertIsInstance(pattern["commonCauses"], list)
                self.assertIsInstance(pattern["suggestedFixes"], list)
                self.assertGreater(len(pattern["commonCauses"]), 0)
                self.assertGreater(len(pattern["suggestedFixes"]), 0)

    def test_pattern_count(self):
        self.assertEqual(len(DEPLOYMENT_FAILURE_PATTERNS), 20)

    def test_get_failure_pattern_found(self):
        pattern = get_failure_pattern("ZipDeployTimeout")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern["errorCode"], "ZipDeployTimeout")
        self.assertEqual(pattern["stage"], "ZipExtract")

    def test_get_failure_pattern_not_found(self):
        self.assertIsNone(get_failure_pattern("NonExistentCode"))

    # --- match_failure_pattern: status-code based ---
    def test_match_504_returns_zip_deploy_timeout(self):
        p = match_failure_pattern(status_code=504)
        self.assertEqual(p["errorCode"], "ZipDeployTimeout")

    def test_match_504_with_scm_returns_scm_timeout(self):
        p = match_failure_pattern(status_code=504, error_message="SCM site timed out")
        self.assertEqual(p["errorCode"], "SCMTimeout")

    def test_match_408_returns_zip_deploy_timeout(self):
        p = match_failure_pattern(status_code=408)
        self.assertEqual(p["errorCode"], "ZipDeployTimeout")

    def test_match_401_returns_auth_failed(self):
        p = match_failure_pattern(status_code=401)
        self.assertEqual(p["errorCode"], "AuthFailed")

    def test_match_403_ssl_returns_ssl_validation_failed(self):
        p = match_failure_pattern(status_code=403, error_message="SSL certificate error")
        self.assertEqual(p["errorCode"], "SSLValidationFailed")

    def test_match_403_permission_denied(self):
        p = match_failure_pattern(status_code=403, error_message="Permission denied")
        self.assertEqual(p["errorCode"], "PermissionDenied")

    def test_match_409_lock_returns_file_lock_error(self):
        p = match_failure_pattern(status_code=409, error_message="File is locked")
        self.assertEqual(p["errorCode"], "FileLockError")

    def test_match_429_returns_insufficient_quota(self):
        p = match_failure_pattern(status_code=429)
        self.assertEqual(p["errorCode"], "InsufficientQuota")

    # --- match_failure_pattern: deployment-status based ---
    def test_match_build_failed(self):
        p = match_failure_pattern(deployment_status="BuildFailed")
        self.assertEqual(p["errorCode"], "OryxBuildFailed")

    def test_match_runtime_failed_oom(self):
        p = match_failure_pattern(deployment_status="RuntimeFailed",
                                  error_message="Container killed with exit code 137")
        self.assertEqual(p["errorCode"], "Exit137")

    def test_match_runtime_failed_port(self):
        p = match_failure_pattern(deployment_status="RuntimeFailed",
                                  error_message="Failed to bind to port 8080")
        self.assertEqual(p["errorCode"], "PortBindingError")

    def test_match_runtime_failed_probe(self):
        p = match_failure_pattern(deployment_status="RuntimeFailed",
                                  error_message="Health probe failed")
        self.assertEqual(p["errorCode"], "StartupProbeFailed")

    def test_match_runtime_failed_docker(self):
        p = match_failure_pattern(deployment_status="RuntimeFailed",
                                  error_message="Failed to pull Docker image")
        self.assertEqual(p["errorCode"], "DockerImagePullFailed")

    def test_match_runtime_failed_generic(self):
        p = match_failure_pattern(deployment_status="RuntimeFailed",
                                  error_message="some unknown error")
        self.assertIsNotNone(p)  # should still return a pattern

    # --- match_failure_pattern: message-based fallback ---
    def test_match_webjob_message(self):
        p = match_failure_pattern(error_message="WebJob startup error")
        self.assertEqual(p["errorCode"], "WebJobFailed")

    def test_match_timeout_message(self):
        p = match_failure_pattern(error_message="Timeout reached while tracking status")
        self.assertEqual(p["errorCode"], "ZipDeployTimeout")

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
        patcher_region = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_region",
            return_value="Central India"
        )
        patcher_sku = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_plan_sku",
            return_value="B1"
        )
        self.mock_runtime = patcher_runtime.start()
        self.mock_region = patcher_region.start()
        self.mock_sku = patcher_sku.start()
        self.addCleanup(patcher_runtime.stop)
        self.addCleanup(patcher_region.stop)
        self.addCleanup(patcher_sku.stop)

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
            params, status_code=504, error_message="Gateway Timeout"
        )
        self.assertEqual(ctx["errorCode"], "ZipDeployTimeout")
        self.assertEqual(ctx["stage"], "ZipExtract")
        self.assertEqual(ctx["runtime"], "PYTHON|3.11")
        self.assertEqual(ctx["region"], "Central India")
        self.assertEqual(ctx["planSku"], "B1")
        self.assertEqual(ctx["deploymentType"], "ZipDeploy")
        self.assertIn("commonCauses", ctx)
        self.assertIn("suggestedFixes", ctx)

    def test_build_context_with_unknown_error(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=599, error_message="Something weird"
        )
        self.assertEqual(ctx["errorCode"], "HTTP_599")
        self.assertIn("rawError", ctx)

    def test_build_context_with_deployment_properties(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        props = {
            "numberOfInstancesInProgress": "1",
            "numberOfInstancesSuccessful": "0",
            "numberOfInstancesFailed": "2",
            "errors": [{"extendedCode": "EXT001", "message": "OOM killed"}],
            "failedInstancesLogs": ["https://logs.example.com/log1"]
        }
        ctx = build_enriched_error_context(
            params, deployment_status="RuntimeFailed",
            error_message="OOM killed", deployment_properties=props
        )
        self.assertEqual(ctx["errorCode"], "Exit137")
        self.assertIn("instanceStatus", ctx)
        self.assertEqual(ctx["instanceStatus"]["numberOfInstancesFailed"], 2)
        self.assertIn("deploymentErrors", ctx)
        self.assertEqual(ctx["failedInstanceLogs"], "https://logs.example.com/log1")

    def test_build_context_includes_last_known_step(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=504, last_known_step="ZipExtract started"
        )
        self.assertEqual(ctx["lastKnownStep"], "ZipExtract started")

    def test_build_context_includes_kudu_status(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(
            params, status_code=504, kudu_status="504"
        )
        self.assertEqual(ctx["kuduStatus"], "504")

    def test_format_error_message_contains_key_sections(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(params, status_code=504)
        msg = format_enriched_error_message(ctx)

        self.assertIn("DEPLOYMENT FAILED", msg)
        self.assertIn("COPILOT CONTEXT", msg)
        self.assertIn("ZipDeployTimeout", msg)
        self.assertIn("ZipExtract", msg)
        self.assertIn("Common Causes:", msg)
        self.assertIn("Suggested Fixes:", msg)
        self.assertIn("Ask Copilot:", msg)
        self.assertIn("gh copilot explain", msg)

    def test_format_error_message_yaml_block(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        ctx = build_enriched_error_context(params, status_code=504)
        msg = format_enriched_error_message(ctx)

        self.assertIn("--- COPILOT CONTEXT ---", msg)
        self.assertIn("--- END CONTEXT ---", msg)
        # The YAML block should contain the errorCode
        start_idx = msg.index("--- COPILOT CONTEXT ---")
        end_idx = msg.index("--- END CONTEXT ---")
        yaml_block = msg[start_idx:end_idx]
        self.assertIn("errorCode: ZipDeployTimeout", yaml_block)

    def test_raise_enriched_deployment_error(self):
        self._patch_app_metadata()
        params = _make_mock_params()
        from knack.util import CLIError
        with self.assertRaises(CLIError) as cm:
            raise_enriched_deployment_error(
                params, status_code=504, error_message="Gateway Timeout"
            )
        self.assertIn("ZipDeployTimeout", str(cm.exception))
        self.assertIn("COPILOT CONTEXT", str(cm.exception))

    def test_raise_enriched_deployment_error_kwargs_only(self):
        """Call raise_enriched_deployment_error with kwargs instead of params."""
        self._patch_app_metadata()
        mock_cmd = MagicMock()
        mock_cmd.cli_ctx = MagicMock()
        from knack.util import CLIError
        with self.assertRaises(CLIError) as cm:
            raise_enriched_deployment_error(
                cmd=mock_cmd,
                resource_group_name="test-rg",
                webapp_name="test-app",
                artifact_type="zip",
                status_code=504,
                error_message="Gateway Timeout"
            )
        self.assertIn("ZipDeployTimeout", str(cm.exception))
        self.assertIn("COPILOT CONTEXT", str(cm.exception))
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
            status_code=504,
            error_message="Gateway Timeout"
        )
        self.assertEqual(ctx["errorCode"], "ZipDeployTimeout")
        self.assertEqual(ctx["deploymentType"], "ZipDeploy")


# ---------------------------------------------------------------------------
# Integration-level test: verify the full error flow
# ---------------------------------------------------------------------------
class TestDeploymentErrorFlow(unittest.TestCase):
    """End-to-end tests simulating real deployment failures."""

    def _patch_app_metadata(self):
        patcher_runtime = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_runtime",
            return_value="NODE|18"
        )
        patcher_region = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_region",
            return_value="East US"
        )
        patcher_sku = patch(
            "azure.cli.command_modules.appservice._deployment_context_engine._get_app_plan_sku",
            return_value="P1V2"
        )
        self.mock_runtime = patcher_runtime.start()
        self.mock_region = patcher_region.start()
        self.mock_sku = patcher_sku.start()
        self.addCleanup(patcher_runtime.stop)
        self.addCleanup(patcher_region.stop)
        self.addCleanup(patcher_sku.stop)

    def test_timeout_scenario(self):
        """Simulate a 504 Gateway Timeout during zip deploy."""
        self._patch_app_metadata()
        params = _make_mock_params(artifact_type="zip")
        from knack.util import CLIError
        with self.assertRaises(CLIError) as cm:
            raise_enriched_deployment_error(
                params, status_code=504,
                error_message="The gateway did not receive a response from the upstream server in time.",
                kudu_status="504"
            )
        error_msg = str(cm.exception)
        self.assertIn("ZipDeployTimeout", error_msg)
        self.assertIn("NODE|18", error_msg)
        self.assertIn("P1V2", error_msg)
        self.assertIn("Scale up the App Service plan", error_msg)

    def test_build_failed_scenario(self):
        """Simulate a build failure (Oryx)."""
        self._patch_app_metadata()
        params = _make_mock_params()
        props = {
            "errors": [{"extendedCode": "ORYX_BUILD_001",
                         "message": "Could not find requirements.txt"}],
            "failedInstancesLogs": []
        }
        from knack.util import CLIError
        with self.assertRaises(CLIError) as cm:
            raise_enriched_deployment_error(
                params, deployment_status="BuildFailed",
                error_message="Oryx build failed: Could not find requirements.txt",
                deployment_properties=props
            )
        error_msg = str(cm.exception)
        self.assertIn("OryxBuildFailed", error_msg)
        self.assertIn("Build", error_msg)

    def test_runtime_failed_oom_scenario(self):
        """Simulate a runtime failure due to OOM (exit 137)."""
        self._patch_app_metadata()
        params = _make_mock_params()
        props = {
            "numberOfInstancesInProgress": "0",
            "numberOfInstancesSuccessful": "0",
            "numberOfInstancesFailed": "1",
            "errors": [{"extendedCode": "RUNTIME_OOM",
                         "message": "Container exited with code 137"}],
            "failedInstancesLogs": ["https://logs.example.com/instance0"]
        }
        from knack.util import CLIError
        with self.assertRaises(CLIError) as cm:
            raise_enriched_deployment_error(
                params, deployment_status="RuntimeFailed",
                error_message="Container exited with code 137 OOM",
                deployment_properties=props
            )
        error_msg = str(cm.exception)
        self.assertIn("Exit137", error_msg)
        self.assertIn("ContainerStartup", error_msg)
        self.assertIn("Lazy-load", error_msg)


if __name__ == '__main__':
    unittest.main()

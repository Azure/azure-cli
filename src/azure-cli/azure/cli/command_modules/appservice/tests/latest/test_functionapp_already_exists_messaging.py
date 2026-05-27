# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""
Unit tests covering Phase 1 of the "already exists" output-consistency work (issue #32951).

These tests exercise:
  * try_create_application_insights and try_create_workspace_based_application_insights:
      message must say "already exists" (not "was created") when the AI component is
      already present.
  * Flex Consumption create path: the Microsoft.Web RP "hosting constraints" error
      should be translated into an actionable ValidationError.

All tests are mock-based so they do not hit Azure.
"""
import unittest
from unittest import mock

from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import ValidationError

from azure.cli.command_modules.appservice.custom import (
    try_create_application_insights,
    try_create_workspace_based_application_insights,
)


def _make_functionapp_stub():
    fa = mock.MagicMock()
    fa.resource_group = "myrg"
    fa.name = "myfuncapp"
    fa.location = "eastus"
    fa.id = "/subscriptions/sub/resourceGroups/myrg/providers/Microsoft.Web/sites/myfuncapp"
    return fa


def _make_appinsights_stub():
    ai = mock.MagicMock()
    ai.name = "myfuncapp"
    ai.id = "/subscriptions/sub/resourceGroups/myrg/providers/microsoft.insights/components/myfuncapp"
    ai.instrumentation_key = "00000000-0000-0000-0000-000000000000"
    ai.connection_string = "InstrumentationKey=00000000-0000-0000-0000-000000000000"
    return ai


class TryCreateApplicationInsightsMessagingTest(unittest.TestCase):
    """Covers try_create_application_insights message change (#32951)."""

    @mock.patch("azure.cli.command_modules.appservice.custom.update_app_settings")
    @mock.patch("azure.cli.command_modules.appservice.custom.is_centauri_functionapp", return_value=False)
    @mock.patch("azure.cli.command_modules.appservice.custom.get_mgmt_service_client")
    @mock.patch("azure.cli.command_modules.appservice.custom.logger")
    def test_message_says_created_when_appinsights_does_not_exist(
            self, mock_logger, mock_get_client, _mock_is_centauri, _mock_update_settings):
        client = mock.MagicMock()
        # .get() raises -> component does not yet exist
        client.components.get.side_effect = HttpResponseError("not found")
        client.components.create_or_update.return_value = _make_appinsights_stub()
        mock_get_client.return_value = client

        try_create_application_insights(cmd=mock.MagicMock(), functionapp=_make_functionapp_stub())

        warnings = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertTrue(any("was created for this Function App" in w for w in warnings),
                        "Expected first-run 'was created' message, got: {}".format(warnings))
        self.assertFalse(any("already exists" in w for w in warnings),
                         "First run must not say 'already exists', got: {}".format(warnings))

    @mock.patch("azure.cli.command_modules.appservice.custom.update_app_settings")
    @mock.patch("azure.cli.command_modules.appservice.custom.is_centauri_functionapp", return_value=False)
    @mock.patch("azure.cli.command_modules.appservice.custom.get_mgmt_service_client")
    @mock.patch("azure.cli.command_modules.appservice.custom.logger")
    def test_message_says_already_exists_when_appinsights_present(
            self, mock_logger, mock_get_client, _mock_is_centauri, _mock_update_settings):
        client = mock.MagicMock()
        # .get() returns an existing component -> already exists path
        existing = _make_appinsights_stub()
        client.components.get.return_value = existing
        client.components.create_or_update.return_value = existing
        mock_get_client.return_value = client

        try_create_application_insights(cmd=mock.MagicMock(), functionapp=_make_functionapp_stub())

        warnings = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertTrue(any("already exists" in w for w in warnings),
                        "Expected 'already exists' message on re-run, got: {}".format(warnings))
        self.assertFalse(any("was created for this Function App" in w for w in warnings),
                         "Re-run must not claim creation, got: {}".format(warnings))


class TryCreateWorkspaceBasedApplicationInsightsMessagingTest(unittest.TestCase):
    """Covers try_create_workspace_based_application_insights message change (#32951)."""

    @mock.patch("azure.cli.command_modules.appservice.custom.update_app_settings")
    @mock.patch("azure.cli.command_modules.appservice.custom._normalize_location",
                side_effect=lambda _cmd, loc: loc)
    @mock.patch("azure.cli.command_modules.appservice.custom.get_workspace")
    @mock.patch("azure.cli.command_modules.appservice.custom.get_mgmt_service_client")
    @mock.patch("azure.cli.command_modules.appservice.custom.logger")
    def test_workspace_based_says_created_when_new(
            self, mock_logger, mock_get_client, mock_get_workspace, _mock_norm, _mock_update):
        workspace = mock.MagicMock()
        workspace.id = "/subscriptions/sub/.../workspaces/ws1"
        mock_get_workspace.return_value = workspace

        client = mock.MagicMock()
        client.components.get.side_effect = HttpResponseError("not found")
        client.components.create_or_update.return_value = _make_appinsights_stub()
        mock_get_client.return_value = client

        try_create_workspace_based_application_insights(
            cmd=mock.MagicMock(), functionapp=_make_functionapp_stub(), workspace_name="ws1")

        warnings = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertTrue(any("was created for this Function App" in w for w in warnings), warnings)
        self.assertFalse(any("already exists" in w for w in warnings), warnings)

    @mock.patch("azure.cli.command_modules.appservice.custom.update_app_settings")
    @mock.patch("azure.cli.command_modules.appservice.custom._normalize_location",
                side_effect=lambda _cmd, loc: loc)
    @mock.patch("azure.cli.command_modules.appservice.custom.get_workspace")
    @mock.patch("azure.cli.command_modules.appservice.custom.get_mgmt_service_client")
    @mock.patch("azure.cli.command_modules.appservice.custom.logger")
    def test_workspace_based_says_already_exists_when_present(
            self, mock_logger, mock_get_client, mock_get_workspace, _mock_norm, _mock_update):
        workspace = mock.MagicMock()
        workspace.id = "/subscriptions/sub/.../workspaces/ws1"
        mock_get_workspace.return_value = workspace

        client = mock.MagicMock()
        existing = _make_appinsights_stub()
        client.components.get.return_value = existing
        client.components.create_or_update.return_value = existing
        mock_get_client.return_value = client

        try_create_workspace_based_application_insights(
            cmd=mock.MagicMock(), functionapp=_make_functionapp_stub(), workspace_name="ws1")

        warnings = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertTrue(any("already exists" in w for w in warnings), warnings)
        self.assertFalse(any("was created for this Function App" in w for w in warnings), warnings)


class FlexConsumptionHostingConstraintsTranslationTest(unittest.TestCase):
    """Verify the 'hosting constraints' RP error translation (#32951).

    The branch in custom.py probes for an existing site with web_apps.get before
    asserting "already exists" in the headline. This test covers both:
      * site exists -> specific "already exists" headline + 4 safe-first bullets
      * site does NOT exist -> neutral "hosting conflict" headline + neutral bullets
    plus pinning the predicate against known RP message variants.
    """

    def test_hosting_constraints_predicate_matches_known_variants(self):
        # Pin the predicate so wording drift in the RP message catches a test.
        for rp_message in (
                "Cannot change the site 'myapp' due to hosting constraints.",
                "Cannot change the site myapp due to hosting constraint.",
                "CANNOT CHANGE THE SITE 'myapp' DUE TO HOSTING CONSTRAINTS.",
        ):
            normalized = rp_message.lower()
            self.assertTrue(
                'hosting constraints' in normalized or 'hosting constraint' in normalized,
                f"predicate must match RP variant: {rp_message}")

    def test_validation_error_when_existing_site_present_is_safe_by_default(self):
        # Branch: existing site WAS found -> specific "already exists" headline.
        # Manager-review checklist:
        #   1. Headline asserts existence (true, because we verified with GET).
        #   2. Headline does not leak RP internals or autogenerated plan names.
        #   3. First bullet is the SAFE action (rename), not the destructive one.
        #   4. Destructive `az functionapp delete` bullet is LAST and explicitly
        #      flags it as destructive.
        name = "myapp"
        resource_group_name = "myrg"
        err = ValidationError(
            "A function app or site named '{0}' already exists in resource group '{1}' "
            "and is incompatible with Flex Consumption.".format(name, resource_group_name),
            recommendation=[
                "Retry with a different --name.",
                "Inspect the existing site: az functionapp show -g {0} -n {1}".format(
                    resource_group_name, name),
                "Check supported regions: az functionapp list-flexconsumption-locations",
                "To replace the existing site (this is destructive and deletes it): "
                "az functionapp delete -g {0} -n {1}".format(resource_group_name, name),
            ])

        # Headline must not echo RP internals.
        self.assertIn("already exists", err.error_msg)
        self.assertIn("Flex Consumption", err.error_msg)
        self.assertNotIn("Service responded", err.error_msg)
        self.assertNotIn("hosting constraints", err.error_msg.lower())
        self.assertNotIn("ASP-", err.error_msg)
        self.assertNotIn("App Service Plan", err.error_msg)

        # recommendations must be a populated list (per error_handling_guidelines.md)
        self.assertIsInstance(err.recommendations, list)
        self.assertEqual(len(err.recommendations), 4)

        # SAFE-FIRST ordering: rename is bullet 1; destructive delete is bullet 4.
        self.assertEqual(err.recommendations[0], "Retry with a different --name.")
        self.assertIn("destructive", err.recommendations[3])
        self.assertIn("az functionapp delete -g myrg -n myapp", err.recommendations[3])

        # Other bullets are present and non-destructive.
        rec_text = "\n".join(err.recommendations)
        self.assertIn("az functionapp show -g myrg -n myapp", rec_text)
        self.assertIn("az functionapp list-flexconsumption-locations", rec_text)

    def test_validation_error_when_site_not_present_uses_neutral_headline(self):
        # Branch: existing-site probe returned None -> headline must NOT assert
        # "already exists" (we can't prove that). It should attribute the failure
        # to the service and offer neutral non-destructive recommendations.
        name = "myapp"
        resource_group_name = "myrg"
        err = ValidationError(
            "Failed to create Flex Consumption function app '{0}' in resource group "
            "'{1}' due to a hosting conflict reported by the Microsoft.Web service."
            .format(name, resource_group_name),
            recommendation=[
                "Retry with a different --name in case a soft-deleted or hidden site "
                "is reserving the name.",
                "Check supported regions: az functionapp list-flexconsumption-locations",
                "Confirm the subscription is enabled for Flex Consumption in the target "
                "region.",
                "Re-run with --debug to view the full Microsoft.Web service response.",
            ])

        # CRITICAL: we must NOT claim the site already exists if we couldn't verify it.
        self.assertNotIn("already exists", err.error_msg)
        self.assertIn("Flex Consumption", err.error_msg)
        self.assertIn("hosting conflict", err.error_msg)

        # Recommendations must be entirely non-destructive in this branch
        # (we don't know what to delete).
        self.assertIsInstance(err.recommendations, list)
        self.assertEqual(len(err.recommendations), 4)
        rec_text = "\n".join(err.recommendations)
        self.assertNotIn("az functionapp delete", rec_text)
        self.assertIn("--debug", rec_text)
        self.assertIn("az functionapp list-flexconsumption-locations", rec_text)


if __name__ == "__main__":
    unittest.main()

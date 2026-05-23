# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Live-recordable scenario tests for ``az monitor sli``.

The ``Microsoft.Monitor`` SLI resource provider is tenant-scoped under a
``Microsoft.Management/serviceGroups`` parent. Azure CLI does not currently
expose a command for creating service groups, so the service group and the
referenced UAMI + AMW account must be pre-provisioned in a tenant where the
``2025-03-01-preview`` API is enabled.

When the cassette is absent or stale, re-record with::

    az login
    azdev test test_monitor_sli_crud --live

The cassette is recorded against the *currently active* subscription, so make
sure ``az account show`` points to a tenant where the SLI preview API is
enabled before re-recording.

Override any of the prerequisites with these environment variables:

  * ``AZURE_CLI_TEST_SLI_SERVICE_GROUP`` - name of an existing service group.
  * ``AZURE_CLI_TEST_SLI_UAMI_ID`` - ARM ID of a UAMI authorized to read from
    the AMW account below.
  * ``AZURE_CLI_TEST_SLI_UAMI_ID_2`` - ARM ID of a second UAMI used by the
    rotation test. Must have the same RBAC on the AMW as the primary UAMI.
  * ``AZURE_CLI_TEST_SLI_AMW_ID`` - ARM ID of the Azure Monitor (AMW) account
    used as both destination and signal source.
"""

import json
import os

from azure.cli.testsdk import ScenarioTest


_DEFAULT_SERVICE_GROUP = "arm-sdk-tests-sg"
# Resource IDs are built relative to the test's current subscription so the
# cassette (scrubbed to MOCKED_SUBSCRIPTION_ID) replays cleanly without the AAZ
# auxiliary-subscription lookup failing against the mocked profile.
_DEFAULT_UAMI_TEMPLATE = (
    "/subscriptions/{sub}/resourcegroups/mfrei/providers/"
    "Microsoft.ManagedIdentity/userAssignedIdentities/mfrei-test-user-managed-identity"
)
_DEFAULT_UAMI_2_TEMPLATE = (
    "/subscriptions/{sub}/resourcegroups/mfrei/providers/"
    "Microsoft.ManagedIdentity/userAssignedIdentities/mfrei-test-user-managed-identity-2"
)
_DEFAULT_AMW_TEMPLATE = (
    "/subscriptions/{sub}/resourceGroups/mfrei/providers/"
    "microsoft.monitor/accounts/streaming-3p-slo-am2cbn-eastus2euap-1"
)


def _build_signal_source(uami_id, amw_id):
    return {
        "filters": [
            {
                "dimensionName": "dimName1",
                "operator": "eq",
                "value": "GetContosoUsers",
                "samplingType": "Count",
            },
        ],
        "metricName": "mfreiTestMetric1",
        "metricNamespace": "mfreiTestNamespace",
        "signalSourceId": "A",
        "sourceAmwAccountManagedIdentity": uami_id,
        "sourceAmwAccountResourceId": amw_id,
        "spatialAggregation": {"dimensions": ["dimName1"], "type": "Count"},
        "temporalAggregation": {"type": "Max"},
    }


class TestMonitorSliScenarios(ScenarioTest):

    def _common_kwargs(self, sub_id, sli_name_prefix):
        return {
            "sg": os.environ.get("AZURE_CLI_TEST_SLI_SERVICE_GROUP", _DEFAULT_SERVICE_GROUP),
            "sli": self.create_random_name(sli_name_prefix, 20),
            "uami_id": os.environ.get(
                "AZURE_CLI_TEST_SLI_UAMI_ID", _DEFAULT_UAMI_TEMPLATE.format(sub=sub_id)
            ),
            "uami_id_2": os.environ.get(
                "AZURE_CLI_TEST_SLI_UAMI_ID_2", _DEFAULT_UAMI_2_TEMPLATE.format(sub=sub_id)
            ),
            "amw_id": os.environ.get(
                "AZURE_CLI_TEST_SLI_AMW_ID", _DEFAULT_AMW_TEMPLATE.format(sub=sub_id)
            ),
        }

    def test_monitor_sli_crud(self):
        sub_id = self.get_subscription_id()
        self.kwargs.update(self._common_kwargs(sub_id, "clisli"))

        good_signal_source = _build_signal_source(self.kwargs["uami_id"], self.kwargs["amw_id"])
        total_signal_source = dict(good_signal_source)
        self.kwargs.update({
            "baseline": json.dumps({
                "baseline": {
                    "evaluationCalculationType": "CalendarDays",
                    "evaluationPeriodDays": 30,
                    "value": 50,
                },
            }),
            "destination_amw_accounts": json.dumps([{
                "identity": self.kwargs["uami_id"],
                "resourceId": self.kwargs["amw_id"],
            }]),
            "sli_properties": json.dumps({
                "goodSignals": {"signalFormula": "A", "signalSources": [good_signal_source]},
                "totalSignals": {"signalFormula": "A", "signalSources": [total_signal_source]},
            }),
        })

        try:
            self.cmd(
                "monitor sli create --service-group-name {sg} --sli-name {sli} "
                "--category Latency --evaluation-type RequestBased "
                "--description 'CLI SLI scenario test' --enable-alert false "
                "--user-assigned {uami_id} "
                "--destination-amw-accounts '{destination_amw_accounts}' "
                "--baseline-properties '{baseline}' --sli-properties '{sli_properties}'",
                checks=[
                    self.check("name", "{sli}"),
                    self.check("properties.category", "Latency"),
                    self.check("properties.evaluationType", "RequestBased"),
                    self.check("properties.enableAlert", False),
                    self.check("properties.description", "CLI SLI scenario test"),
                ],
            )

            self.cmd(
                "monitor sli show --service-group-name {sg} --sli-name {sli}",
                checks=[
                    self.check("name", "{sli}"),
                    self.check("properties.description", "CLI SLI scenario test"),
                ],
            )

            self.cmd(
                "monitor sli list --service-group-name {sg}",
                checks=[self.exists("[?name=='{sli}']")],
            )

            self.cmd(
                "monitor sli update --service-group-name {sg} --sli-name {sli} "
                "--description 'CLI SLI scenario test updated' --enable-alert true",
                checks=[
                    self.check("name", "{sli}"),
                    self.check("properties.description", "CLI SLI scenario test updated"),
                    self.check("properties.enableAlert", True),
                ],
            )
        finally:
            self.cmd("monitor sli delete --service-group-name {sg} --sli-name {sli} --yes")

    def test_monitor_sli_uami_rotation(self):
        """Rotate source-AMW and destination-AMW UAMIs together in a single
        ``az monitor sli update`` call, exercising the three-place identity
        invariant documented in ``az monitor sli update --help``.

        Because the same UAMI is used for both source and destination in this
        fixture, a single rotation pass updates all three identity surfaces:

          1. ``identity.userAssignedIdentities`` (remove old, add new).
          2. ``properties.destinationAmwAccounts[0].identity``.
          3. ``properties.sliProperties.goodSignals.signalSources[0].sourceAmwAccountManagedIdentity``
             and the matching ``totalSignals`` entry (request-based SLI).
        """
        sub_id = self.get_subscription_id()
        self.kwargs.update(self._common_kwargs(sub_id, "clislirot"))

        good_signal_source = _build_signal_source(self.kwargs["uami_id"], self.kwargs["amw_id"])
        total_signal_source = dict(good_signal_source)
        self.kwargs.update({
            "baseline": json.dumps({
                "baseline": {
                    "evaluationCalculationType": "CalendarDays",
                    "evaluationPeriodDays": 30,
                    "value": 50,
                },
            }),
            "destination_amw_accounts": json.dumps([{
                "identity": self.kwargs["uami_id"],
                "resourceId": self.kwargs["amw_id"],
            }]),
            "sli_properties": json.dumps({
                "goodSignals": {"signalFormula": "A", "signalSources": [good_signal_source]},
                "totalSignals": {"signalFormula": "A", "signalSources": [total_signal_source]},
            }),
            # ARM IDs contain dots (Microsoft.ManagedIdentity, etc.), so they
            # cannot be addressed as path segments by --set/--remove. The
            # working idiom is to replace the entire userAssignedIdentities
            # map with a JSON value rooted at a dotless path.
            "user_assigned_identities_new": json.dumps({self.kwargs["uami_id_2"]: {}}),
        })

        try:
            self.cmd(
                "monitor sli create --service-group-name {sg} --sli-name {sli} "
                "--category Latency --evaluation-type RequestBased "
                "--description 'CLI SLI rotation test' --enable-alert false "
                "--user-assigned {uami_id} "
                "--destination-amw-accounts '{destination_amw_accounts}' "
                "--baseline-properties '{baseline}' --sli-properties '{sli_properties}'",
                checks=[
                    self.check("name", "{sli}"),
                    self.check("identity.type", "UserAssigned"),
                    self.check("properties.destinationAmwAccounts[0].identity", "{uami_id}"),
                    self.check(
                        "properties.sliProperties.goodSignals.signalSources[0].sourceAmwAccountManagedIdentity",
                        "{uami_id}",
                    ),
                    self.check(
                        "properties.sliProperties.totalSignals.signalSources[0].sourceAmwAccountManagedIdentity",
                        "{uami_id}",
                    ),
                    self.exists("identity.userAssignedIdentities.\"{uami_id}\""),
                ],
            )

            self.cmd(
                "monitor sli update --service-group-name {sg} --sli-name {sli} "
                "--set 'identity.userAssignedIdentities={user_assigned_identities_new}' "
                "--set 'properties.destinationAmwAccounts[0].identity={uami_id_2}' "
                "--set 'properties.sliProperties.goodSignals.signalSources[0].sourceAmwAccountManagedIdentity={uami_id_2}' "
                "--set 'properties.sliProperties.totalSignals.signalSources[0].sourceAmwAccountManagedIdentity={uami_id_2}'",
                checks=[
                    self.check("name", "{sli}"),
                    self.check("identity.type", "UserAssigned"),
                    self.check("length(identity.userAssignedIdentities)", 1),
                    self.check("properties.destinationAmwAccounts[0].identity", "{uami_id_2}"),
                    self.check(
                        "properties.sliProperties.goodSignals.signalSources[0].sourceAmwAccountManagedIdentity",
                        "{uami_id_2}",
                    ),
                    self.check(
                        "properties.sliProperties.totalSignals.signalSources[0].sourceAmwAccountManagedIdentity",
                        "{uami_id_2}",
                    ),
                    self.exists("identity.userAssignedIdentities.\"{uami_id_2}\""),
                    self.not_exists("identity.userAssignedIdentities.\"{uami_id}\""),
                ],
            )
        finally:
            self.cmd("monitor sli delete --service-group-name {sg} --sli-name {sli} --yes")


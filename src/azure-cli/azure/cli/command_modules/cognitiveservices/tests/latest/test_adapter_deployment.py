# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit and scenario tests for ``az cognitiveservices account adapter-deployment`` custom commands.

``CognitiveServicesAdapterDeploymentUnitTests`` uses mocks — no Azure resources required and
runs in every CI job. Covers the wire-payload shape (properties carrying
``sourceModelId`` and ``targetDeploymentName``, no SKU/capacity/tags) and the LRO
return-poller contract.

``CognitiveServicesAdapterDeploymentScenarioTests`` are recorded scenario tests following
the pattern from ``test_compute.py`` (PR #33759). Each recorded test provisions a fresh
Foundry-enabled Cognitive Services account per test via ``ResourceGroupPreparer`` + inline
``az cognitiveservices account create`` and tears it down at the end — no hardcoded persistent
resources, per ``doc/authoring_tests.md``.

The final lifecycle test (``test_adapter_deployment_create_show_list_delete``) is decorated
``@live_only`` because it requires a pre-provisioned base ``managed-compute-deployment`` and a
protected Foundry-fine-tuning LoRA output; neither can be created inline. Set these environment
variables before running or the test skips:

* ``CLITEST_ADAPTER_RESOURCE_GROUP`` — resource group of the pre-provisioned Foundry account
* ``CLITEST_ADAPTER_ACCOUNT`` — Foundry account name that hosts the base MCD
* ``CLITEST_ADAPTER_TARGET_DEPLOYMENT`` — name of an existing base MCD in that account
* ``CLITEST_ADAPTER_SOURCE_MODEL_ID`` — ``azureai://`` URI of a protected LoRA fine-tuning output

Recording flow (once the required API version is available in the recording subscription):

.. code-block:: text

    az login
    azdev test cognitiveservices.test_adapter_deployment --live
    # Recordings appear at tests/latest/recordings/*.yaml
    # Commit them alongside the test file.

Playback (the default when running via ``azdev test cognitiveservices``) does not require any
Azure access and is what CI uses.
"""

import os
import unittest
from unittest import mock

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests.decorators import live_only

from azure.cli.command_modules.cognitiveservices.custom import (
    adapter_deployment_create,
    adapter_deployment_delete,
    adapter_deployment_list,
    adapter_deployment_show,
)


class CognitiveServicesAdapterDeploymentUnitTests(unittest.TestCase):
    """Unit tests for the adapter-deployment command group custom functions."""

    RG = 'my-rg'
    ACCOUNT = 'my-account'
    ADAPTER_NAME = 'my-lora-adapter'
    SOURCE_MODEL_ID = (
        'azureai://accounts/my-account/projects/my-project/'
        'models/my-fine-tuned-lora/versions/1'
    )
    TARGET_DEPLOYMENT = 'gpt-oss-120b-gpu'

    # ---- create ----

    def test_create_builds_expected_payload_shape(self):
        """The wire payload must be ``{properties: {sourceModelId, targetDeploymentName}}``
        with NO sku/capacity/tags — adapter deployments own no physical compute per the spec."""
        client = mock.Mock()

        adapter_deployment_create(
            client, self.RG, self.ACCOUNT, self.ADAPTER_NAME,
            self.SOURCE_MODEL_ID, self.TARGET_DEPLOYMENT,
        )

        client.begin_create_or_update.assert_called_once()
        args, _kwargs = client.begin_create_or_update.call_args
        self.assertEqual(args[0], self.RG)
        self.assertEqual(args[1], self.ACCOUNT)
        self.assertEqual(args[2], self.ADAPTER_NAME)

        resource_dict = args[3].as_dict()
        self.assertIn('properties', resource_dict)
        self.assertEqual(resource_dict['properties']['sourceModelId'], self.SOURCE_MODEL_ID)
        self.assertEqual(resource_dict['properties']['targetDeploymentName'], self.TARGET_DEPLOYMENT)
        # Spec: adapter deployments own no SKU, capacity, or tags — verify none leak in.
        self.assertNotIn('sku', resource_dict)
        self.assertNotIn('tags', resource_dict)

    def test_create_omits_readonly_fields_from_payload(self):
        """Read-only response fields (activeTargetDeploymentName, provisioningState,
        lastOperation) must never appear on the outbound create payload."""
        client = mock.Mock()

        adapter_deployment_create(
            client, self.RG, self.ACCOUNT, self.ADAPTER_NAME,
            self.SOURCE_MODEL_ID, self.TARGET_DEPLOYMENT,
        )

        properties = client.begin_create_or_update.call_args.args[3].as_dict()['properties']
        self.assertNotIn('activeTargetDeploymentName', properties)
        self.assertNotIn('provisioningState', properties)
        self.assertNotIn('lastOperation', properties)

    def test_create_returns_poller_directly(self):
        """The custom function must return the LRO poller for the CLI framework to wait on;
        it must NOT call ``.result()`` itself."""
        client = mock.Mock()
        poller = client.begin_create_or_update.return_value

        returned = adapter_deployment_create(
            client, self.RG, self.ACCOUNT, self.ADAPTER_NAME,
            self.SOURCE_MODEL_ID, self.TARGET_DEPLOYMENT,
        )

        self.assertIs(returned, poller)
        poller.result.assert_not_called()

    # ---- show / list ----

    def test_show_passes_through_to_client(self):
        client = mock.Mock()
        result = adapter_deployment_show(client, self.RG, self.ACCOUNT, self.ADAPTER_NAME)
        client.get.assert_called_once_with(self.RG, self.ACCOUNT, self.ADAPTER_NAME)
        self.assertEqual(result, client.get.return_value)

    def test_list_passes_through_to_client(self):
        client = mock.Mock()
        result = adapter_deployment_list(client, self.RG, self.ACCOUNT)
        client.list.assert_called_once_with(self.RG, self.ACCOUNT)
        self.assertEqual(result, client.list.return_value)

    # ---- delete ----

    def test_delete_returns_poller_directly(self):
        """Same LRO contract as create: return the poller, let the CLI framework wait."""
        client = mock.Mock()
        poller = client.begin_delete.return_value

        returned = adapter_deployment_delete(
            client, self.RG, self.ACCOUNT, self.ADAPTER_NAME,
        )

        client.begin_delete.assert_called_once_with(self.RG, self.ACCOUNT, self.ADAPTER_NAME)
        self.assertIs(returned, poller)
        poller.result.assert_not_called()


@live_only()
class CognitiveServicesAdapterDeploymentScenarioTests(ScenarioTest):
    """Recorded scenario tests for the adapter-deployment command group.

    Each recorded test provisions a fresh Foundry-enabled Cognitive Services account via
    ``ResourceGroupPreparer`` + inline ``az cognitiveservices account create`` and tears it
    down at the end. Matches the pattern from ``test_compute.py`` (PR #33759) and complies
    with ``doc/authoring_tests.md``: no hardcoded persistent resources; all names via
    ``self.create_random_name`` so playback replaces them with stable monikers.
    """

    # Adapter deployments currently require the 2026-09-15-preview API version, which the
    # CognitiveServices RP only recognises in TIP regions until Fareed's TSP PR #45556
    # merges. Recording must be done from a subscription with TIP access; playback works
    # anywhere. westus2 was validated live via `az cognitiveservices account adapter-deployment list`.
    LOCATION = 'westus2'

    @ResourceGroupPreparer(name_prefix='clitest_cs_adapter', location=LOCATION)
    def test_adapter_deployment_list_empty(self, resource_group):
        """Fresh Foundry-enabled account -> ``adapter-deployment list`` returns an empty array."""
        self.kwargs.update({
            'sname': self.create_random_name(prefix='cog', length=12),
            'location': self.LOCATION,
        })

        self.cmd(
            'az cognitiveservices account create -n {sname} -g {rg} '
            '--kind AIServices --sku S0 -l {location} --yes '
            '--assign-identity --allow-project-management true',
            checks=[self.check('name', '{sname}')],
        )

        self.cmd(
            'az cognitiveservices account adapter-deployment list -n {sname} -g {rg}',
            checks=[self.check('length(@)', 0)],
        )

        self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')

    _LIVE_ENV_VARS = (
        'CLITEST_ADAPTER_RESOURCE_GROUP',
        'CLITEST_ADAPTER_ACCOUNT',
        'CLITEST_ADAPTER_TARGET_DEPLOYMENT',
        'CLITEST_ADAPTER_SOURCE_MODEL_ID',
    )

    @live_only()
    @unittest.skipUnless(
        all(os.environ.get(v) for v in _LIVE_ENV_VARS),
        f'Requires {", ".join(_LIVE_ENV_VARS)} pointing at a pre-provisioned '
        'Foundry account with a base managed-compute-deployment and a protected LoRA '
        'fine-tuning output. Not recorded because these values are site-specific.',
    )
    def test_adapter_deployment_create_show_list_delete(self):
        """Full lifecycle E2E: create -> show -> list-non-empty -> delete.

        Not recorded because the referenced ``sourceModelId`` and ``targetDeploymentName``
        are external, site-specific values that would either leak or fail playback matching.
        Run manually to validate the create path end-to-end against a real Foundry account.
        """
        self.kwargs.update({
            'rg': os.environ['CLITEST_ADAPTER_RESOURCE_GROUP'],
            'sname': os.environ['CLITEST_ADAPTER_ACCOUNT'],
            'aname': self.create_random_name(prefix='adp', length=12),
            'source_model_id': os.environ['CLITEST_ADAPTER_SOURCE_MODEL_ID'],
            'target_deployment': os.environ['CLITEST_ADAPTER_TARGET_DEPLOYMENT'],
        })

        self.cmd(
            'az cognitiveservices account adapter-deployment create -n {sname} -g {rg} '
            '--adapter-deployment-name {aname} '
            '--source-model-id {source_model_id} '
            '--target-deployment-name {target_deployment}',
            checks=[
                self.check('name', '{aname}'),
                self.check('properties.sourceModelId', '{source_model_id}'),
                self.check('properties.targetDeploymentName', '{target_deployment}'),
            ],
        )

        self.cmd(
            'az cognitiveservices account adapter-deployment show -n {sname} -g {rg} '
            '--adapter-deployment-name {aname}',
            checks=[
                self.check('name', '{aname}'),
                self.check('properties.provisioningState', 'Succeeded'),
            ],
        )

        self.cmd(
            'az cognitiveservices account adapter-deployment list -n {sname} -g {rg}',
            checks=[self.greater_than('length(@)', 0)],
        )

        self.cmd(
            'az cognitiveservices account adapter-deployment delete -n {sname} -g {rg} '
            '--adapter-deployment-name {aname}',
        )


if __name__ == '__main__':
    unittest.main()

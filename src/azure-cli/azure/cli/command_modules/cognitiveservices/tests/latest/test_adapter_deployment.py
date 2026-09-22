# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit and scenario tests for ``az cognitiveservices account adapter-deployment`` custom commands.

``CognitiveServicesAdapterDeploymentUnitTests`` uses mocks — no Azure resources required and
runs in every CI job. Covers the wire-payload shape (properties carrying
``sourceModelId`` and ``targetDeploymentName``, no SKU/capacity/tags) and the LRO
return-poller contract.

``CognitiveServicesAdapterDeploymentScenarioTests`` are ``@live_only()`` scenario tests — they
exercise the four commands end-to-end against a real Azure subscription. They
are skipped in normal CI runs and executed only when ``AZURE_TEST_RUN_LIVE=True``
is set. This matches the pattern used by ``test_compute.py`` and ``test_agent.py``
in this same module.

Live prerequisites (see class docstring for details):

* Logged in via ``az login`` with access to a Foundry / Cognitive Services account.
* An existing base ``managed-compute-deployment`` in that account to act as the
  parent (adapter deployments own no GPUs and must attach to an existing MCD).
* An immutable Foundry fine-tuning LoRA output registered as a Project Model
  version, whose URI is used as ``--source-model-id``.

To run the scenario tests locally:
    AZURE_TEST_RUN_LIVE=True azdev test cognitiveservices.test_adapter_deployment.CognitiveServicesAdapterDeploymentScenarioTests
"""

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
    """End-to-end scenario tests for the adapter-deployment command group.

    Decorated with ``@live_only()`` at the class level: skipped in normal CI runs
    and only executed when ``AZURE_TEST_RUN_LIVE=True``. Matches the live-only
    pattern in this module (see ``test_compute.py`` and ``test_agent.py``).

    Unlike the compute scenario tests (which bootstrap their own account and
    cluster inline), adapter deployments cannot be tested without pre-provisioned
    Foundry state:

    1. A Cognitive Services / Foundry account with a project.
    2. A base ``managed-compute-deployment`` in that account whose runtime supports
       LoRA hot-swap (e.g. vLLM). This is the ``--target-deployment-name``.
    3. A protected Foundry fine-tuning LoRA output registered as an immutable
       Project Model version. Its URI (``azureai://accounts/.../projects/.../
       models/.../versions/N``) is the ``--source-model-id``.

    TODO(saanika): fill in the four ``self.kwargs`` placeholders below once the
    service team provisions the shared test resources and grants access.
    """

    # TODO: replace these placeholders with the real Foundry test-resource details
    # (subscription/RG/account/project/base-MCD/LoRA-source-model) once the service
    # team confirms permissions and provides a sample body.
    TEST_ACCOUNT = 'REPLACE_WITH_FOUNDRY_ACCOUNT_NAME'
    TEST_TARGET_DEPLOYMENT = 'REPLACE_WITH_EXISTING_BASE_MCD_NAME'
    TEST_SOURCE_MODEL_ID = (
        'azureai://accounts/REPLACE_WITH_FOUNDRY_ACCOUNT_NAME/'
        'projects/REPLACE_WITH_PROJECT_NAME/'
        'models/REPLACE_WITH_LORA_MODEL_NAME/versions/1'
    )

    @ResourceGroupPreparer(name_prefix='clitest_cs_adapter', location='westus3')
    def test_cognitiveservices_adapter_deployment_create_show_list_delete(self, resource_group):
        """Full lifecycle: create adapter attached to an existing base MCD, show it,
        list, delete."""
        self.kwargs.update({
            'sname': self.TEST_ACCOUNT,
            'aname': self.create_random_name(prefix='adp', length=12),
            'source_model_id': self.TEST_SOURCE_MODEL_ID,
            'target_deployment': self.TEST_TARGET_DEPLOYMENT,
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

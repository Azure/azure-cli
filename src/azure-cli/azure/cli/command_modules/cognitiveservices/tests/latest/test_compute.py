# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit and scenario tests for `az cognitiveservices account compute` custom commands.

`CognitiveServicesComputeUnitTests` uses mocks — no Azure resources required and
runs in every CI job. Covers the wire-payload shape (including the location
dual-placement) and the `--no-wait` behaviour of `create`/`delete`.

`CognitiveServicesComputeScenarioTests` are `@live_only()` scenario tests — they
exercise the four commands end-to-end against a real Azure subscription. They
are skipped in normal CI runs and executed only when `AZURE_TEST_RUN_LIVE=True`
is set. This matches the pattern used by `test_agent.py` in this same module.

Live prerequisites:
  * Logged in via `az login` with access to a subscription that has
    Cognitive Services / AI-Foundry account permissions.
  * `Standard_D64_v3` (full-node) cluster-vCPU quota in the target region for
    the create/show/delete test.

To run the scenario tests locally:
  AZURE_TEST_RUN_LIVE=True azdev test cognitiveservices.test_compute.CognitiveServicesComputeScenarioTests
"""

import time
import unittest
from unittest import mock

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests.decorators import live_only
from azure.cli.testsdk.scenario_tests.decorators import live_only

from azure.cli.command_modules.cognitiveservices.custom import (
    compute_begin_create_or_update,
    compute_delete,
    compute_list,
    compute_show,
)


class CognitiveServicesComputeUnitTests(unittest.TestCase):
    """Unit tests for the compute command group custom functions."""

    RG = 'my-rg'
    ACCOUNT = 'my-account'
    COMPUTE_NAME = 'my-compute'
    LOCATION = 'westcentralus'
    POOL_NAME = 'my-pool'
    INSTANCE_TYPE = 'Standard_D64_v3'
    NODE_COUNT = 1

    # ---- create ----

    def test_create_builds_expected_payload_shape(self):
        """The wire payload must carry `location` on the outer Compute envelope AND
        inside the properties block (RP requires both). Pool goes inside properties.pools[]."""
        client = mock.Mock()

        compute_begin_create_or_update(
            client, self.RG, self.ACCOUNT, self.COMPUTE_NAME,
            self.LOCATION, self.POOL_NAME, self.INSTANCE_TYPE, self.NODE_COUNT,
            no_wait=True,
        )

        client.begin_create_or_update.assert_called_once()
        kwargs = client.begin_create_or_update.call_args.kwargs
        self.assertEqual(kwargs['resource_group_name'], self.RG)
        self.assertEqual(kwargs['account_name'], self.ACCOUNT)
        self.assertEqual(kwargs['compute_name'], self.COMPUTE_NAME)

        resource_dict = kwargs['resource'].as_dict()
        # location on outer Compute envelope
        self.assertEqual(resource_dict['location'], self.LOCATION)
        # location ALSO inside properties (RP requirement)
        self.assertEqual(resource_dict['properties']['location'], self.LOCATION)
        # cluster polymorphism discriminator auto-set by ClusterComputeProperties
        self.assertEqual(resource_dict['properties']['computeType'], 'Cluster')
        # single pool with the passed args
        pools = resource_dict['properties']['pools']
        self.assertEqual(len(pools), 1)
        self.assertEqual(pools[0]['name'], self.POOL_NAME)
        self.assertEqual(pools[0]['instanceType'], self.INSTANCE_TYPE)
        self.assertEqual(pools[0]['nodeCount'], self.NODE_COUNT)

    def test_create_passes_vm_priority_when_provided(self):
        client = mock.Mock()

        compute_begin_create_or_update(
            client, self.RG, self.ACCOUNT, self.COMPUTE_NAME,
            self.LOCATION, self.POOL_NAME, self.INSTANCE_TYPE, self.NODE_COUNT,
            vm_priority='LowPriority', no_wait=True,
        )

        resource_dict = client.begin_create_or_update.call_args.kwargs['resource'].as_dict()
        self.assertEqual(resource_dict['properties']['pools'][0]['vmPriority'], 'LowPriority')

    def test_create_omits_vm_priority_by_default(self):
        """When --vm-priority is omitted, the field should not be sent so the service
        applies its own default."""
        client = mock.Mock()

        compute_begin_create_or_update(
            client, self.RG, self.ACCOUNT, self.COMPUTE_NAME,
            self.LOCATION, self.POOL_NAME, self.INSTANCE_TYPE, self.NODE_COUNT,
            no_wait=True,
        )

        pool = client.begin_create_or_update.call_args.kwargs['resource'].as_dict()['properties']['pools'][0]
        self.assertNotIn('vmPriority', pool)

    def test_create_no_wait_returns_poller_without_result(self):
        client = mock.Mock()
        poller = client.begin_create_or_update.return_value

        returned = compute_begin_create_or_update(
            client, self.RG, self.ACCOUNT, self.COMPUTE_NAME,
            self.LOCATION, self.POOL_NAME, self.INSTANCE_TYPE, self.NODE_COUNT,
            no_wait=True,
        )

        self.assertIs(returned, poller)
        poller.result.assert_not_called()

    def test_create_waits_and_returns_result_by_default(self):
        client = mock.Mock()
        poller = client.begin_create_or_update.return_value

        returned = compute_begin_create_or_update(
            client, self.RG, self.ACCOUNT, self.COMPUTE_NAME,
            self.LOCATION, self.POOL_NAME, self.INSTANCE_TYPE, self.NODE_COUNT,
        )

        poller.result.assert_called_once()
        self.assertEqual(returned, poller.result.return_value)

    # ---- list / show ----

    def test_list_passes_through_to_client(self):
        client = mock.Mock()
        result = compute_list(client, self.RG, self.ACCOUNT)
        client.list.assert_called_once_with(self.RG, self.ACCOUNT)
        self.assertEqual(result, client.list.return_value)

    def test_show_passes_through_to_client(self):
        client = mock.Mock()
        result = compute_show(client, self.RG, self.ACCOUNT, self.COMPUTE_NAME)
        client.get.assert_called_once_with(self.RG, self.ACCOUNT, self.COMPUTE_NAME)
        self.assertEqual(result, client.get.return_value)

    # ---- delete ----

    def test_delete_no_wait_returns_poller_without_result(self):
        client = mock.Mock()
        poller = client.begin_delete.return_value

        returned = compute_delete(
            client, self.RG, self.ACCOUNT, self.COMPUTE_NAME, no_wait=True,
        )

        client.begin_delete.assert_called_once_with(self.RG, self.ACCOUNT, self.COMPUTE_NAME)
        self.assertIs(returned, poller)
        poller.result.assert_not_called()

    def test_delete_waits_and_returns_result_by_default(self):
        client = mock.Mock()
        poller = client.begin_delete.return_value

        returned = compute_delete(
            client, self.RG, self.ACCOUNT, self.COMPUTE_NAME,
        )

        poller.result.assert_called_once()
        self.assertEqual(returned, poller.result.return_value)


@live_only()
class CognitiveServicesComputeScenarioTests(ScenarioTest):
    """End-to-end scenario tests for the compute command group.

    Decorated with @live_only() at the class level: these tests are automatically
    skipped in normal CI runs and only execute when `AZURE_TEST_RUN_LIVE=True`.
    Matches the live-only pattern in this same module (see test_agent.py's
    `CognitiveServicesAgentTests`).

    When run live they create a fresh Cognitive Services account per test, exercise
    the compute commands, and tear the account down. No persistent resources.
    """

    @ResourceGroupPreparer(name_prefix='clitest_cs_compute', location='westcentralus')
    def test_cognitiveservices_compute_list_empty(self, resource_group):
        """Fresh account -> `compute list` returns an empty array."""
        self.kwargs.update({
            'sname': self.create_random_name(prefix='cog', length=12),
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'westcentralus',
        })

        self.cmd(
            'az cognitiveservices account create -n {sname} -g {rg} '
            '--kind {kind} --sku {sku} -l {location} --yes '
            '--assign-identity --allow-project-management true',
            checks=[self.check('name', '{sname}')],
        )

        self.cmd(
            'az cognitiveservices account compute list -n {sname} -g {rg}',
            checks=[self.check('length(@)', 0)],
        )

        self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')

    @ResourceGroupPreparer(name_prefix='clitest_cs_compute', location='westcentralus')
    def test_cognitiveservices_compute_create_show_delete(self, resource_group):
        """Full lifecycle: create a compute (async), show it, list, delete."""
        self.kwargs.update({
            'sname': self.create_random_name(prefix='cog', length=12),
            'cname': self.create_random_name(prefix='comp', length=12),
            'pname': self.create_random_name(prefix='pool', length=12),
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'westcentralus',
            'instance_type': 'Standard_D64_v3',
        })

        self.cmd(
            'az cognitiveservices account create -n {sname} -g {rg} '
            '--kind {kind} --sku {sku} -l {location} --yes '
            '--assign-identity --allow-project-management true',
            checks=[self.check('name', '{sname}')],
        )

        # Fire compute create with --no-wait so the test does not block for the
        # ~10 min provisioning window while recording. Poll via `show` below.
        self.cmd(
            'az cognitiveservices account compute create -n {sname} -g {rg} '
            '--compute-name {cname} --location {location} '
            '--pool-name {pname} --instance-type {instance_type} --node-count 1 '
            '--no-wait',
        )

        # RP is eventually-consistent on read after --no-wait create; give it a
        # moment before `show`/`list` so the compute is indexed.
        time.sleep(30)

        self.cmd(
            'az cognitiveservices account compute show -n {sname} -g {rg} '
            '--compute-name {cname}',
            checks=[self.check('name', '{cname}'), self.check('location', '{location}')],
        )

        self.cmd(
            'az cognitiveservices account compute list -n {sname} -g {rg}',
            checks=[self.check('length(@)', 1), self.check('[0].name', '{cname}')],
        )

        self.cmd(
            'az cognitiveservices account compute delete -n {sname} -g {rg} '
            '--compute-name {cname} --no-wait',
        )

        self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')


if __name__ == '__main__':
    unittest.main()

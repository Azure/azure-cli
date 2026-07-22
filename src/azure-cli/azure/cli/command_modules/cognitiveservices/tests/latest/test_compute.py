# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Unit tests for `az cognitiveservices account compute` custom commands.

These tests mock the SDK client and do not require Azure resources. They validate
that the CLI custom functions build the request payload in the shape the RP
expects and pass through the SDK client calls correctly.
"""

import unittest
from unittest import mock

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


if __name__ == '__main__':
    unittest.main()

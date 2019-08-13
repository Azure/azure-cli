# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ScenarioTest


class IoTPnPTest(ScenarioTest):

    def test_iot_pnp(self):
        self.kwargs.update({
            'endpoint': 'https://provider.azureiotrepository-test.com',
            'name': 'clitestrepo',
            'name2': 'clitestrepo-updated',
            'user_role': 'Reader',
            'user_role2': 'Admin'
        })

        # Test 'az iot pnp repository create'
        repo = self.cmd('iot pnp repository create -e "{endpoint}" -n {name}',
                        checks=[self.exists('id'),
                                self.exists('provisioningState'),
                                self.check('status', 'Provisioned')]).get_output_in_json()

        self.kwargs.update({
            'id': repo['id'],
            'provisioningState': repo['provisioningState']
        })

        # Test 'az iot pnp repository get-provision-status'
        self.cmd('iot pnp repository get-provision-status -e "{endpoint}" -r {id} -s {provisioningState}',
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('provisioningState', '{provisioningState}')])

        # Test 'az iot pnp repository update'
        self.cmd('iot pnp repository update -e "{endpoint}" -r {id} -n {name2}',
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.check('status', 'Provisioned')])

        # Test 'az iot pnp repository list'
        self.cmd('iot pnp repository list -e "{endpoint}"',
                 checks=[self.greater_than('length([*])', 0)])

        # Test 'az iot pnp repository show'
        self.cmd('iot pnp repository show -e "{endpoint}" -r {id}',
                 checks=[self.check('name', '{name2}'),
                         self.check('properties.kind', 'Repository'),
                         self.check('id', '{id}')])

        # Test 'az iot pnp key list'
        self.cmd('iot pnp key list -e "{endpoint}" -r {id}',
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot pnp key create'
        key = self.cmd('iot pnp key create -e "{endpoint}" -r {id} --role {user_role}',
                       checks=[self.check('repositoryId', '{id}'),
                               self.check('userRole', '{user_role}'),
                               self.exists('connectionString'),
                               self.exists('secret'),
                               self.exists('serviceEndpoint'),
                               self.exists('tenantId'),
                               self.exists('tenantName'),
                               self.exists('id')]).get_output_in_json()

        self.kwargs.update({
            'keyId': key['id']
        })

        # Test 'az iot pnp key list'
        self.cmd('iot pnp key list -e "{endpoint}" -r {id}',
                 checks=[self.check('length([*])', 1)])

        # Test 'az iot pnp key show'
        self.cmd('iot pnp key show -e "{endpoint}" -r {id} -k {keyId}',
                 checks=[self.check('repositoryId', repo['id']),
                         self.check('userRole', '{user_role}'),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot pnp key update'
        self.cmd('iot pnp key update -e "{endpoint}" -r {id} -k {keyId} --role {user_role2}',
                 checks=[self.check('repositoryId', '{id}'),
                         self.check('userRole', '{user_role2}'),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot pnp key delete'
        self.cmd('iot pnp key delete -e "{endpoint}" -r {id} -k {keyId}',
                 checks=self.is_empty())

        # Test 'az iot pnp key list'
        self.cmd('iot pnp key list -e "{endpoint}" -r {id}',
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot pnp repository delete'
        self.cmd('iot pnp repository delete -e "{endpoint}" -r {id}',
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('status', 'Deleted')])

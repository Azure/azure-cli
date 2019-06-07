# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ScenarioTest


class IoTDigitalTwinTest(ScenarioTest):

    def test_iot_digitialtwin(self):
        self.kwargs.update({
            'endpoint': 'https://provider.azureiotrepository-test.com',
            'name': 'clitestrepo',
            'name2': 'clitestrepo-updated',
            'user_role': 'Reader',
            'user_role2': 'Admin'
        })

        # Test 'az iot digitaltwin repository create'
        repo = self.cmd('iot digitaltwin repository create -e "{endpoint}" -n {name}',
                        checks=[self.exists('id'),
                                self.exists('provisioningState'),
                                self.check('status', 'Provisioned')]).get_output_in_json()

        # Test 'az iot digitaltwin repository get-provision-status'
        self.cmd('iot digitaltwin repository get-provision-status -e "{endpoint}" -r {} -s {}'.format(repo['id'], repo['provisioningState'], **self.kwargs),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('provisioningState', repo['provisioningState'])])

        # Test 'az iot digitaltwin repository update'
        self.cmd('iot digitaltwin repository update -e "{endpoint}" -r {} -n {name2}'.format(repo['id'], **self.kwargs),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.check('status', 'Provisioned')])

        # Test 'az iot digitaltwin repository list'
        self.cmd('iot digitaltwin repository list -e "{endpoint}"',
                 checks=[self.greater_than('length([*])', 0)])

        # Test 'az iot digitaltwin repository show'
        self.cmd('iot digitaltwin repository show -e "{endpoint}" -r {}'.format(repo['id'], **self.kwargs),
                 checks=[self.check('name', '{name2}'),
                         self.check('properties.kind', 'Repository'),
                         self.check('id', repo['id'])])

        # Test 'az iot digitaltwin key list'
        self.cmd('iot digitaltwin key list -e "{endpoint}" -r {}'.format(repo['id'], **self.kwargs),
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot digitaltwin key create'
        key = self.cmd('iot digitaltwin key create -e "{endpoint}" -r {} --role {user_role}'.format(repo['id'], **self.kwargs),
                       checks=[self.check('repositoryId', repo['id']),
                               self.check('userRole', '{user_role}'),
                               self.exists('connectionString'),
                               self.exists('secret'),
                               self.exists('serviceEndpoint'),
                               self.exists('tenantId'),
                               self.exists('tenantName'),
                               self.exists('id')]).get_output_in_json()

        # Test 'az iot digitaltwin key list'
        self.cmd('iot digitaltwin key list -e "{endpoint}" -r {}'.format(repo['id'], **self.kwargs),
                 checks=[self.check('length([*])', 1)])

        # Test 'az iot digitaltwin key show'
        self.cmd('iot digitaltwin key show -e "{endpoint}" -r {} -k {}'.format(repo['id'], key['id'], **self.kwargs),
                 checks=[self.check('repositoryId', repo['id']),
                         self.check('userRole', '{user_role}'),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot digitaltwin key update'
        self.cmd('iot digitaltwin key update -e "{endpoint}" -r {} -k {} --role {user_role2}'.format(repo['id'], key['id'], **self.kwargs),
                 checks=[self.check('repositoryId', repo['id']),
                         self.check('userRole', '{user_role2}'),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot digitaltwin key delete'
        self.cmd('iot digitaltwin key delete -e "{endpoint}" -r {} -k {}'.format(repo['id'], key['id'], **self.kwargs),
                 checks=self.is_empty())

        # Test 'az iot digitaltwin key list'
        self.cmd('iot digitaltwin key list -e "{endpoint}" -r {}'.format(repo['id'], **self.kwargs),
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot digitaltwin repository delete'
        self.cmd('iot digitaltwin repository delete -e "{endpoint}" -r {}'.format(repo['id'], **self.kwargs),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('status', 'Deleted')])

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ScenarioTest


class IoTPnPTest(ScenarioTest):

    def test_iot_pnp(self):
        self.kwargs.update({
                repo_endpoint = 'https://provider.azureiotrepository-test.com'
                repo_name = 'clitestrepo'
                repo_name2 = 'clitestrepo-updated'
                user_role = 'Reader'
                user_role2 = 'Admin'})

        # Test 'az iot digitaltwin repository create'
        repo = self.cmd('iot digitaltwin repository create -e "{repo_endpoint}" -n {repo_name}',
                        checks=[self.exists('id'),
                                self.exists('provisioningState'),
                                self.check('status', 'Provisioned')]).get_output_in_json()

        # Test 'az iot digitaltwin repository get-provision-status'
        self.cmd('iot digitaltwin repository get-provision-status -e "{repo_endpoint}" -r {0} -s {1}'.format(repo['id'], repo['provisioningState']),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('provisioningState', repo['provisioningState'])])

        # Test 'az iot digitaltwin repository update'
        self.cmd('iot digitaltwin repository update -e "{repo_endpoint}" -r {0} -n {repo_name2}'.format(repo['id']),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.check('status', 'Provisioned')])

        # Test 'az iot digitaltwin repository list'
        self.cmd('iot digitaltwin repository list -e "{repo_endpoint}"',
                 checks=[self.greater_than('length([*])', 0)])

        # Test 'az iot digitaltwin repository show'
        self.cmd('iot digitaltwin repository show -e "{repo_endpoint}" -r {0}'.format(repo['id']),
                 checks=[self.check('name', repo_name2),
                         self.check('properties.kind', 'Repository'),
                         self.check('id', repo['id'])])

        # Test 'az iot digitaltwin key list'
        self.cmd('iot digitaltwin key list -e "{repo_endpoint}" -r {0}'.format(repo['id']),
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot digitaltwin key create'
        key = self.cmd('iot digitaltwin key create -e "{repo_endpoint}" -r {0} --role {user_role}'.format(repo['id']),
                       checks=[self.check('repositoryId', repo['id']),
                               self.check('userRole', user_role),
                               self.exists('connectionString'),
                               self.exists('secret'),
                               self.exists('serviceEndpoint'),
                               self.exists('tenantId'),
                               self.exists('tenantName'),
                               self.exists('id')]).get_output_in_json()

        # Test 'az iot digitaltwin key list'
        self.cmd('iot digitaltwin key list -e "{repo_endpoint}" --id {0}'.format(repo['id']),
                 checks=[self.check('length([*])', 1)])

        # Test 'az iot digitaltwin key show'
        self.cmd('iot digitaltwin key show -e "{repo_endpoint}" --r {1} -k {1}'.format(repo['id'], key['id']),
                 checks=[self.check('repositoryId', repo['id']),
                         self.check('userRole', user_role),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot digitaltwin key update'
        self.cmd('iot digitaltwin key update -e "{repo_endpoint}" -r {0} -k {2} --role {user_role2}'.format(repo['id'], key['id']),
                 checks=[self.check('repositoryId', repo['id']),
                         self.check('userRole', user_role2),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot digitaltwin key delete'
        self.cmd('iot digitaltwin key delete -e "{repo_endpoint}" -r {0} -k {1}'.format(repo['id'], key['id']),
                 checks=self.is_empty())

        # Test 'az iot digitaltwin key list'
        self.cmd('iot digitaltwin key list -e "{repo_endpoint}" -r {0}'.format( repo['id']),
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot digitaltwin repository delete'
        self.cmd('iot digitaltwin repository delete -e "{repo_endpoint}" -r {1}'.format(repo['id']),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('status', 'Deleted')])

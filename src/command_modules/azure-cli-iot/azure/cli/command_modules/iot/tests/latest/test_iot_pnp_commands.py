# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ScenarioTest


class IoTPnPTest(ScenarioTest):

    def test_iot_pnp(self):
        repo_endpoint = 'https://provider.azureiotrepository-test.com'
        repo_name = 'clitestrepo'
        repo_name2 = 'clitestrepo-updated'
        user_role = 'Reader'
        user_role2 = 'Admin'

        # Test 'az iot pnp repository create'
        repo = self.cmd('iot pnp repository create -e "{0}" -n {1}'.format(repo_endpoint, repo_name),
                        checks=[self.exists('id'),
                                self.exists('provisioningState'),
                                self.check('status', 'Provisioned')]).get_output_in_json()

        # Test 'az iot pnp repository get-provision-status'
        self.cmd('iot pnp repository get-provision-status -e "{0}" --id {1} --tid {2}'.format(repo_endpoint, repo['id'], repo['provisioningState']),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('provisioningState', repo['provisioningState'])])

        # Test 'az iot pnp repository update'
        self.cmd('iot pnp repository update -e "{0}" --id {1} -n {2}'.format(repo_endpoint, repo['id'], repo_name2),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.check('status', 'Provisioned')])

        # Test 'az iot pnp repository list'
        self.cmd('iot pnp repository list -e "{0}"'.format(repo_endpoint),
                 checks=[self.greater_than('length([*])', 0)])

        # Test 'az iot pnp repository show'
        self.cmd('iot pnp repository show -e "{0}" --id {1}'.format(repo_endpoint, repo['id']),
                 checks=[self.check('name', repo_name2),
                         self.check('properties.kind', 'Repository'),
                         self.check('id', repo['id'])])

        # Test 'az iot pnp authkey list'
        self.cmd('iot pnp authkey list -e "{0}" --id {1}'.format(repo_endpoint, repo['id']),
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot authkey create'
        key = self.cmd('iot pnp authkey create -e "{0}" --id {1} --user-role {2}'.format(repo_endpoint, repo['id'], user_role),
                       checks=[self.check('repositoryId', repo['id']),
                               self.check('userRole', user_role),
                               self.exists('connectionString'),
                               self.exists('secret'),
                               self.exists('serviceEndpoint'),
                               self.exists('tenantId'),
                               self.exists('tenantName'),
                               self.exists('id')]).get_output_in_json()

        # Test 'az iot pnp authkey list'
        self.cmd('iot pnp authkey list -e "{0}" --id {1}'.format(repo_endpoint, repo['id']),
                 checks=[self.check('length([*])', 1)])

        # Test 'az iot pnp authkey show'
        self.cmd('iot pnp authkey show -e "{0}" --id {1} --kid {2}'.format(repo_endpoint, repo['id'], key['id']),
                 checks=[self.check('repositoryId', repo['id']),
                         self.check('userRole', user_role),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot pnp authkey update'
        self.cmd('iot pnp authkey update -e "{0}" --id {1} --kid {2} --user-role {3}'.format(repo_endpoint, repo['id'], key['id'], user_role2),
                 checks=[self.check('repositoryId', repo['id']),
                         self.check('userRole', user_role2),
                         self.exists('connectionString'),
                         self.exists('secret'),
                         self.exists('serviceEndpoint'),
                         self.exists('tenantId'),
                         self.exists('tenantName'),
                         self.exists('id')])

        # Test 'az iot pnp authkey remove'
        self.cmd('iot pnp authkey remove -e "{0}" --id {1} --kid {2}'.format(repo_endpoint, repo['id'], key['id']),
                 checks=self.is_empty())

        # Test 'az iot pnp authkey list'
        self.cmd('iot pnp authkey list -e "{0}" --id {1}'.format(repo_endpoint, repo['id']),
                 checks=[self.check('length([*])', 0)])

        # Test 'az iot pnp repository remove'
        self.cmd('iot pnp repository remove -e "{0}" --id {1}'.format(repo_endpoint, repo['id']),
                 checks=[self.exists('id'),
                         self.exists('provisioningState'),
                         self.exists('status'),
                         self.check('status', 'Deleted')])

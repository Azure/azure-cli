# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import uuid
import os

from knack.util import CLIError
from azure_functions_devops_build.exceptions import RoleAssignmentException
from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck

CURR_DIR = os.getcwd()
TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'sample_dotnet_function'))


class DevopsBuildCommandsTest(LiveScenarioTest):
    def setUp(self):
        super().setUp()
        # 1. Install devops extension 'az extension add --name azure-devops'
        # 2. To login with 'az login' and 'az devops login' to run the tests (devops extension required)
        # 3. Must be the organization owner and the subscription owner to run the test
        self.azure_devops_organization = "azure-functions-devops-build-test"
        self.os_type = "Windows"
        self.runtime = "dotnet"

        self.functionapp = self.create_random_name(prefix='functionapp-e2e', length=24)
        self.azure_devops_project = self.create_random_name(prefix='test-project-e2e', length=24)
        self.azure_devops_repository = self.create_random_name(prefix='test-repository-e2e', length=24)

        self.kwargs.update({
            'ot': self.os_type,
            'rt': self.runtime,
            'org': self.azure_devops_organization,
            'proj': self.azure_devops_project,
            'repo': self.azure_devops_repository,
            'fn': self.functionapp,
        })

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_command(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        # Test devops build command
        try:
            result = self.cmd('functionapp devops-build create --organization-name {org} --project-name {proj}'
                              ' --repository-name {repo} --functionapp-name {fn} --allow-force-push true'
                              ' --overwrite-yaml true').get_output_in_json()

            self.assertEqual(result['functionapp_name'], self.functionapp)
            self.assertEqual(result['functionapp_name'], self.functionapp)
            self.assertEqual(result['organization_name'], self.azure_devops_organization)
            self.assertEqual(result['project_name'], self.azure_devops_project)
            self.assertEqual(result['repository_name'], self.azure_devops_repository)
        except CLIError:
            raise unittest.SkipTest('You must be the owner of the subscription')
        finally:
            self._tearDownDevopsEnvironment()

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_runtime(self, resource_group, resource_group_location, storage_account_for_test):
        # Overwrite function runtime to use node
        self.kwargs.update({'rt': 'node'})
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        # Test devops build command (mismatched local_runtime:dotnet vs remote_runtime:node)
        try:
            self.cmd('functionapp devops-build create --organization-name {org} --project-name {proj} '
                     '--repository-name {repo} --functionapp-name {fn} --allow-force-push true '
                     '--overwrite-yaml true', expect_failure=True)
        finally:
            self._tearDownDevopsEnvironment()

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_functionapp(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        try:
            self.cmd('functionapp devops-build create --functionapp-name {mismatch}'.format(
                mismatch=self.create_random_name(prefix='mismatch_fn', length=24)
            ), expect_failure=True)
        finally:
            self._tearDownDevopsEnvironment()

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_organization(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        try:
            self.cmd('functionapp devops-build create --functionapp-name {fn} --organization-name {mismatch}'.format(
                fn=self.functionapp,
                mismatch=self.create_random_name(prefix='mismatch_org', length=24)
            ), expect_failure=True)
        finally:
            self._tearDownDevopsEnvironment()

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_project(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        try:
            self.cmd('functionapp devops-build create --functionapp-name {fn} --organization-name {org} '
                     '--project-name {mismatch}'.format(
                         fn=self.functionapp,
                         org=self.azure_devops_organization,
                         mismatch=self.create_random_name(prefix='mismatch_org', length=24)),
                     expect_failure=True
                     )
        finally:
            self._tearDownDevopsEnvironment()

    # Devops environment utilities
    def _setUpDevopsEnvironment(self, resource_group, resource_group_location, storage_account_for_test):
        self.kwargs.update({
            'rg': resource_group,
            'cpl': resource_group_location,
            'sa': storage_account_for_test,
        })

        # Create a new functionapp
        self.cmd('functionapp create --resource-group {rg} --storage-account {sa} '
                 '--os-type {ot} --runtime {rt} --name {fn} --consumption-plan-location {cpl}',
                 checks=[JMESPathCheck('name', self.functionapp), JMESPathCheck('resourceGroup', resource_group)]
                 )

        # Install azure devops extension
        self.cmd('extension add --name azure-devops')

        # Create a new project in Azure Devops
        result = self.cmd('devops project create --organization https://dev.azure.com/{org} --name {proj}', checks=[
            JMESPathCheck('name', self.azure_devops_project),
        ]).get_output_in_json()
        self.azure_devops_project_id = result['id']

        # Create a new repository in Azure Devops
        self.cmd('repos create --organization https://dev.azure.com/{org} --project {proj} --name {repo}', checks=[
            JMESPathCheck('name', self.azure_devops_repository),
        ])

        # Change directory to sample functionapp
        os.chdir(TEST_DIR)

    def _tearDownDevopsEnvironment(self):
        # Change directory back
        os.chdir(CURR_DIR)

        # Remove Azure Devops project
        self.cmd('devops project delete --organization https://dev.azure.com/{org} --id {id} --yes'.format(
            org=self.azure_devops_organization,
            id=self.azure_devops_project_id
        ))

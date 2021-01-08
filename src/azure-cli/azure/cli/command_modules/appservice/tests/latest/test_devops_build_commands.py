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
        # You must be the organization owner and the subscription owner to run the following tests
        # 1. Install devops extension 'az extension add --name azure-devops'
        # 2. Login with 'az login'
        # 3. Go to dev.azure.com apply for a personal access token, and login with 'az devops login'
        # 4. Change the self.azure_devops_organization to your Azure DevOps organization
        self.azure_devops_organization = "azureclitest"  # Put "<Your DevOps Organization>" to record live tests. Please change back to "azureclitest" as we have a routine live tests pipeline using this account.
        self.os_type = "Windows"
        self.runtime = "dotnet"

        self.functionapp = self.create_random_name(prefix='test-functionapp-', length=24)
        self.azure_devops_project = self.create_random_name(prefix='test-project-', length=24)
        self.azure_devops_repository = self.create_random_name(prefix='test-repository-', length=24)

        self.kwargs.update({
            'ot': self.os_type,
            'rt': self.runtime,
            'org': self.azure_devops_organization,
            'proj': self.azure_devops_project,
            'repo': self.azure_devops_repository,
            'fn': self.functionapp,
        })

    @unittest.skip("test has been failing continuously and functions team needs to fix this.")
    @ResourceGroupPreparer(random_name_length=24)
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_command(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        # Test devops build command
        try:
            result = self.cmd('functionapp devops-pipeline create --organization-name {org} --project-name {proj}'
                              ' --repository-name {repo} --functionapp-name {fn} --allow-force-push true'
                              ' --overwrite-yaml true').get_output_in_json()

            self.assertEqual(result['functionapp_name'], self.functionapp)
            self.assertEqual(result['organization_name'], self.azure_devops_organization)
            self.assertEqual(result['project_name'], self.azure_devops_project)
            self.assertEqual(result['repository_name'], self.azure_devops_repository)
        except CLIError:
            raise unittest.SkipTest('You must be the owner of the subscription')
        finally:
            self._tearDownDevopsEnvironment()

    @unittest.skip("test has been failing continuously and functions team needs to fix this.")
    @ResourceGroupPreparer(random_name_length=24)
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_runtime(self, resource_group, resource_group_location, storage_account_for_test):
        # Overwrite function runtime to use node
        self.kwargs.update({'rt': 'node'})
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        # Test devops build command (mismatched local_runtime:dotnet vs remote_runtime:node)
        try:
            self.cmd('functionapp devops-pipeline create --organization-name {org} --project-name {proj} '
                     '--repository-name {repo} --functionapp-name {fn} --allow-force-push true '
                     '--overwrite-yaml true', expect_failure=True)
        finally:
            self._tearDownDevopsEnvironment()

    @unittest.skip("test has been failing continuously and functions team needs to fix this.")
    @ResourceGroupPreparer(random_name_length=24)
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_functionapp(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        # Overwrite functionapp name to use a mismatched value
        self.kwargs.update({'fn': self.create_random_name(prefix='mismatch', length=24)})

        try:
            self.cmd('functionapp devops-pipeline create --organization-name {org} --project-name {proj} '
                     '--repository-name {repo} --functionapp-name {fn} --allow-force-push true '
                     '--overwrite-yaml true', expect_failure=True)
        finally:
            self.kwargs.update({'fn': self.functionapp})
            self._tearDownDevopsEnvironment()

    @unittest.skip("test has been failing continuously and functions team needs to fix this.")
    @ResourceGroupPreparer(random_name_length=24)
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_organization(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        # Overwrite organization name to use a mismatched value
        self.kwargs.update({'org': self.create_random_name(prefix='mismatch', length=24)})

        try:
            self.cmd('functionapp devops-pipeline create --organization-name {org} --project-name {proj} '
                     '--repository-name {repo} --functionapp-name {fn} --allow-force-push true '
                     '--overwrite-yaml true', expect_failure=True)
        finally:
            self.kwargs.update({'org': self.azure_devops_organization})
            self._tearDownDevopsEnvironment()

    @unittest.skip("test has been failing continuously and functions team needs to fix this.")
    @ResourceGroupPreparer(random_name_length=24)
    @StorageAccountPreparer(parameter_name='storage_account_for_test')
    def test_devops_build_mismatch_project(self, resource_group, resource_group_location, storage_account_for_test):
        self._setUpDevopsEnvironment(resource_group, resource_group_location, storage_account_for_test)

        # Overwrite project name to use a mismatched value
        self.kwargs.update({'proj': self.create_random_name(prefix='mismatch', length=24)})

        try:
            self.cmd('functionapp devops-pipeline create --organization-name {org} --project-name {proj} '
                     '--repository-name {repo} --functionapp-name {fn} --allow-force-push true '
                     '--overwrite-yaml true', expect_failure=True)
        finally:
            self.kwargs.update({'proj': self.azure_devops_project})
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
        import time
        # Change directory back
        os.chdir(CURR_DIR)

        # Remove Azure Devops project
        retry = 5
        for i in range(retry):
            try:
                self.cmd('devops project delete --organization https://dev.azure.com/{org} --id {id} --yes'.format(
                    org=self.azure_devops_organization,
                    id=self.azure_devops_project_id
                ))
                break
            except Exception as ex:
                if i == retry - 1:
                    raise ex
                time.sleep(120)

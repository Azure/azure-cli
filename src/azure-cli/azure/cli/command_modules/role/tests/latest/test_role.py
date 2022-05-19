# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI RBAC TEST DEFINITIONS
import json
import os
import sys
import tempfile
import time
import datetime
from unittest import mock
import unittest

from knack.util import CLIError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer
from azure.cli.command_modules.role.msgrpah import GraphError
from ..util import retry
from .test_graph import GraphScenarioTestBase


class RoleScenarioTestBase(GraphScenarioTestBase):

    def run_under_service_principal(self):
        return not self._get_signed_in_user()


class CreateForRbacScenarioTest(RoleScenarioTestBase):

    def test_create_for_rbac_password(self):
        self.kwargs['display_name'] = self.create_random_name('azure-cli-test-', 30)
        result = self.cmd('ad sp create-for-rbac --display-name {display_name}',
                          checks=self.check('displayName', '{display_name}')).get_output_in_json()
        self.kwargs['app_id'] = result['appId']
        self.cmd('role assignment list --assignee {app_id} --all', checks=self.check('length(@)', 0))

    def test_create_for_rbac_create_cert(self):

        self.kwargs['display_name'] = self.create_random_name('azure-cli-test-', 30)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            result = self.cmd('ad sp create-for-rbac -n {display_name} --create-cert',
                              checks=self.check('displayName', '{display_name}')).get_output_in_json()
            self.kwargs['app_id'] = result['appId']

            self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))

            # On Linux or MacOS, check the cert file is a regular file (S_IFREG 0100000) with permission 600
            # https://manpages.ubuntu.com/manpages/focal/man7/inode.7.html
            # Windows doesn't have the Linux permission concept.
            if sys.platform != 'win32':
                assert os.stat(result['fileWithCertAndPrivateKey']).st_mode == 0o100600

            os.remove(result['fileWithCertAndPrivateKey'])

            result = self.cmd('ad app credential reset --id {app_id} --create-cert').get_output_in_json()
            self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))

            if sys.platform != 'win32':
                assert os.stat(result['fileWithCertAndPrivateKey']).st_mode == 0o100600

            os.remove(result['fileWithCertAndPrivateKey'])

    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_new_cert')
    @KeyVaultPreparer(name_prefix='test-rbac-new-kv')
    def test_create_for_rbac_create_cert_keyvault(self, resource_group, key_vault):
        KeyVaultErrorException = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_vault_error#KeyVaultErrorException')
        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'display_name': resource_group,
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'cert': 'cert1',
            'kv': key_vault
        })

        time.sleep(5)  # to avoid 504(too many requests) on a newly created vault
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            try:
                result = self.cmd('ad sp create-for-rbac --create-cert '
                                  '--keyvault {kv} --cert {cert} -n {display_name}').get_output_in_json()
                self.kwargs['app_id'] = result['appId']
            except KeyVaultErrorException:
                if not self.is_live and not self.in_recording:
                    pass  # temporary workaround for keyvault challenge handling was ignored under playback
                else:
                    raise
            cer1 = self.cmd('keyvault certificate show --vault-name {kv} -n {cert}').get_output_in_json()['cer']
            self.cmd('ad app credential reset --id {app_id} --create-cert --keyvault {kv} --cert {cert}')
            cer2 = self.cmd('keyvault certificate show --vault-name {kv} -n {cert}').get_output_in_json()['cer']
            self.assertTrue(cer1 != cer2)

    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_existing_cert')
    @KeyVaultPreparer(name_prefix='test-rbac-exist-kv')
    def test_create_for_rbac_use_cert_keyvault(self, resource_group, key_vault):

        import time
        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'display_name': resource_group,
            'display_name2': resource_group + '2',
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'cert': 'cert1',
            'kv': key_vault
        })
        time.sleep(5)  # to avoid 504(too many requests) on a newly created vault

        # test with valid length cert
        try:
            self.kwargs['policy'] = self.cmd('keyvault certificate get-default-policy').get_output_in_json()
            self.cmd('keyvault certificate create --vault-name {kv} -n {cert} -p "{policy}" --validity 24')
            with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
                result = self.cmd('ad sp create-for-rbac -n {display_name} --keyvault {kv} '
                                  '--cert {cert}').get_output_in_json()
                self.kwargs['app_id'] = result['appId']
            self.cmd('ad app credential reset --id {app_id} --keyvault {kv} --cert {cert}')
        finally:
            try:
                self.cmd('ad app delete --id {app_id}')
            except:
                # Mute the exception, otherwise the exception thrown in the `try` clause will be hidden
                pass

        # test with cert that has too short a validity
        try:
            self.cmd('keyvault certificate create --vault-name {kv} -n {cert} -p "{policy}" --validity 6')
            with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
                result = self.cmd('ad sp create-for-rbac --keyvault {kv} '
                                  '--cert {cert} -n {display_name2}').get_output_in_json()
                self.kwargs['app_id2'] = result['appId']
            self.cmd('ad app credential reset --id {app_id2} --keyvault {kv} --cert {cert}')
        finally:
            try:
                self.cmd('ad app delete --id {app_id2}')
            except:
                pass

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_sp_create_for_rbac')
    def test_create_for_rbac_with_password_with_assignment(self, resource_group):

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'sub': subscription_id,
            'scope': f'/subscriptions/{subscription_id}/resourceGroups/{resource_group}',
            'role': 'Reader',
            'display_name': resource_group
        })

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            result = self.cmd('ad sp create-for-rbac -n {display_name} --scopes {scope} --role {role}',
                              checks=self.check('displayName', '{display_name}')).get_output_in_json()
            self.kwargs['app_id'] = result['appId']
            self.cmd('role assignment list --assignee {app_id} --resource-group {rg}',
                     checks=[
                         self.check("length([])", 1),
                         self.check("[0].roleDefinitionName", '{role}'),
                         self.check("[0].scope", '{scope}')
                     ])
            self.cmd('role assignment delete --assignee {app_id} -g {rg}',
                     checks=self.is_empty())

    def test_create_for_rbac_argument_error(self):
        self.kwargs.update({
            'scope': '/subscriptions/00000000-0000-0000-0000-000000000000',
            'role': 'Reader',
            'display_name': self.create_random_name('azure-cli-test-', 30)
        })

        # No role assignment argument
        # Without this line, no recording YAML will be generated. Playing back this test will make it live and fail
        # in CI because there is no logged in account.
        self.kwargs['app_id'] = self.cmd(
            'ad sp create-for-rbac --display-name {display_name}').get_output_in_json()['appId']

        from azure.cli.core.azclierror import ArgumentUsageError

        # Missing --role
        with self.assertRaisesRegex(ArgumentUsageError, 'both'):
            self.cmd('ad sp create-for-rbac --scopes {scope}')

        # Missing --scopes
        with self.assertRaisesRegex(ArgumentUsageError, 'both'):
            self.cmd('ad sp create-for-rbac --role {role}')


class RoleCreateScenarioTest(RoleScenarioTestBase):

    @AllowLargeResponse()
    def test_role_create_scenario(self):
        subscription_id = self.get_subscription_id()
        role_name = self.create_random_name('cli-test-role', 20)
        template = {
            "Name": role_name,
            "Description": "Can monitor compute, network and storage, and restart virtual machines",
            "Actions": ["Microsoft.Compute/*/read",
                        "Microsoft.Compute/virtualMachines/start/action",
                        "Microsoft.Compute/virtualMachines/restart/action",
                        "Microsoft.Network/*/read",
                        "Microsoft.Storage/*/read",
                        "Microsoft.Authorization/*/read",
                        "Microsoft.Resources/subscriptions/resourceGroups/read",
                        "Microsoft.Resources/subscriptions/resourceGroups/resources/read",
                        "Microsoft.Insights/alertRules/*"],
            "DataActions": [
                "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/*"
            ],
            "NotDataActions": [
                "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write"
            ],
            "AssignableScopes": ["/subscriptions/{}".format(subscription_id)]
        }
        _, temp_file = tempfile.mkstemp()
        with open(temp_file, 'w') as f:
            json.dump(template, f)

        self.kwargs.update({
            'sub': subscription_id,
            'role': role_name,
            'template': temp_file.replace('\\', '\\\\')
        })

        # a few 'sleep' here to handle server replicate latency. It is no-op under playback
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role definition create --role-definition {template}', checks=[
                self.check('permissions[0].dataActions[0]', 'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/*'),
                self.check('permissions[0].notDataActions[0]', 'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write'),
            ])

            role = retry(lambda: self.cmd('role definition list -n {role}',
                                          checks=self.check('[0].roleName', '{role}'))).get_output_in_json()

            # verify we can update
            role[0]['permissions'][0]['actions'].append('Microsoft.Support/*')
            with open(temp_file, 'w') as f:
                json.dump(role[0], f)

            retry(lambda: self.cmd('role definition update --role-definition {template}',
                                   checks=self.check('permissions[0].actions[-1]', 'Microsoft.Support/*')))
            retry(lambda: self.cmd('role definition delete -n {role}', checks=self.is_empty()))
            retry(lambda: self.cmd('role definition list -n {role}', checks=self.is_empty()))


class RoleAssignmentScenarioTest(RoleScenarioTestBase):

    @ResourceGroupPreparer(name_prefix='cli_role_assign')
    @AllowLargeResponse()
    def test_role_assignment_e2e(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            user = self.create_random_name('testuser', 15)
            self.kwargs.update({
                'upn': user + '@azuresdkteam.onmicrosoft.com',
                'nsg': 'nsg1'
            })

            result = self.cmd('ad user create --display-name tester123 --password Test123456789'
                              ' --user-principal-name {upn}').get_output_in_json()
            self.kwargs.update({
                'user_id': result['id']})
            time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

            group = self.create_random_name('testgroup', 15)
            self.kwargs.update({
                'group': group})

            group_result = self.cmd(
                'ad group create --display-name group123 --mail-nickname {group}').get_output_in_json()
            self.kwargs.update({
                'group_id': group_result['id']})
            self.cmd(
                'ad group member add --group {group_id} --member-id {user_id}')

            try:
                self.cmd('network nsg create -n {nsg} -g {rg}')
                result = self.cmd('network nsg show -n {nsg} -g {rg}').get_output_in_json()
                self.kwargs['nsg_id'] = result['id']

                # test role assignments on a resource group
                self.cmd('role assignment create --assignee {upn} --role contributor -g {rg}')
                # verify role assignment create is idempotent
                self.cmd('role assignment create --assignee {upn} --role contributor -g {rg}',
                         self.check("principalName", self.kwargs["upn"]))

                self.cmd('role assignment list -g {rg}', checks=self.check("length([])", 1))
                self.cmd('role assignment list --assignee {upn} --role contributor -g {rg}', checks=[
                    self.check("length([])", 1),
                    self.check("[0].principalName", self.kwargs["upn"])
                ])

                self.cmd('role assignment create --assignee {group_id} --role contributor -g {rg}')

                # test include-groups
                self.cmd('role assignment list --assignee {upn} --all --include-groups', checks=[
                    self.check("length([])", 2)
                ])

                # test couple of more general filters
                result = self.cmd('role assignment list -g {rg} --include-inherited').get_output_in_json()
                self.assertTrue(len(result) >= 1)

                result = self.cmd('role assignment list --all').get_output_in_json()
                self.assertTrue(len(result) >= 1)

                self.cmd('role assignment delete --assignee {group_id} --role contributor -g {rg}')
                self.cmd('role assignment delete --assignee {upn} --role contributor -g {rg}')
                self.cmd('role assignment list -g {rg}',
                         checks=self.is_empty())

                # test role assignments on a resource
                self.cmd('role assignment create --assignee {upn} --role contributor --scope {nsg_id}')
                self.cmd('role assignment list --assignee {upn} --role contributor --scope {nsg_id}',
                         checks=self.check("length([])", 1))
                self.cmd('role assignment delete --assignee {upn} --role contributor --scope {nsg_id}')
                self.cmd('role assignment list --scope {nsg_id}',
                         checks=self.is_empty())

                # test role assignment on subscription level
                self.cmd('role assignment create --assignee {upn} --role reader')
                self.cmd('role assignment list --assignee {upn} --role reader',
                         checks=self.check("length([])", 1))
                self.cmd('role assignment list --assignee {upn}',
                         checks=self.check("length([])", 1))
                self.cmd('role assignment delete --assignee {upn} --role reader')

                # test role assignment on empty scope
                with self.assertRaisesRegex(CLIError, "Cannot find user or service principal in graph database for 'fake'."):
                    self.cmd('role assignment create --assignee fake --role contributor')
            finally:
                self.cmd('ad user delete --id {upn}')

    @ResourceGroupPreparer(name_prefix='cli_role_assign')
    @AllowLargeResponse()
    def test_role_assignment_create_using_principal_type(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.kwargs['rg'] = resource_group

        def _test_role_assignment(assignee_object_id, assignee_principal_type=None, graph_call_fails=False):
            self.kwargs['object_id'] = assignee_object_id
            self.kwargs['assignee_principal_type'] = assignee_principal_type
            # test role assignment on subscription level

            if assignee_principal_type:
                # No graph call
                with mock.patch('azure.cli.command_modules.role.msgrpah._graph_client.GraphClient.directory_object_get_by_ids') \
                        as directory_object_get_by_ids_mock:
                    self.cmd(
                        'role assignment create --assignee-object-id {object_id} '
                        '--assignee-principal-type {assignee_principal_type} --role Reader -g {rg}')
                    # Verify no graph call
                    directory_object_get_by_ids_mock.assert_not_called()
            else:
                # Make graph call to resolve assignee_principal_type
                if graph_call_fails:
                    import requests
                    mock_response = requests.Response()
                    mock_response.status_code = 403
                    mock_response.reason = 'Forbidden for url: https://...'
                    with mock.patch(
                            'azure.cli.command_modules.role.msgrpah._graph_client.GraphClient.directory_object_get_by_ids',
                            side_effect=GraphError('403', mock_response)):
                        self.cmd('role assignment create --assignee-object-id {object_id} --role Reader -g {rg}')
                else:
                    self.cmd('role assignment create --assignee-object-id {object_id} --role Reader -g {rg}')

            self.cmd('role assignment list -g {rg}', checks=self.check("length([])", 1))
            self.cmd('role assignment delete -g {rg}')
            self.cmd('role assignment list -g {rg}', checks=self.check("length([])", 0))

        def _test_role_assignment_graph_call(assignee_object_id, assignee_principal_type):
            # test role assignment with principal type which won't trigger graph call
            _test_role_assignment(assignee_object_id, assignee_principal_type)

            # test role assignment without principal type which will trigger graph call to complete principal type
            _test_role_assignment(assignee_object_id)

            # test role assignment without principal type and graph call fail
            _test_role_assignment(assignee_object_id, graph_call_fails=True)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            # User
            user = self.create_random_name('testuser', 15)
            self.kwargs['upn'] = user + '@azuresdkteam.onmicrosoft.com'

            result = self.cmd('ad user create --display-name tester123 --password Test123456789 '
                              '--user-principal-name {upn}').get_output_in_json()
            time.sleep(30)
            try:
                _test_role_assignment_graph_call(result['id'], 'User')
            finally:
                try:
                    self.cmd('ad user delete --id {upn}')
                except:
                    pass

            # Group
            self.kwargs['group_name'] = self.create_random_name('testgroup', 15)
            result = self.cmd(
                'ad group create --display-name {group_name} --mail-nickname {group_name}').get_output_in_json()
            time.sleep(30)
            try:
                _test_role_assignment_graph_call(result['id'], 'Group')
            finally:
                try:
                    self.cmd('ad group delete --group {object_id}')
                except:
                    pass

            # Service Principal
            self.kwargs['sp_name'] = self.create_random_name('sp', 15)
            result = self.cmd('ad sp create-for-rbac --name {sp_name}').get_output_in_json()
            self.kwargs['app_id'] = result['appId']
            result = self.cmd('ad sp show --id {app_id}').get_output_in_json()
            time.sleep(30)
            try:
                _test_role_assignment_graph_call(result['id'], 'ServicePrincipal')
            finally:
                try:
                    self.cmd('ad sp delete --id {object_id}')
                except:
                    pass

    @ResourceGroupPreparer(name_prefix='cli_role_assign')
    @AllowLargeResponse()
    def test_role_assignment_create_update(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            user = self.create_random_name('testuser', 15)
            self.kwargs.update({
                'upn': user + '@azuresdkteam.onmicrosoft.com',
                'rg': resource_group,
                'description': "Role assignment foo to check on bar",
                'condition': "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:Name] stringEquals 'foo'",
                'condition_version': "2.0"
            })

            result = self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}').get_output_in_json()
            self.kwargs['object_id'] = result['id']
            try:
                # Test create role assignment with description, condition and condition_version
                self.cmd('role assignment create --assignee-object-id {object_id} --assignee-principal-type User --role reader -g {rg} '
                         # Include double quotes to tell shlex to treat arguments as a whole
                         '--description "{description}" '
                         '--condition "{condition}" --condition-version {condition_version}',
                         checks=[
                             self.check("description", "{description}"),
                             self.check("condition", "{condition}"),
                             self.check("conditionVersion", "{condition_version}")
                         ])
                self.cmd('role assignment delete -g {rg}')

                # Test create role assignment with description, condition. condition_version defaults to 2.0
                self.cmd('role assignment create --assignee-object-id {object_id} --assignee-principal-type User --role reader -g {rg} '
                         '--description "{description}" '
                         '--condition "{condition}"',
                         checks=[
                             self.check("description", "{description}"),
                             self.check("condition", "{condition}"),
                             self.check("conditionVersion", "2.0")
                         ])
                self.cmd('role assignment delete -g {rg}')

                # Test error is raised if condition-version is set but condition is not
                with self.assertRaisesRegex(CLIError, "--condition must be set"):
                    self.cmd('role assignment create --assignee-object-id {object_id} --assignee-principal-type User --role reader -g {rg} '
                             '--condition-version {condition_version}')

                # Update
                output = self.cmd('role assignment create --assignee-object-id {object_id} --assignee-principal-type User --role reader -g {rg} '
                                  '--description "{description}" '
                                  '--condition "{condition}" --condition-version {condition_version}').get_output_in_json()

                updated_description = "Some updated description."
                output['description'] = updated_description
                import shlex
                from ..util import escape_apply_kwargs
                # The json contains both single (in description) and double quotes, use shlex to quote and escape it,
                # then escape it again before being passed to self.cmd
                output_json = escape_apply_kwargs(shlex.quote(json.dumps(output)))

                self.cmd("role assignment update --role-assignment {}".format(output_json),
                         checks=[self.check("description", updated_description)])

                with self.assertRaisesRegex(CLIError, "cannot be downgraded"):
                    output['conditionVersion'] = '1.0'
                    output_json = escape_apply_kwargs(shlex.quote(json.dumps(output)))
                    self.cmd("role assignment update --role-assignment {}".format(output_json))

                self.cmd('role assignment delete -g {rg}')

            finally:
                self.cmd('ad user delete --id {upn}')

    @ResourceGroupPreparer(name_prefix='cli_role_assign')
    @AllowLargeResponse()
    def test_role_assignment_handle_conflicted_assignments(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            user = self.create_random_name('testuser', 15)
            self.kwargs.update({
                'upn': user + '@azuresdkteam.onmicrosoft.com',
                'nsg': 'nsg1'
            })

            self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
            time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

            base_dir = os.path.abspath(os.curdir)

            try:
                temp_dir = os.path.realpath(self.create_temp_dir())
                os.chdir(temp_dir)
                self.cmd('configure --default group={rg} --scope local')
                local_defaults_config = self.cmd('configure --list-defaults --scope local').get_output_in_json()

                self.assertGreaterEqual(len(local_defaults_config), 1)
                actual = set([(x['name'], x['source'], x['value']) for x in local_defaults_config if x['name'] == 'group'])
                expected = set([('group', os.path.join(temp_dir, '.azure', 'config'), self.kwargs['rg'])])
                self.assertEqual(actual, expected)

                # test role assignments on a resource group
                rg_id = self.cmd('group show -n {rg}').get_output_in_json()['id']
                self.cmd('role assignment create --assignee {upn} --role reader --scope ' + rg_id)
                self.cmd('role assignment list --assignee {upn} --role reader --scope ' + rg_id, checks=self.check('length([])', 1))
                self.cmd('role assignment delete --assignee {upn} --role reader --scope ' + rg_id)
                self.cmd('role assignment list --assignee {upn} --role reader --scope ' + rg_id, checks=self.check('length([])', 0))
            finally:
                self.cmd('configure --default group="" --scope local')
                os.chdir(base_dir)
                self.cmd('ad user delete --id {upn}')

    def test_role_assignment_empty_string_args(self):
        expected_msg = "{} can't be an empty string"
        with self.assertRaisesRegex(CLIError, expected_msg.format("--assignee")):
            self.cmd('role assignment delete --assignee ""')
        with self.assertRaisesRegex(CLIError, expected_msg.format("--scope")):
            self.cmd('role assignment delete --scope ""')
        with self.assertRaisesRegex(CLIError, expected_msg.format("--role")):
            self.cmd('role assignment delete --role ""')
        with self.assertRaisesRegex(CLIError, expected_msg.format("--resource-group")):
            self.cmd('role assignment delete --resource-group ""')

    @unittest.skip("Known service random 403 issue")
    @ResourceGroupPreparer(name_prefix='cli_role_assign')
    @AllowLargeResponse()
    def test_role_assignment_mgmt_grp(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            user = self.create_random_name('testuser', 15)
            mgmt_grp = self.create_random_name('mgmt_grp', 15)
            self.kwargs.update({
                'upn': user + '@azuresdkteam.onmicrosoft.com',
                'mgmt_grp': mgmt_grp
            })

            self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
            time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

            mgmt_grp_created = False

            try:
                mgmt_grp_id = self.cmd('account management-group create -n {mgmt_grp}').get_output_in_json()['id']
                self.kwargs['scope'] = mgmt_grp_id
                mgmt_grp_created = True
                time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change
                # test role assignments on a resource group
                self.cmd('role assignment create --assignee {upn} --role reader --scope {scope}',
                         checks=self.check('scope', self.kwargs['scope']))

                self.cmd('role assignment list --assignee {upn} --role reader --scope {scope}', checks=[
                    self.check('length([])', 1),
                    self.check('[0].scope', self.kwargs['scope'])
                ])

                self.cmd('role assignment delete --assignee {upn} --role reader --scope {scope}')

                self.cmd('role assignment list --assignee {upn} --role reader --scope {scope}',
                         checks=self.check('length([])', 0))
            finally:
                if mgmt_grp_created:
                    self.cmd('account management-group delete -n {mgmt_grp}')
                self.cmd('ad user delete --id {upn}')

    @ResourceGroupPreparer(name_prefix='cli_role_audit')
    @AllowLargeResponse()
    def test_role_assignment_audits(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            user = self.create_random_name('testuser', 15)
            self.kwargs.update({
                'upn': user + '@azuresdkteam.onmicrosoft.com',
            })

            self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
            time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

            try:
                self.cmd('role assignment create --assignee {upn} --role contributor -g {rg}')

                if self.is_live or self.in_recording:
                    now = datetime.datetime.utcnow()
                    start = now - datetime.timedelta(minutes=1)
                    end = now + datetime.timedelta(minutes=1)
                    start_time = '{}-{}-{}T{}:{}:{}Z'.format(start.year, start.month, start.day, start.hour,
                                                             start.minute, start.second)
                    end_time = '{}-{}-{}T{}:{}:{}Z'.format(end.year, end.month, end.day, end.hour,
                                                           end.minute, end.second)

                else:
                    # figure out the right time stamps from the recording file
                    r = next(r for r in self.cassette.requests if r.method == 'GET' and 'providers/Microsoft.Insights/eventtypes/management/' in r.uri)
                    from urllib.parse import parse_qs, urlparse
                    query_parts = parse_qs(urlparse(r.uri).query)['$filter'][0].split()
                    start_index, end_index = [i + 2 for (i, j) in enumerate(query_parts) if j == 'eventTimestamp']
                    start_time, end_time = query_parts[start_index], query_parts[end_index]

                # Change log is not immediately available. Retry until success.
                def check_changelogs():
                    result = self.cmd('role assignment list-changelogs --start-time {} --end-time {}'.format(
                                      start_time, end_time)).get_output_in_json()
                    self.assertTrue([x for x in result if (resource_group in x['scope'] and
                                                           x['principalName'] == self.kwargs['upn'])])
                retry(check_changelogs, sleep_duration=60, max_retry=15)
            finally:
                self.cmd('ad user delete --id {upn}')


class RoleAssignmentListScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_assignments_for_coadmins')
    @AllowLargeResponse()
    def test_assignments_for_co_admins(self, resource_group):

        result = self.cmd('role assignment list --include-classic-administrator').get_output_in_json()
        self.assertTrue([x for x in result if x['roleDefinitionName'] in ['CoAdministrator', 'AccountAdministrator']])
        self.cmd('role assignment list -g {}'.format(resource_group), checks=[
            self.check("length([])", 0)
        ])
        result = self.cmd('role assignment list -g {} --include-classic-administrator'.format(resource_group)).get_output_in_json()
        self.assertTrue([x for x in result if x['roleDefinitionName'] in ['CoAdministrator', 'AccountAdministrator']])


if __name__ == '__main__':
    unittest.main()

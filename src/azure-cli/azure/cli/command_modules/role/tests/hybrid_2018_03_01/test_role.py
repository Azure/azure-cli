# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI RBAC TEST DEFINITIONS
import json
import os
import tempfile
import time
import datetime
from unittest import mock
import unittest

from azure.cli.testsdk.scenario_tests import AllowLargeResponse, record_only
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer
from ..util import retry


class RoleScenarioTest(ScenarioTest):

    def run_under_service_principal(self):
        account_info = self.cmd('account show').get_output_in_json()
        return account_info['user']['type'] == 'servicePrincipal'


class RbacSPSecretScenarioTest(RoleScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_minimal')
    def test_create_for_rbac_with_secret_no_assignment(self, resource_group):

        self.kwargs['display_name'] = resource_group
        try:
            result = self.cmd('ad sp create-for-rbac -n {display_name} --skip-assignment',
                              checks=self.check('displayName', '{display_name}')).get_output_in_json()
            self.kwargs['app_id'] = result['appId']
        finally:
            self.cmd('ad app delete --id {app_id}')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_password')
    def test_create_for_rbac_with_secret_with_assignment(self, resource_group):

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'display_name': resource_group
        })

        try:
            with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
                result = self.cmd('ad sp create-for-rbac -n {display_name} --scopes {scope} {scope}/resourceGroups/{rg}',
                                  checks=self.check('displayName', '{display_name}')).get_output_in_json()
                self.kwargs['app_id'] = result['appId']
                self.cmd('role assignment list --assignee {app_id} --scope {scope}',
                         checks=self.check("length([])", 1))
                self.cmd('role assignment list --assignee {app_id} -g {rg}',
                         checks=self.check("length([])", 1))
                self.cmd('role assignment delete --assignee {app_id} -g {rg}',
                         checks=self.is_empty())
                self.cmd('role assignment delete --assignee {app_id}',
                         checks=self.is_empty())
        finally:
            self.cmd('ad app delete --id {app_id}')


class RbacSPCertScenarioTest(RoleScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_cert')
    def test_create_for_rbac_with_cert_with_assignment(self, resource_group):

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'display_name': resource_group
        })

        try:
            with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
                result = self.cmd('ad sp create-for-rbac -n {display_name} --scopes {scope} {scope}/resourceGroups/{rg} --create-cert',
                                  checks=self.check('displayName', '{display_name}')).get_output_in_json()
                self.kwargs['app_id'] = result['appId']

                self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))
                os.remove(result['fileWithCertAndPrivateKey'])
                result = self.cmd('ad sp credential reset -n {app_id} --create-cert',
                                  checks=self.check('name', '{app_id}')).get_output_in_json()
                self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))
                os.remove(result['fileWithCertAndPrivateKey'])
        finally:
            self.cmd('ad app delete --id {app_id}',
                     checks=self.is_empty())

class RbacSPKeyVaultScenarioTest2(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_new_cert')
    @KeyVaultPreparer(name_prefix='test-rbac-new-kv')
    def test_create_for_rbac_with_new_kv_cert(self, resource_group, key_vault):
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

        try:
            with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
                try:
                    result = self.cmd('ad sp create-for-rbac --scopes {scope}/resourceGroups/{rg} --create-cert '
                                      '--keyvault {kv} --cert {cert} -n {display_name}').get_output_in_json()
                    self.kwargs['app_id'] = result['appId']
                except KeyVaultErrorException:
                    if not self.is_live and not self.in_recording:
                        pass  # temporary workaround for keyvault challenge handling was ignored under playback
                    else:
                        raise
                cer1 = self.cmd('keyvault certificate show --vault-name {kv} -n {cert}').get_output_in_json()['cer']
                self.cmd('ad sp credential reset -n {app_id} --create-cert --keyvault {kv} --cert {cert}')
                cer2 = self.cmd('keyvault certificate show --vault-name {kv} -n {cert}').get_output_in_json()['cer']
                self.assertTrue(cer1 != cer2)
        finally:
            self.cmd('ad app delete --id {app_id}')


class RbacSPKeyVaultScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_existing_cert')
    @KeyVaultPreparer(name_prefix='test-rbac-exist-kv')
    def test_create_for_rbac_with_existing_kv_cert(self, resource_group, key_vault):

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
                                  '--cert {cert} --scopes {scope}/resourceGroups/{rg}').get_output_in_json()
                self.kwargs['app_id'] = result['appId']
            self.cmd('ad sp credential reset -n {app_id} --keyvault {kv} --cert {cert}')
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
                result = self.cmd('ad sp create-for-rbac --scopes {scope}/resourceGroups/{rg} --keyvault {kv} '
                                  '--cert {cert} -n {display_name2}').get_output_in_json()
                self.kwargs['app_id2'] = result['appId']
            self.cmd('ad sp credential reset -n {app_id2} --keyvault {kv} --cert {cert}')
        finally:
            try:
                self.cmd('ad app delete --id {app_id2}')
            except:
                pass


class RoleCreateScenarioTest(RoleScenarioTest):

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

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            retry(lambda: self.cmd('role definition create --role-definition {template}', checks=[
                self.check('permissions[0].actions[0]', 'Microsoft.Compute/*/read')]))
            retry(lambda: self.cmd('role definition list -n {role}', checks=self.check('[0].roleName', '{role}')))
            # verify we can update
            template['Actions'].append('Microsoft.Support/*')
            with open(temp_file, 'w') as f:
                json.dump(template, f)
            retry(lambda: self.cmd('role definition update --role-definition {template}',
                                   checks=self.check('permissions[0].actions[-1]', 'Microsoft.Support/*')))
            retry(lambda: self.cmd('role definition delete -n {role}', checks=self.is_empty()))


class RoleAssignmentScenarioTest(RoleScenarioTest):

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

            self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
            time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

            try:
                self.cmd('network nsg create -n {nsg} -g {rg}')
                result = self.cmd('network nsg show -n {nsg} -g {rg}').get_output_in_json()
                self.kwargs['nsg_id'] = result['id']

                # test role assignments on a resource group
                self.cmd('role assignment create --assignee {upn} --role contributor -g {rg}')
                self.cmd('role assignment list -g {rg}',
                         checks=self.check("length([])", 1))
                self.cmd('role assignment list --assignee {upn} --role contributor -g {rg}', checks=[
                    self.check("length([])", 1),
                    self.check("[0].properties.principalName", self.kwargs["upn"])
                ])

                # test couple of more general filters
                result = self.cmd('role assignment list -g {rg} --include-inherited').get_output_in_json()
                self.assertTrue(len(result) >= 1)

                result = self.cmd('role assignment list --all').get_output_in_json()
                self.assertTrue(len(result) >= 1)

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
            finally:
                self.cmd('ad user delete --upn-or-object-id {upn}')


class RoleAssignmentListScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_assignments_for_coadmins')
    @AllowLargeResponse()
    def test_assignments_for_co_admins(self, resource_group):

        result = self.cmd('role assignment list --include-classic-administrator').get_output_in_json()
        self.assertTrue([x for x in result if x['properties']['roleDefinitionName'] in ['CoAdministrator', 'AccountAdministrator']])
        self.cmd('role assignment list -g {}'.format(resource_group), checks=[
            self.check("length([])", 0)
        ])
        result = self.cmd('role assignment list -g {} --include-classic-administrator'.format(resource_group)).get_output_in_json()
        self.assertTrue([x for x in result if x['properties']['roleDefinitionName'] in ['CoAdministrator', 'AccountAdministrator']])


if __name__ == '__main__':
    unittest.main()

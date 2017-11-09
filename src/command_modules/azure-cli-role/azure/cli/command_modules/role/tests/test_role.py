# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI RBAC TEST DEFINITIONS
import json
import os
import tempfile
import time
import unittest

from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer


class RbacSPSecretScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_minimal')
    def test_create_for_rbac_with_secret(self, resource_group):

        self.kwargs['sp'] = 'http://{}'.format(resource_group)
        try:
            self.cmd('ad sp create-for-rbac -n {sp}2',
                     checks=self.check('name', '{sp}'))
        finally:
            self.cmd('ad app delete --id {sp}2')

    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_password')
    def test_create_for_rbac_with_secret(self, resource_group):

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'sp': 'http://{}'.format(resource_group)
        })

        try:
            self.cmd('ad sp create-for-rbac -n {sp} --scopes {scope} {scope}/resourceGroups/{rg}',
                     checks=self.check('name', '{sp}'))
            self.cmd('role assignment list --assignee {sp} --scope {scope}',
                     checks=self.check("length([])", 1))
            self.cmd('role assignment list --assignee {sp} -g {rg}',
                     checks=self.check("length([])", 1))
            self.cmd('role assignment delete --assignee {sp} -g {rg}',
                     checks=self.is_empty())
            self.cmd('role assignment delete --assignee {sp}',
                     checks=self.is_empty())
        finally:
            self.cmd('ad app delete --id {sp}')


class RbacSPCertScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_cert')
    def test_create_for_rbac_with_cert(self, resource_group):

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'sp': 'http://' + resource_group
        })

        try:
            result = self.cmd('ad sp create-for-rbac -n {sp} --scopes {scope} {scope}/resourceGroups/{rg} --create-cert',
                              checks=self.check('name', '{sp}')).get_output_in_json()
            self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))
            os.remove(result['fileWithCertAndPrivateKey'])
            result = self.cmd('ad sp reset-credentials -n {sp} --create-cert',
                              checks=self.check('name', '{sp}')).get_output_in_json()
            self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))
            os.remove(result['fileWithCertAndPrivateKey'])
        finally:
            self.cmd('ad app delete --id {sp}',
                     checks=self.is_empty())


class RbacSPKeyVaultScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_new_cert')
    @KeyVaultPreparer()
    def test_create_for_rbac_with_new_kv_cert(self, resource_group, key_vault):

        import time
        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'sp': 'http://{}'.format(resource_group),
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'cert': 'cert1'
        })
        time.sleep(5)

        try:
            self.cmd('ad sp create-for-rbac --scopes {scope} {scope}/resourceGroups/{rg} --create-cert --keyvault {kv} --cert {cert} -n {sp}')
            cer1 = self.cmd('keyvault certificate show --vault-name {kv} -n {cert}').get_output_in_json()['cer']
            self.cmd('ad sp reset-credentials -n {sp} --create-cert --keyvault {kv} --cert {cert}')
            cer2 = self.cmd('keyvault certificate show --vault-name {kv} -n {cert}').get_output_in_json()['cer']
            self.assertTrue(cer1 != cer2)
        finally:
            self.cmd('ad app delete --id {sp}')

    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_existing_cert')
    @KeyVaultPreparer()
    def test_create_for_rbac_with_existing_kv_cert(self, resource_group, key_vault):

        import time
        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'sp': 'http://{}'.format(resource_group),
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'cert': 'cert1'
        })
        time.sleep(5)

        # test with valid length cert
        try:
            self.kwargs['policy'] = self.cmd('keyvault certificate get-default-policy').get_output_in_json()
            self.cmd('keyvault certificate create --vault-name {kv} -n {cert} -p "{policy}" --validity 24')
            self.cmd('ad sp create-for-rbac --scopes {scope} {scope}/resourceGroups/{rg} --keyvault {kv} --cert {cert} -n {sp}')
            self.cmd('ad sp reset-credentials -n {sp} --keyvault {kv} --cert {cert}')
        finally:
            self.cmd('ad app delete --id {sp}')

        # test with cert that has too short a validity
        try:
            self.kwargs['sp'] = '{}2'.format(self.kwargs['sp'])
            self.cmd('keyvault certificate create --vault-name {kv} -n {cert} -p "{policy}" --validity 6')
            self.cmd('ad sp create-for-rbac --scopes {scope} {scope}/resourceGroups/{rg} --keyvault {kv} --cert {cert} -n {sp}')
            self.cmd('ad sp reset-credentials -n {sp} --keyvault {kv} --cert {cert}')
        finally:
            self.cmd('ad app delete --id {sp}')


# TODO: Allow playback when issue #3187 resolved
class RoleCreateScenarioTest(LiveScenarioTest):

    def test_role_create_scenario(self):
        import time

        subscription_id = self.get_subscription_id()
        role_name = 'cli-test-role3'
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
                        "Microsoft.Insights/alertRules/*",
                        "Microsoft.Support/*"],
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

        self.cmd('role definition create --role-definition {template}')
        self.cmd('role definition list -n {role}',
                 checks=self.check('[0].properties.roleName', '{role}'))
        self.cmd('role definition delete -n {role}',
                 checks=self.is_empty())
        time.sleep(60)
        self.cmd('role definition list -n {role}',
                 checks=self.is_empty())


class RoleAssignmentScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_role_assignment')
    def test_role_assignment_scenario(self, resource_group):

        self.kwargs.update({
            'upn': 'testuser1@azuresdkteam.onmicrosoft.com',
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
            self.cmd('role assignment list --assignee {upn} --role contributor -g {rg}',
                     checks=self.check("length([])", 1))

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


if __name__ == '__main__':
    unittest.main()

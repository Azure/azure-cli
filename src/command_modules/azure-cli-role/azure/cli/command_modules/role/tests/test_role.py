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

from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer,
                               JMESPathCheck as JMESPathCheckV2)
from azure.cli.testsdk.vcr_test_base import (VCRTestBase, JMESPathCheck, ResourceGroupVCRTestBase, NoneCheck,
                                             MOCKED_SUBSCRIPTION_ID)


class RbacSPSecretScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_minimal')
    def test_create_for_rbac_with_secret(self, resource_group):

        sp_name = 'http://{}'.format(resource_group)
        try:
            self.cmd('ad sp create-for-rbac -n {}2'.format(sp_name), checks=[
                JMESPathCheckV2('name', sp_name)
            ])
        finally:
            self.cmd('ad app delete --id {}2'.format(sp_name))

    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_password')
    def test_create_for_rbac_with_secret(self, resource_group):

        subscription_id = self.cmd('account list --query "[?isDefault].id"').get_output_in_json()
        scope = '/subscriptions/{}'.format(subscription_id[0])
        sp_name = 'http://{}'.format(resource_group)

        try:
            self.cmd('ad sp create-for-rbac -n {0} --scopes {1} {1}/resourceGroups/{2}'.format(sp_name, scope, resource_group), checks=[
                JMESPathCheckV2('name', sp_name)
            ])
            self.cmd('role assignment list --assignee {} --scope {}'.format(sp_name, scope),
                     checks=[JMESPathCheckV2("length([])", 1)])
            self.cmd('role assignment list --assignee {} -g {}'.format(sp_name, resource_group),
                     checks=[JMESPathCheckV2("length([])", 1)])
            self.cmd('role assignment delete --assignee {} -g {}'.format(sp_name, resource_group),
                     checks=NoneCheck())
            self.cmd('role assignment delete --assignee {}'.format(sp_name), checks=NoneCheck())
        finally:
            self.cmd('ad app delete --id {}'.format(sp_name))


class RbacSPCertScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_cert')
    def test_create_for_rbac_with_cert(self, resource_group):

        subscription_id = self.cmd('account list --query "[?isDefault].id"').get_output_in_json()
        scope = '/subscriptions/{}'.format(subscription_id[0])
        sp_name = 'http://' + resource_group

        try:
            result = self.cmd('ad sp create-for-rbac -n {0} --scopes {1} {1}/resourceGroups/{2} --create-cert'.format(sp_name, scope, resource_group)).get_output_in_json()
            self.assertEqual(sp_name, result['name'])
            self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))
            os.remove(result['fileWithCertAndPrivateKey'])
            result = self.cmd('ad sp reset-credentials -n {0} --create-cert'.format(sp_name)).get_output_in_json()
            self.assertEqual(sp_name, result['name'])
            self.assertTrue(result['fileWithCertAndPrivateKey'].endswith('.pem'))
            os.remove(result['fileWithCertAndPrivateKey'])
        finally:
            self.cmd('ad app delete --id {}'.format(sp_name), checks=NoneCheck())


class RbacSPKeyVaultScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_new_cert')
    @KeyVaultPreparer()
    def test_create_for_rbac_with_new_kv_cert(self, resource_group, key_vault):

        import time
        sp_name = 'http://{}'.format(resource_group)

        subscription_id = self.cmd('account list --query "[?isDefault].id"').get_output_in_json()
        scope = '/subscriptions/{}'.format(subscription_id[0])
        cert_name = 'cert1'
        time.sleep(5)

        try:
            self.cmd('ad sp create-for-rbac --scopes {0} {0}/resourceGroups/{1} --create-cert --keyvault {2} --cert {3} -n {4}'.format(
                scope, resource_group, key_vault, cert_name, sp_name)).get_output_in_json()
            cer1 = self.cmd('keyvault certificate show --vault-name {0} -n {1}'.format(key_vault, cert_name)).get_output_in_json()['cer']
            self.cmd('ad sp reset-credentials -n {0} --create-cert --keyvault {1} --cert {2}'.format(sp_name, key_vault, cert_name))
            cer2 = self.cmd('keyvault certificate show --vault-name {0} -n {1}'.format(key_vault, cert_name)).get_output_in_json()['cer']
            self.assertTrue(cer1 != cer2)
        finally:
            self.cmd('ad app delete --id {}'.format(sp_name))

    @ResourceGroupPreparer(name_prefix='cli_test_sp_with_kv_existing_cert')
    @KeyVaultPreparer()
    def test_create_for_rbac_with_existing_kv_cert(self, resource_group, key_vault):

        import time
        sp_name = 'http://{}'.format(resource_group)

        subscription_id = self.cmd('account list --query "[?isDefault].id"').get_output_in_json()
        scope = '/subscriptions/{}'.format(subscription_id[0])
        cert_name = 'cert1'
        time.sleep(5)

        # test with valid length cert
        try:
            policy = self.cmd('keyvault certificate get-default-policy').get_output_in_json()
            self.cmd('keyvault certificate create --vault-name {} -n {} -p "{}" --validity 24'.format(key_vault, cert_name, policy))
            self.cmd('ad sp create-for-rbac --scopes {0} {0}/resourceGroups/{1} --keyvault {2} --cert {3} -n {4}'.format(
                scope, resource_group, key_vault, cert_name, sp_name)).get_output_in_json()
            self.cmd('ad sp reset-credentials -n {0} --keyvault {1} --cert {2}'.format(sp_name, key_vault, cert_name))
        finally:
            self.cmd('ad app delete --id {}'.format(sp_name))

        # test with cert that has too short a validity
        try:
            sp_name = '{}2'.format(sp_name)
            self.cmd('keyvault certificate create --vault-name {} -n {} -p "{}" --validity 6'.format(key_vault, cert_name, policy))
            self.cmd('ad sp create-for-rbac --scopes {0} {0}/resourceGroups/{1} --keyvault {2} --cert {3} -n {4}'.format(
                scope, resource_group, key_vault, cert_name, sp_name)).get_output_in_json()
            self.cmd('ad sp reset-credentials -n {0} --keyvault {1} --cert {2}'.format(sp_name, key_vault, cert_name))
        finally:
            self.cmd('ad app delete --id {}'.format(sp_name))


class RoleCreateScenarioTest(VCRTestBase):
    def __init__(self, test_method):
        super(RoleCreateScenarioTest, self).__init__(__file__, test_method)

    def test_role_create_scenario(self):
        if self.playback:
            logger.warning('Skipping RoleCreateScenarioTest due to bugs in role commands. '
                           'See issue #3187.')
            return
        self.execute()

    def body(self):
        if self.playback:
            subscription_id = MOCKED_SUBSCRIPTION_ID
        else:
            subscription_id = self.cmd('account list --query "[?isDefault].id" -o tsv')
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

        self.cmd('role definition create --role-definition {}'.format(temp_file.replace('\\', '\\\\')), None)
        self.cmd('role definition list -n {}'.format(role_name),
                 checks=[JMESPathCheck('[0].properties.roleName', role_name)])
        self.cmd('role definition delete -n {}'.format(role_name), None)
        self.cmd('role definition list -n {}'.format(role_name), NoneCheck())


class RoleAssignmentScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(RoleAssignmentScenarioTest, self).__init__(__file__, test_method,
                                                         resource_group='cli-role-assignment-test')
        self.user = 'testuser1@azuresdkteam.onmicrosoft.com'

    def set_up(self):
        super(RoleAssignmentScenarioTest, self).set_up()
        self.cmd(
            'ad user create --display-name tester123 --password Test123456789 --user-principal-name {}'.format(
                self.user), None)
        time.sleep(
            15)  # By-design, it takes some time for RBAC system propagated with graph object change

    def tear_down(self):
        self.cmd('ad user delete --upn-or-object-id {}'.format(self.user), None)
        super(RoleAssignmentScenarioTest, self).tear_down()

    def test_role_assignment_scenario(self):
        if self.playback:
            return  # live-only test, so far unable to replace guid in binary encoded body
        else:
            self.execute()

    def body(self):
        nsg_name = 'nsg1'
        self.cmd('network nsg create -n {} -g {}'.format(nsg_name, self.resource_group), None)
        result = self.cmd('network nsg show -n {} -g {}'.format(nsg_name, self.resource_group),
                          None)
        resource_id = result['id']

        # test role assignments on a resource group
        self.cmd('role assignment create --assignee {} --role contributor -g {}'.format(self.user,
                                                                                        self.resource_group),
                 None)
        self.cmd('role assignment list -g {}'.format(self.resource_group),
                 checks=[JMESPathCheck("length([])", 1)])
        self.cmd('role assignment list --assignee {} --role contributor -g {}'.format(self.user,
                                                                                      self.resource_group),
                 checks=[JMESPathCheck("length([])", 1)])

        # test couple of more general filters
        result = self.cmd(
            'role assignment list -g {} --include-inherited'.format(self.resource_group), None)
        self.assertTrue(len(result) >= 1)

        result = self.cmd('role assignment list --all'.format(self.user, self.resource_group), None)
        self.assertTrue(len(result) >= 1)

        self.cmd('role assignment delete --assignee {} --role contributor -g {}'.format(self.user,
                                                                                        self.resource_group),
                 None)
        self.cmd('role assignment list -g {}'.format(self.resource_group), checks=NoneCheck())

        # test role assignments on a resource
        self.cmd(
            'role assignment create --assignee {} --role contributor --scope {}'.format(self.user,
                                                                                        resource_id),
            None)
        self.cmd(
            'role assignment list --assignee {} --role contributor --scope {}'.format(self.user,
                                                                                      resource_id),
            checks=[JMESPathCheck("length([])", 1)])
        self.cmd(
            'role assignment delete --assignee {} --role contributor --scope {}'.format(self.user,
                                                                                        resource_id),
            None)
        self.cmd('role assignment list --scope {}'.format(resource_id), checks=NoneCheck())

        # test role assignment on subscription level
        self.cmd('role assignment create --assignee {} --role reader'.format(self.user), None)
        self.cmd('role assignment list --assignee {} --role reader'.format(self.user),
                 checks=[JMESPathCheck("length([])", 1)])
        self.cmd('role assignment list --assignee {}'.format(self.user),
                 checks=[JMESPathCheck("length([])", 1)])
        self.cmd('role assignment delete --assignee {} --role reader'.format(self.user), None)


if __name__ == '__main__':
    unittest.main()

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI RBAC TEST DEFINITIONS
import json
import os
import uuid
import tempfile
import time
import datetime
import unittest
import mock

from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer
from .role_scenario_test import RoleScenarioTest


class RbacSPSecretScenarioTest(RoleScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_minimal')
    def test_create_for_rbac_with_secret_no_assignment(self, resource_group):

        self.kwargs['sp'] = 'http://{}'.format(resource_group)
        try:
            self.cmd('ad sp create-for-rbac -n {sp} --skip-assignment', checks=self.check('name', '{sp}'))
        finally:
            self.cmd('ad app delete --id {sp}')

    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_password')
    def test_create_for_rbac_with_secret_with_assignment(self, resource_group):

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'sp': 'http://{}'.format(resource_group)
        })

        try:
            guids = ['88DAAF5A-EA86-4A68-9D45-477538D41300', '88DAAF5A-EA86-4A68-9D45-477538D41301',
                     '88DAAF5A-EA86-4A68-9D45-477538D41302', '88DAAF5A-EA86-4A68-9D45-477538D41303',
                     '88DAAF5A-EA86-4A68-9D45-477538D41304', '88DAAF5A-EA86-4A68-9D45-477538D41305']
            with self.get_guid_gen_patch(guids):
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


class RbacSPCertScenarioTest(RoleScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_create_rbac_sp_with_cert')
    def test_create_for_rbac_with_cert_with_assignment(self, resource_group):

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'sub': subscription_id,
            'scope': '/subscriptions/{}'.format(subscription_id),
            'sp': 'http://' + resource_group
        })

        try:
            guids = ['88DAAF5A-EA86-4A68-9D45-477538D61400', '88DAAF5A-EA86-4A68-9D45-477538D61401', '88DAAF5A-EA86-4A68-9D45-477538D61402',
                     '88DAAF5A-EA86-4A68-9D45-477538D61403', '88DAAF5A-EA86-4A68-9D45-477538D61404', '88DAAF5A-EA86-4A68-9D45-477538D61405',
                     '88DAAF5A-EA86-4A68-9D45-477538D61406', '88DAAF5A-EA86-4A68-9D45-477538D61407', '88DAAF5A-EA86-4A68-9D45-477538D61408']
            with self.get_guid_gen_patch(guids):
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
            'cert': 'cert1',
            'kv': key_vault
        })
        time.sleep(5)

        try:
            guids = ['88DAAF5A-EA86-4A68-9D45-477538D42500', '88DAAF5A-EA86-4A68-9D45-477538D42501', '88DAAF5A-EA86-4A68-9D45-477538D42502',
                     '88DAAF5A-EA86-4A68-9D45-477538D42503', '88DAAF5A-EA86-4A68-9D45-477538D42504', '88DAAF5A-EA86-4A68-9D45-477538D42505']
            with self.get_guid_gen_patch(guids):
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
            'cert': 'cert1',
            'kv': key_vault
        })
        time.sleep(5)

        # test with valid length cert
        try:
            self.kwargs['policy'] = self.cmd('keyvault certificate get-default-policy').get_output_in_json()
            self.cmd('keyvault certificate create --vault-name {kv} -n {cert} -p "{policy}" --validity 24')
            guids = ['88DAAF5A-EA86-4A68-9D45-477538D43600', '88DAAF5A-EA86-4A68-9D45-477538D43601', '88DAAF5A-EA86-4A68-9D45-477538D43602',
                     '88DAAF5A-EA86-4A68-9D45-477538D43603', '88DAAF5A-EA86-4A68-9D45-477538D43604', '88DAAF5A-EA86-4A68-9D45-477538D43605']
            with self.get_guid_gen_patch(guids):
                self.cmd('ad sp create-for-rbac --scopes {scope} {scope}/resourceGroups/{rg} --keyvault {kv} --cert {cert} -n {sp}')
            self.cmd('ad sp reset-credentials -n {sp} --keyvault {kv} --cert {cert}')
        finally:
            self.cmd('ad app delete --id {sp}')

        # test with cert that has too short a validity
        try:
            self.kwargs['sp'] = '{}2'.format(self.kwargs['sp'])
            self.cmd('keyvault certificate create --vault-name {kv} -n {cert} -p "{policy}" --validity 6')
            guids = ['88DAAF5A-EA86-4A68-9D45-477538D42700', '88DAAF5A-EA86-4A68-9D45-477538D42701', '88DAAF5A-EA86-4A68-9D45-477538D42702',
                     '88DAAF5A-EA86-4A68-9D45-477538D42700', '88DAAF5A-EA86-4A68-9D45-477538D42701', '88DAAF5A-EA86-4A68-9D45-477538D42702']
            with self.get_guid_gen_patch(guids):
                self.cmd('ad sp create-for-rbac --scopes {scope} {scope}/resourceGroups/{rg} --keyvault {kv} --cert {cert} -n {sp}')
            self.cmd('ad sp reset-credentials -n {sp} --keyvault {kv} --cert {cert}')
        finally:
            self.cmd('ad app delete --id {sp}')


class RoleCreateScenarioTest(RoleScenarioTest):

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
        with self.get_guid_gen_patch(['88DAAF5A-EA86-4A68-9D45-477538D41738']):
            self.cmd('role definition create --role-definition {template}')
            time.sleep(60)
            self.cmd('role definition list -n {role}',
                     checks=self.check('[0].properties.roleName', '{role}'))
            self.cmd('role definition delete -n {role}',
                     checks=self.is_empty())
            time.sleep(60)
            self.cmd('role definition list -n {role}',
                     checks=self.is_empty())


class RoleAssignmentScenarioTest(RoleScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_role_assign')
    def test_role_assignment_e2e(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.enable_large_payload()
        user = self.create_random_name('testuser', 15)
        self.kwargs.update({
            'upn': user + '@azuresdkteam.onmicrosoft.com',
            'nsg': 'nsg1'
        })

        self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

        guids = ['88DAAF5A-EA86-4A68-9D45-477538D41100', '88DAAF5A-EA86-4A68-9D45-477538D41101', '88DAAF5A-EA86-4A68-9D45-477538D41102']
        with self.get_guid_gen_patch(guids):
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

    @ResourceGroupPreparer(name_prefix='cli_role_audit')
    def test_role_assignment_audits(self, resource_group):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...

        self.enable_large_payload()
        user = self.create_random_name('testuser', 15)
        self.kwargs.update({
            'upn': user + '@azuresdkteam.onmicrosoft.com',
        })

        self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

        guids = ['88DAAF5A-EA86-4A68-9D89-477538D41100']
        with self.get_guid_gen_patch(guids):
            try:
                self.cmd('role assignment create --assignee {upn} --role contributor -g {rg}')

                if self.is_live or self.in_recording:
                    now = datetime.datetime.utcnow()
                    start_time = '{}-{}-{}T{}:{}:{}Z'.format(now.year, now.month, now.day - 1, now.hour,
                                                             now.minute, now.second)
                    time.sleep(15)
                    self.cmd('role assignment list-changelogs --start-time {}'.format(start_time))
                else:
                    # NOTE: get the time range from the recording file and use them below for playback
                    start_time, end_time = '2018-02-10T21:36:06Z', '2018-02-11T21:39:05Z'
                    result = self.cmd('role assignment list-changelogs --start-time {} --end-time {}'.format(
                        start_time, end_time)).get_output_in_json()
                    self.assertTrue([x for x in result if (resource_group in x['scope'] and
                                                           x['principalName'] == self.kwargs['upn'])])
            finally:
                self.cmd('ad user delete --upn-or-object-id {upn}')


class RoleAssignmentListScenarioTest(RoleScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_assignments_for_coadmins')
    def test_assignments_for_co_admins(self, resource_group):
        self.enable_large_payload()

        result = self.cmd('role assignment list --include-classic-administrator').get_output_in_json()
        self.assertTrue([x for x in result if x['properties']['roleDefinitionName'] in ['CoAdministrator', 'AccountAdministrator']])
        self.cmd('role assignment list -g {}'.format(resource_group), checks=[
            self.check("length([])", 0)
        ])
        result = self.cmd('role assignment list -g {} --include-classic-administrator'.format(resource_group)).get_output_in_json()
        self.assertTrue([x for x in result if x['properties']['roleDefinitionName'] in ['CoAdministrator', 'AccountAdministrator']])


if __name__ == '__main__':
    unittest.main()

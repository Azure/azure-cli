# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from azure.core.exceptions import HttpResponseError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, live_only


LOCATION = "westus2"

# -----------------------------------------------------------------------------
# How to run this test
# -----------------------------------------------------------------------------
# This test uses the standard record/playback model. Run these commands from
# the azure-cli repository root.
#
# Playback (default, no Azure access required; requires a recording for each test):
#
#   pytest -vv \
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_account_refresh_ldap_bind_password.py
#
# The positive test creates a new account, pool and LDAP-enabled volume in
# sdk-py-test-rg. It reuses dap-bind-uksouth-identity and the
# ldapbind-uksouth-kv-1 vault and ldapuser-password secret. The existing
# identity must already have permission to read the secret.
# It reuses the default subnet of
# api-test-vnet-westus2stage in sdk-py-test-rg in the active subscription.
# That subnet must be delegated to Microsoft.NetApp/volumes and able to reach
# the existing contoso.com LDAP server at 10.0.2.4.
# The positive test assigns the existing identity to the new account,
# configures LDAP and cleans up each created resource in a finally block,
# including when later commands or checks fail. Cleanup waits 40 seconds before each
# deletion during live/recording runs, with no delay during playback. Only the
# negative test deletes its prepared resource group. The existing network
# is not modified. Re-record after changing the setup.
#
# PowerShell live recording:
#
#   $env:AZURE_TEST_RUN_LIVE = "True"
#   pytest -vv `
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_account_refresh_ldap_bind_password.py
#   Remove-Item Env:AZURE_TEST_RUN_LIVE -ErrorAction SilentlyContinue
#
# Via azdev (live recording):
#
#   azdev test test_refresh_ldap_bind_password --live
#   azdev test test_refresh_ldap_bind_password_without_simple_bind --live
# -----------------------------------------------------------------------------


class AzureNetAppFilesRefreshLdapBindPasswordScenarioTest(ScenarioTest):
    @live_only()
    def test_refresh_ldap_bind_password(self):
        # ToDo: Remove all hardcoded values and replace with dynamic test setup.
        self.kwargs.update({
            'loc': LOCATION,
            'rg': 'sdk-py-test-rg',
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'vol_name': self.create_random_name(prefix='cli-vol-', length=24),
            'identity_name': 'dap-bind-uksouth-identity',
            'key_vault_uri': 'https://ldapbind-uksouth-kv-1.vault.azure.net',
            'secret_name': 'ldapuser-password',
            'ldap_server_ip': '10.0.2.4',
            'network_rg': 'sdk-py-test-rg',
            'vnet_name': 'api-test-vnet-westus2stage',
            'subnet_name': 'default',
        })

        identity = self.cmd(
            "az identity show -g {rg} -n {identity_name}"
        ).get_output_in_json()
        self.kwargs.update({
            'identity_id': identity['id'].replace('/resourcegroups/', '/resourceGroups/', 1),
        })
        created_resources = set()
        try:
            account = self.cmd(
                "az netappfiles account create -g {rg} -a {acc_name} -l {loc} "
                "--identity-type UserAssigned --mi-user-assigned \"{identity_id}\""
            )
            created_resources.add('account')
            account.assert_with_checks([
                self.check('name', '{acc_name}'),
                self.check('identity.type', 'UserAssigned'),
            ])
            pool = self.cmd(
                "az netappfiles pool create -g {rg} -a {acc_name} -p {pool_name} -l {loc} "
                "--service-level Premium --size 4"
            )
            created_resources.add('pool')
            pool.assert_with_checks([self.check('name', '{acc_name}/{pool_name}')])

            self.cmd(
                "az netappfiles account ldap-configuration create --account-name {acc_name} --resource-group {rg} "
                "--domain contoso.com --ldap-port 389 --ldap-servers {ldap_server_ip} "
                "--bind-password-azure-key-vault-uri \"{key_vault_uri}\" --bind-password-secret-name {secret_name} "
                "--bind-password-user-assigned-identity \"{identity_id}\" --bind-auth-level Simple "
                "--bind-dn \"uid=ldapuser,cn=users,cn=accounts,dc=contoso,dc=com\"",
                checks=[self.check('bindAuthenticationLevel', 'Simple')]
            )
            self.cmd(
                "az netappfiles account ldap-configuration wait --account-name {acc_name} --resource-group {rg} "
                "--created --interval 10 --timeout 300"
            )

            subnet = self.cmd(
                "az network vnet subnet show -g {network_rg} --vnet-name {vnet_name} -n {subnet_name}"
            ).get_output_in_json()
            self.kwargs['subnet_id'] = subnet['id']
            volume = self.cmd(
                "az netappfiles volume create -g {rg} --account-name {acc_name} --pool-name {pool_name} "
                "--volume-name {vol_name} -l {loc} --creation-token {vol_name} "
                "--service-level Premium --usage-threshold 100 --ldap-enabled true --ldap-server-type OpenLdap "
                "--subnet \"{subnet_id}\" --vnet {vnet_name} --protocol-types NFSv3"
            )
            created_resources.add('volume')
            volume.assert_with_checks([
                self.check('name', '{acc_name}/{pool_name}/{vol_name}'),
                self.check('ldapEnabled', True),
                self.check('ldapServerType', 'OpenLdap'),
            ])

            result = self.cmd(
                "az netappfiles account refresh-ldap-bind-password "
                "--account-name {acc_name} --resource-group {rg}"
            )
            self.assertEqual(result.output.strip(), '')
        finally:
            for resource, command in (
                ('volume', "az netappfiles volume delete -g {rg} -a {acc_name} -p {pool_name} "
                 "-v {vol_name} --force --yes"),
                ('pool', "az netappfiles pool delete -g {rg} -a {acc_name} -p {pool_name} --yes"),
                ('account', "az netappfiles account delete -g {rg} -a {acc_name} --yes"),
            ):
                if resource in created_resources:
                    with self.subTest(cleanup=resource):
                        if self.is_live or self.in_recording:
                            time.sleep(40)
                        self.cmd(command)

    @ResourceGroupPreparer(
        name_prefix='cli_netappfiles_test_refresh_ldap_',
        additional_tags={'owner': 'cli_test'}
    )
    def test_refresh_ldap_bind_password_without_simple_bind(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24)
        })

        self.cmd(
            "az netappfiles account create -g {rg} -a {acc_name} -l {loc}",
            checks=[self.check('name', '{acc_name}')]
        )

        with self.assertRaises(HttpResponseError) as cm:
            self.cmd(
                "az netappfiles account refresh-ldap-bind-password "
                "--account-name {acc_name} --resource-group {rg}"
            )

        error = str(cm.exception)
        self.assertIn('LdapConfigInvalidForRefreshBindPassword', error)
        self.assertIn('does not have LDAP configured with Simple bind authentication', error)

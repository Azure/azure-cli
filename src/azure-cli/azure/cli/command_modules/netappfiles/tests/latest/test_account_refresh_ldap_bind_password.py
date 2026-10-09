# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core.exceptions import HttpResponseError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


LOCATION = "eastus2"

# -----------------------------------------------------------------------------
# How to run this test
# -----------------------------------------------------------------------------
# This test uses the standard record/playback model. Run these commands from
# the azure-cli repository root.
#
# Playback (default, no Azure access required):
#
#   pytest -vv \
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_account_refresh_ldap_bind_password.py
#
# PowerShell live recording (creates and removes a temporary resource group):
#
#   $env:AZURE_TEST_RUN_LIVE = "True"
#   pytest -vv `
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_account_refresh_ldap_bind_password.py
#   Remove-Item Env:AZURE_TEST_RUN_LIVE -ErrorAction SilentlyContinue
#
# Via azdev (live recording):
#
#   azdev test test_refresh_ldap_bind_password_without_simple_bind --live
# -----------------------------------------------------------------------------


class AzureNetAppFilesRefreshLdapBindPasswordScenarioTest(ScenarioTest):
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

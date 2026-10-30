# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core.exceptions import HttpResponseError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


LOCATION = "westus2"
LDAP_NA_NAME = "na-ldap-test"
LDAP_NA_RG = "sdk-py-test-rg"

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
# Positive test prerequisite: na-ldap-test in sdk-py-test-rg must already have
# LDAP Simple Bind configured with a valid Azure Key Vault password reference.
# Live runs refresh that account's password; only the negative test creates
# and removes a temporary resource group.
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
    def test_refresh_ldap_bind_password(self):
        self.kwargs.update({
            'acc_name': LDAP_NA_NAME,
            'rg': LDAP_NA_RG,
        })

        result = self.cmd(
            "az netappfiles account refresh-ldap-bind-password "
            "--account-name {acc_name} --resource-group {rg}"
        )
        self.assertEqual(result.output.strip(), '')

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

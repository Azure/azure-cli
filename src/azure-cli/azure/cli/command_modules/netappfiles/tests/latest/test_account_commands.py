# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from knack.util import CLIError
from azure.cli.core.azclierror import ValidationError
from azure.core.exceptions import HttpResponseError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import time
LOCATION = "eastus2"
#LOCATION = "eastus2euap"
ADLOCATION = "northeurope"
#ADLOCATION = "eastus2euap"

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesAccountServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_account(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'tags': 'Tag1=Value1 Tag2=Value2'
        })

        # create and check
        # note : active directory checks are performed in their own subgroup test
        self.cmd(
            "az netappfiles account create --resource-group {rg} --account-name '{acc_name}' --location {loc} "
            "--tags {tags}", checks=[
                self.check('name', '{acc_name}'),
                self.check('tags.Tag1', 'Value1'),
                self.check('tags.Tag2', 'Value2')
            ])

        self.cmd("netappfiles account list --resource-group {rg}", checks=[
            self.check('length(@)', 1)
        ])

        # delete and recheck
        self.cmd("az netappfiles account delete --resource-group {rg} --account-name '{acc_name}' --yes")
        self.cmd("netappfiles account list --resource-group {rg}", checks=[
            self.check('length(@)', 0)
        ])

        # and again with short forms and also unquoted
        self.cmd("az netappfiles account create -g {rg} -a {acc_name} -l {loc} --tags {tags}", checks=[
            self.check('name', '{acc_name}')
        ])
        self.cmd("netappfiles account list --resource-group {rg}", checks=[
            self.check('length(@)', 1)
        ])

        self.cmd("az netappfiles account delete --resource-group {rg} -a {acc_name} --yes")
        self.cmd("netappfiles account list --resource-group {rg}", checks=[
            self.check('length(@)', 0)
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_list_accounts(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc1_name': self.create_random_name(prefix='cli-acc-', length=24),
            'acc2_name': self.create_random_name(prefix='cli-acc-', length=24)
        })
        self.cmd("az netappfiles account create -g {rg} -a {acc1_name} -l {loc} --tags Tag1=Value1")
        self.cmd("az netappfiles account create -g {rg} -a {acc2_name} -l {loc} --tags Tag1=Value1")

        self.cmd("netappfiles account list -g {rg}", checks=[
            self.check('length(@)', 2)
        ])

        self.cmd("az netappfiles account delete -g {rg} -a {acc1_name} --yes")
        self.cmd("az netappfiles account delete -g {rg} -a {acc2_name} --yes")

        self.cmd("netappfiles account list -g {rg}", checks=[
            self.check('length(@)', 0)
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_get_account_by_name(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24)
        })
        self.cmd("az netappfiles account create -g {rg} -a {acc_name} -l {loc}")
        account = self.cmd("az netappfiles account show --resource-group {rg} -a {acc_name}", checks=[
            self.check('name', '{acc_name}')
        ]).get_output_in_json()
        # test get account from id
        self.cmd(("az netappfiles account show --ids %s" % account['id']), checks=[self.check('name', '{acc_name}')])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_update_account(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'tags': 'Tag1=Value1 Tag2=Value2'
        })

        # create, update and check
        self.cmd(
            "az netappfiles account create -g {rg} -a '{acc_name}' -l {loc}", checks=[self.check('name', '{acc_name}')])
        self.cmd("az netappfiles account update -g {rg} -a {acc_name} --tags {tags}", checks=[
            self.check('name', '{acc_name}'),
            self.check('tags.Tag1', 'Value1'),
            self.check('tags.Tag2', 'Value2')
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_active_directory(self):
        self.kwargs.update({
            'loc': ADLOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'ad_name': 'cli-ad-name',
            'kdc_ip': '172.016.254.1',
            'ldap': True,
            'ldap_users': True,
            'ad_user': 'ad_user'
        })
        # create account
        self.cmd("az netappfiles account create -g {rg} -a {acc_name} -l {loc} --tags Tag1=Value1", checks=[
            self.check('name', '{acc_name}')
        ])

        account = self.cmd("az netappfiles account show --resource-group {rg} -a {acc_name}", checks=[
            self.check('name', '{acc_name}')
        ]).get_output_in_json()

        if self.is_live or self.in_recording:
            time.sleep(60)
        # add an active directory
        self.cmd(
            "netappfiles account ad add -g {rg} -n {acc_name} --username {ad_user} --password {ad_user} "
            "--smb-server-name SMBSERVER --dns '1.2.3.4' --domain {loc} --ad-name {ad_name} --kdc-ip {kdc_ip} "
            "--ldap-signing {ldap} --allow-local-ldap-users {ldap_users}")
        # self.cmd(
        #     "netappfiles account ad add -g {rg} -n {acc_name} --username {ad_user} --password {ad_user} "
        #     "--smb-server-name SMBSERVER --dns '1.2.3.4' --domain {loc} --ad-name {ad_name} --kdc-ip {kdc_ip} "
        #     "--ldap-signing {ldap} --allow-local-ldap-users {ldap_users}", checks=[
        #         self.check('name', '{acc_name}'),
        #         self.check('activeDirectories[0].username', '{ad_user}'),
        #         self.check('activeDirectories[0].status', 'Created'),
        #         self.check('activeDirectories[0].adName', '{ad_name}'),
        #         self.check('activeDirectories[0].aesEncryption', False),
        #         self.check('activeDirectories[0].ldapSigning', '{ldap}'),
        #         self.check('activeDirectories[0].allowLocalNfsUsersWithLdap', '{ldap_users}')
        #     ])

        # list active directory
        active_directories = self.cmd("netappfiles account ad list -g {rg} -n {acc_name}", checks=[
            self.check('[0].username', '{ad_user}'),
            self.check('length(@)', 1)
        ]).get_output_in_json()

        self.kwargs.update({
            'ad_id': active_directories[0]['activeDirectoryId']
        })

        # update active directory
        self.cmd("az netappfiles account ad update -g {rg} -n {acc_name} --active-directory-id {ad_id} "
                 "--password {ad_user} --username {ad_user} "
                 "--smb-server-name SMBSERVER --dns '1.2.3.5' --domain {loc} --ad-name {ad_name} --kdc-ip {kdc_ip} "
                 "--ldap-signing {ldap} --allow-local-ldap-users {ldap_users}",
                 checks=[
                     self.check('name', '{acc_name}'),
                     self.check('activeDirectories[0].username', '{ad_user}'),
                     self.check('activeDirectories[0].status', 'Created'),
                     self.check('activeDirectories[0].adName', '{ad_name}'),
                     self.check('activeDirectories[0].aesEncryption', False),
                     self.check('activeDirectories[0].ldapSigning', '{ldap}'),
                     #self.check('activeDirectories[0].allowLocalNFSUsersWithLdap', '{ldap_users}')
                 ])

        # remove active directory using the previously obtained details
        self.cmd("netappfiles account ad remove -g {rg} -n {acc_name} --active-directory %s --yes" %
                 active_directories[0]['activeDirectoryId'])

        self.cmd("netappfiles account show -g {rg} -n {acc_name}", checks=[
            self.check('name', '{acc_name}'),
            self.check('activeDirectories', None)
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_account_encryption(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'acc2_name': self.create_random_name(prefix='cli-acc-', length=24),
            'encryption': "Microsoft.NetApp"
        })
        # create account with encryption value
        self.cmd("az netappfiles account create -g {rg} -a {acc_name} -l {loc} --key-source {encryption}", checks=[
            self.check('name', '{acc_name}'),
            self.check('encryption.keySource', '{encryption}')
        ])

        # create account without encryption value
        self.cmd("az netappfiles account create -g {rg} -a {acc2_name} -l {loc}", checks=[
            self.check('name', '{acc2_name}')
        ])

        # update account with encryption value
        self.cmd("az netappfiles account update -g {rg} -a {acc2_name} --key-source {encryption}", checks=[
            self.check('name', '{acc2_name}'),
            self.check('encryption.keySource', '{encryption}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_account_cmk_encryption(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'acc2_name': self.create_random_name(prefix='cli-acc-', length=24),
            'keySource': "Microsoft.KeyVault",
            'keyVaultUri': "myUri",
            'keyName': "myKeyName",
            'keyVaultResourceId': "myKeyVaultResourceId",
            'userAssignedIdentity': "myIdentity",
            'identityType': "UserAssigned"
        })

        with self.assertRaises(HttpResponseError):
            # create account with encryption value                                                                                           user-assigned-identity
            self.cmd("az netappfiles account create -g {rg} -a {acc_name} -l {loc} --key-source {keySource} --identity-type {identityType} --user-assigned-identity {userAssignedIdentity} --key-vault-uri {keyVaultUri} --key-name {keyName} --keyvault-resource-id {keyVaultResourceId} --user-assigned-identity {userAssignedIdentity}", checks=[
                self.check('name', '{acc_name}'),
                self.check('encryption.keySource', '{keySource}'),
                self.check('identity.type', '{identityType}')
            ])

        # create account without encryption value
        self.cmd("az netappfiles account create -g {rg} -a {acc2_name} -l {loc}", checks=[
            self.check('name', '{acc2_name}')
        ])

        # update account with encryption value
        with self.assertRaises(HttpResponseError):
            self.cmd("az netappfiles account update -g {rg} -a {acc2_name} --key-source {keySource} --identity-type {identityType} --user-assigned-identity {userAssignedIdentity}", checks=[
                self.check('name', '{acc2_name}'),
                self.check('encryption.keySource', '{keySource}')
            ])

    #@unittest.skip('(servicedeployment) api has not been deployed cannot test until finalized')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'})
    def test_account_renew_credentials_fails(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'acc2_name': self.create_random_name(prefix='cli-acc-', length=24),
            'keySource': "Microsoft.KeyVault",
            'keyVaultUri': "myUri",
            'keyName': "myKeyName",
            'keyVaultResourceId': "myKeyVaultResourceId",
            'userAssignedIdentity': "myIdentity"
        })

        with self.assertRaises(HttpResponseError):
            # create account with encryption value
            self.cmd("az netappfiles account create -g {rg} -a {acc_name} -l {loc} --key-source {keySource} --key-vault-uri {keyVaultUri} --key-name {keyName} --keyvault-resource-id {keyVaultResourceId} --user-assigned-identity {userAssignedIdentity}", checks=[
                self.check('name', '{acc_name}'),
                self.check('encryption.keySource', '{keySource}')
            ])

        # create account without encryption value
        self.cmd("az netappfiles account create -g {rg} -a {acc2_name} -l {loc}", checks=[
            self.check('name', '{acc2_name}')
        ])

        with self.assertRaises(HttpResponseError) as cm:
            # create account with encryption value
            self.cmd("az netappfiles account renew-credentials -g {rg} -a {acc2_name} ", checks=[
                self.check('name', '{acc2_name}'),
            ])
        self.assertIn('MsiInvalidForRenewal', str(
            cm.exception))
        # with self.assertRaises(CLIError):
        #     # create account with encryption value
        #     self.cmd("az rest --method POST --uri /subscriptions/69a75bda-882e-44d5-8431-63421204132a/resourcegroups/{rg}/providers/Microsoft.NetApp/netappAccounts/{acc_name}/renewCredentials?api-version=2022-05-01  ", checks=[
        #         self.check('name', '{acc_name}'),
        #     ])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_account_', additional_tags={'owner': 'cli_test'}, location='eastus2euap')
    def test_create_account_with_no_location(self):
        self.kwargs.update({
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24)            
        })
        location = "eastus2euap"
        self.cmd("az netappfiles account create -g {rg} -a {acc_name}")
        self.cmd("az netappfiles account show --resource-group {rg} -a {acc_name}", checks=[
            self.check('location', location)
        ])

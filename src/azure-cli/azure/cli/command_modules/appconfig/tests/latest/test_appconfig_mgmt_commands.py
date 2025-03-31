# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import os

from knack.util import CLIError
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.cli.command_modules.appconfig.tests.latest._test_utils import CredentialResponseSanitizer, get_resource_name_prefix

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class AppConfigMgmtScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_mgmt(self, resource_group, location):
        mgmt_prefix = get_resource_name_prefix('MgmtTest')
        config_store_name = self.create_random_name(prefix=mgmt_prefix, length=24)

        location = 'eastus'
        standard_sku = 'standard'
        premium_sku = 'premium'
        tag_key = "key"
        tag_value = "value"
        tag = tag_key + '=' + tag_value
        structured_tag = {tag_key: tag_value}
        system_assigned_identity = '[system]'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': standard_sku,
            'tags': tag,
            'identity': system_assigned_identity,
            'retention_days': 1,
            'enable_purge_protection': False
        })

        store = self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection}',
                         checks=[self.check('name', '{config_store_name}'),
                                 self.check('location', '{rg_loc}'),
                                 self.check('resourceGroup', resource_group),
                                 self.check('provisioningState', 'Succeeded'),
                                 self.check('sku.name', standard_sku),
                                 self.check('tags', structured_tag),
                                 self.check('identity.type', 'SystemAssigned'),
                                 self.check('softDeleteRetentionInDays', '{retention_days}'),
                                 self.check('enablePurgeProtection', '{enable_purge_protection}')]).get_output_in_json()

        self.cmd('appconfig list -g {rg}',
                 checks=[self.check('[0].name', '{config_store_name}'),
                         self.check('[0].location', '{rg_loc}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[0].sku.name', standard_sku),
                         self.check('[0].tags', structured_tag),
                         self.check('[0].identity.type', 'SystemAssigned')])

        self.cmd('appconfig show -n {config_store_name} -g {rg}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', standard_sku),
                         self.check('tags', structured_tag),
                         self.check('identity.type', 'SystemAssigned')])

        tag_key = "Env"
        tag_value = "Prod"
        updated_tag = tag_key + '=' + tag_value
        structured_tag = {tag_key: tag_value}
        self.kwargs.update({
            'updated_tag': updated_tag,
            'update_sku': premium_sku   # update to premium sku
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --tags {updated_tag} --sku {update_sku}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('tags', structured_tag),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', premium_sku)])

        keyvault_prefix = get_resource_name_prefix('cmk-test-keyvault')
        keyvault_name = self.create_random_name(prefix=keyvault_prefix, length=24)
        encryption_key = 'key'
        system_assigned_identity_id = store['identity']['principalId']
        self.kwargs.update({
            'encryption_key': encryption_key,
            'keyvault_name': keyvault_name,
            'identity_id': system_assigned_identity_id
        })

        keyvault = _setup_key_vault(self, self.kwargs)
        keyvault_uri = keyvault['properties']['vaultUri']
        self.kwargs.update({
            'keyvault_uri': keyvault_uri,
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --encryption-key-name {encryption_key} --encryption-key-vault {keyvault_uri}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('tags', structured_tag),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', premium_sku),
                         self.check('encryption.keyVaultProperties.keyIdentifier', keyvault_uri.strip('/') + "/keys/{}/".format(encryption_key))])

        self.kwargs.update({
            'updated_tag': '""',
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --tags {updated_tag}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('resourceGroup', resource_group),
                    self.check('tags', {}),
                    self.check('provisioningState', 'Succeeded'),
                    self.check('sku.name', premium_sku),
                    self.check('encryption.keyVaultProperties.keyIdentifier', keyvault_uri.strip('/') + "/keys/{}/".format(encryption_key))])

        # update private link delegation mode and private network access
        pass_through_auth_mode = 'pass-through'
        local_auth_mode = "local"

        # update authentication mode to 'local'
        self.kwargs.update({
            'data_plane_auth_mode': local_auth_mode,
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --arm-auth-mode {data_plane_auth_mode}',
                 checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('resourceGroup', resource_group),
                    self.check('tags', {}),
                    self.check('provisioningState', 'Succeeded'),
                    self.check('dataPlaneProxy.authenticationMode', 'Local')])

        # enabling private network access should fail
        with self.assertRaisesRegex(HttpResponseError, 'Data plane proxy authentication mode must be set to Pass-through to enable private link delegation'):
            self.cmd('appconfig update -n {config_store_name} -g {rg} --enable-arm-private-network-access')

        # update authengication mode to 'pass-through'
        self.kwargs.update({
            'data_plane_auth_mode': pass_through_auth_mode,
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --arm-auth-mode {data_plane_auth_mode}',
                 checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('resourceGroup', resource_group),
                    self.check('tags', {}),
                    self.check('provisioningState', 'Succeeded'),
                    self.check('dataPlaneProxy.authenticationMode', 'Pass-through')])

        self.cmd('appconfig update -n {config_store_name} -g {rg} --enable-arm-private-network-access',
                 checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('resourceGroup', resource_group),
                    self.check('tags', {}),
                    self.check('provisioningState', 'Succeeded'),
                    self.check('dataPlaneProxy.privateLinkDelegation', 'Enabled')])

        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        # create store in premium tier with replica
        premium_store_prefix = get_resource_name_prefix('MgmtTestPremiumSku')
        replica_prefix = get_resource_name_prefix('MgmtTestReplica')
        config_store_name = self.create_random_name(prefix=premium_store_prefix, length=24)
        replica_name = self.create_random_name(prefix=replica_prefix, length=24)
        tag_key = "key"
        tag_value = "value"
        tag = tag_key + '=' + tag_value
        structured_tag = {tag_key: tag_value}
        
        self.kwargs.update({
            "premium_sku": premium_sku,
            "config_store_name": config_store_name,
            "replica_name": replica_name,
            "replica_location": "westus",
            "tags": tag
        })

        store = self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {premium_sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection} --replica-name {replica_name} --replica-location {replica_location}',
                         checks=[self.check('name', '{config_store_name}'),
                                 self.check('location', '{rg_loc}'),
                                 self.check('resourceGroup', resource_group),
                                 self.check('provisioningState', 'Succeeded'),
                                 self.check('sku.name', premium_sku),
                                 self.check('tags', structured_tag),
                                 self.check('identity.type', 'SystemAssigned'),
                                 self.check('softDeleteRetentionInDays', '{retention_days}'),
                                 self.check('enablePurgeProtection', '{enable_purge_protection}')]).get_output_in_json()
        
        self.cmd('appconfig list -g {rg}',
                 checks=[self.check('[0].name', '{config_store_name}'),
                         self.check('[0].location', '{rg_loc}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[0].sku.name', premium_sku),
                         self.check('[0].tags', structured_tag),
                         self.check('[0].identity.type', 'SystemAssigned')])

        self.cmd('appconfig show -n {config_store_name} -g {rg}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', premium_sku),
                         self.check('tags', structured_tag),
                         self.check('identity.type', 'SystemAssigned')])
        
        self.cmd('appconfig replica show -s {config_store_name} -g {rg} -n {replica_name}',
                 checks=[self.check('name', '{replica_name}'),
                         self.check('location', '{replica_location}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('appconfig replica list -s {config_store_name}',
                 checks=[self.check('[0].name', '{replica_name}'),
                         self.check('[0].location', '{replica_location}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded')])

        self.cmd('appconfig replica delete -s {config_store_name} -g {rg} -n {replica_name} -y')

        with self.assertRaisesRegex(ResourceNotFoundError, f"The replica '{replica_name}' for App Configuration '{config_store_name}' not found."):
            self.cmd('appconfig replica show -s {config_store_name} -g {rg} -n {replica_name}')
        
        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        # create store in premium tier without replica

        config_store_name = self.create_random_name(prefix=premium_store_prefix, length=24)
        
        self.kwargs.update({
            "premium_sku": premium_sku,
            "config_store_name": config_store_name,
        })

        store = self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {premium_sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection} --no-replica',
                         checks=[self.check('name', '{config_store_name}'),
                                 self.check('location', '{rg_loc}'),
                                 self.check('resourceGroup', resource_group),
                                 self.check('provisioningState', 'Succeeded'),
                                 self.check('sku.name', premium_sku),
                                 self.check('tags', structured_tag),
                                 self.check('identity.type', 'SystemAssigned'),
                                 self.check('softDeleteRetentionInDays', '{retention_days}'),
                                 self.check('enablePurgeProtection', '{enable_purge_protection}')]).get_output_in_json()
        
        self.cmd('appconfig list -g {rg}',
                 checks=[self.check('[0].name', '{config_store_name}'),
                         self.check('[0].location', '{rg_loc}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[0].sku.name', premium_sku),
                         self.check('[0].tags', structured_tag),
                         self.check('[0].identity.type', 'SystemAssigned')])

        self.cmd('appconfig show -n {config_store_name} -g {rg}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', premium_sku),
                         self.check('tags', structured_tag),
                         self.check('identity.type', 'SystemAssigned')])
        
        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        test_del_prefix = get_resource_name_prefix('MgmtTestdel')
        config_store_name = self.create_random_name(prefix=test_del_prefix, length=24)

        self.kwargs.update({
            'config_store_name': config_store_name
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection}')
        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        self.cmd('appconfig show-deleted -n {config_store_name}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('purgeProtectionEnabled', '{enable_purge_protection}')])

        deleted_stores = self.cmd('appconfig list-deleted').get_output_in_json()

        found = False
        for deleted_store in deleted_stores:
            if deleted_store['name'] == config_store_name:
                assert deleted_store['location'] == location
                found = True
                break
        assert found

        self.cmd('appconfig recover -n {config_store_name} -y')

        self.cmd('appconfig show -n {config_store_name}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}')])

        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        self.cmd('appconfig purge -n {config_store_name} -y')

        with self.assertRaisesRegex(CLIError, f'Failed to find the deleted App Configuration store \'{config_store_name}\'.'):
            self.cmd('appconfig show-deleted -n {config_store_name}')

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_local_auth(self, resource_group, location):
        disable_local_auth_prefix = get_resource_name_prefix('DisableLocalAuth')
        config_store_name = self.create_random_name(prefix=disable_local_auth_prefix, length=24)

        location = 'eastus'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'disable_local_auth': 'true',
            'retention_days': 1
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --disable-local-auth {disable_local_auth} --retention-days {retention_days}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('disableLocalAuth', True)])

        self.kwargs.update({
            'key': 'test',
            'disable_local_auth': 'false'
        })

        with self.assertRaisesRegex(CLIError, "Cannot find a read write access key for the App Configuration {}".format(config_store_name)):
            self.cmd('appconfig kv set --key {key} -n {config_store_name} -y')

        self.cmd('appconfig update -n {config_store_name} -g {rg} --disable-local-auth {disable_local_auth}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('disableLocalAuth', False)])

        self.cmd('appconfig kv set --key {key} -n {config_store_name} -y',
                 checks=[self.check('key', '{key}')])

    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_public_network_access(self, resource_group, location):
        pub_network_prefix = get_resource_name_prefix('PubNetworkTrue')
        config_store_name = self.create_random_name(prefix=pub_network_prefix, length=24)

        location = 'eastus'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'enable_public_network': 'true',
            'retention_days': 1
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --enable-public-network {enable_public_network} --retention-days {retention_days}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('publicNetworkAccess', 'Enabled')])

        pub_network_null_prefix = get_resource_name_prefix('PubNetworkNull')
        config_store_name = self.create_random_name(prefix=pub_network_null_prefix, length=24)

        self.kwargs.update({
            'config_store_name': config_store_name
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --retention-days {retention_days}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('publicNetworkAccess', None)])

        # Enable public network access with update command
        self.cmd('appconfig update -n {config_store_name} -g {rg} --enable-public-network',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('publicNetworkAccess', 'Enabled')])

def _setup_key_vault(test, kwargs):
    key_vault = test.cmd('keyvault create -n {keyvault_name} -g {rg} -l {rg_loc} --enable-rbac-authorization false --enable-purge-protection --retention-days 7').get_output_in_json()
    test.cmd('keyvault key create --vault-name {keyvault_name} -n {encryption_key}')
    test.cmd('keyvault set-policy -n {keyvault_name} --key-permissions get wrapKey unwrapKey --object-id {identity_id}')

    return key_vault

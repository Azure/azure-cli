# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import time
import datetime

location = 'WestUS'
seclocation = 'EastUS'
premium_sku = 'Premium'
basic_sku = 'Basic'
premium_size = 'P1'
basic_size = 'C0'
name_prefix = 'cliredis'
# These tests rely on an already existing user assigned managed identity. You will need to create it and paste the id below:
user_identity = '/subscriptions/6b9ac7d2-7f6d-4de4-962c-43fda44bc3f2/resourcegroups/kj-aad-testing/providers/Microsoft.ManagedIdentity/userAssignedIdentities/kj-aad-testing-mi'

class RedisCacheTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_with_mandatory_args(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': basic_sku,
            'size': basic_size
        }
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        self.cmd('az redis show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('sku.family', basic_size[0]),
            self.check('sku.capacity', basic_size[1:])
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_with_tags_and_zones(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': seclocation,
            'sku': premium_sku,
            'size': premium_size,
            'tags': "test=tryingzones",
            'zones': "1 2"
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size} --tags {tags} --zones {zones}')
        self.cmd('az redis show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('sku.family', premium_size[0]),
            self.check('sku.capacity', premium_size[1:]),
            self.check('tags.test', 'tryingzones'),
            self.check('length(zones)', 2)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_with_tlsversion_and_settings(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': basic_sku,
            'size': basic_size,
            'tls_version': '1.2',
            'tenant_settings': "hello=1"
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size} --minimum-tls-version {tls_version}  --tenant-settings {tenant_settings}')
        self.cmd('az redis show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('sku.family', basic_size[0]),
            self.check('sku.capacity', basic_size[1:]),
            self.check('minimumTlsVersion', '{tls_version}'),
            self.check('tenantSettings.hello', '1')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_with_redisversion(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': basic_sku,
            'size': basic_size,
            'redis_version': '6'
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size} --redis-version {redis_version}')
        result = self.cmd('az redis show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('sku.family', basic_size[0]),
            self.check('sku.capacity', basic_size[1:])
        ]).get_output_in_json()
        self.check(result['redisVersion'].split('.')[0], '{redis_version}')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_authentication(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': premium_sku,
            'size': premium_size,
            'redis-configuration-enable-aad': os.path.join(curr_dir, 'config_enable-aad.json').replace('\\', '\\\\'),
            'access-policy-name': "accessPolicy1",
            'permissions1': "\"+get +hget\"",
            'permissions2': "+get",
            'access-policy-assignment-name': "accessPolicyAssignmentName1",
            'object-id': "69d700c5-ca77-4335-947e-4f823dd00e1a",
            'object-id-alias1': "kj-aad-testing",
            'object-id-alias2': "aad-testing-app"
        }

        # Create aad enabled cache with access keys disabled
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size} --disable-access-keys true --redis-configuration @"{redis-configuration-enable-aad}"')
        result = self.cmd('az redis show -n {name} -g {rg}').get_output_in_json()
        
        # Verify cache is aad enabled and access keys disabled
        self.assertTrue(result['provisioningState'] == 'Succeeded')
        self.assertTrue(result['redisConfiguration']['aadEnabled'] == "true")
        self.assertTrue(result['disableAccessKeyAuthentication'])

        # List access polices
        result = self.cmd('az redis access-policy list -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(len(result) == 3)

        # Create access policy
        result = self.cmd('az redis access-policy create -n {name} -g {rg} --access-policy-name {access-policy-name} --permissions {permissions1}').get_output_in_json()
        self.assertTrue(result['name'] == self.kwargs['access-policy-name'])
        self.assertTrue(result['permissions'] == "+get +hget allkeys")

        # List access polices
        result = self.cmd('az redis access-policy list -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(len(result) == 4)

        # Update access policy
        result = self.cmd('az redis access-policy update -n {name} -g {rg} --access-policy-name {access-policy-name} --permissions {permissions2}').get_output_in_json()
        self.assertTrue(result['name'] == self.kwargs['access-policy-name'])
        self.assertTrue(result['permissions'] == "+get allkeys")

        # Get access policy
        result = self.cmd('az redis access-policy show -n {name} -g {rg} --access-policy-name {access-policy-name}').get_output_in_json()
        self.assertTrue(result['name'] == self.kwargs['access-policy-name'])
        self.assertTrue(result['permissions'] == "+get allkeys")

        # Create access policy assignment
        result = self.cmd('az redis access-policy-assignment create -n {name} -g {rg} --policy-assignment-name {access-policy-assignment-name} --access-policy-name {access-policy-name} --object-id {object-id} --object-id-alias {object-id-alias1}').get_output_in_json()
        self.assertTrue(result['name'] == self.kwargs['access-policy-assignment-name'])
        self.assertTrue(result['accessPolicyName'] == self.kwargs['access-policy-name'])
        self.assertTrue(result['objectId'] == self.kwargs['object-id'])
        self.assertTrue(result['objectIdAlias'] == self.kwargs['object-id-alias1'])

        # List access policy assignments
        result = self.cmd('az redis access-policy-assignment list -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(len(result) == 1)

        # Update access policy assignment
        result = self.cmd('az redis access-policy-assignment update -n {name} -g {rg} --policy-assignment-name {access-policy-assignment-name} --access-policy-name {access-policy-name} --object-id {object-id} --object-id-alias {object-id-alias2}').get_output_in_json()
        self.assertTrue(result['name'] == self.kwargs['access-policy-assignment-name'])
        self.assertTrue(result['accessPolicyName'] == self.kwargs['access-policy-name'])
        self.assertTrue(result['objectId'] == self.kwargs['object-id'])
        self.assertTrue(result['objectIdAlias'] == self.kwargs['object-id-alias2'])

        # Get access policy assignment
        result = self.cmd('az redis access-policy-assignment show -n {name} -g {rg} --policy-assignment-name {access-policy-assignment-name}').get_output_in_json()
        self.assertTrue(result['name'] == self.kwargs['access-policy-assignment-name'])
        self.assertTrue(result['accessPolicyName'] == self.kwargs['access-policy-name'])
        self.assertTrue(result['objectId'] == self.kwargs['object-id'])
        self.assertTrue(result['objectIdAlias'] == self.kwargs['object-id-alias2'])

        # Delete access policy assignment
        self.cmd('az redis access-policy-assignment delete -n {name} -g {rg} --policy-assignment-name {access-policy-assignment-name}')

        # List access policy assignments
        result = self.cmd('az redis access-policy-assignment list -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(len(result) == 0)

        # Delete access policy
        self.cmd('az redis access-policy delete -n {name} -g {rg} --access-policy-name {access-policy-name}')

        # List access polices
        result = self.cmd('az redis access-policy list -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(len(result) == 3)

        # Enable access keys on cache and verify
        self.cmd('az redis update -n {name} -g {rg} --set "disableAccessKeyAuthentication=false"')
        if self.is_live:
            time.sleep(30)
        result = self.cmd('az redis show -n {name} -g {rg}').get_output_in_json()
        self.assertFalse(result['disableAccessKeyAuthentication'])

        # Commenting out due to issues with tearing down test for update (need to provide exact sleep time for lro to complete)
        """
        # Disable aad on cache
        self.cmd('az redis update -n {name} -g {rg} --set redisConfiguration.aadEnabled=false --no-wait False')
        result = self.cmd('az redis show -n {name} -g {rg}').get_output_in_json()

        # Verify cache is aad disabled
        if self.is_live:
            while result['provisioningState'] == 'ConfiguringAAD':
                result = self.cmd('az redis show -n {name} -g {rg}').get_output_in_json()
                time.sleep(1)
        self.assertTrue(result['provisioningState'] == 'Succeeded')
        self.assertTrue(result['redisConfiguration']['aadEnabled'] == "False")
        """


    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_list_works(self, resource_group):
        self.cmd('az redis list')
        self.cmd('az redis list -g {rg}')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_list_keys(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': basic_sku,
            'size': basic_size
        }
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        result = self.cmd('az redis list-keys -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(result['primaryKey'] is not None)
        self.assertTrue(result['secondaryKey'] is not None)
        # TODO: self.cmd('az redis update -n {name} -g {rg} --set "tags.mytag=mytagval"')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_patch_schedule(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': 'eastus',
            'sku': premium_sku,
            'size': premium_size,
            'schedule_entries_one': "[{\\\"dayOfWeek\\\":\\\"Monday\\\",\\\"startHourUtc\\\":\\\"00\\\",\\\"maintenanceWindow\\\":\\\"PT5H\\\"}]",
            'schedule_entries_two': "[{\\\"dayOfWeek\\\":\\\"Tuesday\\\",\\\"startHourUtc\\\":\\\"01\\\",\\\"maintenanceWindow\\\":\\\"PT10H\\\"}]"
        }
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        self.cmd('az redis patch-schedule create -n {name} -g {rg} --schedule-entries {schedule_entries_one}', checks=[
            self.check('scheduleEntries[0].dayOfWeek', 'Monday'),
            self.check('scheduleEntries[0].maintenanceWindow', '5:00:00'),
            self.check('scheduleEntries[0].startHourUtc', '0')
        ])
        self.cmd('az redis patch-schedule update -n {name} -g {rg} --schedule-entries {schedule_entries_two}', checks=[
            self.check('scheduleEntries[0].dayOfWeek', 'Tuesday'),
            self.check('scheduleEntries[0].maintenanceWindow', '10:00:00'),
            self.check('scheduleEntries[0].startHourUtc', '1')
        ])
        self.cmd('az redis patch-schedule show -n {name} -g {rg}', checks=[
            self.check('scheduleEntries[0].dayOfWeek', 'Tuesday'),
            self.check('scheduleEntries[0].maintenanceWindow', '10:00:00'),
            self.check('scheduleEntries[0].startHourUtc', '1')
        ])
        self.cmd('az redis patch-schedule delete -n {name} -g {rg}')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_list_firewall_and_server_link_works(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': 'eastus',
            'sku': premium_sku,
            'size': premium_size
        }
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        self.cmd('az redis firewall-rules list -n {name} -g {rg}')
        self.cmd('az redis server-link list -n {name} -g {rg}')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_export_import(self, resource_group):
        randName = self.create_random_name(prefix=name_prefix, length=24)
        self.kwargs = {
            'rg': resource_group,
            'name': randName,
            'location': 'westus',
            'sku': premium_sku,
            'size': premium_size,
            'prefix': "redistest",
            'containersasURL': "https://####",
            'filesasURL': "https://####",
            'storageName': "str"+randName[:-3],
            'containerName': "testcontainer",
            'userIdentity': user_identity,
            'storageSubscriptionId': "6b9ac7d2-7f6d-4de4-962c-43fda44bc3f2",
            'startTime': (datetime.datetime.utcnow() - datetime.timedelta(minutes=60)).strftime(f"%Y-%m-%dT%H:%MZ"),
            'expiryTime': (datetime.datetime.utcnow() + datetime.timedelta(minutes=200)).strftime(f"%Y-%m-%dT%H:%MZ")
        }

        if self.is_live :
            storage = self.cmd('az storage account create -n {storageName} -g {rg} -l {location} --sku Standard_LRS').get_output_in_json()
            self.cmd('az storage container create -n {containerName} --account-name {storageName}')
            containersasToken = self.cmd('az storage container generate-sas -n {containerName} --account-name {storageName} --permissions dlrw --expiry {expiryTime} --start {startTime}').output
            containersasURL = storage['primaryEndpoints']['blob'] + self.kwargs['containerName'] + "?" + containersasToken[1:-2]
            filesasURL = storage['primaryEndpoints']['blob'] + self.kwargs['containerName'] + "/"+ self.kwargs["prefix"] + "?" + containersasToken[1:-2]
            self.kwargs['containersasURL'] = containersasURL
            self.kwargs['filesasURL'] = filesasURL
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        
        '''
        self.cmd('az redis export -n {name} -g {rg} --prefix {prefix} --container \'{containersasURL}\' --preferred-data-archive-auth-method SAS')
        if self.is_live:
            time.sleep(5 * 60)
        self.cmd('az redis import-method -n {name} -g {rg} --files "{filesasURL}" --preferred-data-archive-auth-method SAS')
        if self.is_live:
            time.sleep(5 * 60)
        self.cmd('az redis import -n {name} -g {rg} --files "{filesasURL}" --preferred-data-archive-auth-method SAS')
        if self.is_live:
            time.sleep(5 * 60)
        '''     
        # Test import/export with managed identity
        if self.is_live:
            # Setup storage account and cache with managed identity
            self.cmd('az redis identity assign -g {rg} -n {name} --mi-user-assigned {userIdentity}') 
            identities = self.cmd('az identity list').get_output_in_json()
            identity = list(filter(lambda x:x['id']==user_identity,identities))[0]
            principal_id = identity["principalId"]
            storage_id = self.cmd('az storage account show -g {rg} -n {storageName}').get_output_in_json()['id']
            self.cmd(f'az role assignment create --assignee-object-id {principal_id} --role "Storage Blob Data Contributor" --scope {storage_id}')
            #Remove SAS token from URLs (not necessary with managed identity)
            self.kwargs['containersasURL'] = self.kwargs['containersasURL'].split('?')[0]
            self.kwargs['filesasURL'] = self.kwargs['filesasURL'].split('?')[0]
        self.cmd('az redis export -n {name} -g {rg} --prefix {prefix} --container \'{containersasURL}\' --preferred-data-archive-auth-method ManagedIdentity --storage-subscription-id {storageSubscriptionId}')
        # TODO: un comment after July DP release
        # self.cmd('az redis import -n {name} -g {rg} --files {filesasURL} --preferred-data-archive-auth-method ManagedIdentity --storage-subscription-id {storageSubscriptionId}')

        self.cmd('az redis delete -n {name} -g {rg} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_firewall(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': premium_sku,
            'size': premium_size,
            'rulename': 'test'
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')


        self.cmd('az redis firewall-rules create -n {name} -g {rg} --start-ip 127.0.0.1 --end-ip 127.0.0.1 --rule-name {rulename}')
        self.cmd('az redis firewall-rules update -n {name} -g {rg} --start-ip 127.0.0.0 --end-ip 127.0.0.1 --rule-name {rulename}')
        self.cmd('az redis firewall-rules list -n {name} -g {rg}')
        self.cmd('az redis firewall-rules show -n {name} -g {rg} --rule-name {rulename}')
        self.cmd('az redis firewall-rules delete -n {name} -g {rg} --rule-name {rulename}')
        self.cmd('az redis delete -n {name} -g {rg} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_reboot(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': premium_sku,
            'size': premium_size
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')


        self.cmd('az redis force-reboot -n {name} -g {rg} --reboot-type AllNodes')
        if self.is_live:
            time.sleep(2 * 60)
        self.cmd('az redis force-reboot -n {name} -g {rg} --reboot-type PrimaryNode')
        if self.is_live:
            time.sleep(2 * 60)
        self.cmd('az redis force-reboot -n {name} -g {rg} --reboot-type SecondaryNode')
        if self.is_live:
            time.sleep(2 * 60)
        self.cmd('az redis delete -n {name} -g {rg} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_regenerate_key_update_tags(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': premium_sku,
            'size': premium_size
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')


        self.cmd('az redis regenerate-keys -n {name} -g {rg} --key-type Primary')
        self.cmd('az redis regenerate-keys -n {name} -g {rg} --key-type Secondary')
        # TODO: self.cmd('az redis update -n {name} -g {rg} --set "tags.mytag=mytagval"')
        self.cmd('az redis delete -n {name} -g {rg} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_managed_identity(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': basic_sku,
            'size': basic_size,
            'userIdentity': user_identity,
        }
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size} --mi-system-assigned --mi-user-assigned "{userIdentity}"', checks=[
            self.check('identity.type', 'SystemAssigned, UserAssigned'),
            self.check('length(identity.userAssignedIdentities)', 1)
        ])

        # TODO: self.cmd('az redis update -n {name} -g {rg} --set "publicNetworkAccess=Disabled"')
        if self.is_live:
            time.sleep(5*60)

        self.cmd('az redis identity remove -n {name} -g {rg} --mi-system-assigned --mi-user-assigned "{userIdentity}"',checks=[
            self.check('type', 'None')
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity assign -n {name} -g {rg} --mi-system-assigned',checks=[
            self.check('type', 'SystemAssigned'),
            self.check('userAssignedIdentities', None)
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity assign -n {name} -g {rg} --mi-user-assigned "{userIdentity}"',checks=[
            self.check('type', 'SystemAssigned, UserAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity remove -n {name} -g {rg} --mi-system-assigned',checks=[
            self.check('type', 'UserAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity assign -n {name} -g {rg} --mi-system-assigned',checks=[
            self.check('type', 'SystemAssigned, UserAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity remove -n {name} -g {rg} --mi-system-assigned',checks=[
            self.check('type', 'UserAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity remove -n {name} -g {rg} --mi-user-assigned "{userIdentity}"',checks=[
            self.check('type', 'None')
        ])

        self.cmd('az redis identity show -n {name} -g {rg}',checks=[
            self.check('type', 'None')
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity assign -n {name} -g {rg} --mi-system-assigned',checks=[
            self.check('type', 'SystemAssigned'),
            self.check('userAssignedIdentities', None)
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity remove -n {name} -g {rg} --mi-system-assigned',checks=[
            self.check('type', 'None')
        ])

        if self.is_live:
            time.sleep(30)

        self.cmd('az redis identity assign -n {name} -g {rg} --mi-system-assigned --mi-user-assigned "{userIdentity}"',checks=[
            self.check('type', 'SystemAssigned, UserAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])

        self.cmd('az redis identity show -n {name} -g {rg}',checks=[
            self.check('type', 'SystemAssigned, UserAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])


    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_server_link(self, resource_group):

        name = self.create_random_name(prefix=name_prefix, length=24)
        self.kwargs = {
            'rg': resource_group,
            'name': name,
            'secname': name + 'sec',
            'location': location,
            'seclocation': seclocation,
            'sku': premium_sku,
            'size': premium_size
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        self.cmd('az redis create -n {secname} -g {rg} -l {seclocation} --sku {sku} --vm-size {size}')

        self.cmd('az redis server-link create -n {name} -g {rg} --replication-role Secondary --server-to-link {secname}',checks=[
            self.check('provisioningState','Succeeded'),
            self.exists('geoReplicatedPrimaryHostName'),
            self.exists('primaryHostName')
        ])
        if self.is_live:
            time.sleep(5 * 60)
        self.cmd('az redis server-link list -n {name} -g {rg}')
        self.cmd('az redis server-link show -n {name} -g {rg} --linked-server-name {secname}')
        self.cmd('az redis server-link delete -n {name} -g {rg} --linked-server-name {secname}')
        if self.is_live:
            time.sleep(5 * 60)
        
        self.cmd('az redis server-link list -n {name} -g {rg}',checks=[self.is_empty()])
        self.cmd('az redis delete -n {name} -g {rg} -y')
        self.cmd('az redis delete -n {secname} -g {rg} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_update(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': premium_sku,
            'size': premium_size
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        if self.is_live:
            time.sleep(5*60)
        # TODO: self.cmd('az redis update -n {name} -g {rg} --set "publicNetworkAccess=Disabled"')
        if self.is_live:
            time.sleep(5*60)
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_flush(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': premium_sku,
            'size': premium_size
        }
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')
        result = self.cmd('az redis flush -g {rg} -n {name} -y').get_output_in_json()
        assert result['status'] == 'Succeeded'

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_update_channel(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': basic_sku,
            'size': basic_size
        }

        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size} --update-channel Preview')
        if self.is_live:
            time.sleep(5*60)
        # Commenting out due to issues with tearing down test for update (need to provide exact sleep time for lro to complete)
        '''
        self.cmd('az redis update -n {name} -g {rg} --set "RedisVersion=6.0" "UpdateChannel=Preview"')
        if self.is_live:
            time.sleep(5*60)
        '''
        result = self.cmd('az redis show -n {name} -g {rg}').get_output_in_json()
        assert result['updateChannel'] == 'Preview'
        
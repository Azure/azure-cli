# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import time
import datetime

location = 'WestUS2'
seclocation = 'EastUS'
premium_sku = 'Premium'
basic_sku = 'Basic'
premium_size = 'P1'
basic_size = 'C0'
name_prefix = 'cliredis'


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
            'location': location,
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
        self.cmd('az redis update -n {name} -g {rg} --set "tags.mytag=mytagval"')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_patch_schedule(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
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
            'location': location,
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
            'location': location,
            'sku': premium_sku,
            'size': premium_size,
            'prefix': "redistest",
            'containersasURL': "https://####",
            'filesasURL': "https://####",
            'storageName': "str"+randName[:-3],
            'containerName': "testcontainer",
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


        self.cmd('az redis export -n {name} -g {rg} --prefix {prefix} --container \'{containersasURL}\'')
        if self.is_live:
            time.sleep(5 * 60)
        self.cmd('az redis import-method -n {name} -g {rg} --files "{filesasURL}"')
        if self.is_live:
            time.sleep(5 * 60)
        self.cmd('az redis import -n {name} -g {rg} --files "{filesasURL}"')
        if self.is_live:
            time.sleep(5 * 60)
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
        self.cmd('az redis update -n {name} -g {rg} --set "tags.mytag=mytagval"')
        self.cmd('az redis delete -n {name} -g {rg} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache_managed_identity(self, resource_group):
        self.kwargs = {
            'rg': resource_group,
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'location': location,
            'sku': basic_sku,
            'size': basic_size,
            'userIdentity': "/subscriptions/0ee2a145-4d40-44f4-b764-67b40274f1ac/resourcegroups/prn-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/test",
        }
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size} --mi-system-assigned --mi-user-assigned "{userIdentity}"', checks=[
            self.check('identity.type', 'SystemAssigned, UserAssigned'),
            self.check('length(identity.userAssignedIdentities)', 1)
        ])

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

        self.cmd('az redis server-link create -n {name} -g {rg} --replication-role Secondary --server-to-link {secname}')
        if self.is_live:
            time.sleep(5 * 60)
        self.cmd('az redis server-link list -n {name} -g {rg}')
        self.cmd('az redis server-link show -n {name} -g {rg} --linked-server-name {secname}')
        self.cmd('az redis server-link delete -n {name} -g {rg} --linked-server-name {secname}')
        if self.is_live:
            time.sleep(5 * 60)
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
        self.cmd('az redis update -n {name} -g {rg} --set "publicNetworkAccess=Disabled"', checks=[
            self.check("publicNetworkAccess","Disabled")
        ])
        self.cmd('az redis create -n {name} -g {rg} -l {location} --sku {sku} --vm-size {size}')

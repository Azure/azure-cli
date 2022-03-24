# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import os

from azure.core.exceptions import ResourceNotFoundError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse, live_only
from azure.cli.core.util import CLIError
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    JMESPathCheckGreaterThan,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StorageAccountPreparer,
    KeyVaultPreparer,
    LiveScenarioTest,
    record_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from azure.cli.command_modules.sql.custom import (
    ClientAuthenticationType,
    ClientType,
    ComputeModelType,
    ResourceIdType)
from datetime import datetime, timedelta
from time import sleep

# Constants
server_name_prefix = 'clitestserver'
server_name_max_length = 62
managed_instance_name_prefix = 'clitestmi'
instance_pool_name_prefix = 'clitestip'
managed_instance_name_max_length = 20


class SqlServerPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix=server_name_prefix, parameter_name='server', location='westus',
                 admin_user='admin123', admin_password='SecretPassword123',
                 resource_group_parameter_name='resource_group', skip_delete=True):
        super(SqlServerPreparer, self).__init__(name_prefix, server_name_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az sql server create -l {} -g {} -n {} -u {} -p {}'
        execute(DummyCli(), template.format(self.location, group, name, self.admin_user, self.admin_password))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute(DummyCli(), 'az sql server delete -g {} -n {} --yes --no-wait'.format(group, name))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a sql server account a resource group is required. Please add ' \
                       'decorator @{} in front of this storage account preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


class ManagedInstancePreparer(AbstractPreparer, SingleValueReplacer):
    subscription_id = '8313371e-0879-428e-b1da-6353575a9192'
    group = 'CustomerExperienceTeam_RG'
    location = 'westcentralus'
    vnet_name = 'vnet-mi-tooling'
    subnet_name = 'ManagedInstance'
    subnet = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(subscription_id, group, vnet_name, subnet_name)

    # For cross-subnet update SLO, we need a target subnet to move managed instance to.
    target_vnet_name = 'vnet-mi-tooling'
    target_subnet_name = 'ManagedInstance2'
    target_subnet = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(subscription_id, group, target_vnet_name, target_subnet_name)
    target_subnet_vcores = 4
    
    collation = "Serbian_Cyrillic_100_CS_AS"

    licence = 'LicenseIncluded'
    v_core = 4
    storage = 32
    edition = 'GeneralPurpose'
    family = 'Gen5'
    proxy = 'Proxy'

    fog_name = "fgtest2022a"
    primary_name = 'mi-primary-wcus'
    secondary_name = 'mi-mdcs-cx-secondary'
    sec_group = 'mdcs-cx-secondary-vnet'
    sec_location = 'centralus'
    sec_subnet = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/vnet-sql-mi-secondary/subnets/default'.format(subscription_id, sec_group)

    def __init__(self, name_prefix=managed_instance_name_prefix, parameter_name='mi', admin_user='admin123',
                 minimalTlsVersion='', user_assigned_identity_id='', identity_type='', pid='', otherParams='',
                 admin_password='SecretPassword123SecretPassword', public=True, tags='', is_geo_secondary=False,
                 skip_delete=False):
        super(ManagedInstancePreparer, self).__init__(name_prefix, server_name_max_length)
        self.parameter_name = parameter_name
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.public = public
        self.skip_delete = skip_delete
        self.tags = tags
        self.minimalTlsVersion = minimalTlsVersion
        self.identityType = identity_type
        self.userAssignedIdentityId = user_assigned_identity_id
        self.pid = pid
        self.otherParams = otherParams
        self.is_geo_secondary = is_geo_secondary

    def create_resource(self, name, **kwargs):
        location = self.location
        subnet = self.subnet
        v_core = self.v_core

        template = 'az sql mi create -g {} -n {} -l {} -u {} -p {} --subnet {} --license-type {}' \
                   ' --collation {} --capacity {} --storage {} --edition {} --family {} --tags {}' \
                   ' --proxy-override {} --bsr Geo'

        if self.public:
            template += ' --public-data-endpoint-enabled'

        if self.minimalTlsVersion:
            template += f" --minimal-tls-version {self.minimalTlsVersion}"

        if self.identityType == ResourceIdType.system_assigned_user_assigned.value or self.identityType == ResourceIdType.user_assigned.value:
            template += f" --assign-identity --user-assigned-identity-id {self.userAssignedIdentityId} --identity-type {self.identityType} --pid {self.pid}"

        if self.identityType == ResourceIdType.system_assigned.value:
            template += f" --assign-identity"

        if self.otherParams:
            template += f" {self.otherParams}"

        if self.is_geo_secondary:
            location = self.sec_location
            subnet = self.sec_subnet
            v_core = 4

        execute(DummyCli(), template.format(
            self.group, name, location,
            self.admin_user, self.admin_password,
            subnet, self.licence, self.collation,
            v_core, self.storage, self.edition,
            self.family, self.tags, self.proxy))
        return {self.parameter_name: name, 'rg': self.group}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            try:
                execute(DummyCli(), 'az sql mi delete -g {} -n {} --yes --no-wait'.format(self.group, name))
            except ResourceNotFoundError:
                pass


class SqlServerMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(parameter_name='resource_group_1', location='westeurope')
    @ResourceGroupPreparer(parameter_name='resource_group_2', location='westeurope')
    def test_sql_server_mgmt(self, resource_group_1, resource_group_2, resource_group_location):
        server_name_1 = self.create_random_name(server_name_prefix, server_name_max_length)
        server_name_2 = self.create_random_name(server_name_prefix, server_name_max_length)
        server_name_3 = self.create_random_name(server_name_prefix, server_name_max_length)

        admin_login = 'admin123'
        admin_passwords = ['SecretPassword123', 'SecretPassword456', 'SecretPassword789']
        federated_client_id_1 = '748eaea0-6dbc-4be9-a50b-6a2d3dad00d4'
        federated_client_id_2 = '17deee33-9da7-40ce-a33c-8a96f2f8f07d'
        federated_client_id_3 = '00000000-0000-0000-0000-000000000000'

        # test create sql server with minimal required parameters
        server_1 = self.cmd('sql server create -g {} --name {} '
                            '--admin-user {} --admin-password {}'
                            .format(resource_group_1, server_name_1, admin_login, admin_passwords[0]),
                            checks=[
                                JMESPathCheck('name', server_name_1),
                                JMESPathCheck('location', resource_group_location),
                                JMESPathCheck('resourceGroup', resource_group_1),
                                JMESPathCheck('administratorLogin', admin_login),
                                JMESPathCheck('identity', None)]).get_output_in_json()

        # test list sql server should be 1
        self.cmd('sql server list -g {}'.format(resource_group_1), checks=[JMESPathCheck('length(@)', 1)])

        # test update sql server
        self.cmd('sql server update -g {} --name {} --admin-password {} -i'
                 .format(resource_group_1, server_name_1, admin_passwords[1]),
                 checks=[
                     JMESPathCheck('name', server_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('identity.type', 'SystemAssigned')])

        # test update without identity parameter, validate identity still exists
        # also use --id instead of -g/-n
        self.cmd('sql server update --ids {} --admin-password {}'
                 .format(server_1['id'], admin_passwords[0]),
                 checks=[
                     JMESPathCheck('name', server_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('identity.type', 'SystemAssigned')])

        # test create another sql server, with identity this time
        self.cmd('sql server create -g {} --name {} -l {} -i '
                 '--admin-user {} --admin-password {}'
                 .format(resource_group_2, server_name_2, resource_group_location, admin_login, admin_passwords[0]),
                 checks=[
                     JMESPathCheck('name', server_name_2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group_2),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('identity.type', 'SystemAssigned')])

        # test list sql server in that group should be 1
        self.cmd('sql server list -g {}'.format(resource_group_2), checks=[JMESPathCheck('length(@)', 1)])

        # test list sql server in the subscription should be at least 2
        self.cmd('sql server list', checks=[JMESPathCheckGreaterThan('length(@)', 1)])

        # test show sql server
        self.cmd('sql server show -g {} --name {}'
                 .format(resource_group_1, server_name_1),
                 checks=[
                     JMESPathCheck('name', server_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('sql server show --id {}'
                 .format(server_1['id']),
                 checks=[
                     JMESPathCheck('name', server_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('sql server list-usages -g {} -n {}'
                 .format(resource_group_1, server_name_1),
                 checks=[JMESPathCheck('[0].resourceName', server_name_1)])

        # test delete sql server
        self.cmd('sql server delete --id {} --yes'
                 .format(server_1['id']), checks=NoneCheck())
        self.cmd('sql server delete -g {} --name {} --yes'
                 .format(resource_group_2, server_name_2), checks=NoneCheck())

        # test list sql server should be 0
        self.cmd('sql server list -g {}'.format(resource_group_1), checks=[NoneCheck()])

        # test create third sql server, with identity and federated client id
        self.cmd('sql server create -g {} --name {} -l {} -i '
                 '--admin-user {} --admin-password {} --federated-client-id {}'
                 .format(resource_group_1, server_name_3, resource_group_location, admin_login, admin_passwords[0], federated_client_id_1),
                 checks=[
                     JMESPathCheck('name', server_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('identity.type', 'SystemAssigned'),
                     JMESPathCheck('federatedClientId', federated_client_id_1)])
        
        self.cmd('sql server show -g {} --name {}'
                 .format(resource_group_1, server_name_3),
                 checks=[
                     JMESPathCheck('name', server_name_3),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('federatedClientId', federated_client_id_1)])

        # test update sql server's federated client id
        self.cmd('sql server update -g {} --name {} --admin-password {} --federated-client-id {} -i'
                 .format(resource_group_1, server_name_3, admin_passwords[2], federated_client_id_2),
                 checks=[
                     JMESPathCheck('name', server_name_3),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('federatedClientId', federated_client_id_2)])

        # test update sql server's federated client id to empty guid
        self.cmd('sql server update -g {} --name {} --admin-password {} --federated-client-id {} -i'
                 .format(resource_group_1, server_name_3, admin_passwords[2], federated_client_id_3),
                 checks=[
                     JMESPathCheck('name', server_name_3),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('federatedClientId', None)])
                     
        # delete sql server
        self.cmd('sql server delete -g {} --name {} --yes'
                 .format(resource_group_1, server_name_3), checks=NoneCheck())

    @ResourceGroupPreparer(parameter_name='resource_group_1', location='westeurope')
    def test_sql_server_public_network_access_create_mgmt(self, resource_group_1, resource_group_location):
        server_name_1 = self.create_random_name(server_name_prefix, server_name_max_length)
        server_name_2 = self.create_random_name(server_name_prefix, server_name_max_length)
        server_name_3 = self.create_random_name(server_name_prefix, server_name_max_length)
        admin_login = 'admin123'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']

        # test create sql server with no enable-public-network passed in, verify publicNetworkAccess == Enabled
        self.cmd('sql server create -g {} --name {} '
                 '--admin-user {} --admin-password {}'
                 .format(resource_group_1, server_name_1, admin_login, admin_passwords[0]),
                 checks=[
                     JMESPathCheck('name', server_name_1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('publicNetworkAccess', 'Enabled')])

        # test create sql server with enable-public-network == true passed in, verify publicNetworkAccess == Enabled
        self.cmd('sql server create -g {} --name {} '
                 '--admin-user {} --admin-password {} --enable-public-network {}'
                 .format(resource_group_1, server_name_2, admin_login, admin_passwords[0], 'true'),
                 checks=[
                     JMESPathCheck('name', server_name_2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('publicNetworkAccess', 'Enabled')])

        # test create sql server with enable-public-network == false passed in, verify publicNetworkAccess == Disabled
        #   note: although server does not have private links, creating server with disabled public network is allowed
        self.cmd('sql server create -g {} --name {} '
                 '--admin-user {} --admin-password {} -e {}'
                 .format(resource_group_1, server_name_3, admin_login, admin_passwords[0], 'false'),
                 checks=[
                     JMESPathCheck('name', server_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('publicNetworkAccess', 'Disabled')])

        # test get sql server to verify publicNetworkAccess == 'Disabled' for the above server as expected
        #   note: although server does not have private links, creating server with disabled public network is allowed
        self.cmd('sql server show -g {} --name {}'
                 .format(resource_group_1, server_name_3),
                 checks=[
                     JMESPathCheck('name', server_name_3),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('publicNetworkAccess', 'Disabled')])

    @ResourceGroupPreparer(parameter_name='resource_group', location='westeurope')
    def test_sql_server_public_network_access_update_mgmt(self, resource_group, resource_group_location):
        server_name = self.create_random_name(server_name_prefix, server_name_max_length)
        server_name_2 = self.create_random_name(server_name_prefix, server_name_max_length)
        admin_login = 'admin123'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']

        # test create sql server with no enable-public-network passed in, verify publicNetworkAccess == Enabled
        self.cmd('sql server create -g {} --name {} --admin-user {} --admin-password {}'
                 .format(resource_group, server_name, admin_login, admin_passwords[0]),
                 checks=[
                     JMESPathCheck('name', server_name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('publicNetworkAccess', 'Enabled')])

        # test update sql server with enable-public-network == false passed in, verify publicNetworkAccess == Disabled
        #   note: we test for exception thrown here since this server does not have private links so updating server
        #         to disable public network access will throw an error
        try:
            self.cmd('sql server update -g {} -n {} --enable-public-network {}'
                     .format(resource_group, server_name, 'false'))
        except Exception as e:
            expectedmessage = "Unable to set Deny Public Network Access to Yes since there is no private endpoint enabled to access the server"
            if expectedmessage in str(e):
                pass

        # test create sql server with enable-public-network == false passed in, verify publicNetworkAccess == Disabled
        #   note: although server does not have private links, creating server with disabled public network is allowed
        self.cmd('sql server create -g {} --name {} '
                 '--admin-user {} --admin-password {} -e {}'
                 .format(resource_group, server_name_2, admin_login, admin_passwords[0], 'false'),
                 checks=[
                     JMESPathCheck('name', server_name_2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('publicNetworkAccess', 'Disabled')])

        # test update sql server with no enable-public-network passed in, verify publicNetworkAccess == Disabled
        #   note: we test for exception thrown here since this server does not have private links so updating server
        #         to disable public network access will throw an error
        try:
            self.cmd('sql server update -g {} -n {} -i'
                     .format(resource_group, server_name_2))
        except Exception as e:
            expectedmessage = "Unable to set Deny Public Network Access to Yes since there is no private endpoint enabled to access the server"
            if expectedmessage in str(e):
                pass

        # test update sql server with enable-public-network == true passed in, verify publicNetworkAccess == Enabled
        self.cmd('sql server update -g {} -n {} -e {}'
                 .format(resource_group, server_name_2, 'true'),
                 checks=[
                     JMESPathCheck('name', server_name_2),
                     JMESPathCheck('publicNetworkAccess', 'Enabled')])


class SqlServerFirewallMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlServerPreparer(location='eastus')
    def test_sql_firewall_mgmt(self, resource_group, resource_group_location, server):
        firewall_rule_1 = 'rule1'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '255.255.255.255'
        firewall_rule_2 = 'rule2'
        start_ip_address_2 = '123.123.123.123'
        end_ip_address_2 = '123.123.123.124'
        # allow_all_azure_ips_rule = 'AllowAllAzureIPs'
        # allow_all_azure_ips_address = '0.0.0.0'

        # test sql server firewall-rule create
        fw_rule_1 = self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                             '--start-ip-address {} --end-ip-address {}'
                             .format(firewall_rule_1, resource_group, server,
                                     start_ip_address_1, end_ip_address_1),
                             checks=[
                                 JMESPathCheck('name', firewall_rule_1),
                                 JMESPathCheck('resourceGroup', resource_group),
                                 JMESPathCheck('startIpAddress', start_ip_address_1),
                                 JMESPathCheck('endIpAddress', end_ip_address_1)]).get_output_in_json()

        # test sql server firewall-rule show by group/server/name
        self.cmd('sql server firewall-rule show --name {} -g {} --server {}'
                 .format(firewall_rule_1, resource_group, server),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule show by id
        self.cmd('sql server firewall-rule show --id {}'
                 .format(fw_rule_1['id']),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule update by group/server/name
        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, resource_group, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test sql server firewall-rule update by id
        self.cmd('sql server firewall-rule update --id {} '
                 '--start-ip-address {}'
                 .format(fw_rule_1['id'], start_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--end-ip-address {}'
                 .format(firewall_rule_1, resource_group, server,
                         end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule create another rule
        self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_2, resource_group, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test sql server firewall-rule list
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(resource_group, server), checks=[JMESPathCheck('length(@)', 2)])

        # # test sql server firewall-rule create azure ip rule
        # self.cmd('sql server firewall-rule allow-all-azure-ips -g {} --server {} '
        #          .format(resource_group, server), checks=[
        #                      JMESPathCheck('name', allow_all_azure_ips_rule),
        #                      JMESPathCheck('resourceGroup', resource_group),
        #                      JMESPathCheck('startIpAddress', allow_all_azure_ips_address),
        #                      JMESPathCheck('endIpAddress', allow_all_azure_ips_address)])

        # # test sql server firewall-rule list
        # self.cmd('sql server firewall-rule list -g {} --server {}'
        #          .format(resource_group, server), checks=[JMESPathCheck('length(@)', 3)])

        # test sql server firewall-rule delete
        self.cmd('sql server firewall-rule delete --id {}'
                 .format(fw_rule_1['id']), checks=NoneCheck())
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(resource_group, server), checks=[JMESPathCheck('length(@)', 1)])

        self.cmd('sql server firewall-rule delete --name {} -g {} --server {}'
                 .format(firewall_rule_2, resource_group, server), checks=NoneCheck())
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(resource_group, server), checks=[NoneCheck()])


class SqlServerOutboundFirewallMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    @SqlServerPreparer(location='eastus')
    def test_sql_outbound_firewall_mgmt(self, resource_group, resource_group_location, server):
        outbound_firewall_rule_allowed_fqdn_1 = 'testOBFR1'
        outbound_firewall_rule_allowed_fqdn_2 = 'testOBFR2'

        # test sql server outbound-firewall-rule create
        self.cmd('sql server outbound-firewall-rule create -g {} --server {} --outbound-rule-fqdn {}'
                 .format(resource_group, server, outbound_firewall_rule_allowed_fqdn_1),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', outbound_firewall_rule_allowed_fqdn_1)])

        # test sql server outbound-firewall-rule show by group/server/name
        self.cmd('sql server outbound-firewall-rule show -g {} --server {} --outbound-rule-fqdn {}'
                 .format(resource_group, server, outbound_firewall_rule_allowed_fqdn_1),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', outbound_firewall_rule_allowed_fqdn_1)])

        # test sql server outbound-firewall-rule create another rule
        self.cmd('sql server outbound-firewall-rule create -g {} --server {} --outbound-rule-fqdn {}'
                 .format(resource_group, server, outbound_firewall_rule_allowed_fqdn_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', outbound_firewall_rule_allowed_fqdn_2)])

        # test sql server outbound-firewall-rule list
        self.cmd('sql server outbound-firewall-rule list -g {} --server {}'
                 .format(resource_group, server), checks=[JMESPathCheck('length(@)', 2)])

        # test sql server outbound-firewall-rule delete
        self.cmd('sql server outbound-firewall-rule delete -g {} --server {} --outbound-rule-fqdn {}'
                 .format(resource_group, server, outbound_firewall_rule_allowed_fqdn_2), checks=NoneCheck())
        self.cmd('sql server outbound-firewall-rule list -g {} --server {}'
                 .format(resource_group, server), checks=[JMESPathCheck('length(@)', 1)])


class SqlServerDbMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus2')
    @SqlServerPreparer(location='eastus2')
    def test_sql_db_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"
        database_name_2 = "cliautomationdb02"
        database_name_3 = "cliautomationdb03"
        update_service_objective = 'P1'
        update_storage = '10GB'
        update_storage_bytes = str(10 * 1024 * 1024 * 1024)
        read_scale_disabled = 'Disabled'
        read_scale_enabled = 'Enabled'
        backup_storage_redundancy_local = 'local'
        backup_storage_redundancy_zone = 'zone'

        # test sql db commands
        db1 = self.cmd('sql db create -g {} --server {} --name {} --read-scale {} --backup-storage-redundancy {} --yes'
                       .format(resource_group, server, database_name, read_scale_disabled,
                               backup_storage_redundancy_local),
                       checks=[
                           JMESPathCheck('resourceGroup', resource_group),
                           JMESPathCheck('name', database_name),
                           JMESPathCheck('location', resource_group_location),
                           JMESPathCheck('elasticPoolId', None),
                           JMESPathCheck('status', 'Online'),
                           JMESPathCheck('zoneRedundant', False),
                           JMESPathCheck('readScale', 'Disabled'),
                           JMESPathCheck('highAvailabilityReplicaCount', None),
                           JMESPathCheck('requestedBackupStorageRedundancy', 'Local')]).get_output_in_json()

        self.cmd('sql db list -g {} --server {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('length(@)', 2),
                     JMESPathCheck('sort([].name)', sorted([database_name, 'master'])),
                     JMESPathCheck('[0].resourceGroup', resource_group),
                     JMESPathCheck('[1].resourceGroup', resource_group)])

        self.cmd('sql db list-usages -g {} --server {} --name {}'
                 .format(resource_group, server, database_name),
                 checks=[JMESPathCheck('[0].resourceGroup', resource_group)])

        # Show by group/server/name
        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group)])

        # Show by id
        self.cmd('sql db show --id {}'
                 .format(db1['id']),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group)])

        # Update by group/server/name
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {} --max-size {} --read-scale {}'
                 ' --set tags.key1=value1 --backup-storage-redundancy {}'
                 .format(resource_group, server, database_name,
                         update_service_objective, update_storage,
                         read_scale_enabled, backup_storage_redundancy_zone),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('requestedServiceObjectiveName', update_service_objective),
                     JMESPathCheck('maxSizeBytes', update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1'),
                     JMESPathCheck('readScale', 'Enabled'),
                     JMESPathCheck('highAvailabilityReplicaCount', None)])

        # Update by id
        self.cmd('sql db update --id {} --set tags.key2=value2'
                 .format(db1['id']),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('requestedServiceObjectiveName', update_service_objective),
                     JMESPathCheck('maxSizeBytes', update_storage_bytes),
                     JMESPathCheck('tags.key2', 'value2')])

        # Rename by group/server/name
        db2 = self.cmd('sql db rename -g {} -s {} -n {} --new-name {}'
                       .format(resource_group, server, database_name, database_name_2),
                       checks=[
                           JMESPathCheck('resourceGroup', resource_group),
                           JMESPathCheck('name', database_name_2)]).get_output_in_json()

        # Rename by id
        db3 = self.cmd('sql db rename --id {} --new-name {}'
                       .format(db2['id'], database_name_3),
                       checks=[
                           JMESPathCheck('resourceGroup', resource_group),
                           JMESPathCheck('name', database_name_3)]).get_output_in_json()

        # Delete by group/server/name
        self.cmd('sql db delete -g {} --server {} --name {} --yes'
                 .format(resource_group, server, database_name_3),
                 checks=[NoneCheck()])

        # Delete by id
        self.cmd('sql db delete --id {} --yes'
                 .format(db3['id']),
                 checks=[NoneCheck()])

    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    @AllowLargeResponse()
    def test_sql_db_vcore_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"

        # Create database with vcore edition
        vcore_edition = 'GeneralPurpose'
        self.cmd('sql db create -g {} --server {} --name {} --edition {}'
                 .format(resource_group, server, database_name, vcore_edition),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition)])

        # Update database to dtu edition
        dtu_edition = 'Standard'
        dtu_capacity = 10
        self.cmd('sql db update -g {} --server {} --name {} --edition {} --capacity {} --max-size 250GB'
                 .format(resource_group, server, database_name, dtu_edition, dtu_capacity),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', dtu_edition),
                     JMESPathCheck('sku.tier', dtu_edition),
                     JMESPathCheck('sku.capacity', dtu_capacity)])

        # Update database back to vcore edition
        vcore_family = 'Gen5'
        vcore_capacity = 4
        self.cmd('sql db update -g {} --server {} --name {} -e {} -c {} -f {}'
                 .format(resource_group, server, database_name, vcore_edition,
                         vcore_capacity, vcore_family),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('sku.capacity', vcore_capacity),
                     JMESPathCheck('sku.family', vcore_family)])

        # Update only family
        vcore_family_updated = 'Gen5'

        # Update only capacity
        vcore_capacity_updated = 8
        self.cmd('sql db update -g {} -s {} -n {} --capacity {}'
                 .format(resource_group, server, database_name, vcore_capacity_updated),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('sku.capacity', vcore_capacity_updated),
                     JMESPathCheck('sku.family', vcore_family_updated)])

        # Update only edition
        vcore_edition_updated = 'BusinessCritical'
        self.cmd('sql db update -g {} -s {} -n {} --tier {}'
                 .format(resource_group, server, database_name, vcore_edition_updated),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition_updated),
                     JMESPathCheck('sku.tier', vcore_edition_updated),
                     JMESPathCheck('sku.capacity', vcore_capacity_updated),
                     JMESPathCheck('sku.family', vcore_family_updated)])

        # Create database with vcore edition and all sku properties specified
        database_name_2 = 'cliautomationdb02'
        vcore_edition = 'GeneralPurpose'
        self.cmd('sql db create -g {} --server {} --name {} -e {} -c {} -f {}'
                 .format(resource_group, server, database_name_2,
                         vcore_edition_updated, vcore_capacity_updated,
                         vcore_family_updated),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_2),
                     JMESPathCheck('edition', vcore_edition_updated),
                     JMESPathCheck('sku.tier', vcore_edition_updated),
                     JMESPathCheck('sku.capacity', vcore_capacity_updated),
                     JMESPathCheck('sku.family', vcore_family_updated)])

    @ResourceGroupPreparer(name_prefix='clitest-sql', location='eastus2')
    @SqlServerPreparer(name_prefix='clitest-sql', location='eastus2')
    @AllowLargeResponse()
    def test_sql_db_read_replica_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"

        # Create database with Hyperscale edition
        edition = 'Hyperscale'
        family = 'Gen5'
        capacity = 2
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {} --ha-replicas {}'
                 .format(resource_group, server, database_name, edition, family, capacity, 4),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('readScale', 'Enabled'),
                     JMESPathCheck('highAvailabilityReplicaCount', '4')])

        # Increase read replicas
        self.cmd('sql db update -g {} --server {} --name {} --read-replicas {}'
                 .format(resource_group, server, database_name, 3),
                 checks=[
                     JMESPathCheck('readScale', 'Enabled'),
                     JMESPathCheck('highAvailabilityReplicaCount', '3')])

        # Decrease read replicas
        self.cmd('sql db update -g {} --server {} --name {} --read-replicas {}'
                 .format(resource_group, server, database_name, 0),
                 checks=[
                     JMESPathCheck('readScale', 'Disabled'),
                     JMESPathCheck('highAvailabilityReplicaCount', '0')])

        # Alternate syntax
        self.cmd('sql db update -g {} --server {} --name {} --ha-replicas {}'
                 .format(resource_group, server, database_name, 2),
                 checks=[
                     JMESPathCheck('readScale', 'Enabled'),
                     JMESPathCheck('highAvailabilityReplicaCount', '2')])

    @ResourceGroupPreparer(location='westcentralus')
    @SqlServerPreparer(location='westcentralus')
    def test_sql_db_ledger(self, resource_group, resource_group_location, server):
        database_name_one = "cliautomationdb01"
        database_name_two = "cliautomationdb02"

        # test sql db is created with ledger off by default
        self.cmd('sql db create -g {} --server {} --name {} --yes'
                 .format(resource_group, server, database_name_one),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_one),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('ledgerOn', False)])

        self.cmd('sql db show -g {} -s {} --name {}'
                 .format(resource_group, server, database_name_one),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_one),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('ledgerOn', False)])

        # test sql db with ledger on
        self.cmd('sql db create -g {} --server {} --name {} --ledger-on --yes'
                 .format(resource_group, server, database_name_two),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_two),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('ledgerOn', True)])

        self.cmd('sql db show -g {} -s {} --name {}'
                 .format(resource_group, server, database_name_two),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_two),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('ledgerOn', True)])


class SqlServerServerlessDbMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    @AllowLargeResponse()
    def test_sql_db_serverless_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"
        compute_model_serverless = ComputeModelType.serverless
        compute_model_provisioned = ComputeModelType.provisioned

        # Create database with vcore edition
        vcore_edition = 'GeneralPurpose'
        self.cmd('sql db create -g {} --server {} --name {} --edition {}'
                 .format(resource_group, server, database_name, vcore_edition),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition)])

        # Update database to serverless offering
        self.cmd('sql db update -g {} --server {} --name {} --compute-model {}'
                 .format(resource_group, server, database_name, compute_model_serverless),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('sku.name', 'GP_S_Gen5')])

        # Update auto pause delay and min capacity
        auto_pause_delay = 120
        min_capacity = 1.0
        self.cmd('sql db update -g {} -s {} -n {} --auto-pause-delay {} --min-capacity {}'
                 .format(resource_group, server, database_name, auto_pause_delay, min_capacity),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('autoPauseDelay', auto_pause_delay),
                     JMESPathCheck('minCapacity', min_capacity)])

        # Update only vCores
        vCores = 8
        self.cmd('sql db update -g {} -s {} -n {} -c {}'
                 .format(resource_group, server, database_name, vCores),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('sku.capacity', vCores)])

        # Update back to provisioned database offering
        self.cmd('sql db update -g {} --server {} --name {} --compute-model {}'
                 .format(resource_group, server, database_name, compute_model_provisioned),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('sku.name', 'GP_Gen5')])

        # Create database with vcore edition with everything specified for Serverless
        database_name_2 = 'cliautomationdb02'
        vcore_edition = 'GeneralPurpose'
        vcore_family = 'Gen5'
        vcore_capacity = 4
        auto_pause_delay = 120
        min_capacity = 1.0

        self.cmd(
            'sql db create -g {} --server {} --name {} -e {} -c {} -f {} --compute-model {} --auto-pause-delay {} --min-capacity {}'
                .format(resource_group, server, database_name_2,
                        vcore_edition, vcore_capacity,
                        vcore_family, compute_model_serverless, auto_pause_delay, min_capacity),
            checks=[
                JMESPathCheck('resourceGroup', resource_group),
                JMESPathCheck('name', database_name_2),
                JMESPathCheck('edition', vcore_edition),
                JMESPathCheck('sku.tier', vcore_edition),
                JMESPathCheck('sku.capacity', vcore_capacity),
                JMESPathCheck('sku.family', vcore_family),
                JMESPathCheck('sku.name', 'GP_S_Gen5'),
                JMESPathCheck('autoPauseDelay', auto_pause_delay),
                JMESPathCheck('minCapacity', min_capacity)])


class SqlServerDbOperationMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    def test_sql_db_operation_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"
        update_service_objective = 'GP_Gen5_8'

        # Create db
        self.cmd('sql db create -g {} -s {} -n {} --yes'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('status', 'Online')])

        # Update DB with --no-wait
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {} --no-wait'
                 .format(resource_group, server, database_name, update_service_objective))

        # List operations
        ops = list(
            self.cmd('sql db op list -g {} -s {} -d {}'
                     .format(resource_group, server, database_name),
                     checks=[
                         JMESPathCheck('length(@)', 1),
                         JMESPathCheck('[0].resourceGroup', resource_group),
                         JMESPathCheck('[0].databaseName', database_name)
                     ])
                .get_output_in_json())

        # Cancel operation
        self.cmd('sql db op cancel -g {} -s {} -d {} -n {}'
                 .format(resource_group, server, database_name, ops[0]['name']))


class SqlServerDbShortTermRetentionScenarioTest(ScenarioTest):
    def test_sql_db_short_term_retention(self):
        # Initial parameters. default_diffbackup_hours will be changed to 24 soon.
        self.kwargs.update({
            'resource_group': 'WestUS2ResourceGroup',
            'server_name': 'lillian-westus2-server',
            'database_name': 'ps5691',
            'retention_days_v1': 7,
            'diffbackup_hours_v1': 24,
            'retention_days_v2': 6,
            'diffbackup_hours_v2': 12
        })

        # Test UPDATE short term retention policy on live database, value updated to v1.
        self.cmd(
            'sql db str-policy set -g {resource_group} -s {server_name} -n {database_name} --retention-days {retention_days_v1} --diffbackup-hours {diffbackup_hours_v1}',
            checks=[
                self.check('resourceGroup', '{resource_group}'),
                self.check('retentionDays', '{retention_days_v1}'),
                self.check('diffBackupIntervalInHours', '{diffbackup_hours_v1}')])

        # Test GET short term retention policy on live database, value equals to v1.
        self.cmd(
            'sql db str-policy show -g {resource_group} -s {server_name} -n {database_name}',
            checks=[
                self.check('resourceGroup', '{resource_group}'),
                self.check('retentionDays', '{retention_days_v1}'),
                self.check('diffBackupIntervalInHours', '{diffbackup_hours_v1}')])

        # Test UPDATE short term retention policy on live database, value updated to v2.
        self.cmd(
            'sql db str-policy set -g {resource_group} -s {server_name} -n {database_name} --retention-days {retention_days_v2} --diffbackup-hours {diffbackup_hours_v2}',
            checks=[
                self.check('resourceGroup', '{resource_group}'),
                self.check('retentionDays', '{retention_days_v2}'),
                self.check('diffBackupIntervalInHours', '{diffbackup_hours_v2}')])


class SqlServerDbLongTermRetentionScenarioTest(ScenarioTest):
    def test_sql_db_long_term_retention(
            self):
        self.kwargs.update({
            'rg': 'ayang',
            'loc': 'southeastasia',
            'server_name': 'ayang-seas',
            'database_name': 'db1',
            'weekly_retention': 'P1W',
            'monthly_retention': 'P1M',
            'yearly_retention': 'P2M',
            'week_of_year': 12
        })

        # test update long term retention on live database
        self.cmd(
            'sql db ltr-policy set -g {rg} -s {server_name} -n {database_name}'
            ' --weekly-retention {weekly_retention} --monthly-retention {monthly_retention}'
            ' --yearly-retention {yearly_retention} --week-of-year {week_of_year}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('weeklyRetention', '{weekly_retention}'),
                self.check('monthlyRetention', '{monthly_retention}'),
                self.check('yearlyRetention', '{yearly_retention}')])

        # test get long term retention policy on live database
        self.cmd(
            'sql db ltr-policy show -g {rg} -s {server_name} -n {database_name}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('weeklyRetention', '{weekly_retention}'),
                self.check('monthlyRetention', '{monthly_retention}'),
                self.check('yearlyRetention', '{yearly_retention}')])

        # test list long term retention backups for location
        # with resource group
        self.cmd(
            'sql db ltr-backup list -l {loc} -g {rg}',
            checks=[
                self.greater_than('length(@)', 0)])
        # without resource group
        self.cmd(
            'sql db ltr-backup list -l {loc}',
            checks=[
                self.greater_than('length(@)', 0)])

        # test list long term retention backups for instance
        # with resource group
        self.cmd(
            'sql db ltr-backup list -l {loc} -s {server_name} -g {rg}',
            checks=[
                self.greater_than('length(@)', 0)])

        # without resource group
        self.cmd(
            'sql db ltr-backup list -l {loc} -s {server_name}',
            checks=[
                self.greater_than('length(@)', 0)])

        # test list long term retention backups for database
        # with resource group
        self.cmd(
            'sql db ltr-backup list -l {loc} -s {server_name} -d {database_name} -g {rg}',
            checks=[
                self.greater_than('length(@)', 0)])

        # without resource group
        self.cmd(
            'sql db ltr-backup list -l {loc} -s {server_name} -d {database_name}',
            checks=[
                self.greater_than('length(@)', 0)])

        # setup for test show long term retention backup
        backup = self.cmd(
            'sql db ltr-backup list -l {loc} -s {server_name} -d {database_name} --latest True').get_output_in_json()

        self.kwargs.update({
            'backup_name': backup[0]['name'],
            'backup_id': backup[0]['id']
        })

        # test show long term retention backup
        self.cmd(
            'sql db ltr-backup show -l {loc} -s {server_name} -d {database_name} -n {backup_name}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('serverName', '{server_name}'),
                self.check('databaseName', '{database_name}'),
                self.check('name', '{backup_name}')])

        # test restore managed database from LTR backup
        self.kwargs.update({
            'dest_database_name': 'cli-restore-ltr'
        })

        self.cmd(
            'sql db ltr-backup restore --backup-id \'{backup_id}\' --dest-database {dest_database_name}'
            ' --dest-server {server_name} --dest-resource-group {rg}',
            checks=[
                self.check('name', '{dest_database_name}')])

        # test delete long term retention backup
        self.cmd(
            'sql db ltr-backup delete -l {loc} -s {server_name} -d {database_name} -n \'{backup_name}\' --yes',
            checks=[NoneCheck()])


class SqlManagedInstanceOperationMgmtScenarioTest(ScenarioTest):

    @ManagedInstancePreparer()
    def test_sql_mi_operation_mgmt(self, mi, rg):
        managed_instance_name = mi
        resource_group = rg
        edition_updated = 'BusinessCritical'
        v_core_update = 4

        # Managed instance becomes ready before the operation is completed. For that reason, we should wait
        # for the operation to complete in order to proceed with testing.
        if self.is_live:
            sleep(120)

        print('Updating MI...\n')

        # Update sql managed_instance
        self.cmd('sql mi update -g {} -n {} --edition {} --capacity {} --no-wait'
                 .format(resource_group, managed_instance_name, edition_updated, v_core_update))

        print('Listing all operations...\n')

        # List operations
        ops = list(
            self.cmd('sql mi op list -g {} --mi {}'
                     .format(resource_group, managed_instance_name),
                     checks=[
                         JMESPathCheck('length(@)', 2),
                         JMESPathCheck('[0].resourceGroup', resource_group),
                         JMESPathCheck('[0].managedInstanceName', managed_instance_name)
                     ])
                .get_output_in_json())

        print('Canceling operation...\n')

        # Cancel operation
        self.cmd('sql mi op cancel -g {} --mi {} -n {}'
                 .format(resource_group, managed_instance_name, ops[1]['name']))


class SqlServerConnectionPolicyScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlServerPreparer(location='eastus')
    def test_sql_server_connection_policy(self, resource_group, resource_group_location, server):
        # Show
        self.cmd('sql server conn-policy show -g {} -s {}'
                 .format(resource_group, server),
                 checks=[JMESPathCheck('connectionType', 'Default')])

        # Update
        for type in ('Proxy', 'Default', 'Redirect'):
            self.cmd('sql server conn-policy update -g {} -s {} -t {}'
                     .format(resource_group, server, type),
                     checks=[JMESPathCheck('connectionType', type)])


class AzureActiveDirectoryAdministratorScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    def test_aad_admin(self, resource_group, server):
        self.kwargs.update({
            'rg': resource_group,
            'sn': server,
            'administrator_name': "ActiveDirectory",
            'oid': '5e90ef3b-9b42-4777-819b-25c36961ea4d',
            'oid2': 'e4d43337-d52c-4a0c-b581-09055e0359a0',
            'user': 'DSEngAll',
            'user2': 'TestUser'
        })

        print('Arguments are updated with login and sid data')

        self.cmd('sql server ad-admin create -s {sn} -g {rg} -i {oid} -u {user}',
                 checks=[
                     self.check('login', '{user}'),
                     self.check('sid', '{oid}')])

        self.cmd('sql server ad-admin list -s {sn} -g {rg}',
                 checks=[
                     self.check('[0].login', '{user}'),
                     self.check('[0].sid', '{oid}')])
        
        self.cmd('sql server ad-admin update -s {sn} -g {rg}'
                 ' -u {user2} -i {oid2}',
                 checks=[
                     self.check('login', '{user2}'),
                     self.check('sid', '{oid2}')])
        
        self.cmd('sql server ad-admin delete -s {sn} -g {rg}')

        self.cmd('sql server ad-admin list -s {sn} -g {rg}',
                 checks=[
                     self.check('[0].login', None),
                     self.check('[0].sid', None)])


class SqlServerADOnlyAuthScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    def test_aadonly(self, resource_group, server):
        print('\n********************')
        print("Server: {}".format(server))
        print('********************\n')

        user = 'DSEngAll'
        oid = '5e90ef3b-9b42-4777-819b-25c36961ea4d'

        self.cmd('sql server ad-admin create -s {} -g {} -u {} -i {}'.format(server, resource_group, user, oid),
                 checks=[])

        self.cmd('sql server ad-only-auth enable -n {} -g {}'.format(server, resource_group), checks=[])
        self.cmd('sql server ad-only-auth disable -n {} -g {}'.format(server, resource_group), checks=[])
        self.cmd('sql server ad-only-auth get -n {} -g {}'.format(server, resource_group), checks=[])


class SqlServerDbCopyScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(parameter_name='resource_group_1', location='westeurope')
    @ResourceGroupPreparer(parameter_name='resource_group_2', location='westeurope')
    @SqlServerPreparer(parameter_name='server1', resource_group_parameter_name='resource_group_1',
                       location='westeurope')
    @SqlServerPreparer(parameter_name='server2', resource_group_parameter_name='resource_group_2',
                       location='westeurope')
    @AllowLargeResponse()
    def test_sql_db_copy(self, resource_group_1, resource_group_2,
                         resource_group_location,
                         server1, server2):
        database_name = "cliautomationdb01"
        database_copy_name = "cliautomationdb02"
        service_objective = 'GP_Gen5_8'

        # create database
        self.cmd('sql db create -g {} --server {} --name {} --yes'
                 .format(resource_group_1, server1, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('status', 'Online')])

        # copy database to same server (min parameters)
        self.cmd('sql db copy -g {} --server {} --name {} '
                 '--dest-name {}'
                 .format(resource_group_1, server1, database_name, database_copy_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('name', database_copy_name)
                 ])

        # copy database to same server (min parameters, plus service_objective)
        self.cmd('sql db copy -g {} --server {} --name {} '
                 '--dest-name {} --service-objective {}'
                 .format(resource_group_1, server1, database_name, database_copy_name, service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('name', database_copy_name),
                     JMESPathCheck('requestedServiceObjectiveName', service_objective),
                 ])

        # copy database to same server specify backup storage redundancy
        bsr_database = "bsr_database"
        backup_storage_redundancy = 'local'
        self.cmd('sql db copy -g {} --server {} --name {} '
                 '--dest-name {} --backup-storage-redundancy {}'
                 .format(resource_group_1, server1, database_name, bsr_database, backup_storage_redundancy),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('name', bsr_database),
                     JMESPathCheck('requestedBackupStorageRedundancy', 'Local')
                 ])

        # copy database to elastic pool in other server (max parameters, other than
        # service_objective)
        pool_name = 'pool1'
        pool_edition = 'GeneralPurpose'
        self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                 ' --edition {}'
                 .format(resource_group_2, server2, pool_name, pool_edition))

        self.cmd('sql db copy -g {} --server {} --name {} '
                 '--dest-name {} --dest-resource-group {} --dest-server {} '
                 '--elastic-pool {}'
                 .format(resource_group_1, server1, database_name, database_copy_name,
                         resource_group_2, server2, pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_2),
                     JMESPathCheck('name', database_copy_name),
                     JMESPathCheck('elasticPoolName', pool_name)
                 ])


def _get_earliest_restore_date(db):
    return datetime.strptime(db['earliestRestoreDate'], "%Y-%m-%dT%H:%M:%S+00:00")


def _get_earliest_restore_date_for_deleted_db(deleted_db):
    return datetime.strptime(deleted_db['earliestRestoreDate'], "%Y-%m-%dT%H:%M:%S+00:00")


def _get_deleted_date(deleted_db):
    return datetime.strptime(deleted_db['deletionDate'], "%Y-%m-%dT%H:%M:%S.%f+00:00")


def _create_db_wait_for_first_backup(test, resource_group, server, database_name):
    # create db
    db = test.cmd('sql db create -g {} --server {} --name {} -y'
                  .format(resource_group, server, database_name),
                  checks=[
                      JMESPathCheck('resourceGroup', resource_group),
                      JMESPathCheck('name', database_name),
                      JMESPathCheck('status', 'Online')]).get_output_in_json()

    # Wait until earliestRestoreDate is in the past. When run live, this will take at least
    # 10 minutes. Unforunately there's no way to speed this up
    while db['earliestRestoreDate'] is None:
        sleep(60)
        db = test.cmd('sql db show -g {} -s {} -n {}'
                      .format(resource_group, server, database_name)).get_output_in_json()

    earliest_restore_date = _get_earliest_restore_date(db)

    if datetime.utcnow() <= earliest_restore_date:
        print('Waiting until earliest restore date', earliest_restore_date)

    while datetime.utcnow() <= earliest_restore_date:
        sleep(10)  # seconds

    return db


def _wait_until_first_backup_midb(self):
    earliest_restore_date_string = None

    while earliest_restore_date_string is None:
        db = self.cmd('sql midb show -g {rg} --mi {managed_instance_name} -n {database_name}',
                      checks=[self.greater_than('length(@)', 0)])

        earliest_restore_date_string = db.json_value['earliestRestorePoint']


class SqlServerDbRestoreScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    @AllowLargeResponse()
    def test_sql_db_restore(self, resource_group, resource_group_location, server):
        database_name = 'cliautomationdb01'

        # Standalone db
        restore_service_objective = 'S1'
        restore_edition = 'Standard'
        restore_standalone_database_name = 'cliautomationdb01restore1'

        restore_pool_database_name = 'cliautomationdb01restore2'
        elastic_pool = 'cliautomationpool1'

        # create elastic pool
        self.cmd('sql elastic-pool create -g {} -s {} -n {}'
                 .format(resource_group, server, elastic_pool))

        # Create database and wait for first backup to exist
        _create_db_wait_for_first_backup(self, resource_group, server, database_name)

        # Restore to standalone db
        self.cmd('sql db restore -g {} -s {} -n {} -t {} --dest-name {}'
                 ' --service-objective {} --edition {}'
                 .format(resource_group, server, database_name, datetime.utcnow().isoformat(),
                         restore_standalone_database_name, restore_service_objective,
                         restore_edition),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', restore_standalone_database_name),
                     JMESPathCheck('requestedServiceObjectiveName',
                                   restore_service_objective),
                     JMESPathCheck('status', 'Online')])

        # Restore to db into pool. Note that 'elasticPoolName' is populated
        # in transform func which only runs after `show`/`list` commands.
        self.cmd('sql db restore -g {} -s {} -n {} -t {} --dest-name {}'
                 ' --elastic-pool {}'
                 .format(resource_group, server, database_name, datetime.utcnow().isoformat(),
                         restore_pool_database_name, elastic_pool),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', restore_pool_database_name),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db show -g {} -s {} -n {}'
                 .format(resource_group, server, restore_pool_database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', restore_pool_database_name),
                     JMESPathCheck('status', 'Online'),
                     JMESPathCheck('elasticPoolName', elastic_pool)])

        # restore db with backup storage redundancy parameter
        bsr_database = 'bsr_database'
        backup_storage_redundancy = 'geo'
        self.cmd('sql db restore -g {} -s {} -n {} -t {} --dest-name {} --backup-storage-redundancy {}'
                 .format(resource_group, server, database_name, datetime.utcnow().isoformat(),
                         bsr_database, backup_storage_redundancy),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', bsr_database),
                     JMESPathCheck('requestedBackupStorageRedundancy', 'Geo')])


class SqlServerDbRestoreDeletedScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    @AllowLargeResponse()
    def test_sql_db_restore_deleted(self, resource_group, resource_group_location, server):
        database_name = 'cliautomationdb01'

        # Standalone db
        restore_service_objective = 'S1'
        restore_edition = 'Standard'
        restore_database_name1 = 'cliautomationdb01restore1'
        restore_database_name2 = 'cliautomationdb01restore2'

        # Create database and wait for first backup to exist
        _create_db_wait_for_first_backup(self, resource_group, server, database_name)

        # Delete database
        self.cmd('sql db delete -g {} -s {} -n {} --yes'.format(resource_group, server, database_name))

        # Wait for deleted database to become visible. When run live, this will take around
        # 5-10 minutes. Unforunately there's no way to speed this up. Use timeout to ensure
        # test doesn't loop forever if there's a bug.
        start_time = datetime.now()
        timeout = timedelta(0, 15 * 60)  # 15 minutes timeout

        while True:
            deleted_dbs = list(
                self.cmd('sql db list-deleted -g {} -s {}'.format(resource_group, server)).get_output_in_json())

            if deleted_dbs:
                # Deleted db found, stop polling
                break

            # Deleted db not found, sleep (if running live) and then poll again.
            if self.is_live:
                self.assertTrue(datetime.now() < start_time + timeout, 'Deleted db not found before timeout expired.')
                sleep(10)  # seconds

        deleted_db = deleted_dbs[0]

        # Restore deleted to latest point in time
        self.cmd('sql db restore -g {} -s {} -n {} --deleted-time {} --dest-name {}'
                 ' --service-objective {} --edition {}'
                 .format(resource_group, server, database_name, _get_deleted_date(deleted_db).isoformat(),
                         restore_database_name1, restore_service_objective,
                         restore_edition),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', restore_database_name1),
                     JMESPathCheck('requestedServiceObjectiveName',
                                   restore_service_objective),
                     JMESPathCheck('status', 'Online')])

        # Restore deleted to earlier point in time
        self.cmd('sql db restore -g {} -s {} -n {} -t {} --deleted-time {} --dest-name {}'
                 .format(resource_group, server, database_name,
                         _get_earliest_restore_date_for_deleted_db(deleted_db).isoformat(),
                         _get_deleted_date(deleted_db).isoformat(), restore_database_name2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', restore_database_name2),
                     JMESPathCheck('status', 'Online')])


class SqlServerDbSecurityScenarioTest(ScenarioTest):
    def _get_storage_endpoint(self, storage_account, resource_group):
        return self.cmd('storage account show -g {} -n {}'
                        ' --query primaryEndpoints.blob'
                        .format(resource_group, storage_account)).get_output_in_json()

    def _get_storage_key(self, storage_account, resource_group):
        return self.cmd('storage account keys list -g {} -n {} --query [0].value'
                        .format(resource_group, storage_account)).get_output_in_json()

    @ResourceGroupPreparer(location='westeurope')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    @SqlServerPreparer(location='westeurope')
    @StorageAccountPreparer(location='westus')
    @StorageAccountPreparer(parameter_name='storage_account_2',
                            resource_group_parameter_name='resource_group_2')
    def test_sql_db_security_mgmt(self, resource_group, resource_group_2,
                                  resource_group_location, server,
                                  storage_account, storage_account_2):
        database_name = "cliautomationdb01"
        state_enabled = 'Enabled'
        state_disabled = 'Disabled'

        # get storage account endpoint and key
        storage_endpoint = self._get_storage_endpoint(storage_account, resource_group)
        key = self._get_storage_key(storage_account, resource_group)

        # create db
        self.cmd('sql db create -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('status', 'Online')])

        # get audit policy
        self.cmd('sql db audit-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('blobStorageTargetState', state_disabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # update audit policy - enable
        retention_days = 30
        audit_actions_input = 'DATABASE_LOGOUT_GROUP DATABASE_ROLE_MEMBER_CHANGE_GROUP'
        audit_actions_expected = ['DATABASE_LOGOUT_GROUP',
                                  'DATABASE_ROLE_MEMBER_CHANGE_GROUP']

        self.cmd('sql db audit-policy update -g {} -s {} -n {}'
                 ' --state {} --blob-storage-target-state {} --storage-key {} --storage-endpoint={}'
                 ' --retention-days={} --actions {}'
                 .format(resource_group, server, database_name, state_enabled, state_enabled, key,
                         storage_endpoint, retention_days, audit_actions_input),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageEndpoint', storage_endpoint),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy
        self.cmd('sql db audit-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # update audit policy - specify storage account and resource group. use secondary key
        storage_endpoint_2 = self._get_storage_endpoint(storage_account_2, resource_group_2)
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --blob-storage-target-state {} --storage-account {}'
                 .format(resource_group, server, database_name, state_enabled, storage_account_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # update audit policy - disable
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --state {}'
                 .format(resource_group, server, database_name, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_disabled),
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get threat detection policy
        self.cmd('sql db threat-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[JMESPathCheck('resourceGroup', resource_group)])

        # update threat detection policy - enable
        disabled_alerts_input = 'Sql_Injection_Vulnerability Access_Anomaly'
        disabled_alerts_expected = ['Sql_Injection_Vulnerability', 'Access_Anomaly']
        email_addresses_input = 'test1@example.com test2@example.com'
        email_addresses_expected = ['test1@example.com', 'test2@example.com']
        email_account_admins = True

        self.cmd('sql db threat-policy update -g {} -s {} -n {}'
                 ' --state {} --storage-key {} --storage-endpoint {}'
                 ' --retention-days {} --email-addresses {} --disabled-alerts {}'
                 ' --email-account-admins {}'
                 .format(resource_group, server, database_name, state_enabled, key,
                         storage_endpoint, retention_days, email_addresses_input,
                         disabled_alerts_input, email_account_admins),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageAccountAccessKey', ''),
                     JMESPathCheck('storageEndpoint', storage_endpoint),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('emailAddresses', email_addresses_expected),
                     JMESPathCheck('disabledAlerts', disabled_alerts_expected),
                     JMESPathCheck('emailAccountAdmins', email_account_admins)])

        # update threat policy - specify storage account and resource group. use secondary key
        key_2 = self._get_storage_key(storage_account_2, resource_group_2)
        self.cmd('sql db threat-policy update -g {} -s {} -n {}'
                 ' --storage-account {}'
                 .format(resource_group, server, database_name, storage_account_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageAccountAccessKey', ''),
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('emailAddresses', email_addresses_expected),
                     JMESPathCheck('disabledAlerts', disabled_alerts_expected),
                     JMESPathCheck('emailAccountAdmins', email_account_admins)])

        # create log analytics workspace
        log_analytics_workspace_name = self.create_random_name("laws", 20)

        log_analytics_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {}'
                                              .format(resource_group, log_analytics_workspace_name),
                                              checks=[
                                                  JMESPathCheck('resourceGroup', resource_group),
                                                  JMESPathCheck('name', log_analytics_workspace_name),
                                                  JMESPathCheck('provisioningState',
                                                                'Succeeded')]).get_output_in_json()['id']

        # update audit policy - enable log analytics target
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --state {}'
                 ' --log-analytics-target-state {} --log-analytics-workspace-resource-id {}'
                 .format(resource_group, server, database_name, state_enabled,
                         state_enabled, log_analytics_workspace_id),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify logAnalyticsTargetState is enabled and isAzureMonitorTargetEnabled is true
        self.cmd('sql db audit-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_enabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', True)])

        # update audit policy - disable log analytics target
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --state {} --log-analytics-target-state {}'
                 .format(resource_group, server, database_name, state_enabled, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify logAnalyticsTargetState is disabled and isAzureMonitorTargetEnabled is false
        self.cmd('sql db audit-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # create event hub namespace
        eventhub_namespace = 'cliehnamespacedb01'

        self.cmd('eventhubs namespace create -g {} -n {}'
                 .format(resource_group, eventhub_namespace),
                 checks=[
                     JMESPathCheck('provisioningState', 'Succeeded')])

        # create event hub
        eventhub_name = 'cliehdb01'

        self.cmd('eventhubs eventhub create -g {} -n {} --namespace-name {}'
                 .format(resource_group, eventhub_name, eventhub_namespace),
                 checks=[
                     JMESPathCheck('status', 'Active')])

        # create event hub autorization rule
        eventhub_auth_rule = 'cliehauthruledb01'

        eventhub_auth_rule_id = self.cmd(
            'eventhubs namespace authorization-rule create -g {} -n {} --namespace-name {} --rights Listen Manage Send'
                .format(resource_group, eventhub_auth_rule, eventhub_namespace)).get_output_in_json()['id']

        # update audit policy - enable event hub target
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --state {} --event-hub-target-state {}'
                 ' --event-hub-authorization-rule-id {} --event-hub {}'
                 .format(resource_group, server, database_name, state_enabled, state_enabled,
                         eventhub_auth_rule_id, eventhub_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify eventHubTargetState is enabled and isAzureMonitorTargetEnabled is true
        self.cmd('sql db audit-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_enabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', True)])

        # update audit policy - disable event hub target
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --state {} --event-hub-target-state {}'
                 .format(resource_group, server, database_name, state_enabled, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify eventHubTargetState is disabled and isAzureMonitorTargetEnabled is false
        self.cmd('sql db audit-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])


class SqlServerSecurityScenarioTest(ScenarioTest):
    def _get_storage_endpoint(self, storage_account, resource_group):
        return self.cmd('storage account show -g {} -n {}'
                        ' --query primaryEndpoints.blob'
                        .format(resource_group, storage_account)).get_output_in_json()

    def _get_storage_key(self, storage_account, resource_group):
        return self.cmd('storage account keys list -g {} -n {} --query [0].value'
                        .format(resource_group, storage_account)).get_output_in_json()

    @ResourceGroupPreparer(location='westeurope')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    @SqlServerPreparer(location='westeurope')
    @StorageAccountPreparer(location='westus')
    @StorageAccountPreparer(parameter_name='storage_account_2',
                            resource_group_parameter_name='resource_group_2')
    def test_sql_server_security_mgmt(self, resource_group, resource_group_2,
                                      resource_group_location, server,
                                      storage_account, storage_account_2):
        state_enabled = 'Enabled'
        state_disabled = 'Disabled'

        # get storage account endpoint and key
        storage_endpoint = self._get_storage_endpoint(storage_account, resource_group)
        key = self._get_storage_key(storage_account, resource_group)

        # get audit policy
        self.cmd('sql server audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('blobStorageTargetState', state_disabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # update audit policy - enable
        retention_days = 30
        audit_actions_input = 'DATABASE_LOGOUT_GROUP DATABASE_ROLE_MEMBER_CHANGE_GROUP'
        audit_actions_expected = ['DATABASE_LOGOUT_GROUP',
                                  'DATABASE_ROLE_MEMBER_CHANGE_GROUP']

        self.cmd('sql server audit-policy update -g {} -n {}'
                 ' --state {} --blob-storage-target-state {} --storage-key {} --storage-endpoint={}'
                 ' --retention-days={} --actions {}'
                 .format(resource_group, server, state_enabled, state_enabled, key,
                         storage_endpoint, retention_days, audit_actions_input),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageEndpoint', storage_endpoint),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy
        self.cmd('sql server audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # update audit policy - specify storage account and resource group. use secondary key
        storage_endpoint_2 = self._get_storage_endpoint(storage_account_2, resource_group_2)
        self.cmd('sql server audit-policy update -g {} -n {}'
                 ' --blob-storage-target-state {} --storage-account {}'
                 .format(resource_group, server, state_enabled, storage_account_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # update audit policy - disable
        self.cmd('sql server audit-policy update -g {} -n {}'
                 ' --state {}'
                 .format(resource_group, server, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_disabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # create log analytics workspace
        log_analytics_workspace_name = self.create_random_name("laws", 20)

        log_analytics_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {}'
                                              .format(resource_group, log_analytics_workspace_name),
                                              checks=[
                                                  JMESPathCheck('resourceGroup', resource_group),
                                                  JMESPathCheck('name', log_analytics_workspace_name),
                                                  JMESPathCheck('provisioningState',
                                                                'Succeeded')]).get_output_in_json()['id']

        # update audit policy - enable log analytics target
        self.cmd('sql server audit-policy update -g {} -n {}'
                 ' --state {}'
                 ' --log-analytics-target-state {} --log-analytics-workspace-resource-id {}'
                 .format(resource_group, server, state_enabled, state_enabled, log_analytics_workspace_id),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify logAnalyticsTargetState is enabled and isAzureMonitorTargetEnabled is true
        self.cmd('sql server audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_enabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', True)])

        # update audit policy - disable log analytics target
        self.cmd('sql server audit-policy update -g {} -n {}'
                 ' --state {} --log-analytics-target-state {}'
                 .format(resource_group, server, state_enabled, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify logAnalyticsTargetState is disabled and isAzureMonitorTargetEnabled is false
        self.cmd('sql server audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # create event hub namespace
        eventhub_namespace = 'cliehnamespacedb01'

        self.cmd('eventhubs namespace create -g {} -n {}'
                 .format(resource_group, eventhub_namespace),
                 checks=[
                     JMESPathCheck('provisioningState', 'Succeeded')])

        # create event hub
        eventhub_name = 'cliehsrv01'

        self.cmd('eventhubs eventhub create -g {} -n {} --namespace-name {}'
                 .format(resource_group, eventhub_name, eventhub_namespace),
                 checks=[
                     JMESPathCheck('status', 'Active')])

        # create event hub autorization rule
        eventhub_auth_rule = 'cliehauthruledb01'

        eventhub_auth_rule_id = self.cmd(
            'eventhubs namespace authorization-rule create -g {} -n {} --namespace-name {} --rights Listen Manage Send'
                .format(resource_group, eventhub_auth_rule, eventhub_namespace)).get_output_in_json()['id']

        # update audit policy - enable event hub target
        self.cmd('sql server audit-policy update -g {} -n {}'
                 ' --state {} --event-hub-target-state {}'
                 ' --event-hub-authorization-rule-id {} --event-hub {}'
                 .format(resource_group, server, state_enabled, state_enabled,
                         eventhub_auth_rule_id, eventhub_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify eventHubTargetState is enabled and isAzureMonitorTargetEnabled is true
        self.cmd('sql server audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_enabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', True)])

        # update audit policy - disable event hub target
        self.cmd('sql server audit-policy update -g {} -n {}'
                 ' --state {} --event-hub-target-state {}'
                 .format(resource_group, server, state_enabled, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get audit policy - verify eventHubTargetState is disabled and isAzureMonitorTargetEnabled is false
        self.cmd('sql server audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])


class SqlServerMSSupportScenarioTest(ScenarioTest):
    def _get_storage_endpoint(self, storage_account, resource_group):
        return self.cmd('storage account show -g {} -n {}'
                        ' --query primaryEndpoints.blob'
                        .format(resource_group, storage_account)).get_output_in_json()

    def _get_storage_key(self, storage_account, resource_group):
        return self.cmd('storage account keys list -g {} -n {} --query [0].value'
                        .format(resource_group, storage_account)).get_output_in_json()

    @ResourceGroupPreparer(location='westeurope')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    @SqlServerPreparer(location='westeurope')
    @StorageAccountPreparer(location='westus')
    @StorageAccountPreparer(parameter_name='storage_account_2',
                            resource_group_parameter_name='resource_group_2')
    def test_sql_server_ms_support_mgmt(self, resource_group, resource_group_2,
                                        resource_group_location, server,
                                        storage_account, storage_account_2):
        state_enabled = 'Enabled'
        state_disabled = 'Disabled'

        # get storage account endpoint and key
        storage_endpoint = self._get_storage_endpoint(storage_account, resource_group)
        key = self._get_storage_key(storage_account, resource_group)

        # get MS support audit policy
        self.cmd('sql server ms-support audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('blobStorageTargetState', state_disabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # update MS support audit policy - enable
        self.cmd('sql server ms-support audit-policy update -g {} -n {}'
                 ' --state {} --blob-storage-target-state {} --storage-key {} --storage-endpoint={}'
                 .format(resource_group, server, state_enabled, state_enabled, key, storage_endpoint),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageEndpoint', storage_endpoint)])

        # get MS support audit policy
        self.cmd('sql server ms-support audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # update MS support audit policy - specify storage account and resource group. use secondary key
        storage_endpoint_2 = self._get_storage_endpoint(storage_account_2, resource_group_2)
        self.cmd(
            'sql server ms-support audit-policy update -g {} -n {} --blob-storage-target-state {} --storage-account {}'
                .format(resource_group, server, state_enabled, storage_account_2),
            checks=[
                JMESPathCheck('resourceGroup', resource_group),
                JMESPathCheck('state', state_enabled),
                JMESPathCheck('storageEndpoint', storage_endpoint_2)])

        # update MS support audit policy - disable
        self.cmd('sql server ms-support audit-policy update -g {} -n {} --state {}'
                 .format(resource_group, server, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_disabled)])

        # create log analytics workspace
        log_analytics_workspace_name = "clilaworkspacems04"

        log_analytics_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {}'
                                              .format(resource_group, log_analytics_workspace_name),
                                              checks=[
                                                  JMESPathCheck('resourceGroup', resource_group),
                                                  JMESPathCheck('name', log_analytics_workspace_name),
                                                  JMESPathCheck('provisioningState',
                                                                'Succeeded')]).get_output_in_json()['id']

        # update MS support audit policy - enable log analytics target
        self.cmd('sql server ms-support audit-policy update -g {} -n {} --state {}'
                 ' --log-analytics-target-state {} --log-analytics-workspace-resource-id {}'
                 .format(resource_group, server, state_enabled, state_enabled, log_analytics_workspace_id),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled)])

        # get MS support audit policy - verify logAnalyticsTargetState is enabled and isAzureMonitorTargetEnabled is true
        self.cmd('sql server ms-support audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_enabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', True)])

        # update MS support audit policy - disable log analytics target
        self.cmd('sql server ms-support audit-policy update -g {} -n {} --state {} --log-analytics-target-state {}'
                 .format(resource_group, server, state_enabled, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled)])

        # get MS support audit policy - verify logAnalyticsTargetState is disabled and isAzureMonitorTargetEnabled is false
        self.cmd('sql server ms-support audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])

        # create event hub namespace
        eventhub_namespace = 'cliehnamespacems02'

        self.cmd('eventhubs namespace create -g {} -n {}'
                 .format(resource_group, eventhub_namespace),
                 checks=[
                     JMESPathCheck('provisioningState', 'Succeeded')])

        # create event hub
        eventhub_name = 'cliehms02'

        self.cmd('eventhubs eventhub create -g {} -n {} --namespace-name {}'
                 .format(resource_group, eventhub_name, eventhub_namespace),
                 checks=[
                     JMESPathCheck('status', 'Active')])

        # create event hub autorization rule
        eventhub_auth_rule = 'cliehauthrulems02'

        eventhub_auth_rule_id = self.cmd(
            'eventhubs namespace authorization-rule create -g {} -n {} --namespace-name {} --rights Listen Manage Send'
                .format(resource_group, eventhub_auth_rule, eventhub_namespace)).get_output_in_json()['id']

        # update MS support audit policy - enable event hub target
        self.cmd('sql server ms-support audit-policy update -g {} -n {} --state {} --event-hub-target-state {}'
                 ' --event-hub-authorization-rule-id {} --event-hub {}'
                 .format(resource_group, server, state_enabled, state_enabled,
                         eventhub_auth_rule_id, eventhub_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled)])

        # get MS support audit policy - verify eventHubTargetState is enabled and isAzureMonitorTargetEnabled is true
        self.cmd('sql server ms-support audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_enabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', True)])

        # update MS support audit policy - disable event hub target
        self.cmd('sql server ms-support audit-policy update -g {} -n {} --state {} --event-hub-target-state {}'
                 .format(resource_group, server, state_enabled, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled)])

        # get MS support audit policy - verify eventHubTargetState is disabled and isAzureMonitorTargetEnabled is false
        self.cmd('sql server ms-support audit-policy show -g {} -n {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('blobStorageTargetState', state_enabled),
                     JMESPathCheck('logAnalyticsTargetState', state_disabled),
                     JMESPathCheck('eventHubTargetState', state_disabled),
                     JMESPathCheck('isAzureMonitorTargetEnabled', False)])


class SqlServerDwMgmtScenarioTest(ScenarioTest):
    # pylint: disable=too-many-instance-attributes
    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    @AllowLargeResponse()
    def test_sql_dw_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"

        update_service_objective = 'DW200c'
        update_storage = '20TB'
        update_storage_bytes = str(20 * 1024 * 1024 * 1024 * 1024)

        # test sql db commands
        dw = self.cmd('sql dw create -g {} --server {} --name {}'
                      .format(resource_group, server, database_name),
                      checks=[
                          JMESPathCheck('resourceGroup', resource_group),
                          JMESPathCheck('name', database_name),
                          JMESPathCheck('location', resource_group_location),
                          JMESPathCheck('edition', 'DataWarehouse'),
                          JMESPathCheck('sku.tier', 'DataWarehouse'),
                          JMESPathCheck('status', 'Online')]).get_output_in_json()

        # Sanity check that the default max size is not equal to the size that we will update to
        # later. That way we know that update is actually updating the size.
        self.assertNotEqual(dw['maxSizeBytes'], update_storage_bytes,
                            'Initial max size in bytes is equal to the value we want to update to later,'
                            ' so we will not be able to verify that update max size is actually updating.')

        # DataWarehouse is a little quirky and is considered to be both a database and its
        # separate own type of thing. (Why? Because it has the same REST endpoint as regular
        # database, so it must be a database. However it has only a subset of supported operations,
        # so to clarify which operations are supported by dw we group them under `sql dw`.) So the
        # dw shows up under both `db list` and `dw list`.
        self.cmd('sql db list -g {} --server {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('length(@)', 2),  # includes dw and master
                     JMESPathCheck('sort([].name)', sorted([database_name, 'master'])),
                     JMESPathCheck('[0].resourceGroup', resource_group),
                     JMESPathCheck('[1].resourceGroup', resource_group)])

        self.cmd('sql dw list -g {} --server {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', database_name),
                     JMESPathCheck('[0].resourceGroup', resource_group)])

        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group)])

        # pause/resume
        self.cmd('sql dw pause -g {} --server {} --name {}'
                 .format(resource_group, server, database_name),
                 checks=[NoneCheck()])

        self.cmd('sql dw show --id {}'
                 .format(dw['id']),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('status', 'Paused')])

        self.cmd('sql dw resume -g {} --server {} --name {}'
                 .format(resource_group, server, database_name),
                 checks=[NoneCheck()])

        self.cmd('sql dw show --id {}'
                 .format(dw['id']),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('status', 'Online')])

        # Update DW storage
        self.cmd('sql dw update -g {} -s {} -n {} --max-size {}'
                 ' --set tags.key1=value1'
                 .format(resource_group, server, database_name, update_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('maxSizeBytes', update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        # Update DW service objective
        self.cmd('sql dw update --id {} --service-objective {}'
                 .format(dw['id'], update_service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('requestedServiceObjectiveName', update_service_objective),
                     JMESPathCheck('maxSizeBytes', update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        # Delete DW
        self.cmd('sql dw delete -g {} --server {} --name {} --yes'
                 .format(resource_group, server, database_name),
                 checks=[NoneCheck()])

        self.cmd('sql dw delete --id {} --yes'
                 .format(dw['id']),
                 checks=[NoneCheck()])


class SqlServerDnsAliasMgmtScenarioTest(ScenarioTest):

    # create 2 servers in the same resource group, and 1 server in a different resource group
    @ResourceGroupPreparer(parameter_name="resource_group_1",
                           parameter_name_for_location="resource_group_location_1",
                           location='eastus')
    @ResourceGroupPreparer(parameter_name="resource_group_2",
                           parameter_name_for_location="resource_group_location_2",
                           location='eastus')
    @SqlServerPreparer(parameter_name="server_name_1",
                       resource_group_parameter_name="resource_group_1",
                       location='eastus')
    @SqlServerPreparer(parameter_name="server_name_2",
                       resource_group_parameter_name="resource_group_1",
                       location='eastus')
    @SqlServerPreparer(parameter_name="server_name_3",
                       resource_group_parameter_name="resource_group_2",
                       location='eastus')
    def test_sql_server_dns_alias_mgmt(self,
                                       resource_group_1, resource_group_location_1,
                                       resource_group_2, resource_group_location_2,
                                       server_name_1, server_name_2, server_name_3):
        # helper class so that it's clear which servers are in which groups
        class ServerInfo(object):  # pylint: disable=too-few-public-methods
            def __init__(self, name, group, location):
                self.name = name
                self.group = group
                self.location = location

        s1 = ServerInfo(server_name_1, resource_group_1, resource_group_location_1)
        s2 = ServerInfo(server_name_2, resource_group_1, resource_group_location_1)
        s3 = ServerInfo(server_name_3, resource_group_2, resource_group_location_2)

        alias_name = 'alias1'

        # verify setup
        for s in (s1, s2, s3):
            self.cmd('sql server show -g {} -n {}'
                     .format(s.group, s.name),
                     checks=[
                         JMESPathCheck('name', s.name),
                         JMESPathCheck('resourceGroup', s.group)])

        # Create server dns alias
        self.cmd('sql server dns-alias create -n {} -s {} -g {}'
                 .format(alias_name, s1.name, s1.group),
                 checks=[
                     JMESPathCheck('name', alias_name),
                     JMESPathCheck('resourceGroup', s1.group)
                 ])

        # Check that alias is created on a right server
        self.cmd('sql server dns-alias list -s {} -g {}'
                 .format(s1.name, s1.group),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', alias_name)
                 ])

        # Repoint alias to the server within the same resource group
        self.cmd('sql server dns-alias set -n {} --original-server {} -s {} -g {}'
                 .format(alias_name, s1.name, s2.name, s2.group),
                 checks=[])

        # List the aliases on old server to check if alias is not pointing there
        self.cmd('sql server dns-alias list -s {} -g {}'
                 .format(s1.name, s1.group),
                 checks=[
                     JMESPathCheck('length(@)', 0)
                 ])

        # Check if alias is pointing to new server
        self.cmd('sql server dns-alias list -s {} -g {}'
                 .format(s2.name, s2.group),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', alias_name)
                 ])

        # Repoint alias to the same server (to check that operation is idempotent)
        self.cmd('sql server dns-alias set -n {} --original-server {} -s {} -g {}'
                 .format(alias_name, s1.name, s2.name, s2.group),
                 checks=[])

        # Check if alias is pointing to the right server
        self.cmd('sql server dns-alias list -s {} -g {}'
                 .format(s2.name, s2.group),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', alias_name)
                 ])

        # Repoint alias to the server within the same resource group
        self.cmd('sql server dns-alias set -n {} --original-server {} --original-resource-group {} -s {} -g {}'
                 .format(alias_name, s2.name, s2.group, s3.name, s3.group),
                 checks=[])

        # List the aliases on old server to check if alias is not pointing there
        self.cmd('sql server dns-alias list -s {} -g {}'
                 .format(s2.name, s2.group),
                 checks=[
                     JMESPathCheck('length(@)', 0)
                 ])

        # Check if alias is pointing to new server
        self.cmd('sql server dns-alias list -s {} -g {}'
                 .format(s3.name, s3.group),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', alias_name)
                 ])

        # Drop alias
        self.cmd('sql server dns-alias delete -n {} -s {} -g {}'
                 .format(alias_name, s3.name, s3.group),
                 checks=[])

        # Verify that alias got dropped correctly
        self.cmd('sql server dns-alias list -s {} -g {}'
                 .format(s3.name, s3.group),
                 checks=[
                     JMESPathCheck('length(@)', 0)
                 ])


class SqlServerDbReplicaMgmtScenarioTest(ScenarioTest):
    # create 2 servers in the same resource group, and 1 server in a different resource group
    @ResourceGroupPreparer(parameter_name="resource_group_1",
                           parameter_name_for_location="resource_group_location_1",
                           location='westeurope')
    @ResourceGroupPreparer(parameter_name="resource_group_2",
                           parameter_name_for_location="resource_group_location_2",
                           location='westeurope')
    @SqlServerPreparer(parameter_name="server_name_1",
                       resource_group_parameter_name="resource_group_1",
                       location='westeurope')
    @SqlServerPreparer(parameter_name="server_name_2",
                       resource_group_parameter_name="resource_group_1",
                       location='westeurope')
    @SqlServerPreparer(parameter_name="server_name_3",
                       resource_group_parameter_name="resource_group_2",
                       location='westeurope')
    @AllowLargeResponse()
    def test_sql_db_replica_mgmt(self,
                                 resource_group_1, resource_group_location_1,
                                 resource_group_2, resource_group_location_2,
                                 server_name_1, server_name_2, server_name_3):

        database_name = "cliautomationdb01"
        target_database_name = "cliautomationdb02"
        hs_database_name = "cliautomationhs03"
        hs_target_database_name = "cliautomationnr04"
        service_objective = 'GP_Gen5_8'
        hs_service_objective = 'HS_Gen5_8'

        # helper class so that it's clear which servers are in which groups
        class ServerInfo(object):  # pylint: disable=too-few-public-methods
            def __init__(self, name, group, location):
                self.name = name
                self.group = group
                self.location = location

        s1 = ServerInfo(server_name_1, resource_group_1, resource_group_location_1)
        s2 = ServerInfo(server_name_2, resource_group_1, resource_group_location_1)
        s3 = ServerInfo(server_name_3, resource_group_2, resource_group_location_2)

        # verify setup
        for s in (s1, s2, s3):
            self.cmd('sql server show -g {} -n {}'
                     .format(s.group, s.name),
                     checks=[
                         JMESPathCheck('name', s.name),
                         JMESPathCheck('resourceGroup', s.group)])

        # create db in first server
        self.cmd('sql db create -g {} -s {} -n {} --yes'
                 .format(s1.group, s1.name, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s1.group)])

        # create hs db in first server
        self.cmd('sql db create -g {} -s {} -n {} --service-objective {} --yes'
                 .format(s1.group, s1.name, hs_database_name, hs_service_objective),
                 checks=[
                     JMESPathCheck('name', hs_database_name),
                     JMESPathCheck('resourceGroup', s1.group)])

        # create replica in second server with min params
        # partner resource group unspecified because s1.group == s2.group
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-server {}'
                 .format(s1.group, s1.name, database_name,
                         s2.name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s2.group)])

        # create replica in second server with backup storage redundancy
        backup_storage_redundancy = "zone"
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-server {} --backup-storage-redundancy {}'
                 .format(s1.group, s1.name, database_name,
                         s2.name, backup_storage_redundancy),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s2.group),
                     JMESPathCheck('requestedBackupStorageRedundancy', 'Zone')])

        # check that the replica was created in the correct server
        self.cmd('sql db show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s2.group)])

        # Delete replica in second server and recreate with explicit service objective and name
        self.cmd('sql db delete -g {} -s {} -n {} --yes'
                 .format(s2.group, s2.name, database_name))

        secondary_type = "Geo"
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-server {} '
                 ' --service-objective {} --partner-database {} --secondary-type {}'
                 .format(s1.group, s1.name, database_name,
                         s2.name, service_objective, target_database_name, secondary_type),
                 checks=[
                     JMESPathCheck('name', target_database_name),
                     JMESPathCheck('resourceGroup', s2.group),
                     JMESPathCheck('requestedServiceObjectiveName', service_objective),
                     JMESPathCheck('secondaryType', secondary_type)])

        # Create a named replica
        secondary_type = "Named"
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-server {} '
                 ' --service-objective {} --partner-resource-group {} --partner-database {} --secondary-type {} --ha-replicas {}'
                 .format(s1.group, s1.name, hs_database_name,
                         s1.name, hs_service_objective, s1.group, hs_target_database_name, secondary_type, 2),
                 checks=[
                     JMESPathCheck('name', hs_target_database_name),
                     JMESPathCheck('resourceGroup', s1.group),
                     JMESPathCheck('requestedServiceObjectiveName', hs_service_objective),
                     JMESPathCheck('secondaryType', secondary_type),
                     JMESPathCheck('highAvailabilityReplicaCount', 2)])

        # Create replica in pool in third server with max params (except service objective)
        pool_name = 'pool1'
        pool_edition = 'GeneralPurpose'
        self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                 ' --edition {}'
                 .format(s3.group, s3.name, pool_name, pool_edition))

        self.cmd('sql db replica create -g {} -s {} -n {} --partner-server {}'
                 ' --partner-resource-group {} --elastic-pool {}'
                 .format(s1.group, s1.name, database_name,
                         s3.name, s3.group, pool_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s3.group),
                     JMESPathCheck('elasticPoolName', pool_name)])

        # check that the replica was created in the correct server
        self.cmd('sql db show -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s3.group)])

        # list replica links on s1 - it should link to s2 and s3
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s1.group, s1.name, database_name),
                 checks=[JMESPathCheck('length(@)', 2)])

        # list replica links on s3 - it should link only to s1
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].role', 'Secondary'),
                     JMESPathCheck('[0].partnerRole', 'Primary')])

        # Failover to s3.
        self.cmd('sql db replica set-primary -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[NoneCheck()])

        # list replica links on s3 - it should link to s1 and s2
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[JMESPathCheck('length(@)', 2)])

        # Stop replication from s3 to s2 twice. Second time should be no-op.
        for _ in range(2):
            # Delete link
            self.cmd('sql db replica delete-link -g {} -s {} -n {} --partner-resource-group {}'
                     ' --partner-server {} --yes'
                     .format(s3.group, s3.name, database_name, s2.group, s2.name),
                     checks=[NoneCheck()])

            # Verify link was deleted. s3 should still be the primary.
            self.cmd('sql db replica list-links -g {} -s {} -n {}'
                     .format(s3.group, s3.name, database_name),
                     checks=[
                         JMESPathCheck('length(@)', 1),
                         JMESPathCheck('[0].role', 'Primary'),
                         JMESPathCheck('[0].partnerRole', 'Secondary')])

        # Failover to s3 again (should be no-op, it's already primary)
        self.cmd('sql db replica set-primary -g {} -s {} -n {} --allow-data-loss'
                 .format(s3.group, s3.name, database_name),
                 checks=[NoneCheck()])

        # s3 should still be the primary.
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].role', 'Primary'),
                     JMESPathCheck('[0].partnerRole', 'Secondary')])

        # Force failover back to s1
        self.cmd('sql db replica set-primary -g {} -s {} -n {} --allow-data-loss'
                 .format(s1.group, s1.name, database_name),
                 checks=[NoneCheck()])


class SqlElasticPoolsMgmtScenarioTest(ScenarioTest):
    def __init__(self, method_name):
        super(SqlElasticPoolsMgmtScenarioTest, self).__init__(method_name)
        self.pool_name = "cliautomationpool01"

    def verify_activities(self, activities, resource_group, server):
        if isinstance(activities, list.__class__):
            raise AssertionError("Actual value '{}' expected to be list class."
                                 .format(activities))

        for activity in activities:
            if isinstance(activity, dict.__class__):
                raise AssertionError("Actual value '{}' expected to be dict class"
                                     .format(activities))
            if activity['resourceGroup'] != resource_group:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['resourceGroup'], resource_group))
            elif activity['serverName'] != server:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['serverName'], server))
            elif activity['currentElasticPoolName'] != self.pool_name:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['currentElasticPoolName'], self.pool_name))
        return True

    @ResourceGroupPreparer(location='eastus2')
    @SqlServerPreparer(location='eastus2')
    @AllowLargeResponse()
    def test_sql_elastic_pools_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb02"
        pool_name2 = "cliautomationpool02"
        edition = 'Standard'

        dtu = 1200
        db_dtu_min = 10
        db_dtu_max = 50
        storage = '1200GB'
        storage_mb = 1228800

        updated_dtu = 50
        updated_db_dtu_min = 10
        updated_db_dtu_max = 50
        updated_storage = '50GB'
        updated_storage_mb = 51200

        db_service_objective = 'S1'

        # test sql elastic-pool commands
        elastic_pool_1 = self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                                  '--dtu {} --edition {} --db-dtu-min {} --db-dtu-max {} '
                                  '--storage {}'
                                  .format(resource_group, server, self.pool_name, dtu,
                                          edition, db_dtu_min, db_dtu_max, storage),
                                  checks=[
                                      JMESPathCheck('resourceGroup', resource_group),
                                      JMESPathCheck('name', self.pool_name),
                                      JMESPathCheck('location', resource_group_location),
                                      JMESPathCheck('state', 'Ready'),
                                      JMESPathCheck('dtu', dtu),
                                      JMESPathCheck('sku.capacity', dtu),
                                      JMESPathCheck('databaseDtuMin', db_dtu_min),
                                      JMESPathCheck('databaseDtuMax', db_dtu_max),
                                      JMESPathCheck('perDatabaseSettings.minCapacity', db_dtu_min),
                                      JMESPathCheck('perDatabaseSettings.maxCapacity', db_dtu_max),
                                      JMESPathCheck('edition', edition),
                                      JMESPathCheck('sku.tier', edition)]).get_output_in_json()

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('databaseDtuMin', db_dtu_min),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('storageMb', storage_mb),
                     JMESPathCheck('zoneRedundant', False)])

        self.cmd('sql elastic-pool show --id {}'
                 .format(elastic_pool_1['id']),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('databaseDtuMin', db_dtu_min),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('storageMb', storage_mb)])

        self.cmd('sql elastic-pool list -g {} --server {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('[0].resourceGroup', resource_group),
                     JMESPathCheck('[0].name', self.pool_name),
                     JMESPathCheck('[0].state', 'Ready'),
                     JMESPathCheck('[0].databaseDtuMin', db_dtu_min),
                     JMESPathCheck('[0].databaseDtuMax', db_dtu_max),
                     JMESPathCheck('[0].edition', edition),
                     JMESPathCheck('[0].storageMb', storage_mb)])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--dtu {} --storage {} --set tags.key1=value1'
                 .format(resource_group, server, self.pool_name,
                         updated_dtu, updated_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', updated_dtu),
                     JMESPathCheck('sku.capacity', updated_dtu),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('databaseDtuMin', db_dtu_min),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('perDatabaseSettings.minCapacity', db_dtu_min),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', db_dtu_max),
                     JMESPathCheck('storageMb', updated_storage_mb),
                     JMESPathCheck('maxSizeBytes', updated_storage_mb * 1024 * 1024),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql elastic-pool update --id {} '
                 '--dtu {} --db-dtu-min {} --db-dtu-max {} --storage {}'
                 .format(elastic_pool_1['id'], dtu,
                         updated_db_dtu_min, updated_db_dtu_max,
                         storage),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', dtu),
                     JMESPathCheck('sku.capacity', dtu),
                     JMESPathCheck('databaseDtuMin', updated_db_dtu_min),
                     JMESPathCheck('databaseDtuMax', updated_db_dtu_max),
                     JMESPathCheck('perDatabaseSettings.minCapacity', updated_db_dtu_min),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', updated_db_dtu_max),
                     JMESPathCheck('storageMb', storage_mb),
                     JMESPathCheck('maxSizeBytes', storage_mb * 1024 * 1024),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--remove tags.key1'
                 .format(resource_group, server, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('tags', {})])

        # create a second pool with minimal params
        elastic_pool_2 = self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                                  .format(resource_group, server, pool_name2),
                                  checks=[
                                      JMESPathCheck('resourceGroup', resource_group),
                                      JMESPathCheck('name', pool_name2),
                                      JMESPathCheck('location', resource_group_location),
                                      JMESPathCheck('state', 'Ready')]).get_output_in_json()

        self.cmd('sql elastic-pool list -g {} -s {}'.format(resource_group, server),
                 checks=[JMESPathCheck('length(@)', 2)])

        # Create a database directly in an Azure sql elastic pool.
        # Note that 'elasticPoolName' is populated in transform
        # func which only runs after `show`/`list` commands.
        self.cmd('sql db create -g {} --server {} --name {} '
                 '--elastic-pool {}'
                 .format(resource_group, server, database_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolId', elastic_pool_1['id']),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(resource_group, server, database_name),
                 checks=[JMESPathCheck('elasticPoolName', self.pool_name)])

        if self.is_live:
            sleep(120)

        # Move database to second pool by specifying pool name.
        # Also specify service objective just for fun.
        # Note that 'elasticPoolName' is populated in transform
        # func which only runs after `show`/`list` commands.
        self.cmd('sql db update -g {} -s {} -n {} --elastic-pool {}'
                 ' --service-objective ElasticPool'
                 .format(resource_group, server, database_name, pool_name2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolId', elastic_pool_2['id']),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(resource_group, server, database_name),
                 checks=[JMESPathCheck('elasticPoolName', pool_name2)])

        if self.is_live:
            sleep(60)

        # Remove database from pool
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {}'
                 .format(resource_group, server, database_name, db_service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('requestedServiceObjectiveName', db_service_objective),
                     JMESPathCheck('status', 'Online')])

        if self.is_live:
            sleep(60)

        # Move database back into pool by specifying pool id.
        # Note that 'elasticPoolName' is populated in transform
        # func which only runs after `show`/`list` commands.
        self.cmd('sql db update -g {} -s {} -n {} --elastic-pool {}'
                 ' --service-objective ElasticPool'
                 .format(resource_group, server, database_name, elastic_pool_1['id']),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolId', elastic_pool_1['id']),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolId', elastic_pool_1['id']),
                     JMESPathCheck('elasticPoolName', self.pool_name),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        # List databases in a pool
        self.cmd('sql elastic-pool list-dbs -g {} -s {} -n {}'
                 .format(resource_group, server, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', resource_group),
                     JMESPathCheck('[0].name', database_name),
                     JMESPathCheck('[0].elasticPoolName', self.pool_name)])

        # List databases in a pool - alternative command
        self.cmd('sql db list -g {} -s {} --elastic-pool {}'
                 .format(resource_group, server, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', resource_group),
                     JMESPathCheck('[0].name', database_name),
                     JMESPathCheck('[0].elasticPoolName', self.pool_name)])

        # delete sql server database
        self.cmd('sql db delete -g {} --server {} --name {} --yes'
                 .format(resource_group, server, database_name),
                 checks=[NoneCheck()])

        # delete sql elastic pool
        self.cmd('sql elastic-pool delete -g {} --server {} --name {}'
                 .format(resource_group, server, self.pool_name),
                 checks=[NoneCheck()])

        # delete sql elastic pool by id
        self.cmd('sql elastic-pool delete --id {}'
                 .format(elastic_pool_1['id']),
                 checks=[NoneCheck()])

    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    @AllowLargeResponse()
    def test_sql_elastic_pools_vcore_mgmt(self, resource_group, resource_group_location, server):
        pool_name = "cliautomationpool1"

        # Create pool with vcore edition
        vcore_edition = 'GeneralPurpose'
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {}'
                 .format(resource_group, server, pool_name, vcore_edition),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition)])

        # Update pool to dtu edition
        dtu_edition = 'Standard'
        dtu_capacity = 100
        db_dtu_max = 10
        self.cmd('sql elastic-pool update -g {} --server {} --name {} --edition {} --capacity {} --max-size 250GB '
                 '--db-max-dtu {}'
                 .format(resource_group, server, pool_name, dtu_edition, dtu_capacity, db_dtu_max),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('edition', dtu_edition),
                     JMESPathCheck('sku.tier', dtu_edition),
                     JMESPathCheck('dtu', dtu_capacity),
                     JMESPathCheck('sku.capacity', dtu_capacity),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', db_dtu_max)])

        # Update pool back to vcore edition
        vcore_family = 'Gen5'
        vcore_family_updated = 'Gen5'
        vcore_capacity = 4
        self.cmd('sql elastic-pool update -g {} --server {} --name {} -e {} -c {} -f {} '
                 '--db-max-capacity 2'
                 .format(resource_group, server, pool_name, vcore_edition,
                         vcore_capacity, vcore_family),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('dtu', None),
                     JMESPathCheck('sku.capacity', vcore_capacity),
                     JMESPathCheck('sku.family', vcore_family),
                     JMESPathCheck('databaseDtuMin', None),
                     JMESPathCheck('databaseDtuMax', None),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', 2)])

        # Update only capacity
        vcore_capacity_updated = 8
        self.cmd('sql elastic-pool update -g {} -s {} -n {} --capacity {}'
                 .format(resource_group, server, pool_name, vcore_capacity_updated),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('edition', vcore_edition),
                     JMESPathCheck('sku.tier', vcore_edition),
                     JMESPathCheck('dtu', None),
                     JMESPathCheck('sku.capacity', vcore_capacity_updated),
                     JMESPathCheck('sku.family', vcore_family_updated),
                     JMESPathCheck('databaseDtuMin', None),
                     JMESPathCheck('databaseDtuMax', None),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', 2)])

        # Update only edition
        vcore_edition_updated = 'BusinessCritical'
        self.cmd('sql elastic-pool update -g {} -s {} -n {} --tier {}'
                 .format(resource_group, server, pool_name, vcore_edition_updated),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('edition', vcore_edition_updated),
                     JMESPathCheck('sku.tier', vcore_edition_updated),
                     JMESPathCheck('dtu', None),
                     JMESPathCheck('sku.capacity', vcore_capacity_updated),
                     JMESPathCheck('sku.family', vcore_family_updated),
                     JMESPathCheck('databaseDtuMin', None),
                     JMESPathCheck('databaseDtuMax', None),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', 2)])

        # Update only db min & max cap
        db_min_capacity_updated = 0.5
        db_max_capacity_updated = 1
        self.cmd('sql elastic-pool update -g {} -s {} -n {} --db-max-capacity {} --db-min-capacity {}'
                 .format(resource_group, server, pool_name, db_max_capacity_updated, db_min_capacity_updated),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('edition', vcore_edition_updated),
                     JMESPathCheck('sku.tier', vcore_edition_updated),
                     JMESPathCheck('dtu', None),
                     JMESPathCheck('sku.capacity', vcore_capacity_updated),
                     JMESPathCheck('sku.family', vcore_family_updated),
                     JMESPathCheck('databaseDtuMin', None),
                     JMESPathCheck('databaseDtuMax', None),
                     JMESPathCheck('perDatabaseSettings.minCapacity', db_min_capacity_updated),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', db_max_capacity_updated)])

        # Create pool with vcore edition and all sku properties specified
        pool_name_2 = 'cliautomationpool2'
        vcore_edition = 'GeneralPurpose'
        self.cmd('sql elastic-pool create -g {} --server {} --name {} -e {} -c {} -f {}'
                 .format(resource_group, server, pool_name_2,
                         vcore_edition_updated, vcore_capacity_updated,
                         vcore_family_updated),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_2),
                     JMESPathCheck('edition', vcore_edition_updated),
                     JMESPathCheck('sku.tier', vcore_edition_updated),
                     JMESPathCheck('dtu', None),
                     JMESPathCheck('sku.capacity', vcore_capacity_updated),
                     JMESPathCheck('sku.family', vcore_family_updated),
                     JMESPathCheck('databaseDtuMin', None),
                     JMESPathCheck('databaseDtuMax', None)])


class SqlElasticPoolOperationMgmtScenarioTest(ScenarioTest):
    def __init__(self, method_name):
        super(SqlElasticPoolOperationMgmtScenarioTest, self).__init__(method_name)
        self.pool_name = "operationtestep1"

    @ResourceGroupPreparer(location='westeurope')
    @SqlServerPreparer(location='westeurope')
    @AllowLargeResponse()
    def test_sql_elastic_pool_operation_mgmt(self, resource_group, resource_group_location, server):
        edition = 'Premium'
        dtu = 125
        db_dtu_min = 0
        db_dtu_max = 50
        storage = '50GB'
        storage_mb = 51200

        update_dtu = 250
        update_db_dtu_min = 50
        update_db_dtu_max = 250

        # Create elastic pool
        self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                 '--dtu {} --edition {} --db-dtu-min {} --db-dtu-max {} --storage {}'
                 .format(resource_group, server, self.pool_name, dtu, edition, db_dtu_min, db_dtu_max, storage),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', dtu),
                     JMESPathCheck('sku.capacity', dtu),
                     JMESPathCheck('databaseDtuMin', db_dtu_min),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('perDatabaseSettings.minCapacity', db_dtu_min),
                     JMESPathCheck('perDatabaseSettings.maxCapacity', db_dtu_max),
                     JMESPathCheck('storageMb', storage_mb),
                     JMESPathCheck('maxSizeBytes', storage_mb * 1024 * 1024)])

        # Update elastic pool
        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--dtu {} --db-dtu-min {} --db-dtu-max {}'
                 .format(resource_group, server, self.pool_name, update_dtu, update_db_dtu_min, update_db_dtu_max))

        # List operations on the elastic pool
        ops = list(self.cmd('sql elastic-pool op list -g {} --server {} --elastic-pool {}'
                            .format(resource_group, server, self.pool_name)).get_output_in_json())

        # Cancel operation
        try:
            self.cmd('sql elastic-pool op cancel -g {} --server {} --elastic-pool {} --name {}'
                     .format(resource_group, server, self.pool_name, ops[0]['name']))
        except Exception as e:
            expectedmessage = "Cannot cancel management operation {} in current state.".format(ops[0]['name'])
            if expectedmessage in str(e):
                pass


class SqlServerCapabilityScenarioTest(ScenarioTest):
    @AllowLargeResponse()
    def test_sql_capabilities(self):
        location = 'westeurope'
        # New capabilities are added quite frequently and the state of each capability depends
        # on your subscription. So it's not a good idea to make strict checks against exactly
        # which capabilities are returned. The idea is to just check the overall structure.

        db_max_size_length_jmespath = 'length([].supportedServiceLevelObjectives[].supportedMaxSizes[])'

        # Get all db capabilities
        self.cmd('sql db list-editions -l {}'.format(location),
                 checks=[
                     # At least system, standard, and premium edition exist
                     JMESPathCheckExists("[?name == 'System']"),
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheckExists("[?name == 'Premium']"),
                     # At least s0 and p1 service objectives exist
                     JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'S0']"),
                     JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'P1']"),
                     # Max size data is omitted
                     JMESPathCheck(db_max_size_length_jmespath, 0)])

        # Get all available db capabilities
        self.cmd('sql db list-editions -l {} --available'.format(location),
                 checks=[
                     # System edition is not available
                     JMESPathCheck("length([?name == 'System'])", 0),
                     # At least standard and premium edition exist
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheckExists("[?name == 'Premium']"),
                     # At least s0 and p1 service objectives exist
                     JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'S0']"),
                     JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'P1']"),
                     # Max size data is omitted
                     JMESPathCheck(db_max_size_length_jmespath, 0)])

        # Get all db capabilities with size data
        self.cmd('sql db list-editions -l {} --show-details max-size'.format(location),
                 checks=[
                     # Max size data is included
                     JMESPathCheckGreaterThan(db_max_size_length_jmespath, 0)])

        # Search for db edition - note that it's case insensitive
        self.cmd('sql db list-editions -l {} --edition standard'.format(location),
                 checks=[
                     # Standard edition exists, other editions don't
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheck("length([?name != 'Standard'])", 0)])

        # Search for dtus
        self.cmd('sql db list-editions -l {} --dtu 100'.format(location),
                 checks=[
                     # All results have 100 dtu
                     JMESPathCheckGreaterThan(
                         'length([].supportedServiceLevelObjectives[?performanceLevel.value == `100`][])', 0),
                     JMESPathCheck('length([].supportedServiceLevelObjectives[?performanceLevel.value != `100`][])', 0),
                     JMESPathCheck('length([].supportedServiceLevelObjectives[?performanceLevel.unit != `DTU`][])', 0)])

        # Search for vcores
        self.cmd('sql db list-editions -l {} --vcore 2'.format(location),
                 checks=[
                     # All results have 2 vcores
                     JMESPathCheckGreaterThan(
                         'length([].supportedServiceLevelObjectives[?performanceLevel.value == `2`][])', 0),
                     JMESPathCheck('length([].supportedServiceLevelObjectives[?performanceLevel.value != `2`][])', 0),
                     JMESPathCheck('length([].supportedServiceLevelObjectives[?performanceLevel.unit != `VCores`][])',
                                   0)])

        # Search for db service objective - note that it's case insensitive
        # Checked items:
        #   * Standard edition exists, other editions don't
        #   * S0 service objective exists, others don't exist
        self.cmd('sql db list-editions -l {} --edition standard --service-objective s0'.format(location),
                 checks=[JMESPathCheckExists("[?name == 'Standard']"),
                         JMESPathCheck("length([?name != 'Standard'])", 0),
                         JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'S0']"),
                         JMESPathCheck("length([].supportedServiceLevelObjectives[] | [?name != 'S0'])", 0)])

        pool_max_size_length_jmespath = 'length([].supportedElasticPoolPerformanceLevels[].supportedMaxSizes[])'
        pool_db_max_dtu_length_jmespath = 'length([].supportedElasticPoolPerformanceLevels[].supportedPerDatabaseMaxPerformanceLevels[])'
        pool_db_min_dtu_length_jmespath = (
            'length([].supportedElasticPoolPerformanceLevels[].supportedPerDatabaseMaxPerformanceLevels[]'
            '.supportedPerDatabaseMinPerformanceLevels[])')
        pool_db_max_size_length_jmespath = 'length([].supportedElasticPoolPerformanceLevels[].supportedPerDatabaseMaxSizes[])'

        # Get all elastic pool capabilities
        self.cmd('sql elastic-pool list-editions -l {}'.format(location),
                 checks=[JMESPathCheckExists("[?name == 'Standard']"),  # At least standard and premium edition exist
                         JMESPathCheckExists("[?name == 'Premium']"),
                         JMESPathCheck(pool_max_size_length_jmespath, 0),  # Optional details are omitted
                         JMESPathCheck(pool_db_max_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_max_size_length_jmespath, 0)])

        # Search for elastic pool edition - note that it's case insensitive
        self.cmd('sql elastic-pool list-editions -l {} --edition standard'.format(location),
                 checks=[JMESPathCheckExists("[?name == 'Standard']"),  # Standard edition exists, other editions don't
                         JMESPathCheck("length([?name != 'Standard'])", 0)])

        # Search for dtus
        self.cmd('sql elastic-pool list-editions -l {} --dtu 100'.format(location),
                 checks=[
                     # All results have 100 dtu
                     JMESPathCheckGreaterThan(
                         'length([].supportedElasticPoolPerformanceLevels[?performanceLevel.value == `100`][])', 0),
                     JMESPathCheck(
                         'length([].supportedElasticPoolPerformanceLevels[?performanceLevel.value != `100`][])', 0),
                     JMESPathCheck('length([].supportedServiceLevelObjectives[?performanceLevel.unit != `DTU`][])', 0)])

        # Search for vcores
        self.cmd('sql elastic-pool list-editions -l {} --vcore 2'.format(location),
                 checks=[
                     # All results have 2 vcores
                     JMESPathCheckGreaterThan(
                         'length([].supportedElasticPoolPerformanceLevels[?performanceLevel.value == `2`][])', 0),
                     JMESPathCheck('length([].supportedElasticPoolPerformanceLevels[?performanceLevel.value != `2`][])',
                                   0),
                     JMESPathCheck('length([].supportedServiceLevelObjectives[?performanceLevel.unit != `VCores`][])',
                                   0)])

        # Get all db capabilities with pool max size
        self.cmd('sql elastic-pool list-editions -l {} --show-details max-size'.format(location),
                 checks=[JMESPathCheckGreaterThan(pool_max_size_length_jmespath, 0),
                         JMESPathCheck(pool_db_max_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_max_size_length_jmespath, 0)])

        # Get all db capabilities with per db max size
        self.cmd('sql elastic-pool list-editions -l {} --show-details db-max-size'.format(location),
                 checks=[JMESPathCheck(pool_max_size_length_jmespath, 0),
                         JMESPathCheck(pool_db_max_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                         JMESPathCheckGreaterThan(pool_db_max_size_length_jmespath, 0)])

        # Get all db capabilities with per db max dtu
        self.cmd('sql elastic-pool list-editions -l {} --edition standard --show-details db-max-dtu'.format(location),
                 checks=[JMESPathCheck(pool_max_size_length_jmespath, 0),
                         JMESPathCheckGreaterThan(pool_db_max_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_max_size_length_jmespath, 0)])

        # Get all db capabilities with per db min dtu (which is nested under per db max dtu)
        self.cmd('sql elastic-pool list-editions -l {} --edition standard --show-details db-min-dtu'.format(location),
                 checks=[JMESPathCheck(pool_max_size_length_jmespath, 0),
                         JMESPathCheckGreaterThan(pool_db_max_dtu_length_jmespath, 0),
                         JMESPathCheckGreaterThan(pool_db_min_dtu_length_jmespath, 0),
                         JMESPathCheck(pool_db_max_size_length_jmespath, 0)])

        # Get all db capabilities with everything
        self.cmd('sql elastic-pool list-editions -l {} --edition standard --show-details db-min-dtu db-max-dtu '
                 'db-max-size max-size'.format(location),
                 checks=[JMESPathCheckGreaterThan(pool_max_size_length_jmespath, 0),
                         JMESPathCheckGreaterThan(pool_db_max_dtu_length_jmespath, 0),
                         JMESPathCheckGreaterThan(pool_db_min_dtu_length_jmespath, 0),
                         JMESPathCheckGreaterThan(pool_db_max_size_length_jmespath, 0)])


class SqlServerImportExportMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    @SqlServerPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus')
    @AllowLargeResponse()
    def test_sql_db_import_export_mgmt(self, resource_group, resource_group_location, server, storage_account):
        location_long_name = 'eastus'
        admin_login = 'admin123'
        admin_password = 'SecretPassword123'
        db_name = 'cliautomationdb01'
        db_name2 = 'cliautomationdb02'
        db_name3 = 'cliautomationdb03'
        blob = 'testbacpac.bacpac'
        blob2 = 'testbacpac2.bacpac'

        container = 'bacpacs'

        firewall_rule_1 = 'allowAllIps'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '0.0.0.0'

        # create server firewall rule
        self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, resource_group, server,
                         start_ip_address_1, end_ip_address_1),
                 checks=[JMESPathCheck('name', firewall_rule_1),
                         JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('startIpAddress', start_ip_address_1),
                         JMESPathCheck('endIpAddress', end_ip_address_1)])

        # create dbs
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name),
                 checks=[JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('name', db_name),
                         JMESPathCheck('location', location_long_name),
                         JMESPathCheck('elasticPoolId', None),
                         JMESPathCheck('status', 'Online')])

        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name2),
                 checks=[JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('name', db_name2),
                         JMESPathCheck('location', location_long_name),
                         JMESPathCheck('elasticPoolId', None),
                         JMESPathCheck('status', 'Online')])

        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name3),
                 checks=[JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('name', db_name3),
                         JMESPathCheck('location', location_long_name),
                         JMESPathCheck('elasticPoolId', None),
                         JMESPathCheck('status', 'Online')])

        # get storage account endpoint
        storage_endpoint = self.cmd('storage account show -g {} -n {}'
                                    ' --query primaryEndpoints.blob'
                                    .format(resource_group, storage_account)).get_output_in_json()
        bacpacUri = '{}{}/{}'.format(storage_endpoint, container, blob)
        bacpacUri2 = '{}{}/{}'.format(storage_endpoint, container, blob2)

        # get storage account key
        storageKey = self.cmd('storage account keys list -g {} -n {} --query [0].value'
                              .format(resource_group, storage_account)).get_output_in_json()

        # Set Expiry
        expiryString = '9999-12-25T00:00:00Z'

        # Get sas key
        sasKey = self.cmd('storage blob generate-sas --account-name {} -c {} -n {} --permissions rw --expiry {}'.format(
            storage_account, container, blob2, expiryString)).get_output_in_json()

        # create storage account blob container
        self.cmd('storage container create -n {} --account-name {} --account-key {} '
                 .format(container, storage_account, storageKey),
                 checks=[JMESPathCheck('created', True)])

        # export database to blob container using both keys
        self.cmd('sql db export -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type StorageAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name, resource_group, admin_password, admin_login, storageKey, bacpacUri),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri),
                     JMESPathCheck('databaseName', db_name),
                     JMESPathCheck('requestType', 'ExportDatabase'),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])

        self.cmd('sql db export -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type SharedAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name, resource_group, admin_password, admin_login, sasKey, bacpacUri2),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri2),
                     JMESPathCheck('databaseName', db_name),
                     JMESPathCheck('requestType', 'ExportDatabase'),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])

        # import bacpac to second database using Storage Key
        self.cmd('sql db import -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type StorageAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name2, resource_group, admin_password, admin_login, storageKey, bacpacUri),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri),
                     JMESPathCheck('databaseName', db_name2),
                     JMESPathCheck('requestType', 'ImportToExistingDatabase'),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])

        # import bacpac to third database using SAS key
        self.cmd('sql db import -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type SharedAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name3, resource_group, admin_password, admin_login, sasKey, bacpacUri2),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri2),
                     JMESPathCheck('databaseName', db_name3),
                     JMESPathCheck('requestType', 'ImportToExistingDatabase'),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])


class SqlServerConnectionStringScenarioTest(ScenarioTest):
    def test_sql_db_conn_str(self):
        # ADO.NET, username/password
        conn_str = self.cmd('sql db show-connection-string -s myserver -n mydb -c ado.net').get_output_in_json()
        self.assertEqual(conn_str,
                         'Server=tcp:myserver.database.windows.net,1433;Database=mydb;User ID=<username>;Password=<password>;Encrypt=true;Connection Timeout=30;')

        # ADO.NET, ADPassword
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c ado.net -a ADPassword').get_output_in_json()
        self.assertEqual(conn_str,
                         'Server=tcp:myserver.database.windows.net,1433;Database=mydb;User ID=<username>;Password=<password>;Encrypt=true;Connection Timeout=30;Authentication="Active Directory Password"')

        # ADO.NET, ADIntegrated
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c ado.net -a ADIntegrated').get_output_in_json()
        self.assertEqual(conn_str,
                         'Server=tcp:myserver.database.windows.net,1433;Database=mydb;Encrypt=true;Connection Timeout=30;Authentication="Active Directory Integrated"')

        # SqlCmd, username/password
        conn_str = self.cmd('sql db show-connection-string -s myserver -n mydb -c sqlcmd').get_output_in_json()
        self.assertEqual(conn_str,
                         'sqlcmd -S tcp:myserver.database.windows.net,1433 -d mydb -U <username> -P <password> -N -l 30')

        # SqlCmd, ADPassword
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c sqlcmd -a ADPassword').get_output_in_json()
        self.assertEqual(conn_str,
                         'sqlcmd -S tcp:myserver.database.windows.net,1433 -d mydb -U <username> -P <password> -G -N -l 30')

        # SqlCmd, ADIntegrated
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c sqlcmd -a ADIntegrated').get_output_in_json()
        self.assertEqual(conn_str, 'sqlcmd -S tcp:myserver.database.windows.net,1433 -d mydb -G -N -l 30')

        # JDBC, user name/password
        conn_str = self.cmd('sql db show-connection-string -s myserver -n mydb -c jdbc').get_output_in_json()
        self.assertEqual(conn_str,
                         'jdbc:sqlserver://myserver.database.windows.net:1433;database=mydb;user=<username>@myserver;password=<password>;encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=30')

        # JDBC, ADPassword
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c jdbc -a ADPassword').get_output_in_json()
        self.assertEqual(conn_str,
                         'jdbc:sqlserver://myserver.database.windows.net:1433;database=mydb;user=<username>;password=<password>;encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=30;authentication=ActiveDirectoryPassword')

        # JDBC, ADIntegrated
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c jdbc -a ADIntegrated').get_output_in_json()
        self.assertEqual(conn_str,
                         'jdbc:sqlserver://myserver.database.windows.net:1433;database=mydb;encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=30;authentication=ActiveDirectoryIntegrated')

        # PHP PDO, user name/password
        conn_str = self.cmd('sql db show-connection-string -s myserver -n mydb -c php_pdo').get_output_in_json()
        self.assertEqual(conn_str,
                         '$conn = new PDO("sqlsrv:server = tcp:myserver.database.windows.net,1433; Database = mydb; LoginTimeout = 30; Encrypt = 1; TrustServerCertificate = 0;", "<username>", "<password>");')

        # PHP PDO, ADPassword
        self.cmd('sql db show-connection-string -s myserver -n mydb -c php_pdo -a ADPassword', expect_failure=True)

        # PHP PDO, ADIntegrated
        self.cmd('sql db show-connection-string -s myserver -n mydb -c php_pdo -a ADIntegrated', expect_failure=True)

        # PHP, user name/password
        conn_str = self.cmd('sql db show-connection-string -s myserver -n mydb -c php').get_output_in_json()
        self.assertEqual(conn_str,
                         '$connectionOptions = array("UID"=>"<username>@myserver", "PWD"=>"<password>", "Database"=>mydb, "LoginTimeout" => 30, "Encrypt" => 1, "TrustServerCertificate" => 0); $serverName = "tcp:myserver.database.windows.net,1433"; $conn = sqlsrv_connect($serverName, $connectionOptions);')

        # PHP, ADPassword
        self.cmd('sql db show-connection-string -s myserver -n mydb -c php -a ADPassword', expect_failure=True)

        # PHP, ADIntegrated
        self.cmd('sql db show-connection-string -s myserver -n mydb -c php -a ADIntegrated', expect_failure=True)

        # ODBC, user name/password
        conn_str = self.cmd('sql db show-connection-string -s myserver -n mydb -c odbc').get_output_in_json()
        self.assertEqual(conn_str,
                         'Driver={ODBC Driver 13 for SQL Server};Server=tcp:myserver.database.windows.net,1433;Database=mydb;Uid=<username>@myserver;Pwd=<password>;Encrypt=yes;TrustServerCertificate=no;')

        # ODBC, ADPassword
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c odbc -a ADPassword').get_output_in_json()
        self.assertEqual(conn_str,
                         'Driver={ODBC Driver 13 for SQL Server};Server=tcp:myserver.database.windows.net,1433;Database=mydb;Uid=<username>@myserver;Pwd=<password>;Encrypt=yes;TrustServerCertificate=no;Authentication=ActiveDirectoryPassword')

        # ODBC, ADIntegrated
        conn_str = self.cmd(
            'sql db show-connection-string -s myserver -n mydb -c odbc -a ADIntegrated').get_output_in_json()
        self.assertEqual(conn_str,
                         'Driver={ODBC Driver 13 for SQL Server};Server=tcp:myserver.database.windows.net,1433;Database=mydb;Encrypt=yes;TrustServerCertificate=no;Authentication=ActiveDirectoryIntegrated')


class SqlTransparentDataEncryptionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlServerPreparer(location='eastus')
    def test_sql_tde(self, resource_group, server):
        sn = server
        db_name = self.create_random_name("sqltdedb", 20)

        # create database
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, sn, db_name))

        # validate encryption is on by default
        self.cmd('sql db tde show -g {} -s {} -d {}'
                 .format(resource_group, sn, db_name),
                 checks=[JMESPathCheck('state', 'Enabled')])

        # disable encryption
        self.cmd('sql db tde set -g {} -s {} -d {} --status Disabled'
                 .format(resource_group, sn, db_name))

        sleep(5)

        self.cmd('sql db tde show -g {} -s {} -d {}'
                 .format(resource_group, sn, db_name),
                 checks=[JMESPathCheck('state', 'Disabled')])

        # enable encryption
        self.cmd('sql db tde set -g {} -s {} -d {} --status Enabled'
                 .format(resource_group, sn, db_name))

        sleep(5)

        # validate encryption is enabled
        self.cmd('sql db tde show -g {} -s {} -d {}'
                 .format(resource_group, sn, db_name),
                 checks=[JMESPathCheck('state', 'Enabled')])

    @ResourceGroupPreparer(location='eastus')
    @SqlServerPreparer(location='eastus')
    @KeyVaultPreparer(location='eastus', name_prefix='sqltdebyok')
    def test_sql_tdebyok(self, resource_group, server, key_vault):
        resource_prefix = 'sqltdebyok'

        # add identity to server
        server_resp = self.cmd('sql server update -g {} -n {} -i'
                               .format(resource_group, server)).get_output_in_json()
        server_identity = server_resp['identity']['principalId']

        # create db
        db_name = self.create_random_name(resource_prefix, 20)
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name))

        # create vault and acl server identity
        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions wrapKey unwrapKey get list'
                 .format(resource_group, key_vault, server_identity))

        # create key
        key_name = self.create_random_name(resource_prefix, 32)
        key_resp = self.cmd('keyvault key create -n {} -p software --vault-name {}'
                            .format(key_name, key_vault)).get_output_in_json()
        kid = key_resp['key']['kid']

        # add server key
        server_key_resp = self.cmd('sql server key create -g {} -s {} -k {}'
                                   .format(resource_group, server, kid),
                                   checks=[
                                       JMESPathCheck('uri', kid),
                                       JMESPathCheck('serverKeyType', 'AzureKeyVault')])
        server_key_name = server_key_resp.get_output_in_json()['name']

        # validate show key
        self.cmd('sql server key show -g {} -s {} -k {}'
                 .format(resource_group, server, kid),
                 checks=[
                     JMESPathCheck('uri', kid),
                     JMESPathCheck('serverKeyType', 'AzureKeyVault'),
                     JMESPathCheck('name', server_key_name)])

        # validate list key (should return 2 items)
        self.cmd('sql server key list -g {} -s {}'
                 .format(resource_group, server),
                 checks=[JMESPathCheck('length(@)', 2)])

        # validate encryption protector is service managed via show
        self.cmd('sql server tde-key show -g {} -s {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('serverKeyType', 'ServiceManaged'),
                     JMESPathCheck('serverKeyName', 'ServiceManaged')])

        # update encryption protector to akv key
        self.cmd('sql server tde-key set -g {} -s {} -t AzureKeyVault -k {} --auto-rotation-enabled'
                 .format(resource_group, server, kid),
                 checks=[
                     JMESPathCheck('serverKeyType', 'AzureKeyVault'),
                     JMESPathCheck('serverKeyName', server_key_name),
                     JMESPathCheck('uri', kid)])
                     # JMESPathCheck('autoRotationEnabled', True) - property is removed from backend
                     

        # validate encryption protector is akv via show
        self.cmd('sql server tde-key show -g {} -s {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('serverKeyType', 'AzureKeyVault'),
                     JMESPathCheck('serverKeyName', server_key_name),
                     JMESPathCheck('uri', kid)])

        # update encryption protector to service managed
        self.cmd('sql server tde-key set -g {} -s {} -t ServiceManaged'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('serverKeyType', 'ServiceManaged'),
                     JMESPathCheck('serverKeyName', 'ServiceManaged')])

        # validate encryption protector is service managed via show
        self.cmd('sql server tde-key show -g {} -s {}'
                 .format(resource_group, server),
                 checks=[
                     JMESPathCheck('serverKeyType', 'ServiceManaged'),
                     JMESPathCheck('serverKeyName', 'ServiceManaged')])

        # delete server key
        self.cmd('sql server key delete -g {} -s {} -k {}'
                 .format(resource_group, server, kid))

        # wait for key to be deleted
        time.sleep(10)

        # validate deleted server key via list (should return 1 item)
        self.cmd('sql server key list -g {} -s {}'
                 .format(resource_group, server),
                 checks=[JMESPathCheck('length(@)', 1)])


class SqlServerIdentityTest(ScenarioTest):

    @AllowLargeResponse()
    def test_sql_server_identity(self):
        server_name_test = 'umitest'
        server_name = self.create_random_name(server_name_test, managed_instance_name_max_length)
        admin_login = 'admin123'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']
        families = ['Gen5']

        subnet = '/subscriptions/e64f3e8e-ab91-4a65-8cdd-5cd2f47d00b4/resourceGroups/alswansotest3-rg/providers/Microsoft.Network/virtualNetworks/vnet-alswansotestmi/subnets/ManagedInstance'

        license_type = 'LicenseIncluded'
        loc = 'eastus2euap'
        v_cores = 4
        storage_size_in_gb = '32'
        edition = 'GeneralPurpose'
        resource_group_1 = "alswansotest3-rg"
        collation = "SQL_Latin1_General_CP1_CI_AS"
        proxy_override = "Proxy"

        test_umi = '/subscriptions/e64f3e8e-ab91-4a65-8cdd-5cd2f47d00b4/resourceGroups/viparek/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi'
        umi_list = '/subscriptions/e64f3e8e-ab91-4a65-8cdd-5cd2f47d00b4/resourceGroups/viparek/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi'

        identity_type = ResourceIdType.system_assigned_user_assigned.value
        user = admin_login

        self.cmd('sql server create -g {} -n {} -l {} -i '
                 '--admin-user {} --admin-password {} --user-assigned-identity-id {} --identity-type {} --pid {}'
                 .format(resource_group_1, server_name, loc, user, admin_passwords[0], umi_list, identity_type,
                         test_umi),
                 checks=[
                     JMESPathCheck('name', server_name),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', user),
                     JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned')])

        # test show sql server
        self.cmd('sql server show -g {} --name {}'
                 .format(resource_group_1, server_name),
                 checks=[
                     JMESPathCheck('name', server_name),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('sql server delete -g {} -n {} --yes'
                 .format(resource_group_1, server_name), checks=NoneCheck())

        # test show sql server doesn't return anything
        self.cmd('sql server show -g {} -n {}'
                 .format(resource_group_1, server_name),
                 expect_failure=True)


class SqlServerVnetMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    @SqlServerPreparer(location='eastus')
    def test_sql_vnet_mgmt(self, resource_group, resource_group_location, server):
        vnet_rule_1 = 'rule1'
        vnet_rule_2 = 'rule2'

        # Create vnet's - vnet1 and vnet2

        vnetName1 = 'vnet1'
        vnetName2 = 'vnet2'
        subnetName = 'subnet1'
        addressPrefix = '10.0.1.0/24'
        endpoint = 'Microsoft.Sql'

        # Vnet 1 without service endpoints to test ignore-missing-vnet-service-endpoint feature
        self.cmd('network vnet create -g {} -n {}'.format(resource_group, vnetName1))
        self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefix {}'
                 .format(resource_group, vnetName1, subnetName, addressPrefix))

        vnet1 = self.cmd('network vnet subnet show -n {} --vnet-name {} -g {}'
                         .format(subnetName, vnetName1, resource_group)).get_output_in_json()
        vnet_id_1 = vnet1['id']

        # Vnet 2
        self.cmd('network vnet create -g {} -n {}'.format(resource_group, vnetName2))
        self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefix {} --service-endpoints {}'
                 .format(resource_group, vnetName2, subnetName, addressPrefix, endpoint),
                 checks=JMESPathCheck('serviceEndpoints[0].service', 'Microsoft.Sql'))

        vnet2 = self.cmd('network vnet subnet show -n {} --vnet-name {} -g {}'
                         .format(subnetName, vnetName2, resource_group)).get_output_in_json()
        vnet_id_2 = vnet2['id']

        # test sql server vnet-rule create using subnet name and vnet name and ignore-missing-vnet-service-endpoint flag
        self.cmd('sql server vnet-rule create --name {} -g {} --server {} --subnet {} --vnet-name {} -i'
                 .format(vnet_rule_1, resource_group, server, subnetName, vnetName1))

        # test sql server vnet-rule show rule 1
        self.cmd('sql server vnet-rule show --name {} -g {} --server {}'
                 .format(vnet_rule_1, resource_group, server),
                 checks=[
                     JMESPathCheck('name', vnet_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('ignoreMissingVnetServiceEndpoint', True)])

        # test sql server vnet-rule create using subnet id
        self.cmd('sql server vnet-rule create --name {} -g {} --server {} --subnet {}'
                 .format(vnet_rule_2, resource_group, server, vnet_id_2),
                 checks=[
                     JMESPathCheck('name', vnet_rule_2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('virtualNetworkSubnetId', vnet_id_2),
                     JMESPathCheck('ignoreMissingVnetServiceEndpoint', False)])

        # test sql server vnet-rule update rule 1 with vnet 2
        self.cmd('sql server vnet-rule update --name {} -g {} --server {} --subnet {}'
                 .format(vnet_rule_1, resource_group, server, vnet_id_2),
                 checks=[
                     JMESPathCheck('name', vnet_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('virtualNetworkSubnetId', vnet_id_2),
                     JMESPathCheck('ignoreMissingVnetServiceEndpoint', False)])

        # test sql server vnet-rule update rule 2 with vnet 1 and ignore-missing-vnet-service-endpoint flag
        self.cmd('sql server vnet-rule update --name {} -g {} --server {} --subnet {} -i'
                 .format(vnet_rule_2, resource_group, server, vnet_id_1),
                 checks=[JMESPathCheck('name', vnet_rule_2),
                         JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('virtualNetworkSubnetId', vnet_id_1),
                         JMESPathCheck('ignoreMissingVnetServiceEndpoint', True)])

        # test sql server vnet-rule list
        self.cmd('sql server vnet-rule list -g {} --server {}'.format(resource_group, server),
                 checks=[JMESPathCheck('length(@)', 2)])

        # test sql server vnet-rule delete rule 1
        self.cmd('sql server vnet-rule delete --name {} -g {} --server {}'.format(vnet_rule_1, resource_group, server),
                 checks=NoneCheck())

        # test sql server vnet-rule delete rule 2
        self.cmd('sql server vnet-rule delete --name {} -g {} --server {}'.format(vnet_rule_2, resource_group, server),
                 checks=NoneCheck())


class SqlSubscriptionUsagesScenarioTest(ScenarioTest):
    def test_sql_subscription_usages(self):
        self.cmd('sql list-usages -l westus',
                 checks=[JMESPathCheckGreaterThan('length(@)', 0)])

        self.cmd('sql show-usage -l westus -u ServerQuota',
                 checks=[
                     JMESPathCheck('name', 'ServerQuota'),
                     JMESPathCheckGreaterThan('limit', 0)])


class SqlZoneResilienceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    @SqlServerPreparer(location='eastus')
    @AllowLargeResponse()
    def test_sql_zone_resilient_database(self, resource_group, resource_group_location, server):
        database_name = "createUnzonedUpdateToZonedDb"
        database_name_2 = "createZonedUpdateToUnzonedDb"
        database_name_3 = "updateNoParamForUnzonedDb"
        database_name_4 = "updateNoParamForZonedDb"

        # Test creating database with zone resilience set to false.  Expect regular database created.
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --zone-redundant {}'
                 .format(resource_group, server, database_name, "Premium", False),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', False)])

        # Test running update on regular database with zone resilience set to true.  Expect zone resilience to update to true.
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {} --zone-redundant'
                 .format(resource_group, server, database_name, 'P1'),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('status', 'Online'),
                     JMESPathCheck('requestedServiceObjectiveName', 'P1'),
                     JMESPathCheck('zoneRedundant', True)])

        # Test creating database with zone resilience set to true.  Expect zone resilient database created.
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --z'
                 .format(resource_group, server, database_name_2, "Premium"),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', True)])

        # Test running update on zoned database with zone resilience set to false.  Expect zone resilience to update to false
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {} --z {}'
                 .format(resource_group, server, database_name_2, 'P1', False),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_2),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('status', 'Online'),
                     JMESPathCheck('requestedServiceObjectiveName', 'P1'),
                     JMESPathCheck('zoneRedundant', False)])

        # Create database with no zone resilience set.  Expect regular database created.
        self.cmd('sql db create -g {} --server {} --name {} --edition {}'
                 .format(resource_group, server, database_name_3, "Premium"),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', False)])

        # Test running update on regular database with no zone resilience set.  Expect zone resilience to stay false.
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {}'
                 .format(resource_group, server, database_name_3, 'P2'),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_3),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('status', 'Online'),
                     JMESPathCheck('requestedServiceObjectiveName', 'P2'),
                     JMESPathCheck('zoneRedundant', False)])

        # Create database with zone resilience set.  Expect zone resilient database created.
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --zone-redundant'
                 .format(resource_group, server, database_name_4, "Premium"),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_4),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', True)])

        # Test running update on zoned database with no zone resilience set.  Expect zone resilience to stay true.
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {}'
                 .format(resource_group, server, database_name_4, 'P2'),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_4),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('status', 'Online'),
                     JMESPathCheck('requestedServiceObjectiveName', 'P2'),
                     JMESPathCheck('zoneRedundant', True)])

    @ResourceGroupPreparer(location='eastus')
    @SqlServerPreparer(location='eastus')
    @AllowLargeResponse()
    def test_sql_zone_resilient_pool(self, resource_group, resource_group_location, server):
        pool_name = "createUnzonedUpdateToZonedPool"
        pool_name_2 = "createZonedUpdateToUnzonedPool"
        pool_name_3 = "updateNoParamForUnzonedPool"
        pool_name_4 = "updateNoParamForZonedPool"

        # Test creating pool with zone resilience set to false.  Expect regular pool created.
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {} --z {}'
                 .format(resource_group, server, pool_name, "Premium", False))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('zoneRedundant', False)])

        # Test running update on regular pool with zone resilience set to true.  Expect zone resilience to update to true
        self.cmd('sql elastic-pool update -g {} -s {} -n {} --z'
                 .format(resource_group, server, pool_name))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name),
                     JMESPathCheck('zoneRedundant', True)])

        # Test creating pool with zone resilience set to true.  Expect zone resilient pool created.
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {} --zone-redundant'
                 .format(resource_group, server, pool_name_2, "Premium"))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_2),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('zoneRedundant', True)])

        # Test running update on zoned pool with zone resilience set to false.  Expect zone resilience to update to false
        self.cmd('sql elastic-pool update -g {} -s {} -n {} --zone-redundant {}'
                 .format(resource_group, server, pool_name_2, False))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_2),
                     JMESPathCheck('zoneRedundant', False)])

        # Create pool with no zone resilience set.  Expect regular pool created.
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {}'
                 .format(resource_group, server, pool_name_3, "Premium"))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name_3),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_3),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('zoneRedundant', False)])

        # Test running update on regular pool with no zone resilience set.  Expect zone resilience to stay false
        self.cmd('sql elastic-pool update -g {} -s {} -n {} --dtu {}'
                 .format(resource_group, server, pool_name_3, 250))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name_3),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_3),
                     JMESPathCheck('dtu', 250),
                     JMESPathCheck('zoneRedundant', False)])

        # Create pool with zone resilience set.  Expect zone resilient pool created.
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {} --zone-redundant'
                 .format(resource_group, server, pool_name_4, "Premium"))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name_4),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_4),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('zoneRedundant', True)])

        # Test running update on zoned pool with no zone resilience set.  Expect zone resilience to stay true
        self.cmd('sql elastic-pool update -g {} -s {} -n {} --dtu {}'
                 .format(resource_group, server, pool_name_4, 250))

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(resource_group, server, pool_name_4),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_4),
                     JMESPathCheck('dtu', 250),
                     JMESPathCheck('zoneRedundant', True)])

    @ResourceGroupPreparer(location='eastus2euap')
    @SqlServerPreparer(location='eastus2euap')
    @AllowLargeResponse()
    def test_sql_zone_resilient_copy_hyperscale_database(self, resource_group, server):
        # Set db names
        source_non_zr_db_name = "sourceNonZrDb"
        source_zr_db_name = "sourceZrDb"
        copy_source_non_zr_true_param_db_name = "copySourceNonZrTrueParamDb"
        copy_source_zr_false_param_db_name = "copySourceZrFalseParamDb"
        copy_source_non_zr_no_param_db_name = "copySourceNonZrNoParamDb"
        copy_source_zr_no_param_db_name = "copySourceZrNoParamDb"

        # Create non zone redundant source vldb
        # Verify created vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Geo)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}'
                 .format(resource_group, server, source_non_zr_db_name, "Hyperscale", 'Gen5', 2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', source_non_zr_db_name),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
                     JMESPathCheck('requestedBackupStorageRedundancy', 'Geo'),
                     JMESPathCheck('zoneRedundant', False)])

		# Create zone redundant source vldb with zone redundancy == true and backup storage redundancy == Zone 
        # Verify created vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}  --backup-storage-redundancy {} --zone-redundant {}'
                 .format(resource_group, server, source_zr_db_name, "Hyperscale", 'Gen5', 2, 'zone', True),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', source_zr_db_name),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

        # Copy non zone redundant source vldb with zone redundancy == true and backup storage redundancy == Zone
        # Verify copied vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db copy -g {} --server {} --name {} --dest-name {} --backup-storage-redundancy {} --z'
                 .format(resource_group, server, source_non_zr_db_name, copy_source_non_zr_true_param_db_name, 'zone'),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', copy_source_non_zr_true_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

        # Copy zone redundant source vldb with zone redundancy == false
        # Verify copied vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Zone)
        self.cmd('sql db copy -g {} --server {} --name {} --dest-name {} --zone-redundant {}'
                 .format(resource_group, server, source_zr_db_name, copy_source_zr_false_param_db_name, False),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', copy_source_zr_false_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', False)])

        # Copy non zone redundant source vldb with no parameters passed in
        # Verify copied vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Geo)
        self.cmd('sql db copy -g {} --server {} --name {} --dest-name {}'
                 .format(resource_group, server, source_non_zr_db_name, copy_source_non_zr_no_param_db_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', copy_source_non_zr_no_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Geo'),
                     JMESPathCheck('zoneRedundant', False)])

        # Copy zone redundant source vldb with no parameters passed in
        # Verify copied vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db copy -g {} --server {} --name {} --dest-name {}'
                 .format(resource_group, server, source_zr_db_name, copy_source_zr_no_param_db_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', copy_source_zr_no_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

    @ResourceGroupPreparer(parameter_name="resource_group_pri", location='eastus2euap')
    @SqlServerPreparer(parameter_name="server_name_pri", resource_group_parameter_name="resource_group_pri",location='eastus2euap')
    @ResourceGroupPreparer(parameter_name="resource_group_sec", location='eastus2euap')
    @SqlServerPreparer(parameter_name="server_name_sec", resource_group_parameter_name="resource_group_sec",location='eastus2euap')
    @AllowLargeResponse()
    def test_sql_zone_resilient_replica_hyperscale_database(self, resource_group_pri, server_name_pri, resource_group_sec, server_name_sec):
        # Set db names
        non_zr_db_name_1 = "nonZrDb1"
        zr_db_name_1 = "zrDb1"
        non_zr_db_name_2 = "nonZrDb2"
        zr_db_name_2 = "zrDb2"
        pri_non_zr_true_param_db_name = "priNonZrTrueParamDb"
        pri_zr_false_param_db_name = "priZrFalseParamDb"
        pri_non_zr_no_param_db_name = "priNonZrNoParamDb"
        pri_zr_no_param_db_name = "priZrNoParamDb"

        # Create non zone redundant primary vldb
        # Verify created vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Geo)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}'
                 .format(resource_group_pri, server_name_pri, non_zr_db_name_1, "Hyperscale", 'Gen5', 2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_pri),
                     JMESPathCheck('name', non_zr_db_name_1),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
                     JMESPathCheck('requestedBackupStorageRedundancy', 'Geo'),
                     JMESPathCheck('zoneRedundant', False)])

        # Create secondary vldb replica from non zone redundant primary vldb with zone redundancy == true and backup storage redundancy == Zone
        # Verify created secondary vldb replica has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-resource-group {} --partner-server {} '
                 '--partner-database {} --backup-storage-redundancy {} --z'
                 .format(resource_group_pri, server_name_pri, non_zr_db_name_1, 
                         resource_group_sec, server_name_sec, pri_non_zr_true_param_db_name, 'zone'),
                 checks=[
					 JMESPathCheck('name', pri_non_zr_true_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

		# Create zone redundant primary vldb with zone redundancy == true and backup storage redundancy == Zone 
        # Verify created vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}  --backup-storage-redundancy {} --zone-redundant {}'
                 .format(resource_group_pri, server_name_pri, zr_db_name_1, "Hyperscale", 'Gen5', 2, 'zone', True),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_pri),
                     JMESPathCheck('name', zr_db_name_1),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

        # Create secondary vldb replica from zone redundant primary vldb with zone redundancy == false
        # Verify created secondary vldb replica has correct values (specifically zone redundancy == false and backup storage redundancy == Zone)
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-resource-group {} --partner-server {} '
                 '--partner-database {} --z {}'
                 .format(resource_group_pri, server_name_pri, zr_db_name_1, 
                         resource_group_sec, server_name_sec, pri_zr_false_param_db_name, False),
                 checks=[
					 JMESPathCheck('name', pri_zr_false_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', False)])

        # Create non zone redundant primary vldb
        # Verify created vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Geo)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}'
                 .format(resource_group_pri, server_name_pri, non_zr_db_name_2, "Hyperscale", 'Gen5', 2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_pri),
                     JMESPathCheck('name', non_zr_db_name_2),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
                     JMESPathCheck('requestedBackupStorageRedundancy', 'Geo'),
                     JMESPathCheck('zoneRedundant', False)])

        # Create secondary vldb replica from non zone redundant primary vldb with no parameters passed in
        # Verify created secondary vldb replica has correct values (specifically zone redundancy == false and backup storage redundancy == geo)
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-resource-group {} --partner-server {} --partner-database {}'
                 .format(resource_group_pri, server_name_pri, non_zr_db_name_2, 
                         resource_group_sec, server_name_sec, pri_non_zr_no_param_db_name),
                 checks=[
					 JMESPathCheck('name', pri_non_zr_no_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Geo'),
                     JMESPathCheck('zoneRedundant', False)])

		# Create zone redundant primary vldb with zone redundancy == true and backup storage redundancy == Zone 
        # Verify created vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}  --backup-storage-redundancy {} --zone-redundant'
                 .format(resource_group_pri, server_name_pri, zr_db_name_2, "Hyperscale", 'Gen5', 2, 'zone'),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_pri),
                     JMESPathCheck('name', zr_db_name_2),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

        # Create secondary vldb replica from zone redundant primary vldb with no parameters passed in
        # Verify created secondary vldb replica has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-resource-group {} --partner-server {} --partner-database {}'
                 .format(resource_group_pri, server_name_pri, zr_db_name_2, 
                         resource_group_sec, server_name_sec, pri_zr_no_param_db_name),
                 checks=[
					 JMESPathCheck('name', pri_zr_no_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

    @ResourceGroupPreparer(location='eastus2euap')
    @SqlServerPreparer(location='eastus2euap')
    @AllowLargeResponse()
    def test_sql_zone_resilient_restore_hyperscale_database(self, resource_group, server):
        # Set db names
        source_non_zr_db_name = "sourceNonZrDb"
        source_zr_db_name = "sourceZrDb"
        restore_source_non_zr_true_param_db_name = "restoreSourceNonZrTrueParamDb"
        restore_source_zr_false_param_db_name = "restoreSourceZrFalseParamDb"
        restore_source_non_zr_no_param_db_name = "restoreSourceNonZrNoParamDb"
        restore_source_zr_no_param_db_name = "restoreSourceZrNoParamDb"

        # Create non zone redundant source vldb
        # Verify created vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Geo)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}'
                 .format(resource_group, server, source_non_zr_db_name, "Hyperscale", 'Gen5', 2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', source_non_zr_db_name),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
                     JMESPathCheck('requestedBackupStorageRedundancy', 'Geo'),
                     JMESPathCheck('zoneRedundant', False)])

		# Create zone redundant source vldb with zone redundancy == true and backup storage redundancy == Zone 
        # Verify created vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --family {} --capacity {}  --backup-storage-redundancy {} --zone-redundant {}'
                 .format(resource_group, server, source_zr_db_name, "Hyperscale", 'Gen5', 2, 'zone', True),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', source_zr_db_name),
                     JMESPathCheck('edition', 'Hyperscale'),
                     JMESPathCheck('sku.tier', 'Hyperscale'),
					 JMESPathCheck('sku.family', 'Gen5'),
					 JMESPathCheck('sku.capacity', 2),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

        # Restore non zone redundant source vldb with zone redundancy == true and backup storage redundancy == Zone
        # Verify restored vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db restore -g {} --server {} --name {} --dest-name {} --time {} '
                 '--edition {} --family {} --capacity {} --backup-storage-redundancy {} --z'
                 .format(resource_group, server, source_non_zr_db_name, restore_source_non_zr_true_param_db_name, datetime.utcnow().isoformat(), 
                         "Hyperscale", 'Gen5', 2, 'zone'),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', restore_source_non_zr_true_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

        # Restore zone redundant source vldb with zone redundancy == false
        # Verify restored vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Zone)
        self.cmd('sql db restore -g {} --server {} --name {} --dest-name {} --time {} --z {}'
                 .format(resource_group, server, source_zr_db_name, restore_source_zr_false_param_db_name, datetime.utcnow().isoformat(), False),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', restore_source_zr_false_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', False)])


        # Restore non zone redundant source vldb with no parameters passed in
        # Verify restored vldb has correct values (specifically zone redundancy == false and backup storage redundancy == Geo)
        self.cmd('sql db restore -g {} --server {} --name {} --dest-name {} --time {}'
                 .format(resource_group, server, source_non_zr_db_name, restore_source_non_zr_no_param_db_name, datetime.utcnow().isoformat()),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', restore_source_non_zr_no_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Geo'),
                     JMESPathCheck('zoneRedundant', False)])

        # Restore zone redundant source vldb with no parameters passed in
        # Verify restored vldb has correct values (specifically zone redundancy == true and backup storage redundancy == Zone)
        self.cmd('sql db restore -g {} --server {} --name {} --dest-name {} --time {}'
                 .format(resource_group, server, source_zr_db_name, restore_source_zr_no_param_db_name, datetime.utcnow().isoformat()),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
					 JMESPathCheck('name', restore_source_zr_no_param_db_name),
					 JMESPathCheck('requestedBackupStorageRedundancy', 'Zone'),
                     JMESPathCheck('zoneRedundant', True)])

class SqlDBMaintenanceScenarioTest(ScenarioTest):
    DEFAULT_MC = "SQL_Default"
    MDB1 = "SQL_EastUS2_DB_1"
    MDB2 = "SQL_EastUS2_DB_2"

    def _get_full_maintenance_id(self, name):
        return "/subscriptions/{}/providers/Microsoft.Maintenance/publicMaintenanceConfigurations/{}".format(
            self.get_subscription_id(), name)

    @ResourceGroupPreparer(location='eastus2')
    @SqlServerPreparer(location='eastus2')
    @AllowLargeResponse()
    def test_sql_db_maintenance(self, resource_group, resource_group_location, server):
        database_name_1 = "createDb1maintenance"
        database_name_2 = "createDb2maintenance"
        database_name_3 = "updateEnrollAndSwitchDb1maintenance"

        # Test creating database with maintenance set to DB_1
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --maint-config-id {}'
                 .format(resource_group, server, database_name_1, "Premium", self.MDB1),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB1))])

        # Test creating database with maintenance set to DB_2 (full id)
        self.cmd('sql db create -g {} --server {} --name {} --edition {} --capacity {} --maint-config-id {}'
                 .format(resource_group, server, database_name_2, "Standard", 50,
                         self._get_full_maintenance_id(self.MDB2)),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Standard'),
                     JMESPathCheck('sku.tier', 'Standard'),
                     JMESPathCheck('sku.capacity', 50),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB2))])

        # Test creating database with no maintenance specified
        self.cmd('sql db create -g {} --server {} --name {} --edition {}'
                 .format(resource_group, server, database_name_3, "Standard"),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Standard'),
                     JMESPathCheck('sku.tier', 'Standard'),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.DEFAULT_MC))])

        # Test enrolling into maintenance
        self.cmd('sql db update -g {} --server {} --name {} --edition {} --capacity {} -m {}'
                 .format(resource_group, server, database_name_3, "Premium", 125, self.MDB2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('sku.capacity', 125),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB2))])

        # Test switching maintenance and enrolling into zone redundancy
        self.cmd('sql db update -g {} --server {} --name {} -m {} --zone-redundant'
                 .format(resource_group, server, database_name_3, self._get_full_maintenance_id(self.MDB1)),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('elasticPoolId', None),
                     JMESPathCheck('edition', 'Premium'),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', True),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB1))])

    @ResourceGroupPreparer(location='eastus2')
    @SqlServerPreparer(location='eastus2')
    @AllowLargeResponse()
    def test_sql_elastic_pool_maintenance(self, resource_group, resource_group_location, server):
        pool_name_1 = "createDb1maintenance"
        pool_name_2 = "createDb2maintenance"
        pool_name_3 = "updateEnrollAndSwitchDb1maintenance"

        # Test creating elastic pool with maintenance set to DB_1
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {} --maint-config-id {}'
                 .format(resource_group, server, pool_name_1, "Premium", self.MDB1),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB1))])

        # Test creating elastic pool with maintenance set to DB_2 (full id)
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {} --capacity {} --maint-config-id {}'
                 .format(resource_group, server, pool_name_2, "Standard", 100,
                         self._get_full_maintenance_id(self.MDB2)),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_2),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('sku.tier', 'Standard'),
                     JMESPathCheck('sku.capacity', 100),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB2))])

        # Test creating elastic pool with no maintenance specified
        self.cmd('sql elastic-pool create -g {} --server {} --name {} --edition {}'
                 .format(resource_group, server, pool_name_3, "Premium"),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.DEFAULT_MC))])

        # Test enrolling into maintenance
        self.cmd('sql elastic-pool update -g {} --server {} --name {} --edition {} -m {}'
                 .format(resource_group, server, pool_name_3, "Premium", self.MDB2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('sku.capacity', 125),
                     JMESPathCheck('zoneRedundant', False),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB2))])

        # Test switching maintenance and enrolling into zone redundancy
        self.cmd('sql elastic-pool update -g {} --server {} --name {} --maint-config-id {} --zone-redundant'
                 .format(resource_group, server, pool_name_3, self._get_full_maintenance_id(self.MDB1)),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', pool_name_3),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('sku.tier', 'Premium'),
                     JMESPathCheck('zoneRedundant', True),
                     JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(self.MDB1))])


class SqlServerTrustGroupsScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ManagedInstancePreparer(parameter_name="mi1")
    @ManagedInstancePreparer(parameter_name="mi2")
    def test_sql_server_trust_groups(self, mi1, rg, mi2):
        self.kwargs.update({
            'loc': ManagedInstancePreparer.location,
            'rg': rg,
            'managed_instance_name_1': mi1,
            'managed_instance_name_2': mi2
        })

        # Create sql managed_instance
        managed_instance_1 = self.cmd('sql mi show -g {rg} -n {managed_instance_name_1}').get_output_in_json()

        managed_instance_2 = self.cmd('sql mi show -g {rg} -n {managed_instance_name_2}').get_output_in_json()

        self.kwargs.update({
            'stg_name': 'stg-test',
            'trust_scope': 'GlobalTransactions',
            'mi1': managed_instance_1['id'],
            'mi2': managed_instance_2['id'],
        })

        stg = self.cmd(
            'az sql stg create -g {rg} -l {loc} --trust-scope {trust_scope} -n {stg_name} -m {mi1} {mi2}').get_output_in_json()
        assert stg['name'] == 'stg-test'

        self.cmd('az sql stg show -g {rg} -l {loc} -n {stg_name}').get_output_in_json()

        stg_list = self.cmd('az sql stg list -g {rg} --instance-name {managed_instance_name_1}').get_output_in_json()
        assert len(stg_list) == 1

        stg_list = self.cmd('az sql stg list -g {rg} -l {loc}').get_output_in_json()
        assert len(stg_list) >= 1

        self.cmd('az sql stg delete -g {rg} -l {loc} -n {stg_name} --yes')


class SqlManagedInstanceCustomMaintenanceWindow(ScenarioTest):
    MMI1 = "SQL_WestCentralUS_MI_1"

    def _get_full_maintenance_id(self, name):
        return "/subscriptions/{}/providers/Microsoft.Maintenance/publicMaintenanceConfigurations/{}".format(
            self.get_subscription_id(), name)

    def test_sql_managed_instance_cmw(self):
        # Values of existing resources in order to test this feature
        loc = 'westcentralus'
        resource_group = ManagedInstancePreparer.group
        subnet = ManagedInstancePreparer.subnet
        ####

        self.kwargs.update({
            'loc': loc,
            'rg': resource_group,
            'subnet': subnet,
            'managed_instance_name': self.create_random_name(managed_instance_name_prefix,
                                                             managed_instance_name_max_length),
            'username': 'admin123',
            'admin_password': 'SecretPassword123',
            'timezone_id': 'Central European Standard Time',
            'license_type': 'LicenseIncluded',
            'v_cores': 8,
            'storage_size_in_gb': '128',
            'edition': 'GeneralPurpose',
            'family': 'Gen5',
            'collation': ManagedInstancePreparer.collation,
            'proxy_override': "Proxy",
            'maintenance_id': self._get_full_maintenance_id(self.MMI1)
        })

        # test create sql managed_instance with FMW
        managed_instance = self.cmd('sql mi create -g {rg} -n {managed_instance_name} -l {loc} '
                                    '-u {username} -p {admin_password} --subnet {subnet} --license-type {license_type} --capacity {v_cores} '
                                    '--storage {storage_size_in_gb} --edition {edition} --family {family} --collation {collation} '
                                    '--proxy-override {proxy_override} --public-data-endpoint-enabled --timezone-id "{timezone_id}" --maint-config-id "{maintenance_id}"',
                                    checks=[
                                        self.check('name', '{managed_instance_name}'),
                                        self.check('resourceGroup', '{rg}'),
                                        self.check('administratorLogin', '{username}'),
                                        self.check('vCores', '{v_cores}'),
                                        self.check('storageSizeInGb', '{storage_size_in_gb}'),
                                        self.check('licenseType', '{license_type}'),
                                        self.check('sku.tier', '{edition}'),
                                        self.check('sku.family', '{family}'),
                                        self.check('sku.capacity', '{v_cores}'),
                                        self.check('identity', None),
                                        self.check('collation', '{collation}'),
                                        self.check('proxyOverride', '{proxy_override}'),
                                        self.check('publicDataEndpointEnabled', 'True'),
                                        self.check('maintenanceConfigurationId',
                                                   self._get_full_maintenance_id(self.MMI1))]).get_output_in_json()

        # test delete sql managed instance 2
        self.cmd('sql mi delete --ids {} --yes'
                 .format(managed_instance['id']), checks=NoneCheck())


class SqlManagedInstanceMgmtScenarioTest(ScenarioTest):
    DEFAULT_MC = "SQL_Default"
    MMI1 = "SQL_WestEurope_MI_1"
    tag1 = "tagName1=tagValue1"
    tag2 = "tagName2=tagValue2"
    backup_storage_redundancy = "Local"

    def _get_full_maintenance_id(self, name):
        return "/subscriptions/{}/providers/Microsoft.Maintenance/publicMaintenanceConfigurations/{}".format(
            self.get_subscription_id(), name)

    @AllowLargeResponse()
    @ManagedInstancePreparer(
        tags=f"{tag1} {tag2}",
        minimalTlsVersion="1.2",
        otherParams=f"--bsr {backup_storage_redundancy}")
    def test_sql_managed_instance_mgmt(self, mi, rg):
        managed_instance_name_1 = mi
        resource_group_1 = rg
        admin_login = 'admin123'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']
        tls1_2 = "1.2"
        tls1_1 = "1.1"
        user = admin_login

        # test show sql managed instance 1
        subnet = ManagedInstancePreparer.subnet
        target_subnet = ManagedInstancePreparer.target_subnet
        if not (self.in_recording or self.is_live):
            subnet = subnet.replace(ManagedInstancePreparer.subscription_id, "00000000-0000-0000-0000-000000000000")
            target_subnet = target_subnet.replace(ManagedInstancePreparer.subscription_id, "00000000-0000-0000-0000-000000000000")

        managed_instance_1 = self.cmd('sql mi show -g {} -n {}'
                                      .format(resource_group_1, managed_instance_name_1),
                                      checks=[
                                          JMESPathCheck('name', managed_instance_name_1),
                                          JMESPathCheck('subnetId', subnet),
                                          JMESPathCheck('resourceGroup', resource_group_1),
                                          JMESPathCheck('administratorLogin', user),
                                          JMESPathCheck('vCores', ManagedInstancePreparer.v_core),
                                          JMESPathCheck('storageSizeInGb', ManagedInstancePreparer.storage),
                                          JMESPathCheck('licenseType', ManagedInstancePreparer.licence),
                                          JMESPathCheck('sku.tier', ManagedInstancePreparer.edition),
                                          JMESPathCheck('sku.family', ManagedInstancePreparer.family),
                                          JMESPathCheck('sku.capacity', ManagedInstancePreparer.v_core),
                                          JMESPathCheck('collation', ManagedInstancePreparer.collation),
                                          JMESPathCheck('identity', None),
                                          JMESPathCheck('publicDataEndpointEnabled', 'True'),
                                          JMESPathCheck('minimalTlsVersion', tls1_2),
                                          JMESPathCheck('tags', "{'tagName1': 'tagValue1', 'tagName2': 'tagValue2'}"),
                                          JMESPathCheck('currentBackupStorageRedundancy', self.backup_storage_redundancy),
                                          JMESPathCheck('maintenanceConfigurationId', self._get_full_maintenance_id(
                                              self.DEFAULT_MC))]).get_output_in_json()

        # test show sql managed instance 1 using id
        self.cmd('sql mi show --ids {}'
                 .format(managed_instance_1['id']),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', user)])

        # Managed instance becomes ready before the operation is completed. For that reason, we should wait
        # for the operation to complete in order to proceed with testing.
        if self.is_live:
            sleep(120)

        # test update sql managed_instance 1
        self.cmd('sql mi update -g {} -n {} --admin-password {} -i'
                 .format(resource_group_1, managed_instance_name_1, admin_passwords[1]),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     # remove this check since there is an issue and the fix is being deployed currently
                     # JMESPathCheck('identity.type', 'SystemAssigned')
                     JMESPathCheck('administratorLogin', user)])

        # test update without identity parameter, validate identity still exists
        # also use --ids instead of -g/-n
        self.cmd('sql mi update --ids {} --admin-password {}'
                 .format(managed_instance_1['id'], admin_passwords[0]),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     # remove this check since there is an issue and the fix is being deployed currently
                     # JMESPathCheck('identity.type', 'SystemAssigned')
                     JMESPathCheck('administratorLogin', user)])

        # test update proxyOverride and publicDataEndpointEnabled
        # test is currently removed due to long execution time due to waiting for SqlAliasStateMachine completion to complete
        # self.cmd('sql mi update -g {} -n {} --proxy-override {} --public-data-endpoint-enabled {}'
        #         .format(resource_group_1, managed_instance_name_1, proxy_override_update, public_data_endpoint_enabled_update),
        #         checks=[
        #             JMESPathCheck('name', managed_instance_name_1),
        #             JMESPathCheck('resourceGroup', resource_group_1),
        #             JMESPathCheck('proxyOverride', proxy_override_update),
        #             JMESPathCheck('publicDataEndpointEnabled', public_data_endpoint_enabled_update)])

        # test update minimalTlsVersion
        self.cmd('sql mi update -g {} -n {} --minimal-tls-version {}'
                 .format(resource_group_1, managed_instance_name_1, tls1_1),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('minimalTlsVersion', tls1_1)])

        # test update managed instance tags
        tag3 = "tagName3=tagValue3"
        self.cmd('sql mi update -g {} -n {} --set tags.{}'
                 .format(resource_group_1, managed_instance_name_1, tag3),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('tags',
                                   "{'tagName1': 'tagValue1', 'tagName2': 'tagValue2', 'tagName3': 'tagValue3'}")])

        # test remove managed instance tags
        self.cmd('sql mi update -g {} -n {} --remove tags.tagName1'
                 .format(resource_group_1, managed_instance_name_1),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('tags', "{'tagName2': 'tagValue2', 'tagName3': 'tagValue3'}")])

        # test override managed instance tags
        self.cmd('sql mi update -g {} -n {} --tags {}'
                 .format(resource_group_1, managed_instance_name_1, self.tag1),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('tags', "{'tagName1': 'tagValue1'}")])

        # test clear managed instance tags by passing ""
        self.cmd('sql mi update -g {} -n {} --tags ""'
                 .format(resource_group_1, managed_instance_name_1),
                 checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('tags', {})])

        # test cross-subnet update SLO with the subnet resource id
        self.cmd('sql mi update -g {} -n {} --subnet {} --capacity {}'
                .format(resource_group_1, managed_instance_name_1, target_subnet, ManagedInstancePreparer.target_subnet_vcores),
                checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('subnetId', target_subnet)])

        # test cross-subnet update SLO with subnet and vNet names
        self.cmd('sql mi update -g {} -n {} --subnet {} --vnet-name {}'
            .format(resource_group_1, managed_instance_name_1, ManagedInstancePreparer.subnet_name, ManagedInstancePreparer.vnet_name),
                checks=[
                     JMESPathCheck('name', managed_instance_name_1),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('subnetId', subnet)])

        # test list sql managed_instance in the subscription should be at least 1
        self.cmd('sql mi list', checks=[JMESPathCheckGreaterThan('length(@)', 0)])

class SqlManagedInstanceBackupStorageRedundancyTest(ScenarioTest):
    bsr_geo = "Geo"

    @AllowLargeResponse()
    @ManagedInstancePreparer(
        otherParams=f"--bsr {bsr_geo}")
    def test_sql_managed_instance_bsr(self, mi, rg):
        managed_instance_name_1 = mi
        resource_group_1 = rg

        # test show sql managed instance 1
        self.cmd('sql mi show -g {} -n {}'
            .format(resource_group_1, managed_instance_name_1),
            checks=[
                JMESPathCheck('name', managed_instance_name_1),
                JMESPathCheck('resourceGroup', resource_group_1),
                JMESPathCheck('currentBackupStorageRedundancy', self.bsr_geo),
                JMESPathCheck('requestedBackupStorageRedundancy', self.bsr_geo)])
        if self.is_live:
            sleep(120)

        bsr_local = "Local"
        # Test update bsr to Local
        self.cmd('sql mi update -g {} -n {} --bsr {} --yes'
            .format(resource_group_1, managed_instance_name_1, bsr_local),
            checks=[
                JMESPathCheck('name', managed_instance_name_1),
                JMESPathCheck('resourceGroup', resource_group_1),
                JMESPathCheck('currentBackupStorageRedundancy', bsr_local),
                JMESPathCheck('requestedBackupStorageRedundancy', bsr_local)])

        if self.is_live:
            sleep(120)

        # Test update bsr to Geo
        self.cmd('sql mi update -g {} -n {} --bsr {} --yes'
            .format(resource_group_1, managed_instance_name_1, self.bsr_geo),
            checks=[
                JMESPathCheck('name', managed_instance_name_1),
                JMESPathCheck('resourceGroup', resource_group_1),
                JMESPathCheck('currentBackupStorageRedundancy', self.bsr_geo),
                JMESPathCheck('requestedBackupStorageRedundancy', self.bsr_geo)])

class SqlManagedInstanceMgmtScenarioIdentityTest(ScenarioTest):
    test_umi = '/subscriptions/{}/resourcegroups/{}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mi-tooling-managed-identity'.format(ManagedInstancePreparer.subscription_id, ManagedInstancePreparer.group)
    verify_umi_with_empty_uuid = '/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/{}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mi-tooling-managed-identity'.format(ManagedInstancePreparer.group)

    @AllowLargeResponse()
    @ManagedInstancePreparer(
        identity_type=ResourceIdType.system_assigned_user_assigned.value,
        user_assigned_identity_id=test_umi,
        pid=test_umi)
    def test_sql_managed_instance_create_identity_mgmt(self, mi, rg):
        managed_instance_name = mi
        resource_group_1 = rg

        # test show sql managed instance
        self.cmd('sql mi show -g {} -n {}'
                 .format(resource_group_1, managed_instance_name),
                 checks=[
                     JMESPathCheck('name', managed_instance_name),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck(
                         'primaryUserAssignedIdentityId',
                         self.test_umi if self.in_recording or self.is_live else self.verify_umi_with_empty_uuid
                     ),
                     JMESPathCheck('identity.type', 'SystemAssigned,UserAssigned')]
                 )


class SqlManagedInstancePoolScenarioTest(ScenarioTest):
    # Instance pool test should be deprecated and also it takes more then 5 hours to record.
    @live_only()
    @ManagedInstancePreparer()
    def test_sql_instance_pool(self, mi, rg):
        print("Starting instance pool tests")
        instance_pool_name_1 = self.create_random_name(instance_pool_name_prefix, managed_instance_name_max_length)
        instance_pool_name_2 = self.create_random_name(instance_pool_name_prefix, managed_instance_name_max_length)
        license_type = ManagedInstancePreparer.licence
        location = ManagedInstancePreparer.location
        v_cores = ManagedInstancePreparer.v_core
        edition = ManagedInstancePreparer.edition
        family = ManagedInstancePreparer.family
        resource_group = rg

        subnet = ManagedInstancePreparer.subnet
        num_pools = len(self.cmd('sql instance-pool list -g {}'.format(resource_group)).get_output_in_json())

        # test create sql managed_instance
        self.cmd(
            'sql instance-pool create -g {} -n {} -l {} '
            '--subnet {} --license-type {} --capacity {} -e {} -f {}'.format(
                resource_group, instance_pool_name_1, location, subnet, license_type, v_cores, edition, family),
            checks=[
                JMESPathCheck('name', instance_pool_name_1),
                JMESPathCheck('resourceGroup', resource_group),
                JMESPathCheck('vCores', v_cores),
                JMESPathCheck('licenseType', license_type),
                JMESPathCheck('sku.tier', edition),
                JMESPathCheck('sku.family', family)])

        # test show sql instance pool
        self.cmd('sql instance-pool show -g {} -n {}'
                 .format(resource_group, instance_pool_name_1),
                 checks=[
                     JMESPathCheck('name', instance_pool_name_1),
                     JMESPathCheck('resourceGroup', resource_group)])

        # test updating tags of an instance pool
        tag1 = "bar=foo"
        tag2 = "foo=bar"
        self.cmd('sql instance-pool update -g {} -n {} --tags {} {}'
                 .format(resource_group, instance_pool_name_1, tag1, tag2),
                 checks=[
                     JMESPathCheck('name', instance_pool_name_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('tags', "{'bar': 'foo', 'foo': 'bar'}")])

        # test updating instance pool to clear tags by passing ""
        self.cmd('sql instance-pool update -g {} -n {} --tags ""'
                 .format(resource_group, instance_pool_name_1),
                 checks=[
                     JMESPathCheck('name', instance_pool_name_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('tags', {})])

        # Instance Pool 2
        self.cmd(
            'sql instance-pool create -g {} -n {} -l {} '
            '--subnet {} --license-type {} --capacity {} -e {} -f {}'.format(
                resource_group, instance_pool_name_2, location, subnet, license_type, v_cores, edition, family),
            checks=[
                JMESPathCheck('name', instance_pool_name_2),
                JMESPathCheck('resourceGroup', resource_group),
                JMESPathCheck('vCores', v_cores),
                JMESPathCheck('licenseType', license_type),
                JMESPathCheck('sku.tier', edition),
                JMESPathCheck('sku.family', family)])

        # test show sql instance pool
        self.cmd('sql instance-pool show -g {} -n {}'
                 .format(resource_group, instance_pool_name_2),
                 checks=[
                     JMESPathCheck('name', instance_pool_name_2),
                     JMESPathCheck('resourceGroup', resource_group)])

        # test updating tags of an instance pool
        tag1 = "bar=foo"
        tag2 = "foo=bar"
        self.cmd('sql instance-pool update -g {} -n {} --tags {} {}'
                 .format(resource_group, instance_pool_name_2, tag1, tag2),
                 checks=[
                     JMESPathCheck('name', instance_pool_name_2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('tags', "{'bar': 'foo', 'foo': 'bar'}")])

        # test updating instance pool to clear tags by passing ""
        self.cmd('sql instance-pool update -g {} -n {} --tags ""'
                 .format(resource_group, instance_pool_name_2),
                 checks=[
                     JMESPathCheck('name', instance_pool_name_2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('tags', {})])

        self.cmd('sql instance-pool list -g {}'
                 .format(resource_group),
                 checks=[
                     JMESPathCheck('length(@)', num_pools + 2)])

        # test delete sql managed instance
        self.cmd('sql instance-pool delete -g {} -n {} --yes'
                 .format(resource_group, instance_pool_name_1), checks=NoneCheck())

        # test show sql managed instance doesn't return anything
        self.cmd('sql instance-pool show -g {} -n {}'
                 .format(resource_group, instance_pool_name_1),
                 expect_failure=True)

        # test delete sql managed instance
        self.cmd('sql instance-pool delete -g {} -n {} --yes --no-wait'
                 .format(resource_group, instance_pool_name_2), checks=NoneCheck())

        # verify all created instance pool above have been deleted
        self.cmd('sql instance-pool list -g {}'
                 .format(resource_group),
                 checks=[
                     JMESPathCheck('length(@)', num_pools)])


class SqlManagedInstanceTransparentDataEncryptionScenarioTest(ScenarioTest):
    @ManagedInstancePreparer(
        identity_type=ResourceIdType.system_assigned.value
    )
    def test_sql_mi_tdebyok(self, mi, rg):
        resource_prefix = 'sqltdebyok'

        self.kwargs.update({
            'loc': ManagedInstancePreparer.location,
            'rg': rg,
            'managed_instance_name': mi,
            'database_name': self.create_random_name(resource_prefix, 20),
            'collation': ManagedInstancePreparer.collation,
        })

        # get sql managed_instance
        managed_instance = self.cmd('sql mi show -g {rg} -n {managed_instance_name}').get_output_in_json()

        self.kwargs.update({
            'mi_identity': managed_instance['identity']['principalId'],
            'vault_name': self.create_random_name(resource_prefix, 24),
            'key_name': self.create_random_name(resource_prefix, 32),
        })

        # create database
        self.cmd('sql midb create -g {rg} --mi {managed_instance_name} -n {database_name} --collation {collation}',
                 checks=[
                     self.check('resourceGroup', '{rg}'),
                     self.check('name', '{database_name}'),
                     self.check('location', '{loc}'),
                     self.check('collation', '{collation}'),
                     self.check('status', 'Online')])

        # create vault and acl server identity

        self.cmd('keyvault create -g {rg} -n {vault_name} --enable-soft-delete true')
        self.cmd(
            'keyvault set-policy -g {rg} -n {vault_name} --object-id {mi_identity} --key-permissions wrapKey unwrapKey get list')

        # create key
        key_resp = self.cmd(
            'keyvault key create -n {key_name} -p software --vault-name {vault_name}').get_output_in_json()

        self.kwargs.update({
            'kid': key_resp['key']['kid'],
        })

        # add server key
        server_key_resp = self.cmd('sql mi key create -g {rg} --mi {managed_instance_name} -k {kid}',
                                   checks=[
                                       self.check('uri', '{kid}'),
                                       self.check('serverKeyType', 'AzureKeyVault')])

        self.kwargs.update({
            'server_key_name': server_key_resp.get_output_in_json()['name'],
        })

        # validate show key
        self.cmd('sql mi key show -g {rg} --mi {managed_instance_name} -k {kid}',
                 checks=[
                     self.check('uri', '{kid}'),
                     self.check('serverKeyType', 'AzureKeyVault'),
                     self.check('name', '{server_key_name}')])

        # validate list key (should return 2 items)
        self.cmd('sql mi key list -g {rg} --mi {managed_instance_name}',
                 checks=[JMESPathCheck('length(@)', 2)])

        # validate encryption protector is service managed via show
        self.cmd('sql mi tde-key show -g {rg} --mi {managed_instance_name}',
                 checks=[
                     self.check('serverKeyType', 'ServiceManaged'),
                     self.check('serverKeyName', 'ServiceManaged')])

        # update encryption protector to akv key
        self.cmd(
            'sql mi tde-key set -g {rg} --mi {managed_instance_name} -t AzureKeyVault -k {kid}',
            checks=[
                self.check('serverKeyType', 'AzureKeyVault'),
                self.check('serverKeyName', '{server_key_name}'),
                self.check('uri', '{kid}')])
                
        # validate encryption protector is akv via show
        self.cmd('sql mi tde-key show -g {rg} --mi {managed_instance_name}',
                 checks=[
                     self.check('serverKeyType', 'AzureKeyVault'),
                     self.check('serverKeyName', '{server_key_name}'),
                     self.check('uri', '{kid}')])

        # update encryption protector to service managed
        self.cmd('sql mi tde-key set -g {rg} --mi {managed_instance_name} -t ServiceManaged',
                 checks=[
                     self.check('serverKeyType', 'ServiceManaged'),
                     self.check('serverKeyName', 'ServiceManaged')])

        # validate encryption protector is service managed via show
        self.cmd('sql mi tde-key show -g {rg} --mi {managed_instance_name}',
                 checks=[
                     self.check('serverKeyType', 'ServiceManaged'),
                     self.check('serverKeyName', 'ServiceManaged')])


class SqlManagedInstanceDbShortTermRetentionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest')
    @ManagedInstancePreparer()
    def test_sql_managed_db_short_retention(self, mi, rg):
        resource_prefix = 'MIDBShortTermRetention'

        loc = 'westcentralus'
        resource_group = 'autobot-managed-instance-v12'
        subnet = '/subscriptions/4b9746e4-d324-4e1d-be53-ec3c8f3a0c18/resourceGroups/autobot-managed-instance-v12/providers/Microsoft.Network/virtualNetworks/autobot-managed-instance-vnet/subnets/clsubnet'

        self.kwargs.update({
            'loc': ManagedInstancePreparer.location,
            'managed_instance_name': mi,
            'database_name': self.create_random_name(resource_prefix, 50),
            'collation': ManagedInstancePreparer.collation,
            'retention_days_inc': 14,
            'retention_days_dec': 7,
            'rg': rg
        })

        # create database
        self.cmd('sql midb create -g {rg} --mi {managed_instance_name} -n {database_name} --collation {collation}',
                 checks=[
                     self.check('resourceGroup', '{rg}'),
                     self.check('name', '{database_name}'),
                     self.check('location', '{loc}'),
                     self.check('collation', '{collation}'),
                     self.check('status', 'Online')])

        # test update short term retention on live database
        self.cmd(
            'sql midb short-term-retention-policy set -g {rg} --mi {managed_instance_name} -n {database_name} --retention-days {retention_days_inc}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('retentionDays', '{retention_days_inc}')])

        # test get short term retention on live database
        self.cmd('sql midb short-term-retention-policy show -g {rg} --mi {managed_instance_name} -n {database_name}',
                 checks=[
                     self.check('resourceGroup', '{rg}'),
                     self.check('retentionDays', '{retention_days_inc}')])

        # Wait for first backup before dropping
        _wait_until_first_backup_midb(self)

        # Delete by group/server/name
        self.cmd('sql midb delete -g {rg} --managed-instance {managed_instance_name} -n {database_name} --yes',
                 checks=[NoneCheck()])

        # Get deleted database
        deleted_databases = self.cmd('sql midb list-deleted -g {rg} --managed-instance {managed_instance_name}',
                                     checks=[
                                         self.greater_than('length(@)', 0)])

        self.kwargs.update({
            'deleted_time': _get_deleted_date(deleted_databases.json_value[0]).isoformat()
        })

        # test update short term retention on deleted database
        self.cmd(
            'sql midb short-term-retention-policy set -g {rg} --mi {managed_instance_name} -n {database_name} --retention-days {retention_days_dec} --deleted-time {deleted_time}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('retentionDays', '{retention_days_dec}')])

        # test get short term retention on deleted database
        self.cmd(
            'sql midb short-term-retention-policy show -g {rg} --mi {managed_instance_name} -n {database_name} --deleted-time {deleted_time}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('retentionDays', '{retention_days_dec}')])


class SqlManagedInstanceDbLongTermRetentionScenarioTest(ScenarioTest):
    @ManagedInstancePreparer()
    def test_sql_managed_db_long_term_retention(self, mi, rg):
        resource_prefix = 'MIDBLongTermRetention'
        self.kwargs.update({
            'rg': rg,
            'loc': ManagedInstancePreparer.location,
            'managed_instance_name': mi,
            'database_name': self.create_random_name(resource_prefix, 50),
            'weekly_retention': 'P1W',
            'monthly_retention': 'P1M',
            'yearly_retention': 'P2M',
            'week_of_year': 12,
            'collation': ManagedInstancePreparer.collation
        })

        # create database
        self.cmd('sql midb create -g {rg} --mi {managed_instance_name} -n {database_name} --collation {collation}',
                 checks=[
                     self.check('resourceGroup', '{rg}'),
                     self.check('name', '{database_name}'),
                     self.check('location', '{loc}'),
                     self.check('collation', '{collation}'),
                     self.check('status', 'Online')])

        # test update long term retention on live database
        self.cmd(
            'sql midb ltr-policy set -g {rg} --mi {managed_instance_name} -n {database_name} --weekly-retention {weekly_retention} --monthly-retention {monthly_retention} --yearly-retention {yearly_retention} --week-of-year {week_of_year}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('weeklyRetention', '{weekly_retention}'),
                self.check('monthlyRetention', '{monthly_retention}'),
                self.check('yearlyRetention', '{yearly_retention}')])

        # test get long term retention policy on live database
        self.cmd(
            'sql midb ltr-policy show -g {rg} --mi {managed_instance_name} -n {database_name}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('weeklyRetention', '{weekly_retention}'),
                self.check('monthlyRetention', '{monthly_retention}'),
                self.check('yearlyRetention', '{yearly_retention}')])

        # test list long term retention backups for location
        # with resource group
        self.cmd(
            'sql midb ltr-backup list -l {loc} -g {rg}',
            checks=[
                JMESPathCheckGreaterThan('length(@)', 0)])

        # without resource group
        self.cmd(
            'sql midb ltr-backup list -l {loc}',
            checks=[
                JMESPathCheckGreaterThan('length(@)', 0)])

        # test list long term retention backups for instance
        # with resource group
        self.cmd(
            'sql midb ltr-backup list -l {loc} --mi {managed_instance_name} -g {rg}',
            checks=[
                self.check('length(@)', 0)])

        # without resource group
        self.cmd(
            'sql midb ltr-backup list -l {loc} --mi {managed_instance_name}',
            checks=[
                self.check('length(@)', 0)])

        # test list long term retention backups for database
        # with resource group
        self.cmd(
            'sql midb ltr-backup list -l {loc} --mi {managed_instance_name} -d {database_name} -g {rg}',
            checks=[
                self.check('length(@)', 0)])

        # without resource group
        self.cmd(
            'sql midb ltr-backup list -l {loc} --mi {managed_instance_name} -d {database_name}',
            checks=[
                self.check('length(@)', 0)])


# Milan: we need to think a way to test restore with ltr as in live mode this is not possible
# because after setting LTR it needs to pass some time before backup to show up
#

# # setup for test show long term retention backup
# backup = self.cmd(
#     'sql midb ltr-backup list -l {loc} --mi {managed_instance_name} -d {database_name} --latest').get_output_in_json()

# self.kwargs.update({
#     'backup_name': backup[0]['name'],
#     'backup_id': backup[0]['id']
# })

# # test show long term retention backup
# self.cmd(
#     'sql midb ltr-backup show -l {loc} --mi {managed_instance_name} -d {database_name} -n {backup_name}',
#     checks=[
#         self.check('resourceGroup', '{rg}'),
#         self.check('managedInstanceName', '{managed_instance_name}'),
#         self.check('databaseName', '{database_name}'),
#         self.check('name', '{backup_name}')])

# self.cmd(
#     'sql midb ltr-backup show --id {backup_id}',
#     checks=[
#         self.check('resourceGroup', '{rg}'),
#         self.check('managedInstanceName', '{managed_instance_name}'),
#         self.check('databaseName', '{database_name}'),
#         self.check('name', '{backup_name}')])

# # test restore managed database from LTR backup
# self.kwargs.update({
#     'dest_database_name': 'cli-restore-ltr-backup-test2'
# })

# self.cmd(
#     'sql midb ltr-backup restore --backup-id \'{backup_id}\' --dest-database {dest_database_name} --dest-mi {managed_instance_name} --dest-resource-group {rg}',
#     checks=[
#         self.check('name', '{dest_database_name}')])

# # test delete long term retention backup
# self.cmd(
#     'sql midb ltr-backup delete -l {loc} --mi {managed_instance_name} -d {database_name} -n \'{backup_name}\' --yes',
#     checks=[NoneCheck()])


class SqlManagedInstanceRestoreDeletedDbScenarioTest(ScenarioTest):
    @ManagedInstancePreparer()
    def test_sql_managed_deleted_db_restore(self, mi, rg):
        resource_prefix = 'MIRestoreDeletedDB'

        self.kwargs.update({
            'loc': ManagedInstancePreparer.location,
            'rg': rg,
            'managed_instance_name': mi,
            'database_name': self.create_random_name(resource_prefix, 50),
            'restored_database_name': self.create_random_name(resource_prefix, 50),
            'collation': ManagedInstancePreparer.collation
        })

        # create database
        self.cmd('sql midb create -g {rg} --mi {managed_instance_name} -n {database_name} --collation {collation}',
                 checks=[
                     self.check('resourceGroup', '{rg}'),
                     self.check('name', '{database_name}'),
                     self.check('location', '{loc}'),
                     self.check('collation', '{collation}'),
                     self.check('status', 'Online')])

        # Wait for first backup before dropping
        _wait_until_first_backup_midb(self)

        # Delete by group/server/name
        self.cmd('sql midb delete -g {rg} --managed-instance {managed_instance_name} -n {database_name} --yes',
                 checks=[NoneCheck()])

        # Get deleted database
        deleted_databases = self.cmd('sql midb list-deleted -g {rg} --managed-instance {managed_instance_name}',
                                     checks=[
                                         self.greater_than('length(@)', 0)])

        self.kwargs.update({
            'deleted_time': _get_deleted_date(deleted_databases.json_value[0]).isoformat()
        })

        # test restore deleted database
        self.cmd(
            'sql midb restore -g {rg} --mi {managed_instance_name} -n {database_name} --dest-name {restored_database_name} --deleted-time {deleted_time} --time {deleted_time}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('name', '{restored_database_name}'),
                self.check('status', 'Online')])


class SqlManagedInstanceDbMgmtScenarioTest(ScenarioTest):
    @ManagedInstancePreparer()
    def test_sql_managed_db_mgmt(self, mi, rg):
        database_name = "cliautomationdb01"
        database_name_restored = "restoredcliautomationdb01"

        managed_instance_name_1 = mi
        resource_group_1 = rg

        loc = ManagedInstancePreparer.location
        collation = ManagedInstancePreparer.collation

        # test sql db commands
        db1 = self.cmd('sql midb create -g {} --mi {} -n {} --collation {}'
                       .format(resource_group_1, managed_instance_name_1, database_name, collation),
                       checks=[
                           JMESPathCheck('resourceGroup', resource_group_1),
                           JMESPathCheck('name', database_name),
                           JMESPathCheck('location', loc),
                           JMESPathCheck('collation', collation),
                           JMESPathCheck('status', 'Online')]).get_output_in_json()

        time.sleep(
            300)  # Sleeping 5 minutes should be enough for the restore to be possible (Skipped under playback mode)

        # test sql db restore command
        db1 = self.cmd('sql midb restore -g {} --mi {} -n {} --dest-name {} --time {}'
                       .format(resource_group_1, managed_instance_name_1, database_name, database_name_restored,
                               datetime.utcnow().isoformat()),
                       checks=[
                           JMESPathCheck('resourceGroup', resource_group_1),
                           JMESPathCheck('name', database_name_restored),
                           JMESPathCheck('location', loc),
                           JMESPathCheck('status', 'Online')]).get_output_in_json()

        self.cmd('sql midb list -g {} --managed-instance {}'
                 .format(resource_group_1, managed_instance_name_1),
                 checks=[JMESPathCheck('length(@)', 2)])

        # Show by group/managed_instance/database-name
        self.cmd('sql midb show -g {} --managed-instance {} -n {}'
                 .format(resource_group_1, managed_instance_name_1, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('collation', collation),
                     JMESPathCheck('status', 'Online')])

        # Show by id
        self.cmd('sql midb show --ids {}'
                 .format(db1['id']),
                 checks=[
                     JMESPathCheck('name', database_name_restored),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('collation', collation),
                     JMESPathCheck('status', 'Online')])

        # Delete by group/server/name
        self.cmd('sql midb delete -g {} --managed-instance {} -n {} --yes'
                 .format(resource_group_1, managed_instance_name_1, database_name),
                 checks=[NoneCheck()])

        # test show sql managed db doesn't return anything
        self.cmd('sql midb show -g {} --managed-instance {} -n {}'
                 .format(resource_group_1, managed_instance_name_1, database_name),
                 expect_failure=True)


class SqlManagedInstanceAzureActiveDirectoryAdministratorScenarioTest(ScenarioTest):
    # This MI AAD test needs special AD setup, please contact MI AAD team for new recording.
    def test_sql_mi_aad_admin(self):
        print('Test is started...\n')

        self.kwargs.update({
            'oid': '03db4d3a-a1d3-42d1-8055-2452646dbc2a',
            'oid2': '23716ccd-3bf5-4934-9773-20ce34909e2e',
            'user': 'dmitar@aadsqlmi.net',
            'user2': 'srdan@aadsqlmi.onmicrosoft.com',
            'managed_instance_name': "migrantpermissionstest",
            'rg': "srbozovi_test"
        })

        print('Arguments are updated with login and sid data')

        self.cmd('sql mi ad-admin create --mi {managed_instance_name} -g {rg} -i {oid} -u {user}',
                 checks=[
                     self.check('login', '{user}'),
                     self.check('sid', '{oid}')])

        print('Aad admin is set...\n')

        self.cmd('sql mi ad-admin list --mi {managed_instance_name} -g {rg}',
                 checks=[
                     self.check('[0].login', '{user}'),
                     self.check('[0].sid', '{oid}')])

        print('Get aad admin...\n')

        self.cmd('sql mi ad-admin update --mi {managed_instance_name} -g {rg} -u {user2} -i {oid2}',
                 checks=[
                     self.check('login', '{user2}'),
                     self.check('sid', '{oid2}')])

        print('Aad admin is updated...\n')

        self.cmd('sql mi ad-admin delete --mi {managed_instance_name} -g {rg}')

        print('Aad admin is deleted...\n')

        self.cmd('sql mi ad-admin list --mi {managed_instance_name} -g {rg}',
                 checks=[
                     self.check('login', None)])

        print('Test is finished...\n')


class SqlManagedInstanceAzureADOnlyAuthenticationsScenarioTest(ScenarioTest):
    # This MI AAD test needs special AD setup, please contact MI AAD team for new recording.
    def test_sql_mi_ad_only_auth(self):
        print('Test is started...\n')

        self.kwargs.update({
            'oid': '03db4d3a-a1d3-42d1-8055-2452646dbc2a',
            'user': 'dmitar@aadsqlmi.net',
            'managed_instance_name': "migrantpermissionstest",
            'rg': "srbozovi_test"
        })

        print('Arguments are updated with login and sid data')

        self.cmd('sql mi ad-admin create --mi {managed_instance_name} -g {rg} -i {oid} -u {user}',
                 checks=[
                     self.check('login', '{user}'),
                     self.check('sid', '{oid}')])

        self.cmd('sql mi ad-only-auth enable -n {managed_instance_name} -g {rg}', checks=[])
        self.cmd('sql mi ad-only-auth disable -n {managed_instance_name} -g {rg}', checks=[])
        self.cmd('sql mi ad-only-auth get -n {managed_instance_name} -g {rg}', checks=[])


class SqlFailoverGroupMgmtScenarioTest(ScenarioTest):
    # create 2 servers in the same resource group, and 1 server in a different resource group
    @ResourceGroupPreparer(parameter_name="resource_group_1",
                           parameter_name_for_location="resource_group_location_1")
    @ResourceGroupPreparer(parameter_name="resource_group_2",
                           parameter_name_for_location="resource_group_location_2")
    @SqlServerPreparer(parameter_name="server_name_1",
                       resource_group_parameter_name="resource_group_1",
                       location='westeurope')
    @SqlServerPreparer(parameter_name="server_name_2",
                       resource_group_parameter_name="resource_group_2", location='eastus')
    def test_sql_failover_group_mgmt(self,
                                     resource_group_1, resource_group_location_1,
                                     resource_group_2, resource_group_location_2,
                                     server_name_1, server_name_2):
        # helper class so that it's clear which servers are in which groups
        class ServerInfo(object):  # pylint disable=too-few-public-methods
            def __init__(self, name, group, location):
                self.name = name
                self.group = group
                self.location = location

        from azure.cli.core.commands.client_factory import get_subscription_id

        s1 = ServerInfo(server_name_1, resource_group_1, resource_group_location_1)
        s2 = ServerInfo(server_name_2, resource_group_2, resource_group_location_2)

        failover_group_name = "fgclitest16578-lulu"

        database_name = "db1"

        server2_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}".format(
            get_subscription_id(self.cli_ctx),
            resource_group_2,
            server_name_2)

        # Create database on primary server
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(s1.group, s1.name, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', s1.group),
                     JMESPathCheck('name', database_name)
                 ])

        # Create Failover Group
        self.cmd(
            'sql failover-group create -n {} -g {} -s {} --partner-resource-group {} --partner-server {} --failover-policy Automatic --grace-period 2'
                .format(failover_group_name, s1.group, s1.name, s2.group, s2.name),
            checks=[
                JMESPathCheck('name', failover_group_name),
                JMESPathCheck('resourceGroup', s1.group),
                JMESPathCheck('partnerServers[0].id', server2_id),
                JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 120),
                JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                JMESPathCheck('length(databases)', 0)
            ])

        # List of all failover groups on the primary server
        self.cmd('sql failover-group list -g {} -s {}'
                 .format(s1.group, s1.name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', failover_group_name),
                     JMESPathCheck('[0].replicationRole', 'Primary')
                 ])

        # Get Failover Group on a partner server and check if role is secondary
        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, failover_group_name),
                 checks=[
                     JMESPathCheck('name', failover_group_name),
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                     JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 120),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                     JMESPathCheck('replicationRole', 'Secondary'),
                     JMESPathCheck('length(databases)', 0)
                 ])

        if self.in_recording:
            time.sleep(60)

        # Update Failover Group
        self.cmd('sql failover-group update -g {} -s {} -n {} --grace-period 3 --add-db {}'
                 .format(s1.group, s1.name, failover_group_name, database_name),
                 checks=[
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                     JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 180),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                     JMESPathCheck('length(databases)', 1)
                 ])

        # Check if properties got propagated to secondary server
        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, failover_group_name),
                 checks=[
                     JMESPathCheck('name', failover_group_name),
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                     JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 180),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                     JMESPathCheck('replicationRole', 'Secondary'),
                     JMESPathCheck('length(databases)', 1)
                 ])

        # Check if database is created on partner side
        self.cmd('sql db list -g {} -s {}'
                 .format(s2.group, s2.name),
                 checks=[
                     JMESPathCheck('length(@)', 2)
                 ])

        if self.in_recording:
            time.sleep(60)

        # Update Failover Group failover policy to Manual
        self.cmd('sql failover-group update -g {} -s {} -n {} --failover-policy Manual'
                 .format(s1.group, s1.name, failover_group_name),
                 checks=[
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Manual'),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                     JMESPathCheck('length(databases)', 1)
                 ])

        # Failover Failover Group
        self.cmd('sql failover-group set-primary -g {} -s {} -n {}'
                 .format(s2.group, s2.name, failover_group_name))

        # The failover operation is completed when new primary is promoted to primary role
        # But there is a async part to make old primary a new secondary
        # And we have to wait for this to complete if we are recording the test
        if self.in_recording:
            time.sleep(60)

        # Check the roles of failover groups to confirm failover happened
        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Primary')
                 ])

        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s1.group, s1.name, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        # Fail back to original server
        self.cmd('sql failover-group set-primary -g {} -s {} -n {}'
                 .format(s1.group, s1.name, failover_group_name))

        # The failover operation is completed when new primary is promoted to primary role
        # But there is a async part to make old primary a new secondary
        # And we have to wait for this to complete if we are recording the test
        if self.in_recording:
            time.sleep(60)

        # Check the roles of failover groups to confirm failover happened
        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s1.group, s1.name, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Primary')
                 ])

        # Do no-op failover to the same server
        self.cmd('sql failover-group set-primary -g {} -s {} -n {}'
                 .format(s1.group, s1.name, failover_group_name))

        # Check the roles of failover groups to confirm failover didn't happen
        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        self.cmd('sql failover-group show -g {} -s {} -n {}'
                 .format(s1.group, s1.name, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Primary')
                 ])

        # Remove database from failover group
        self.cmd('sql failover-group update -g {} -s {} -n {} --remove-db {}'
                 .format(s1.group, s1.name, failover_group_name, database_name),
                 checks=[
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Manual'),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                     JMESPathCheck('length(databases)', 0)
                 ])

        # Check if database got removed
        self.cmd('sql db show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, database_name),
                 checks=[
                     JMESPathCheck('[0].failoverGroupId', 'None')
                 ])

        # Drop failover group
        self.cmd('sql failover-group delete -g {} -s {} -n {}'
                 .format(s1.group, s1.name, failover_group_name))

        # Check if failover group  really got dropped
        self.cmd('sql failover-group list -g {} -s {}'
                 .format(s1.group, s1.name),
                 checks=[
                     JMESPathCheck('length(@)', 0)
                 ])

        self.cmd('sql failover-group list -g {} -s {}'
                 .format(s2.group, s2.name),
                 checks=[
                     JMESPathCheck('length(@)', 0)
                 ])


class SqlVirtualClusterMgmtScenarioTest(ScenarioTest):
    @ManagedInstancePreparer()
    def test_sql_virtual_cluster_mgmt(self, mi, rg):
        subnet = ManagedInstancePreparer.subnet

        self.kwargs.update({
            'loc': ManagedInstancePreparer.location,
            'subnet_id': subnet,
            'rg': rg
        })

        if not (self.in_recording or self.is_live):
            self.kwargs.update({
                'subnet_id': subnet.replace(ManagedInstancePreparer.subscription_id,
                                            "00000000-0000-0000-0000-000000000000")
            })

        # test list sql virtual cluster in the subscription, should be at least 1
        virtual_clusters = self.cmd('sql virtual-cluster list',
                                    checks=[
                                        self.greater_than('length(@)', 0),
                                        self.greater_than('length([?subnetId == \'{subnet_id}\'])', 1),
                                        self.check('[?subnetId == \'{subnet_id}\'].location | [0]', '{loc}'),
                                        self.check('[?subnetId == \'{subnet_id}\'].resourceGroup | [0]', '{rg}')])

        # test list sql virtual cluster in the resource group, should be at least 1
        virtual_clusters = self.cmd('sql virtual-cluster list -g {rg}',
                                    checks=[
                                        self.greater_than('length(@)', 0),
                                        self.greater_than('length([?subnetId == \'{subnet_id}\'])', 1),
                                        self.check('[?subnetId == \'{subnet_id}\'].location | [0]', '{loc}'),
                                        self.check('[?subnetId == \'{subnet_id}\'].resourceGroup | [0]',
                                                   '{rg}')]).get_output_in_json()

        virtual_cluster = next(vc for vc in virtual_clusters if vc['subnetId'] == self._apply_kwargs('{subnet_id}'))

        self.kwargs.update({
            'vc_name': virtual_cluster['name']
        })

        # test show sql virtual cluster
        self.cmd('sql virtual-cluster show -g {rg} -n {vc_name}',
                 checks=[
                     self.check('location', '{loc}'),
                     self.check('name', '{vc_name}'),
                     self.check('resourceGroup', '{rg}'),
                     self.check('subnetId', '{subnet_id}')])


class SqlInstanceFailoverGroupMgmtScenarioTest(ScenarioTest):
    def test_sql_instance_failover_group_mgmt(self):
        resource_group_name = ManagedInstancePreparer.group
        primary_name = ManagedInstancePreparer.primary_name
        secondary_name = ManagedInstancePreparer.secondary_name
        secondary_group = ManagedInstancePreparer.sec_group
        failover_group_name = ManagedInstancePreparer.fog_name
        primary_location = ManagedInstancePreparer.location
        secondary_location = ManagedInstancePreparer.sec_location

        # Create Failover Group
        self.cmd(
            'sql instance-failover-group create -n {} -g {} --mi {} --partner-resource-group {} --partner-mi {} --failover-policy Automatic --grace-period 2'
                .format(failover_group_name, resource_group_name, primary_name, secondary_group,
                        secondary_name),
            checks=[
                JMESPathCheck('name', failover_group_name),
                JMESPathCheck('resourceGroup', resource_group_name),
                JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 120)
            ])

        # Get Instance Failover Group on a partner managed instance and check if role is secondary
        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(secondary_group, secondary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('name', failover_group_name),
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                     JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 120),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        # Update Failover Group
        self.cmd('sql instance-failover-group update -g {} -n {} -l {} --grace-period 3 '
                 .format(resource_group_name, failover_group_name, primary_location),
                 checks=[
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                     JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 180),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled')
                 ])

        # Check if properties got propagated to secondary server
        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(secondary_group, secondary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('name', failover_group_name),
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Automatic'),
                     JMESPathCheck('readWriteEndpoint.failoverWithDataLossGracePeriodMinutes', 180),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled'),
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        # Update Failover Group failover policy to Manual
        self.cmd('sql instance-failover-group update -g {} -n {} -l {} --failover-policy Manual'
                 .format(resource_group_name, failover_group_name, primary_location),
                 checks=[
                     JMESPathCheck('readWriteEndpoint.failoverPolicy', 'Manual'),
                     JMESPathCheck('readOnlyEndpoint.failoverPolicy', 'Disabled')
                 ])

        # Failover Failover Group
        self.cmd('sql instance-failover-group set-primary -g {} -n {} -l {} '
                 .format(secondary_group, failover_group_name, secondary_location))

        # The failover operation is completed when new primary is promoted to primary role
        # But there is a async part to make old primary a new secondary
        # And we have to wait for this to complete if we are recording the test
        if self.in_recording:
            time.sleep(30)

        # Check the roles of failover groups to confirm failover happened
        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(secondary_group, secondary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Primary')
                 ])

        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(resource_group_name, primary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        # Fail back to original server
        self.cmd('sql instance-failover-group set-primary --allow-data-loss -g {} -n {} -l {}'
                 .format(resource_group_name, failover_group_name, primary_location))

        # The failover operation is completed when new primary is promoted to primary role
        # But there is a async part to make old primary a new secondary
        # And we have to wait for this to complete if we are recording the test
        if self.in_recording:
            time.sleep(30)

        # Check the roles of failover groups to confirm failover happened
        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(secondary_group, secondary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(resource_group_name, primary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Primary')
                 ])

        # Do no-op failover to the same server
        self.cmd('sql instance-failover-group set-primary -g {} -n {} -l {}'
                 .format(resource_group_name, failover_group_name, primary_location))

        # Check the roles of failover groups to confirm failover didn't happen
        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(secondary_group, secondary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Secondary')
                 ])

        self.cmd('sql instance-failover-group show -g {} -l {} -n {}'
                 .format(resource_group_name, primary_location, failover_group_name),
                 checks=[
                     JMESPathCheck('replicationRole', 'Primary')
                 ])

        # Drop failover group
        self.cmd('sql instance-failover-group delete -g {} -l {} -n {}'
                 .format(resource_group_name, primary_location, failover_group_name),
                 checks=NoneCheck())


class SqlDbSensitivityClassificationsScenarioTest(ScenarioTest):
    def _get_storage_endpoint(self, storage_account, resource_group):
        return self.cmd('storage account show -g {} -n {}'
                        ' --query primaryEndpoints.blob'
                        .format(resource_group, storage_account)).get_output_in_json()

    def _get_storage_key(self, storage_account, resource_group):
        return self.cmd('storage account keys list -g {} -n {} --query [0].value'
                        .format(resource_group, storage_account)).get_output_in_json()

    @ResourceGroupPreparer(location='eastus2')
    @SqlServerPreparer(location='eastus2')
    @StorageAccountPreparer(location='eastus2')
    def test_sql_db_sensitivity_classifications(self, resource_group, resource_group_location, server, storage_account):
        from azure.mgmt.sql.models import SampleName
        database_name = "sensitivityclassificationsdb01"

        # create db
        self.cmd('sql db create -g {} -s {} -n {} --sample-name {}'
                 .format(resource_group, server, database_name, SampleName.adventure_works_lt),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('status', 'Online')])

        # list current sensitivity classifications
        self.cmd('sql db classification list -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('length(@)', 0)])  # No classifications are set at the beginning

        # get storage account endpoint and key
        storage_endpoint = self._get_storage_endpoint(storage_account, resource_group)
        key = self._get_storage_key(storage_account, resource_group)

        # enable ADS - (required to use data classification)
        disabled_alerts_input = 'Sql_Injection_Vulnerability Access_Anomaly'
        disabled_alerts_expected = ['Sql_Injection_Vulnerability', 'Access_Anomaly']
        email_addresses_input = 'test1@example.com test2@example.com'
        email_addresses_expected = ['test1@example.com', 'test2@example.com']
        email_account_admins = True
        state_enabled = 'Enabled'
        retention_days = 30

        self.cmd('sql db threat-policy update -g {} -s {} -n {}'
                 ' --state {} --storage-key {} --storage-endpoint {}'
                 ' --retention-days {} --email-addresses {} --disabled-alerts {}'
                 ' --email-account-admins {}'
                 .format(resource_group, server, database_name, state_enabled, key,
                         storage_endpoint, retention_days, email_addresses_input,
                         disabled_alerts_input, email_account_admins),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageAccountAccessKey', ''),
                     JMESPathCheck('storageEndpoint', storage_endpoint),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('emailAddresses', email_addresses_expected),
                     JMESPathCheck('disabledAlerts', disabled_alerts_expected),
                     JMESPathCheck('emailAccountAdmins', email_account_admins)])

        # list recommended sensitivity classifications
        expected_recommended_sensitivityclassifications_count = 15
        self.cmd('sql db classification recommendation list -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('length(@)', expected_recommended_sensitivityclassifications_count)])

        schema_name = 'SalesLT'
        table_name = 'Customer'
        column_name = 'FirstName'

        # disable the recommendation for SalesLT/Customer/FirstName
        self.cmd('sql db classification recommendation disable -g {} -s {} -n {} --schema {} --table {} --column {}'
                 .format(resource_group, server, database_name, schema_name, table_name, column_name))

        # list recommended sensitivity classifications
        self.cmd('sql db classification recommendation list -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('length(@)', expected_recommended_sensitivityclassifications_count - 1)])

        # re-enable the disabled recommendation
        self.cmd('sql db classification recommendation enable -g {} -s {} -n {} --schema {} --table {} --column {}'
                 .format(resource_group, server, database_name, schema_name, table_name, column_name))

        # lits recommended sensitivity classifications
        self.cmd('sql db classification recommendation list -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('length(@)', expected_recommended_sensitivityclassifications_count)])

        # update the sensitivity classification
        information_type = 'Name'
        label_name = 'Confidential - GDPR'

        response = self.cmd(
            'sql db classification update -g {} -s {} -n {} --schema {} --table {} --column {} --information-type {} --label "{}"'
                .format(resource_group, server, database_name, schema_name, table_name, column_name, information_type,
                        label_name),
            checks=[
                JMESPathCheck('informationType', information_type),
                JMESPathCheck('labelName', label_name)]).get_output_in_json()

        information_type_id = response['informationTypeId']
        label_id = response['labelId']

        # get the classified column
        self.cmd('sql db classification show -g {} -s {} -n {} --schema {} --table {} --column {}'
                 .format(resource_group, server, database_name, schema_name, table_name, column_name),
                 checks=[
                     JMESPathCheck('informationType', information_type),
                     JMESPathCheck('labelName', label_name),
                     JMESPathCheck('informationTypeId', information_type_id),
                     JMESPathCheck('labelId', label_id)])

        # list recommended classifications
        self.cmd('sql db classification recommendation list -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('length(@)', expected_recommended_sensitivityclassifications_count - 1)])

        # list current classifications
        self.cmd('sql db classification list -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('length(@)', 1)])

        # delete the label
        self.cmd('sql db classification delete -g {} -s {} -n {} --schema {} --table {} --column {}'
                 .format(resource_group, server, database_name, schema_name, table_name, column_name))

        # list current labels
        self.cmd('sql db classification list -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('length(@)', 0)])


class SqlServerMinimalTlsVersionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    def test_sql_server_minimal_tls_version(self, resource_group):
        server_name_1 = self.create_random_name(server_name_prefix, server_name_max_length)
        admin_login = 'admin123'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']
        resource_group_location = "eastus"
        tls1_2 = "1.2"
        tls1_1 = "1.1"

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} '
                 '--admin-user {} --admin-password {} --minimal-tls-version {}'
                 .format(resource_group, server_name_1, admin_login, admin_passwords[0], tls1_2),
                 checks=[
                     JMESPathCheck('name', server_name_1),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('minimalTlsVersion', tls1_2)]).get_output_in_json()

        # test update sql server
        self.cmd('sql server update -g {} --name {} --minimal-tls-version {} -i'
                 .format(resource_group, server_name_1, tls1_1),
                 checks=[
                     JMESPathCheck('name', server_name_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('minimalTlsVersion', tls1_1)])


class SqlManagedInstanceFailoverScenarionTest(ScenarioTest):
    @ManagedInstancePreparer()
    def test_sql_mi_failover_mgmt(self, mi, rg):
        self.kwargs.update({
            'resource_group': rg,
            'managed_instance_name': mi
        })

        # Wait for 5 minutes so that first full backup is created
        if self.in_recording or self.is_live:
            sleep(5 * 60)

        # Failover managed instance primary replica
        self.cmd('sql mi failover -g {resource_group} -n {managed_instance_name}', checks=NoneCheck())


class SqlManagedDatabaseLogReplayScenarionTest(ScenarioTest):
    @live_only()
    @AllowLargeResponse()
    @ManagedInstancePreparer()
    def test_sql_midb_logreplay_mgmt(self, mi, rg):

        managed_database_name = 'logReplayTestDb'
        managed_database_name1 = 'logReplayTestDb1'
        # Uploading bak file to blob is restricted by testing framework, so only mitigation for now is to use hard-coded values
        self.kwargs.update({
            'storage_account': 'toolingsa',
            'container_name': 'tools',
            'resource_group': rg,
            'managed_instance_name': mi,
            'managed_database_name': managed_database_name,
            'managed_database_name1': managed_database_name1,
            'storage_uri': 'https://toolingsa.blob.core.windows.net/tools',
            'last_backup_name': 'full.bak'
        })

        from datetime import datetime, timedelta
        self.kwargs['expiry'] = (datetime.utcnow() + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%MZ')

        self.kwargs['storage_key'] = str(self.cmd(
            'az storage account keys list -n {storage_account} -g {resource_group} --query "[0].value"').output)
        self.kwargs['sas_token'] = self.cmd(
            'storage container generate-sas --account-name {storage_account} --account-key {storage_key} --name {container_name} --permissions rl --expiry {expiry}  -otsv').output.strip()

        # Start Log Replay Service
        self.cmd(
            'sql midb log-replay start -g {resource_group} --mi {managed_instance_name} -n {managed_database_name} --ss {sas_token} --su {storage_uri} --no-wait',
            checks=NoneCheck())

        if self.in_recording or self.is_live:
            sleep(10)

        self.cmd(
            'sql midb log-replay wait -g {resource_group} --mi {managed_instance_name} -n {managed_database_name} --exists')

        # Complete log replay service
        self.cmd(
            'sql midb log-replay complete -g {resource_group} --mi {managed_instance_name} -n {managed_database_name} --last-bn {last_backup_name}',
            checks=NoneCheck())

        if self.in_recording or self.is_live:
            sleep(60)

        # Verify status is Online
        self.cmd('sql midb show -g {resource_group} --mi {managed_instance_name} -n {managed_database_name}',
                 checks=[
                     JMESPathCheck('status', 'Online')])

        # Cancel test for Log replay

        # Start Log Replay Service
        self.cmd(
            'sql midb log-replay start -g {resource_group} --mi {managed_instance_name} -n {managed_database_name1} --ss {sas_token} --su {storage_uri} --no-wait',
            checks=NoneCheck())

        self.cmd(
            'sql midb log-replay show -g {resource_group} --mi {managed_instance_name} -n {managed_database_name1}',
            checks=[
                JMESPathCheck('type', 'Microsoft.Sql/managedInstances/databases/restoreDetails'),
                JMESPathCheck('resourceGroup', rg)])

        # Wait a minute to start restoring
        if self.in_recording or self.is_live:
            sleep(60)

        # Cancel log replay service
        self.cmd(
            'sql midb log-replay stop -g {resource_group} --mi {managed_instance_name} -n {managed_database_name1} --yes',
            checks=NoneCheck())


class SqlLedgerDigestUploadsScenarioTest(ScenarioTest):
    def _get_storage_endpoint(self, storage_account, resource_group):
        return self.cmd('storage account show -g {} -n {}'
                        ' --query primaryEndpoints.blob'
                        .format(resource_group, storage_account)).get_output_in_json()

    @ResourceGroupPreparer()
    @SqlServerPreparer(location='westcentralus')
    def test_sql_ledger(self, resource_group, server):
        db_name = self.create_random_name("sqlledgerdb", 20)
        endpoint = "https://test.confidential-ledger.azure.com"

        # create database
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name))

        # validate ledger digest uploads is disabled by default
        self.cmd('sql db ledger-digest-uploads show -g {} -s {} --name {}'
                 .format(resource_group, server, db_name),
                 checks=[JMESPathCheck('state', 'Disabled')])

        # enable uploads to ACL dummy instance
        self.cmd('sql db ledger-digest-uploads enable -g {} -s {} --name {} --endpoint {}'
                 .format(resource_group, server, db_name, endpoint))

        sleep(2)

        # validate setting through show command
        self.cmd('sql db ledger-digest-uploads show -g {} -s {} --name {}'
                 .format(resource_group, server, db_name),
                 checks=[JMESPathCheck('state', 'Enabled'),
                         JMESPathCheck('digestStorageEndpoint', endpoint)])

        # disable ledger digest uploads
        self.cmd('sql db ledger-digest-uploads disable -g {} -s {} --name {}'
                 .format(resource_group, server, db_name))

        sleep(2)

        # validate setting through show command
        self.cmd('sql db ledger-digest-uploads show -g {} -s {} --name {}'
                 .format(resource_group, server, db_name),
                 checks=[JMESPathCheck('state', 'Disabled')])

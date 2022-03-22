# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import pytest
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from dateutil import tz
from ipaddress import ip_network

from azure.cli.testsdk.scenario_tests import AllowLargeResponse, record_only
from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk import ResourceGroupPreparer, StorageAccountPreparer, KeyVaultPreparer, ScenarioTest

from knack.util import CLIError

secret_text_encoding_values = ['utf-8', 'utf-16le', 'utf-16be', 'ascii']
secret_binary_encoding_values = ['base64', 'hex']
secret_encoding_values = secret_text_encoding_values + secret_binary_encoding_values


def _asn1_to_iso8601(asn1_date):
    import dateutil.parser
    if isinstance(asn1_date, bytes):
        asn1_date = asn1_date.decode('utf-8')
    return dateutil.parser.parse(asn1_date)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
KEYS_DIR = os.path.join(TEST_DIR, 'keys')

# for hsm scenario tests
TEST_HSM_NAME = 'ystesthsm'
TEST_HSM_URL = 'https://{}.managedhsm.azure.net'.format(TEST_HSM_NAME)

# for other HSM operations live/playback
ACTIVE_HSM_NAME = 'clitest-1102'
ACTIVE_HSM_URL = 'https://{}.managedhsm.azure.net'.format(ACTIVE_HSM_NAME)

# For security domain playback
SD_ACTIVE_HSM_NAME = 'clitest0914'
SD_ACTIVE_HSM_URL = 'https://{}.managedhsm.azure.net'.format(SD_ACTIVE_HSM_NAME)
SD_NEXT_ACTIVE_HSM_NAME = 'clitest0914b'
SD_NEXT_ACTIVE_HSM_URL = 'https://{}.managedhsm.azure.net'.format(SD_NEXT_ACTIVE_HSM_NAME)


def _create_keyvault(test, kwargs, additional_args=None):
    # need premium KeyVault to store keys in HSM
    # if --enable-soft-delete is not specified, turn that off to prevent the tests from leaving waste behind
    if additional_args is None:
        additional_args = ''
    if '--enable-soft-delete' not in additional_args:
        additional_args += ' --enable-soft-delete false'
    kwargs['add'] = additional_args
    return test.cmd('keyvault create -g {rg} -n {kv} -l {loc} --sku premium --retention-days 7 {add}')


def _create_hsm(test):
    # There's no generic way to get the object id of signed in user/sp, just use a fixed one
    return test.cmd('keyvault create --hsm-name {hsm} -g {rg} -l {loc} '
                    '--administrators "3707fb2f-ac10-4591-a04f-8b0d786ea37d"')


def _delete_and_purge_hsm(test):
    test.cmd('keyvault delete --hsm-name {hsm} -g {rg}')
    test.cmd('keyvault purge --hsm-name {hsm} -l {loc}')
    time.sleep(10)


def _clear_hsm_role_assignments(test, hsm_url, assignees):
    for assignee in assignees:
        test.cmd('keyvault role assignment delete --id {hsm_url} --assignee {assignee}'
                 .format(hsm_url=hsm_url, assignee=assignee))
    time.sleep(10)


def _clear_hsm(test, hsm_url):
    all_keys = test.cmd('keyvault key list --id {hsm_url} --query "[].kid"'
                        .format(hsm_url=hsm_url)).get_output_in_json()
    for key_id in all_keys:
        test.cmd('keyvault key delete --id {key_id}'.format(key_id=key_id))

    time.sleep(10)
    all_keys = test.cmd('keyvault key list-deleted --id {hsm_url} --query "[].kid"'
                        .format(hsm_url=hsm_url)).get_output_in_json()
    for key_id in all_keys:
        test.cmd('keyvault key purge --id {key_id}'.format(key_id=key_id)
                 .replace('/keys/', '/deletedkeys/'))
    time.sleep(10)


class DateTimeParseTest(unittest.TestCase):
    def test_parse_asn1_date(self):
        expected = datetime(year=2017,
                            month=4,
                            day=24,
                            hour=16,
                            minute=37,
                            second=20,
                            tzinfo=tz.tzutc())
        self.assertEqual(_asn1_to_iso8601("20170424163720Z"), expected)


class KeyVaultPrivateLinkResourceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_plr')
    @KeyVaultPreparer(name_prefix='cli-test-kv-plr-', location='eastus2')
    def test_keyvault_private_link_resource(self, resource_group, key_vault):
        self.cmd('keyvault private-link-resource list --vault-name {kv}',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('[0].groupId', 'vault')
                 ])


class KeyVaultMHSMPrivateLinkResourceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_hsm_plr_rg')
    def test_mhsm_private_link_resource(self, resource_group):
        self.kwargs.update({
            'hsm': self.create_random_name('cli-test-hsm-plr-', 24),
            'loc': 'centraluseuap'
        })
        _create_hsm(self)
        self.cmd('keyvault private-link-resource list --hsm-name {hsm}',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('[0].groupId', 'managedhsm')
                 ])
        _delete_and_purge_hsm(self)


class KeyVaultPrivateEndpointConnectionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_pec')
    @KeyVaultPreparer(name_prefix='cli-test-kv-pec-', location='eastus2')
    def test_keyvault_private_endpoint_connection(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'eastus2',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        # Prepare vault and network
        self.kwargs['kv_id'] = self.cmd('keyvault show -n {kv} -g {rg} --query "id" -otsv').output
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pe = self.cmd('network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
                      '--connection-name {pe_connection} --private-connection-resource-id {kv_id} '
                      '--group-id vault').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']

        # Show the connection at vault side
        keyvault = self.cmd('keyvault show -n {kv}',
                            checks=self.check('length(properties.privateEndpointConnections)', 1)).get_output_in_json()
        self.kwargs['kv_pec_id'] = keyvault['properties']['privateEndpointConnections'][0]['id']
        self.cmd('keyvault private-endpoint-connection show --id {kv_pec_id}',
                 checks=self.check('id', '{kv_pec_id}'))
        self.kwargs['kv_pec_name'] = self.kwargs['kv_pec_id'].split('/')[-1]
        self.cmd('keyvault private-endpoint-connection show --vault-name {kv} --name {kv_pec_name}',
                 checks=self.check('name', '{kv_pec_name}'))
        self.cmd('keyvault private-endpoint-connection show --vault-name {kv} -n {kv_pec_name}',
                 checks=self.check('name', '{kv_pec_name}'))

        # Try running `set-policy` on the linked vault
        self.kwargs['policy_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --certificate-permissions get list',
                 checks=self.check('length(properties.accessPolicies[0].permissions.certificates)', 2))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd('keyvault private-endpoint-connection reject --id {kv_pec_id} '
                 '--description "{rejection_desc}" --no-wait', checks=self.is_empty())

        self.cmd('keyvault private-endpoint-connection show --id {kv_pec_id}',
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', '{rejection_desc}'),
                     self.check('provisioningState', 'Updating')
                 ])

        self.cmd('keyvault private-endpoint-connection wait --id {kv_pec_id} --created')
        self.cmd('keyvault private-endpoint-connection show --id {kv_pec_id}',
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', '{rejection_desc}'),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('keyvault private-endpoint-connection approve --vault-name {kv} --name {kv_pec_name} '
                 '--description "{approval_desc}"', checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('privateLinkServiceConnectionState.description', '{approval_desc}'),
                     self.check('provisioningState', 'Updating')
                 ])


class KeyVaultHSMPrivateEndpointConnectionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_pec')
    def test_hsm_private_endpoint_connection(self, resource_group):
        self.kwargs.update({
            'hsm': self.create_random_name('cli-test-hsm-pec-', 24),
            'loc': 'centraluseuap',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        # Prepare vault and network
        hsm = _create_hsm(self).get_output_in_json()
        self.kwargs['hsm_id'] = hsm['id']
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pe = self.cmd('network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
                      '--connection-name {pe_connection} --private-connection-resource-id {hsm_id} '
                      '--group-id managedhsm').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']

        # Show the connection at vault side
        hsm = self.cmd('keyvault show --hsm-name {hsm}',
                       checks=self.check('length(properties.privateEndpointConnections)', 1)).get_output_in_json()
        self.kwargs['hsm_pec_id'] = hsm['properties']['privateEndpointConnections'][0]['id']
        self.cmd('keyvault private-endpoint-connection show --id {hsm_pec_id}',
                 checks=self.check('id', '{hsm_pec_id}'))
        self.kwargs['hsm_pec_name'] = self.kwargs['hsm_pec_id'].split('/')[-1]
        self.cmd('keyvault private-endpoint-connection show --hsm-name {hsm} --name {hsm_pec_name}',
                 checks=self.check('name', '{hsm_pec_name}'))

        # List private endpoint connections
        self.cmd('keyvault private-endpoint-connection list --hsm-name {hsm}',
                 checks=[self.check('length(@)', 1), self.check('[0].id', '{hsm_pec_id}')])

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd('keyvault private-endpoint-connection approve --hsm-name {hsm} --name {hsm_pec_name} '
                 '--description "{approval_desc}"', checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('privateLinkServiceConnectionState.description', '{approval_desc}'),
                     self.check('provisioningState', 'Updating')
                 ])
        self.cmd('keyvault private-endpoint-connection wait --id {hsm_pec_id} --created')

        self.cmd('keyvault private-endpoint-connection reject --id {hsm_pec_id} '
                 '--description "{rejection_desc}" --no-wait', checks=self.is_empty())

        self.cmd('keyvault private-endpoint-connection wait --id {hsm_pec_id} --created')
        self.cmd('keyvault private-endpoint-connection show --id {hsm_pec_id}',
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', '{rejection_desc}'),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('keyvault private-endpoint-connection delete --hsm-name {hsm} --name {hsm_pec_name}')

        # clear resources
        self.cmd('network private-endpoint delete -g {rg} -n {pe}')
        _delete_and_purge_hsm(self)


class KeyVaultHSMMgmtScenarioTest(ScenarioTest):

    def test_keyvault_hsm_mgmt(self):
        self.kwargs.update({
            'hsm_name': self.create_random_name('clitest-mhsm-', 24),
            'rg': 'clitest-mhsm-rg',
            'loc': 'eastus2',
            'init_admin': '3707fb2f-ac10-4591-a04f-8b0d786ea37d'
        })

        show_checks = [
            self.check('location', '{loc}'),
            self.check('name', '{hsm_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('sku.name', 'Standard_B1'),
            self.check('type', 'Microsoft.KeyVault/managedHSMs'),
            self.check('length(properties.initialAdminObjectIds)', 1),
            self.check('properties.initialAdminObjectIds[0]', '{init_admin}'),
            self.exists('properties.hsmUri')
        ]

        show_deleted_checks = [
            self.check('name', '{hsm_name}'),
            self.check('type', 'Microsoft.Keyvault/deletedManagedHSMs'),
            self.check('properties.location', '{loc}'),
            self.exists('properties.deletionDate')
        ]

        list_checks = [
            self.check('length(@)', 1),
            self.check('[0].location', '{loc}'),
            self.check('[0].name', '{hsm_name}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].sku.name', 'Standard_B1'),
            self.check('length([0].properties.initialAdminObjectIds)', 1),
            self.check('[0].properties.initialAdminObjectIds[0]', '{init_admin}'),
            self.exists('[0].properties.hsmUri')
        ]

        list_deleted_checks = [
            self.check('length([?name==\'{hsm_name}\'])', 1),
            self.exists('[?name==\'{hsm_name}\'&&properties.location==\'{loc}\'&&properties.deletionDate]'),
        ]

        self.cmd('group create -g {rg} -l {loc}'),
        self.cmd('keyvault create --hsm-name {hsm_name} -g {rg} -l {loc} --administrators {init_admin}')

        self.cmd('keyvault show --hsm-name {hsm_name}', checks=show_checks)
        self.cmd('keyvault show --hsm-name {hsm_name} -g {rg}', checks=show_checks)

        self.cmd('keyvault update-hsm --hsm-name {hsm_name} --bypass None', checks=[
            self.check('properties.networkAcls.bypass', 'None')
        ])

        self.cmd(r"keyvault list --resource-type hsm --query [?name==\'{hsm_name}\']", checks=list_checks)
        self.cmd('keyvault list --resource-type hsm -g {rg}', checks=list_checks)

        self.cmd('keyvault delete --hsm-name {hsm_name}')
        self.cmd('keyvault show-deleted --hsm-name {hsm_name}', checks=show_deleted_checks)
        self.cmd('keyvault show-deleted --hsm-name {hsm_name} -l {loc}', checks=show_deleted_checks)
        self.cmd('keyvault list-deleted --resource-type hsm', checks=list_deleted_checks)

        self.cmd('keyvault recover --hsm-name {hsm_name}')
        self.cmd('keyvault show --hsm-name {hsm_name}', checks=show_checks)
        time.sleep(120)

        self.cmd('keyvault delete --hsm-name {hsm_name}')
        self.cmd('keyvault purge --hsm-name {hsm_name}')
        self.cmd('group delete -n {rg} --yes')


class KeyVaultMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_mgmt')
    def test_keyvault_mgmt(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-mgmt-', 24),
            'kv2': self.create_random_name('cli-test-kv-mgmt-', 24),
            'kv3': self.create_random_name('cli-test-kv-mgmt-', 24),
            'kv4': self.create_random_name('cli-test-kv-mgmt-', 24),
            'loc': 'eastus'
        })

        # test create keyvault with default access policy set
        keyvault = self.cmd('keyvault create -g {rg} -n {kv} -l {loc}', checks=[
            self.check('name', '{kv}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 1),
            self.check('properties.sku.name', 'standard'),
            self.check('properties.enableSoftDelete', True),
            self.check('properties.enablePurgeProtection', None),
            self.check('properties.softDeleteRetentionInDays', 90)
        ]).get_output_in_json()

        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaisesRegex(InvalidArgumentValueError, 'already exist'):
            self.cmd('keyvault create -g {rg} -n {kv} -l {loc}')
        self.kwargs['policy_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        self.cmd('keyvault show -n {kv}', checks=[
            self.check('name', '{kv}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 1),
        ])
        self.cmd('keyvault list -g {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{kv}'),
            self.check('[0].location', '{loc}'),
            self.check('[0].resourceGroup', '{rg}')
        ])
        # test updating keyvault sku name
        self.cmd('keyvault update -g {rg} -n {kv} --set properties.sku.name=premium', checks=[
            self.check('name', '{kv}'),
            self.check('properties.sku.name', 'premium'),
        ])
        # test updating updating other properties
        self.cmd('keyvault update -g {rg} -n {kv} --enable-soft-delete '
                 '--enabled-for-deployment --enabled-for-disk-encryption --enabled-for-template-deployment '
                 '--bypass AzureServices --default-action Deny',
                 checks=[
                     self.check('name', '{kv}'),
                     self.check('properties.enableSoftDelete', True),
                     self.check('properties.enablePurgeProtection', None),
                     self.check('properties.enabledForDeployment', True),
                     self.check('properties.enabledForDiskEncryption', True),
                     self.check('properties.enabledForTemplateDeployment', True),
                     self.check('properties.networkAcls.bypass', 'AzureServices'),
                     self.check('properties.networkAcls.defaultAction', 'Deny')
                 ])
        # test policy set
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --key-permissions get wrapkey wrapKey',
                 checks=self.check('length(properties.accessPolicies[0].permissions.keys)', 2))
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --key-permissions get wrapkey wrapkey',
                 checks=self.check('length(properties.accessPolicies[0].permissions.keys)', 2))
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --certificate-permissions get list',
                 checks=self.check('length(properties.accessPolicies[0].permissions.certificates)', 2))
        # test policy for compound identity set
        result = self.cmd('ad app create --display-name {kv}').get_output_in_json()
        self.kwargs['app_id'] = result['appId']
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --application-id {app_id} --key-permissions get list',
                 checks=[
                     self.check('properties.accessPolicies[1].applicationId', self.kwargs['app_id']),
                     self.check('properties.accessPolicies[1].objectId', self.kwargs['policy_id']),
                     self.check('length(properties.accessPolicies[1].permissions.keys)', 2)
                 ])
        # test policy for compound identity delete
        self.cmd('keyvault delete-policy -g {rg} -n {kv} --object-id {policy_id} --application-id {app_id}',
                 checks=self.check('length(properties.accessPolicies)', 1))
        self.cmd('ad app delete --id {app_id}')
        # test policy delete
        self.cmd('keyvault delete-policy -g {rg} -n {kv} --object-id {policy_id}', checks=[
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 0)
        ])

        # test keyvault delete
        self.cmd('keyvault delete -n {kv}')
        self.cmd('keyvault list -g {rg}', checks=self.is_empty())
        self.cmd('keyvault show-deleted -n {kv}', checks=self.check('type', 'Microsoft.KeyVault/deletedVaults'))
        self.cmd('keyvault purge -n {kv}')
        # ' will be parsed by shlex, so need escaping
        self.cmd(r"az keyvault list-deleted --resource-type vault --query [?name==\'{kv}\']", checks=self.is_empty())

        # test create keyvault further
        self.cmd('keyvault create -g {rg} -n {kv2} -l {loc} '  # enableSoftDelete is True if omitted
                 '--retention-days 7 '
                 '--sku premium '
                 '--enabled-for-deployment true --enabled-for-disk-encryption true --enabled-for-template-deployment true '
                 '--no-self-perms ',  # no self permission assigned
                 checks=[
                     self.check('properties.enableSoftDelete', True),
                     self.check('properties.softDeleteRetentionInDays', 7),
                     self.check('properties.sku.name', 'premium'),
                     self.check('properties.enabledForDeployment', True),
                     self.check('properties.enabledForDiskEncryption', True),
                     self.check('properties.enabledForTemplateDeployment', True),
                     self.check('type(properties.accessPolicies)', 'array'),
                     self.check('length(properties.accessPolicies)', 0),
                 ])
        self.cmd('keyvault delete -n {kv2}')
        self.cmd('keyvault purge -n {kv2}')

        # test explicitly set '--enable-soft-delete true --enable-purge-protection true'
        # unfortunately this will leave some waste behind, so make it the last test to lowered the execution count
        self.cmd('keyvault create -g {rg} -n {kv4} -l {loc} --enable-soft-delete true --enable-purge-protection true',
                 checks=[self.check('properties.enableSoftDelete', True),
                         self.check('properties.enablePurgeProtection', True)])

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_list_deleted')
    def test_keyvault_list_deleted(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-mgmt-', 24),
            'hsm': self.create_random_name('cli-test-hsm-mgmt-', 24),
            'loc': 'eastus'
        })
        _create_keyvault(self, self.kwargs, additional_args='--enable-soft-delete')
        _create_hsm(self)

        # delete resources
        self.cmd('keyvault delete --name {kv}')
        self.cmd('keyvault delete --hsm-name {hsm}')

        # test list deleted vaults
        self.cmd('keyvault list-deleted --resource-type vault', checks=[
            self.exists("[?name=='{kv}']"),
            self.not_exists("[?name=='{hsm}']")
        ])
        # test list deleted hsms
        self.cmd('keyvault list-deleted --resource-type hsm', checks=[
            self.exists("[?name=='{hsm}']"),
            self.not_exists("[?name=='{kv}']")
        ])
        # test list deleted vaults and hsms
        self.cmd('keyvault list-deleted', checks=[
            self.exists("[?name=='{hsm}']"),
            self.exists("[?name=='{kv}']")
        ])

        # clean resources
        self.cmd('keyvault purge --name {kv} -l {loc}')
        self.cmd('keyvault purge --hsm-name {hsm} -l {loc}')


class KeyVaultHSMSecurityDomainScenarioTest(ScenarioTest):
    @record_only()
    @AllowLargeResponse()
    def test_keyvault_hsm_security_domain(self):
        sdtest_dir = tempfile.mkdtemp()
        self.kwargs.update({
            'hsm_url': SD_ACTIVE_HSM_NAME,
            'hsm_name': SD_ACTIVE_HSM_NAME,
            'next_hsm_url': SD_NEXT_ACTIVE_HSM_URL,
            'next_hsm_name': SD_NEXT_ACTIVE_HSM_NAME,
            'loc': 'eastus2',
            'init_admin': '9ac02ab3-5061-4ec6-a3d8-2cdaa5f29efa',
            'key_name': self.create_random_name('key', 10),
            'rg': 'bim-rg',
            'sdtest_dir': sdtest_dir
        })
        self.kwargs.update({
            'sdfile': os.path.join(self.kwargs['sdtest_dir'], 'sdfile.json'),
            'exchange_key': os.path.join(self.kwargs['sdtest_dir'], 'sdex.pem'),
            'key_backup': os.path.join(self.kwargs['sdtest_dir'], 'key.bak')
        })

        for i in range(1, 4):
            self.kwargs['cer{}_path'.format(i)] = os.path.join(KEYS_DIR, 'sd{}.cer'.format(i))
            self.kwargs['key{}_path'.format(i)] = os.path.join(KEYS_DIR, 'sd{}.pem'.format(i))

        # create a new key and backup it
        self.cmd('az keyvault key create --hsm-name {hsm_name} -n {key_name}')
        self.cmd('az keyvault key backup --hsm-name {hsm_name} -n {key_name} -f "{key_backup}"')

        # download SD
        self.cmd('az keyvault security-domain download --hsm-name {hsm_name} --security-domain-file "{sdfile}" '
                 '--sd-quorum 2 --sd-wrapping-keys "{cer1_path}" "{cer2_path}" "{cer3_path}" --no-wait')

        # delete the HSM
        self.cmd('az keyvault delete --hsm-name {hsm_name}')

        # create a new HSM
        self.cmd('az keyvault create --hsm-name {next_hsm_name} -l {loc} -g {rg} --administrators {init_admin} '
                 '--retention-days 7 --no-wait')

        # wait until the HSM is ready for recovery
        self.cmd('az keyvault wait-hsm --hsm-name {next_hsm_name} --created')

        # download the exchange key
        self.cmd('az keyvault security-domain init-recovery --hsm-name {next_hsm_name} '
                 '--sd-exchange-key "{exchange_key}"')

        # upload the blob
        self.cmd('az keyvault security-domain upload --hsm-name {next_hsm_name} --sd-file "{sdfile}" '
                 '--sd-exchange-key "{exchange_key}" '
                 '--sd-wrapping-keys "{key1_path}" "{key2_path}"')

        # restore the key
        self.cmd('az keyvault key restore --hsm-name {next_hsm_name} -f "{key_backup}"')

        files = ['sdfile', 'exchange_key', 'key_backup']
        for f in files:
            if os.path.exists(self.kwargs[f]):
                os.remove(self.kwargs[f])


class KeyVaultHSMSelectiveKeyRestoreScenarioTest(ScenarioTest):
    # @record_only()
    @unittest.skip('cannot run')
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_hsm_selective_key_restore')
    def test_keyvault_hsm_selective_key_restore(self):
        self.kwargs.update({
            'hsm_url': ACTIVE_HSM_URL,
            'hsm_name': ACTIVE_HSM_NAME,
            'key_name': self.create_random_name('selective-restore-', 24),
            'storage_account': self.create_random_name('clitesthsmsa', 24),
            'blob': self.create_random_name('clitesthsmblob', 24),
            'sas_start': (datetime.utcnow() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'sas_expiry': (datetime.utcnow() + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
        })

        _clear_hsm(self, hsm_url=self.kwargs['hsm_url'])
        key = self.cmd('az keyvault key create -n {key_name} --hsm-name {hsm_name}').get_output_in_json()
        self.kwargs['kid'] = '/'.join(key['key']['kid'].split('/')[:-1])
        self.cmd('az storage account create -n {storage_account} -g {rg}')
        self.cmd('az storage container create -n {blob} --account-name {storage_account} -g {rg}')

        self.kwargs['sas'] = '?' + self.cmd('az storage account generate-sas --start {sas_start} --expiry {sas_expiry} '
                                            '--https-only '
                                            '--permissions rwdlacu --resource-types sco --services b '
                                            '--account-name {storage_account}').get_output_in_json().replace('%3A', ':')

        backup_data = self.cmd('az keyvault backup start --hsm-name {hsm_name} --blob-container-name {blob} '
                               '--storage-account-name {storage_account} '
                               '--storage-container-SAS-token "{sas}"',
                               checks=[
                                   self.check('status', 'Succeeded'),
                                   self.exists('startTime'),
                                   self.exists('jobId'),
                                   self.exists('folderUrl')
                               ]).get_output_in_json()

        self.kwargs['backup_folder'] = backup_data['folderUrl'].split('/')[-1]

        self.cmd('az keyvault key list --hsm-name {hsm_name}', checks=self.check('length(@)', 1))
        self.cmd('az keyvault key delete -n {key_name} --hsm-name {hsm_name}')
        self.cmd('az keyvault key purge -n {key_name} --hsm-name {hsm_name}')
        self.cmd('az keyvault key list --hsm-name {hsm_name}', checks=self.check('length(@)', 0))

        self.cmd('az keyvault key restore --hsm-name {hsm_name} --blob-container-name {blob} '
                 '--storage-account-name {storage_account} '
                 '--storage-container-SAS-token "{sas}" '
                 '--backup-folder "{backup_folder}" '
                 '--name {key_name}', checks=self.check('status', 'Succeeded'))

        self.cmd('az keyvault key list --hsm-name {hsm_name}', checks=[
            self.check('length(@)', 1),
            self.check('[0].kid', '{kid}')
        ])


class KeyVaultHSMFullBackupRestoreScenarioTest(ScenarioTest):
    # @record_only()
    @unittest.skip('cannot run')
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_hsm_full_backup')
    @AllowLargeResponse()
    def test_keyvault_hsm_full_backup_restore(self):
        self.kwargs.update({
            'hsm_url': ACTIVE_HSM_URL,
            'hsm_name': ACTIVE_HSM_NAME,
            'storage_account': self.create_random_name('clitesthsmsa', 24),
            'blob': self.create_random_name('clitesthsmblob', 24),
            'sas_start': (datetime.utcnow() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'sas_expiry': (datetime.utcnow() + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
        })
        self.cmd('az storage account create -n {storage_account} -g {rg}')
        self.cmd('az storage container create -n {blob} --account-name {storage_account} -g {rg}')

        self.kwargs['sas'] = '?' + self.cmd('az storage account generate-sas --start {sas_start} --expiry {sas_expiry} '
                                            '--https-only '
                                            '--permissions rwdlacu --resource-types sco --services b '
                                            '--account-name {storage_account}').get_output_in_json().replace('%3A', ':')

        self.cmd('az keyvault backup start --id {hsm_url} --blob-container-name {blob} '
                 '--storage-account-name {storage_account} '
                 '--storage-container-SAS-token "{sas}"',
                 checks=[
                     self.check('status', 'Succeeded'),
                     self.exists('startTime'),
                     self.exists('jobId'),
                     self.exists('folderUrl')
                 ])

        backup_data = self.cmd('az keyvault backup start --hsm-name {hsm_name} --blob-container-name {blob} '
                               '--storage-account-name {storage_account} '
                               '--storage-container-SAS-token "{sas}"',
                               checks=[
                                   self.check('status', 'Succeeded'),
                                   self.exists('startTime'),
                                   self.exists('jobId'),
                                   self.exists('folderUrl')
                               ]).get_output_in_json()

        self.kwargs['backup_folder'] = backup_data['folderUrl'].split('/')[-1]
        self.cmd('az keyvault restore start --hsm-name {hsm_name} --blob-container-name {blob} '
                 '--storage-account-name {storage_account} '
                 '--storage-container-SAS-token "{sas}" '
                 '--backup-folder "{backup_folder}"',
                 checks=[
                     self.check('status', 'Succeeded'),
                     self.exists('startTime'),
                     self.exists('jobId')
                 ])


class KeyVaultHSMRoleScenarioTest(ScenarioTest):
    # @record_only()
    @unittest.skip('cannot run')
    def test_keyvault_hsm_role(self):
        self.kwargs.update({
            'hsm_url': ACTIVE_HSM_URL,
            'hsm_name': ACTIVE_HSM_NAME,
            'key1': self.create_random_name('key-role-', 24),
            'key2': self.create_random_name('key-role-', 24),
            'role_name1': 'Managed HSM Crypto Officer',
            'role_name2': 'Managed HSM Crypto User',
            'user1': 'fey_microsoft.com#EXT#@AzureSDKTeam.onmicrosoft.com',
            'user2': 'jiasli_microsoft.com#EXT#@AzureSDKTeam.onmicrosoft.com',
            'user3': 'yungez_microsoft.com#EXT#@AzureSDKTeam.onmicrosoft.com',
            'user3_principal_id': '7e58ddef-4719-4c36-a485-4c2a0a843a46'
        })

        for i in range(10):
            self.kwargs['role_assignment_name{}'.format(i + 1)] = self.create_guid()

        _clear_hsm_role_assignments(self, hsm_url=self.kwargs['hsm_url'],
                                    assignees=[self.kwargs['user1'], self.kwargs['user2'], self.kwargs['user3']])

        role_definitions = self.cmd('keyvault role definition list --hsm-name {hsm_name}').get_output_in_json()

        role_def1 = [r for r in role_definitions if r['roleName'] == self.kwargs['role_name1']][0]
        role_def2 = [r for r in role_definitions if r['roleName'] == self.kwargs['role_name2']][0]

        self.kwargs.update({
            'role_def_id1': role_def1['id'],
            'role_def_id2': role_def2['id'],
            'role_def_name1': role_def1['name'],
            'role_def_name2': role_def2['name']
        })

        # user1 + role1/role2
        role_assignment1 = self.cmd('keyvault role assignment create --id {hsm_url} --role "{role_name1}" '
                                    '--assignee {user1} --scope keys --name {role_assignment_name1}',
                                    checks=[
                                        self.check('name', '{role_assignment_name1}'),
                                        self.check('roleDefinitionId', '{role_def_id1}'),
                                        self.check('roleName', '{role_name1}'),
                                        self.check('principalName', '{user1}'),
                                        self.check('scope', '/keys')
                                    ]).get_output_in_json()
        self.kwargs['role_assignment_id1'] = role_assignment1['id']

        role_assignment2 = self.cmd('keyvault role assignment create --hsm-name {hsm_name} --role "{role_name2}" '
                                    '--assignee {user1} --scope "/" --name {role_assignment_name2}',
                                    checks=[
                                        self.check('name', '{role_assignment_name2}'),
                                        self.check('roleDefinitionId', '{role_def_id2}'),
                                        self.check('roleName', '{role_name2}'),
                                        self.check('principalName', '{user1}'),
                                        self.check('scope', '/')
                                    ]).get_output_in_json()
        self.kwargs['role_assignment_id2'] = role_assignment2['id']

        # user2 + role1/role2
        self.cmd('keyvault role assignment create --id {hsm_url} --role "{role_name1}" '
                 '--assignee {user2} --scope keys --name {role_assignment_name3}',
                 checks=[
                     self.check('name', '{role_assignment_name3}'),
                     self.check('roleDefinitionId', '{role_def_id1}'),
                     self.check('roleName', '{role_name1}'),
                     self.check('principalName', '{user2}'),
                     self.check('scope', '/keys')
                 ]).get_output_in_json()

        self.cmd('keyvault role assignment create --id {hsm_url} --role "{role_name2}" '
                 '--assignee {user2} --scope "/" --name {role_assignment_name4}',
                 checks=[
                     self.check('name', '{role_assignment_name4}'),
                     self.check('roleDefinitionId', '{role_def_id2}'),
                     self.check('roleName', '{role_name2}'),
                     self.check('principalName', '{user2}'),
                     self.check('scope', '/')
                 ]).get_output_in_json()

        # user3 + role1/role2
        self.cmd('keyvault role assignment create --id {hsm_url} --role "{role_name1}" '
                 '--assignee {user3_principal_id} --scope keys --name {role_assignment_name5}',
                 checks=[
                     self.check('name', '{role_assignment_name5}'),
                     self.check('principalId', '{user3_principal_id}'),
                     self.check('roleDefinitionId', '{role_def_id1}'),
                     self.check('roleName', '{role_name1}'),
                     self.check('principalName', '{user3}'),
                     self.check('scope', '/keys')
                 ]).get_output_in_json()

        self.cmd('keyvault role assignment create --id {hsm_url} --role "{role_name2}" '
                 '--assignee-object-id {user3_principal_id} --scope "/" --name {role_assignment_name6}',
                 checks=[
                     self.check('name', '{role_assignment_name6}'),
                     self.check('principalId', '{user3_principal_id}'),
                     self.check('roleDefinitionId', '{role_def_id2}'),
                     self.check('roleName', '{role_name2}'),
                     self.check('principalName', '{user3}'),
                     self.check('scope', '/')
                 ]).get_output_in_json()

        time.sleep(10)

        # list all (including this one: assignee=bim,role=Administrator, scope=/)
        self.cmd('keyvault role assignment list --id {hsm_url}', checks=self.check('length(@)', 7))

        # list by scope
        self.cmd('keyvault role assignment list --id {hsm_url} --scope keys', checks=self.check('length(@)', 3))
        self.cmd('keyvault role assignment list --hsm-name {hsm_name} --scope /keys', checks=self.check('length(@)', 3))
        self.cmd('keyvault role assignment list --id {hsm_url} --scope ""', checks=self.check('length(@)', 4))
        self.cmd('keyvault role assignment list --hsm-name {hsm_name} --scope "/"', checks=self.check('length(@)', 4))

        # list by role
        self.cmd('keyvault role assignment list --id {hsm_url} --role "{role_name1}"',
                 checks=self.check('length(@)', 3))
        self.cmd('keyvault role assignment list --hsm-name {hsm_name} --role "{role_name2}"',
                 checks=self.check('length(@)', 3))

        # list by assignee
        self.cmd('keyvault role assignment list --id {hsm_url} --assignee {user1}',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault role assignment list --hsm-name {hsm_name} --assignee {user2}',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault role assignment list --id {hsm_url} --assignee {user3_principal_id}',
                 checks=self.check('length(@)', 2))

        # list by multiple conditions
        self.cmd('keyvault role assignment list --id {hsm_url} --assignee {user1} --scope keys',
                 checks=self.check('length(@)', 1))
        self.cmd('keyvault role assignment list --hsm-name {hsm_name} --assignee {user1} --role "{role_name1}"',
                 checks=self.check('length(@)', 1))
        self.cmd('keyvault role assignment list --id {hsm_url} --assignee {user3_principal_id} --role "{role_name1}" '
                 '--scope keys',
                 checks=self.check('length(@)', 1))
        self.cmd('keyvault role assignment list --id {hsm_url} --assignee {user3_principal_id} --role "{role_name2}" '
                 '--scope ""',
                 checks=self.check('length(@)', 1))
        self.cmd('keyvault role assignment list --id {hsm_url} --assignee {user3_principal_id} --role "{role_name2}" '
                 '--scope keys',
                 checks=self.check('length(@)', 0))

        # delete by ids
        self.cmd('keyvault role assignment delete --id {hsm_url} --ids {role_assignment_id1} {role_assignment_id2}',
                 checks=self.check('length(@)', 2))

        # delete by name
        self.cmd('keyvault role assignment delete --hsm-name {hsm_name} --name {role_assignment_name3}',
                 checks=self.check('length(@)', 1))

        # delete by assignee
        self.cmd('keyvault role assignment delete --id {hsm_url} --assignee {user2}',
                 checks=self.check('length(@)', 1))

        # delete by role
        self.cmd('keyvault role assignment delete --id {hsm_url} --role "{role_name2}"',
                 checks=self.check('length(@)', 1))

        # delete by scope
        self.cmd('keyvault role assignment delete --hsm-name {hsm_name} --scope keys',
                 checks=self.check('length(@)', 1))

        # check final result
        self.cmd('keyvault role assignment list --id {hsm_url}', checks=self.check('length(@)', 1))


class RoleDefinitionNameReplacer(RecordingProcessor):

    def process_request(self, request):
        if 'providers/Microsoft.Authorization/roleDefinitions/' in request.uri:
            uri_pieces = request.uri.split('/')
            uri_pieces[-1] = '00000000-0000-0000-0000-000000000000'
            request.uri = '/'.join(uri_pieces)
        return request


class KeyVaultHSMRoleDefintionTest(ScenarioTest):

    def __init__(self, method_name):
        super(KeyVaultHSMRoleDefintionTest, self).__init__(
            method_name,
            recording_processors=[RoleDefinitionNameReplacer()],
            replay_processors=[RoleDefinitionNameReplacer()]
        )

    # @record_only()
    def test_keyvault_role_definition(self):

        def role_definition_checks():
            checks = [
                self.check('roleName', '{roleName}'),
                self.check('description', '{description}'),
                self.check('roleType', 'CustomRole'),
                self.check('type', 'Microsoft.Authorization/roleDefinitions'),
                self.check('assignableScopes', ['/']),
                self.check('permissions[0].actions', self.kwargs.get('actions', None)),
                self.check('permissions[0].notActions', self.kwargs.get('notActions', None)),
                self.check('permissions[0].dataActions', self.kwargs.get('dataActions', None)),
                self.check('permissions[0].notDataActions', self.kwargs.get('notDataActions', None))
            ]
            return checks

        self.kwargs.update({
            'hsm_name': 'clitest-hsm',
            'roleName': 'TestCustomRole',
            'description': 'Custom role description',
            'actions': [],
            'notActions': [],
            'dataActions': ['Microsoft.KeyVault/managedHsm/keys/sign/action'],
            'notDataActions': []
        })

        role_definition = {
            'roleName': self.kwargs.get('roleName', None),
            'description': self.kwargs.get('description', None),
            'actions': self.kwargs.get('actions', None),
            'notActions': self.kwargs.get('notActions', None),
            'dataActions': self.kwargs.get('dataActions', None),
            'notDataActions': self.kwargs.get('notDataActions', None),
        }

        _, temp_file = tempfile.mkstemp()
        with open(temp_file, 'w') as f:
            json.dump(role_definition, f)

        self.kwargs.update({
            'role_definition': temp_file.replace('\\', '\\\\')
        })

        # record existing role definition number
        results = self.cmd('keyvault role definition list --hsm-name {hsm_name}').get_output_in_json()
        self.kwargs.update({
            'role_number': len(results)
        })

        # check create a role defintion
        custom_role_definition = self.cmd('keyvault role definition create --hsm-name {hsm_name} --role-definition {role_definition}',
                                          checks=role_definition_checks()).get_output_in_json()

        self.kwargs.update({
            'name': custom_role_definition.get('name', None),
            'id': custom_role_definition.get('id', None)
        })
        self.cmd('keyvault role definition show --hsm-name {hsm_name} --name {name}',
                 checks=role_definition_checks())

        # update the role definition
        self.kwargs.update({
            'dataActions': [
                'Microsoft.KeyVault/managedHsm/keys/read/action',
                'Microsoft.KeyVault/managedHsm/keys/write/action',
                'Microsoft.KeyVault/managedHsm/keys/backup/action',
                'Microsoft.KeyVault/managedHsm/keys/create'
            ]
        })
        role_definition['name'] = self.kwargs.get('name', None)
        role_definition['id'] = self.kwargs.get('id', None)
        role_definition['dataActions'] = self.kwargs.get('dataActions', None)

        _, temp_file = tempfile.mkstemp()
        with open(temp_file, 'w') as f:
            json.dump(role_definition, f)

        self.kwargs.update({
            'updated_role_definition': temp_file.replace('\\', '\\\\')
        })

        # check update a role definition
        self.cmd('keyvault role definition update --hsm-name {hsm_name} --role-definition {updated_role_definition}',
                 checks=role_definition_checks())
        self.cmd('keyvault role definition show --hsm-name {hsm_name} --name {name}',
                 checks=role_definition_checks())

        # check list role definitions
        self.cmd('keyvault role definition list --hsm-name {hsm_name}',
                 checks=[self.check('length(@)', self.kwargs.get('role_number') + 1)])

        # check delete a role definition
        self.cmd('keyvault role definition delete --hsm-name {hsm_name} --name {name}')
        self.cmd('keyvault role definition list --hsm-name {hsm_name}',
                 checks=[self.check('length(@)', self.kwargs.get('role_number'))])


class KeyVaultKeyScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_key')
    @KeyVaultPreparer(name_prefix='cli-test-kv-key-', location='eastus2')
    @KeyVaultPreparer(name_prefix='cli-test-kv-key-', location='eastus2', sku='premium',
                      parameter_name='key_vault2', key='kv2')
    def test_keyvault_key(self, resource_group, key_vault, key_vault2):
        self.kwargs.update({
            'loc': 'eastus2',
            'key': self.create_random_name('key1-', 24),
            'key2': self.create_random_name('key2-', 24)
        })
        keyvault = self.cmd('keyvault show -n {kv} -g {rg}').get_output_in_json()
        self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        key_perms = keyvault['properties']['accessPolicies'][0]['permissions']['keys']
        key_perms.extend(['encrypt', 'decrypt', 'purge'])
        self.kwargs['key_perms'] = ' '.join(key_perms)

        # create a key
        key = self.cmd('keyvault key create --vault-name {kv} -n {key} -p software',
                       checks=self.check('attributes.enabled', True)).get_output_in_json()
        first_kid = key['key']['kid']
        first_version = first_kid.rsplit('/', 1)[1]
        self.cmd('keyvault key create --vault-name {kv} -n {key2}')

        # encrypt/decrypt
        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms}')
        self.kwargs['plaintext_value'] = 'abcdef'
        self.kwargs['base64_value'] = 'YWJjZGVm'
        self.kwargs['encryption_result1'] = self.cmd('keyvault key encrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{plaintext_value}" --data-type plaintext').get_output_in_json()['result']
        self.kwargs['encryption_result2'] = self.cmd('keyvault key encrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{base64_value}" --data-type base64').get_output_in_json()['result']
        self.cmd('keyvault key decrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{encryption_result1}" --data-type plaintext',
                 checks=self.check('result', '{plaintext_value}'))
        self.cmd('keyvault key decrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{encryption_result2}" --data-type base64',
                 checks=self.check('result', '{base64_value}'))

        # list keys
        self.cmd('keyvault key list --vault-name {kv}',
                 checks=[
                     self.check('length(@)', 2),
                     self.exists('[0].name')
                 ])
        self.cmd('keyvault key list --vault-name {kv} --maxresults 10', checks=self.check('length(@)', 2))
        self.cmd('keyvault key list --vault-name {kv} --maxresults 1', checks=self.check('length(@)', 1))

        # create a new key version
        key = self.cmd('keyvault key create --vault-name {kv} -n {key} -p software --disabled --ops encrypt decrypt '
                       '--tags test=foo',
                       checks=[
                           self.check('attributes.enabled', False),
                           self.check('length(key.keyOps)', 2),
                           self.check('tags', {'test': 'foo'})
                       ]).get_output_in_json()
        second_kid = key['key']['kid']
        pure_kid = '/'.join(second_kid.split('/')[:-1])  # Remove version field
        self.kwargs['kid'] = second_kid
        self.kwargs['pkid'] = pure_kid

        # list key versions
        self.cmd('keyvault key list-versions --vault-name {kv} -n {key}',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault key list-versions --vault-name {kv} -n {key} --maxresults 10',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault key list-versions --vault-name {kv} -n {key} --maxresults 1',
                 checks=self.check('length(@)', 1))
        self.cmd('keyvault key list-versions --id {kid}', checks=self.check('length(@)', 2))
        self.cmd('keyvault key list-versions --id {pkid}', checks=self.check('length(@)', 2))

        # show key (latest)
        self.cmd('keyvault key show --vault-name {kv} -n {key}',
                 checks=self.check('key.kid', second_kid))

        # show key (specific version)
        self.kwargs.update({
            'version1': first_version,
            'kid1': first_kid,
            'kid2': second_kid
        })
        self.cmd('keyvault key show --vault-name {kv} -n {key} -v {version1}',
                 checks=self.check('key.kid', '{kid1}'))

        # show key (by id)
        self.cmd('keyvault key show --id {kid1}', checks=self.check('key.kid', '{kid1}'))

        # set key attributes
        self.cmd('keyvault key set-attributes --vault-name {kv} -n {key} --enabled true', checks=[
            self.check('key.kid', '{kid2}'),
            self.check('attributes.enabled', True)
        ])

        # backup and then delete key
        self.kwargs['key_file'] = os.path.join(tempfile.mkdtemp(), 'backup.key')
        self.cmd('keyvault key backup --vault-name {kv} -n {key} --file "{key_file}"')
        self.cmd('keyvault key delete --vault-name {kv} -n {key}')
        time.sleep(120)
        self.cmd('keyvault key purge --vault-name {kv} -n {key}')
        time.sleep(120)
        self.cmd('keyvault key delete --vault-name {kv} -n {key2}')
        self.cmd('keyvault key list --vault-name {kv}', checks=self.is_empty())
        self.cmd('keyvault key list --vault-name {kv} --maxresults 10', checks=self.is_empty())

        # restore key from backup
        self.cmd('keyvault key restore --vault-name {kv} --file "{key_file}"')
        self.cmd('keyvault key list-versions --vault-name {kv} -n {key}',
                 checks=[
                     self.check('length(@)', 2),
                     self.exists('[0].name'),
                     self.exists('[1].name')
                 ])
        self.cmd('keyvault key list-versions --vault-name {kv} -n {key} --maxresults 10',
                 checks=self.check('length(@)', 2))
        if os.path.isfile(self.kwargs['key_file']):
            os.remove(self.kwargs['key_file'])

        # import PEM from file
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem'),
            'key_enc_password': 'password',
            'key_plain_file': os.path.join(TEST_DIR, 'mydomain.test.pem')
        })
        self.cmd('keyvault key import --vault-name {kv} -n import-key-plain --pem-file "{key_plain_file}" -p software')
        self.cmd('keyvault key import --vault-name {kv} -n import-key-encrypted --pem-file "{key_enc_file}" '
                 '--pem-password {key_enc_password} -p hsm')

        # import PEM from string
        with open(os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem'), 'rb') as f:
            key_enc_string = f.read().decode('UTF-8')
        with open(os.path.join(TEST_DIR, 'mydomain.test.pem'), 'rb') as f:
            key_plain_string = f.read().decode('UTF-8')
        self.kwargs.update({
            'key_enc_string': key_enc_string,
            'key_enc_password': 'password',
            'key_plain_string': key_plain_string
        })
        self.cmd("keyvault key import --vault-name {kv} -n import-key-plain --pem-string '{key_plain_string}' -p software")
        self.cmd('keyvault key import --vault-name {kv} -n import-key-encrypted --pem-string "{key_enc_string}" --pem-password {key_enc_password} -p hsm')

        # create ec keys
        self.cmd('keyvault key create --vault-name {kv} -n eckey1 --kty EC',
                 checks=self.check('key.kty', 'EC'))
        self.cmd('keyvault key create --vault-name {kv} -n eckey1 --curve P-256',
                 checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-256')])
        self.cmd('keyvault key delete --vault-name {kv} -n eckey1')

        # import ec PEM
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'ec521pw.pem'),
            'key_enc_password': 'pass1234',
            'key_plain_file': os.path.join(TEST_DIR, 'ec256.pem')
        })
        self.cmd('keyvault key import --vault-name {kv} -n import-eckey-plain --pem-file "{key_plain_file}" '
                 '-p software', checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-256')])
        self.cmd('keyvault key import --vault-name {kv} -n import-eckey-encrypted --pem-file "{key_enc_file}" '
                 '--pem-password {key_enc_password}',
                 checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-521')])

        # create KEK
        self.cmd('keyvault key create --vault-name {kv2} --name key1 --kty RSA-HSM --size 2048 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
        self.cmd('keyvault key create --vault-name {kv2} --name key2 --kty RSA-HSM --size 3072 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
        self.cmd('keyvault key create --vault-name {kv2} --name key2 --kty RSA-HSM --size 4096 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_key')
    @KeyVaultPreparer(name_prefix='cli-test-kv-key-', location='eastus2')
    def test_keyvault_key_rotation(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'eastus2',
            'key': self.create_random_name('key-', 24),
            'policy': os.path.join(TEST_DIR, 'rotation_policy.json')
        })
        keyvault = self.cmd('keyvault show -n {kv} -g {rg}').get_output_in_json()
        self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        key_perms = keyvault['properties']['accessPolicies'][0]['permissions']['keys']
        key_perms.extend(['rotate'])
        self.kwargs['key_perms'] = ' '.join(key_perms)
        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms}')

        # create a key
        key = self.cmd('keyvault key create --vault-name {kv} -n {key} -p software',
                       checks=self.check('attributes.enabled', True)).get_output_in_json()

        # update rotation-policy
        self.cmd('keyvault key rotation-policy update --value "{policy}" --vault-name {kv} -n {key}',
                 checks=[self.check('expiresIn', 'P30D'),
                         self.check('length(lifetimeActions)', 2),
                         self.check('lifetimeActions[0].action', 'Rotate'),
                         self.check('lifetimeActions[0].timeAfterCreate', 'P15D'),
                         self.check('lifetimeActions[1].action', 'Notify'),
                         self.check('lifetimeActions[1].timeBeforeExpiry', 'P7D')])

        # show rotation-policy
        self.cmd('keyvault key rotation-policy show --vault-name {kv} -n {key}',
                 checks=[self.check('expiresIn', 'P30D'),
                         self.check('length(lifetimeActions)', 2),
                         self.check('lifetimeActions[0].action', 'Rotate'),
                         self.check('lifetimeActions[0].timeAfterCreate', 'P15D'),
                         self.check('lifetimeActions[1].action', 'Notify'),
                         self.check('lifetimeActions[1].timeBeforeExpiry', 'P7D')])

        # rotate key
        self.cmd('keyvault key rotate --vault-name {kv} -n {key}')


class KeyVaultHSMKeyUsingHSMNameScenarioTest(ScenarioTest):
    # @record_only()
    @unittest.skip('cannot run')
    def test_keyvault_hsm_key_using_hsm_name(self):
        self.kwargs.update({
            'hsm_name': ACTIVE_HSM_NAME,
            'hsm_url': ACTIVE_HSM_URL,
            'key': self.create_random_name('key2-', 24)
        })

        _clear_hsm(self, hsm_url=self.kwargs['hsm_url'])

        # create a key
        hsm_key = self.cmd('keyvault key create --hsm-name {hsm_name} -n {key}',
                           checks=self.check('attributes.enabled', True)).get_output_in_json()
        self.kwargs['hsm_kid1'] = hsm_key['key']['kid']
        self.kwargs['hsm_version1'] = self.kwargs['hsm_kid1'].rsplit('/', 1)[1]

        # encrypt/decrypt
        self.kwargs['plaintext_value'] = 'abcdef'
        self.kwargs['base64_value'] = 'YWJjZGVm'
        self.kwargs['encryption_result1'] = \
            self.cmd('keyvault key encrypt -n {key} --hsm-name {hsm_name} -a RSA-OAEP --value "{plaintext_value}" '
                     '--data-type plaintext').get_output_in_json()['result']
        self.kwargs['encryption_result2'] = \
            self.cmd('keyvault key encrypt -n {key} --hsm-name {hsm_name} -a RSA-OAEP --value "{base64_value}" '
                     '--data-type base64').get_output_in_json()['result']
        self.cmd('keyvault key decrypt -n {key} --hsm-name {hsm_name} -a RSA-OAEP --value "{encryption_result1}" '
                 '--data-type plaintext', checks=self.check('result', '{plaintext_value}'))
        self.cmd('keyvault key decrypt -n {key} --hsm-name {hsm_name} -a RSA-OAEP --value "{encryption_result2}" '
                 '--data-type base64', checks=self.check('result', '{base64_value}'))

        # delete/recover
        deleted_key = self.cmd('keyvault key delete --hsm-name {hsm_name} -n {key}',
                               checks=self.check('key.kid', '{hsm_kid1}')).get_output_in_json()
        self.kwargs['hsm_recovery_id'] = deleted_key['recoveryId']
        self.cmd('keyvault key list-deleted --hsm-name {hsm_name}', checks=self.check('length(@)', 1))
        self.cmd('keyvault key recover --hsm-name {hsm_name} -n {key}',
                 checks=self.check('key.kid', '{hsm_kid1}'))

        # list keys
        self.cmd('keyvault key list --hsm-name {hsm_name}',
                 checks=self.check('length(@)', 1))
        self.cmd('keyvault key list --hsm-name {hsm_name} --maxresults 10',
                 checks=self.check('length(@)', 1))

        # create a new key version
        hsm_key = self.cmd('keyvault key create --hsm-name {hsm_name} -n {key} --disabled --ops encrypt decrypt '
                           '--kty RSA-HSM',
                           checks=[
                               self.check('attributes.enabled', False),
                               self.check('length(key.keyOps)', 2)
                           ]).get_output_in_json()
        hsm_second_kid = hsm_key['key']['kid']
        hsm_pure_kid = '/'.join(hsm_second_kid.split('/')[:-1])  # Remove version field
        self.kwargs['hsm_kid'] = hsm_second_kid
        self.kwargs['hsm_pkid'] = hsm_pure_kid

        # list key versions
        self.cmd('keyvault key list-versions --hsm-name {hsm_name} -n {key}',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault key list-versions --hsm-name {hsm_name} -n {key} --maxresults 10',
                 checks=self.check('length(@)', 2))

        # show key (latest)
        self.cmd('keyvault key show --hsm-name {hsm_name} -n {key}',
                 checks=self.check('key.kid', hsm_second_kid))

        # show key (specific version)
        self.kwargs['hsm_kid2'] = hsm_second_kid
        self.cmd('keyvault key show --hsm-name {hsm_name} -n {key} -v {hsm_version1}',
                 checks=self.check('key.kid', '{hsm_kid1}'))

        # show key (by id)
        self.cmd('keyvault key show --id {hsm_kid1}', checks=self.check('key.kid', '{hsm_kid1}'))

        # set key attributes
        self.cmd('keyvault key set-attributes --hsm-name {hsm_name} -n {key} --enabled true', checks=[
            self.check('key.kid', '{hsm_kid2}'),
            self.check('attributes.enabled', True)
        ])

        # backup and then delete key
        self.kwargs['key_file'] = os.path.join(tempfile.mkdtemp(), 'backup-hsm.key')
        self.cmd('keyvault key backup --hsm-name {hsm_name} -n {key} --file "{key_file}"')
        self.cmd('keyvault key delete --hsm-name {hsm_name} -n {key}')
        self.cmd('keyvault key purge --hsm-name {hsm_name} -n {key}')
        self.cmd('keyvault key list --hsm-name {hsm_name}', checks=self.is_empty())
        self.cmd('keyvault key list --hsm-name {hsm_name} --maxresults 10', checks=self.is_empty())

        # restore key from backup
        self.cmd('keyvault key restore --hsm-name {hsm_name} --file "{key_file}"')
        self.cmd('keyvault key list --hsm-name {hsm_name}',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('[0].name', '{key}')
                 ])
        if os.path.exists(self.kwargs['key_file']):
            os.remove(self.kwargs['key_file'])

        # import PEM
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem'),
            'key_enc_password': 'password',
            'key_plain_file': os.path.join(TEST_DIR, 'mydomain.test.pem')
        })
        self.cmd('keyvault key import --hsm-name {hsm_name} -n import-key-plain --pem-file "{key_plain_file}" -p hsm',
                 checks=self.check('key.kty', 'RSA-HSM'))
        self.cmd('keyvault key import --hsm-name {hsm_name} -n import-key-encrypted --pem-file "{key_enc_file}" '
                 '--pem-password {key_enc_password} -p hsm', checks=self.check('key.kty', 'RSA-HSM'))

        # import ec PEM
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'ec521pw.pem'),
            'key_enc_password': 'pass1234',
            'key_plain_file': os.path.join(TEST_DIR, 'ec256.pem')
        })
        self.cmd('keyvault key import --hsm-name {hsm_name} -n import-eckey-plain --pem-file "{key_plain_file}" '
                 '-p hsm', checks=[self.check('key.kty', 'EC-HSM'), self.check('key.crv', 'P-256')])
        """ Enable this when service is ready
        self.cmd('keyvault key import --hsm-name {hsm_name} -n import-eckey-encrypted --pem-file "{key_enc_file}" '
                 '--pem-password {key_enc_password}',
                 checks=[self.check('key.kty', 'EC-HSM'), self.check('key.crv', 'P-521')])
        """

        # create ec keys
        self.cmd('keyvault key create --hsm-name {hsm_name} -n eckey1 --kty EC-HSM',
                 checks=self.check('key.kty', 'EC-HSM'))
        self.cmd('keyvault key create --hsm-name {hsm_name} -n eckey1 --kty EC-HSM --curve P-256',
                 checks=[self.check('key.kty', 'EC-HSM'), self.check('key.crv', 'P-256')])
        self.cmd('keyvault key delete --hsm-name {hsm_name} -n eckey1')

        # create KEK
        self.cmd('keyvault key create --hsm-name {hsm_name} -n key1 --kty RSA-HSM --size 2048 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
        self.cmd('keyvault key create --hsm-name {hsm_name} -n key2 --kty RSA-HSM --size 3072 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
        self.cmd('keyvault key create --hsm-name {hsm_name} -n key2 --kty RSA-HSM --size 4096 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])

    # Since the MHSM has to be activated manually so we use fixed hsm resource and mark the test as record_only
    @record_only()
    def test_keyvault_hsm_key_random(self):
        self.kwargs.update({
            'hsm_name': TEST_HSM_NAME,
            'hsm_url': TEST_HSM_URL
        })

        result = self.cmd('keyvault key random --count 4 --hsm-name {hsm_name}').get_output_in_json()
        self.assertIsNotNone(result['value'])

        result = self.cmd('keyvault key random --count 1 --id {hsm_url}').get_output_in_json()
        self.assertIsNotNone(result['value'])

    # Since the MHSM has to be activated manually so we use fixed hsm resource and mark the test as record_only
    @record_only()
    def test_keyvault_hsm_key_encrypt_AES(self):
        self.kwargs.update({
            'hsm_name': TEST_HSM_NAME,
            'hsm_url': TEST_HSM_URL,
            'key': self.create_random_name('oct256key-', 24)
        })

        self.cmd('keyvault key create --kty oct-HSM --size 256 -n {key} --hsm-name {hsm_name} --ops encrypt decrypt')

        self.kwargs['plaintext_value'] = 'this is plaintext'
        self.kwargs['base64_value'] = 'dGhpcyBpcyBwbGFpbnRleHQ='
        self.kwargs['aad'] = '101112131415161718191a1b1c1d1e1f'
        encryption_result1 = self.cmd('keyvault key encrypt -n {key} --hsm-name {hsm_name} -a A256GCM --value "{plaintext_value}" --data-type plaintext --aad {aad}').get_output_in_json()
        encryption_result2 = self.cmd('keyvault key encrypt -n {key} --hsm-name {hsm_name} -a A256GCM --value "{base64_value}" --data-type base64 --aad {aad}').get_output_in_json()
        self.cmd('keyvault key decrypt -n {} --hsm-name {} -a A256GCM --value "{}" --data-type plaintext --iv {} --tag {} --aad {}'
                 .format(self.kwargs['key'], self.kwargs['hsm_name'], encryption_result1['result'], encryption_result1['iv'], encryption_result1['tag'], encryption_result1['aad']),
                 checks=self.check('result', '{plaintext_value}'))
        self.cmd('keyvault key decrypt -n {} --hsm-name {} -a A256GCM --value "{}" --data-type base64 --iv {} --tag {} --aad {}'
                 .format(self.kwargs['key'], self.kwargs['hsm_name'], encryption_result2['result'], encryption_result2['iv'], encryption_result2['tag'], encryption_result2['aad']),
                 checks=self.check('result', '{base64_value}'))

        self.cmd('keyvault key delete -n {key} --hsm-name {hsm_name}')
        self.cmd('keyvault key purge -n {key} --hsm-name {hsm_name}')

    # Since the MHSM has to be activated manually so we use fixed hsm resource and mark the test as record_only
    @record_only()
    def test_keyvault_hsm_key_release_policy(self):
        self.kwargs.update({
            'hsm_name': TEST_HSM_NAME,
            'hsm_url': TEST_HSM_URL,
            'key1': self.create_random_name('skr1-', 24),
            'key2': self.create_random_name('skr2-', 24),
            'policy': os.path.join(TEST_DIR, 'release_policy.json').replace('\\', '\\\\')
        })
        # test create with policy file
        key1 = self.cmd('keyvault key create --kty EC-HSM -n {key1} --exportable --policy {policy} --hsm-name {hsm_name}').get_output_in_json()
        self.assertIn('x-ms-sgx-is-debuggable', key1['releasePolicy']['encodedPolicy'])
        self.assertEqual(key1['releasePolicy']['immutable'], False)
        # test create with default policy
        key2 = self.cmd('keyvault key create --kty EC-HSM -n {key2} --exportable  --default-cvm-policy --hsm-name {hsm_name}').get_output_in_json()
        self.assertIn('x-ms-attestation-type', key2['releasePolicy']['encodedPolicy'])
        self.assertEqual(key2['releasePolicy']['immutable'], False)
        # test update with immutability
        result = self.cmd('keyvault key set-attributes --policy {policy} --immutable -n {key2} --hsm-name {hsm_name}').get_output_in_json()
        self.assertIn('x-ms-sgx-is-debuggable', result['releasePolicy']['encodedPolicy'])
        self.assertEqual(result['releasePolicy']['immutable'], True)

        # clear test resources
        self.cmd('keyvault key delete -n {key1} --hsm-name {hsm_name}')
        self.cmd('keyvault key purge -n {key1} --hsm-name {hsm_name}')
        self.cmd('keyvault key delete -n {key2} --hsm-name {hsm_name}')
        self.cmd('keyvault key purge -n {key2} --hsm-name {hsm_name}')


class KeyVaultHSMKeyUsingHSMURLScenarioTest(ScenarioTest):
    # @record_only()
    @unittest.skip('cannot run')
    def test_keyvault_hsm_key_using_hsm_url(self):
        self.kwargs.update({
            'hsm_name': ACTIVE_HSM_NAME,
            'hsm_url': ACTIVE_HSM_URL,
            'key': self.create_random_name('key-', 24)
        })

        _clear_hsm(self, hsm_url=self.kwargs['hsm_url'])

        # test exception
        with self.assertRaises(CLIError):
            self.cmd('keyvault key create --vault-name {hsm_name} --id {hsm_url} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key create --hsm-name {hsm_name} --id {hsm_url} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key create --vault-name {hsm_name} --hsm-name {hsm_name} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key delete --vault-name {hsm_name} --hsm-name {hsm_name} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key download --vault-name {hsm_name} --hsm-name {hsm_name} -n {key} -f test.key')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key list --vault-name {hsm_name} --hsm-name {hsm_name}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key list-deleted --vault-name {hsm_name} --hsm-name {hsm_name}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key list-versions --vault-name {hsm_name} --hsm-name {hsm_name} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key purge --vault-name {hsm_name} --hsm-name {hsm_name} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key set-attributes --vault-name {hsm_name} --hsm-name {hsm_name} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key show --vault-name {hsm_name} --hsm-name {hsm_name} -n {key}')
        with self.assertRaises(CLIError):
            self.cmd('keyvault key show-deleted --vault-name {hsm_name} --hsm-name {hsm_name} -n {key}')

        # create a key
        hsm_key = self.cmd('keyvault key create --id {hsm_url}/keys/{key} -p hsm',
                           checks=self.check('attributes.enabled', True)).get_output_in_json()
        self.kwargs['hsm_kid1'] = hsm_key['key']['kid']
        self.kwargs['hsm_version1'] = self.kwargs['hsm_kid1'].rsplit('/', 1)[1]

        # encrypt/decrypt
        self.kwargs['plaintext_value'] = 'abcdef'
        self.kwargs['base64_value'] = 'YWJjZGVm'
        self.kwargs['encryption_result1'] = \
            self.cmd('keyvault key encrypt --id {hsm_url}/keys/{key} -a RSA-OAEP --value "{plaintext_value}" '
                     '--data-type plaintext').get_output_in_json()['result']
        self.kwargs['encryption_result2'] = \
            self.cmd('keyvault key encrypt --id {hsm_url}/keys/{key} -a RSA-OAEP --value "{base64_value}" '
                     '--data-type base64').get_output_in_json()['result']
        self.cmd('keyvault key decrypt --id {hsm_url}/keys/{key} -a RSA-OAEP --value "{encryption_result1}" '
                 '--data-type plaintext', checks=self.check('result', '{plaintext_value}'))
        self.cmd('keyvault key decrypt --id {hsm_url}/keys/{key} -a RSA-OAEP --value "{encryption_result2}" '
                 '--data-type base64', checks=self.check('result', '{base64_value}'))

        # delete/recover
        deleted_key = self.cmd('keyvault key delete --id {hsm_kid1}',
                               checks=self.check('key.kid', '{hsm_kid1}')).get_output_in_json()
        self.kwargs['hsm_recovery_id'] = deleted_key['recoveryId']
        self.cmd('keyvault key list-deleted --id {hsm_url}', checks=self.check('length(@)', 1))
        self.cmd('keyvault key recover --id {hsm_recovery_id}',
                 checks=self.check('key.kid', '{hsm_kid1}'))

        # list keys
        self.cmd('keyvault key list --id {hsm_url}',
                 checks=self.check('length(@)', 1))
        self.cmd('keyvault key list --id {hsm_url} --maxresults 10',
                 checks=self.check('length(@)', 1))

        # create a new key version
        hsm_key = self.cmd('keyvault key create --id {hsm_url}/keys/{key} -p hsm --disabled --ops encrypt decrypt '
                           '--kty RSA-HSM',
                           checks=[
                               self.check('attributes.enabled', False),
                               self.check('length(key.keyOps)', 2)
                           ]).get_output_in_json()
        hsm_second_kid = hsm_key['key']['kid']
        hsm_pure_kid = '/'.join(hsm_second_kid.split('/')[:-1])  # Remove version field
        self.kwargs['hsm_kid'] = hsm_second_kid
        self.kwargs['hsm_pkid'] = hsm_pure_kid

        # list key versions
        self.cmd('keyvault key list-versions --id {hsm_url}/keys/{key}',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault key list-versions --id {hsm_url}/keys/{key} --maxresults 10',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault key list-versions --id {hsm_kid}', checks=self.check('length(@)', 2))
        self.cmd('keyvault key list-versions --id {hsm_pkid}', checks=self.check('length(@)', 2))

        # show key (latest)
        self.cmd('keyvault key show --id {hsm_url}/keys/{key}',
                 checks=self.check('key.kid', hsm_second_kid))

        # show key (specific version)
        self.kwargs['hsm_kid2'] = hsm_second_kid
        self.cmd('keyvault key show --id {hsm_url}/keys/{key} -v {hsm_version1}',
                 checks=self.check('key.kid', '{hsm_kid1}'))

        # show key (by id)
        self.cmd('keyvault key show --id {hsm_kid1}', checks=self.check('key.kid', '{hsm_kid1}'))

        # set key attributes
        self.cmd('keyvault key set-attributes --id {hsm_url}/keys/{key} --enabled true', checks=[
            self.check('key.kid', '{hsm_kid2}'),
            self.check('attributes.enabled', True)
        ])

        # backup and then delete key
        self.kwargs['key_file'] = os.path.join(tempfile.mkdtemp(), 'backup-hsm.key')
        self.cmd('keyvault key backup --id {hsm_url}/keys/{key} --file "{key_file}"')
        self.cmd('keyvault key delete --id {hsm_url}/keys/{key}')
        self.cmd('keyvault key purge --id {hsm_url}/deletedkeys/{key}')
        self.cmd('keyvault key list --id {hsm_url}', checks=self.is_empty())
        self.cmd('keyvault key list --id {hsm_url} --maxresults 10', checks=self.is_empty())

        # restore key from backup
        self.cmd('keyvault key restore --id {hsm_url} --file "{key_file}"')
        self.cmd('keyvault key list --id {hsm_url}',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('[0].name', '{key}')
                 ])
        if os.path.isfile(self.kwargs['key_file']):
            os.remove(self.kwargs['key_file'])

        # import PEM
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem'),
            'key_enc_password': 'password',
            'key_plain_file': os.path.join(TEST_DIR, 'mydomain.test.pem')
        })
        self.cmd('keyvault key import --id {hsm_url}/keys/import-key-plain --pem-file "{key_plain_file}" -p hsm',
                 checks=self.check('key.kty', 'RSA-HSM'))
        self.cmd('keyvault key import --id {hsm_url}/keys/import-key-encrypted --pem-file "{key_enc_file}" '
                 '--pem-password {key_enc_password} -p hsm', checks=self.check('key.kty', 'RSA-HSM'))

        # import ec PEM
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'ec521pw.pem'),
            'key_enc_password': 'pass1234',
            'key_plain_file': os.path.join(TEST_DIR, 'ec256.pem')
        })
        self.cmd('keyvault key import --id {hsm_url}/keys/import-eckey-plain --pem-file "{key_plain_file}" '
                 '-p hsm', checks=[self.check('key.kty', 'EC-HSM'), self.check('key.crv', 'P-256')])
        """ Enable this when service is ready
        self.cmd('keyvault key import --id {hsm_url}/keys/import-eckey-encrypted --pem-file "{key_enc_file}" '
                 '--pem-password {key_enc_password}',
                 checks=[self.check('key.kty', 'EC-HSM'), self.check('key.crv', 'P-521')])
        """

        # create ec keys
        self.cmd('keyvault key create --id {hsm_url}/keys/eckey1 --kty EC-HSM',
                 checks=self.check('key.kty', 'EC-HSM'))
        self.cmd('keyvault key create --id {hsm_url}/keys/eckey1 --kty EC-HSM --curve P-256',
                 checks=[self.check('key.kty', 'EC-HSM'), self.check('key.crv', 'P-256')])
        self.cmd('keyvault key delete --id {hsm_url}/keys/eckey1')

        # create KEK
        self.cmd('keyvault key create --id {hsm_url}/keys/key1 --kty RSA-HSM --size 2048 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
        self.cmd('keyvault key create --id {hsm_url}/keys/key2 --kty RSA-HSM --size 3072 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
        self.cmd('keyvault key create --id {hsm_url}/keys/key2 --kty RSA-HSM --size 4096 --ops import',
                 checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])


class KeyVaultKeyDownloadScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_kv_key_download')
    @KeyVaultPreparer(name_prefix='cli-test-kv-key-d-', location='eastus2')
    def test_keyvault_key_download(self, resource_group, key_vault):
        import OpenSSL.crypto

        self.kwargs.update({
            'loc': 'eastus2'
        })

        key_names = [
            'ec-p256.pem',
            'ec-p384.pem',
            'ec-p521.pem',
            'ec-p256k.pem',
            'rsa-2048.pem',
            'rsa-3072.pem',
            'rsa-4096.pem'
        ]

        # RSA Keys
        # * Generate: `openssl genrsa -out rsa-4096.pem 4096`
        # * Extract public key: `openssl rsa -in rsa-4096.pem -pubout > rsa-4096.pub.pem`
        # * Public key PEM to DER: `openssl rsa -pubin -inform PEM -in rsa-4096.pub.pem -outform DER -out rsa-4096.pub.der`

        # EC Keys
        # * Generate: `openssl ecparam -genkey -name secp521r1 -out ec521.key`
        # * Extract public key (PEM): `openssl ec -in ec-p521.pem -pubout -out ec-p521.pub.pem`
        # * Extract public key (DER): `openssl ec -in ec-p521.pem -pubout -outform DER -out ec-p521.pub.der`

        for key_name in key_names:
            var_name = key_name.split('.')[0] + '-file'
            self.kwargs[var_name] = os.path.join(KEYS_DIR, key_name)
            self.cmd('keyvault key import --vault-name {{kv}} -n {var_name} --pem-file "{{{var_name}}}"'
                     .format(var_name=var_name))

            der_downloaded_filename = var_name + '.der'
            pem_downloaded_filename = var_name + '.pem'

            try:
                self.cmd('keyvault key download --vault-name {{kv}} -n {var_name} -f "{filename}" -e DER'
                         .format(var_name=var_name, filename=der_downloaded_filename))
                self.cmd('keyvault key download --vault-name {{kv}} -n {var_name} -f "{filename}" -e PEM'
                         .format(var_name=var_name, filename=pem_downloaded_filename))

                expected_pem = []
                pem_pub_filename = os.path.join(KEYS_DIR, key_name.split('.')[0] + '.pub.pem')
                with open(pem_pub_filename, 'r') as pem_file:
                    expected_pem = pem_file.readlines()
                expected_pem = ''.join(expected_pem).replace('\n', '')

                def verify(path, file_type):
                    with open(path, 'rb') as f:
                        pub_key = OpenSSL.crypto.load_publickey(file_type, f.read())
                        actual_pem = OpenSSL.crypto.dump_publickey(OpenSSL.crypto.FILETYPE_PEM, pub_key)
                        if isinstance(actual_pem, bytes):
                            actual_pem = actual_pem.decode("utf-8")
                        self.assertIn(expected_pem, actual_pem.replace('\n', ''))

                    verify(der_downloaded_filename, OpenSSL.crypto.FILETYPE_ASN1)
                    verify(pem_downloaded_filename, OpenSSL.crypto.FILETYPE_PEM)
            finally:
                if os.path.exists(der_downloaded_filename):
                    os.remove(der_downloaded_filename)
                if os.path.exists(pem_downloaded_filename):
                    os.remove(pem_downloaded_filename)


class KeyVaultHSMKeyDownloadScenarioTest(ScenarioTest):
    # @record_only()
    @unittest.skip('cannot run')
    def test_keyvault_hsm_key_download(self):
        self.kwargs.update({
            'hsm_url': ACTIVE_HSM_URL,
            'hsm_name': ACTIVE_HSM_NAME
        })

        key_names = [
            'ec-p256-hsm.pem',
            'ec-p384-hsm.pem',
            'rsa-2048-hsm.pem',
            'rsa-3072-hsm.pem',
            'rsa-4096-hsm.pem'
        ]

        _clear_hsm(self, hsm_url=self.kwargs['hsm_url'])

        for key_name in key_names:
            var_name = key_name.split('.')[0] + '-file'
            if key_name.startswith('rsa'):
                rsa_size = key_name.split('-')[1]
                self.cmd('keyvault key create --hsm-name {{hsm_name}} -n {var_name}'
                         ' -p hsm --kty RSA-HSM --size {rsa_size}'.format(var_name=var_name, rsa_size=rsa_size))
            elif key_name.startswith('ec'):
                ec_curve = key_name.split('-')[1]
                curve_names = {
                    'p256': 'P-256',
                    'p384': 'P-384'
                }
                self.cmd('keyvault key create --id {{hsm_url}}/keys/{var_name}'
                         ' -p hsm --kty EC-HSM --curve {curve_name}'
                         .format(var_name=var_name, curve_name=curve_names[ec_curve]))

            der_downloaded_filename = var_name + '.der'
            pem_downloaded_filename = var_name + '.pem'

            try:
                self.cmd('keyvault key download --id {{hsm_url}}/keys/{var_name} -f "{filename}" -e DER'
                         .format(var_name=var_name, filename=der_downloaded_filename))
                self.cmd('keyvault key download --hsm-name {{hsm_name}} -n {var_name} -f "{filename}" -e PEM'
                         .format(var_name=var_name, filename=pem_downloaded_filename))
            finally:
                if os.path.exists(der_downloaded_filename):
                    os.remove(der_downloaded_filename)
                if os.path.exists(pem_downloaded_filename):
                    os.remove(pem_downloaded_filename)


class KeyVaultSecretSoftDeleteScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_secret_soft_delete')
    @KeyVaultPreparer(name_prefix='cli-test-kv-se-sd-', location='eastus')
    def test_keyvault_secret_soft_delete(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'eastus',
            'sec': 'secret1'
        })
        self.cmd('keyvault show -n {kv}', checks=self.check('properties.enableSoftDelete', True))

        max_timeout = 100
        time_counter = 0
        while time_counter <= max_timeout:
            try:
                # show deleted
                self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value ABC123',
                         checks=self.check('value', 'ABC123'))
                data = self.cmd('keyvault secret delete --vault-name {kv} -n {sec}').get_output_in_json()
                self.kwargs['secret_id'] = data['id']
                self.kwargs['secret_recovery_id'] = data['recoveryId']
                self.cmd('keyvault secret list-deleted --vault-name {kv}', checks=self.check('length(@)', 1))
                self.cmd('keyvault secret list-deleted --vault-name {kv} --maxresults 10',
                         checks=self.check('length(@)', 1))
                self.cmd('keyvault secret show-deleted --id {secret_recovery_id}',
                         checks=self.check('id', '{secret_id}'))
                self.cmd('keyvault secret show-deleted --vault-name {kv} -n {sec}',
                         checks=self.check('id', '{secret_id}'))
            except:  # pylint: disable=bare-except
                time.sleep(10)
                time_counter += 10
            else:
                break


class KeyVaultSecretScenarioTest(ScenarioTest):
    def _test_download_secret(self):
        secret_path = os.path.join(TEST_DIR, 'test_secret.txt')
        self.kwargs['src_path'] = secret_path
        with open(secret_path, 'r') as f:
            expected = f.read().replace('\r\n', '\n')

        def _test_set_and_download(encoding):
            self.kwargs['enc'] = encoding
            self.cmd('keyvault secret set --vault-name {kv} -n download-{enc} --file "{src_path}" --encoding {enc}')
            dest_path = os.path.join(TEST_DIR, 'recover-{}'.format(encoding))
            self.kwargs['dest_path'] = dest_path
            self.cmd('keyvault secret download --vault-name {kv} -n download-{enc} --file "{dest_path}"')
            with open(dest_path, 'r') as f:
                actual = f.read().replace('\r\n', '\n')
            self.assertEqual(actual, expected)
            os.remove(dest_path)

        for encoding in secret_encoding_values:
            _test_set_and_download(encoding)

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_secret')
    @KeyVaultPreparer(name_prefix='cli-test-kv-se-')
    def test_keyvault_secret(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'westus',
            'sec': 'secret1',
            'sec2': 'secret2'
        })
        keyvault = self.cmd('keyvault show -n {kv} -g {rg}').get_output_in_json()
        self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        secret_perms = keyvault['properties']['accessPolicies'][0]['permissions']['secrets']
        secret_perms.append('purge')
        self.kwargs['secret_perms'] = ' '.join(secret_perms)
        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --secret-permissions {secret_perms}')

        # create a secret
        secret = self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value ABC123',
                          checks=self.check('value', 'ABC123')).get_output_in_json()
        first_sid = secret['id']
        first_sname = first_sid.split('/')[4]
        first_version = first_sid.rsplit('/', 1)[1]
        self.kwargs.update({
            'sid1': first_sid,
            'ver1': first_version
        })
        self.cmd('keyvault secret set --vault-name {kv} -n {sec2} --value 123456', checks=self.check('value', '123456'))

        # list secrets
        self.cmd('keyvault secret list --vault-name {kv}',
                 checks=[
                     self.check('length(@)', 2),
                     self.check('[0].name', first_sname)
                 ])
        self.cmd('keyvault secret list --vault-name {kv} --maxresults 10', checks=self.check('length(@)', 2))
        self.cmd('keyvault secret list --vault-name {kv} --maxresults 1', checks=self.check('length(@)', 1))

        # create a new secret version
        secret = self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value DEF456 --tags test=foo --description "test type"', checks=[
            self.check('value', 'DEF456'),
            self.check('tags', {'file-encoding': 'utf-8', 'test': 'foo'}),
            self.check('contentType', 'test type'),
            self.check('name', first_sname)
        ]).get_output_in_json()
        self.kwargs['sid2'] = secret['id']

        # list secret versions
        self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec}',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec} --maxresults 10',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec} --maxresults 1',
                 checks=self.check('length(@)', 1))

        # show secret (latest)
        self.cmd('keyvault secret show --vault-name {kv} -n {sec}',
                 checks=[
                     self.check('id', '{sid2}'),
                     self.check('name', '{sec}')
                 ])

        # show secret (specific version)
        self.cmd('keyvault secret show --vault-name {kv} -n {sec} -v {ver1}',
                 checks=self.check('id', '{sid1}'))

        # show secret (by id)
        self.cmd('keyvault secret show --id {sid1}',
                 checks=self.check('id', '{sid1}'))

        # set secret attributes
        self.cmd('keyvault secret set-attributes --vault-name {kv} -n {sec} --enabled false', checks=[
            self.check('id', '{sid2}'),
            self.check('attributes.enabled', False),
            self.check('name', '{sec}')
        ])

        # backup and then delete secret
        self.kwargs['bak_file'] = os.path.join(tempfile.mkdtemp(), 'backup.secret')
        self.cmd('keyvault secret backup --vault-name {kv} -n {sec} --file "{bak_file}"')
        self.cmd('keyvault secret delete --vault-name {kv} -n {sec}', checks=self.check('name', '{sec}'))
        time.sleep(60)
        self.cmd('keyvault secret purge --vault-name {kv} -n {sec}')
        time.sleep(60)
        self.cmd('keyvault secret delete --vault-name {kv} -n {sec2}', checks=self.check('name', '{sec2}'))
        self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())

        # restore secret from backup
        self.cmd('keyvault secret restore --vault-name {kv} --file "{bak_file}"', checks=self.check('name', '{sec}'))
        self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec}',
                 checks=self.check('length(@)', 2))
        if os.path.isfile(self.kwargs['bak_file']):
            os.remove(self.kwargs['bak_file'])

        # delete secret
        self.cmd('keyvault secret delete --vault-name {kv} -n {sec}')
        self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())
        self.cmd('keyvault secret list --vault-name {kv} --maxresults 10', checks=self.is_empty())

        self._test_download_secret()


class KeyVaultCertificateRestoreScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_soft_delete_')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-sd-')
    def test_keyvault_certificate_soft_delete(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'eastus',
            'policy_path' : os.path.join(TEST_DIR, 'policy.json')
        })
        self.cmd('keyvault show -n {kv}', checks=self.check('properties.enableSoftDelete', True))

        self.cmd('keyvault certificate create --vault-name {kv} -n cert1 -p @"{policy_path}"', checks=[
            self.check('status', 'completed'),
            self.check('name', 'cert1')
        ])
        data = self.cmd('keyvault certificate delete --vault-name {kv} -n cert1').get_output_in_json()
        self.kwargs['cert_id'] = data['id']
        self.kwargs['cert_recovery_id'] = data['recoveryId']

        max_timeout = 100
        time_counter = 0
        while time_counter <= max_timeout:
            try:
                # show deleted
                self.cmd('keyvault certificate list-deleted --vault-name {kv}', checks=self.check('length(@)', 1))
                self.cmd('keyvault certificate list-deleted --vault-name {kv} --maxresults 10',
                         checks=self.check('length(@)', 1))
                self.cmd('keyvault certificate show-deleted --id {secret_recovery_id}',
                         checks=self.check('id', '{secret_id}'))
                self.cmd('keyvault certificate show-deleted --vault-name {kv} -n {sec}',
                         checks=self.check('id', '{secret_id}'))
            except:  # pylint: disable=bare-except
                time.sleep(10)
                time_counter += 10
            else:
                break


class KeyVaultCertificateContactsScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_contacts')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-co-')
    def test_keyvault_certificate_contacts(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'westus'
        })

        self.cmd('keyvault certificate contact add --vault-name {kv} --email admin@contoso.com --name "John Doe" --phone 123-456-7890')
        self.cmd('keyvault certificate contact add --vault-name {kv} --email other@contoso.com ')
        self.cmd('keyvault certificate contact list --vault-name {kv}',
                 checks=self.check('length(contactList)', 2))
        self.cmd('keyvault certificate contact delete --vault-name {kv} --email admin@contoso.com')
        self.cmd('keyvault certificate contact list --vault-name {kv}', checks=[
            self.check('length(contactList)', 1),
            self.check('contactList[0].emailAddress', 'other@contoso.com')
        ])


class KeyVaultCertificateIssuerScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_issuer')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-is-')
    def test_keyvault_certificate_issuers(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'westus'
        })

        self.cmd('keyvault certificate issuer create --vault-name {kv} --issuer-name issuer1 --provider Test', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True)
        ])
        self.cmd('keyvault certificate issuer show --vault-name {kv} --issuer-name issuer1', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True)
        ])
        self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name issuer1 --organization-id TestOrg --account-id test_account', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True),
            self.check('organizationDetails.id', 'TestOrg'),
            self.check('credentials.accountId', 'test_account')
        ])
        with self.assertRaises(CLIError):
            self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name notexist '
                     '--organization-id TestOrg --account-id test_account')
        self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name issuer1 --account-id ""', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True),
            self.check('organizationDetails.id', 'TestOrg'),
            self.check('credentials.accountId', None)
        ])
        self.cmd('keyvault certificate issuer list --vault-name {kv}',
                 checks=self.check('length(@)', 1))

        # test admin commands
        self.cmd('keyvault certificate issuer admin add --vault-name {kv} --issuer-name issuer1 --email test@test.com --first-name Test --last-name Admin --phone 123-456-7890', checks=[
            self.check('emailAddress', 'test@test.com'),
            self.check('firstName', 'Test'),
            self.check('lastName', 'Admin'),
            self.check('phone', '123-456-7890'),
        ])
        self.cmd('keyvault certificate issuer admin add --vault-name {kv} --issuer-name issuer1 --email test2@test.com', checks=[
            self.check('emailAddress', 'test2@test.com'),
            self.check('firstName', None),
            self.check('lastName', None),
            self.check('phone', None),
        ])
        self.cmd('keyvault certificate issuer admin list --vault-name {kv} --issuer-name issuer1',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault certificate issuer admin delete --vault-name {kv} --issuer-name issuer1 --email test@test.com')
        self.cmd('keyvault certificate issuer admin list --vault-name {kv} --issuer-name issuer1',
                 checks=self.check('length(@)', 1))

        self.cmd('keyvault certificate issuer delete --vault-name {kv} --issuer-name issuer1')
        self.cmd('keyvault certificate issuer list --vault-name {kv}', checks=self.is_empty())


class KeyVaultPendingCertificateScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_pending')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-pe-')
    def test_keyvault_pending_certificate(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'westus',
            'policy_path': os.path.join(TEST_DIR, 'policy_pending.json')
        })

        self.kwargs['fake_cert_path'] = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        self.cmd('keyvault certificate create --vault-name {kv} -n pending-cert -p @"{policy_path}"', checks=[
            self.check('statusDetails', 'Pending certificate created. Please Perform Merge to complete the request.'),
            self.check('cancellationRequested', False),
            self.check('status', 'inProgress'),
            self.check('name', 'pending-cert')
        ])
        self.cmd('keyvault certificate pending show --vault-name {kv} -n pending-cert', checks=[
            self.check('statusDetails', 'Pending certificate created. Please Perform Merge to complete the request.'),
            self.check('cancellationRequested', False),
            self.check('status', 'inProgress'),
            self.check('name', 'pending-cert')
        ])

        self.cmd('keyvault certificate list --vault-name {kv} --include-pending', checks=self.check('length(@)', 1))
        self.cmd('keyvault certificate list --vault-name {kv} --include-pending true',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('[0].name', 'pending-cert')
                 ])
        self.cmd('keyvault certificate list --vault-name {kv}', checks=self.check('length(@)', 0))
        self.cmd('keyvault certificate list --vault-name {kv}  --include-pending false', checks=self.check('length(@)', 0))

        # we do not have a way of actually getting a certificate that would pass this test so
        # we simply ensure that the payload successfully serializes and is received by the server
        with self.assertRaises(CLIError):
            self.cmd('keyvault certificate pending merge --vault-name {kv} -n pending-cert --file "{fake_cert_path}"')
        self.cmd('keyvault certificate pending delete --vault-name {kv} -n pending-cert',
                 checks=self.check('name', 'pending-cert'))

        self.cmd('keyvault certificate pending show --vault-name {kv} -n pending-cert', expect_failure=True)


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultCertificateDownloadScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_download')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-dl-', location='eastus2')
    def test_keyvault_certificate_download(self, resource_group, key_vault):
        import OpenSSL.crypto

        self.kwargs.update({
            'loc': 'eastus2'
        })

        pem_file = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        pem_policy_path = os.path.join(TEST_DIR, 'policy_import_pem.json')
        self.kwargs.update({
            'pem_file': pem_file,
            'pem_policy_path': pem_policy_path
        })
        pem_cert = self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert1 --file "{pem_file}" -p @"{pem_policy_path}"').get_output_in_json()
        cert_data = pem_cert['cer']

        dest_binary = os.path.join(TEST_DIR, 'download-binary')
        dest_string = os.path.join(TEST_DIR, 'download-string')
        self.kwargs.update({
            'dest_binary': dest_binary,
            'dest_string': dest_string
        })

        expected_pem = "-----BEGIN CERTIFICATE-----\n" + \
                       cert_data + \
                       '-----END CERTIFICATE-----\n'
        expected_pem = expected_pem.replace('\n', '')

        try:
            self.cmd('keyvault certificate download --vault-name {kv} -n pem-cert1 --file "{dest_binary}" -e DER')
            self.cmd('keyvault certificate download --vault-name {kv} -n pem-cert1 --file "{dest_string}" -e PEM')
            self.cmd('keyvault certificate delete --vault-name {kv} -n pem-cert1')

            def verify(path, file_type):
                with open(path, 'rb') as f:
                    x509 = OpenSSL.crypto.load_certificate(file_type, f.read())
                    actual_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509)
                    if isinstance(actual_pem, bytes):
                        actual_pem = actual_pem.decode("utf-8")
                    self.assertIn(expected_pem, actual_pem.replace('\n', ''))

            verify(dest_binary, OpenSSL.crypto.FILETYPE_ASN1)
            verify(dest_string, OpenSSL.crypto.FILETYPE_PEM)
        finally:
            if os.path.exists(dest_binary):
                os.remove(dest_binary)
            if os.path.exists(dest_string):
                os.remove(dest_string)


class KeyVaultCertificateDefaultPolicyScenarioTest(ScenarioTest):
    def test_keyvault_certificate_get_default_policy(self):
        result = self.cmd('keyvault certificate get-default-policy').get_output_in_json()
        self.assertEqual(result['keyProperties']['keyType'], 'RSA')
        self.assertEqual(result['issuerParameters']['name'], 'Self')
        self.assertEqual(result['secretProperties']['contentType'], 'application/x-pkcs12')
        subject = 'CN=CLIGetDefaultPolicy'
        self.assertEqual(result['x509CertificateProperties']['subject'], subject)

        result = self.cmd('keyvault certificate get-default-policy --scaffold').get_output_in_json()
        self.assertIn('RSA or RSA-HSM', result['keyProperties']['keyType'])
        self.assertIn('Self', result['issuerParameters']['name'])
        self.assertIn('application/x-pkcs12', result['secretProperties']['contentType'])
        self.assertIn('Contoso', result['x509CertificateProperties']['subject'])


class KeyVaultCertificateScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_cert')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-')
    def test_keyvault_certificate_crud(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'westus'
        })

        keyvault = self.cmd('keyvault show -n {kv} -g {rg}').get_output_in_json()
        self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']

        policy_path = os.path.join(TEST_DIR, 'policy.json')
        policy2_path = os.path.join(TEST_DIR, 'policy2.json')
        policy3_path = os.path.join(TEST_DIR, 'policy3.json')
        cert_secret_path = os.path.join(TEST_DIR, 'cert_secret.der')
        self.kwargs.update({
            'policy_path': policy_path,
            'policy2_path': policy2_path,
            'policy3_path': policy3_path,
            'cert_secret_path': cert_secret_path
        })

        # create certificates
        self.cmd('keyvault certificate create --vault-name {kv} -n cert1 -p @"{policy_path}"',
                 checks=[
                     self.check('status', 'completed'),
                     self.check('name', 'cert1')
                 ])
        self.cmd('keyvault certificate create --vault-name {kv} -n cert2 -p @"{policy_path}"',
                 checks=[
                     self.check('status', 'completed'),
                     self.check('name', 'cert2')
                 ])

        # import with same policy
        policy = self.cmd('keyvault certificate show --vault-name {kv} -n cert2 --query policy').get_output_in_json()
        if not os.path.exists(policy3_path) or self.is_live:
            with open(policy3_path, "w") as f:
                f.write(json.dumps(policy))

        self.cmd('keyvault secret download --vault-name {kv} --file "{cert_secret_path}" -n cert2 --encoding base64')

        self.cmd('keyvault certificate import --vault-name {kv} --file "{cert_secret_path}" -n cert2 -p @"{policy3_path}"',
                 checks=[
                     self.check('name', 'cert2'),
                     self.check('policy.secretProperties.contentType',
                                policy['secretProperties']['contentType'])
                 ])
        self.cmd('keyvault certificate delete --vault-name {kv} -n cert2')
        if os.path.exists(cert_secret_path):
            os.remove(cert_secret_path)

        # list certificates
        self.cmd('keyvault certificate list --vault-name {kv}',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('[0].name', 'cert1')
                 ])
        self.cmd('keyvault certificate list --vault-name {kv} --maxresults 10',
                 checks=self.check('length(@)', 1))

        # create a new certificate version
        self.cmd('keyvault certificate create --vault-name {kv} -n cert1 -p @"{policy2_path}"', checks=[
            self.check('status', 'completed'),
        ])

        # list certificate versions
        self.cmd('keyvault certificate list-versions --vault-name {kv} -n cert1 --maxresults 10',
                 checks=[
                     self.check('length(@)', 2),
                     self.check('[0].name', 'cert1')
                 ])
        ver_list = self.cmd('keyvault certificate list-versions --vault-name {kv} -n cert1',
                            checks=self.check('length(@)', 2)).get_output_in_json()

        ver_list = sorted(ver_list, key=lambda x: x['attributes']['created'])
        versions = [x['id'] for x in ver_list]

        # show certificate (latest)
        self.cmd('keyvault certificate show --vault-name {kv} -n cert1', checks=[
            self.check('id', versions[1]),
            self.check('policy.x509CertificateProperties.validityInMonths', 50),
            self.check('name', 'cert1')
        ])

        # show certificate (specific version)
        cert_version = versions[0].rsplit('/', 1)[1]
        self.kwargs['ver1'] = cert_version
        self.cmd('keyvault certificate show --vault-name {kv} -n cert1 -v {ver1}',
                 checks=self.check('id', versions[0]))

        # show certificate (by id)
        self.kwargs.update({'cert_id': versions[0]})
        self.cmd('keyvault certificate show --id {cert_id}',
                 checks=self.check('id', versions[0]))

        # plan to not display the managed keys/secrets
        self.cmd('keyvault key list --vault-name {kv}', checks=self.is_empty())
        self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())
        self.cmd('keyvault key show --vault-name {kv} -n cert1',
                 checks=self.check('managed', True))
        self.cmd('keyvault secret show --vault-name {kv} -n cert1',
                 checks=self.check('managed', True))

        # update certificate attributes
        self.cmd('keyvault certificate set-attributes --vault-name {kv} -n cert1 --enabled false -p @"{policy_path}"', checks=[
            self.check('id', versions[1]),
            self.check('attributes.enabled', False),
            self.check('policy.x509CertificateProperties.validityInMonths', 60),
            self.check('name', 'cert1')
        ])

        # backup and then delete certificate
        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} '
                 '--certificate-permissions backup delete get restore list purge')

        bak_file = 'backup.cert'
        self.kwargs['bak_file'] = bak_file
        self.cmd('keyvault certificate backup --vault-name {kv} -n cert1 --file {bak_file}')
        self.cmd('keyvault certificate delete --vault-name {kv} -n cert1')
        time.sleep(60)
        self.cmd('keyvault certificate purge --vault-name {kv} -n cert1')
        time.sleep(10)

        self.cmd('keyvault certificate list --vault-name {kv}',
                 checks=self.is_empty())
        self.cmd('keyvault certificate list --vault-name {kv} --maxresults 10',
                 checks=self.is_empty())

        # restore certificate from backup
        self.cmd('keyvault certificate restore --vault-name {kv} --file {bak_file}')
        self.cmd('keyvault certificate list --vault-name {kv}',
                 checks=self.check('length(@)', 1))
        if os.path.isfile(bak_file):
            os.remove(bak_file)


def _generate_certificate(path, keyfile=None, password=None):
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes

    if keyfile:
        with open(path, "rb") as kf:
            key_bytes = kf.read()
            key = serialization.load_pem_private_key(key_bytes, password, default_backend())
    else:
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption(),
        )

    # Various details about who we are. For a self-signed certificate the
    # Subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u'US'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u'WA'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u'Redmond'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"mysite.com")])

    cert = x509.CertificateBuilder().subject_name(subject) \
                                    .issuer_name(issuer) \
                                    .public_key(key.public_key()) \
                                    .serial_number(x509.random_serial_number()) \
                                    .not_valid_before(datetime.utcnow()) \
                                    .not_valid_after(datetime.utcnow() + timedelta(days=10)) \
                                    .sign(key, hashes.SHA256(), default_backend())

    # Write the cert out to disk
    with open(path, "wb") as f:
        f.write(key_bytes)
        f.write(cert.public_bytes(serialization.Encoding.PEM))


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultCertificateImportScenario(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_cert_import')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-im-', location='eastus2')
    def test_keyvault_certificate_import(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'eastus2'
        })

        # Create certificate with encrypted key
        # openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 3650 -out cert.pem
        # openssl pkcs8 -in key.pem -topk8 -v1 PBE-SHA1-3DES -out key.pem
        # type key.pem cert.pem > import_pem_encrypted_pwd_1234.pem
        # del key.pem cert.pem

        # Create certificate with plain key
        # openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 3650 -out cert.pem
        # type key.pem cert.pem > import_pem_plain.pem
        # del key.pem cert.pem

        # test certificate import
        self.kwargs.update({
            'pem_encrypted_file': os.path.join(TEST_DIR, 'import_pem_encrypted_pwd_1234.pem'),
            'pem_encrypted_password': '1234',
            'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
            'pem_policy_path': os.path.join(TEST_DIR, 'policy_import_pem.json')
        })

        self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
        self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert2 --file "{pem_encrypted_file}" --password {pem_encrypted_password} -p @"{pem_policy_path}"')

        # Test certificate file not exist
        with self.assertRaises(CLIError):
            self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert2 --file "notexist.json" -p @"{pem_policy_path}"')

        # self.kwargs.update({
        #     'pfx_plain_file': os.path.join(TEST_DIR, 'import_pfx.pfx'),
        #     'pfx_policy_path': os.path.join(TEST_DIR, 'policy_import_pfx.json')
        # })
        # self.cmd('keyvault certificate import --vault-name {kv} -n pfx-cert --file "{pfx_plain_file}" -p @"{pfx_policy_path}"')


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultSoftDeleteScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sd')
    @KeyVaultPreparer(name_prefix='cli-test-kv-sd-', location='eastus2', skip_delete=True)
    @KeyVaultPreparer(name_prefix='cli-test-kv-sd-', location='eastus2', parameter_name='key_vault2', key='kv2', skip_delete=True)
    def test_keyvault_softdelete(self, resource_group, key_vault, key_vault2):
        self.kwargs.update({
            'loc': 'eastus2'
        })

        vault = self.cmd('keyvault show -n {kv} -g {rg}').get_output_in_json()

        # add all purge permissions to default the access policy
        default_policy = vault['properties']['accessPolicies'][0]
        cert_perms = default_policy['permissions']['certificates']
        key_perms = default_policy['permissions']['keys']
        secret_perms = default_policy['permissions']['secrets']
        obj_id = default_policy['objectId']

        for p in [cert_perms, key_perms, secret_perms]:
            p.append('purge')

        self.kwargs.update({
            'obj_id': obj_id,
            'key_perms': ' '.join(key_perms),
            'secret_perms': ' '.join(secret_perms),
            'cert_perms': ' '.join(cert_perms)
        })

        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms} --secret-permissions {secret_perms} --certificate-permissions {cert_perms}')

        # create secrets keys and certificates to delete recover and purge
        self.cmd('keyvault secret set --vault-name {kv} -n secret1 --value ABC123',
                 checks=self.check('value', 'ABC123'))
        self.cmd('keyvault secret set --vault-name {kv} -n secret2 --value ABC123',
                 checks=self.check('value', 'ABC123'))

        self.cmd('keyvault key create --vault-name {kv} -n key1 -p software',
                 checks=self.check('attributes.enabled', True))
        self.cmd('keyvault key create --vault-name {kv} -n key2 -p software',
                 checks=self.check('attributes.enabled', True))

        # test key get-policy-template
        self.cmd('keyvault key get-policy-template',
                 checks=self.check('length(@)', 2))

        self.kwargs.update({
            'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
            'pem_policy_path': os.path.join(TEST_DIR, 'policy_import_pem.json')
        })
        self.cmd('keyvault certificate import --vault-name {kv} -n cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
        self.cmd('keyvault certificate import --vault-name {kv} -n cert2 --file "{pem_plain_file}" -p @"{pem_policy_path}"')

        # delete the secrets keys and certificates
        self.cmd('keyvault secret delete --vault-name {kv} -n secret1')
        self.cmd('keyvault secret delete --vault-name {kv} -n secret2')
        self.cmd('keyvault key delete --vault-name {kv} -n key1')
        self.cmd('keyvault key delete --vault-name {kv} -n key2')
        self.cmd('keyvault certificate delete --vault-name {kv} -n cert1')
        self.cmd('keyvault certificate delete --vault-name {kv} -n cert2')

        max_timeout = 100
        time_counter = 0
        while time_counter <= max_timeout:
            try:
                # recover secrets keys and certificates
                self.cmd('keyvault secret recover --vault-name {kv} -n secret1')
                self.cmd('keyvault key recover --vault-name {kv} -n key1')
                self.cmd('keyvault certificate recover --vault-name {kv} -n cert1')
            except:  # pylint: disable=bare-except
                time.sleep(10)
                time_counter += 10
            else:
                break

        # purge secrets keys and certificates
        time.sleep(120)
        self.cmd('keyvault secret purge --vault-name {kv} -n secret2')
        self.cmd('keyvault key purge --vault-name {kv} -n key2')
        self.cmd('keyvault certificate purge --vault-name {kv} -n cert2')

        # recover and purge
        self.cmd('keyvault delete -n {kv}')
        self.cmd('keyvault recover -n {kv} --no-wait')
        self.cmd('keyvault wait --updated -n {kv}')
        self.cmd('keyvault delete -n {kv}')
        self.cmd('keyvault purge -n {kv}')

        # recover and purge with location
        self.cmd('keyvault delete -n {kv2}')
        self.cmd('keyvault recover -n {kv2} -l {loc}', checks=self.check('name', '{kv2}'))
        self.cmd('keyvault delete -n {kv2}')
        self.cmd('keyvault purge -n {kv2} -l {loc}')


class KeyVaultStorageAccountScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sa')
    @StorageAccountPreparer(name_prefix='clitestkvsa')
    @KeyVaultPreparer(name_prefix='cli-test-kv-sa-')
    def test_keyvault_storage_account(self, resource_group, storage_account, key_vault):
        self.kwargs.update({
            'loc': 'westus',
            'sa_rid': f'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{storage_account}'
            })

        if self.is_live:
            # Give Key Vault access to the storage account
            self.cmd('az role assignment create --role "Storage Account Key Operator Service Role" '
                     '--assignee "https://vault.azure.net" --scope {sa_rid}')
            # Give tester all permissions to keyvault storage
            # (remember to replace the object id if you are the new tester)
            self.cmd('az keyvault set-policy -n {kv} --storage-permissions all purge --object-id 3707fb2f-ac10-4591-a04f-8b0d786ea37d')
            time.sleep(300)

        retry = 0
        while retry <= 3:
            try:
                kv_sa = self.cmd('keyvault storage add --vault-name {kv} -n {sa} --active-key-name key1 '
                                 '--auto-regenerate-key --regeneration-period P90D --resource-id {sa_rid}',
                                 checks=[self.check('activeKeyName', 'key1'),
                                         self.check('attributes.enabled', True),
                                         self.check('autoRegenerateKey', True),
                                         self.check('regenerationPeriod', 'P90D'),
                                         self.check('resourceId', '{sa_rid}')]).get_output_in_json()
                break
            except CLIError as e:
                if "Key vault service doesn't have proper permissions to access the storage account" in e.args[0]:
                    time.sleep(120)
                    retry += 1
                else:
                    raise e
        self.kwargs.update({
            'sa_id': kv_sa['id']
        })

        # create an account sas definition
        acct_sas_template = self.cmd('storage account generate-sas --expiry 2023-01-01 --permissions acdlpruw '
                                     '--resource-types sco --services bfqt --https-only --account-name {sa} '
                                     '--account-key 00000000 -o tsv').output.strip('\n')
        self.kwargs.update({
            'acct_temp': acct_sas_template,
            'acct_sas_name': 'allacctaccess'
        })
        sas_def = self.cmd('keyvault storage sas-definition create --vault-name {kv} --account-name {sa} '
                           '-n {acct_sas_name} --validity-period PT4H --sas-type account --template-uri "{acct_temp}"',
                           checks=[self.check('attributes.enabled', True)]).get_output_in_json()
        self.kwargs.update({
            'acct_sas_sid': sas_def['secretId'],
            'acct_sas_id': sas_def['id'],
        })

        # use the account sas token to create a container and a blob
        acct_sas_token = self.cmd('keyvault secret show --id {acct_sas_sid} --query value -o tsv').output.strip('\n')

        self.kwargs.update({
            'acct_sas': acct_sas_token,
            'c': 'cont1'
        })
        self.cmd('storage container create -n {c} --account-name {sa} --sas-token "{acct_sas}"',
                 checks=[self.check('created', True)])

        # regenerate the storage account key
        self.cmd('keyvault storage regenerate-key --id {sa_id} --key-name key1')

        # use the account sas token to upload a blob
        acct_sas_token = self.cmd('keyvault secret show --id {acct_sas_sid} --query value -o tsv').output.strip('\n')
        self.kwargs.update({
            'acct_sas': acct_sas_token,
            'b': 'test_secret.txt',
            'f': os.path.join(TEST_DIR, 'test_secret.txt')
        })
        time.sleep(60)
        self.cmd('storage blob upload -f "{f}" -c {c} -n {b} --account-name {sa} --sas-token "{acct_sas}"',
                 checks=[self.exists('lastModified')])

        # create a service sas token
        blob_sas_template = self.cmd('storage blob generate-sas -c {c} -n {b} --account-name {sa}'
                                     ' --account-key 00000000 --permissions r -o tsv').output.strip('\n')
        blob_url = self.cmd('storage blob url -c {c} -n {b} --account-name {sa} -o tsv').output.strip('\n')

        blob_temp = '{}?{}'.format(blob_url, blob_sas_template)
        print('blob_temp', blob_temp)
        self.kwargs.update({
            'blob_temp': blob_temp,
            'blob_sas_name': 'blob1r'
        })

        sas_def = self.cmd('keyvault storage sas-definition create --vault-name {kv} --account-name {sa} '
                           '-n {blob_sas_name} --sas-type service --validity-period P1D --template-uri "{blob_temp}"',
                           checks=[self.check('attributes.enabled', True)]).get_output_in_json()
        self.kwargs.update({
            'blob_sas_sid': sas_def['secretId'],
            'blob_sas_id': sas_def['id'],
        })

        # list the sas definitions
        self.cmd('keyvault storage sas-definition list --vault-name {kv} --account-name {sa}',
                 checks=[self.check('length(@)', 2)])

        # update the sas definitions
        self.cmd('keyvault storage sas-definition update --vault-name {kv} --account-name {sa} -n {blob_sas_name} '
                 '--sas-type service --validity-period PT12H --template-uri "{blob_temp}" --disabled',
                 checks=[self.check('attributes.enabled', False), self.check('validityPeriod', 'PT12H')])

        # show a sas definition by (vault, account-name, name) and by id
        self.cmd('keyvault storage sas-definition show --vault-name {kv} --account-name {sa} -n {blob_sas_name}',
                 checks=[self.check('id', '{blob_sas_id}')])
        self.cmd('keyvault storage sas-definition show --id {acct_sas_id}',
                 checks=[self.check('id', '{acct_sas_id}')])

        # delete a sas definition by (vault, account-name, name) and by id
        self.cmd('keyvault storage sas-definition delete --vault-name {kv} --account-name {sa} -n {blob_sas_name}')
        self.cmd('keyvault storage sas-definition delete --id {acct_sas_id}')

        # list the sas definitions and secrets verfy none are left
        self.cmd('keyvault storage sas-definition list --vault-name {kv} --account-name {sa}',
                 checks=[self.check('length(@)', 0)])
        self.cmd('keyvault secret list --vault-name {kv}', checks=[self.check('length(@)', 0)])

        # list the deleted sas definitions
        self.cmd('keyvault storage sas-definition list-deleted --vault-name {kv} --account-name {sa}',
                 checks=[self.check('length(@)', 2)])

        # show the deleted sas definition
        self.cmd('keyvault storage sas-definition show-deleted --vault-name {kv} --account-name {sa} -n {blob_sas_name}',
                 checks=[self.exists('recoveryId')])

        # recover the deleted
        self.cmd('keyvault storage sas-definition recover --vault-name {kv} --account-name {sa} -n {blob_sas_name}')

        self.cmd('keyvault storage sas-definition list-deleted --vault-name {kv} --account-name {sa}',
                 checks=[self.check('length(@)', 1)])

        # list the storage accounts
        self.cmd('keyvault storage list --vault-name {kv}', checks=[self.check('length(@)', 1)])

        # show the storage account by vault and name and by id
        self.cmd('keyvault storage show --vault-name {kv} -n {sa}',
                 checks=[self.check('resourceId', '{sa_rid}')])
        self.cmd('keyvault storage show --id {sa_id}',
                 checks=[self.check('resourceId', '{sa_rid}')])

        # update the storage account
        self.cmd('keyvault storage update --vault-name {kv} -n {sa} --regeneration-period P30D',
                 checks=[self.check('regenerationPeriod', 'P30D')])

        # delete the storage account and verify no storage accounts exist in the vault
        self.cmd('keyvault storage remove --id {sa_id}')
        self.cmd('keyvault storage list --vault-name {kv}', checks=[self.check('length(@)', 0)])
        self.cmd('keyvault storage list-deleted --vault-name {kv}', checks=[self.check('length(@)', 1)])
        self.cmd('keyvault storage show-deleted -n {sa} --vault-name {kv}', checks=[self.exists('recoveryId')])

        # recover the deleted storage account
        self.cmd('keyvault storage recover -n {sa} --vault-name {kv}')
        self.cmd('keyvault storage list --vault-name {kv}', checks=[self.check('length(@)', 1)])
        self.cmd('keyvault storage list-deleted --vault-name {kv}', checks=[self.check('length(@)', 0)])

        # backup the storage account in local file
        self.kwargs.update({
            'file': os.path.join(TEST_DIR, 'backup.blob')
        })
        self.cmd('keyvault storage backup -f "{file}" -n {sa} --vault-name {kv}')

        # permanently delete the storage account
        self.cmd('keyvault storage remove -n {sa} --vault-name {kv}')
        with self.assertRaisesRegex(CLIError, 'not found'):  # CLIError will be raised saying storage account not found, this need to be refined later
            self.cmd('keyvault storage purge -n {sa} --vault-name {kv}')
        self.cmd('keyvault storage list --vault-name {kv}', checks=[self.check('length(@)', 0)])
        self.cmd('keyvault storage list-deleted --vault-name {kv}', checks=[self.check('length(@)', 0)])

        # restore storage account from local backup
        self.cmd('keyvault storage restore -f "{file}" --vault-name {kv}')
        self.cmd('keyvault storage list --vault-name {kv}', checks=[self.check('length(@)', 1)])

        # clear local file
        try:
            os.remove(self.kwargs['file'])
        except Exception:
            return


class KeyVaultNetworkRuleScenarioTest(ScenarioTest):
    def _create_subnet(self, vnet_name='{vnet}', subnet_name='{subnet}'):
        self.cmd('network vnet create -g {{rg}} -n {vnet_name} -l {{loc}}'.format(vnet_name=vnet_name))
        self.cmd('network vnet subnet create -g {{rg}} --vnet-name {vnet_name} --name {subnet_name} '
                 '--address-prefixes 10.0.0.0/21 --service-endpoints Microsoft.KeyVault'.
                 format(vnet_name=vnet_name, subnet_name=subnet_name))
        return self.cmd('network vnet subnet show -g {{rg}} --vnet-name {vnet_name} --name {subnet_name}'.
                        format(vnet_name=vnet_name, subnet_name=subnet_name))

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_network_rule')
    def test_keyvault_network_rule(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-nr-', 24),
            'kv2': self.create_random_name('cli-test-kv-nr-', 24),
            'kv3': self.create_random_name('cli-test-kv-nr-', 24),
            'kv4': self.create_random_name('cli-test-kv-nr-', 24),
            'kv5': self.create_random_name('cli-test-kv-nr-', 24),
            'kv6': self.create_random_name('cli-test-kv-nr-', 24),
            'vnet': self.create_random_name('cli-test-vnet-', 24),
            'vnet2': self.create_random_name('cli-test-vnet-', 24),
            'vnet3': self.create_random_name('cli-test-vnet-', 24),
            'loc': 'eastus2',
            'subnet': self.create_random_name('cli-test-subnet-', 24),
            'subnet2': self.create_random_name('cli-test-subnet-', 24),
            'subnet3': self.create_random_name('cli-test-subnet-', 24),
            'ip': '1.2.3.4/32',
            'ip2': '2.3.4.0/24',
            'ip3': '3.4.5.0/24',
            'ip4': '4.5.0.0/16',
            'ip5': '1.2.3.4'
        })

        subnet = self._create_subnet().get_output_in_json()
        self.kwargs.update({
            # key vault service will convert subnet ID to lowercase, so convert subnet ID to lowercase in advance
            'subnetId': subnet['id'].lower()
        })

        # test creating network rules while creating vault
        network_acls = {
            'ip': [self.kwargs['ip'], self.kwargs['ip2']],
            'vnet': ['{}/{}'.format(self.kwargs['vnet'], self.kwargs['subnet'])]
        }
        json_filename = os.path.join(TEST_DIR, 'network_acls.json')
        network_acls2 = network_acls
        network_acls2['vnet'] = [self.kwargs['subnetId']]
        with open(json_filename, 'w') as f:
            json.dump(network_acls2, f)
        json_string = json.dumps(network_acls2).replace('"', '\\"')

        self.kwargs.update({
            'network_acls_json_string': json_string,
            'network_acls_json_filename': json_filename
        })
        self.cmd('keyvault create -n {kv2} -l {loc} -g {rg} --network-acls "{network_acls_json_string}"', checks=[
            self.check('length(properties.networkAcls.ipRules)', 2),
            self.check('properties.networkAcls.ipRules[0].value', '{ip}'),
            self.check('properties.networkAcls.ipRules[1].value', '{ip2}'),
            self.check('length(properties.networkAcls.virtualNetworkRules)', 1),
            self.check('properties.networkAcls.virtualNetworkRules[0].id', '{subnetId}')
        ])

        self.cmd('keyvault create -n {kv3} -l {loc} -g {rg} --network-acls "{network_acls_json_filename}"', checks=[
            self.check('length(properties.networkAcls.ipRules)', 2),
            self.check('properties.networkAcls.ipRules[0].value', '{ip}'),
            self.check('properties.networkAcls.ipRules[1].value', '{ip2}'),
            self.check('length(properties.networkAcls.virtualNetworkRules)', 1),
            self.check('properties.networkAcls.virtualNetworkRules[0].id', '{subnetId}')
        ])

        subnet2 = self._create_subnet(vnet_name='{vnet2}', subnet_name='{subnet2}').get_output_in_json()
        subnet3 = self._create_subnet(vnet_name='{vnet3}', subnet_name='{subnet3}').get_output_in_json()
        self.kwargs.update({
            'subnetId2': subnet2['id'].lower(),
            'subnetId3': subnet3['id'].lower()
        })

        self.cmd('keyvault create -n {kv4} -l {loc} -g {rg} --network-acls-ips {ip3} {ip4} '
                 '--network-acls-vnets {subnetId2} {vnet3}/{subnet3}', checks=[
                     self.check('length(properties.networkAcls.ipRules)', 2),
                     self.check('properties.networkAcls.ipRules[0].value', '{ip3}'),
                     self.check('properties.networkAcls.ipRules[1].value', '{ip4}'),
                     self.check('length(properties.networkAcls.virtualNetworkRules)', 2),
                     self.check('properties.networkAcls.virtualNetworkRules[0].id', '{subnetId2}'),
                     self.check('properties.networkAcls.virtualNetworkRules[1].id', '{subnetId3}')
                 ])

        self.cmd('keyvault create -n {kv5} -l {loc} -g {rg} --network-acls "@{network_acls_json_filename}" '
                 '--network-acls-ips {ip3} {ip4} '
                 '--network-acls-vnets {subnetId2} {vnet3}/{subnet3}', checks=[
                     self.check('length(properties.networkAcls.ipRules)', 4),
                     self.check('properties.networkAcls.ipRules[0].value', '{ip}'),
                     self.check('properties.networkAcls.ipRules[1].value', '{ip2}'),
                     self.check('properties.networkAcls.ipRules[2].value', '{ip3}'),
                     self.check('properties.networkAcls.ipRules[3].value', '{ip4}'),
                     self.check('length(properties.networkAcls.virtualNetworkRules)', 3),
                     self.check('properties.networkAcls.virtualNetworkRules[0].id', '{subnetId}'),
                     self.check('properties.networkAcls.virtualNetworkRules[1].id', '{subnetId2}'),
                     self.check('properties.networkAcls.virtualNetworkRules[2].id', '{subnetId3}')
                 ])

        self.cmd('keyvault create -n {kv6} -l {loc} -g {rg} --network-acls "{network_acls_json_filename}" '
                 '--network-acls-ips {ip3} {ip4} '
                 '--network-acls-vnets {subnetId2} {vnet3}/{subnet3}', checks=[
                     self.check('length(properties.networkAcls.ipRules)', 4),
                     self.check('properties.networkAcls.ipRules[0].value', '{ip}'),
                     self.check('properties.networkAcls.ipRules[1].value', '{ip2}'),
                     self.check('properties.networkAcls.ipRules[2].value', '{ip3}'),
                     self.check('properties.networkAcls.ipRules[3].value', '{ip4}'),
                     self.check('length(properties.networkAcls.virtualNetworkRules)', 3),
                     self.check('properties.networkAcls.virtualNetworkRules[0].id', '{subnetId}'),
                     self.check('properties.networkAcls.virtualNetworkRules[1].id', '{subnetId2}'),
                     self.check('properties.networkAcls.virtualNetworkRules[2].id', '{subnetId3}')
                 ])

        if os.path.isfile(json_filename):
            os.remove(json_filename)

        # basic tests
        _create_keyvault(self, self.kwargs)
        self.cmd('keyvault update --name {kv} --resource-group {rg} --default-action Deny')

        # add network-rule for subnet
        self.cmd('keyvault network-rule add --subnet {subnetId} --name {kv} --resource-group {rg}', checks=[
            self.check('properties.networkAcls.virtualNetworkRules[0].id', '{subnetId}')])

        # Add twice to make sure there is no duplication
        self.cmd('keyvault network-rule add --subnet {subnetId} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.virtualNetworkRules)', 1),
            self.check('properties.networkAcls.virtualNetworkRules[0].id', '{subnetId}')
        ])

        # list network-rule for subnet
        self.cmd('keyvault network-rule list --name {kv} --resource-group {rg}', checks=[
            self.check('virtualNetworkRules[0].id', '{subnetId}')])

        # remove network-rule for subnet
        self.cmd('keyvault network-rule remove --subnet {subnetId} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.virtualNetworkRules)', 0)])

        # add network-rule for ip-address
        self.cmd('keyvault network-rule add --ip-address {ip} --name {kv} --resource-group {rg}', checks=[
            self.check('properties.networkAcls.ipRules[0].value', '{ip}')])

        # Add twice to make sure there is no duplication
        self.cmd('keyvault network-rule add --ip-address {ip} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.ipRules)', 1),
            self.check('properties.networkAcls.ipRules[0].value', '{ip}')
        ])

        # Add ip without CIDR format to make sure there is no duplication
        self.cmd('keyvault network-rule add --ip-address {ip5} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.ipRules)', 1),
            self.check('properties.networkAcls.ipRules[0].value', '{ip}')
        ])

        # list network-rule for ip-address
        self.cmd('keyvault network-rule list --name {kv} --resource-group {rg}', checks=[
            self.check('ipRules[0].value', '{ip}')])

        # remove network-rule for ip-address
        self.cmd('keyvault network-rule remove --ip-address {ip} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.ipRules)', 0)])

        # remove network-rule for ip-address without CIDR
        self.cmd('keyvault network-rule add --ip-address {ip} --name {kv} --resource-group {rg}')
        self.cmd('keyvault network-rule remove --ip-address {ip5} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.ipRules)', 0)])

        # Add multiple ip addresses
        self.cmd('keyvault network-rule add --ip-address {ip} {ip2} {ip3} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.ipRules)', 3)
        ])

        # Add multiple ip addresses with overlaps between them
        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('keyvault network-rule add --ip-address {ip} {ip5} --name {kv} --resource-group {rg}')

        # Add multiple ip addresses with some overlaps with the server
        self.cmd('keyvault network-rule add --ip-address {ip4} {ip5} --name {kv} --resource-group {rg}', checks=[
            self.check('length(properties.networkAcls.ipRules)', 4)
        ])

class KeyVaultPublicNetworkAccessScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_pna')
    def test_keyvault_public_network_access(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-pna-', 24),
            'kv2': self.create_random_name('cli-test-kv2-pna-', 24),
            'kv3': self.create_random_name('cli-test-kv3-pna-', 24),
            'loc': 'eastus2euap'
        })
        self.cmd('keyvault create -g {rg} -n {kv} -l {loc}',
                 checks=[self.check('properties.publicNetworkAccess', 'Enabled')])
        self.cmd('keyvault create -g {rg} -n {kv2} -l {loc} --public-network-access Enabled',
                 checks=[self.check('properties.publicNetworkAccess', 'Enabled')])
        self.cmd('keyvault create -g {rg} -n {kv3} -l {loc} --public-network-access Disabled',
                 checks=[self.check('properties.publicNetworkAccess', 'Disabled')])
        self.cmd('keyvault update -g {rg} -n {kv3} --public-network-access Enabled',
                 checks=[self.check('properties.publicNetworkAccess', 'Enabled')])


if __name__ == '__main__':
    unittest.main()

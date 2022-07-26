# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import datetime
import os
import time
from shutil import rmtree
from msrestazure.azure_exceptions import CloudError

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, VirtualNetworkPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from knack.util import CLIError


class DataLakeStoreFileAccessScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_adls_access')
    def test_dls_file_access_mgmt(self):

        user_id = '470c0ccf-c91a-4597-98cd-48507d2f1486'

        self.kwargs.update({
            'dls': self.create_random_name('cliadls', 24),
            'loc': 'eastus2',
            'dir': 'adltestfolder01',
            'user_id': user_id,
            'acl_to_add': 'user:{}:rwx'.format(user_id),
            'acl_to_modify': 'user:{}:-w-'.format(user_id),
            'acl_to_remove': 'user:{}'.format(user_id)
        })

        # create ADLS account
        self.cmd('dls account create -g {rg} -n {dls} -l {loc} --disable-encryption')
        result = self.cmd('dls account show -g {rg} -n {dls}').get_output_in_json()
        while result['provisioningState'] != 'Succeeded' and result['provisioningState'] != 'Failed':
            time.sleep(5)
            result = self.cmd('dls account show -g {rg} -n {dls}').get_output_in_json()

        if result['provisioningState'] == 'Failed':
            raise CLIError('Failed to create the adls account, tests cannot proceed!')

        # create a folder
        self.cmd('dls fs create -n {dls} --path "{dir}" --folder --force')
        # get the folder
        self.cmd('dls fs show -n {dls} --path "{dir}"', checks=[
            self.check('name', '{dir}'),
            self.check('type', 'DIRECTORY'),
            self.check('length', 0),
        ])

        # set the owner and owning group for the file and confirm them
        self.kwargs.update({
            'group_id': '80a3ed5f-959e-4696-ba3c-d3c8b2db6766',
            'user_id': '6361e05d-c381-4275-a932-5535806bb323'
        })
        self.cmd('dls fs access set-owner -n {dls} --path "{dir}" --group {group_id} --owner {user_id}')

        # get the file and confirm those values
        self.cmd('dls fs show -n {dls} --path "{dir}"', checks=[
            self.check('name', '{dir}'),
            self.check('type', 'DIRECTORY'),
            self.check('length', 0),
            self.check('owner', '{user_id}'),
            self.check('group', '{group_id}'),
        ])

        # set the permissions on the file
        self.cmd('dls fs access set-permission -n {dls} --path "{dir}" --permission 777')
        # get the file and confirm those values
        self.cmd('dls fs show -n {dls} --path "{dir}"', checks=[
            self.check('name', '{dir}'),
            self.check('type', 'DIRECTORY'),
            self.check('length', 0),
            self.check('permission', '777'),
        ])

        # get the initial ACE
        result = self.cmd('dls fs access show -n {dls} --path "{dir}"').get_output_in_json()
        inital_acl_length = len(result['entries'])
        new_acl = ','.join(result['entries'])
        new_acl += ',{acl_to_add}'.format(**self.kwargs)
        self.kwargs['new_acl'] = new_acl
        # set the full ACL
        self.cmd('dls fs access set -n {dls} --path "{dir}" --acl-spec {new_acl}')
        # get the ACL and confirm that it has grown
        set_result = self.cmd('dls fs access show -n {dls} --path "{dir}"').get_output_in_json()
        assert len(set_result['entries']) > inital_acl_length
        assert self.kwargs['acl_to_add'] in set_result['entries']

        # modify that ACE with set-entry
        self.cmd('dls fs access set-entry -n {dls} --path "{dir}" --acl-spec {acl_to_modify}')
        # get the ACL and confirm it has been modified
        modify_result = self.cmd('dls fs access show -n {dls} --path "{dir}"').get_output_in_json()
        assert len(set_result['entries']) > inital_acl_length
        assert self.kwargs['acl_to_modify'] in modify_result['entries']
        # remove an ACE
        self.cmd('dls fs access remove-entry -n {dls} --path "{dir}" --acl-spec {acl_to_remove}')
        # get ACL and ensure that it is smaller than before
        remove_result = self.cmd('dls fs access show -n {dls} --path "{dir}"').get_output_in_json()
        assert len(remove_result['entries']) < len(modify_result['entries'])
        assert self.kwargs['acl_to_modify'] not in remove_result['entries']
        # remove default ACL
        self.cmd('dls fs access remove-all -n {dls} --path "{dir}" --default-acl')
        remove_result = self.cmd('dls fs access show -n {dls} --path "{dir}"').get_output_in_json()
        # there should be four entries left
        assert 4 == len(remove_result['entries'])

        # remove ACL
        self.cmd('dls fs access remove-all -n {dls} --path "{dir}"')
        remove_result = self.cmd('dls fs access show -n {dls} --path "{dir}"').get_output_in_json()
        # there should be three entries left
        assert 3 == len(remove_result['entries'])


class DataLakeStoreFileScenarioTest(ScenarioTest):

    def setUp(self):
        from unittest import mock
        import uuid

        def const_uuid():
            return uuid.UUID('{12345678-1234-5678-1234-567812345678}')

        self.mp = mock.patch('uuid.uuid4', const_uuid)
        self.mp.__enter__()
        super(DataLakeStoreFileScenarioTest, self).setUp()

    def tearDown(self):
        local_folder = self.kwargs.get('local_folder', None)
        if local_folder and os.path.exists(local_folder):
            rmtree(local_folder)
        self.mp.__exit__(None, None, None)
        return super(DataLakeStoreFileScenarioTest, self).tearDown()

    @ResourceGroupPreparer(name_prefix='cls_test_adls_file')
    def test_dls_file_mgmt(self):

        local_folder = 'adls_resources'
        self.kwargs.update({
            'dls': self.create_random_name('cliadls', 24),
            'loc': 'eastus2',
            'dir': local_folder,
            'local_folder': os.path.join(os.getcwd(), local_folder),
            'local_file': os.path.join(local_folder, 'sample_file.txt'),
            'local_file_content': 'Local File Content',
            'folder1': 'adltestfolder01',
            'folder2': 'adltestfolder02',
            'file': 'adltestfile01',
            'upload_file': 'adltestfile02',
            'join_file': 'adltestfile03',
            'download_file': 'adltestfile04',
            'content': '123456'
        })

        # create ADLS account
        self.cmd('dls account create -g {rg} -n {dls} -l {loc} --disable-encryption')
        result = self.cmd('dls account show -g {rg} -n {dls}').get_output_in_json()
        while result['provisioningState'] != 'Succeeded' and result['provisioningState'] != 'Failed':
            time.sleep(5)
            result = self.cmd('dls account show -g {rg} -n {dls}').get_output_in_json()

        if result['provisioningState'] == 'Failed':
            raise CLIError('Failed to create the adls account, tests cannot proceed!')

        # create local file
        if os.path.exists(local_folder):
            rmtree(local_folder)

        os.makedirs(local_folder)
        with open(self.kwargs['local_file'], 'w') as f:
            f.write(self.kwargs['local_file_content'])

        # file and folder manipulation
        # create a folder
        self.cmd('dls fs create -n {dls} --path "{folder1}" --folder --force')
        # get the folder
        self.cmd('dls fs show -n {dls} --path "{folder1}"', checks=[
            self.check('name', '{folder1}'),
            self.check('type', 'DIRECTORY'),
            self.check('length', 0),
        ])

        # create a file
        self.cmd('dls fs create -n {dls} --path "{folder1}/{file}" --content {content}')
        # get the file
        result = self.cmd('dls fs show -n {dls} --path "{folder1}/{file}"', checks=[
            self.check('name', '{folder1}/{file}'),
            self.check('type', 'FILE'),
            self.check('length', len(self.kwargs['content'])),
        ]).get_output_in_json()

        # set expiration time on the file
        # this future time gives the milliseconds since the epoch that have occured as of 01/31/2030 at noon
        epoch_time = datetime.datetime.utcfromtimestamp(0)
        final_time = datetime.datetime(2030, 1, 31, 12)
        self.kwargs['time_in_milliseconds'] = (final_time - epoch_time).total_seconds() * 1000
        self.cmd('dls fs set-expiry -n {dls} --path "{folder1}/{file}" --expiration-time {time_in_milliseconds}')
        new_result = self.cmd('dls fs show -n {dls} --path "{folder1}/{file}"', checks=[
            self.check('name', '{folder1}/{file}'),
            self.check('type', 'FILE'),
            self.check('length', len(self.kwargs['content'])),
        ]).get_output_in_json()

        # this value is not guaranteed to be exact, but it should be within a very small range (around 200ms)
        assert self.kwargs['time_in_milliseconds'] - 100 < new_result['msExpirationTime'] < self.kwargs['time_in_milliseconds'] + 100

        # remove the expiration time
        self.cmd('dls fs remove-expiry -n {dls} --path "{folder1}/{file}"')
        self.cmd('dls fs show -n {dls} --path "{folder1}/{file}"', checks=[
            self.check('name', '{folder1}/{file}'),
            self.check('type', 'FILE'),
            self.check('length', len(self.kwargs['content'])),
            self.check('msExpirationTime', result['msExpirationTime']),
        ])

        # move the file
        # this requires that the folder exists
        self.cmd('dls fs create -n {dls} --path "{folder2}" --folder --force')
        self.cmd('dls fs move -n {dls} --source-path "{folder1}/{file}" --destination-path "{folder2}/{file}"')
        # get the file at the new location
        self.cmd('dls fs show -n {dls} --path "{folder2}/{file}"', checks=[
            self.check('name', '{folder2}/{file}'),
            self.check('type', 'FILE'),
            self.check('length', len(self.kwargs['content'])),
        ])

        # preview the file
        result = self.cmd('dls fs preview -n {dls} --path "{folder2}/{file}"').get_output_in_json()
        assert result == self.kwargs['content']

        # partial file preview
        result = self.cmd('dls fs preview -n {dls} --path "{folder2}/{file}" --length 1 --offset 3').get_output_in_json()
        assert len(result) == 1
        assert result == '4'

        # list the directory, which contains just the one file
        self.cmd('dls fs list -n {dls} --path "{folder2}"', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].pathSuffix', '{file}'),
            self.check('[0].type', 'FILE'),
            self.check('[0].length', len(self.kwargs['content'])),
        ])

        # append content to a file
        self.cmd('dls fs append -n {dls} --path "{folder2}/{file}" --content {content}')
        # get the file
        self.cmd('dls fs show -n {dls} --path "{folder2}/{file}"', checks=[
            self.check('name', '{folder2}/{file}'),
            self.check('type', 'FILE'),
            self.check('length', len(self.kwargs['content']) * 2),
        ])

        # upload a file
        self.cmd('dls fs upload -n {dls} --destination-path "{folder1}/{upload_file}" --source-path "{local_file}"')
        # get the file
        self.cmd('dls fs show -n {dls} --path "{folder1}/{upload_file}"', checks=[
            self.check('name', '{folder1}/{upload_file}'),
            self.check('type', 'FILE'),
            self.check('length', len(self.kwargs['local_file_content'])),
        ])
        # join the uploaded file to the created file
        self.cmd('dls fs join -n {dls} --destination-path "{folder1}/{join_file}" --source-paths "{folder1}/{upload_file}" "{folder2}/{file}"')
        self.cmd('dls fs show -n {dls} --path "{folder1}/{join_file}"', checks=[
            self.check('name', '{folder1}/{join_file}'),
            self.check('type', 'FILE'),
            self.check('length', len(self.kwargs['local_file_content']) + (len(self.kwargs['content']) * 2)),
        ])

        # download the joined file
        self.cmd('dls fs download -n {dls} --destination-path "{dir}/{download_file}" --source-path "{folder1}/{join_file}"')
        assert os.path.getsize(os.path.join(self.kwargs['dir'], self.kwargs['download_file'])) == len(self.kwargs['local_file_content']) + (len(self.kwargs['content']) * 2)

        # delete the file and confirm it is gone.
        self.cmd('dls fs delete -n {dls} --path "{folder1}/{join_file}"')
        self.cmd('dls fs list -n {dls} --path "{folder1}"', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])

        # delete a folder that has contents and confirm it is gone.
        self.cmd('dls fs create -n {dls} --path "{folder2}" --folder')
        self.cmd('dls fs create -n {dls} --path "{folder2}/tempfile01.txt"')
        self.cmd('dls fs delete -n {dls} --path "{folder2}" --recurse')
        time.sleep(10)

        # test that the path is gone
        result = self.cmd('dls fs test -n {dls} --path "{folder2}"').get_output_in_json()
        self.assertTrue(not result)

        # test that the other folder still exists
        result = self.cmd('dls fs test -n {dls} --path "{folder1}"').get_output_in_json()
        self.assertTrue(result)


class DataLakeStoreAccountScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_adls_mgmt')
    @VirtualNetworkPreparer()
    @AllowLargeResponse()
    def test_dls_account_mgmt(self, resource_group):

        self.kwargs.update({
            'dls': self.create_random_name('cliadls', 24),
            'loc': 'eastus2',
            'updated_subnet': 'updatedSubnet'
        })

        # test create keyvault with default access policy set
        self.cmd('dls account create -g {rg} -n {dls} -l {loc}', checks=[
            self.check('name', '{dls}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('encryptionState', 'Enabled'),
        ])
        self.cmd('dls account show -n {dls} -g {rg}', checks=[
            self.check('name', '{dls}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('encryptionState', 'Enabled'),
        ])

        # attempt to enable the key vault when it is already enabled, which should throw
        with self.assertRaises(CloudError):
            self.cmd('dls account enable-key-vault -n {dls} -g {rg}')

        self.cmd('dls account list -g {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{dls}'),
            self.check('[0].location', '{loc}'),
            self.check('[0].resourceGroup', '{rg}'),
        ])
        result = self.cmd('dls account list').get_output_in_json()
        assert isinstance(result, list)
        assert len(result) >= 1

        # test update acct
        self.cmd('dls account update -g {rg} -n {dls} --firewall-state Enabled --trusted-id-provider-state Enabled')
        self.cmd('dls account show -n {dls} -g {rg}', checks=[
            self.check('name', '{dls}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('firewallState', 'Enabled'),
            self.check('trustedIdProviderState', 'Enabled'),
        ])

        # test firewall crud
        self.kwargs.update({
            'fw': 'testfirewallrule01',
            'start_ip': '127.0.0.1',
            'end_ip': '127.0.0.2',
            'new_end_ip': '127.0.0.3'
        })
        self.cmd('dls account firewall create -g {rg} -n {dls} --firewall-rule-name {fw} --start-ip-address {start_ip} --end-ip-address {end_ip}')
        self.cmd('dls account firewall show -g {rg} -n {dls} --firewall-rule-name {fw}', checks=[
            self.check('name', '{fw}'),
            self.check('startIpAddress', '{start_ip}'),
            self.check('endIpAddress', '{end_ip}'),
        ])

        self.cmd('dls account firewall update -g {rg} -n {dls} --firewall-rule-name {fw} --end-ip-address {new_end_ip}')
        self.cmd('dls account firewall show -g {rg} -n {dls} --firewall-rule-name {fw}', checks=[
            self.check('name', '{fw}'),
            self.check('startIpAddress', '{start_ip}'),
            self.check('endIpAddress', '{new_end_ip}'),
        ])

        self.cmd('dls account firewall list -g {rg} -n {dls}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        self.cmd('dls account firewall delete -g {rg} -n {dls} --firewall-rule-name {fw}')
        self.cmd('dls account firewall list -g {rg} -n {dls}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])

        # test virtual network rule crud
        subnet_id = self.cmd('network vnet subnet show -g {rg} -n default --vnet-name {vnet}').get_output_in_json()['id']
        updated_subnet_id = self.cmd('network vnet subnet create --resource-group {rg} --vnet-name {vnet} --name {updated_subnet} --address-prefixes 10.0.1.0/24').get_output_in_json()['id']

        self.kwargs.update({
            'subnet_id': subnet_id,
            'updated_subnet_id': updated_subnet_id,
            'network_rule': 'dlsVnetRule'
        })
        self.cmd('network vnet subnet update --service-endpoints Microsoft.AzureActiveDirectory --ids "{subnet_id}"')
        self.cmd('network vnet subnet update --service-endpoints Microsoft.AzureActiveDirectory --ids "{updated_subnet_id}"')

        self.cmd('dls account network-rule create -g {rg} --account-name {dls} --name {network_rule} --subnet {subnet_id}')
        self.cmd('dls account network-rule show -g {rg} --account-name {dls} --name {network_rule}', checks=[
            self.check('name', '{network_rule}'),
        ])

        self.cmd('dls account network-rule update -g {rg} --account-name {dls} --name {network_rule} --subnet {updated_subnet_id}')
        self.cmd('dls account network-rule show -g {rg} --account-name {dls} --name {network_rule}', checks=[
            self.check('name', '{network_rule}'),
        ])

        self.cmd('dls account network-rule list -g {rg} --account-name {dls}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        self.cmd('dls account network-rule delete -g {rg} --account-name {dls} --name {network_rule}')
        self.cmd('dls account network-rule list -g {rg} --account-name {dls}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])
        # test trusted id provider CRUD
        self.kwargs.update({
            'trusted_provider': 'https://sts.windows.net/9d5b43a0-804c-4c82-8791-36aca2f72342',
            'new_provider': 'https://sts.windows.net/fceb709f-96f1-4c65-b06f-2541114bffb3',
            'provider': 'testprovider01'
        })
        self.cmd('dls account trusted-provider create -g {rg} -n {dls} --trusted-id-provider-name {provider} --id-provider {trusted_provider}')
        self.cmd('dls account trusted-provider show -g {rg} -n {dls} --trusted-id-provider-name {provider}', checks=[
            self.check('name', '{provider}'),
            self.check('idProvider', '{trusted_provider}'),
        ])

        self.cmd('dls account trusted-provider update -g {rg} -n {dls} --trusted-id-provider-name {provider} --id-provider {new_provider}')
        self.cmd('dls account trusted-provider show -g {rg} -n {dls} --trusted-id-provider-name {provider}', checks=[
            self.check('name', '{provider}'),
            self.check('idProvider', '{new_provider}'),
        ])

        self.cmd('dls account trusted-provider list -g {rg} -n {dls}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
        ])
        self.cmd('dls account trusted-provider delete -g {rg} -n {dls} --trusted-id-provider-name {provider}')
        self.cmd('dls account trusted-provider list -g {rg} -n {dls}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])

        # test account deletion
        self.cmd('dls account delete -g {rg} -n {dls}')
        self.cmd('dls account list -g {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0),
        ])

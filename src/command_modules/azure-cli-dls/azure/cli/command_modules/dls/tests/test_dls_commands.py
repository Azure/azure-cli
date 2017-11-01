# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from __future__ import print_function

import datetime
import os
import time
from shutil import rmtree
from msrestazure.azure_exceptions import CloudError

from knack.util import CLIError
from azure.cli.testsdk.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck)


class DataLakeStoreFileAccessScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeStoreFileAccessScenarioTest, self).__init__(__file__, test_method, resource_group='test-adls-access')
        self.adls_name = 'cliadls123426'
        self.location = 'eastus2'

    def test_dls_file_access_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeStoreFileAccessScenarioTest, self).set_up()

        # create ADLS account
        self.cmd('dls account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_name, self.location))
        result = self.cmd('dls account show -g {} -n {}'.format(self.resource_group, self.adls_name))
        while result['provisioningState'] != 'Succeeded' and result['provisioningState'] != 'Failed':
            time.sleep(5)
            result = self.cmd('dls account show -g {} -n {}'.format(self.resource_group, self.adls_name))

        if result['provisioningState'] == 'Failed':
            raise CLIError('Failed to create the adls account, tests cannot proceed!')

    def body(self):
        # define variables
        adls = self.adls_name
        folder_name = 'adltestfolder01'
        user_id = '470c0ccf-c91a-4597-98cd-48507d2f1486'
        acl_to_add = 'user:{}:rwx'.format(user_id)
        acl_to_modify = 'user:{}:-w-'.format(user_id)
        acl_to_remove = 'user:{}'.format(user_id)

        # create a folder
        self.cmd('dls fs create -n {} --path "{}" --folder --force'.format(adls, folder_name))
        # get the folder
        self.cmd('dls fs show -n {} --path "{}"'.format(adls, folder_name), checks=[
            JMESPathCheck('name', folder_name),
            JMESPathCheck('type', 'DIRECTORY'),
            JMESPathCheck('length', 0),
        ])

        # set the owner and owning group for the file and confirm them
        group_id = '80a3ed5f-959e-4696-ba3c-d3c8b2db6766'
        user_id = '6361e05d-c381-4275-a932-5535806bb323'
        self.cmd('dls fs access set-owner -n {} --path "{}" --group {} --owner {}'.format(adls, folder_name, group_id, user_id))

        # get the file and confirm those values
        result = self.cmd('dls fs show -n {} --path "{}"'.format(adls, folder_name), checks=[
            JMESPathCheck('name', folder_name),
            JMESPathCheck('type', 'DIRECTORY'),
            JMESPathCheck('length', 0),
            JMESPathCheck('owner', user_id),
            JMESPathCheck('group', group_id),
        ])

        # set the permissions on the file
        self.cmd('dls fs access set-permission -n {} --path "{}" --permission {}'.format(adls, folder_name, 777))
        # get the file and confirm those values
        result = self.cmd('dls fs show -n {} --path "{}"'.format(adls, folder_name), checks=[
            JMESPathCheck('name', folder_name),
            JMESPathCheck('type', 'DIRECTORY'),
            JMESPathCheck('length', 0),
            JMESPathCheck('permission', '777'),
        ])

        # get the initial ACE
        result = self.cmd('dls fs access show -n {} --path "{}"'.format(adls, folder_name))
        inital_acl_length = len(result['entries'])
        new_acl = ','.join(result['entries'])
        new_acl += ',{}'.format(acl_to_add)
        # set the full ACL
        self.cmd('dls fs access set -n {} --path "{}" --acl-spec {}'.format(adls, folder_name, new_acl))
        # get the ACL and confirm that it has grown
        set_result = self.cmd('dls fs access show -n {} --path "{}"'.format(adls, folder_name))
        assert len(set_result['entries']) > inital_acl_length
        assert acl_to_add in set_result['entries']

        # modify that ACE with set-entry
        self.cmd('dls fs access set-entry -n {} --path "{}" --acl-spec {}'.format(adls, folder_name, acl_to_modify))
        # get the ACL and confirm it has been modified
        modify_result = self.cmd('dls fs access show -n {} --path "{}"'.format(adls, folder_name))
        assert len(set_result['entries']) > inital_acl_length
        assert acl_to_modify in modify_result['entries']
        # remove an ACE
        self.cmd('dls fs access remove-entry -n {} --path "{}" --acl-spec {}'.format(adls, folder_name, acl_to_remove))
        # get ACL and ensure that it is smaller than before
        remove_result = self.cmd('dls fs access show -n {} --path "{}"'.format(adls, folder_name))
        assert len(remove_result['entries']) < len(modify_result['entries'])
        assert acl_to_modify not in remove_result['entries']
        # remove default ACL
        self.cmd('dls fs access remove-all -n {} --path "{}" --default-acl'.format(adls, folder_name))
        remove_result = self.cmd('dls fs access show -n {} --path "{}"'.format(adls, folder_name))
        # there should be four entries left
        assert 4 == len(remove_result['entries'])

        # remove ACL
        self.cmd('dls fs access remove-all -n {} --path "{}"'.format(adls, folder_name))
        remove_result = self.cmd('dls fs access show -n {} --path "{}"'.format(adls, folder_name))
        # there should be three entries left
        assert 3 == len(remove_result['entries'])


class DataLakeStoreFileScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeStoreFileScenarioTest, self).__init__(__file__, test_method, resource_group='test-adls-file')
        self.adls_name = 'cliadls123416'
        self.location = 'eastus2'
        self.local_folder = os.path.join(os.getcwd(), 'adls_resources')
        self.local_file = os.path.join(self.local_folder, 'sample_file.txt')
        self.local_file_content = 'Local File Content'

    def test_dls_file_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeStoreFileScenarioTest, self).set_up()

        # create ADLS account
        self.cmd('dls account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_name, self.location))
        result = self.cmd('dls account show -g {} -n {}'.format(self.resource_group, self.adls_name))
        while result['provisioningState'] != 'Succeeded' and result['provisioningState'] != 'Failed':
            time.sleep(5)
            result = self.cmd('dls account show -g {} -n {}'.format(self.resource_group, self.adls_name))

        if result['provisioningState'] == 'Failed':
            raise CLIError('Failed to create the adls account, tests cannot proceed!')

    def tear_down(self):
        super(DataLakeStoreFileScenarioTest, self).tear_down()
        if os.path.exists(self.local_folder):
            rmtree(self.local_folder)

    def body(self):
        adls = self.adls_name
        folder_name = 'adltestfolder01'
        move_folder_name = 'adltestfolder02'
        file_name = 'adltestfile01'
        upload_file_name = 'adltestfile02'
        join_file_name = 'adltestfile03'
        download_file_name = 'adltestfile04'
        file_content = '123456'

        # create local file
        if os.path.exists(self.local_folder):
            rmtree(self.local_folder)

        os.makedirs(self.local_folder)
        with open(self.local_file, 'w') as f:
            f.write(self.local_file_content)

        # file and folder manipulation
        # create a folder
        self.cmd('dls fs create -n {} --path "{}" --folder --force'.format(adls, folder_name))
        # get the folder
        self.cmd('dls fs show -n {} --path "{}"'.format(adls, folder_name), checks=[
            JMESPathCheck('name', folder_name),
            JMESPathCheck('type', 'DIRECTORY'),
            JMESPathCheck('length', 0),
        ])

        # create a file
        self.cmd('dls fs create -n {} --path "{}/{}" --content {}'.format(adls, folder_name, file_name, file_content))
        # get the file
        result = self.cmd('dls fs show -n {} --path "{}/{}"'.format(adls, folder_name, file_name), checks=[
            JMESPathCheck('name', '{}/{}'.format(folder_name, file_name)),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
        ])

        # set expiration time on the file
        # this future time gives the milliseconds since the epoch that have occured as of 01/31/2030 at noon
        epoch_time = datetime.datetime.utcfromtimestamp(0)
        final_time = datetime.datetime(2030, 1, 31, 12)
        time_in_milliseconds = (final_time - epoch_time).total_seconds() * 1000
        self.cmd('dls fs set-expiry -n {} --path "{}/{}" --expiration-time {}'.format(adls, folder_name, file_name, time_in_milliseconds))
        new_result = self.cmd('dls fs show -n {} --path "{}/{}"'.format(adls, folder_name, file_name), checks=[
            JMESPathCheck('name', '{}/{}'.format(folder_name, file_name)),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
        ])

        # this value is not guaranteed to be exact, but it should be within a very small range (around 200ms)
        assert time_in_milliseconds - 100 < new_result['msExpirationTime'] < time_in_milliseconds + 100

        # remove the expiration time
        self.cmd('dls fs remove-expiry -n {} --path "{}/{}"'.format(adls, folder_name, file_name))
        self.cmd('dls fs show -n {} --path "{}/{}"'.format(adls, folder_name, file_name), checks=[
            JMESPathCheck('name', '{}/{}'.format(folder_name, file_name)),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
            JMESPathCheck('msExpirationTime', result['msExpirationTime']),
        ])

        # move the file
        # this requires that the folder exists
        self.cmd('dls fs create -n {} --path "{}" --folder --force'.format(adls, move_folder_name))
        self.cmd('dls fs move -n {} --source-path "{}/{}" --destination-path "{}/{}"'.format(adls, folder_name, file_name, move_folder_name, file_name))
        # get the file at the new location
        self.cmd('dls fs show -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name), checks=[
            JMESPathCheck('name', '{}/{}'.format(move_folder_name, file_name)),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
        ])

        # preview the file
        result = self.cmd('dls fs preview -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name))
        assert result == file_content

        # partial file preview
        result = self.cmd('dls fs preview -n {} --path "{}/{}" --length 1 --offset 3'.format(adls, move_folder_name, file_name))
        assert len(result) == 1
        assert result == '4'

        # list the directory, which contains just the one file
        self.cmd('dls fs list -n {} --path "{}"'.format(adls, move_folder_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].pathSuffix', file_name),
            JMESPathCheck('[0].type', 'FILE'),
            JMESPathCheck('[0].length', len(file_content)),
        ])

        # append content to a file
        self.cmd('dls fs append -n {} --path "{}/{}" --content {}'.format(adls, move_folder_name, file_name, file_content))
        # get the file
        self.cmd('dls fs show -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name), checks=[
            JMESPathCheck('name', '{}/{}'.format(move_folder_name, file_name)),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content) * 2),
        ])

        # upload a file
        self.cmd('dls fs upload -n {} --destination-path "{}/{}" --source-path "{}"'.format(adls, folder_name, upload_file_name, self.local_file))
        # get the file
        self.cmd('dls fs show -n {} --path "{}/{}"'.format(adls, folder_name, upload_file_name), checks=[
            JMESPathCheck('name', '{}/{}'.format(folder_name, upload_file_name)),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(self.local_file_content)),
        ])
        # join the uploaded file to the created file
        self.cmd('dls fs join -n {} --destination-path "{}/{}" --source-paths "{}/{}","{}/{}"'.format(adls, folder_name, join_file_name, folder_name, upload_file_name, move_folder_name, file_name))
        self.cmd('dls fs show -n {} --path "{}/{}"'.format(adls, folder_name, join_file_name), checks=[
            JMESPathCheck('name', '{}/{}'.format(folder_name, join_file_name)),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(self.local_file_content) + (len(file_content) * 2)),
        ])

        # download the joined file
        self.cmd('dls fs download -n {} --destination-path "{}" --source-path "{}/{}"'.format(adls, os.path.join(self.local_folder, download_file_name), folder_name, join_file_name))
        assert os.path.getsize(os.path.join(self.local_folder, download_file_name)) == len(self.local_file_content) + (len(file_content) * 2)

        # delete the file and confirm it is gone.
        self.cmd('dls fs delete -n {} --path "{}/{}"'.format(adls, folder_name, join_file_name))
        self.cmd('dls fs list -n {} --path "{}"'.format(adls, folder_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])

        # delete a folder that has contents and confirm it is gone.
        self.cmd('dls fs create -n {} --path "{}" --folder'.format(adls, move_folder_name))
        self.cmd('dls fs create -n {} --path "{}/{}"'.format(adls, move_folder_name, 'tempfile01.txt'))
        self.cmd('dls fs delete -n {} --path "{}" --recurse'.format(adls, move_folder_name))
        # test that the path is gone
        assert not self.cmd('dls fs test -n {} --path "{}"'.format(adls, move_folder_name))

        # test that the other folder still exists
        assert self.cmd('dls fs test -n {} --path "{}"'.format(adls, folder_name))

        if os.path.exists(self.local_folder):
            rmtree(self.local_folder)


class DataLakeStoreAccountScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeStoreAccountScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adls-mgmt')
        self.adls_name = 'cliadls1234510'
        self.location = 'eastus2'

    def test_dls_account_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeStoreAccountScenarioTest, self).set_up()

    def body(self):
        rg = self.resource_group
        adls = self.adls_name
        loc = self.location
        # test create keyvault with default access policy set
        self.cmd('dls account create -g {} -n {} -l {}'.format(rg, adls, loc), checks=[
            JMESPathCheck('name', adls),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('encryptionState', 'Enabled'),
        ])
        self.cmd('dls account show -n {} -g {}'.format(adls, rg), checks=[
            JMESPathCheck('name', adls),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('encryptionState', 'Enabled'),
        ])

        # attempt to enable the key vault when it is already enabled, which should throw
        with self.assertRaises(CloudError):
            self.cmd('dls account enable-key-vault -n {} -g {}'.format(adls, rg))

        self.cmd('dls account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', adls),
            JMESPathCheck('[0].location', loc),
            JMESPathCheck('[0].resourceGroup', rg),
        ])
        result = self.cmd('dls account list')
        assert isinstance(result, list)
        assert len(result) >= 1

        # test update acct
        self.cmd('dls account update -g {} -n {} --firewall-state Enabled --trusted-id-provider-state Enabled'.format(rg, adls))
        self.cmd('dls account show -n {} -g {}'.format(adls, rg), checks=[
            JMESPathCheck('name', adls),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('firewallState', 'Enabled'),
            JMESPathCheck('trustedIdProviderState', 'Enabled'),
        ])

        # test firewall crud
        fw_name = 'testfirewallrule01'
        start_ip = '127.0.0.1'
        end_ip = '127.0.0.2'
        new_end_ip = '127.0.0.3'
        self.cmd('dls account firewall create -g {} -n {} --firewall-rule-name {} --start-ip-address {} --end-ip-address {}'.format(rg, adls, fw_name, start_ip, end_ip))
        self.cmd('dls account firewall show -g {} -n {} --firewall-rule-name {}'.format(rg, adls, fw_name), checks=[
            JMESPathCheck('name', fw_name),
            JMESPathCheck('startIpAddress', start_ip),
            JMESPathCheck('endIpAddress', end_ip),
        ])

        self.cmd('dls account firewall update -g {} -n {} --firewall-rule-name {} --end-ip-address {}'.format(rg, adls, fw_name, new_end_ip))
        self.cmd('dls account firewall show -g {} -n {} --firewall-rule-name {}'.format(rg, adls, fw_name), checks=[
            JMESPathCheck('name', fw_name),
            JMESPathCheck('startIpAddress', start_ip),
            JMESPathCheck('endIpAddress', new_end_ip),
        ])

        self.cmd('dls account firewall list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        self.cmd('dls account firewall delete -g {} -n {} --firewall-rule-name {}'.format(rg, adls, fw_name))
        self.cmd('dls account firewall list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])
        # test trusted id provider CRUD
        trusted_provider = 'https://sts.windows.net/9d5b43a0-804c-4c82-8791-36aca2f72342'
        new_provider = 'https://sts.windows.net/fceb709f-96f1-4c65-b06f-2541114bffb3'
        provider_name = 'testprovider01'
        self.cmd('dls account trusted-provider create -g {} -n {} --trusted-id-provider-name {} --id-provider {}'.format(rg, adls, provider_name, trusted_provider))
        self.cmd('dls account trusted-provider show -g {} -n {} --trusted-id-provider-name {}'.format(rg, adls, provider_name), checks=[
            JMESPathCheck('name', provider_name),
            JMESPathCheck('idProvider', trusted_provider),
        ])

        self.cmd('dls account trusted-provider update -g {} -n {} --trusted-id-provider-name {} --id-provider {}'.format(rg, adls, provider_name, new_provider))
        self.cmd('dls account trusted-provider show -g {} -n {} --trusted-id-provider-name {}'.format(rg, adls, provider_name), checks=[
            JMESPathCheck('name', provider_name),
            JMESPathCheck('idProvider', new_provider),
        ])

        self.cmd('dls account trusted-provider list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        self.cmd('dls account trusted-provider delete -g {} -n {} --trusted-id-provider-name {}'.format(rg, adls, provider_name))
        self.cmd('dls account trusted-provider list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])

        # test account deletion
        self.cmd('dls account delete -g {} -n {}'.format(rg, adls))
        self.cmd('dls account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])

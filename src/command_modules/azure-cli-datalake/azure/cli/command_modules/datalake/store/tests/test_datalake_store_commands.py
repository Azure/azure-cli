# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
from __future__ import print_function

import os
import time

from shutil import rmtree
from azure.cli.core._util import CLIError
from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck)

class DataLakeStoreFileScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeStoreFileScenarioTest, self).__init__(__file__, test_method, resource_group='test-adls-file')
        self.adls_name = 'cliadls123416'
        self.location = 'eastus2'
        self.local_folder = os.path.join(os.getcwd(), 'adls_resources')
        self.local_file = os.path.join(self.local_folder, 'sample_file.txt')
        self.local_file_content = 'Local File Content'

    def test_datalake_store_file_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeStoreFileScenarioTest, self).set_up()

        # create ADLS account
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_name, self.location))
        result = self.cmd('datalake store account show -g {} -n {}'.format(self.resource_group, self.adls_name))
        while result['provisioningState'] != 'Succeeded' and result['provisioningState'] != 'Failed':
            time.sleep(5)
            result = self.cmd('datalake store account show -g {} -n {}'.format(self.resource_group, self.adls_name))

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
        self.cmd('datalake store file create -n {} --path "{}" --folder --force'.format(adls, folder_name))
        # get the folder
        self.cmd('datalake store file show -n {} --path "{}"'.format(adls, folder_name), checks=[
            JMESPathCheck('name', folder_name),
            JMESPathCheck('type', 'DIRECTORY'),
            JMESPathCheck('length', 0),
        ])

        # create a file
        self.cmd('datalake store file create -n {} --path "{}/{}" --content {}'.format(adls, folder_name, file_name, file_content))
        # get the file
        self.cmd('datalake store file show -n {} --path "{}/{}"'.format(adls, folder_name, file_name), checks=[
            JMESPathCheck('pathSuffix', file_name),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
        ])

        # move the file
        # this requires that the folder exists
        self.cmd('datalake store file create -n {} --path "{}" --folder --force'.format(adls, move_folder_name))
        self.cmd('datalake store file move -n {} --source-path "{}/{}" --destination-path "{}/{}"'.format(adls, folder_name, file_name, move_folder_name, file_name))
        # get the file at the new location
        self.cmd('datalake store file show -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name), checks=[
            JMESPathCheck('pathSuffix', file_name),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
        ])

        # preview the file
        result = self.cmd('datalake store file preview -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name))
        assert result == file_content

        # partial file preview
        result = self.cmd('datalake store file preview -n {} --path "{}/{}" --length 1 --offset 3'.format(adls, move_folder_name, file_name))
        assert len(result) == 1
        assert result == '4'

        # list the directory, which contains just the one file
        self.cmd('datalake store file list -n {} --path "{}"'.format(adls, move_folder_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].pathSuffix', file_name),
            JMESPathCheck('[0].type', 'FILE'),
            JMESPathCheck('[0].length', len(file_content)),
        ])

        # set the owner and owning group for the file and confirm them
        group_id = '80a3ed5f-959e-4696-ba3c-d3c8b2db6766'
        user_id = '6361e05d-c381-4275-a932-5535806bb323'
        self.cmd('datalake store file set-owner -n {} --path "{}/{}" --group {} --owner {}'.format(adls, move_folder_name, file_name, group_id, user_id))

        # get the file and confirm those values
        result = self.cmd('datalake store file show -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name), checks=[
            JMESPathCheck('pathSuffix', file_name),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
            JMESPathCheck('owner', user_id),
            JMESPathCheck('group', group_id),
        ])

        # set the permissions on the file
        self.cmd('datalake store file set-permission -n {} --path "{}/{}" --permission {}'.format(adls, move_folder_name, file_name, 777))
        # get the file and confirm those values
        result = self.cmd('datalake store file show -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name), checks=[
            JMESPathCheck('pathSuffix', file_name),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content)),
            JMESPathCheck('permission', '777'),
        ])

        # append content to a file
        self.cmd('datalake store file append -n {} --path "{}/{}" --content {}'.format(adls, move_folder_name, file_name, file_content))
        # get the file
        self.cmd('datalake store file show -n {} --path "{}/{}"'.format(adls, move_folder_name, file_name), checks=[
            JMESPathCheck('pathSuffix', file_name),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(file_content) * 2),
        ])

        # upload a file
        self.cmd('datalake store file upload -n {} --destination-path "{}/{}" --source-path "{}"'.format(adls, folder_name, upload_file_name, self.local_file))
        # get the file
        self.cmd('datalake store file show -n {} --path "{}/{}"'.format(adls, folder_name, upload_file_name), checks=[
            JMESPathCheck('pathSuffix', upload_file_name),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(self.local_file_content)),
        ])
        # join the uploaded file to the created file
        self.cmd('datalake store file join -n {} --destination-path "{}/{}" --source-paths "{}/{}","{}/{}"'.format(adls, folder_name, join_file_name, folder_name, upload_file_name, move_folder_name, file_name))
        self.cmd('datalake store file show -n {} --path "{}/{}"'.format(adls, folder_name, join_file_name), checks=[
            JMESPathCheck('pathSuffix', join_file_name),
            JMESPathCheck('type', 'FILE'),
            JMESPathCheck('length', len(self.local_file_content) + (len(file_content)*2)),
        ])

        # download the joined file
        self.cmd('datalake store file download -n {} --destination-path "{}" --source-path "{}/{}"'.format(adls, os.path.join(self.local_folder, download_file_name), folder_name, join_file_name))
        assert os.path.getsize(os.path.join(self.local_folder, download_file_name)) == len(self.local_file_content) + (len(file_content)*2)

        # delete the file and confirm it is gone.
        self.cmd('datalake store file delete -n {} --path "{}/{}"'.format(adls, folder_name, join_file_name))
        self.cmd('datalake store file list -n {} --path "{}"'.format(adls, folder_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])

        # delete a folder that has contents and confirm it is gone.
        self.cmd('datalake store file create -n {} --path "{}" --folder'.format(adls, move_folder_name))
        self.cmd('datalake store file create -n {} --path "{}/{}"'.format(adls, move_folder_name, 'tempfile01.txt'))
        self.cmd('datalake store file delete -n {} --path "{}" --recurse'.format(adls, move_folder_name))
        # test that the path is gone
        assert not self.cmd('datalake store file test -n {} --path "{}"'.format(adls, move_folder_name))

        # test that the other folder still exists
        assert self.cmd('datalake store file test -n {} --path "{}"'.format(adls, folder_name))

        if os.path.exists(self.local_folder):
            rmtree(self.local_folder)

        # TODO once there are commands for them:
        # file expiration
        # acl management

class DataLakeStoreAccountScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeStoreAccountScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adls-mgmt')
        self.adls_name = 'cliadls1234510'
        self.location = 'eastus2'

    def test_datalake_store_account_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeStoreAccountScenarioTest, self).set_up()

    def body(self):
        rg = self.resource_group
        adls = self.adls_name
        loc = self.location
        # test create keyvault with default access policy set
        self.cmd('datalake store account create -g {} -n {} -l {}'.format(rg, adls, loc), checks=[
            JMESPathCheck('name', adls),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('encryptionState', 'Enabled'),
        ])
        self.cmd('datalake store account show -n {} -g {}'.format(adls, rg), checks=[
            JMESPathCheck('name', adls),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('encryptionState', 'Enabled'),
        ])
        self.cmd('datalake store account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', adls),
            JMESPathCheck('[0].location', loc),
            JMESPathCheck('[0].resourceGroup', rg),
        ])
        result = self.cmd('datalake store account list')
        assert isinstance(result, list)
        assert len(result) >= 1

        # test update acct
        self.cmd('datalake store account update -g {} -n {} --firewall-state Enabled --trusted-id-provider-state Enabled'.format(rg, adls))
        self.cmd('datalake store account show -n {} -g {}'.format(adls, rg), checks=[
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
        self.cmd('datalake store account firewall create -g {} -n {} --firewall-rule-name {} --start-ip-address {} --end-ip-address {}'.format(rg, adls, fw_name, start_ip, end_ip))
        self.cmd('datalake store account firewall show -g {} -n {} --firewall-rule-name {}'.format(rg, adls, fw_name), checks=[
            JMESPathCheck('name', fw_name),
            JMESPathCheck('startIpAddress', start_ip),
            JMESPathCheck('endIpAddress', end_ip),
        ])

        self.cmd('datalake store account firewall update -g {} -n {} --firewall-rule-name {} --end-ip-address {}'.format(rg, adls, fw_name, new_end_ip))
        self.cmd('datalake store account firewall show -g {} -n {} --firewall-rule-name {}'.format(rg, adls, fw_name), checks=[
            JMESPathCheck('name', fw_name),
            JMESPathCheck('startIpAddress', start_ip),
            JMESPathCheck('endIpAddress', new_end_ip),
        ])

        self.cmd('datalake store account firewall list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        self.cmd('datalake store account firewall delete -g {} -n {} --firewall-rule-name {}'.format(rg, adls, fw_name))
        self.cmd('datalake store account firewall list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])
        # test trusted id provider CRUD
        trusted_provider = 'https://sts.windows.net/9d5b43a0-804c-4c82-8791-36aca2f72342'
        new_provider = 'https://sts.windows.net/fceb709f-96f1-4c65-b06f-2541114bffb3'
        provider_name = 'testprovider01'
        self.cmd('datalake store account trusted-provider create -g {} -n {} --trusted-id-provider-name {} --id-provider {}'.format(rg, adls, provider_name, trusted_provider))
        self.cmd('datalake store account trusted-provider show -g {} -n {} --trusted-id-provider-name {}'.format(rg, adls, provider_name), checks=[
            JMESPathCheck('name', provider_name),
            JMESPathCheck('idProvider', trusted_provider),
        ])

        self.cmd('datalake store account trusted-provider update -g {} -n {} --trusted-id-provider-name {} --id-provider {}'.format(rg, adls, provider_name, new_provider))
        self.cmd('datalake store account trusted-provider show -g {} -n {} --trusted-id-provider-name {}'.format(rg, adls, provider_name), checks=[
            JMESPathCheck('name', provider_name),
            JMESPathCheck('idProvider', new_provider),
        ])

        self.cmd('datalake store account trusted-provider list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        self.cmd('datalake store account trusted-provider delete -g {} -n {} --trusted-id-provider-name {}'.format(rg, adls, provider_name))
        self.cmd('datalake store account trusted-provider list -g {} -n {}'.format(rg, adls), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])
        # test account deletion
        self.cmd('datalake store account delete -g {} -n {}'.format(rg, adls))
        self.cmd('datalake store account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])

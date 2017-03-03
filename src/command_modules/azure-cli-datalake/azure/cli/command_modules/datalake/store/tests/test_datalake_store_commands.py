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

from azure.cli.core._util import CLIError
from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck,
                                                     NoneCheck, VCRTestBase)

class DataLakeStoreFileScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeStoreFileScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adls-mgmt')
        self.adls_name = 'cliadls123450'
        self.location = 'eastus2'

    def test_datalake_store_file_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeStoreFileScenarioTest, self).set_up()
        # create ADLS account
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[0], self.location))

    def body(self):
        rg = self.resource_group
        adls = self.adls_name
        loc = self.location
        # file and folder manipulation
        # file expiration
        # permissions
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
        adls_acct = self.cmd('datalake store account create -g {} -n {} -l {}'.format(rg, adls, loc), checks=[
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
        assert type(result) == list
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

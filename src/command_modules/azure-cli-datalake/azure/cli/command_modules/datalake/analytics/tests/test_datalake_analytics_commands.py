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

class DataLakeAnalyticsCatalogScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeAnalyticsCatalogScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adla-mgmt')
        self.adls_names = ['cliadls123450', 'cliadls123451']
        self.adla_name = 'cliadla123450'
        self.wasb_name = 'cliadlwasb123450'
        self.location = 'eastus2'
        # define catalog item names

    def test_datalake_analytics_catalog_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeAnalyticsCatalogScenarioTest, self).set_up()
        # create ADLS accounts
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[0], self.location))
        self.cmd('datalake analytics account create -g {} -n {} -l {} --default-datalake-store {}'.format(self.resource_group, self.adls_names[0], self.location))
        # run job to construct catalog

    def body(self):
        rg = self.resource_group
        adla = self.adla_name
        loc = self.location
        # get all the catalog items
        # credential crud

class DataLakeAnalyticsJobScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeAnalyticsJobScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adla-mgmt')
        self.adls_names = ['cliadls123450', 'cliadls123451']
        self.adla_name = 'cliadla123450'
        self.wasb_name = 'cliadlwasb123450'
        self.location = 'eastus2'

    def test_datalake_analytics_job_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeAnalyticsJobScenarioTest, self).set_up()
        # create ADLS accounts
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[0], self.location))
        self.cmd('datalake analytics account create -g {} -n {} -l {} --default-datalake-store {}'.format(self.resource_group, self.adls_names[0], self.location))

    def body(self):
        rg = self.resource_group
        adla = self.adla_name
        loc = self.location
        # submit job
        # cancel job
        # re-submit job
        # wait for the job to finish
        # get the job
        # list all jobs

class DataLakeAnalyticsAccountScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeAnalyticsAccountScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adla-mgmt')
        self.adls_names = ['cliadls123450', 'cliadls123451']
        self.adla_name = 'cliadla123450'
        self.wasb_name = 'cliadlwasb123450'
        self.location = 'eastus2'

    def test_datalake_analytics_account_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeAnalyticsAccountScenarioTest, self).set_up()
        # create ADLS accounts
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[0], self.location))
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[1], self.location))
        self.cmd('storage account create -g {} -n {} -l {} --sku Standard_GRS'.format(self.resource_group, self.wasb_name, self.location))
        result = self.cmd('storage account keys list -g {} -n {}'.format(self.resource_group, self.wasb_name))
        self.wasb_key = result[0]['value']

    def body(self):
        rg = self.resource_group
        adls1 = self.adls_names[0]
        adls2 = self.adls_names[1]
        adla = self.adla_name
        loc = self.location
        # test create keyvault with default access policy set
        adla_acct = self.cmd('datalake analytics account create -g {} -n {} -l {} --default-datalake-store {}'.format(rg, adla, loc, adls1), checks=[
            JMESPathCheck('name', adla),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('defaultDataLakeStoreAccount', adls1),
            JMESPathCheck('type(dataLakeStoreAccounts)', 'array'),
            JMESPathCheck('length(dataLakeStoreAccounts)', 1),
            JMESPathCheck('maxDegreeOfParallelism', 30),
            JMESPathCheck('maxJobCount', 3),
            JMESPathCheck('queryStoreRetention', 30),
        ])
        self.cmd('datalake analytics account show -n {} -g {}'.format(adla, rg), checks=[
            JMESPathCheck('name', adla),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('defaultDataLakeStoreAccount', adls1),
            JMESPathCheck('type(dataLakeStoreAccounts)', 'array'),
            JMESPathCheck('length(dataLakeStoreAccounts)', 1),
            JMESPathCheck('maxDegreeOfParallelism', 30),
            JMESPathCheck('maxJobCount', 3),
            JMESPathCheck('queryStoreRetention', 30),
        ])
        self.cmd('datalake analytics account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', adla),
            JMESPathCheck('[0].location', loc),
            JMESPathCheck('[0].resourceGroup', rg),
        ])
        result = self.cmd('datalake analytics account list')
        assert type(result) == list
        assert len(result) >= 1
        
        # test update acct
        self.cmd('datalake analytics account update -g {} -n {} --firewall-state Enabled --max-degree-of-parallelism 15 --max-job-count 2 --query-store-retention 15 --allow-azure-ips Enabled'.format(rg, adla))
        self.cmd('datalake analytics account show -n {} -g {}'.format(adla, rg), checks=[
            JMESPathCheck('name', adla),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('defaultDataLakeStoreAccount', adls1),
            JMESPathCheck('type(dataLakeStoreAccounts)', 'array'),
            JMESPathCheck('length(dataLakeStoreAccounts)', 1),
            JMESPathCheck('maxDegreeOfParallelism', 15),
            JMESPathCheck('maxJobCount', 2),
            JMESPathCheck('queryStoreRetention', 15)
            # TODO: add validation for firewall rules once they are
            # live in production.
        ])

        # test adls acct add get, delete
        self.cmd('datalake analytics account datalake-store add -g {} -n {} --data-lake-store-account-name {}'.format(rg, adla, adls2))
        self.cmd('datalake analytics account datalake-store show -g {} -n {} --data-lake-store-account-name {}'.format(rg, adla, adls2), checks=[
            JMESPathCheck('name', adls2)
        ])
        self.cmd('datalake analytics account datalake-store list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 2),
        ])
        self.cmd('datalake analytics account datalake-store delete -g {} -n {} --data-lake-store-account-name {}'.format(rg, adla, adls2))
        self.cmd('datalake analytics account datalake-store list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        # test wasb add, get delete
        self.cmd('datalake analytics account blob add -g {} -n {} --storage-account-name {} --access-key {}'.format(rg, adla, self.wasb_name, self.wasb_key))
        self.cmd('datalake analytics account blob show -g {} -n {} --storage-account-name {}'.format(rg, adla, self.wasb_name), checks=[
            JMESPathCheck('name', self.wasb_name)
        ])
        self.cmd('datalake analytics account blob list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
        ])
        self.cmd('datalake analytics account blob delete -g {} -n {} --storage-account-name {}'.format(rg, adla, self.wasb_name))
        self.cmd('datalake analytics account blob list -g {} -n {}'.format(rg, adla), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])
        # test account deletion
        self.cmd('datalake analytics account delete -g {} -n {}'.format(rg, adla))
        self.cmd('datalake analytics account list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 0),
        ])
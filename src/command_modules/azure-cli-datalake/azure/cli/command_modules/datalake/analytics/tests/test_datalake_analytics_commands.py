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

class DataLakeAnalyticsAccountScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(DataLakeAnalyticsAccountScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-adla-mgmt')
        self.adls_names = ['cliadls123450', 'cliadls123451']
        self.adla_name = 'cliadla123450'
        self.location = 'eastus2'

    def test_datalake_analytics_account_mgmt(self):
        self.execute()

    def set_up(self):
        super(DataLakeAnalyticsAccountScenarioTest, self).set_up()
        # create ADLS accounts
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[0], self.location))
        self.cmd('datalake store account create -g {} -n {} -l {} --disable-encryption'.format(self.resource_group, self.adls_names[1], self.location))

    def body(self):
        rg = self.resource_group
        adls1 = self.adls_names[0]
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
        self.cmd('datalake analytics account list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', adla),
            JMESPathCheck('[0].location', loc),
            JMESPathCheck('[0].resourceGroup', rg),
        ])

        # test update acct
        # test adls acct add get, delete
        # test wasb add, get delete
        # test account deletion
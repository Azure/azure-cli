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

from azure.cli.command_modules.keyvault._params import secret_encoding_values

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

def _before_record_response(response):
    # ignore any 401 responses during playback
    if response['status']['code'] == 401:
        response = None
    return response

class BatchMgmtAccountScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(BatchMgmtAccountScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli-test-batch-mgmt'
        self.account_names = ['cli-batch-12345-0',
                               'cli-batch-12345-1',
                               'cli-batch-12345-2',
                               'cli-batch-12345-3']
        self.location = 'westus'

    def test_account_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        name = self.account_names[0]
        loc = self.location
        # test create account with default set
        account = self.cmd('batch account create -g {} -n {} -l {}'.format(rg, name, loc), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg)
        ])

        # test batch account delete
        self.cmd('batch account delete -n {}'.format(name))
        self.cmd('batch account list -g {}'.format(rg), checks=NoneCheck())


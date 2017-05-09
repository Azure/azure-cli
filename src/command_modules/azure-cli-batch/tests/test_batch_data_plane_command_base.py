# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk.vcr_test_base import VCRTestBase


class BatchDataPlaneTestBase(VCRTestBase):
    # pylint:disable=too-few-public-methods

    def __init__(self, test_file, test_method):
        super(BatchDataPlaneTestBase, self).__init__(test_file, test_method)
        self.account_name = 'clitest1'
        if not self.playback:
            self.account_key = os.environ['AZURE_BATCH_ACCESS_KEY']
        else:
            self.account_key = 'ZmFrZV9hY29jdW50X2tleQ=='
        self.account_endpoint = 'https://clitest1.uksouth.batch.azure.com/'

    def cmd(self, command, checks=None, allowed_exceptions=None,
            debug=False):
        command = '{} --account-name {} --account-key "{}" --account-endpoint {}'.\
            format(command, self.account_name, self.account_key, self.account_endpoint)
        return super(BatchDataPlaneTestBase, self).cmd(command, checks, allowed_exceptions, debug)

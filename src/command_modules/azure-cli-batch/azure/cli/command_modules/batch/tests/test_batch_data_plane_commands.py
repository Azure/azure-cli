# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core.test_utils.vcr_test_base import (VCRTestBase, JMESPathCheck)

class BatchCertificateScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(BatchCertificateScenarioTest, self).__init__(__file__, test_method)
        self.create_cert_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  'data',
                                                  'batchtest.cer')
        self.cert_thumbprint = '59833fd835f827e9ec693a4c82435a6360cc6271'
        self.account_name = 'test1'
        if not self.playback:
            self.account_key = os.environ['AZURE_BATCH_ACCESS_KEY']
        else:
            self.account_key = 'non null default value'
        self.account_endpoint = 'https://test1.westus.batch.azure.com/'

    def test_batch_certificate_cmd(self):
        self.execute()

    def body(self):
        # test create certificate with default set
        self.cmd('batch certificate create --thumbprint {} '
                 '--thumbprint-algorithm sha1 --cert-file "{}"'.
                 format(self.cert_thumbprint, self.create_cert_file_path),
                 checks=[
                     JMESPathCheck('thumbprint', self.cert_thumbprint),
                     JMESPathCheck('thumbprintAlgorithm', 'sha1'),
                     JMESPathCheck('state', 'active')
                     ])

        # test create account with default set
        self.cmd('batch certificate list', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].thumbprint', self.cert_thumbprint),
        ])

        self.cmd("batch certificate delete --thumbprint {} --thumbprint-algorithm sha1 --force".
                 format(self.cert_thumbprint))

        self.cmd('batch certificate show --thumbprint {} --thumbprint-algorithm sha1'.
                 format(self.cert_thumbprint),
                 checks=[
                     JMESPathCheck('thumbprint', self.cert_thumbprint),
                     JMESPathCheck('thumbprintAlgorithm', 'sha1'),
                     JMESPathCheck('state', 'deleting')
                     ])

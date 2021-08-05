# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long,too-many-statements

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest

from OpenSSL import crypto, SSL
from os.path import exists, join
from azure.cli.command_modules.iot.tests.latest._test_utils import _create_test_cert, _delete_test_cert, _create_verification_cert
import random
import unittest

VERIFICATION_FILE = "verify.cer"
CERT_FILE = "testcert.cer"
KEY_FILE = "testkey.pvk"
MAX_INT = 9223372036854775807


class IotHubCertificateTest(ScenarioTest):
    def __init__(self, test_method):
        super(IotHubCertificateTest, self).__init__('test_certificate_lifecycle')
        self.hub_name = 'iot-hub-for-cert-test'
        _create_test_cert(CERT_FILE, KEY_FILE, self.create_random_name(prefix='TESTCERT', length=24), 3, random.randint(0, MAX_INT))

    def __del__(self):
        _delete_test_cert(CERT_FILE, KEY_FILE, VERIFICATION_FILE)

    @unittest.skip("Need to check this")
    @ResourceGroupPreparer()
    def test_certificate_lifecycle(self, resource_group):
        hub = self._create_test_hub(resource_group)
        cert_name = self.create_random_name(prefix='certificate-', length=48)

        # Create certificate
        self.cmd('iot hub certificate create --hub-name {0} -g {1} -n {2} -p {3}'.format(hub, resource_group, cert_name, CERT_FILE),
                 checks=[self.check('name', cert_name),
                         self.check('properties.isVerified', False)])

        # List certificates
        output = self.cmd('iot hub certificate list --hub-name {0} -g {1}'.format(hub, resource_group),
                          checks=[self.check('length(value)', 1),
                                  self.check('value[0].name', cert_name),
                                  self.check('value[0].properties.isVerified', False)]).get_output_in_json()
        assert len(output['value']) == 1

        # Get certificate
        etag = self.cmd('iot hub certificate show --hub-name {0} -g {1} -n {2}'.format(hub, resource_group, cert_name),
                        checks=[self.check('name', cert_name),
                                self.check('properties.isVerified', False)]).get_output_in_json()['etag']

        # Generate verification code
        output = self.cmd('iot hub certificate generate-verification-code --hub-name {0} -g {1} -n {2} --etag {3}'.format(hub, resource_group, cert_name, etag),
                          checks=[self.check('name', cert_name)]).get_output_in_json()

        assert 'verificationCode' in output['properties']

        verification_code = output['properties']['verificationCode']
        etag = output['etag']

        _create_verification_cert(CERT_FILE, KEY_FILE, VERIFICATION_FILE, verification_code, 3, random.randint(0, MAX_INT))

        # Verify certificate
        etag = self.cmd('iot hub certificate verify --hub-name {0} -g {1} -n {2} -p {3} --etag {4}'.format(hub, resource_group, cert_name, VERIFICATION_FILE, etag),
                        checks=[self.check('name', cert_name),
                                self.check('properties.isVerified', True)]).get_output_in_json()['etag']

        # Delete certificate
        self.cmd('iot hub certificate delete --hub-name {0} -g {1} -n {2} --etag {3}'.format(hub, resource_group, cert_name, etag))

    def _create_test_hub(self, resource_group):
        hub = self.create_random_name(prefix='iot-hub-for-cert-test', length=48)

        self.cmd('iot hub create -n {0} -g {1} --sku S1'.format(hub, resource_group),
                 checks=[self.check('resourcegroup', resource_group),
                         self.check('name', hub),
                         self.check('sku.name', 'S1')])

        return hub

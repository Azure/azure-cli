# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long,too-many-statements

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest

from azure.cli.command_modules.iot.tests.latest._test_utils import (
    _create_test_cert, _delete_test_cert, _create_verification_cert, _create_fake_chain_cert
)
import random

VERIFICATION_FILE = "verify.cer"
CERT_FILE = "testcert.cer"
KEY_FILE = "testkey.pvk"
CHAIN_FILE = "testcert-chain.pem"
MAX_INT = 9223372036854775807


class IotHubCertificateTest(ScenarioTest):
    def __init__(self, test_method):
        super(IotHubCertificateTest, self).__init__('test_certificate_lifecycle')
        self.hub_name = 'iot-hub-for-cert-test'
        _create_test_cert(CERT_FILE, KEY_FILE, self.create_random_name(prefix='TESTCERT', length=24), 3, random.randint(0, MAX_INT))
        _create_fake_chain_cert(CERT_FILE, CHAIN_FILE)

    def __del__(self):
        _delete_test_cert([CERT_FILE, KEY_FILE, VERIFICATION_FILE, CHAIN_FILE])

    @ResourceGroupPreparer()
    def test_certificate_lifecycle(self, resource_group):
        hub = self._create_test_hub(resource_group)
        cert_name = self.create_random_name(prefix='certificate-', length=48)
        cert_name_verified = self.create_random_name(prefix='verified-certificate-', length=48)
        chain_name = self.create_random_name(prefix='certificate-', length=48)

        # Create certificate
        self.cmd('iot hub certificate create --hub-name {0} -g {1} -n {2} -p {3}'.format(hub, resource_group, cert_name, CERT_FILE),
                 checks=[self.check('name', cert_name),
                         self.check('properties.isVerified', False)])

        # Create verified certificate
        etag_verified = self.cmd('iot hub certificate create --hub-name {0} -g {1} -n {2} -p {3} --verified'.format(hub, resource_group, cert_name_verified, CERT_FILE),
                                 checks=[self.check('name', cert_name_verified),
                                         self.check('properties.isVerified', True)]).get_output_in_json()['etag']

        # List certificates
        output = self.cmd('iot hub certificate list --hub-name {0} -g {1}'.format(hub, resource_group),
                          checks=[self.check('length(value)', 2),
                                  self.check('value[0].name', cert_name),
                                  self.check('value[0].properties.isVerified', False),
                                  self.check('value[1].name', cert_name_verified),
                                  self.check('value[1].properties.isVerified', True)]).get_output_in_json()
        assert len(output['value']) == 2

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

        # Create certificate from a chain - test how certificate is encoded in the service call
        self.cmd('iot hub certificate create --hub-name {0} -g {1} -n {2} -p {3}'.format(hub, resource_group, chain_name, CHAIN_FILE),
                 checks=[self.check('name', chain_name),
                         self.check('properties.isVerified', False)])

        # Delete certificates
        self.cmd('iot hub certificate delete --hub-name {0} -g {1} -n {2} --etag {3}'.format(hub, resource_group, cert_name, etag))
        self.cmd('iot hub certificate delete --hub-name {0} -g {1} -n {2} --etag {3}'.format(hub, resource_group, cert_name_verified, etag_verified))
        self.cmd('iot hub certificate delete --hub-name {0} -g {1} -n {2} --etag *'.format(hub, resource_group, chain_name))

    def _create_test_hub(self, resource_group):
        hub = self.create_random_name(prefix='iot-hub-for-cert-test', length=48)

        self.cmd('iot hub create -n {0} -g {1} --sku S1'.format(hub, resource_group),
                 checks=[self.check('resourcegroup', resource_group),
                         self.check('name', hub),
                         self.check('sku.name', 'S1')])

        return hub

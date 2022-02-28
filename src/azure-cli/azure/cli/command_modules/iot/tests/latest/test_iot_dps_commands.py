# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

from azure.cli.command_modules.iot.tests.latest._test_utils import _create_test_cert, _delete_test_cert, _create_verification_cert
from azure.cli.command_modules.iot.tests.latest.recording_processors import KeyReplacer
from azure.core.exceptions import HttpResponseError
import random


class IoTDpsTest(ScenarioTest):

    def __init__(self, method_name):
        super(IoTDpsTest, self).__init__(
            method_name, recording_processors=[KeyReplacer()]
        )

    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_dps_lifecycle(self, group_name, group_location):
        dps_name = self.create_random_name('dps', 20)

        # Create DPS
        tags = "key1=value1 key2=value2"
        self.cmd('az iot dps create -g {} -n {} --tags {}'.format(group_name, dps_name, tags),
                 checks=[self.check('name', dps_name),
                         self.check('location', group_location),
                         self.check('tags', {'key1': 'value1', 'key2': 'value2'})])

        # List DPS
        self.cmd('az iot dps list -g {}'.format(group_name), checks=[
            self.check('length([*])', 1),
            self.check('[0].name', dps_name),
            self.check('[0].location', group_location)
        ])

        # Get DPS
        self.cmd('az iot dps show -g {} -n {}'.format(group_name, dps_name), checks=[
            self.check('name', dps_name),
            self.check('location', group_location)
        ])

        property_to_update = 'properties.allocationPolicy'
        updated_value = 'GeoLatency'
        updated_tags = "key3=value3"
        # Update DPS
        updated_dps = self.cmd('az iot dps update -g {} -n {} --tags {} --set {}="{}"'
                               .format(group_name, dps_name, updated_tags, property_to_update, updated_value),
                               checks=[self.check('name', dps_name),
                                       self.check('location', group_location),
                                       self.check(property_to_update, updated_value),
                                       self.check('tags', {'key3': 'value3'})])

        # Update DPS with removing tags
        updated_dps = self.cmd('az iot dps update -g {} -n {} --tags ""'
                               .format(group_name, dps_name)).get_output_in_json()

        assert len(updated_dps['tags']) == 0

        # Test DPS Access Policy Lifecycle
        policy_name = self.create_random_name('policy', 20)
        right = 'EnrollmentRead'
        new_right = 'EnrollmentWrite'

        # Create access policy
        self.cmd('az iot dps policy create -g {} --dps-name {} --pn {} -r {}'.format(group_name, dps_name, policy_name, right), checks=[
            self.check('keyName', policy_name),
            self.check('rights', right)
        ])

        # List access policy
        self.cmd('az iot dps policy list -g {} --dps-name {}'.format(group_name, dps_name), checks=[
            self.check('length([*])', 2),
            self.check('[1].keyName', policy_name),
            self.check('[1].rights', right)
        ])

        # Get access policy
        self.cmd('az iot dps policy show -g {} --dps-name {} --pn {}'.format(group_name, dps_name, policy_name), checks=[
            self.check('keyName', policy_name),
            self.check('rights', right)
        ])

        # Create update policy
        self.cmd('az iot dps policy update -g {} --dps-name {} --pn {} -r {}'.format(group_name, dps_name, policy_name, new_right),
                 checks=[
                     self.check('keyName', policy_name),
                     self.check('rights', new_right)
        ])

        # Delete policy
        self.cmd('az iot dps policy delete -g {} --dps-name {} --pn {}'.format(group_name, dps_name, policy_name))

        # Delete DPS
        self.cmd('az iot dps delete -g {} -n {}'.format(group_name, dps_name))

        # Data Residency tests
        dr_dps_name = self.create_random_name('dps-dr', 20)

        # Data residency not enabled in this region
        with self.assertRaises(HttpResponseError):
            self.cmd('az iot dps create -g {} -n {} --edr'.format(group_name, dr_dps_name))

        # Successfully create in this region
        self.cmd('az iot dps create -g {} -n {} --location southeastasia --edr'.format(group_name, dr_dps_name),
                 checks=[self.check('name', dr_dps_name),
                         self.check('location', 'southeastasia'),
                         self.check('properties.enableDataResidency', True)])
        self.cmd('az iot dps delete -g {} -n {}'.format(group_name, dr_dps_name))


    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_dps_certificate_lifecycle(self, group_name, group_location):
        dps_name = self.create_random_name('dps', 20)

        # Create DPS
        self.cmd('az iot dps create -g {} -n {}'.format(group_name, dps_name),
                 checks=[self.check('name', dps_name),
                         self.check('location', group_location)])

        # Test DPS Certificate Lifecycle
        cert_name = self.create_random_name('certificate', 20)
        cert_name_verified = self.create_random_name(prefix='verified-certificate-', length=48)

        # Set up cert file for test
        verification_file = "verify.cer"
        cert_file = "testcert.cer"
        key_file = "testkey.pvk"
        max_int = 9223372036854775807
        _create_test_cert(cert_file, key_file, self.create_random_name(prefix='TESTCERT', length=24), 3, random.randint(0, max_int))

        # Create certificates
        self.cmd('az iot dps certificate create --dps-name {} -g {} --name {} -p {}'.format(dps_name, group_name, cert_name, cert_file),
                 checks=[
                     self.check('name', cert_name),
                     self.check('properties.isVerified', False)
        ])

        etag_verified = self.cmd('az iot dps certificate create --dps-name {} -g {} --name {} -p {} --verified'.format(dps_name, group_name, cert_name_verified, cert_file),
                                 checks=[
                                    self.check('name', cert_name_verified),
                                    self.check('properties.isVerified', True)
        ]).get_output_in_json()['etag']

        # List certificates
        cert_list = self.cmd('az iot dps certificate list --dps-name {} -g {}'.format(dps_name, group_name),
                             checks=[self.check('length(value)', 2)]
                            ).get_output_in_json()['value']

        for cert in cert_list:
            assert cert['name'] == cert_name_verified if cert['properties']['isVerified'] else cert_name

        assert cert_list[0]['name'] != cert_list[1]['name']

        # Get certificate
        etag = self.cmd('az iot dps certificate show --dps-name {} -g {} --name {}'.format(dps_name, group_name, cert_name), checks=[
            self.check('name', cert_name),
            self.check('properties.isVerified', False)
        ]).get_output_in_json()['etag']

        # Update certificate
        etag = self.cmd('az iot dps certificate update --dps-name {} -g {} --name {} -p {} --etag {}'
                        .format(dps_name, group_name, cert_name, cert_file, etag),
                        checks=[
                            self.check('name', cert_name),
                            self.check('properties.isVerified', False)
                        ]).get_output_in_json()['etag']

        # Generate verification code
        output = self.cmd('az iot dps certificate generate-verification-code --dps-name {} -g {} -n {} --etag {}'
                          .format(dps_name, group_name, cert_name, etag),
                          checks=[
                              self.check('name', cert_name),
                              self.check('properties.isVerified', False)
                          ]).get_output_in_json()

        verification_code = output['properties']['verificationCode']
        etag = output['etag']
        _create_verification_cert(cert_file, key_file, verification_file, verification_code, 3, random.randint(0, max_int))

        # Verify certificate
        etag = self.cmd('az iot dps certificate verify --dps-name {} -g {} -n {} -p {} --etag {}'.format(dps_name, group_name, cert_name, verification_file, etag),
                        checks=[
                            self.check('name', cert_name),
                            self.check('properties.isVerified', True)
        ]).get_output_in_json()['etag']

        # Delete certificates
        self.cmd('az iot dps certificate delete --dps-name {} -g {} --name {} --etag {}'.format(dps_name, group_name, cert_name, etag))
        self.cmd('az iot dps certificate delete --dps-name {} -g {} --name {} --etag {}'.format(dps_name, group_name, cert_name_verified, etag_verified))

        _delete_test_cert(cert_file, key_file, verification_file)

        # Delete DPS
        self.cmd('az iot dps delete -g {} -n {}'.format(group_name, dps_name))


    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_dps_linked_hub_lifecycle(self, group_name, group_location):
        dps_name = self.create_random_name('dps', 20)
        hub_name = self.create_random_name('iot', 20)
        hub_host_name = '{}.azure-devices.net'.format(hub_name)
        key_name = self.create_random_name('key', 20)
        permission = 'RegistryWrite'

        # Create DPS
        self.cmd('az iot dps create -g {} -n {}'.format(group_name, dps_name),
                 checks=[self.check('name', dps_name),
                         self.check('location', group_location)])

        # Create and set up Hub
        self.cmd('az iot hub create -n {} -g {} --sku S1'.format(hub_name, group_name),
                 checks=[self.check('resourcegroup', group_name),
                         self.check('name', hub_name),
                         self.check('sku.name', 'S1')])

        self.cmd('az iot hub policy create --hub-name {} -n {} --permissions {}'.format(hub_name, key_name, permission))

        # Create linked-hub fails if there is no hub name or connection string
        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --l {}'
                 .format(dps_name, group_name, group_location),
                 expect_failure=True)

        # Create linked-hub fails with a fake connection string
        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --connection-string {}'
                 .format(dps_name, group_name, "Test"),
                 expect_failure=True)

        # Create linked-hub with only hub name
        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --hub-name {}'
                 .format(dps_name, group_name, hub_name))
        self.cmd('az iot dps linked-hub delete --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_host_name))

        # Create linked-hub with hub name, resource group, location
        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --hub-name {} --hrg {} --l {}'
                 .format(dps_name, group_name, hub_name, group_name, group_location))
        self.cmd('az iot dps linked-hub delete --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_name))

        # Create linked-hub using only connection string
        connection_string = self._show_hub_connection_string(hub_name, group_name)
        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --connection-string {}'
                 .format(dps_name, group_name, connection_string))
        self.cmd('az iot dps linked-hub delete --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_name))

        # Create linked-hub using only connection string in lower case
        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --connection-string {}'
                 .format(dps_name, group_name, connection_string.lower()))
        self.cmd('az iot dps linked-hub delete --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_name))

        # Create linked-hub using connection string and location
        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --connection-string {} -l {}'
                 .format(dps_name, group_name, connection_string, group_location))

        self.cmd('az iot dps linked-hub list --dps-name {} -g {}'.format(dps_name, group_name), checks=[
            self.check('length([*])', 1),
            self.check('[0].name', '{}.azure-devices.net'.format(hub_name)),
            self.check('[0].location', group_location)
        ])

        self.cmd('az iot dps linked-hub show --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_host_name), checks=[
            self.check('name', hub_host_name),
            self.check('location', group_location)
        ])

        # Linked hub should support host name and hub name
        self.cmd('az iot dps linked-hub show --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_name), checks=[
            self.check('name', hub_host_name),
            self.check('location', group_location)
        ])

        allocationWeight = 10
        applyAllocationPolicy = True
        self.cmd('az iot dps linked-hub update --dps-name {} -g {} --linked-hub {} --allocation-weight {} --apply-allocation-policy {}'
                 .format(dps_name, group_name, hub_host_name, allocationWeight, applyAllocationPolicy))

        self.cmd('az iot dps linked-hub show --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_host_name), checks=[
            self.check('name', hub_host_name),
            self.check('location', group_location),
            self.check('allocationWeight', allocationWeight),
            self.check('applyAllocationPolicy', applyAllocationPolicy)
        ])

        self.cmd('az iot dps linked-hub delete --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_host_name))

        # Delete DPS and Hub
        self.cmd('az iot dps delete -g {} -n {}'.format(group_name, dps_name))
        self.cmd('az iot hub delete -n {} -g {}'.format(hub_name, group_name))

    def _get_hub_policy_primary_key(self, hub_name, key_name):
        output = self.cmd('az iot hub policy show --hub-name {} -n {}'.format(hub_name, key_name))
        return output.get_output_in_json()['primaryKey']

    def _show_hub_connection_string(self, hub_name, group_name):
        output = self.cmd('az iot hub show-connection-string --name {} -g {}'.format(hub_name, group_name))
        return output.get_output_in_json()['connectionString']

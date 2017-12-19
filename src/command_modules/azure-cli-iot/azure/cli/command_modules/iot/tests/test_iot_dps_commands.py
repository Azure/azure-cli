# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

from ._test_utils import _create_test_cert, _delete_test_cert, _create_verification_cert
import random


class IoTDpsTest(ScenarioTest):

    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_dps_lifecycle(self, group_name, group_location):
        name = self.create_random_name('dps', 20)

        # Create DPS
        self.cmd('az iot dps create -g {} -n {}'.format(group_name, name), checks=[
            self.check('name', name),
            self.check('location', group_location)
        ])

        # List DPS
        self.cmd('az iot dps list -g {}'.format(group_name), checks=[
            self.check('length([*])', 1),
            self.check('[0].name', name),
            self.check('[0].location', group_location)
        ])

        # Get DPS
        self.cmd('az iot dps show -g {} -n {}'.format(group_name, name), checks=[
            self.check('name', name),
            self.check('location', group_location)
        ])

        property_to_update = 'properties.allocationPolicy'
        updated_value = 'GeoLatency'
        # Update DPS
        self.cmd('az iot dps update -g {} -n {} --set {}="{}"'.format(group_name, name, property_to_update, updated_value), checks=[
            self.check('name', name),
            self.check('location', group_location),
            self.check(property_to_update, updated_value)
        ])

        # Delete DPS
        self.cmd('az iot dps delete -g {} -n {}'.format(group_name, name))

    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_dps_access_policy_lifecycle(self, group_name, group_location):
        policy_name = self.create_random_name('policy', 20)
        right = 'EnrollmentRead'
        new_right = 'EnrollmentWrite'

        # Set up a provisioning service
        dps_name = self._create_test_dps(group_name, group_location)

        # Create access policy
        self.cmd('az iot dps access-policy create -g {} --dps-name {} -n {} -r {}'.format(group_name, dps_name, policy_name, right), checks=[
            self.check('keyName', policy_name),
            self.check('rights', right)
        ])

        # List access policy
        self.cmd('az iot dps access-policy list -g {} --dps-name {}'.format(group_name, dps_name), checks=[
            self.check('length([*])', 2),
            self.check('[1].keyName', policy_name),
            self.check('[1].rights', right)
        ])

        # Get access policy
        self.cmd('az iot dps access-policy show -g {} --dps-name {} -n {}'.format(group_name, dps_name, policy_name), checks=[
            self.check('keyName', policy_name),
            self.check('rights', right)
        ])

        # Create update policy
        self.cmd('az iot dps access-policy update -g {} --dps-name {} -n {} -r {}'.format(group_name, dps_name, policy_name, new_right),
                 checks=[
                     self.check('keyName', policy_name),
                     self.check('rights', new_right)
        ])

        # Delete access policy
        self.cmd('az iot dps access-policy delete -g {} --dps-name {} -n {}'.format(group_name, dps_name, policy_name), checks=[
            self.check('length([*])', 1)
        ])

        # Tear down the provisioning service
        self._delete_test_dps(dps_name, group_name)

    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_dps_linked_hub_lifecycle(self, group_name, group_location):
        key_name = self.create_random_name('key', 20)
        permission = 'RegistryWrite'

        # Set up a hub with a policy to be link
        hub_name = self._create_test_hub(group_name)
        hub_host_name = '{}.azure-devices.net'.format(hub_name)

        self.cmd('az iot hub policy create --hub-name {} -n {} --permissions {}'.format(hub_name, key_name, permission))

        primary_key = self._get_hub_policy_primary_key(hub_name, key_name)
        connection_string = 'HostName={};SharedAccessKeyName={};SharedAccessKey={}'.format(hub_host_name, key_name, primary_key)

        # Set up a provisioning service
        dps_name = self._create_test_dps(group_name, group_location)

        self.cmd('az iot dps linked-hub create --dps-name {} -g {} --connection-string {} -l {}'
                 .format(dps_name, group_name, connection_string, group_location))
        # Service bug here preventing us doing the self.check:
        # 1. "create" returns an array instead of the object
        # 2. "create" returns an empty array sometimes

        self.cmd('az iot dps linked-hub list --dps-name {} -g {}'.format(dps_name, group_name), checks=[
            self.check('length([*])', 1),
            self.check('[0].name', '{}.azure-devices.net'.format(hub_name)),
            self.check('[0].location', group_location)
        ])

        self.cmd('az iot dps linked-hub show --dps-name {} -g {} --linked-hub {}'.format(dps_name, group_name, hub_host_name), checks=[
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

        # Tear down the provisioning service
        self._delete_test_dps(dps_name, group_name)

        # Tear down the hub
        self._delete_test_hub(hub_name)

    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_dps_certificate_lifecycle(self, group_name, group_location):
        # Set up a provisioning service
        dps_name = self._create_test_dps(group_name, group_location)
        cert_name = self.create_random_name('certificate', 20)

        # Set up cert file for test
        verification_file = "verify.cer"
        cert_file = "testcert.cer"
        key_file = "testkey.pvk"
        max_int = 9223372036854775807
        _create_test_cert(cert_file, key_file, self.create_random_name(prefix='TESTCERT', length=24), 3, random.randint(0, max_int))

        # Create certificate
        self.cmd('az iot dps certificate create --dps-name {} -g {} --name {} -p {}'.format(dps_name, group_name, cert_name, cert_file),
                 checks=[
                     self.check('name', cert_name),
                     self.check('properties.isVerified', False)
        ])

        # List certificates
        self.cmd('az iot dps certificate list --dps-name {} -g {}'.format(dps_name, group_name), checks=[
            self.check('length(@)', 1),
        ])

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
        etag = self.cmd('iot dps certificate verify --dps-name {} -g {} -n {} -p {} --etag {}'.format(dps_name, group_name, cert_name, verification_file, etag),
                        checks=[
                            self.check('name', cert_name),
                            self.check('properties.isVerified', True)
        ]).get_output_in_json()['etag']

        # Delete certificate
        self.cmd('az iot dps certificate delete --dps-name {} -g {} --name {} --etag {}'.format(dps_name, group_name, cert_name, etag))

        # Tear down the provisioning service
        self._delete_test_dps(dps_name, group_name)
        _delete_test_cert(cert_file, key_file, verification_file)

    def _create_test_dps(self, group_name, group_location):
        dps_name = dps_name = self.create_random_name('iot-dps-for-dps-test', length=48)
        self.cmd('az iot dps create -g {} -n {}'.format(group_name, dps_name), checks=[
            self.check('name', dps_name),
            self.check('location', group_location)
        ])
        return dps_name

    def _create_test_hub(self, group_name):
        hub_name = self.create_random_name(prefix='iot-hub-for-dps-test', length=48)
        self.cmd('az iot hub create -n {} -g {} --sku S1'.format(hub_name, group_name), checks=[
            self.check('resourceGroup', group_name),
            self.check('name', hub_name),
            self.check('sku.name', 'S1')
        ])
        return hub_name

    def _delete_test_dps(self, dps_name, group_name):
        self.cmd('az iot dps delete -g {} -n {}'.format(group_name, dps_name))

    def _delete_test_hub(self, hub_name):
        self.cmd('az iot hub delete -n {}'.format(hub_name))

    def _get_hub_policy_primary_key(self, hub_name, key_name):
        output = self.cmd('az iot hub policy show --hub-name {} -n {}'.format(hub_name, key_name))
        return output.get_output_in_json()['primaryKey']

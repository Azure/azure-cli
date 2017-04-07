# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import unittest

from azure.cli.core.test_utils.vcr_test_base import ResourceGroupVCRTestBase, JMESPathCheck

# pylint: disable=line-too-long


class AzureContainerServiceScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(AzureContainerServiceScenarioTest, self).__init__(__file__, test_method,
                                                                resource_group='cliTestRg_Acs')
        self.pub_ssh_filename = None

    def test_acs_create_update(self):
        self.execute()

    def body(self):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)

        acs_name = 'acstest123'
        dns_prefix = 'myacs1234'

        # create
        pathname = pathname.replace('\\', '\\\\')
        print('acs create -g {} -n {} --dns-prefix {} --ssh-key-value {}'.format(
            self.resource_group, acs_name, dns_prefix, pathname))
        self.cmd('acs create -g {} -n {} --dns-prefix {} --ssh-key-value {}'.format(
            self.resource_group, acs_name, dns_prefix, pathname), checks=[
            JMESPathCheck('properties.outputs.masterFQDN.value',
                          '{}mgmt.{}.cloudapp.azure.com'.format(dns_prefix, self.location)),
            JMESPathCheck('properties.outputs.agentFQDN.value',
                          '{}agents.{}.cloudapp.azure.com'.format(dns_prefix, self.location))
        ])

        # show
        self.cmd('acs show -g {} -n {}'.format(self.resource_group, acs_name), checks=[
            JMESPathCheck('agentPoolProfiles[0].count', 3),
            JMESPathCheck('agentPoolProfiles[0].vmSize', 'Standard_D2_v2'),
            JMESPathCheck('masterProfile.dnsPrefix', dns_prefix + 'mgmt'),
            JMESPathCheck('orchestratorProfile.orchestratorType', 'DCOS'),
            JMESPathCheck('name', acs_name),
        ])

        # scale-up
        self.cmd('acs scale -g {} -n {} --new-agent-count 5'.format(self.resource_group, acs_name), checks=[
            JMESPathCheck('agentPoolProfiles[0].count', 5),
        ])
        # show again
        self.cmd('acs show -g {} -n {}'.format(self.resource_group, acs_name), checks=[
            JMESPathCheck('agentPoolProfiles[0].count', 5),
        ])

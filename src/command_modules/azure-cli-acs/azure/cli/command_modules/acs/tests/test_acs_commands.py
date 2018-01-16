# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer,
                               RoleBasedServicePrincipalPreparer)

# flake8: noqa

class AzureContainerServiceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_acs_create_default_service(self, resource_group, resource_group_location):
        ssh_pubkey_file = self.generate_ssh_keys().replace('\\', '\\\\')
        acs_name = self.create_random_name('cliacstest', 16)
        dns_prefix = self.create_random_name('cliacsdns', 16)

        # create
        create_cmd = 'acs create -g {} -n {} --dns-prefix {} --ssh-key-value {} -l {}'
        self.cmd(create_cmd.format(resource_group, acs_name, dns_prefix, ssh_pubkey_file, resource_group_location),
                 checks=[self.check('properties.outputs.masterFQDN.value',
                                       '{}mgmt.{}.cloudapp.azure.com'.format(dns_prefix, resource_group_location)),
                         self.check('properties.outputs.agentFQDN.value',
                                       '{}agent.{}.cloudapp.azure.com'.format(dns_prefix, resource_group_location))])

        # show
        self.cmd('acs show -g {} -n {}'.format(resource_group, acs_name), checks=[
            self.check('agentPoolProfiles[0].count', 3),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D2_v2'),
            self.check('masterProfile.dnsPrefix', dns_prefix + 'mgmt'),
            self.check('orchestratorProfile.orchestratorType', 'DCOS'),
            self.check('name', acs_name),
        ])

        # scale-up
        self.cmd('acs scale -g {} -n {} --new-agent-count 5'.format(resource_group, acs_name),
                 checks=self.check('agentPoolProfiles[0].count', 5))

        # show again
        self.cmd('acs show -g {} -n {}'.format(resource_group, acs_name),
                 checks=self.check('agentPoolProfiles[0].count', 5))

    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)

        return pathname

class AzureContainerServiceKubernetesScenarioTest(ScenarioTest):

    # the length is set to avoid following error:
    # Resource name k8s-master-ip-cliacstestgae47e-clitestdqdcoaas25vlhygb2aktyv4-c10894mgmt-D811C917
    # is invalid. The name can be up to 80 characters long.
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer()
    def test_acs_create_kubernetes(self, resource_group, sp_name, sp_password):
        acs_name = self.create_random_name('acs', 14)
        ssh_pubkey_file = self.generate_ssh_keys().replace('\\', '\\\\')
        cmd = 'acs create -g {} -n {} --orchestrator-type Kubernetes --service-principal {} ' \
              '--client-secret {} --ssh-key-value {}'
        self.cmd(cmd.format(resource_group, acs_name, sp_name, sp_password, ssh_pubkey_file),
                 checks=[self.check('properties.provisioningState', 'Succeeded')])


    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)

        return pathname

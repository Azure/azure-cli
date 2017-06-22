# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer,
                               RoleBasedServicePrincipalPreparer, JMESPathCheck)


class AzureContainerServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_acs_create_default_service(self, resource_group, resource_group_location):
        loc = resource_group_location
        ssh_pubkey_file = self.generate_ssh_keys()

        acs_name = self.create_random_name('cliacstest', 16)
        dns_prefix = self.create_random_name('cliasdns', 16)

        # create
        ssh_pubkey_file = ssh_pubkey_file.replace('\\', '\\\\')
        create_cmd = 'acs create -g {} -n {} --dns-prefix {} --ssh-key-value {}'
        self.cmd(create_cmd.format(resource_group, acs_name, dns_prefix, ssh_pubkey_file),
                 checks=[JMESPathCheck('properties.outputs.masterFQDN.value',
                                       '{}mgmt.{}.cloudapp.azure.com'.format(dns_prefix, loc)),
                         JMESPathCheck('properties.outputs.agentFQDN.value',
                                       '{}agents.{}.cloudapp.azure.com'.format(dns_prefix, loc))])

        # show
        self.cmd('acs show -g {} -n {}'.format(resource_group, acs_name), checks=[
            JMESPathCheck('agentPoolProfiles[0].count', 3),
            JMESPathCheck('agentPoolProfiles[0].vmSize', 'Standard_D2_v2'),
            JMESPathCheck('masterProfile.dnsPrefix', dns_prefix + 'mgmt'),
            JMESPathCheck('orchestratorProfile.orchestratorType', 'DCOS'),
            JMESPathCheck('name', acs_name),
        ])

        # scale-up
        self.cmd('acs scale -g {} -n {} --new-agent-count 5'.format(resource_group, acs_name),
                 checks=JMESPathCheck('agentPoolProfiles[0].count', 5))

        # show again
        self.cmd('acs show -g {} -n {}'.format(resource_group, acs_name),
                 checks=JMESPathCheck('agentPoolProfiles[0].count', 5))

    # the length is set to avoid following error:
    # Resource name k8s-master-ip-cliacstestdf9e19-clitest.rgbb2842ffee75a33f04366f72f08527c5157885b
    # 80664c0560e06962ede3e78f0-00977c-7A54A2DE is invalid. The name can be up to 80 characters
    # long.
    @ResourceGroupPreparer(random_name_length=30, name_prefix='clitest')
    @RoleBasedServicePrincipalPreparer()
    def test_acs_create_kubernetes(self, resource_group, sp_name, sp_password):
        acs_name = self.create_random_name('cliacstest', 16)
        ssh_pubkey_file = self.generate_ssh_keys().replace('\\', '\\\\')
        cmd = 'acs create -g {} -n {} --orchestrator-type Kubernetes --service-principal {} ' \
              '--client-secret {} --ssh-key-value {}'
        self.cmd(cmd.format(resource_group, acs_name, sp_name, sp_password, ssh_pubkey_file),
                 checks=[JMESPathCheck('properties.provisioningState', 'Succeeded')])

    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)

        return pathname

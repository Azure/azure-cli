# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer,
                               RoleBasedServicePrincipalPreparer, live_only)

AZURE_TEST_RUN_LIVE = bool(os.environ.get('AZURE_TEST_RUN_LIVE'))


# TODO: deprecated, will remove this after container service commands (acs) are removed during
# the next breaking change window.
@unittest.skip("needs explicit service principal management")
class AzureContainerServiceScenarioTest(ScenarioTest):

    location = 'eastus'

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location=location)
    @RoleBasedServicePrincipalPreparer(skip_assignment=not AZURE_TEST_RUN_LIVE)
    def test_acs_create_default_service(self, resource_group, sp_name, sp_password):
        # kwargs for string formatting
        self.kwargs.update({
            'resource_group': resource_group,
            'name': self.create_random_name('cliacstest', 16),
            'dns_prefix': self.create_random_name('cliacsdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': self.location,
            'service_principal': sp_name,
            'client_secret': sp_password
        })

        # create
        create_cmd = 'acs create -g {resource_group} -n {name} --dns-prefix {dns_prefix} --agent-count 1 ' \
                     '--service-principal {service_principal} --client-secret {client_secret} --ssh-key-value {ssh_key_value}'
        self.fail(create_cmd.format(**self.kwargs))
        self.cmd(create_cmd, checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.outputs.masterFQDN.value', '{dns_prefix}mgmt.{location}.cloudapp.azure.com'),
            self.check('properties.outputs.agentFQDN.value', '{dns_prefix}agent.{location}.cloudapp.azure.com'),
        ])

        # show
        self.cmd('acs show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D2_v2'),
            self.check('masterProfile.dnsPrefix', '{dns_prefix}mgmt'),
            self.check('orchestratorProfile.orchestratorType', 'DCOS'),
            self.check('name', '{name}'),
        ])

        # scale-up
        self.cmd('acs scale -g {resource_group} -n {name} --new-agent-count 5',
                 checks=self.check('agentPoolProfiles[0].count', 5))

        # show again
        self.cmd('acs show -g {resource_group} -n {name}',
                 checks=self.check('agentPoolProfiles[0].count', 5))

    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        fd, pathname = tempfile.mkstemp()
        try:
            with open(pathname, 'w') as key_file:
                key_file.write(TEST_SSH_KEY_PUB)
        finally:
            os.close(fd)

        return pathname


@unittest.skip("skip acs tests as it's deprected")
class AzureContainerServiceKubernetesScenarioTest(ScenarioTest):

    # the length is set to avoid following error:
    # Resource name k8s-master-ip-cliacstestgae47e-clitestdqdcoaas25vlhygb2aktyv4-c10894mgmt-D811C917
    # is invalid. The name can be up to 80 characters long.
    @live_only()  # the test is flaky under recording that you have to pre-create a role assignment 
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer(skip_assignment=not AZURE_TEST_RUN_LIVE)
    def test_acs_create_kubernetes(self, resource_group, sp_name, sp_password):
        # kwargs for string formatting
        self.kwargs.update({
            'resource_group': resource_group,
            'name': self.create_random_name('acs', 14),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'service_principal': sp_name,
            'client_secret': sp_password
        })

        cmd = 'acs create -g {resource_group} -n {name} --orchestrator-type Kubernetes --agent-count 1 ' \
              '--service-principal {service_principal} --client-secret {client_secret} --ssh-key-value {ssh_key_value}'
        self.cmd(cmd, checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        # show the cluster
        self.cmd('acs show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 1),
            self.check('type', 'Microsoft.ContainerService/ContainerServices'),
            self.check('orchestratorProfile.orchestratorType', 'Kubernetes'),
        ])

        # scale-up
        self.cmd('acs scale -g {resource_group} -n {name} --new-agent-count 3',
                 checks=self.check('agentPoolProfiles[0].count', 3))

    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        fd, pathname = tempfile.mkstemp()
        try:
            with open(pathname, 'w') as key_file:
                key_file.write(TEST_SSH_KEY_PUB)
        finally:
            os.close(fd)

        return pathname

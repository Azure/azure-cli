# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest

from azure.cli.testsdk import (
    ResourceGroupPreparer, RoleBasedServicePrincipalPreparer, ScenarioTest)
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.checkers import StringContainCheck

# flake8: noqa

class AzureKubernetesServiceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service(self, resource_group, resource_group_location, sp_name, sp_password):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name}  --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.check('provisioningState', 'Succeeded')
        ])

        # list
        self.cmd('aks list -g {resource_group}', checks=[
            self.check('[0].type', '{resource_type}'),
            StringContainCheck(aks_name),
            StringContainCheck(resource_group)
        ])

        # list in tabular format
        self.cmd('aks list -g {resource_group} -o table', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group)
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 3),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS1_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file {file}')
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # get-credentials without directory in path
        temp_path = 'kubeconfig.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} -f {file}')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.remove(temp_path)

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 5', checks=[
            self.check('agentPoolProfiles[0].count', 5)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 5)
        ])

        # scale down
        self.cmd('aks scale -g {resource_group} -n {name} -c 1', checks=[
            self.check('agentPoolProfiles[0].count', 1)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 1)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} -y', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_service_no_wait(self, resource_group, resource_group_location, sp_name, sp_password):
        # kwargs for string formatting
        self.kwargs.update({
            'resource_group': resource_group,
            'name': self.create_random_name('cliakstest', 16),
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': sp_name,
            'client_secret': sp_password
        })

        # create --no-wait
        create_cmd = 'aks create -g {resource_group} -n {name} -p {dns_name_prefix} --ssh-key-value {ssh_key_value} ' \
                     '-l {location} --service-principal {service_principal} --client-secret {client_secret} ' \
                     '--tags scenario_test --no-wait'
        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 3),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS1_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('provisioningState', 'Succeeded')
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer()
    @AllowLargeResponse()
    def test_aks_create_with_upgrade(self, resource_group, resource_group_location, sp_name, sp_password):
        # kwargs for string formatting
        self.kwargs.update({
            'resource_group': resource_group,
            'name': self.create_random_name('cliakstest', 16),
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'k8s_version': '1.7.12'
        })

        # show k8s versions
        self.cmd('aks get-versions -l {location}', checks=[
            self.exists('orchestrators[*].orchestratorVersion')
        ])

        # show k8s versions in table format
        self.cmd('aks get-versions -l {location} -o table', checks=[
            StringContainCheck(self.kwargs['k8s_version'])
        ])

        # create
        create_cmd = 'aks create -g {resource_group} -n {name} --dns-name-prefix {dns_name_prefix} ' \
                     '--ssh-key-value {ssh_key_value} --kubernetes-version {k8s_version} -l {location} ' \
                     '--service-principal {service_principal} --client-secret {client_secret} -c 1'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.check('provisioningState', 'Succeeded')
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS1_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('kubernetesVersion', '{k8s_version}')
        ])

        # get versions for upgrade
        self.cmd('aks get-upgrades -g {resource_group} -n {name}', checks=[
            self.exists('id'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].kubernetesVersion', '{k8s_version}'),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.exists('controlPlaneProfile.upgrades'),
            self.check('type', 'Microsoft.ContainerService/managedClusters/upgradeprofiles')
        ])

        # get versions for upgrade in table format
        k8s_upgrade_version = '1.8.7'
        self.cmd('aks get-upgrades -g {resource_group} -n {name} --output=table', checks=[
            StringContainCheck('Upgrades'),
            StringContainCheck(k8s_upgrade_version)
        ])


        # upgrade
        self.kwargs.update({'k8s_version': k8s_upgrade_version})
        self.cmd('aks upgrade -g {resource_group} -n {name} --kubernetes-version {k8s_version} --yes', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('kubernetesVersion', '{k8s_version}')
        ])

        # get versions for upgrade in table format
        self.cmd('aks get-upgrades -g {resource_group} -n {name} --output=table', checks=[
            StringContainCheck('Upgrades'),
            StringContainCheck('None available')
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} -y', checks=[self.is_empty()])


    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)
        return pathname

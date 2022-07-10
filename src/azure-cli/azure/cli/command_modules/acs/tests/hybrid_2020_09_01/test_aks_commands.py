# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest

from knack.util import CLIError

from azure.cli.testsdk import (
    ResourceGroupPreparer, RoleBasedServicePrincipalPreparer, VirtualNetworkPreparer, ScenarioTest, live_only)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.checkers import (
    StringContainCheck, StringContainCheckIgnoreCase)
from azure.cli.command_modules.acs._format import version_to_tuple
from azure.cli.command_modules.acs.tests.hybrid_2020_09_01.recording_processors import KeyReplacer

# flake8: noqa


# The RoleBasedServicePrincipalPreparer returns sp name and needs to be turned
# into Application ID URI. Based on the recording files, some Application ID (GUID)
# is set with the environment varibale for sp_name. This method is compatible with
# both cases.
def _process_sp_name(sp_name):
    return sp_name


class AzureKubernetesServiceScenarioTest(ScenarioTest):
    def __init__(self, method_name):
        super(AzureKubernetesServiceScenarioTest, self).__init__(
            method_name, recording_processors=[KeyReplacer()]
        )

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_service_no_wait(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0

        create_version, upgrade_version = self._get_versions(
            resource_group_location)
        # kwargs for string formatting
        self.kwargs.update({
            'resource_group': resource_group,
            'name': self.create_random_name('cliakstest', 16),
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'k8s_version': create_version,
            'vm_size': 'Standard_DS2_v2'
        })

        # create --no-wait
        create_cmd = 'aks create -g {resource_group} -n {name} -p {dns_name_prefix} --ssh-key-value {ssh_key_value} ' \
                     '-l {location} --service-principal {service_principal} --client-secret {client_secret} -k {k8s_version} ' \
                     '--node-vm-size {vm_size} ' \
                     '--tags scenario_test -c 1 --no-wait'
        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd(
            'aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # show k8s versions
        self.cmd('aks get-versions -l {location}', checks=[
            self.exists('orchestrators[*].orchestratorVersion')
        ])

        # show k8s versions in table format
        self.cmd('aks get-versions -l {location} -o table', checks=[
            StringContainCheck(self.kwargs['k8s_version'])
        ])

        # get versions for upgrade
        self.cmd('aks get-upgrades -g {resource_group} -n {name}', checks=[
            self.exists('id'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('controlPlaneProfile.kubernetesVersion',
                       '{k8s_version}'),
            self.check('controlPlaneProfile.osType', 'Linux'),
            self.exists('controlPlaneProfile.upgrades'),
            self.check(
                'type', 'Microsoft.ContainerService/managedClusters/upgradeprofiles')
        ])

        # get versions for upgrade in table format
        self.cmd('aks get-upgrades -g {resource_group} -n {name} --output table', checks=[
            StringContainCheck('Upgrades'),
            StringContainCheck(upgrade_version)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    @live_only()
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service_without_skip_role_assignment(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'vnet_subnet_id': self.generate_vnet_subnet_id(resource_group)
        })
        # create cluster without skip_role_assignment
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 --service-principal={service_principal} ' \
                     '--client-secret={client_secret} --vnet-subnet-id={vnet_subnet_id} '\
                     '--no-ssh-key'
        self.cmd(create_cmd, checks=[
            self.check(
                'agentPoolProfiles[0].vnetSubnetId', '{vnet_subnet_id}'),
            self.check('provisioningState', 'Succeeded')
        ])

        check_role_assignment_cmd = 'role assignment list --scope={vnet_subnet_id}'
        self.cmd(check_role_assignment_cmd, checks=[
            self.check('[0].properties.scope', '{vnet_subnet_id}')
        ])

        # create cluster with same role assignment
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 --service-principal={service_principal} ' \
                     '--client-secret={client_secret} --vnet-subnet-id={vnet_subnet_id} '\
                     '--no-ssh-key'
        self.cmd(create_cmd, checks=[
            self.check(
                'agentPoolProfiles[0].vnetSubnetId', '{vnet_subnet_id}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_default_setting(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd(
            'aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].type', 'VirtualMachineScaleSets'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Standard'),
            self.exists(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # get-credentials without directory in path
        temp_path = self.create_random_name('kubeconfig', 24) + '.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} -f "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.remove(temp_path)

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_nodepool_create_scale_delete(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        tags = "key1=value1"
        new_tags = "key2=value2"
        labels = "label1=value1"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'tags': tags,
            'new_tags': new_tags,
            'labels': labels,
            'nodepool1_name': nodepool1_name,
            'nodepool2_name': nodepool2_name
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded')
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].mode', 'System'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --labels {labels} --node-count=1 --tags {tags}', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name),
            self.check('[1].tags.key1', 'value1'),
            self.check('[1].nodeLabels.label1', 'value1'),
            self.check('[1].mode', 'User')
        ])
        # nodepool list in tabular format
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name} -o table', checks=[
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name)
        ])
        # nodepool scale up
        self.cmd('aks nodepool scale --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3', checks=[
            self.check('count', 3)
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('count', 3)
        ])

        # nodepool get-upgrades
        self.cmd('aks nodepool get-upgrades --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool1_name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            self.check(
                'type', "Microsoft.ContainerService/managedClusters/agentPools/upgradeProfiles")
        ])

        self.cmd('aks nodepool get-upgrades --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool2_name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool2_name),
            self.check(
                'type', "Microsoft.ContainerService/managedClusters/agentPools/upgradeProfiles")
        ])

        # nodepool update
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --tags {new_tags}', checks=[
            self.check('tags.key2', 'value2')
        ])

        # #nodepool delete
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_upgrade_node_image_only_cluster(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('c', 6)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--nodepool-name {node_pool_name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
                     '--ssh-key-value={ssh_key_value} ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        upgrade_node_image_only_cluster_cmd = 'aks upgrade ' \
                                              '-g {resource_group} ' \
                                              '-n {name} ' \
                                              '--node-image-only ' \
                                              '--yes'
        self.cmd(upgrade_node_image_only_cluster_cmd, checks=[
            self.check(
                'agentPoolProfiles[0].provisioningState', 'UpgradingNodeImageVersion')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_upgrade_node_image_only_nodepool(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('c', 6)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--nodepool-name {node_pool_name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
                     '--ssh-key-value={ssh_key_value} ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        upgrade_node_image_only_nodepool_cmd = 'aks nodepool upgrade ' \
                                               '--resource-group={resource_group} ' \
                                               '--cluster-name={name} ' \
                                               '-n {node_pool_name} ' \
                                               '--node-image-only ' \
                                               '--no-wait'
        self.cmd(upgrade_node_image_only_nodepool_cmd)

        get_nodepool_cmd = 'aks nodepool show ' \
                           '--resource-group={resource_group} ' \
                           '--cluster-name={name} ' \
                           '-n {node_pool_name} '
        self.cmd(get_nodepool_cmd, checks=[
            self.check('provisioningState', 'UpgradingNodeImageVersion')
        ])


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

    def generate_vnet_subnet_id(self, resource_group):
        vnet_name = self.create_random_name('clivnet', 16)
        subnet_name = self.create_random_name('clisubnet', 16)
        address_prefix = "192.168.0.0/16"
        subnet_prefix = "192.168.0.0/24"
        vnet_subnet = self.cmd('az network vnet create -n {} -g {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
                               .format(vnet_name, resource_group, address_prefix, subnet_name, subnet_prefix)).get_output_in_json()
        return vnet_subnet.get("newVNet").get("subnets")[0].get("id")

    def generate_ppg_id(self, resource_group, location):
        ppg_name = self.create_random_name('clippg', 16)
        ppg = self.cmd('az ppg create -n {} -g {} --location {}'
                       .format(ppg_name, resource_group, location)).get_output_in_json()
        return ppg.get("id")

    def _get_versions(self, location):
        """Return the previous and current Kubernetes minor release versions, such as ("1.11.6", "1.12.4")."""
        versions = self.cmd(
            "az aks get-versions -l westus2 --query 'orchestrators[].orchestratorVersion'").get_output_in_json()
        # sort by semantic version, from newest to oldest
        versions = sorted(versions, key=version_to_tuple, reverse=True)
        upgrade_version = versions[0]
        # find the first version that doesn't start with the latest major.minor.
        prefix = upgrade_version[:upgrade_version.rfind('.')]
        create_version = next(x for x in versions if not x.startswith(prefix))
        return create_version, upgrade_version

    def generate_user_assigned_identity_resource_id(self, resource_group):
        identity_name = self.create_random_name('cli', 16)
        identity = self.cmd('az identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        return identity.get("id")


        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        identity_name = self.create_random_name('cliakstest', 16)
        subdomain_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'identity_name': identity_name,
            'subdomain_name': subdomain_name,
        })

        # create private dns zone
        create_private_dns_zone = 'network private-dns zone create --resource-group={resource_group} --name="privatelink.westus2.azmk8s.io"'
        zone = self.cmd(create_private_dns_zone, checks=[
            self.check('provisioningState', 'Succeeded')
        ]).get_output_in_json()
        zone_id = zone["id"]
        assert zone_id is not None
        self.kwargs.update({
            'zone_id': zone_id,
        })

        # create identity
        create_identity = 'identity create --resource-group={resource_group} --name={identity_name}'
        identity = self.cmd(create_identity, checks=[
            self.check('name', identity_name)
        ]).get_output_in_json()
        identity_id = identity["principalId"]
        identity_resource_id = identity["id"]
        assert identity_id is not None
        self.kwargs.update({
            'identity_id': identity_id,
            'identity_resource_id': identity_resource_id,
        })

        # assign
        from unittest import mock
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            assignment = self.cmd(
                'role assignment create --assignee-object-id={identity_id} --role "Private DNS Zone Contributor" --scope={zone_id} --assignee-principal-type ServicePrincipal').get_output_in_json()
        assert assignment["roleDefinitionId"] is not None

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--node-count=1 --generate-ssh-keys --fqdn-subdomain={subdomain_name} ' \
                     '--load-balancer-sku=standard --enable-private-cluster --private-dns-zone={zone_id} --enable-managed-identity --assign-identity {identity_resource_id}'
        self.cmd(create_cmd, checks=[
            self.exists('privateFqdn'),
            self.exists('fqdnSubdomain'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('apiServerAccessProfile.privateDnsZone', zone_id),
        ])

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
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.checkers import (StringContainCheck, StringContainCheckIgnoreCase)
from azure.cli.command_modules.acs._format import version_to_tuple

# flake8: noqa


# The RoleBasedServicePrincipalPreparer returns sp name and needs to be turned
# into Application ID URI. Based on the recording files, some Application ID (GUID)
# is set with the environment varibale for sp_name. This method is compatible with
# both cases.  
def _process_sp_name(sp_name):
    from azure.cli.core.util import is_guid
    return sp_name if is_guid(sp_name) else 'http://{}'.format(sp_name)


class AzureKubernetesServiceScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        tags = "key1=value1"
        nodepool_labels = "label1=value1 label2=value2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'tags': tags,
            'nodepool_labels': nodepool_labels,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} --tags {tags} ' \
                     '--nodepool-labels {nodepool_labels}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('tags.key1', 'value1')
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('agentPoolProfiles[0].nodeLabels.label1','value1'),
            self.check('agentPoolProfiles[0].nodeLabels.label2','value2'),
            self.exists('kubernetesVersion')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_service_no_wait(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0

        create_version, upgrade_version = self._get_versions(resource_group_location)
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
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('controlPlaneProfile.kubernetesVersion', '{k8s_version}'),
            self.check('controlPlaneProfile.osType', 'Linux'),
            self.exists('controlPlaneProfile.upgrades'),
            self.check('type', 'Microsoft.ContainerService/managedClusters/upgradeprofiles')
        ])

        # get versions for upgrade in table format
        self.cmd('aks get-upgrades -g {resource_group} -n {name} --output table', checks=[
            StringContainCheck('Upgrades'),
            StringContainCheck(upgrade_version)
        ])

        # enable http application routing addon
        self.cmd('aks enable-addons -g {resource_group} -n {name} --addons http_application_routing', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.httpApplicationRouting.enabled', True)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    # TODO: remove when issue #9392 is addressed.
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='southcentralus')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_scale_with_custom_nodepool_name(self, resource_group, resource_group_location, sp_name, sp_password):
        create_version, _ = self._get_versions(resource_group_location)
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
            'k8s_version': create_version,
            'nodepool_name': self.create_random_name('np', 12)
        })

        # create
        create_cmd = 'aks create -g {resource_group} -n {name} -p {dns_name_prefix} --nodepool-name {nodepool_name} ' \
                     '-l {location} --service-principal {service_principal} --client-secret {client_secret} -k {k8s_version} ' \
                     '--ssh-key-value {ssh_key_value} --tags scenario_test -c 1'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded')
        ])

        # list
        self.cmd('aks list -g {resource_group}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group)
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].name', '{nodepool_name}'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.KubeDashboard.enabled', False)
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --nodepool-name {nodepool_name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)


    # TODO: Remove when issue #9392 is addressed.
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
            self.check('agentPoolProfiles[0].vnetSubnetId', '{vnet_subnet_id}'),
            self.check('provisioningState', 'Succeeded')
        ])

        check_role_assignment_cmd = 'role assignment list --scope={vnet_subnet_id}'
        self.cmd(check_role_assignment_cmd, checks=[
            self.check('[0].scope', '{vnet_subnet_id}')
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
            self.check('agentPoolProfiles[0].vnetSubnetId', '{vnet_subnet_id}'),
            self.check('provisioningState', 'Succeeded')
        ])

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service_with_skip_role_assignment(self, resource_group, resource_group_location, sp_name, sp_password):
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
                     '--client-secret={client_secret} --vnet-subnet-id={vnet_subnet_id} ' \
                     '--skip-subnet-role-assignment --no-ssh-key'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        check_role_assignment_cmd = 'role assignment list --scope={vnet_subnet_id}'
        self.cmd(check_role_assignment_cmd, checks=[
            self.is_empty()
        ])

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_service_without_SP_and_with_role_assignment(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'vnet_subnet_id': self.generate_vnet_subnet_id(resource_group)
        })
        # create cluster without skip_role_assignment
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 --vnet-subnet-id={vnet_subnet_id}  --no-ssh-key --yes'

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        check_role_assignment_cmd = 'role assignment list --scope={vnet_subnet_id}'
        self.cmd(check_role_assignment_cmd, checks=[
            self.check('[0].scope', '{vnet_subnet_id}')
        ])

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service_with_monitoring_addon(self, resource_group, resource_group_location, sp_name, sp_password):
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

        # create cluster with monitoring-addon
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} --enable-addons monitoring'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights')
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
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # disable monitoring add-on
        self.cmd('aks disable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
            self.check('addonProfiles.omsagent.config', None)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
            self.check('addonProfiles.omsagent.config', None)

        ])

        # enable monitoring add-on
        self.cmd('aks enable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    @VirtualNetworkPreparer()
    def test_aks_create_default_service_with_virtual_node_addon(self, resource_group, resource_group_location, sp_name, sp_password):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        subnet_id = self.cmd('network vnet subnet show --resource-group {rg} --vnet-name {vnet} --name default').get_output_in_json()['id']
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'subnet_id': subnet_id
        })

        # create cluster with virtual-node addon
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} --enable-addons virtual-node ' \
                     '--aci-subnet-name default --vnet-subnet-id "{subnet_id}" --network-plugin azure'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.aciConnectorLinux.enabled', True),
            self.check('addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
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
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('addonProfiles.aciConnectorLinux.enabled', True),
            self.check('addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
        ])

        # disable virtual-node add-on
        self.cmd('aks disable-addons -a virtual-node -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.aciConnectorLinux.enabled', False),
            self.check('addonProfiles.aciConnectorLinux.config', None)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.aciConnectorLinux.enabled', False),
            self.check('addonProfiles.aciConnectorLinux.config', None)

        ])

        # enable virtual node add-on
        self.cmd('aks enable-addons -a virtual-node -g {resource_group} -n {name} --subnet-name default', checks=[
            self.check('addonProfiles.aciConnectorLinux.enabled', True),
            self.check('addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('addonProfiles.aciConnectorLinux.enabled', True),
            self.check('addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_blb_vmas(self, resource_group, resource_group_location, sp_name, sp_password):
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
                     '--load-balancer-sku=basic --vm-set-type=availabilityset --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('agentPoolProfiles[0].type', 'AvailabilitySet'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Basic'),
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

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
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # get-credentials without directory in path
        temp_path = self.create_random_name('kubeconfig', 24) + '.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} -f "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.remove(temp_path)

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_private_cluster_then_update(self, resource_group, resource_group_location, sp_name, sp_password):
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
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets ' \
                     '--enable-private-cluster --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('apiServerAccessProfile.enablePrivateCluster', True),
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update api-server-authorized-ip-ranges is not supported
        with self.assertRaises(CLIError) as err:
            self.cmd('aks update -g {resource_group} -n {name} --api-server-authorized-ip-ranges=1.2.3.4/32')

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_cluster_with_apiserver_authorized_ranges_then_update(self, resource_group, resource_group_location, sp_name, sp_password):
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
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets ' \
                     '--api-server-authorized-ip-ranges=1.2.3.4/32 --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('apiServerAccessProfile.enablePrivateCluster', None),
            self.check('apiServerAccessProfile.authorizedIpRanges', ['1.2.3.4/32']),
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update api-server-authorized-ip-ranges
        self.cmd('aks update -g {resource_group} -n {name} --api-server-authorized-ip-ranges=""', checks=[
            self.check('apiServerAccessProfile.authorizedIpRanges', None)
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_slb_vmss_with_default_mgd_outbound_ip_then_update(self, resource_group, resource_group_location, sp_name, sp_password):
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
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update managed outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-managed-outbound-ip-count 2', checks=[
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 2),
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 2),
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_slb_vmss_with_outbound_ip_then_update(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        ip1_name = self.create_random_name('cliaksslbip1', 16)
        ip2_name = self.create_random_name('cliaksslbip2', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ip1_name': ip1_name,
            'ip2_name': ip2_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create public ip address
        ip1_id = self.cmd('az network public-ip create -g {rg} -n {ip1_name} --location {location} --sku Standard '). \
            get_output_in_json().get("publicIp").get("id")
        ip2_id = self.cmd('az network public-ip create -g {rg} -n {ip2_name} --location {location} --sku Standard '). \
            get_output_in_json().get("publicIp").get("id")

        self.kwargs.update({
            'ip1_id': ip1_id,
            'ip2_id': ip2_id
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --load-balancer-outbound-ips {ip1_id}'

        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].type', 'VirtualMachineScaleSets'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Standard'),
            self.exists('networkProfile.loadBalancerProfile'),
            self.exists('networkProfile.loadBalancerProfile.outboundIps'),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-outbound-ips {ip1_id},{ip2_id}', checks=[
            StringContainCheck(ip1_id),
            StringContainCheck(ip2_id)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            StringContainCheck(ip1_id),
            StringContainCheck(ip2_id)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_slb_vmss_with_outbound_ip_prefixes_then_update(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        ipprefix1_name = self.create_random_name('cliaksslbipp1', 20)
        ipprefix2_name = self.create_random_name('cliaksslbipp2', 20)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ipprefix1_name': ipprefix1_name,
            'ipprefix2_name': ipprefix2_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create public ip prefix
        ipprefix1_id = self.cmd('az network public-ip prefix create -g {rg} -n {ipprefix1_name} --location {location} --length 29'). \
            get_output_in_json().get("id")
        ipprefix2_id = self.cmd('az network public-ip prefix create -g {rg} -n {ipprefix2_name} --location {location} --length 29'). \
            get_output_in_json().get("id")

        self.kwargs.update({
            'ipprefix1_id': ipprefix1_id,
            'ipprefix2_id': ipprefix2_id
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --load-balancer-outbound-ip-prefixes {ipprefix1_id}'

        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            StringContainCheck(ipprefix1_id)
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].type', 'VirtualMachineScaleSets'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Standard'),
            self.exists('networkProfile.loadBalancerProfile'),
            self.exists('networkProfile.loadBalancerProfile.outboundIpPrefixes'),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-outbound-ip-prefixes {ipprefix1_id},{ipprefix2_id}', checks=[
            StringContainCheck(ipprefix1_id),
            StringContainCheck(ipprefix2_id)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            StringContainCheck(ipprefix1_id),
            StringContainCheck(ipprefix2_id)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

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
        labels="label1=value1"
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
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --labels {labels} --node-count=1 --tags {tags}',checks=[
            self.check('provisioningState', 'Succeeded')
            ])

        #nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name),
            self.check('[1].tags.key1','value1'),
            self.check('[1].nodeLabels.label1','value1'),
            self.check('[1].mode', 'User')
        ])
        #nodepool list in tabular format
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name} -o table', checks=[
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name)
        ])
        #nodepool scale up
        self.cmd('aks nodepool scale --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3', checks=[
            self.check('count', 3)
        ])

        #nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('count', 3)
        ])

        #nodepool get-upgrades
        self.cmd('aks nodepool get-upgrades --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool1_name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            self.check('type', "Microsoft.ContainerService/managedClusters/agentPools/upgradeProfiles")
        ])

        self.cmd('aks nodepool get-upgrades --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool2_name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool2_name),
            self.check('type', "Microsoft.ContainerService/managedClusters/agentPools/upgradeProfiles")
        ])

        #nodepool update
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --tags {new_tags}', checks=[
            self.check('tags.key2','value2')
        ])

        # #nodepool delete
        self.cmd('aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_nodepool_system_pool(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        nodepool3_name = "nodepool3"
        tags = "key1=value1"
        new_tags = "key2=value2"
        labels="label1=value1"
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
            'nodepool2_name': nodepool2_name,
            'nodepool3_name': nodepool3_name
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
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add user mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --labels {labels} --node-count=1 --tags {tags}',checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('mode', 'User')
            ])

        #nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name),
            self.check('[0].mode', 'System'),
            self.check('[1].tags.key1','value1'),
            self.check('[1].nodeLabels.label1','value1'),
            self.check('[1].mode', 'User')
        ])

        #nodepool list in tabular format
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name} -o table', checks=[
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name)
        ])

         # nodepool add another system mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name} --labels {labels} --node-count=1 --tags {tags} --mode system',checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        #nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name}', checks=[
            self.check('mode', 'System')
        ])

        #nodepool delete the first system pool
        self.cmd('aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --no-wait', checks=[self.is_empty()])

        #nodepool update nodepool2 to system pool
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --mode System', checks=[
            self.check('mode', 'System')
        ])

        #nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('mode', 'System')
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_availability_zones(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'nodepool1_name': nodepool1_name,
            'nodepool2_name': nodepool2_name,
            'zones': "1 2 3"
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=3 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} --zones {zones}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].availabilityZones[0]', '1'),
            self.check('agentPoolProfiles[0].availabilityZones[1]', '2'),
            self.check('agentPoolProfiles[0].availabilityZones[2]', '3'),
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 3),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].availabilityZones[0]', '1'),
            self.check('agentPoolProfiles[0].availabilityZones[1]', '2'),
            self.check('agentPoolProfiles[0].availabilityZones[2]', '3'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3 --zones {zones}',checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('availabilityZones[0]', '1'),
            self.check('availabilityZones[1]', '2'),
            self.check('availabilityZones[2]', '3'),
            ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_managed_identity_with_service_principal(self, resource_group, resource_group_location, sp_name, sp_password):
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
                     '--service-principal={service_principal} --client-secret={client_secret} --enable-managed-identity'

        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.exists('servicePrincipalProfile'),
            self.not_exists('identity'),
            self.check('provisioningState', 'Succeeded'),
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.not_exists('identity'),
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_with_paid_sku(self, resource_group, resource_group_location, sp_name, sp_password):
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
                     '--service-principal={service_principal} --client-secret={client_secret} --uptime-sla '
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.tier', 'Paid')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_with_windows(self, resource_group, resource_group_location, sp_name, sp_password):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': 'replacePassword1234$',
            'nodepool2_name': 'npwin',
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.adminUsername', 'azureuser1')
        ])

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1',checks=[
            self.check('provisioningState', 'Succeeded')
            ])

        # update Windows license type
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-ahub', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.licenseType', 'Windows_Server')
        ])

        # #nodepool delete
        self.cmd('aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_with_ahub(self, resource_group, resource_group_location, sp_name, sp_password):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': 'replacePassword1234$',
            'nodepool2_name': 'npwin',
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure --enable-ahub'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.adminUsername', 'azureuser1'),
            self.check('windowsProfile.licenseType', 'Windows_Server')
        ])

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1',checks=[
            self.check('provisioningState', 'Succeeded')
            ])

        # update Windows license type
        self.cmd('aks update --resource-group={resource_group} --name={name} --disable-ahub', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.licenseType', 'None')
        ])

        # #nodepool delete
        self.cmd('aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_managed_identity_without_service_principal(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-managed-identity'

        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.exists('identity'),
            self.exists('identityProfile'),
            self.check('provisioningState', 'Succeeded'),
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.exists('identity'),
            self.exists('identityProfile')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # get-credentials without directory in path
        temp_path = 'kubeconfig.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} -f "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.remove(temp_path)

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_managed_aad(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-aad --aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000001')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000003 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId', '00000000-0000-0000-0000-000000000003')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    @RoleBasedServicePrincipalPreparer()
    def test_managed_aad_enable_azure_rbac(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-aad --aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.enableAzureRbac', False),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000001')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-azure-rbac -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.enableAzureRbac', True)
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--disable-azure-rbac -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.enableAzureRbac', False)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_aadv1_and_update_with_managed_aad(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--aad-server-app-id 00000000-0000-0000-0000-000000000001 ' \
                     '--aad-server-app-secret fake-secret ' \
                     '--aad-client-app-id 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id d5b55040-0c14-48cc-a028-91457fc190d9 ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', None),
            self.check('aadProfile.serverAppId', '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.clientAppId', '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId', 'd5b55040-0c14-48cc-a028-91457fc190d9')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-aad ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000003 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000004 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000003'),
            self.check('aadProfile.tenantId', '00000000-0000-0000-0000-000000000004')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='southcentralus')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_nonaad_and_update_with_managed_aad(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile', None)
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-aad ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000002 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.tenantId', '00000000-0000-0000-0000-000000000002')
        ])

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
            self.check('agentPoolProfiles[0].provisioningState', 'UpgradingNodeImageVersion')
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_spot_node_pool(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        spot_node_pool_name = self.create_random_name('s', 6)
        spot_max_price = 88.88888  # Good number with large value.
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'spot_node_pool_name': spot_node_pool_name,
            'spot_max_price': spot_max_price,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
                     '--ssh-key-value={ssh_key_value} ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        create_spot_node_pool_cmd = 'aks nodepool add ' \
                                    '--resource-group={resource_group} ' \
                                    '--cluster-name={name} ' \
                                    '-n {spot_node_pool_name} ' \
                                    '--priority Spot ' \
                                    '--spot-max-price {spot_max_price} ' \
                                    '-c 1'
        self.cmd(create_spot_node_pool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('name', spot_node_pool_name),
            self.check('scaleSetEvictionPolicy', 'Delete'),
            self.check('nodeTaints[0]', 'kubernetes.azure.com/scalesetpriority=spot:NoSchedule'),
            self.check('spotMaxPrice', spot_max_price)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_with_ppg(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('p', 10)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ppg': self.generate_ppg_id(resource_group, resource_group_location)
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
            '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
            '--service-principal={service_principal} --client-secret={client_secret} --ppg={ppg} '
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].proximityPlacementGroupId', '{ppg}')
        ])

        # add node pool
        create_ppg_node_pool_cmd = 'aks nodepool add ' \
            '--resource-group={resource_group} ' \
            '--cluster-name={name} ' \
            '-n {node_pool_name} ' \
            '--ppg={ppg} '
        self.cmd(create_ppg_node_pool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('name', node_pool_name),
            self.check('proximityPlacementGroupId', '{ppg}')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_managed_disk(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--generate-ssh-keys ' \
                     '--vm-set-type VirtualMachineScaleSets -c 1 ' \
                     '--node-osdisk-type=Managed'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].osDiskType', 'Managed'),
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_ephemeral_disk(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--generate-ssh-keys ' \
                     '--vm-set-type VirtualMachineScaleSets -c 1 ' \
                     '--node-osdisk-type=Ephemeral --node-osdisk-size 60'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].osDiskType', 'Ephemeral'),
        ])
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_control_plane_user_assigned_identity(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'identity_resource_id': self.generate_user_assigned_identity_resource_id(resource_group),
            'vnet_subnet_id': self.generate_vnet_subnet_id(resource_group)
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-managed-identity --assign-identity={identity_resource_id} ' \
                     '--vnet-subnet-id={vnet_subnet_id}'

        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.exists('identity'),
            self.exists('identityProfile'),
            self.check('provisioningState', 'Succeeded'),
            self.check('identity.type', "UserAssigned")
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.exists('identity'),
            self.exists('identityProfile')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # get-credentials without directory in path
        temp_path = 'kubeconfig.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} -f "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.remove(temp_path)

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westeurope')
    def test_aks_create_with_ingress_appgw_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity --generate-ssh-keys ' \
                     '-a ingress-appgw --appgw-subnet-cidr 10.2.0.0/16 -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ingressApplicationGateway.enabled', True),
            self.check(
                'addonProfiles.ingressApplicationGateway.config.subnetCIDR', "10.2.0.0/16")
        ])

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_byo_subnet_with_ingress_appgw_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        vnet_name = self.create_random_name('cliakstest', 16)
        appgw_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'aks_name': aks_name,
            'vnet_name': vnet_name,
            'appgw_name': appgw_name
        })

        # create virtual network
        create_vnet = 'network vnet create --resource-group={resource_group} --name={vnet_name} ' \
                      '--address-prefix 11.0.0.0/16 --subnet-name aks-subnet --subnet-prefix 11.0.0.0/24 -o json'
        vnet = self.cmd(create_vnet, checks=[
            self.check('newVNet.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_subnet = 'network vnet subnet create -n appgw-subnet --resource-group={resource_group} --vnet-name {vnet_name} ' \
                        '--address-prefixes 11.0.1.0/24  -o json'
        self.cmd(create_subnet, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        vnet_id = vnet['newVNet']["id"]
        assert vnet_id is not None
        self.kwargs.update({
            'vnet_id': vnet_id,
        })

        # create aks cluster
        create_cmd = 'aks create --resource-group={resource_group} --name={aks_name} --enable-managed-identity --generate-ssh-keys ' \
                     '--vnet-subnet-id {vnet_id}/subnets/aks-subnet ' \
                     '-a ingress-appgw --appgw-name gateway --appgw-subnet-id {vnet_id}/subnets/appgw-subnet --yes -o json'
        aks_cluster = self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ingressApplicationGateway.enabled', True),
            self.check(
                'addonProfiles.ingressApplicationGateway.config.applicationGatewayName', "gateway"),
            self.check('addonProfiles.ingressApplicationGateway.config.subnetId',
                       vnet_id + '/subnets/appgw-subnet')
        ]).get_output_in_json()

        addon_client_id = aks_cluster["addonProfiles"]["ingressApplicationGateway"]["identity"]["clientId"]

        self.kwargs.update({
            'addon_client_id': addon_client_id,
        })

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_byo_appgw_with_ingress_appgw_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        vnet_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'aks_name': aks_name,
            'vnet_name': vnet_name
        })

        # create virtual network
        create_vnet = 'network vnet create --resource-group={resource_group} --name={vnet_name} ' \
                      '--address-prefix 11.0.0.0/16 --subnet-name aks-subnet --subnet-prefix 11.0.0.0/24 -o json'
        vnet = self.cmd(create_vnet, checks=[
            self.check('newVNet.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_subnet = 'network vnet subnet create -n appgw-subnet --resource-group={resource_group} --vnet-name {vnet_name} ' \
                        '--address-prefixes 11.0.1.0/24  -o json'
        self.cmd(create_subnet, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        vnet_id = vnet['newVNet']["id"]
        assert vnet_id is not None
        self.kwargs.update({
            'vnet_id': vnet_id,
        })

        # create public ip for app gateway
        create_pip = 'network public-ip create -n appgw-ip -g {resource_group} ' \
                     '--allocation-method Static --sku Standard  -o json'
        self.cmd(create_pip, checks=[
            self.check('publicIp.provisioningState', 'Succeeded')
        ])

        # create app gateway
        create_appgw = 'network application-gateway create -n appgw -g {resource_group} ' \
                       '--sku Standard_v2 --public-ip-address appgw-ip --subnet {vnet_id}/subnets/appgw-subnet'
        self.cmd(create_appgw)

        # construct group id
        from msrestazure.tools import parse_resource_id, resource_id
        parsed_vnet_id = parse_resource_id(vnet_id)
        group_id = resource_id(subscription=parsed_vnet_id["subscription"],
                               resource_group=parsed_vnet_id["resource_group"])
        appgw_id = group_id + "/providers/Microsoft.Network/applicationGateways/appgw"

        self.kwargs.update({
            'appgw_id': appgw_id,
            'appgw_group_id': group_id
        })

        # create aks cluster
        create_cmd = 'aks create -n {aks_name} -g {resource_group} --enable-managed-identity --generate-ssh-keys ' \
                     '--vnet-subnet-id {vnet_id}/subnets/aks-subnet ' \
                     '-a ingress-appgw --appgw-id {appgw_id} --yes -o json'
        aks_cluster = self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ingressApplicationGateway.enabled', True),
            self.check(
                'addonProfiles.ingressApplicationGateway.config.applicationGatewayId', appgw_id)
        ]).get_output_in_json()

        addon_client_id = aks_cluster["addonProfiles"]["ingressApplicationGateway"]["identity"]["clientId"]

        self.kwargs.update({
            'addon_client_id': addon_client_id,
        })

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_service_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        tags = "key1=value1"
        nodepool_labels = "label1=value1 label2=value2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'tags': tags,
            'nodepool_labels': nodepool_labels,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--tags {tags} ' \
                     '--nodepool-labels {nodepool_labels}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('tags.key1', 'value1')
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('agentPoolProfiles[0].nodeLabels.label1','value1'),
            self.check('agentPoolProfiles[0].nodeLabels.label2','value2'),
            self.exists('kubernetesVersion')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_service_no_wait_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0

        create_version, upgrade_version = self._get_versions(resource_group_location)
        # kwargs for string formatting
        self.kwargs.update({
            'resource_group': resource_group,
            'name': self.create_random_name('cliakstest', 16),
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'k8s_version': create_version,
            'vm_size': 'Standard_DS2_v2'
        })

        # create --no-wait
        create_cmd = 'aks create -g {resource_group} -n {name} -p {dns_name_prefix} --ssh-key-value {ssh_key_value} ' \
                     '-l {location} -k {k8s_version} ' \
                     '--node-vm-size {vm_size} ' \
                     '--tags scenario_test -c 1 --no-wait'
        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('controlPlaneProfile.kubernetesVersion', '{k8s_version}'),
            self.check('controlPlaneProfile.osType', 'Linux'),
            self.exists('controlPlaneProfile.upgrades'),
            self.check('type', 'Microsoft.ContainerService/managedClusters/upgradeprofiles')
        ])

        # get versions for upgrade in table format
        self.cmd('aks get-upgrades -g {resource_group} -n {name} --output table', checks=[
            StringContainCheck('Upgrades'),
            StringContainCheck(upgrade_version)
        ])

        # enable http application routing addon
        self.cmd('aks enable-addons -g {resource_group} -n {name} --addons http_application_routing', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.httpApplicationRouting.enabled', True)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    # TODO: remove when issue #9392 is addressed.
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='southcentralus')
    def test_aks_create_scale_with_custom_nodepool_name_msi(self, resource_group, resource_group_location):
        create_version, _ = self._get_versions(resource_group_location)
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'k8s_version': create_version,
            'nodepool_name': self.create_random_name('np', 12)
        })

        # create
        create_cmd = 'aks create -g {resource_group} -n {name} -p {dns_name_prefix} --nodepool-name {nodepool_name} ' \
                     '-l {location} -k {k8s_version} ' \
                     '--ssh-key-value {ssh_key_value} --tags scenario_test -c 1'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded')
        ])

        # list
        self.cmd('aks list -g {resource_group}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group)
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].name', '{nodepool_name}'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.KubeDashboard.enabled', False)
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --nodepool-name {nodepool_name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)


    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_service_without_skip_role_assignment_msi(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'vnet_subnet_id': self.generate_vnet_subnet_id(resource_group)
        })
        # create cluster without skip_role_assignment
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 ' \
                     '--vnet-subnet-id={vnet_subnet_id} '\
                     '--no-ssh-key --yes'
        self.cmd(create_cmd, checks=[
            self.check('agentPoolProfiles[0].vnetSubnetId', '{vnet_subnet_id}'),
            self.check('provisioningState', 'Succeeded')
        ])

        check_role_assignment_cmd = 'role assignment list --scope={vnet_subnet_id}'
        self.cmd(check_role_assignment_cmd, checks=[
            self.check('[0].scope', '{vnet_subnet_id}')
        ])


    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_service_with_skip_role_assignment_msi(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'vnet_subnet_id': self.generate_vnet_subnet_id(resource_group)
        })
        # create cluster without skip_role_assignment
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 ' \
                     '--vnet-subnet-id={vnet_subnet_id} ' \
                     '--skip-subnet-role-assignment --no-ssh-key'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        check_role_assignment_cmd = 'role assignment list --scope={vnet_subnet_id}'
        self.cmd(check_role_assignment_cmd, checks=[
            self.is_empty()
        ])

    # TODO: Remove when issue #9392 is addressed.
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_service_with_monitoring_addon_msi(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create cluster with monitoring-addon
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-addons monitoring'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights')
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
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # disable monitoring add-on
        self.cmd('aks disable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
            self.check('addonProfiles.omsagent.config', None)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
            self.check('addonProfiles.omsagent.config', None)

        ])

        # enable monitoring add-on
        self.cmd('aks enable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_blb_vmas_msi(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=basic --vm-set-type=availabilityset --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('agentPoolProfiles[0].type', 'AvailabilitySet'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Basic'),
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_setting_msi(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # get-credentials without directory in path
        temp_path = self.create_random_name('kubeconfig', 24) + '.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} -f "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.remove(temp_path)

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_private_cluster_then_update_msi(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets ' \
                     '--enable-private-cluster --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('apiServerAccessProfile.enablePrivateCluster', True),
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update api-server-authorized-ip-ranges is not supported
        with self.assertRaises(CLIError) as err:
            self.cmd('aks update -g {resource_group} -n {name} --api-server-authorized-ip-ranges=1.2.3.4/32')

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_cluster_with_apiserver_authorized_ranges_then_update_msi(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets ' \
                     '--api-server-authorized-ip-ranges=1.2.3.4/32 --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('apiServerAccessProfile.enablePrivateCluster', None),
            self.check('apiServerAccessProfile.authorizedIpRanges', ['1.2.3.4/32']),
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update api-server-authorized-ip-ranges
        self.cmd('aks update -g {resource_group} -n {name} --api-server-authorized-ip-ranges=""', checks=[
            self.check('apiServerAccessProfile.authorizedIpRanges', None)
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_slb_vmss_with_default_mgd_outbound_ip_then_update_msi(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --no-wait'

        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('aks wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

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
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update managed outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-managed-outbound-ip-count 2', checks=[
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 2),
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('networkProfile.loadBalancerProfile.managedOutboundIps.count', 2),
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_slb_vmss_with_outbound_ip_then_update_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        ip1_name = self.create_random_name('cliaksslbip1', 16)
        ip2_name = self.create_random_name('cliaksslbip2', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ip1_name': ip1_name,
            'ip2_name': ip2_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create public ip address
        ip1_id = self.cmd('az network public-ip create -g {rg} -n {ip1_name} --location {location} --sku Standard '). \
            get_output_in_json().get("publicIp").get("id")
        ip2_id = self.cmd('az network public-ip create -g {rg} -n {ip2_name} --location {location} --sku Standard '). \
            get_output_in_json().get("publicIp").get("id")

        self.kwargs.update({
            'ip1_id': ip1_id,
            'ip2_id': ip2_id
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --load-balancer-outbound-ips {ip1_id}'

        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].type', 'VirtualMachineScaleSets'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Standard'),
            self.exists('networkProfile.loadBalancerProfile'),
            self.exists('networkProfile.loadBalancerProfile.outboundIps'),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-outbound-ips {ip1_id},{ip2_id}', checks=[
            StringContainCheck(ip1_id),
            StringContainCheck(ip2_id)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            StringContainCheck(ip1_id),
            StringContainCheck(ip2_id)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_slb_vmss_with_outbound_ip_prefixes_then_update_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        ipprefix1_name = self.create_random_name('cliaksslbipp1', 20)
        ipprefix2_name = self.create_random_name('cliaksslbipp2', 20)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ipprefix1_name': ipprefix1_name,
            'ipprefix2_name': ipprefix2_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create public ip prefix
        ipprefix1_id = self.cmd('az network public-ip prefix create -g {rg} -n {ipprefix1_name} --location {location} --length 29'). \
            get_output_in_json().get("id")
        ipprefix2_id = self.cmd('az network public-ip prefix create -g {rg} -n {ipprefix2_name} --location {location} --length 29'). \
            get_output_in_json().get("id")

        self.kwargs.update({
            'ipprefix1_id': ipprefix1_id,
            'ipprefix2_id': ipprefix2_id
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --load-balancer-outbound-ip-prefixes {ipprefix1_id}'

        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            StringContainCheck(ipprefix1_id)
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
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].type', 'VirtualMachineScaleSets'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Standard'),
            self.exists('networkProfile.loadBalancerProfile'),
            self.exists('networkProfile.loadBalancerProfile.outboundIpPrefixes'),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIps')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # update outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-outbound-ip-prefixes {ipprefix1_id},{ipprefix2_id}', checks=[
            StringContainCheck(ipprefix1_id),
            StringContainCheck(ipprefix2_id)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            StringContainCheck(ipprefix1_id),
            StringContainCheck(ipprefix2_id)
        ])

        #delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_create_scale_delete_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        tags = "key1=value1"
        new_tags = "key2=value2"
        labels="label1=value1"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'tags': tags,
            'new_tags': new_tags,
            'labels': labels,
            'nodepool1_name': nodepool1_name,
            'nodepool2_name': nodepool2_name
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} '
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
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --labels {labels} --node-count=1 --tags {tags}',checks=[
            self.check('provisioningState', 'Succeeded')
            ])

        #nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name),
            self.check('[1].tags.key1','value1'),
            self.check('[1].nodeLabels.label1','value1'),
            self.check('[1].mode', 'User')
        ])
        #nodepool list in tabular format
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name} -o table', checks=[
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name)
        ])
        #nodepool scale up
        self.cmd('aks nodepool scale --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3', checks=[
            self.check('count', 3)
        ])

        #nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('count', 3)
        ])

        #nodepool get-upgrades
        self.cmd('aks nodepool get-upgrades --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool1_name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            self.check('type', "Microsoft.ContainerService/managedClusters/agentPools/upgradeProfiles")
        ])

        self.cmd('aks nodepool get-upgrades --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool2_name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool2_name),
            self.check('type', "Microsoft.ContainerService/managedClusters/agentPools/upgradeProfiles")
        ])

        #nodepool update
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --tags {new_tags}', checks=[
            self.check('tags.key2','value2')
        ])

        # #nodepool delete
        self.cmd('aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_system_pool_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        nodepool3_name = "nodepool3"
        tags = "key1=value1"
        new_tags = "key2=value2"
        labels="label1=value1"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'tags': tags,
            'new_tags': new_tags,
            'labels': labels,
            'nodepool1_name': nodepool1_name,
            'nodepool2_name': nodepool2_name,
            'nodepool3_name': nodepool3_name
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} '
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
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add user mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --labels {labels} --node-count=1 --tags {tags}',checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('mode', 'User')
            ])

        #nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name),
            self.check('[0].mode', 'System'),
            self.check('[1].tags.key1','value1'),
            self.check('[1].nodeLabels.label1','value1'),
            self.check('[1].mode', 'User')
        ])

        #nodepool list in tabular format
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name} -o table', checks=[
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name)
        ])

         # nodepool add another system mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name} --labels {labels} --node-count=1 --tags {tags} --mode system',checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        #nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name}', checks=[
            self.check('mode', 'System')
        ])

        #nodepool delete the first system pool
        self.cmd('aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --no-wait', checks=[self.is_empty()])

        #nodepool update nodepool2 to system pool
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --mode System', checks=[
            self.check('mode', 'System')
        ])

        #nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('mode', 'System')
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_availability_zones_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'nodepool1_name': nodepool1_name,
            'nodepool2_name': nodepool2_name,
            'zones': "1 2 3"
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=3 --ssh-key-value={ssh_key_value} ' \
                     '--zones {zones}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].availabilityZones[0]', '1'),
            self.check('agentPoolProfiles[0].availabilityZones[1]', '2'),
            self.check('agentPoolProfiles[0].availabilityZones[2]', '3'),
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 3),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].availabilityZones[0]', '1'),
            self.check('agentPoolProfiles[0].availabilityZones[1]', '2'),
            self.check('agentPoolProfiles[0].availabilityZones[2]', '3'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd('aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3 --zones {zones}',checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('availabilityZones[0]', '1'),
            self.check('availabilityZones[1]', '2'),
            self.check('availabilityZones[2]', '3'),
            ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_paid_sku_msi(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--uptime-sla '
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.tier', 'Paid')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_windows_msi(self, resource_group, resource_group_location):
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
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': 'replacePassword1234$',
            'nodepool2_name': 'npwin',
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.adminUsername', 'azureuser1')
        ])

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1',checks=[
            self.check('provisioningState', 'Succeeded')
            ])

        # update Windows license type
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-ahub', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.licenseType', 'Windows_Server')
        ])

        # #nodepool delete
        self.cmd('aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    def test_aks_managed_aad_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-aad --aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000001')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000003 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId', '00000000-0000-0000-0000-000000000003')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    def test_aks_create_aadv1_and_update_with_managed_aad_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--aad-server-app-id 00000000-0000-0000-0000-000000000001 ' \
                     '--aad-server-app-secret fake-secret ' \
                     '--aad-client-app-id 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id d5b55040-0c14-48cc-a028-91457fc190d9 ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', None),
            self.check('aadProfile.serverAppId', '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.clientAppId', '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId', 'd5b55040-0c14-48cc-a028-91457fc190d9')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-aad ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000003 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000004 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000003'),
            self.check('aadProfile.tenantId', '00000000-0000-0000-0000-000000000004')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='southcentralus')
    def test_aks_create_nonaad_and_update_with_managed_aad_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile', None)
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-aad ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000002 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.adminGroupObjectIds[0]', '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.tenantId', '00000000-0000-0000-0000-000000000002')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_upgrade_node_image_only_cluster_msi(self, resource_group, resource_group_location):
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
            self.check('agentPoolProfiles[0].provisioningState', 'UpgradingNodeImageVersion')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_upgrade_node_image_only_nodepool_msi(self, resource_group, resource_group_location):
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_spot_node_pool_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        spot_node_pool_name = self.create_random_name('s', 6)
        spot_max_price = 88.88888  # Good number with large value.
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'spot_node_pool_name': spot_node_pool_name,
            'spot_max_price': spot_max_price,
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\')
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
                     '--ssh-key-value={ssh_key_value} ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        create_spot_node_pool_cmd = 'aks nodepool add ' \
                                    '--resource-group={resource_group} ' \
                                    '--cluster-name={name} ' \
                                    '-n {spot_node_pool_name} ' \
                                    '--priority Spot ' \
                                    '--spot-max-price {spot_max_price} ' \
                                    '-c 1'
        self.cmd(create_spot_node_pool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('name', spot_node_pool_name),
            self.check('scaleSetEvictionPolicy', 'Delete'),
            self.check('nodeTaints[0]', 'kubernetes.azure.com/scalesetpriority=spot:NoSchedule'),
            self.check('spotMaxPrice', spot_max_price)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_ppg_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('p', 10)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys().replace('\\', '\\\\'),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ppg': self.generate_ppg_id(resource_group, resource_group_location)
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
            '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
            '--ppg={ppg} '
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].proximityPlacementGroupId', '{ppg}')
        ])

        # add node pool
        create_ppg_node_pool_cmd = 'aks nodepool add ' \
            '--resource-group={resource_group} ' \
            '--cluster-name={name} ' \
            '-n {node_pool_name} ' \
            '--ppg={ppg} '
        self.cmd(create_ppg_node_pool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('name', node_pool_name),
            self.check('proximityPlacementGroupId', '{ppg}')
        ])

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_stop_and_start(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        stop_cmd = 'aks stop --resource-group={resource_group} --name={name}'
        self.cmd(stop_cmd)

        start_cmd = 'aks start --resource-group={resource_group} --name={name}'
        self.cmd(start_cmd)

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_confcom_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity --generate-ssh-keys ' \
                     '-a confcom -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check('addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "false")
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_confcom_addon_helper_enabled(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity --generate-ssh-keys ' \
                     '-a confcom --enable-sgxquotehelper -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check('addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "true")
        ])

    @live_only()  # without live only fails with need az login
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_addons_confcom_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity --generate-ssh-keys ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin', None)
        ])

        enable_cmd = 'aks enable-addons --addons confcom --resource-group={resource_group} --name={name} -o json'
        self.cmd(enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check('addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "false")
        ])

    @live_only()  # without live only fails with need az login
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_disable_addons_confcom_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity --generate-ssh-keys ' \
                     '-a confcom -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check('addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "false")
        ])

        disable_cmd = 'aks disable-addons --addons confcom --resource-group={resource_group} --name={name} -o json'
        self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', False),
            self.check('addonProfiles.ACCSGXDevicePlugin.config', None)
        ])
    
    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)
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
        versions = self.cmd("az aks get-versions -l westus2 --query 'orchestrators[].orchestratorVersion'").get_output_in_json()
        # sort by semantic version, from newest to oldest
        versions = sorted(versions, key=version_to_tuple, reverse=True)
        upgrade_version = versions[0]
        # find the first version that doesn't start with the latest major.minor.
        prefix = upgrade_version[:upgrade_version.rfind('.')]
        create_version = next(x for x in versions if not x.startswith(prefix))
        return create_version, upgrade_version

    def generate_user_assigned_identity_resource_id(self, resource_group):
        identity_name = self.create_random_name('cli', 16)
        identity = self.cmd('az identity create -g {} -n {}'.format(resource_group, identity_name)).get_output_in_json()
        return identity.get("id")

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_fqdn_subdomain(self, resource_group, resource_group_location):
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
        import mock
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            assignment = self.cmd('role assignment create --assignee-object-id={identity_id} --role "Private DNS Zone Contributor" --scope={zone_id} --assignee-principal-type ServicePrincipal').get_output_in_json()
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_update_with_windows_password(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'location': resource_group_location,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': self.create_random_name('p@0A', 14),
            'nodepool2_name': 'npwin',
            'new_windows_admin_password': self.create_random_name('n!C3', 14),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --generate-ssh-keys ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.adminUsername', 'azureuser1')
        ])

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # update Windows password
        self.cmd('aks update --resource-group={resource_group} --name={name} --windows-admin-password {new_windows_admin_password}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # #nodepool delete
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @RoleBasedServicePrincipalPreparer()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westeurope')
    def test_aks_update_to_msi_cluster(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --generate-ssh-keys ' \
                     '--service-principal={service_principal} --client-secret={client_secret} '

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # update to MSI cluster
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-managed-identity --yes', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('identity.type', 'SystemAssigned')
        ])
        
        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @RoleBasedServicePrincipalPreparer()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westeurope')
    def test_aks_update_to_msi_cluster_with_addons(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'service_principal': _process_sp_name(sp_name),
            'client_secret': sp_password,
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --generate-ssh-keys --enable-addons monitoring ' \
                     '--service-principal={service_principal} --client-secret={client_secret} '
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # update to MSI cluster
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-managed-identity --yes', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('identity.type', 'SystemAssigned')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

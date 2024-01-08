# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import subprocess
import tempfile
import time
import unittest

from azure.cli.command_modules.acs._consts import \
    CONST_KUBE_DASHBOARD_ADDON_NAME
from azure.cli.command_modules.acs._format import version_to_tuple
from azure.cli.command_modules.acs.tests.latest.custom_preparers import (
    AKSCustomResourceGroupPreparer, AKSCustomRoleBasedServicePrincipalPreparer,
    AKSCustomVirtualNetworkPreparer)
from azure.cli.command_modules.acs.tests.latest.recording_processors import \
    KeyReplacer
from azure.cli.command_modules.acs.tests.latest.utils import get_test_data_file_path
from azure.cli.core.azclierror import ClientRequestError, CLIInternalError
from azure.cli.testsdk import ScenarioTest, live_only
from azure.cli.testsdk.checkers import (StringCheck, StringContainCheck,
                                        StringContainCheckIgnoreCase)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from knack.util import CLIError

# flake8: noqa

class AzureKubernetesServiceScenarioTest(ScenarioTest):
    def __init__(self, method_name):
        super(AzureKubernetesServiceScenarioTest, self).__init__(
            method_name, recording_processors=[KeyReplacer()]
        )

    @classmethod
    def generate_ssh_keys(cls):
        """
        If the `--ssh-key-value` option is not specified, the validator will try to read the ssh-key from the "~/.ssh"
        directory, and if no key exists, it will call the method provided by azure-cli.core to generate one under the
        "~/.ssh" directory.

        In order to avoid misuse of personal ssh-key during testing and the race condition that is prone to occur
        when key creation is handled by azure-cli when performing test cases concurrently, we provide this function as
        a workround.

        In the scenario of runner and AKS check-in pipeline, a temporary ssh-key will be generated in advance under the
        "tests/latest/data/.ssh" sub-directory of the acs module in the cloned azure-cli repository when setting up the
        environment. Each test case will read the ssh-key from a pre-generated file during execution, so there will be no
        race conditions caused by concurrent reading and writing/creating of the same file.
        """
        acs_base_dir = os.getenv("ACS_BASE_DIR", None)
        if acs_base_dir:
            pre_generated_ssh_key_path = os.path.join(acs_base_dir, "tests/latest/data/.ssh/id_rsa.pub")
            if os.path.exists(pre_generated_ssh_key_path):
                return pre_generated_ssh_key_path.replace('\\', '\\\\')

        # In the CLI check-in pipeline scenario, the following fake ssh-key will be used. Each test case will read the
        # ssh-key from a different temporary file during execution, so there will be no race conditions caused by
        # concurrent reading and writing/creating of the same file.
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        fd, pathname = tempfile.mkstemp()
        try:
            with open(pathname, 'w') as key_file:
                key_file.write(TEST_SSH_KEY_PUB)
        finally:
            os.close(fd)
        return pathname.replace('\\', '\\\\')

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
        versions = self._get_versions_by_location(location=location)
        upgrade_version = versions[0]
        # find the first version that doesn't start with the latest major.minor.
        prefix = upgrade_version[:upgrade_version.rfind('.')]
        create_version = next(x for x in versions if not x.startswith(prefix))
        return create_version, upgrade_version

    def _get_versions_by_location(self, location):
        versions = self.cmd(
            "az aks get-versions -l {} --query 'values[*].patchVersions.keys(@)[]'".format(location)).get_output_in_json()
        # sort by semantic version, from newest to oldest
        versions = sorted(versions, key=version_to_tuple, reverse=True)
        return versions

    def generate_user_assigned_identity_resource_id(self, resource_group):
        identity_name = self.create_random_name('cli', 16)
        identity = self.cmd('az identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        return identity.get("id")

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        tags = "key1=value1"
        nodepool_labels = "label1=value1 label2=value2"
        nodepool_tags = "tag1=tv1 tag2=tv2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'tags': tags,
            'nodepool_labels': nodepool_labels,
            'nodepool_tags': nodepool_tags,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--tags {tags} --nodepool-labels {nodepool_labels} --nodepool-tags {nodepool_tags}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.exists('kubernetesVersion'),
            self.exists('fqdn'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].nodeLabels.label1', 'value1'),
            self.check('agentPoolProfiles[0].nodeLabels.label2', 'value2'),
            self.check('agentPoolProfiles[0].tags.tag1', 'tv1'),
            self.check('agentPoolProfiles[0].tags.tag2', 'tv2'),
            self.check('agentPoolProfiles[0].maxPods', 110),
            self.check('agentPoolProfiles[0].osDiskSizeGb', 128),
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

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_default_sp(self, resource_group, resource_group_location, sp_name, sp_password):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        tags = "key1=value1"
        nodepool_labels = "label1=value1 label2=value2"
        nodepool_tags = "tag1=tv1 tag2=tv2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'tags': tags,
            'nodepool_labels': nodepool_labels,
            'nodepool_tags': nodepool_tags,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--tags {tags} --nodepool-labels {nodepool_labels} --nodepool-tags {nodepool_tags} ' \
                     '--service-principal={service_principal} --client-secret={client_secret}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('name', '{name}'),
            self.exists('nodeResourceGroup'),
            self.exists('kubernetesVersion'),
            self.exists('fqdn'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('agentPoolProfiles[0].nodeLabels.label1', 'value1'),
            self.check('agentPoolProfiles[0].nodeLabels.label2', 'value2'),
            self.check('agentPoolProfiles[0].tags.tag1', 'tv1'),
            self.check('agentPoolProfiles[0].tags.tag2', 'tv2'),
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

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_private_cluster(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --enable-private-cluster'

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.exists('fqdn'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('networkProfile.loadBalancerSku', 'Standard'),
            self.check('apiServerAccessProfile.enablePrivateCluster', True),
            self.check('networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIPs')
        ])

        # update api-server-authorized-ip-ranges is not supported
        with self.assertRaises(CLIError):
            self.cmd(
                'aks update -g {resource_group} -n {name} --api-server-authorized-ip-ranges=1.2.3.4/32')

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_private_cluster_without_public_fqdn(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-private-cluster --disable-public-fqdn --node-count=1 ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.exists('privateFqdn'),
            self.check('fqdn', None),
            self.check('apiServerAccessProfile.enablePrivateCluster', True),
            self.check('apiServerAccessProfile.enablePrivateClusterPublicFqdn', False),
        ])

        # update
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --enable-public-fqdn'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.exists('privateFqdn'),
            self.exists('fqdn'),
            self.check('apiServerAccessProfile.enablePrivateClusterPublicFqdn', True),
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_private_cluster_update_dns_zone(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-private-cluster --node-count=1 --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.exists('privateFqdn'),
            self.check('apiServerAccessProfile.enablePrivateCluster', True),
            self.check('apiServerAccessProfile.privateDnsZone', 'system'),
        ])

        # update
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --private-dns-zone none'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.exists('privateFqdn'),
            self.exists('fqdn'),
            self.check('apiServerAccessProfile.privateDnsZone', 'none'),
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_api_server_authorized_ip_ranges(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --api-server-authorized-ip-ranges=1.2.3.4/32'

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('networkProfile.loadBalancerSku', 'Standard'),
            self.check('apiServerAccessProfile.enablePrivateCluster', None),
            self.check('apiServerAccessProfile.authorizedIpRanges', ['1.2.3.4/32']),
            self.check('networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
            self.exists('networkProfile.loadBalancerProfile.effectiveOutboundIPs')
        ])

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

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_and_update_with_http_proxy_config(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'http_proxy_path': get_test_data_file_path('httpproxyconfig.json').replace('\\', '\\\\'),
            'custom_data_path': get_test_data_file_path('setup_proxy.sh').replace('\\', '\\\\'),
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_vnet_cmd = 'network vnet create \
            --resource-group={resource_group} \
            --name={name} \
            --address-prefixes 10.42.0.0/16 \
            --subnet-name aks-subnet \
            --subnet-prefix 10.42.1.0/24'

        create_subnet_cmd = 'network vnet subnet create \
            --resource-group={resource_group} \
            --vnet-name={name} \
            --name proxy-subnet \
            --address-prefix 10.42.3.0/24'

        show_subnet_cmd = 'network vnet subnet show \
            --resource-group={resource_group} \
            --vnet-name={name} \
            --name aks-subnet'

        # name below MUST match the name used in testcerts for httpproxyconfig.json.
        # otherwise the VM will not present a cert with correct hostname
        # else, change the cert to have the correct hostname (harder)
        create_vm_cmd = 'vm create \
            --resource-group={resource_group} \
            --name=cli-proxy-vm \
            --image Canonical:0001-com-ubuntu-server-focal:20_04-lts:latest \
            --ssh-key-values @{ssh_key_value} \
            --public-ip-address "" \
            --custom-data {custom_data_path} \
            --vnet-name {name} \
            --subnet proxy-subnet'

        self.cmd(create_vnet_cmd, checks=[
            self.check('newVNet.provisioningState', 'Succeeded')
        ])

        self.cmd(create_subnet_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        subnet_output = self.cmd(show_subnet_cmd).get_output_in_json()
        subnet_id = subnet_output["id"]
        assert subnet_id is not None

        self.cmd(create_vm_cmd)

        self.kwargs.update({
            'vnet_subnet_id': subnet_id,
        })

        # use custom feature so it does not require subscription to regiter the feature
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --http-proxy-config={http_proxy_path} ' \
                     '--ssh-key-value={ssh_key_value} --enable-managed-identity --yes --vnet-subnet-id {vnet_subnet_id} -o json'

        self.cmd(create_cmd, checks=[
            self.check('httpProxyConfig.httpProxy',
                       'http://cli-proxy-vm:3128/'),
            self.check('httpProxyConfig.httpsProxy',
                       'https://cli-proxy-vm:3129/'),
            self.check('httpProxyConfig.trustedCa', 'LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZHekNDQXdPZ0F3SUJBZ0lVT1FvajhDTFpkc2Vscjk3cnZJd3g1T0xEc3V3d0RRWUpLb1pJaHZjTkFRRUwKQlFBd0Z6RVZNQk1HQTFVRUF3d01ZMnhwTFhCeWIzaDVMWFp0TUI0WERUSXlNRE13T0RFMk5EUTBOMW9YRFRNeQpNRE13TlRFMk5EUTBOMW93RnpFVk1CTUdBMVVFQXd3TVkyeHBMWEJ5YjNoNUxYWnRNSUlDSWpBTkJna3Foa2lHCjl3MEJBUUVGQUFPQ0FnOEFNSUlDQ2dLQ0FnRUEvTVB0VjVCVFB0NmNxaTRSZE1sbXIzeUlzYTJ1anpjaHh2NGgKanNDMUR0blJnb3M1UzQxUEgwcmkrM3RUU1ZYMzJ5cndzWStyRDFZUnVwbTZsbUU3R2hVNUkwR2k5b3prU0YwWgpLS2FKaTJveXBVL0ZCK1FQcXpvQ1JzTUV3R0NibUtGVmw4VnVoeW5kWEs0YjRrYmxyOWJsL2V1d2Q3TThTYnZ6CldVam5lRHJRc2lJc3J6UFQ0S0FaTHFjdHpEZTRsbFBUN1lLYTMzaGlFUE9mdldpWitkcWthUUE5UDY0eFhTeW4KZkhYOHVWQUozdUJWSmVHeEQwcGtOSjdqT3J5YVV1SEh1Y1U4UzltSWpuS2pBQjVhUGpMSDV4QXM2bG1iMzEyMgp5KzF0bkVBbVhNNTBEK1VvRWpmUzZIT2I1cmRpcVhHdmMxS2JvS2p6a1BDUnh4MmE3MmN2ZWdVajZtZ0FKTHpnClRoRTFsbGNtVTRpemd4b0lNa1ZwR1RWT0xMbjFWRkt1TmhNWkN2RnZLZ25Lb0F2M0cwRlVuZldFYVJSalNObUQKTFlhTURUNUg5WnQycERJVWpVR1N0Q2w3Z1J6TUVuWXdKTzN5aURwZzQzbzVkUnlzVXlMOUpmRS9OaDdUZzYxOApuOGNKL1c3K1FZYllsanVyYXA4cjdRRlNyb2wzVkNoRkIrT29yNW5pK3ZvaFNBd0pmMFVsTXBHM3hXbXkxVUk0ClRGS2ZGR1JSVHpyUCs3Yk53WDVoSXZJeTVWdGd5YU9xSndUeGhpL0pkeHRPcjJ0QTVyQ1c3K0N0Z1N2emtxTkUKWHlyN3ZrWWdwNlk1TFpneTR0VWpLMEswT1VnVmRqQk9oRHBFenkvRkY4dzFGRVZnSjBxWS9yV2NMa0JIRFQ4Ugp2SmtoaW84Q0F3RUFBYU5mTUYwd0Z3WURWUjBSQkJBd0RvSU1ZMnhwTFhCeWIzaDVMWFp0TUJJR0ExVWRFd0VCCi93UUlNQVlCQWY4Q0FRQXdEd1lEVlIwUEFRSC9CQVVEQXdmbmdEQWRCZ05WSFNVRUZqQVVCZ2dyQmdFRkJRY0QKQWdZSUt3WUJCUVVIQXdFd0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dJQkFBb21qQ3lYdmFRT3hnWUs1MHNYTEIyKwp3QWZkc3g1bm5HZGd5Zmc0dXJXMlZtMTVEaEd2STdDL250cTBkWXkyNE4vVWJHN1VEWHZseUxJSkZxMVhQN25mCnBaRzBWQ2paNjlibXhLbTNaOG0wL0F3TXZpOGU5ZWR5OHY5a05CQ3dMR2tIYkE4WW85Q0lpUWdlbGZwcDF2VWgKYm5OQmhhRCtpdTZDZmlDTHdnSmIvaXc3ZW8vQ3lvWnF4K3RqWGFPMnpYdm00cC8rUUlmQU9ndEdRTEZVOGNmWgovZ1VyVHE1Z0ZxMCtQOUd5V3NBVEpGNnE3TDZXWlpqME91VHNlN2Y0Q1NpajZNbk9NTXhBK0pvYWhKejdsc1NpClRKSEl3RXA1ci9SeWhweWVwUXhGWWNVSDVKSmY5cmFoWExXWmkrOVRqeFNNMll5aHhmUlBzaVVFdUdEb2s3OFEKbS9RUGlDaTlKSmIxb2NtVGpBVjh4RFNob2NpdlhPRnlobjZMbjc3dkxqWStBYXZ0V0RoUXRocHVQeHNMdFZ6bQplMFNIMTFkRUxSdGI3NG1xWE9yTzdmdS8rSUJzM0pxTEUvVSt4dXhRdHZHOHZHMXlES0hIU1pxUzJoL1dzNGw0Ck5pQXNoSGdlaFFEUEJjWTl3WVl6ZkJnWnBPVU16ZERmNTB4K0ZTbFk0M1dPSkp6U3VRaDR5WjArM2t5Z3VDRjgKcm5NTFNjZXlTNGNpNExtSi9LQ1N1R2RmNlhWWXo4QkU5Z2pqanBDUDZxeTBVbFJlZldzL2lnL3djSysyYkYxVApuL1l2KzZnWGVDVEhKNzVxRElQbHA3RFJVVWswZmJNajRiSWthb2dXV2s0emYydThteFpMYTBsZVBLTktaTi9tCkdDdkZ3cjNlaSt1LzhjenA1RjdUCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K')
        ])

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'http_proxy_path': get_test_data_file_path('httpproxyconfig_update.json').replace('\\', '\\\\'),
        })

        update_cmd = 'aks update --resource-group={resource_group} --name={name} --http-proxy-config={http_proxy_path}'

        self.cmd(update_cmd, checks=[
            self.check('httpProxyConfig.httpProxy',
                       'http://cli-proxy-vm:3128/'),
            self.check('httpProxyConfig.httpsProxy',
                       'https://cli-proxy-vm:3129/'),
            self.check('httpProxyConfig.trustedCa', 'LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZERENDQXZTZ0F3SUJBZ0lVQlJ3cGs1eTh5ckdrNmtYTjhkSHlMRUNvaHBrd0RRWUpLb1pJaHZjTkFRRUwKQlFBd0VqRVFNQTRHQTFVRUF3d0habTl2TFdKaGNqQWVGdzB5TVRFd01UTXdNekU1TlRoYUZ3MHpNVEV3TVRFdwpNekU1TlRoYU1CSXhFREFPQmdOVkJBTU1CMlp2YnkxaVlYSXdnZ0lpTUEwR0NTcUdTSWIzRFFFQkFRVUFBNElDCkR3QXdnZ0lLQW9JQ0FRRFcwRE9sVC9yci9xUEZIUU9lNndBNDkyVGh3VWxZaDhCQkszTW9VWVZLNjEvL2xXekEKeFkrYzlmazlvckUrZXhMSVpwdUg1VnNZR21MNUFyc05sVmNBMkU4MWgwSlBPYUo1eEpiZG40YldpZG9vdXRVVwpXeDNhYUJLSEt0RWdZbUNmTjliWXlZMlNWRWQvNS9HeGh0akVabHJ1aEtRdkZVa3hwR0xKK1JRQ25oNklZakQwCnNpQ0YyTjJhVUJ4RE5KaUdmeHlHSVIrY2p4Vlcrd01md05CQ0l6QVkxMnY4WmpzUXdmUWlhOE5oWEx3M0tuRm0KdzUrcHN2bU1HL1FFUUtZMXNOTnk2dS9DZkI3cmIxQ0EwcjdNNnFsNFMrWHJjZUVRcXpDUWR6NWJueGNYbmFkbwp5MDlhdm5OSGRqbmpvcHNPSkxhd2hzb3RGNWFrL1FLdjYzdU9yVFFlOHlPSWlCZ3JSUzdwejcxbVlhRGNMcXFtCmtmdDVLYnFnMHNZYmo0M09LSm5aZ3crTUtackhoSFJKNi9BcWxOclZML3pFUytHU0ozQ1lSaE5nYXdDQ0Nqd1gKanZYZnkycWFEV2NQbWZaSWVVMVNzdE05THBVRWFQNjJzUVNmb3NEdnZFbUFyUVgwcmd1WGhvZ3pRUFdGWVlEKwo4SUNFYkNFc21hVnN3MzhVUzgzbFlGVCtyTHh3cm5UK1JXSUZ2WFRXbHhCNm5JeWpsOXBhNzlkdU5ocjJxN2RzCjVOU3ZWWHg5UGNqVTQ2VUZ6QnVTbUl0Q0M0Y1NadFRWc3l6ZnpMd2hKbGlqV0czTkp5TnpHUkZQcUpQdTNJUzEKZ3VtKytqdWx4bXZNWm1vM1RqSE5JRm90a0kyd3d3ZUtIcWpYcW9STmwvVnZobE5CaXZRR2gxeGovd0lEQVFBQgpvMW93V0RBU0JnTlZIUkVFQ3pBSmdnZG1iMjh0WW1GeU1CSUdBMVVkRXdFQi93UUlNQVlCQWY4Q0FRQXdEd1lEClZSMFBBUUgvQkFVREF3Zm5nREFkQmdOVkhTVUVGakFVQmdnckJnRUZCUWNEQWdZSUt3WUJCUVVIQXdFd0RRWUoKS29aSWh2Y05BUUVMQlFBRGdnSUJBTDF3RlpTdUw4NTM3aHpUTXhSUWJjcWdEU2F4RUd0ZDJaNTVCcnVWQVloagpxQjR6STd1UVZ2SkNpeXdmQm5BNnZmejh2UDBzdGJJbkVtajh1dS9CSS81NzZqR0tWUWRQSDhqMnQvN1NQWjFKClhBWk9wc1hoVll2RmtpQlhVeW1RMnAvRjFqb2ZRRE1JQ0htdHhRUSthakJQNjBpcnFnVnpsRi95NlQySUgzOHYKbGordndIam52WW5vVmhGNEY0TlE5amp6S3Y1NUhVTk0xUEJKZkFaOTJqeXovczdPMmN2cjhNWlNkT2s5QVk1RQp5RXRlQjBTSjdLS0tUZklBVmVMQzdrRnBHR3FsRkRBNzhPSS9YakNZViswRjk4MHdNOVkxTEVUa3ZMamVSMEFyCnVzZDNIS1Vtd2EwTVEwUTNZNGxma0ZtNjJTclhvcjJURC9WZHpFZWNOTnVmV1VJTVNuaEJDNTVHWjBOTVYvR0QKRXhGZTVWQkhUZEZVNlIwb3JCOVFjVll1Mzk0MEt5NXhkbHNaUHZlMmRJNS9WOXhzY0Zad3cxWWs4K21RK3NVeQp2UVBoL2ZmK0tTQjdVVkdvTVNXUlg3YjFFMGVzZSs4QzZlaVV2OXpDR0VRbkVCcnFIQWxSUDJ2ZzQ0bXFJSnRzCjN2NUt1NW0ySmJoeWNsQVR3VUNQZkN3a2tLRTg0MzZGRitDK0ZUVTJ1OWVpL2t5QTAxYi9zRFl2cWdsS2FWK3MKbEVHRkhjd05Ea2VrS1BFUEZxNkpnZ3R0WlNidE5SMnFadzl3cExIbDVuVlVXdnBGa2hvcW1KVkphK0VBSTQ1LwpqRkh4VG9PMHp1NlBxc1p5SnM2TC84Z3BhbTcwMDV6b0VETVRjcFltMlduMFBKcEg3NE9zUHJVRDVJWVA5ZEt5Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K')
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_private_dns_zone(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        identity_name = self.create_random_name('cliakstest', 16)
        subdomain_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'identity_name': identity_name,
            'subdomain_name': subdomain_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create private dns zone
        create_private_dns_zone = 'network private-dns zone create --resource-group={resource_group} --name="privatelink.{location}.azmk8s.io"'
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
        with unittest.mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            assignment = self.cmd(
                'role assignment create --assignee-object-id={identity_id} --role "Private DNS Zone Contributor" --scope={zone_id} --assignee-principal-type ServicePrincipal').get_output_in_json()
        assert assignment["roleDefinitionId"] is not None

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--node-count=1 --fqdn-subdomain={subdomain_name} ' \
                     '--load-balancer-sku=standard --enable-private-cluster --private-dns-zone={zone_id} ' \
                     '--enable-managed-identity --assign-identity {identity_resource_id} --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.exists('privateFqdn'),
            self.check('fqdnSubdomain', subdomain_name),
            self.check('apiServerAccessProfile.privateDnsZone', zone_id),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        tags = "key1=value1"
        nodepool_labels = "label1=value1 label2=value2"
        nodepool_tags = "tag1=tv1 tag2=tv2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'tags': tags,
            'nodepool_labels': nodepool_labels,
            'nodepool_tags': nodepool_tags,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} --tags {tags} ' \
                     '--nodepool-labels {nodepool_labels} --nodepool-tags {nodepool_tags} ' \
                     '--max-pods=100 --admin-username=adminuser'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('tags.key1', 'value1'),
            self.check('servicePrincipalProfile.clientId', sp_name),
            self.check('agentPoolProfiles[0].maxPods', 100),
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
            self.check('agentPoolProfiles[0].maxPods', 100),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('agentPoolProfiles[0].nodeLabels.label1', 'value1'),
            self.check('agentPoolProfiles[0].nodeLabels.label2', 'value2'),
            self.check('agentPoolProfiles[0].tags.tag1', 'tv1'),
            self.check('agentPoolProfiles[0].tags.tag2', 'tv2'),
            self.check('linuxProfile.adminUsername', 'adminuser'),
            self.check('enableRbac', True),
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.exists('values[*].patchVersions.keys(@)[]')
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_scale_with_custom_nodepool_name(self, resource_group, resource_group_location, sp_name, sp_password):
        create_version, _ = self._get_versions(resource_group_location)
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.check('provisioningState', 'Succeeded')
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    @AllowLargeResponse(8192)
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service_without_skip_role_assignment(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.check(
                'agentPoolProfiles[0].vnetSubnetId', '{vnet_subnet_id}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @AllowLargeResponse(8192)
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service_with_skip_role_assignment(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'service_principal': sp_name,
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

    @AllowLargeResponse(8192)
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_and_update_with_managed_nat_gateway_outbound(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets -c 1 ' \
                     '--outbound-type=managedNATGateway ' \
                     '--generate-ssh-keys ' \
                     '--nat-gateway-managed-outbound-ip-count=1 ' \
                     '--nat-gateway-idle-timeout=4 ' \
                     '--location={location}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.outboundType', 'managedNATGateway'),
            self.check('networkProfile.natGatewayProfile.idleTimeoutInMinutes', 4),
            self.check('networkProfile.natGatewayProfile.managedOutboundIpProfile.count', 1),
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--nat-gateway-managed-outbound-ip-count=2 ' \
                     '--nat-gateway-idle-timeout=30 '
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.outboundType', 'managedNATGateway'),
            self.check('networkProfile.natGatewayProfile.idleTimeoutInMinutes', 30),
            self.check('networkProfile.natGatewayProfile.managedOutboundIpProfile.count', 2),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_update_outbound_from_slb_to_natgateway(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets -c 1 ' \
                     '--outbound-type=loadbalancer  --load-balancer-managed-outbound-ip-count 2 ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.outboundType', 'loadBalancer'),
            self.check('networkProfile.loadBalancerProfile.managedOutboundIPs.count', 2),
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--nat-gateway-managed-outbound-ip-count 2 ' \
                     '--nat-gateway-idle-timeout 30 ' \
                     '--outbound-type managedNATGateway '
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.outboundType', 'managedNATGateway'),
            self.check('networkProfile.natGatewayProfile.idleTimeoutInMinutes', 30),
            self.check('networkProfile.natGatewayProfile.managedOutboundIpProfile.count', 2),
        ])

    # live only due to role assignment is not mocked
    @live_only()
    @AllowLargeResponse(8192)
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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

    # live only due to workspace is not mocked
    @live_only()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service_with_monitoring_addon(self, resource_group, resource_group_location, sp_name, sp_password):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.exists(
                'addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
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
            self.exists(
                'addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # disable monitoring add-on
        disable_addon_output = self.cmd('aks disable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
        ]).get_output_in_json()
        assert bool(disable_addon_output["addonProfiles"]["omsagent"]["config"]) == False

        # show again
        show_output = self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
        ]).get_output_in_json()
        assert bool(show_output["addonProfiles"]["omsagent"]["config"]) == False

        # enable monitoring add-on
        self.cmd('aks enable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists(
                'addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
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
            self.exists(
                'addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomVirtualNetworkPreparer(address_prefixes='10.128.0.0/24', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service_with_virtual_node_addon(self, resource_group, resource_group_location, sp_name, sp_password):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        subnet_id = self.cmd(
            'network vnet subnet show --resource-group {rg} --vnet-name {vnet} --name default').get_output_in_json()['id']
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.check(
                'addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
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
            self.check(
                'addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
        ])

        # disable virtual-node add-on
        disable_addon_output = self.cmd('aks disable-addons -a virtual-node -g {resource_group} -n {name}').get_output_in_json()
        assert disable_addon_output["addonProfiles"]["aciConnectorLinux"]["enabled"] == False
        # None for addon v1, {} for addon v2
        assert bool(disable_addon_output["addonProfiles"]["aciConnectorLinux"]["config"]) == False


        # show again
        show_output = self.cmd('aks show -g {resource_group} -n {name}').get_output_in_json()
        assert show_output["addonProfiles"]["aciConnectorLinux"]["enabled"] == False
        # None for addon v1, {} for addon v2
        assert bool(show_output["addonProfiles"]["aciConnectorLinux"]["config"]) == False

        # enable virtual node add-on
        self.cmd('aks enable-addons -a virtual-node -g {resource_group} -n {name} --subnet-name default', checks=[
            self.check('addonProfiles.aciConnectorLinux.enabled', True),
            self.check(
                'addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
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
            self.check(
                'addonProfiles.aciConnectorLinux.config.SubnetName', 'default'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_blb_vmas(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.check('agentPoolProfiles[0].type', 'AvailabilitySet'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Basic'),
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

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_default_setting(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
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
        from azure.cli.testsdk.utilities import create_random_name
        temp_path = create_random_name('kubeconfig', 24) + '.tmp'
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_slb_vmss_with_default_mgd_outbound_ip_then_update(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
            self.exists(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs')
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

        # update managed outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-managed-outbound-ip-count 2', checks=[
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 2),
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 2),
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.exists('networkProfile.loadBalancerProfile.outboundIPs'),
            self.exists(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs')
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

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.exists(
                'networkProfile.loadBalancerProfile.outboundIpPrefixes'),
            self.exists(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs')
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

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
        labels = "label1=value1"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add user mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --labels {labels} --node-count=1 --tags {tags}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('mode', 'User')
        ])

        # nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name),
            self.check('[0].mode', 'System'),
            self.check('[1].tags.key1', 'value1'),
            self.check('[1].nodeLabels.label1', 'value1'),
            self.check('[1].mode', 'User')
        ])

        # nodepool list in tabular format
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name} -o table', checks=[
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name)
        ])

        # nodepool add another system mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name} --labels {labels} --node-count=1 --tags {tags} --mode system', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name}', checks=[
            self.check('mode', 'System')
        ])

        # nodepool delete the first system pool
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --no-wait', checks=[self.is_empty()])

        # nodepool update nodepool2 to system pool
        # make sure no input won't wipe out exsiting labels
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --mode System', checks=[
            self.check('mode', 'System'),
            self.check('nodeLabels.label1', 'value1')
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('mode', 'System'),
            self.check('nodeLabels.label1', 'value1')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus', preserve_default_location=True)
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3 --zones {zones}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('availabilityZones[0]', '1'),
            self.check('availabilityZones[1]', '2'),
            self.check('availabilityZones[2]', '3'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_managed_identity_with_service_principal(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_with_paid_sku(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
            self.check('sku.tier', 'Standard')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_with_standard_sku(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-count=1 --ssh-key-value={ssh_key_value} --tier standard'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', 'Base'),
            self.check('sku.tier', 'Standard'),
        ])

        # update
        create_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--tier free'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', 'Base'),
            self.check('sku.tier', 'Free'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_with_windows(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # update Windows license type
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-ahub', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.licenseType', 'Windows_Server')
        ])

        # #nodepool delete
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_with_ahub(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'service_principal': sp_name,
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
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # update Windows license type
        self.cmd('aks update --resource-group={resource_group} --name={name} --disable-ahub', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.licenseType', 'None')
        ])

        # #nodepool delete
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_managed_identity_without_service_principal(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {resource_group} -n {name} -f -')

        # get-credentials without directory in path
        from azure.cli.testsdk.utilities import create_random_name
        temp_path = create_random_name('kubeconfig', 24) + '.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} -f "{file}"')
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    def test_aks_managed_aad(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-aad --aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000001')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000003 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId',
                       '00000000-0000-0000-0000-000000000003')
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    def test_managed_aad_enable_azure_rbac(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-aad --aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check('aadProfile.enableAzureRbac', False),
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000001')
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    def test_aks_create_aadv1_and_update_with_managed_aad(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--aad-server-app-id 00000000-0000-0000-0000-000000000001 ' \
                     '--aad-server-app-secret fake-secret ' \
                     '--aad-client-app-id 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id d5b55040-0c14-48cc-a028-91457fc190d9 ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AADv1AllowCreate ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', None),
            self.check('aadProfile.serverAppId',
                       '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.clientAppId',
                       '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId',
                       'd5b55040-0c14-48cc-a028-91457fc190d9')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-aad ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000003 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000004 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000003'),
            self.check('aadProfile.tenantId',
                       '00000000-0000-0000-0000-000000000004')
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='southcentralus')
    def test_aks_create_nonaad_and_update_with_managed_aad(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
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
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.tenantId',
                       '00000000-0000-0000-0000-000000000002')
        ])

    # @AllowLargeResponse()
    # @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    # def test_aks_upgrade_node_image_only_cluster(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
    #     self.test_resources_count = 0
        # kwargs for string formatting
    #     aks_name = self.create_random_name('cliakstest', 16)
    #     node_pool_name = self.create_random_name('c', 6)
    #     self.kwargs.update({
    #         'resource_group': resource_group,
    #         'name': aks_name,
    #         'node_pool_name': node_pool_name,
    #         'ssh_key_value': self.generate_ssh_keys()
    #     })

    #     create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
    #                  '--nodepool-name {node_pool_name} ' \
    #                  '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
    #                  '--ssh-key-value={ssh_key_value} ' \
    #                  '-o json'
    #     self.cmd(create_cmd, checks=[
    #         self.check('provisioningState', 'Succeeded')
    #     ])

    #     upgrade_node_image_only_cluster_cmd = 'aks upgrade ' \
    #                                           '-g {resource_group} ' \
    #                                           '-n {name} ' \
    #                                           '--node-image-only ' \
    #                                           '--yes'
    #     self.cmd(upgrade_node_image_only_cluster_cmd, checks=[
    #         self.check(
    #             'agentPoolProfiles[0].provisioningState', 'UpgradingNodeImageVersion')
    #     ])

    # @AllowLargeResponse()
    # @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    # def test_aks_upgrade_node_image_only_nodepool(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
    #     self.test_resources_count = 0
        # kwargs for string formatting
    #     aks_name = self.create_random_name('cliakstest', 16)
    #     node_pool_name = self.create_random_name('c', 6)
    #     self.kwargs.update({
    #         'resource_group': resource_group,
    #         'name': aks_name,
    #         'node_pool_name': node_pool_name,
    #         'ssh_key_value': self.generate_ssh_keys()
    #     })

    #     create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
    #                  '--nodepool-name {node_pool_name} ' \
    #                  '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
    #                  '--ssh-key-value={ssh_key_value} ' \
    #                  '-o json'
    #     self.cmd(create_cmd, checks=[
    #         self.check('provisioningState', 'Succeeded')
    #     ])

    #     upgrade_node_image_only_nodepool_cmd = 'aks nodepool upgrade ' \
    #                                            '--resource-group={resource_group} ' \
    #                                            '--cluster-name={name} ' \
    #                                            '-n {node_pool_name} ' \
    #                                            '--node-image-only ' \
    #                                            '--no-wait'
    #     self.cmd(upgrade_node_image_only_nodepool_cmd)

    #     get_nodepool_cmd = 'aks nodepool show ' \
    #                        '--resource-group={resource_group} ' \
    #                        '--cluster-name={name} ' \
    #                        '-n {node_pool_name} '
    #     self.cmd(get_nodepool_cmd, checks=[
    #         self.check('provisioningState', 'UpgradingNodeImageVersion')
    #     ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_upgrade_kubernetes_version_nodepool(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('c', 6)
        create_version, upgrade_version = self._get_versions(resource_group_location)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'ssh_key_value': self.generate_ssh_keys(),
            'create_version': create_version,
            'upgrade_version': upgrade_version
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
                     '--ssh-key-value={ssh_key_value} --kubernetes-version {upgrade_version} ' \
                     '-o json'

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        create_nodepool_cmd = 'aks nodepool add ' \
                              '--resource-group={resource_group} ' \
                              '--cluster-name={name} ' \
                              '-n {node_pool_name} ' \
                              '--node-count=1 ' \
                              '--kubernetes-version {create_version} '
        self.cmd(create_nodepool_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        upgrade_kubernetes_version_nodepool_cmd = 'aks nodepool upgrade ' \
                                               '--resource-group={resource_group} ' \
                                               '--cluster-name={name} --nodepool-name {node_pool_name} ' \
                                               '--kubernetes-version {upgrade_version} --yes ' \
                                               '--no-wait'
        self.cmd(upgrade_kubernetes_version_nodepool_cmd)

        get_nodepool_cmd = 'aks nodepool show ' \
                           '--resource-group={resource_group} ' \
                           '--cluster-name={name} ' \
                           '-n {node_pool_name} '
        self.cmd(get_nodepool_cmd, checks=[
            self.check('provisioningState', 'Upgrading')
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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
            'ssh_key_value': self.generate_ssh_keys()
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
            self.check(
                'nodeTaints[0]', 'kubernetes.azure.com/scalesetpriority=spot:NoSchedule'),
            self.check('spotMaxPrice', spot_max_price)
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
            'service_principal': sp_name,
            'client_secret': sp_password,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.check(
                'agentPoolProfiles[0].proximityPlacementGroupId', '{ppg}')
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_managed_disk(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets -c 1 ' \
                     '--node-osdisk-type=Managed ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].osDiskType', 'Managed'),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_ephemeral_disk(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets -c 1 ' \
                     '--node-osdisk-type=Ephemeral --node-osdisk-size 60 ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].osDiskType', 'Ephemeral'),
            self.check('agentPoolProfiles[0].osDiskSizeGb', 60),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_create_with_ossku(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets -c 1 ' \
                     '--os-sku Ubuntu ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].osSku', 'Ubuntu'),
        ])
        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_nodepool_add_with_ossku(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('c', 6)
        node_pool_name_second = self.create_random_name('c', 6)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'node_pool_name_second': node_pool_name_second,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--nodepool-name {node_pool_name} -c 1 ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # nodepool get-upgrades
        self.cmd('aks nodepool add '
                 '--resource-group={resource_group} '
                 '--cluster-name={name} '
                 '--name={node_pool_name_second} '
                 '--os-sku CBLMariner',
                 checks=[
                    self.check('provisioningState', 'Succeeded'),
                    self.check('osSku', 'CBLMariner'),
                 ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_add_with_ossku_windows2022(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        _, create_version = self._get_versions(resource_group_location)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': 'replace-Password1234$',
            'windows_nodepool_name': 'npwin',
            'k8s_version': create_version,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure ' \
                     '--ssh-key-value={ssh_key_value} --kubernetes-version={k8s_version}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.adminUsername', 'azureuser1')
        ])

        # add Windows2022 nodepool
        self.cmd('aks nodepool add '
                 '--resource-group={resource_group} '
                 '--cluster-name={name} '
                 '--name={windows_nodepool_name} '
                 '--node-count=1 '
                 '--os-type Windows '
                 '--os-sku Windows2022 '
                 '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AKSWindows2022Preview',
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('osSku', 'Windows2022'),
            ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westcentralus')
    def test_aks_control_plane_user_assigned_identity(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'identity_resource_id': self.generate_user_assigned_identity_resource_id(resource_group),
            # used to test update one identity to another
            'another_identity_resource_id': self.generate_user_assigned_identity_resource_id(resource_group),
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
            self.exists('identityProfile'),
            self.check(
                "identity.userAssignedIdentities | keys(@) | contains(@, '{}')".format(
                    self.kwargs.get("identity_resource_id")
                ),
                True,
            )
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
        from azure.cli.testsdk.utilities import create_random_name
        temp_path = create_random_name('kubeconfig', 24) + '.tmp'
        self.kwargs.update({'file': temp_path})
        try:
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} -f "{file}"')
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

        # update identity
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                '--enable-managed-identity --assign-identity={another_identity_resource_id} ' \
                '--yes'
        self.cmd(update_cmd, checks=[
            self.exists('identity'),
            self.check('provisioningState', 'Succeeded'),
            self.check('identity.type', "UserAssigned")
        ])

        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check(
                "identity.userAssignedIdentities | keys(@) | contains(@, '{}')".format(
                    self.kwargs.get("another_identity_resource_id")
                ),
                True,
            )
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westeurope')
    def test_aks_create_with_ingress_appgw_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '-a ingress-appgw --appgw-subnet-cidr 10.232.0.0/16 ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ingressApplicationGateway.enabled', True),
            self.check(
                'addonProfiles.ingressApplicationGateway.config.subnetCIDR', "10.232.0.0/16")
        ])

    # live only due to role assignment is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_byo_subnet_with_ingress_appgw_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        vnet_name = self.create_random_name('cliakstest', 16)
        appgw_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'aks_name': aks_name,
            'vnet_name': vnet_name,
            'appgw_name': appgw_name,
            'ssh_key_value': self.generate_ssh_keys()
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
        create_cmd = 'aks create --resource-group={resource_group} --name={aks_name} --enable-managed-identity ' \
                     '--vnet-subnet-id {vnet_id}/subnets/aks-subnet -a ingress-appgw ' \
                     '--appgw-name gateway --appgw-subnet-id {vnet_id}/subnets/appgw-subnet ' \
                     '--appgw-watch-namespace=kube-system --yes ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        aks_cluster = self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ingressApplicationGateway.enabled', True),
            self.check(
                'addonProfiles.ingressApplicationGateway.config.applicationGatewayName', "gateway"),
            self.check('addonProfiles.ingressApplicationGateway.config.subnetId',
                       vnet_id + '/subnets/appgw-subnet'),
            self.check('addonProfiles.ingressApplicationGateway.config.watchNamespace', 'kube-system')
        ]).get_output_in_json()

        addon_client_id = aks_cluster["addonProfiles"]["ingressApplicationGateway"]["identity"]["clientId"]

        self.kwargs.update({
            'addon_client_id': addon_client_id,
        })

    # live only due to role assignment is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_byo_appgw_with_ingress_appgw_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        vnet_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'aks_name': aks_name,
            'vnet_name': vnet_name,
            'ssh_key_value': self.generate_ssh_keys()
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

        show_subnet = 'network vnet subnet show -n appgw-subnet --resource-group={resource_group} --vnet-name {vnet_name} '
        subnet_details = self.cmd(show_subnet).get_output_in_json()
        if subnet_details.get("networkSecurityGroup"):
            # clean up nsg set by policy, otherwise would block creating appgw
            update_subnet = 'network vnet subnet update -n appgw-subnet --resource-group={resource_group} --vnet-name {vnet_name} ' \
                            '--nsg ""'
            self.cmd(update_subnet, checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('networkSecurityGroup', None),
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
        # add priority since this is a mandatory parameter since 2021-08-01 API version for network operations
        create_appgw = 'network application-gateway create -n appgw -g {resource_group} ' \
                       '--sku Standard_v2 --public-ip-address appgw-ip --subnet {vnet_id}/subnets/appgw-subnet --priority 1001'
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
        create_cmd = 'aks create -n {aks_name} -g {resource_group} --enable-managed-identity ' \
                     '--vnet-subnet-id {vnet_id}/subnets/aks-subnet ' \
                     '-a ingress-appgw --appgw-id {appgw_id} --yes ' \
                     '--ssh-key-value={ssh_key_value} -o json'
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_service_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        tags = "key1=value1"
        nodepool_labels = "label1=value1 label2=value2"
        nodepool_taints = "taint1=value1:PreferNoSchedule,taint2=value2:PreferNoSchedule"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'tags': tags,
            'nodepool_labels': nodepool_labels,
            'nodepool_taints': nodepool_taints,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--tags {tags} ' \
                     '--nodepool-labels {nodepool_labels} ' \
                     '--nodepool-taints {nodepool_taints} '
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
            self.check('agentPoolProfiles[0].nodeLabels.label1', 'value1'),
            self.check('agentPoolProfiles[0].nodeLabels.label2', 'value2'),
            self.check('agentPoolProfiles[0].nodeTaints[0]', 'taint1=value1:PreferNoSchedule'),
            self.check('agentPoolProfiles[0].nodeTaints[1]', 'taint2=value2:PreferNoSchedule'),
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_service_no_wait_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0

        create_version, upgrade_version = self._get_versions(
            resource_group_location)
        # kwargs for string formatting
        self.kwargs.update({
            'resource_group': resource_group,
            'name': self.create_random_name('cliakstest', 16),
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.exists('values[*].patchVersions.keys(@)[]')
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_scale_with_custom_nodepool_name_msi(self, resource_group, resource_group_location):
        create_version, _ = self._get_versions(resource_group_location)
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.check('provisioningState', 'Succeeded')
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
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('aks show -g {resource_group} -n {name}', expect_failure=True)

    # live only due to role assignment is not mocked
    @live_only()
    @AllowLargeResponse(8192)
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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
            self.check(
                'agentPoolProfiles[0].vnetSubnetId', '{vnet_subnet_id}'),
            self.check('provisioningState', 'Succeeded')
        ])

        check_role_assignment_cmd = 'role assignment list --scope={vnet_subnet_id}'
        self.cmd(check_role_assignment_cmd, checks=[
            self.check('[0].scope', '{vnet_subnet_id}')
        ])

    @AllowLargeResponse(8192)
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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

    # live only due to workspace is not mocked
    @live_only()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_service_with_monitoring_addon_msi(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.exists(
                'addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
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
            self.exists(
                'addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # disable monitoring add-on
        disable_addon_output = self.cmd('aks disable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
        ]).get_output_in_json()
        assert bool(disable_addon_output["addonProfiles"]["omsagent"]["config"]) == False

        # show again
        show_output = self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', False),
        ]).get_output_in_json()
        assert bool(show_output["addonProfiles"]["omsagent"]["config"]) == False

        # enable monitoring add-on
        self.cmd('aks enable-addons -a monitoring -g {resource_group} -n {name}', checks=[
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            self.check('addonProfiles.omsagent.config.useAADAuth', "true"),
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
            self.exists(
                'addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID'),
            StringContainCheckIgnoreCase('Microsoft.OperationalInsights'),
            StringContainCheckIgnoreCase('DefaultResourceGroup'),
            StringContainCheckIgnoreCase('DefaultWorkspace')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_blb_vmas_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=basic --vm-set-type=availabilityset --no-wait'

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
            self.check('agentPoolProfiles[0].type', 'AvailabilitySet'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.exists('kubernetesVersion'),
            self.check('networkProfile.loadBalancerSku', 'Basic'),
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

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_default_setting_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
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
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
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
        from azure.cli.testsdk.utilities import create_random_name
        temp_path = create_random_name('kubeconfig', 24) + '.tmp'
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_slb_vmss_with_default_mgd_outbound_ip_then_update_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --no-wait'

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
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
            self.exists(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs')
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

        # update managed outbound IP
        self.cmd('aks update -g {resource_group} -n {name} --load-balancer-managed-outbound-ip-count 2', checks=[
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 2),
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 2),
        ])

        # scale up
        self.cmd('aks scale -g {resource_group} -n {name} --node-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.exists('networkProfile.loadBalancerProfile.outboundIPs'),
            self.exists(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs')
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

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.exists(
                'networkProfile.loadBalancerProfile.outboundIpPrefixes'),
            self.exists(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs')
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

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_create_scale_delete_msi(self, resource_group, resource_group_location):
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
            'ssh_key_value': self.generate_ssh_keys(),
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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
        labels = "label1=value1"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add user mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --labels {labels} --node-count=1 --tags {tags}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('mode', 'User')
        ])

        # nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name),
            self.check('[0].mode', 'System'),
            self.check('[1].tags.key1', 'value1'),
            self.check('[1].nodeLabels.label1', 'value1'),
            self.check('[1].mode', 'User')
        ])

        # nodepool list in tabular format
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name} -o table', checks=[
            StringContainCheck(nodepool1_name),
            StringContainCheck(nodepool2_name)
        ])

        # nodepool add another system mode pool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name} --labels {labels} --node-count=1 --tags {tags} --mode system', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool3_name}', checks=[
            self.check('mode', 'System')
        ])

        # nodepool delete the first system pool
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --no-wait', checks=[self.is_empty()])

        # nodepool update nodepool2 to system pool
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --mode System', checks=[
            self.check('mode', 'System')
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('mode', 'System')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_update_label_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        nodepool3_name = "nodepool3"
        tags = "key1=value1"
        new_tags = "key2=value2"
        labels = "label1=value1"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --labels {labels}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            self.check('[0].mode', 'System'),
            self.check('[0].nodeLabels.label1', 'value1'),
        ])

        # nodepool update nodepool2 label
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --labels label1=value2', checks=[
            self.check('nodeLabels.label1', 'value2')
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name}', checks=[
            self.check('nodeLabels.label1', 'value2')
        ])

        # nodepool delete nodepool2 label
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --labels ', checks=[
            self.check('nodeLabels.label1', None)
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name}', checks=[
            self.check('nodeLabels.label1', None)
        ])
        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_update_taints_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool1_name = "nodepool1"
        nodepool2_name = "nodepool2"
        nodepool3_name = "nodepool3"
        taints = "key1=value1:PreferNoSchedule"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'taints': taints,
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --node-taints {taints}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # nodepool list
        self.cmd('aks nodepool list --resource-group={resource_group} --cluster-name={name}', checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group),
            StringContainCheck(nodepool1_name),
            self.check('[0].mode', 'System'),
            self.check('[0].nodeTaints[0]', 'key1=value1:PreferNoSchedule'),
        ])

        # nodepool update nodepool2 taint
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --node-taints key1=value2:PreferNoSchedule', checks=[
            self.check('nodeTaints[0]', 'key1=value2:PreferNoSchedule'),
        ])

        # nodepool show
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name}', checks=[
            self.check('nodeTaints[0]', 'key1=value2:PreferNoSchedule')
        ])

        # nodepool delete nodepool2 taint
        self.cmd('aks nodepool update --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name} --node-taints "" ')

        # nodepool show
        self.cmd(
            "aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool1_name}",
            checks=[
                self.check("nodeTaints", None),
            ],
        )

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_create_with_oidc_issuer_enabled(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-managed-identity ' \
                     '--enable-oidc-issuer ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableOIDCIssuerPreview ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('oidcIssuerProfile.enabled', True),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_update_with_oidc_issuer_enabled(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-managed-identity ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableOIDCIssuerPreview ' \
                     '--enable-oidc-issuer'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('oidcIssuerProfile.enabled', True),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_create_with_workload_identity_enabled(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = ' '.join([
            'aks', 'create', '--resource-group={resource_group}', '--name={name}', '--location={location}',
            '--enable-managed-identity', '--enable-oidc-issuer', '--enable-workload-identity',
            '--ssh-key-value={ssh_key_value}',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableWorkloadIdentityPreview,AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableOIDCIssuerPreview',
        ])
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('oidcIssuerProfile.enabled', True),
            self.check('securityProfile.workloadIdentity.enabled', True),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_update_with_workload_identity(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = ' '.join([
            'aks', 'create', '--resource-group={resource_group}', '--name={name}', '--location={location}',
            '--enable-managed-identity', '--enable-oidc-issuer',
            '--ssh-key-value={ssh_key_value}',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableWorkloadIdentityPreview,AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableOIDCIssuerPreview',
        ])
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        enable_cmd = ' '.join([
            'aks', 'update', '--resource-group={resource_group}', '--name={name}',
            '--enable-workload-identity',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableWorkloadIdentityPreview,AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableOIDCIssuerPreview',
        ])
        self.cmd(enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.workloadIdentity.enabled', True),
        ])

        disable_cmd = ' '.join([
            'aks', 'update', '--resource-group={resource_group}', '--name={name}',
            '--disable-workload-identity',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableWorkloadIdentityPreview,AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableOIDCIssuerPreview',
        ])
        self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.workloadIdentity.enabled', False),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_scale_down_mode(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool2_name = "nodepool2"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'nodepool2_name': nodepool2_name,
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)


        # nodepool create nodepool2 with Deallocate mode
            self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --scale-down-mode Deallocate --node-count=3', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # nodepool scale down nodepool2
        self.cmd('aks nodepool scale --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=1', checks=[
            self.check('count', 1)
        ])

        # nodepool show nodepool2
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('count', 1)
        ])

        # nodepool scale up nodepool2
        self.cmd('aks nodepool scale --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3', checks=[
            self.check('count', 3)
        ])

        # nodepool show nodepool2
        self.cmd('aks nodepool show --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name}', checks=[
            self.check('count', 3)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus', preserve_default_location=True)
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
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.cmd(
                'aks get-credentials -g {resource_group} -n {name} --file "{file}"')
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.close(fd)
            os.remove(temp_path)

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --node-count=3 --zones {zones}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('availabilityZones[0]', '1'),
            self.check('availabilityZones[1]', '2'),
            self.check('availabilityZones[2]', '3'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_paid_sku_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--uptime-sla'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.tier', 'Standard')
        ])
        # update to no uptime sla
        no_uptime_sla_cmd = 'aks update --resource-group={resource_group} --name={name} --no-uptime-sla'
        self.cmd(no_uptime_sla_cmd, checks=[
            self.check('sku.tier', 'Free')
        ])
        # update to uptime sla again
        uptime_sla_cmd = 'aks update --resource-group={resource_group} --name={name} --uptime-sla'
        self.cmd(uptime_sla_cmd, checks=[
            self.check('sku.tier', 'Standard')
        ])
        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_windows_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
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
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # update Windows license type
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-ahub', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.licenseType', 'Windows_Server')
        ])

        # #nodepool delete
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    def test_aks_managed_aad_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--enable-aad --aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000001')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000003 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId',
                       '00000000-0000-0000-0000-000000000003')
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    def test_aks_create_aadv1_and_update_with_managed_aad_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--aad-server-app-id 00000000-0000-0000-0000-000000000001 ' \
                     '--aad-server-app-secret fake-secret ' \
                     '--aad-client-app-id 00000000-0000-0000-0000-000000000002 ' \
                     '--aad-tenant-id d5b55040-0c14-48cc-a028-91457fc190d9 ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AADv1AllowCreate ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', None),
            self.check('aadProfile.serverAppId',
                       '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.clientAppId',
                       '00000000-0000-0000-0000-000000000002'),
            self.check('aadProfile.tenantId',
                       'd5b55040-0c14-48cc-a028-91457fc190d9')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-aad ' \
                     '--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000003 ' \
                     '--aad-tenant-id 00000000-0000-0000-0000-000000000004 -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.managed', True),
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000003'),
            self.check('aadProfile.tenantId',
                       '00000000-0000-0000-0000-000000000004')
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='southcentralus')
    def test_aks_create_nonaad_and_update_with_managed_aad_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
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
            self.check(
                'aadProfile.adminGroupObjectIDs[0]', '00000000-0000-0000-0000-000000000001'),
            self.check('aadProfile.tenantId',
                       '00000000-0000-0000-0000-000000000002')
        ])

    # @AllowLargeResponse()
    # @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    # def test_aks_upgrade_node_image_only_cluster_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
    #     self.test_resources_count = 0
        # kwargs for string formatting
    #     aks_name = self.create_random_name('cliakstest', 16)
    #     node_pool_name = self.create_random_name('c', 6)
    #     self.kwargs.update({
    #         'resource_group': resource_group,
    #         'name': aks_name,
    #         'node_pool_name': node_pool_name,
    #         'ssh_key_value': self.generate_ssh_keys()
    #     })

    #     create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
    #                  '--nodepool-name {node_pool_name} ' \
    #                  '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
    #                  '--ssh-key-value={ssh_key_value} ' \
    #                  '-o json'
    #     self.cmd(create_cmd, checks=[
    #         self.check('provisioningState', 'Succeeded')
    #     ])

    #     upgrade_node_image_only_cluster_cmd = 'aks upgrade ' \
    #                                           '-g {resource_group} ' \
    #                                           '-n {name} ' \
    #                                           '--node-image-only ' \
    #                                           '--yes'
    #     self.cmd(upgrade_node_image_only_cluster_cmd, checks=[
    #         self.check(
    #             'agentPoolProfiles[0].provisioningState', 'UpgradingNodeImageVersion')
    #     ])

    # @AllowLargeResponse()
    # @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    # def test_aks_upgrade_node_image_only_nodepool_msi(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
    #     self.test_resources_count = 0
        # kwargs for string formatting
    #     aks_name = self.create_random_name('cliakstest', 16)
    #     node_pool_name = self.create_random_name('c', 6)
    #     self.kwargs.update({
    #         'resource_group': resource_group,
    #         'name': aks_name,
    #         'node_pool_name': node_pool_name,
    #         'ssh_key_value': self.generate_ssh_keys()
    #     })

    #     create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
    #                  '--nodepool-name {node_pool_name} ' \
    #                  '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
    #                  '--ssh-key-value={ssh_key_value} ' \
    #                  '-o json'
    #     self.cmd(create_cmd, checks=[
    #         self.check('provisioningState', 'Succeeded')
    #     ])

    #     upgrade_node_image_only_nodepool_cmd = 'aks nodepool upgrade ' \
    #                                            '--resource-group={resource_group} ' \
    #                                            '--cluster-name={name} ' \
    #                                            '-n {node_pool_name} ' \
    #                                            '--node-image-only ' \
    #                                            '--no-wait'
    #     self.cmd(upgrade_node_image_only_nodepool_cmd)

    #     get_nodepool_cmd = 'aks nodepool show ' \
    #                        '--resource-group={resource_group} ' \
    #                        '--cluster-name={name} ' \
    #                        '-n {node_pool_name} '
    #     self.cmd(get_nodepool_cmd, checks=[
    #         self.check('provisioningState', 'UpgradingNodeImageVersion')
    #     ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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
            'ssh_key_value': self.generate_ssh_keys()
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
            self.check(
                'nodeTaints[0]', 'kubernetes.azure.com/scalesetpriority=spot:NoSchedule'),
            self.check('spotMaxPrice', spot_max_price)
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
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
            'ssh_key_value': self.generate_ssh_keys(),
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
            self.check(
                'agentPoolProfiles[0].proximityPlacementGroupId', '{ppg}')
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
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_stop_and_start(self, resource_group, resource_group_location):
        # This is the only test case in which the `--generate-ssh-keys` option is enabled in the `aks create` command.
        # Please do not enable this option in other test cases to avoid race conditions during concurrent testing.
        # For more details, please refer to issue #18854.
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --generate-ssh-keys'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        stop_cmd = 'aks stop --resource-group={resource_group} --name={name}'
        self.cmd(stop_cmd)

        start_cmd = 'aks start --resource-group={resource_group} --name={name}'
        self.cmd(start_cmd)

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_stop_and_start_private_cluster(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value} --enable-private-cluster'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        stop_cmd = 'aks stop --resource-group={resource_group} --name={name}'
        self.cmd(stop_cmd)

        start_cmd = 'aks start --resource-group={resource_group} --name={name}'
        self.cmd(start_cmd)

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_abort(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value} --no-wait'
        self.cmd(create_cmd)

        abort_cmd = 'aks operation-abort --resource-group={resource_group} --name={name}'
        self.cmd(abort_cmd, checks=[self.is_empty()])

        time.sleep(10)
        show_cmd = 'aks show --resource-group={resource_group} --name={name}'
        self.cmd(show_cmd, checks=[self.check('provisioningState', 'Canceled')])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_abort(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('c', 6)
        node_vm_size = 'Standard_DS2_v2'
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'ssh_key_value': self.generate_ssh_keys(),
            'node_vm_size': node_vm_size,
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
                     '--ssh-key-value={ssh_key_value} ' \
                     '--node-vm-size={node_vm_size} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # add nodepool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={node_pool_name} --node-vm-size={node_vm_size} --node-count=2', checks=[
            self.check('provisioningState', 'Succeeded')
        ])
        # stop nodepool
        self.cmd('aks nodepool stop --no-wait --resource-group={resource_group} --cluster-name={name} --nodepool-name={node_pool_name} --aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/PreviewStartStopAgentPool')

        abort_cmd = 'aks nodepool operation-abort --resource-group={resource_group} --cluster-name={name} --nodepool-name={node_pool_name}'
        self.cmd(abort_cmd, checks=[self.is_empty()])

        time.sleep(10)
        get_nodepool_cmd = 'aks nodepool show ' \
                           '--resource-group={resource_group} ' \
                           '--cluster-name={name} ' \
                           '-n {node_pool_name} '
        self.cmd(get_nodepool_cmd, checks=[
            self.check('provisioningState', 'Canceled'),
            self.check('powerState.code', 'Running')
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_confcom_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '-a confcom --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check(
                'addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "false")
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_confcom_addon_helper_enabled(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '-a confcom --enable-sgxquotehelper --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check(
                'addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "true")
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_addons_confcom_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin', None)
        ])

        enable_cmd = 'aks enable-addons --addons confcom --resource-group={resource_group} --name={name} -o json'
        self.cmd(enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check(
                'addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "false")
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_disable_addons_confcom_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '-a confcom --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', True),
            self.check(
                'addonProfiles.ACCSGXDevicePlugin.config.ACCSGXQuoteHelperEnabled', "false")
        ])

        disable_cmd = 'aks disable-addons --addons confcom --resource-group={resource_group} --name={name} -o json'
        disable_addon_output = self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.ACCSGXDevicePlugin.enabled', False),
        ]).get_output_in_json()
        assert bool(disable_addon_output["addonProfiles"]["ACCSGXDevicePlugin"]["config"]) == False

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
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
            'service_principal': sp_name,
            'client_secret': sp_password,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': self.create_random_name('p@0A', 14),
            'nodepool2_name': 'npwin',
            'new_windows_admin_password': self.create_random_name('n!C3', 14),
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure ' \
                     '--ssh-key-value={ssh_key_value}'
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

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westeurope')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_update_to_msi_cluster(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--ssh-key-value={ssh_key_value}'

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

    # live only due to workspace is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westeurope')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_update_to_msi_cluster_with_addons(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-addons monitoring ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--ssh-key-value={ssh_key_value}'
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

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_auto_upgrade_channel(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-managed-identity --auto-upgrade-channel rapid ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.upgradeChannel', 'rapid')
        ])

        # update upgrade channel
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--auto-upgrade-channel stable'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.upgradeChannel', 'stable')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_node_os_upgrade_channel(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-managed-identity ' \
                     '--node-os-upgrade-channel NodeImage ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.nodeOsUpgradeChannel', 'NodeImage')
        ])

        # update node os upgrade channel
        self.cmd('aks update --resource-group={resource_group} --name={name} --node-os-upgrade-channel None', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.nodeOsUpgradeChannel', 'None')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_auto_upgrade_channel_and_node_os_upgrade_channel(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-managed-identity ' \
                     '--auto-upgrade-channel rapid ' \
                     '--node-os-upgrade-channel NodeImage ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.upgradeChannel', 'rapid'),
            self.check('autoUpgradeProfile.nodeOsUpgradeChannel', 'NodeImage')
        ])

        # update auto upgrade channel and node os upgrade channel
        self.cmd('aks update --resource-group={resource_group} --name={name} --auto-upgrade-channel stable --node-os-upgrade-channel None', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.upgradeChannel', 'stable'),
            self.check('autoUpgradeProfile.nodeOsUpgradeChannel', 'None')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # live only due to "could not grant Managed Identity Operator permission to cluster identity at scope ..."
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_custom_kubelet_identity(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        control_plane_identity_name = self.create_random_name('cliakstest', 16)
        kubelet_identity_name = self.create_random_name('cliakstest', 16)
        new_kubelet_identity_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'control_plane_identity_name': control_plane_identity_name,
            'kubelet_identity_name': kubelet_identity_name,
            "new_kubelet_identity_name": new_kubelet_identity_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create control plane identity
        control_plane_identity = 'identity create --resource-group={resource_group} --name={control_plane_identity_name}'
        c_identity = self.cmd(control_plane_identity, checks=[
            self.check('name', control_plane_identity_name)
        ]).get_output_in_json()
        control_plane_identity_resource_id = c_identity["id"]
        assert control_plane_identity_resource_id is not None
        self.kwargs.update({
            'control_plane_identity_resource_id': control_plane_identity_resource_id,
        })

        # create kubelet identity
        kubelet_identity = 'identity create --resource-group={resource_group} --name={kubelet_identity_name}'
        k_identity = self.cmd(kubelet_identity, checks=[
            self.check('name', kubelet_identity_name)
        ]).get_output_in_json()
        kubelet_identity_resource_id = k_identity["id"]
        assert kubelet_identity_resource_id is not None
        self.kwargs.update({
            'kubelet_identity_resource_id': kubelet_identity_resource_id,
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--node-count=1 --enable-managed-identity ' \
                     '--assign-identity {control_plane_identity_resource_id} --assign-kubelet-identity {kubelet_identity_resource_id} ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.exists('identity'),
            self.exists('identityProfile'),
            self.check('provisioningState', 'Succeeded'),
            self.check('identityProfile.kubeletidentity.resourceId', kubelet_identity_resource_id),
        ])

        # create new kubelet identity
        new_kubelet_identity = 'identity create --resource-group={resource_group} --name={new_kubelet_identity_name}'
        new_identity = self.cmd(new_kubelet_identity, checks=[
            self.check('name', new_kubelet_identity_name)
        ]).get_output_in_json()
        new_kubelet_identity_resource_id = new_identity["id"]
        assert new_kubelet_identity_resource_id is not None
        self.kwargs.update({
            'new_kubelet_identity_resource_id': new_kubelet_identity_resource_id,
        })

        # update to new kubelet identity
        self.cmd('aks update --resource-group={resource_group} --name={name} --assign-kubelet-identity {new_kubelet_identity_resource_id} --yes', checks=[
            self.exists('identity'),
            self.exists('identityProfile'),
            self.check('provisioningState', 'Succeeded'),
            self.check('identityProfile.kubeletidentity.resourceId',
                       new_kubelet_identity_resource_id),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus', preserve_default_location=True)
    def test_aks_create_with_network_dataplane_cilium(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--network-plugin azure --network-plugin-mode overlay --ssh-key-value={ssh_key_value} ' \
                     '--pod-cidr 10.244.0.0/16 --node-count 1 ' \
                     '--network-dataplane=cilium ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/CiliumDataplanePreview,AKSHTTPCustomFeatures=Microsoft.ContainerService/AzureOverlayPreview'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.podCidr', '10.244.0.0/16'),
            self.check('networkProfile.networkPlugin', 'azure'),
            self.check('networkProfile.networkPluginMode', 'overlay'),
            self.check('networkProfile.networkPolicy', 'cilium'),
            self.check('networkProfile.networkDataplane', 'cilium'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus', preserve_default_location=True)
    def test_aks_enable_utlra_ssd(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --node-vm-size Standard_D2s_v3 ' \
                     '--zones 1 2 3 --enable-ultra-ssd --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_browse(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # test aks browse cmd
        subscription_id = self.get_subscription_id()
        browse_cmd = 'aks browse --resource-group={resource_group} --name={name} --listen-address=127.0.0.1 --listen-port=8080 --disable-browser'
        self.cmd(browse_cmd, checks=[
            StringCheck("Kubernetes resources view on https://portal.azure.com/#resource/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerService/managedClusters/{}/workloads".format(subscription_id, resource_group, aks_name))
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # live only since execution of `kubectl get pods` in subprocess and cannot be mocked by testsdk
    @unittest.skip("Unable to create a cluster with version lower than 1.19.0 that meets the test requirements")
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_browse_legacy(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # find the latest version lower than 1.19.0
        versions = self._get_versions_by_location(resource_group_location)
        try:
            legacy_version = next(x for x in versions if version_to_tuple(x) < version_to_tuple('1.19.0'))
        except StopIteration:
            raise CLIInternalError("No version lower than '1.19.0' is supported in region '{}'!".format(resource_group_location))

        self.kwargs.update({
            'k8s_version': legacy_version,
            'dashboard': "kube-dashboard",

        })
        # create legacy cluster and enable kube-dashboard addon
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value} ' \
                     '-k {k8s_version} -a {dashboard}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('kubernetesVersion', legacy_version),
            self.check('addonProfiles.{}.enabled'.format(CONST_KUBE_DASHBOARD_ADDON_NAME), True)
        ])

        # install kubectl
        try:
            subprocess.call(["az", "aks", "install-cli"])
        except subprocess.CalledProcessError as err:
            raise CLIInternalError("Failed to install kubectl with error: '{}'!".format(err))

        # create test hook file
        hook_file_path = get_test_data_file_path("test_aks_browse_legacy.hook")
        test_hook_data = {
            "configs": {
                "enableTimeout": True,
                "timeoutInterval": 10,
            }
        }
        with open(hook_file_path, "w") as f:
            json.dump(test_hook_data, f)

        try:
            # test aks browse cmd
            browse_cmd = 'aks browse --resource-group={resource_group} --name={name} --listen-address=1.1.1.1 --listen-port=8080 --disable-browser'
            self.cmd(browse_cmd, checks=[
                StringCheck("Test Invalid Address! Test Passed!")
            ])
        # clean up test hook file even if test failed
        finally:
            if os.path.exists(hook_file_path):
                # delete file
                os.remove(hook_file_path)

            # delete cluster
            self.cmd(
                'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # live only, otherwise the current recording mechanism will also record the binary files of
    # kubectl and kubelogin resulting in the cassette file size exceeding 100MB
    @live_only()
    def test_aks_install_kubectl(self):
        ctl_fd, ctl_temp_file = tempfile.mkstemp()
        login_fd, login_temp_file = tempfile.mkstemp()
        version = "latest"
        install_cmd = 'aks install-cli --client-version={} --install-location={} --base-src-url={} ' \
                      '--kubelogin-version={} --kubelogin-install-location={} --kubelogin-base-src-url={}'.format(version, ctl_temp_file, "", version, login_temp_file, "")

        # install kubectl & kubelogin
        try:
            self.cmd(install_cmd, checks=[self.is_empty()])
            self.assertGreater(os.path.getsize(ctl_temp_file), 0)
            self.assertGreater(os.path.getsize(login_temp_file), 0)
        finally:
            os.close(ctl_fd)
            os.close(login_fd)
            os.remove(ctl_temp_file)
            os.remove(login_temp_file)

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_autoscaler_then_update(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        tags = "tag1=v1 tag2=v2"
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'tags': tags,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --tags {tags} ' \
                     '--ssh-key-value={ssh_key_value} --enable-cluster-autoscaler ' \
                     '-c 1 --min-count 1 --max-count 5 ' \
                     '--cluster-autoscaler-profile scan-interval=30s expander=least-waste'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoScalerProfile.scanInterval', '30s'),
            self.check('autoScalerProfile.expander', 'least-waste'),
            self.check('agentPoolProfiles[0].enableAutoScaling', True),
            self.check('agentPoolProfiles[0].minCount', 1),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].maxCount', 5),
            self.check('tags.tag1', 'v1'),
            self.check('tags.tag2', 'v2'),
        ])

        # disable autoscaler and update tags
        new_tags = "tag3=v3"
        self.kwargs.update({'tags': new_tags})
        disable_autoscaler_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                                 '--tags {tags} --disable-cluster-autoscaler'
        self.cmd(disable_autoscaler_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].enableAutoScaling', False),
            self.check('agentPoolProfiles[0].minCount', None),
            self.check('agentPoolProfiles[0].maxCount', None),
            self.check('tags.tag1', None),
            self.check('tags.tag2', None),
            self.check('tags.tag3', "v3"),
        ])

        # enable autoscaler and update tags
        other_new_tags = ""
        self.kwargs.update({'tags': other_new_tags})
        enable_autoscaler_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                                '--tags {tags} --enable-cluster-autoscaler --min-count 2 --max-count 5'
        self.cmd(enable_autoscaler_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].enableAutoScaling', True),
            self.check('agentPoolProfiles[0].minCount', 2),
            self.check('agentPoolProfiles[0].maxCount', 5),
            self.check('tags', None),
        ])

        # clear autoscaler profile
        clear_autoscaler_profile_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                                       '--cluster-autoscaler-profile=""'
        self.cmd(clear_autoscaler_profile_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoScalerProfile.scanInterval', '10s'),
            self.check('autoScalerProfile.expander', 'random')
        ])

        # update autoscaler
        update_autoscaler_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                                '--update-cluster-autoscaler --min-count 3 --max-count 101'
        self.cmd(update_autoscaler_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].minCount', 3),
            self.check('agentPoolProfiles[0].maxCount', 101)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_autoscaler_then_update(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        np_name = self.create_random_name('clinp', 12)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'nodepool_name': np_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} -c 1'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].count', 1),
        ])

        add_nodepool_cmd = 'aks nodepool add -g {resource_group} --cluster-name {name} -n {nodepool_name} ' \
                     '--mode user --enable-cluster-autoscaler -c 0 --min-count 0 --max-count 3'
        self.cmd(add_nodepool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('count', 0),
            self.check('minCount', 0),
            self.check('maxCount', 3),
        ])

        update_nodepool_cmd = 'aks nodepool update -g {resource_group} --cluster-name {name} -n {nodepool_name} ' \
                     '--update-cluster-autoscaler --min-count 1 --max-count 101'
        self.cmd(update_nodepool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('minCount', 1),
            self.check('maxCount', 101),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])
        
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_drain_timeout(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        np_name = self.create_random_name('clinp', 12)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'nodepool_name': np_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} -c 1'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        add_nodepool_cmd = 'aks nodepool add -g {resource_group} --cluster-name {name} -n {nodepool_name} ' \
                     '--mode user --drain-timeout 10'
        self.cmd(add_nodepool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('upgradeSettings.drainTimeoutInMinutes', 10),
        ])

        update_nodepool_cmd = 'aks nodepool update -g {resource_group} --cluster-name {name} -n {nodepool_name} ' \
                      '--drain-timeout 60'
        self.cmd(update_nodepool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('upgradeSettings.drainTimeoutInMinutes', 60),
        ])

        #actually running an upgrade is too expensive for these tests.

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westcentralus')
    def test_aks_nodepool_stop_and_start(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool_name = self.create_random_name('c', 6)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'nodepool_name' : nodepool_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create aks cluster
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])
        # add nodepool
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool_name} --node-count=2', checks=[
            self.check('provisioningState', 'Succeeded')
        ])
        # stop nodepool
        self.cmd('aks nodepool stop --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool_name}', checks=[
            self.check('powerState.code', 'Stopped')
        ])
        #start nodepool
        self.cmd('aks nodepool start --resource-group={resource_group} --cluster-name={name} --nodepool-name={nodepool_name}', checks=[
            self.check('powerState.code', 'Running')
        ])
        # delete AKS cluster
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_loadbalancer_then_update(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --load-balancer-sku=standard ' \
                     '--load-balancer-managed-outbound-ip-count 2 --load-balancer-outbound-ports 2048 ' \
                     '--load-balancer-idle-timeout 5'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.loadBalancerProfile.allocatedOutboundPorts', 2048),
            self.check('networkProfile.loadBalancerProfile.idleTimeoutInMinutes', 5),
            self.check('networkProfile.loadBalancerProfile.effectiveOutboundIPs | length(@) == `2`', True)
        ])

        # update
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--load-balancer-outbound-ports 1024 --load-balancer-idle-timeout 10'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.loadBalancerProfile.allocatedOutboundPorts', 1024),
            self.check('networkProfile.loadBalancerProfile.idleTimeoutInMinutes', 10)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_node_public_ip(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        ipprefix_name = self.create_random_name('cliaksipprefix', 20)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
            'ipprefix_name': ipprefix_name
        })

        # create public ip prefix
        ipprefix_id = self.cmd('az network public-ip prefix create -g {rg} -n {ipprefix_name} --location {location} --length 29'). \
            get_output_in_json().get("id")

        self.kwargs.update({
            'ipprefix_id': ipprefix_id
        })

        # create
        subscription_id = self.get_subscription_id()
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --enable-node-public-ip --node-public-ip-prefix-id {ipprefix_id}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].enableNodePublicIp', True),
            self.check('agentPoolProfiles[0].nodePublicIpPrefixId', "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/publicIPPrefixes/{}".format(subscription_id, resource_group, ipprefix_name))
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_network_cidr(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --pod-cidr 10.244.0.0/16 --service-cidr 10.0.0.0/16 ' \
                     '--dns-service-ip 10.0.2.10 --network-plugin kubenet --network-policy calico'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.podCidr', '10.244.0.0/16'),
            self.check('networkProfile.serviceCidr', '10.0.0.0/16'),
            self.check('networkProfile.dnsServiceIp', '10.0.2.10'),
            self.check('networkProfile.networkPlugin', 'kubenet'),
            self.check('networkProfile.networkPolicy', 'calico')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # live only due to dependency `_add_role_assignment` is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_attach_acr(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        acr_name = self.create_random_name('cliaksacr', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys(),
            'service_principal': sp_name,
            'client_secret': sp_password,
            'acr_name': acr_name
        })

        # create acr
        create_acr_cmd = 'acr create -g {resource_group} -n {acr_name} --sku basic'
        self.cmd(create_acr_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--ssh-key-value={ssh_key_value} --attach-acr={acr_name}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('servicePrincipalProfile.clientId', sp_name)
        ])

         # add Mariner node pool
        node_pool_cmd = 'aks nodepool add --resource-group={resource_group} --cluster-name={name} ' \
                        '-n marinerpool --os-sku mariner'
        self.cmd(node_pool_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # install kubectl
        try:
            subprocess.call(["az", "aks", "install-cli"])
        except subprocess.CalledProcessError as err:
            raise CLIInternalError("Failed to install kubectl with error: '{}'!".format(err))

        # create test hook file
        hook_file_path = get_test_data_file_path("test_aks_create_attach_acr.hook")
        test_hook_data = {
            "configs": {
                "returnOutput": True,
            }
        }
        with open(hook_file_path, "w") as f:
            json.dump(test_hook_data, f)

        try:
            # get credential
            fd, browse_path = tempfile.mkstemp()
            self.kwargs.update(
                {
                    "browse_path": browse_path,
                }
            )
            try:
                get_credential_cmd = "aks get-credentials -n {name} -g {resource_group} -f {browse_path}"
                self.cmd(get_credential_cmd)
            finally:
                os.close(fd)
            # get node name
            k_get_node_cmd = ["kubectl", "get", "node", "-l", "kubernetes.azure.com/os-sku=Ubuntu", "-o", "name", "--kubeconfig", browse_path]
            k_get_node_output = subprocess.check_output(
                k_get_node_cmd,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
            node_names = k_get_node_output.split("\n")
            node_name = node_names[0].strip().strip("node/").strip()
            self.kwargs.update(
                {
                    "node_name": node_name,
                }
            )
            # check acr from Ubuntu node
            check_cmd = "aks check-acr -n {name} -g {resource_group} --acr {acr_name}.azurecr.io --node-name {node_name}"
            self.cmd(
                check_cmd,
                checks=[
                    StringContainCheck("Your cluster can pull images from {}.azurecr.io!".format(acr_name)),
                ],
            )
            # check acr from Mariner node
            k_get_mariner_node_cmd = ["kubectl", "get", "node", "-l", "kubernetes.azure.com/os-sku=Mariner", "-o", "name", "--kubeconfig", browse_path]
            k_get_node_output = subprocess.check_output(
                k_get_mariner_node_cmd,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
            mariner_node_names = k_get_node_output.split("\n")
            mariner_node_name = mariner_node_names[0].strip().strip("node/").strip()
            self.kwargs.update(
                {
                    "mariner_node_name": mariner_node_name,
                }
            )
            check_mariner_cmd = "aks check-acr -n {name} -g {resource_group} --acr {acr_name}.azurecr.io --node-name {mariner_node_name}"
            self.cmd(
                check_mariner_cmd,
                checks=[
                    StringContainCheck("Your cluster can pull images from {}.azurecr.io!".format(acr_name)),
                ],
            )
        # clean up test hook file even if test failed
        finally:
            if os.path.exists(hook_file_path):
                # delete file
                os.remove(hook_file_path)

            # delete cluster
            self.cmd(
                'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # live only due to role assignment is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_with_outbound_type_udr(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        vnet_name = self.create_random_name('cliaksvnet', 20)
        aks_subnet_name = self.create_random_name('cliakssubnet', 20)
        fw_subnet_name = 'AzureFirewallSubnet'  # this must not be changed
        fw_publicip_name = self.create_random_name('clifwpublicip', 20)
        fw_name = self.create_random_name('cliaksfw', 20)
        fw_ipconfig_name = self.create_random_name('cliaksfwipconfig', 20)
        fw_route_table_name = self.create_random_name('cliaksfwrt', 20)
        fw_route_name = self.create_random_name('cliaksfwrn', 20)
        fw_route_internet_name = self.create_random_name('cliaksfwrin', 20)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
            'service_principal': sp_name,
            'client_secret': sp_password,
            'vnet_name': vnet_name,
            'aks_subnet_name': aks_subnet_name,
            'fw_subnet_name': fw_subnet_name,
            'fw_publicip_name': fw_publicip_name,
            'fw_name': fw_name,
            'fw_ipconfig_name': fw_ipconfig_name,
            'fw_route_table_name': fw_route_table_name,
            'fw_route_name': fw_route_name,
            'fw_route_internet_name': fw_route_internet_name
        })

        # dedicated virtual network with AKS subnet
        aks_subnet_cmd = 'network vnet create -g {resource_group} -n {vnet_name} ' \
                         '--address-prefixes 10.42.0.0/16 --subnet-name {aks_subnet_name} ' \
                         '--subnet-prefix 10.42.1.0/24'
        self.cmd(aks_subnet_cmd, checks=[
            self.check('newVNet.provisioningState', 'Succeeded'),
            self.check('newVNet.addressSpace.addressPrefixes[0]', '10.42.0.0/16'),
            self.check('newVNet.subnets[0].addressPrefix', '10.42.1.0/24'),
            self.check('newVNet.subnets[0].name', aks_subnet_name),
        ])

        # dedicated subnet for Azure Firewall (Firewall name cannot be changed)
        fw_subnet_cmd = 'network vnet subnet create -g {resource_group} --vnet-name {vnet_name} ' \
                         '--address-prefixes 10.42.2.0/24 --name {fw_subnet_name}'
        self.cmd(fw_subnet_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addressPrefix', '10.42.2.0/24'),
            self.check('name', fw_subnet_name)
        ])

        # create public ip
        public_ip_cmd = 'network public-ip create -g {resource_group} -n {fw_publicip_name} --sku Standard'
        self.cmd(public_ip_cmd, checks=[
            self.check('publicIp.name', fw_publicip_name),
            self.check('publicIp.sku.name', 'Standard')
        ])

        # install Azure Firewall preview CLI extension
        try:
            subprocess.call(["az", "extension", "add", "--name", "azure-firewall", "--yes"])
        except subprocess.CalledProcessError as err:
            raise CLIInternalError("Failed to install azure-firewall extension with error: '{}'!".format(err))

        # deploy Azure Firewall
        deploy_azfw_cmd = 'network firewall create -g {resource_group} -n {fw_name} --enable-dns-proxy true'
        self.cmd(deploy_azfw_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('name', fw_name),
            self.check('additionalProperties.\"Network.DNS.EnableProxy\"', 'true')
        ])

        # configure Firewall IP Config
        config_fw_ip_config_cmd = 'network firewall ip-config create -g {resource_group} -f {fw_name} -n {fw_ipconfig_name} --public-ip-address {fw_publicip_name} --vnet-name {vnet_name}'
        self.cmd(config_fw_ip_config_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        get_fw_public_ip_cmd = 'network public-ip show -g {resource_group} -n {fw_publicip_name}'
        fw_public_ip = self.cmd(get_fw_public_ip_cmd).get_output_in_json()
        fw_public_ip_address = fw_public_ip.get("ipAddress")

        get_fw_private_ip_cmd = 'network firewall show -g {resource_group} -n {fw_name}'
        fw_private_ip = self.cmd(get_fw_private_ip_cmd).get_output_in_json()
        fw_private_ip_address = fw_private_ip.get("ipConfigurations")[0].get("privateIPAddress")

        self.kwargs.update({
            'fw_public_ip_address': fw_public_ip_address,
            'fw_private_ip_address': fw_private_ip_address
        })

        # create UDR and add a route for Azure Firewall
        create_route_table_cmd = 'network route-table create -g {resource_group} --name {fw_route_table_name}'
        self.cmd(create_route_table_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        create_route_cmd = 'network route-table route create -g {resource_group} --name {fw_route_name} ' \
                           '--route-table-name {fw_route_table_name} --address-prefix 0.0.0.0/0 ' \
                           '--next-hop-type VirtualAppliance --next-hop-ip-address {fw_private_ip_address}'
        self.cmd(create_route_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        create_route_internet_cmd = 'network route-table route create -g {resource_group} --name {fw_route_internet_name} ' \
                                    '--route-table-name {fw_route_table_name} --address-prefix {fw_public_ip_address}/32 ' \
                                    '--next-hop-type Internet'
        self.cmd(create_route_internet_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # add FW Network Rules
        create_udp_network_rule_cmd = "network firewall network-rule create -g {resource_group} -f {fw_name} " \
                                      "--collection-name 'aksfwnr' -n 'apiudp' --protocols 'UDP' --source-addresses '*' " \
                                      "--destination-addresses 'AzureCloud.{location}' --destination-ports 1194 " \
                                      "--action allow --priority 100"
        self.cmd(create_udp_network_rule_cmd, checks=[
            self.check('destinationAddresses[0]', 'AzureCloud.{}'.format(resource_group_location))
        ])

        create_tcp_network_rule_cmd = "network firewall network-rule create -g {resource_group} -f {fw_name} " \
                                      "--collection-name 'aksfwnr' -n 'apitcp' --protocols 'TCP' --source-addresses '*' " \
                                      "--destination-addresses 'AzureCloud.{location}' --destination-ports 9000"
        self.cmd(create_tcp_network_rule_cmd, checks=[
            self.check('destinationAddresses[0]', 'AzureCloud.{}'.format(resource_group_location))
        ])

        create_time_newtork_rule_cmd = "network firewall network-rule create -g {resource_group} -f {fw_name} " \
                                       "--collection-name 'aksfwnr' -n 'time' --protocols 'UDP' --source-addresses '*' " \
                                       "--destination-fqdns 'ntp.ubuntu.com' --destination-ports 123"
        self.cmd(create_time_newtork_rule_cmd, checks=[
            self.check('destinationFqdns[0]', 'ntp.ubuntu.com')
        ])

        # add FW Application Rules
        create_app_rule_cmd = "network firewall application-rule create -g {resource_group} -f {fw_name} " \
                              "--collection-name 'aksfwar' -n 'fqdn' --protocols 'http=80' 'https=443' --source-addresses '*' " \
                              "--fqdn-tags 'AzureKubernetesService' --action allow --priority 100"
        self.cmd(create_app_rule_cmd, checks=[
            self.check('fqdnTags[0]', 'AzureKubernetesService')
        ])

        # associate route table with next hop to Firewall to the AKS subnet
        update_route_table_cmd = 'network vnet subnet update -g {resource_group} --vnet-name {vnet_name} --name {aks_subnet_name} --route-table {fw_route_table_name}'
        self.cmd(update_route_table_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        subscription_id = self.get_subscription_id()
        vnet_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}".format(subscription_id, resource_group, vnet_name)
        vnet_subnet_id = "{}/subnets/{}".format(vnet_id, aks_subnet_name)
        self.kwargs.update({
            'vnet_id': vnet_id,
            'vnet_subnet_id': vnet_subnet_id
        })

        # role assignment
        role_assignment_cmd = 'role assignment create --assignee={service_principal} --scope {vnet_id} --role "Network Contributor"'
        self.cmd(role_assignment_cmd, checks=[
            self.check('scope', vnet_id)
        ])

        # create cluster
        subscription_id = self.get_subscription_id()
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --outbound-type userDefinedRouting --vnet-subnet-id {vnet_subnet_id} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--api-server-authorized-ip-ranges {fw_public_ip_address}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.outboundType', 'userDefinedRouting')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

        # uninstall Azure Firewall preview CLI extension
        try:
            subprocess.call(["az", "extension", "remove", "--name", "azure-firewall"])
        except subprocess.CalledProcessError as err:
            raise CLIInternalError("Failed to uninstall azure-firewall extension with error: '{}'!".format(err))

    # live only due to key vault creation is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_node_osdisk_diskencryptionset(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        kv_name = self.create_random_name('cliakskv', 20)
        key_name = self.create_random_name('cliakskey', 20)
        des_name = self.create_random_name('cliaksdes', 20)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys(),
            'kv_name': kv_name,
            'key_name': key_name,
            'des_name': des_name
        })

        # create key vault
        create_kv_cmd = 'keyvault create -n {kv_name} -g {resource_group} --enable-purge-protection true'
        self.cmd(create_kv_cmd, checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('name', kv_name)
        ])

        # create key
        create_key_cmd = 'keyvault key create --vault-name {kv_name} --name {key_name} --protection software'
        self.cmd(create_key_cmd, checks=[
            self.check('attributes.enabled', True)
        ])

        # get key url and key vault id
        get_kid_cmd = 'keyvault key show --vault-name {kv_name} --name {key_name}'
        key_url = self.cmd(get_kid_cmd).get_output_in_json().get("key").get("kid")
        subscription_id = self.get_subscription_id()
        kv_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.KeyVault/vaults/{}".format(subscription_id, resource_group, kv_name)
        self.kwargs.update({
            'key_url': key_url,
            'kv_id': kv_id
        })

        # create disk-encryption-set
        create_des_cmd = 'disk-encryption-set create -n {des_name} -g {resource_group} --source-vault {kv_id} --key-url {key_url}'
        self.cmd(create_des_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # get disk-encryption-set identity and id
        get_des_identity_cmd = 'disk-encryption-set show -n {des_name}  -g {resource_group}'
        des_identity = self.cmd(get_des_identity_cmd).get_output_in_json().get("identity").get("principalId")
        des_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/diskEncryptionSets/{}".format(subscription_id, resource_group, des_name)
        self.kwargs.update({
            'des_identity': des_identity,
            'des_id': des_id
        })

        # update key vault security policy settings
        update_kv_cmd = 'keyvault set-policy -n {kv_name} -g {resource_group} --object-id {des_identity} --key-permissions wrapkey unwrapkey get'
        self.cmd(update_kv_cmd, checks=[
            self.check('properties.accessPolicies[1].objectId', des_identity)
        ])

        # create cluster
        create_cmd = 'aks create -n {name} -g {resource_group} --ssh-key-value={ssh_key_value} --node-osdisk-diskencryptionset-id {des_id}'
        self.cmd(create_cmd, checks=[
            self.check('diskEncryptionSetId', des_id)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # need to register feature 'Microsoft.Compute/EncryptionAtHost'
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_enable_encryption(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --enable-encryption-at-host'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].enableEncryptionAtHost', True)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_enable_azure_rbac(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --enable-aad --enable-azure-rbac'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('aadProfile.enableAzureRbac', True),
            self.check('aadProfile.managed', True),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_disable_rbac(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --disable-rbac'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('enableRbac', False)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # live only due to workspace is not mocked correctly
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_defender(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--ssh-key-value={ssh_key_value} --enable-defender'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.defender.securityMonitoring.enabled', True)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # live only due to workspace is not mocked correctly
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_update_with_defender(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # update to enable defender
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-defender', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.defender.securityMonitoring.enabled', True)
        ])

         # update to disable defender
        self.cmd('aks update --resource-group={resource_group} --name={name} --disable-defender', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.defender.securityMonitoring.enabled', False)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_azuremonitormetrics(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        node_vm_size = 'standard_d2s_v3'
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
            'node_vm_size': node_vm_size
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--ssh-key-value={ssh_key_value} --node-vm-size={node_vm_size} --enable-managed-identity ' \
                     '--enable-azure-monitor-metrics --enable-windows-recording-rules --output=json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # azuremonitor metrics will be set to false after initial creation command as its in the
        # postprocessing step that we do an update to enable it. Adding a wait for the second put request
        # in addonput.py which enables the Azure Monitor Metrics addon as all the DC* resources
        # have now been created.
        wait_cmd = ' '.join([
            'aks', 'wait', '--resource-group={resource_group}', '--name={name}', '--updated',
            '--interval 60', '--timeout 300',
        ])
        self.cmd(wait_cmd, checks=[
            self.is_empty(),
        ])

        self.cmd('aks show -g {resource_group} -n {name} --output=json', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('azureMonitorProfile.metrics.enabled', True),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_update_with_azuremonitormetrics(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        node_vm_size = 'standard_d2s_v3'
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
            'node_vm_size': node_vm_size,
        })

        # create: without enable-azure-monitor-metrics
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} --ssh-key-value={ssh_key_value} --node-vm-size={node_vm_size} --enable-managed-identity --output=json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.not_exists('azureMonitorProfile.metrics'),
        ])

        # update: enable-azure-monitor-metrics
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --yes --output=json ' \
                     '--enable-azure-monitor-metrics --enable-managed-identity --enable-windows-recording-rules'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('azureMonitorProfile.metrics.enabled', True),
        ])

        # update: disable-azure-monitor-metrics
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --yes --output=json ' \
                     '--disable-azure-monitor-metrics'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('azureMonitorProfile.metrics.enabled', False),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    # live only due to dependency `_add_role_assignment` is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_update_attatch_acr(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        acr_name = self.create_random_name('cliaksacr', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys(),
            'service_principal': sp_name,
            'client_secret': sp_password,
            'acr_name': acr_name
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('servicePrincipalProfile.clientId', sp_name)
        ])

        # create acr
        create_acr_cmd = 'acr create -g {resource_group} -n {acr_name} --sku basic'
        self.cmd(create_acr_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # build command to check role assignment
        subscription_id = self.get_subscription_id()
        acr_scope = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/registries/{}".format(
            subscription_id, resource_group, acr_name
        )
        self.kwargs.update({"sp_name": sp_name, "acr_scope": acr_scope})
        role_assignment_check_cmd = (
            "role assignment list --assignee {sp_name} --scope {acr_scope}"
        )

        # attach acr
        attach_cmd = "aks update --resource-group={resource_group} --name={name} --attach-acr={acr_name}"
        self.cmd(attach_cmd)

        # check role assignment
        self.cmd(role_assignment_check_cmd, checks=[self.check('length(@) == `1`', True)])

        # detach acr
        attach_cmd = 'aks update --resource-group={resource_group} --name={name} --detach-acr={acr_name}'
        self.cmd(attach_cmd)

        # check role assignment
        self.cmd(role_assignment_check_cmd, checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_create_with_SP_then_update_to_user_assigned_identity(self, resource_group, resource_group_location, sp_name, sp_password):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys(),
            'service_principal': sp_name,
            'client_secret': sp_password,
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('servicePrincipalProfile.clientId', sp_name)
        ])

        # update to assignd identity
        identity_resource_id = self.generate_user_assigned_identity_resource_id(resource_group)
        self.kwargs.update({
            "identity_resource_id": identity_resource_id
        })
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-managed-identity --assign-identity={identity_resource_id} --yes'
        self.cmd(
            update_cmd,
            checks=[
                self.check(
                    "identity.userAssignedIdentities | keys(@) | contains(@, '{}')".format(identity_resource_id),
                    True,
                )
            ],
        )

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_disable_local_accounts(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--enable-aad --aad-admin-group-object-ids 00000000-0000-0000-0000-000000000001 ' \
                     '--disable-local-accounts --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('disableLocalAccounts', True)
        ])

        # update to enable local accounts
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-local-accounts', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('disableLocalAccounts', False)
        ])

         # update to disable local accounts
        self.cmd('aks update --resource-group={resource_group} --name={name} --disable-local-accounts', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('disableLocalAccounts', True)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_openservicemesh_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '-a open-service-mesh --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.openServiceMesh.enabled', True),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_openservicemesh_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.openServiceMesh', None),
        ])

        enable_cmd = 'aks enable-addons --addons open-service-mesh --resource-group={resource_group} --name={name} -o json'
        self.cmd(enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.openServiceMesh.enabled', True),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_disable_openservicemesh_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-managed-identity ' \
                     '-a open-service-mesh --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.openServiceMesh.enabled', True),
        ])

        disable_cmd = 'aks disable-addons --addons open-service-mesh --resource-group={resource_group} --name={name} -o json'
        disable_addon_output = self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.openServiceMesh.enabled', False),
        ]).get_output_in_json()
        assert bool(disable_addon_output["addonProfiles"]["openServiceMesh"]["config"]) == False

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_azurekeyvaultsecretsprovider_addon(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '-a azure-keyvault-secrets-provider --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.enabled', True),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.enableSecretRotation', "false"),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.rotationPollInterval', "2m")
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_addon_with_azurekeyvaultsecretsprovider_with_secret_rotation(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '-a azure-keyvault-secrets-provider --enable-secret-rotation --rotation-poll-interval 30m ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.enabled', True),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.enableSecretRotation', "true"),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.rotationPollInterval', "30m")
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_addon_with_azurekeyvaultsecretsprovider(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('addonProfiles.azureKeyvaultSecretsProvider', None)
        ])

        enable_cmd = 'aks enable-addons --addons azure-keyvault-secrets-provider --resource-group={resource_group} --name={name} -o json'
        self.cmd(enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.enabled', True),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.enableSecretRotation', "false")
        ])

        update_enable_cmd = 'aks update --resource-group={resource_group} --name={name} --enable-secret-rotation --rotation-poll-interval 120s -o json'
        self.cmd(update_enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.enabled', True),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.enableSecretRotation', "true"),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.rotationPollInterval', "120s")
        ])

        update_disable_cmd = 'aks update --resource-group={resource_group} --name={name} --disable-secret-rotation -o json'
        self.cmd(update_disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.enabled', True),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.enableSecretRotation', "false"),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.rotationPollInterval', "120s")
        ])

        disable_cmd = 'aks disable-addons --addons azure-keyvault-secrets-provider --resource-group={resource_group} --name={name} -o json'
        disable_addon_output = self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.enabled', False),
        ]).get_output_in_json()
        assert bool(disable_addon_output["addonProfiles"]["azureKeyvaultSecretsProvider"]["config"]) == False

        enable_with_secret_rotation_cmd = 'aks enable-addons --addons azure-keyvault-secrets-provider --enable-secret-rotation --rotation-poll-interval 1h --resource-group={resource_group} --name={name} -o json'
        self.cmd(enable_with_secret_rotation_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.enabled', True),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.enableSecretRotation', "true"),
            self.check(
                'addonProfiles.azureKeyvaultSecretsProvider.config.rotationPollInterval', "1h")
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_and_update_with_csi_drivers_extensibility(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value} -o json \
                        --disable-disk-driver \
                        --disable-file-driver \
                        --disable-snapshot-controller'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.diskCsiDriver.enabled', False),
            self.check('storageProfile.fileCsiDriver.enabled', False),
            self.check('storageProfile.snapshotController.enabled', False),
        ])

        # check standard reconcile scenario
        update_cmd = 'aks update --resource-group={resource_group} --name={name} -y -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.diskCsiDriver.enabled', False),
            self.check('storageProfile.fileCsiDriver.enabled', False),
            self.check('storageProfile.snapshotController.enabled', False),
        ])

        enable_cmd = 'aks update --resource-group={resource_group} --name={name} -o json \
                        --enable-disk-driver \
                        --enable-file-driver \
                        --enable-snapshot-controller'
        self.cmd(enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.diskCsiDriver.enabled', True),
            self.check('storageProfile.fileCsiDriver.enabled', True),
            self.check('storageProfile.snapshotController.enabled', True),
        ])

        # check standard reconcile scenario
        update_cmd = 'aks update --resource-group={resource_group} --name={name} -y -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.diskCsiDriver.enabled', True),
            self.check('storageProfile.fileCsiDriver.enabled', True),
            self.check('storageProfile.snapshotController.enabled', True),
        ])

        disable_cmd = 'aks update --resource-group={resource_group} --name={name} -o json \
                        --disable-disk-driver \
                        --disable-file-driver \
                        --disable-snapshot-controller -y'
        self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.diskCsiDriver.enabled', False),
            self.check('storageProfile.fileCsiDriver.enabled', False),
            self.check('storageProfile.snapshotController.enabled', False),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_standard_csi_drivers(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # check standard creation scenario
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.diskCsiDriver.enabled', True),
            self.check('storageProfile.diskCsiDriver.version', None),
            self.check('storageProfile.fileCsiDriver.enabled', True),
            self.check('storageProfile.snapshotController.enabled', True),
        ])

        # check standard reconcile scenario
        update_cmd = 'aks update --resource-group={resource_group} --name={name} -y -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.diskCsiDriver.enabled', True),
            self.check('storageProfile.diskCsiDriver.version', None),
            self.check('storageProfile.fileCsiDriver.enabled', True),
            self.check('storageProfile.snapshotController.enabled', True),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap', preserve_default_location=True)
    def test_aks_create_with_standard_blob_csi_driver(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # check standard creation scenario
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', None),
        ])

        # check standard reconcile scenario
        update_cmd = 'aks update --resource-group={resource_group} --name={name} -y -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', None),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap', preserve_default_location=True)
    def test_aks_create_and_update_with_blob_csi_driver(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create aks with blob driver
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value} -o json \
                        --enable-blob-driver'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', True),
        ])

        # check standard reconcile scenario
        update_cmd = 'aks update --resource-group={resource_group} --name={name} -y -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', True),
        ])

        # disable blob driver
        disable_cmd = 'aks update --resource-group={resource_group} --name={name} -o json \
                        --disable-blob-driver -y'
        self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', False),
        ])

        # check standard reconcile scenario
        update_cmd = 'aks update --resource-group={resource_group} --name={name} -y -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', False),
        ])

        # enable blob driver
        enable_cmd = 'aks update --resource-group={resource_group} --name={name} -o json \
                        --enable-blob-driver -y'
        self.cmd(enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', True),
        ])

        # check standard reconcile scenario
        update_cmd = 'aks update --resource-group={resource_group} --name={name} -y -o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.blobCsiDriver.enabled', True),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2')
    @AKSCustomRoleBasedServicePrincipalPreparer()
    def test_aks_update_labels_taints(self, resource_group, resource_group_location, sp_name, sp_password):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool_labels = "label1=value1 label2=value2"
        nodepool_taints = "taint1=value1:PreferNoSchedule,taint2=value2:PreferNoSchedule"
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'service_principal': sp_name,
            'client_secret': sp_password,
            'ssh_key_value': self.generate_ssh_keys(),
            'nodepool_labels': nodepool_labels,
            "nodepool_taints": nodepool_taints,
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--service-principal={service_principal} --client-secret={client_secret} ' \
                     '--ssh-key-value={ssh_key_value}'

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--nodepool-labels {nodepool_labels} --nodepool-taints {nodepool_taints}'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].nodeLabels.label1', 'value1'),
            self.check('agentPoolProfiles[0].nodeLabels.label2', 'value2'),
            self.check('agentPoolProfiles[0].nodeTaints[0]', 'taint1=value1:PreferNoSchedule'),
            self.check('agentPoolProfiles[0].nodeTaints[1]', 'taint2=value2:PreferNoSchedule'),
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--nodepool-labels "" --nodepool-taints ""'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].nodeLabels.label1', None),
            self.check('agentPoolProfiles[0].nodeLabels.label2', None),
            self.check('agentPoolProfiles[0].nodeTaints', None),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_custom_headers(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        # the content specified by the custom header is deprecated, we are only testing the option
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--ssh-key-value={ssh_key_value} --auto-upgrade-channel rapid ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AutoUpgradePreview'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.upgradeChannel', 'rapid')
        ])

        # update
        # the content specified by the custom header is deprecated, we are only testing the option
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--auto-upgrade-channel stable ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AutoUpgradePreview'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('autoUpgradeProfile.upgradeChannel', 'stable')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_create_with_fips(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'nodepool2_name': 'np2',
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --enable-fips-image ' \
                     '--generate-ssh-keys '
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].enableFips', True)
        ])

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --enable-fips-image', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('enableFips', True)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_nodepool_snapshot(self, resource_group, resource_group_location):
        create_version, upgrade_version = self._get_versions(resource_group_location)
        aks_name = self.create_random_name('cliakstest', 16)
        aks_name2 = self.create_random_name('cliakstest', 16)
        nodepool_name = self.create_random_name('c', 6)
        nodepool_name2 = self.create_random_name('c', 6)
        snapshot_name = self.create_random_name('s', 16)
        tagVar = "test"
        tagVal = "value"
        tags = tagVar + "=" + tagVal

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'aks_name2': aks_name2,
            'location': resource_group_location,
            'nodepool_name': nodepool_name,
            'nodepool_name2': nodepool_name2,
            'snapshot_name': snapshot_name,
            'k8s_version': create_version,
            'upgrade_k8s_version': upgrade_version,
            'ssh_key_value': self.generate_ssh_keys(),
            'tags': tags
        })

        # create an aks cluster not using snapshot
        create_cmd = 'aks create --resource-group {resource_group} --name {name} --location {location} ' \
                     '--nodepool-name {nodepool_name} ' \
                     '--node-count 1 ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        response = self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ]).get_output_in_json()

        cluster_resource_id = response["id"]
        assert cluster_resource_id is not None
        nodepool_resource_id = cluster_resource_id + "/agentPools/" + nodepool_name
        self.kwargs.update({
            'nodepool_resource_id': nodepool_resource_id,
        })
        print("The nodepool resource id %s " % nodepool_resource_id)

        # create snapshot from the nodepool
        create_snapshot_cmd = 'aks nodepool snapshot create --resource-group {resource_group} --name {snapshot_name} --location {location} ' \
                              '--nodepool-id {nodepool_resource_id} -o json'
        response = self.cmd(create_snapshot_cmd, checks=[
            self.check('creationData.sourceResourceId', nodepool_resource_id)
        ]).get_output_in_json()

        snapshot_resource_id = response["id"]
        assert snapshot_resource_id is not None
        self.kwargs.update({
            'snapshot_resource_id': snapshot_resource_id,
        })
        print("The snapshot resource id %s " % snapshot_resource_id)

        # update tags on nodepool snapshot
        update_snapshot_cmd = 'aks nodepool snapshot update --resource-group {resource_group} --name {snapshot_name} --tags {tags} -o json'
        response = self.cmd(update_snapshot_cmd, checks=[
            self.check('tags', {tagVar: tagVal})
        ]).get_output_in_json()

        # delete the original AKS cluster
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

        # show the snapshot
        show_snapshot_cmd = 'aks nodepool snapshot show --resource-group {resource_group} --name {snapshot_name} -o json'
        response = self.cmd(show_snapshot_cmd, checks=[
            self.check('creationData.sourceResourceId', nodepool_resource_id)
        ]).get_output_in_json()

        # list the snapshots
        list_snapshot_cmd = 'aks nodepool snapshot list --resource-group {resource_group} -o json'
        response = self.cmd(list_snapshot_cmd, checks=[]).get_output_in_json()
        assert len(response) > 0

        # create another aks cluster using this snapshot
        create_cmd = 'aks create --resource-group {resource_group} --name {aks_name2} --location {location} ' \
                     '--nodepool-name {nodepool_name} ' \
                     '--node-count 1 --snapshot-id {snapshot_resource_id} ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].creationData.sourceResourceId', snapshot_resource_id)
        ]).get_output_in_json()

        # add a new nodepool to this cluster using this snapshot
        add_nodepool_cmd = 'aks nodepool add --resource-group={resource_group} --cluster-name={aks_name2} --name={nodepool_name2} --node-count 1 ' \
                           '--snapshot-id {snapshot_resource_id} -o json'
        self.cmd(add_nodepool_cmd,
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('creationData.sourceResourceId', snapshot_resource_id)
        ])

        # upgrade the nodepool2 using this snapshot again
        # upgrade_node_image_only_nodepool_cmd = 'aks nodepool upgrade ' \
        #                                        '--resource-group {resource_group} ' \
        #                                        '--cluster-name {aks_name2} ' \
        #                                        '-n {nodepool_name2} ' \
        #                                        '--node-image-only ' \
        #                                        '--snapshot-id {snapshot_resource_id} -o json'
        # self.cmd(upgrade_node_image_only_nodepool_cmd)

        # get_nodepool_cmd = 'aks nodepool show ' \
        #                    '--resource-group={resource_group} ' \
        #                    '--cluster-name={aks_name2} ' \
        #                    '-n {nodepool_name2} '
        # self.cmd(get_nodepool_cmd, checks=[
        #     self.check('provisioningState', 'Succeeded'),
        #     self.check('creationData.sourceResourceId', snapshot_resource_id)
        # ])

        # delete the 2nd AKS cluster
        self.cmd('aks delete -g {resource_group} -n {aks_name2} --yes --no-wait', checks=[self.is_empty()])

        # delete the snapshot
        delete_snapshot_cmd = 'aks nodepool snapshot delete --resource-group {resource_group} --name {snapshot_name} --yes --no-wait'
        self.cmd(delete_snapshot_cmd, checks=[
            self.is_empty()
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_create_with_windows_gmsa(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': 'replace-Password1234$',
            'nodepool2_name': 'npwin',
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure ' \
                     '--ssh-key-value={ssh_key_value} --enable-windows-gmsa --yes ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AKSWindowsGmsaPreview'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.adminUsername', 'azureuser1'),
            self.check('windowsProfile.gmsaProfile.enabled', 'True')
        ])

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # nodepool delete
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westcentralus')
    def test_aks_update_with_windows_gmsa(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'windows_admin_username': 'azureuser1',
            'windows_admin_password': 'replace-Password1234$',
            'nodepool2_name': 'npwin',
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 ' \
                     '--windows-admin-username={windows_admin_username} --windows-admin-password={windows_admin_password} ' \
                     '--load-balancer-sku=standard --vm-set-type=virtualmachinescalesets --network-plugin=azure ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.adminUsername', 'azureuser1'),
            self.not_exists('windowsProfile.gmsaProfile')
        ])

        # nodepool add
        self.cmd('aks nodepool add --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --os-type Windows --node-count=1', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # enable Windows gmsa
        update_enable_cmd = "aks update --resource-group={resource_group} --name={name} --enable-windows-gmsa --yes " \
                     "--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AKSWindowsGmsaPreview"
        self.cmd(update_enable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.gmsaProfile.enabled', 'True')
        ])

        # disable Windows gmsa
        update_disable_cmd = "aks update --resource-group={resource_group} --name={name} --disable-windows-gmsa"
        self.cmd(update_disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('windowsProfile.gmsaProfile.enabled', 'False')
        ])

        # nodepool delete
        self.cmd(
            'aks nodepool delete --resource-group={resource_group} --cluster-name={name} --name={nodepool2_name} --no-wait', checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_monitoring_aad_auth_msi(self, resource_group, resource_group_location,):
        aks_name = self.create_random_name('cliakstest', 16)
        self.create_new_cluster_with_monitoring_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=False)

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_monitoring_aad_auth_uai(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.create_new_cluster_with_monitoring_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=True)

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_monitoring_aad_auth_msi_with_syslog(self, resource_group, resource_group_location,):
        aks_name = self.create_random_name('cliakstest', 16)
        self.create_new_cluster_with_monitoring_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=False, syslog_enabled=True)

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_monitoring_aad_auth_msi_with_datacollectionsettings(self, resource_group, resource_group_location,):
        aks_name = self.create_random_name('cliakstest', 16)
        self.create_new_cluster_with_monitoring_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=False, syslog_enabled=False, data_collection_settings=get_test_data_file_path('datacollectionsettings.json'))

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_monitoring_aad_auth_uai_with_syslog(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.create_new_cluster_with_monitoring_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=True, syslog_enabled=True)

    def create_new_cluster_with_monitoring_aad_auth(self, resource_group, resource_group_location, aks_name, user_assigned_identity=False, syslog_enabled=False, data_collection_settings=None):
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        if user_assigned_identity:
            uai_cmd = f'identity create -g {resource_group} -n {aks_name}_uai'
            resp = self.cmd(uai_cmd).get_output_in_json()
            identity_id = resp["id"]
            print("********************")
            print(f"identity_id: {identity_id}")
            print("********************")

        # create
        create_cmd = f'aks create --resource-group={resource_group} --name={aks_name} --location={resource_group_location} ' \
                     '--enable-managed-identity ' \
                     '--enable-addons monitoring ' \
                     '--node-count 1 ' \
                     '--ssh-key-value={ssh_key_value} '
        create_cmd += f'--assign-identity {identity_id} ' if user_assigned_identity else ''
        create_cmd += f'--enable-syslog ' if syslog_enabled else ''
        create_cmd += f'--data-collection-settings {data_collection_settings} ' if data_collection_settings else ''

        response = self.cmd(create_cmd, checks=[
            self.check('addonProfiles.omsagent.enabled', True),
            self.check('addonProfiles.omsagent.config.useAADAuth', 'true')
        ]).get_output_in_json()

        cluster_resource_id = response["id"]
        subscription = cluster_resource_id.split("/")[2]
        workspace_resource_id = response["addonProfiles"]["omsagent"]["config"]["logAnalyticsWorkspaceResourceID"]

        # check that the DCR was created
        location = resource_group_location
        dataCollectionRuleName = f"MSCI-{location}-{aks_name}"
        dataCollectionRuleName = dataCollectionRuleName[0:64]
        dcr_resource_id = f"/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Insights/dataCollectionRules/{dataCollectionRuleName}"
        get_cmd = f'rest --method get --url https://management.azure.com{dcr_resource_id}?api-version=2022-06-01'
        self.cmd(get_cmd, checks=[
            self.check('properties.destinations.logAnalytics[0].workspaceResourceId', f'{workspace_resource_id}')
        ])

        if syslog_enabled:
            self.cmd(get_cmd, checks=[
                self.check('properties.dataSources.syslog[0].streams[0]', f'Microsoft-Syslog')
            ])

        if data_collection_settings:
             self.cmd(get_cmd, checks=[
                self.check('properties.dataSources.extensions[0].name', f'ContainerInsightsExtension'),
                self.check('properties.dataSources.extensions[0].extensionSettings.dataCollectionSettings.interval', f'1m'),
                self.check('properties.dataSources.extensions[0].extensionSettings.dataCollectionSettings.namespaceFilteringMode', f'Include'),
                self.check('properties.dataSources.extensions[0].extensionSettings.dataCollectionSettings.namespaces[0]', f'kube-system'),
                self.check('properties.dataSources.extensions[0].extensionSettings.dataCollectionSettings.streams[0]', f'Microsoft-ContainerLogV2'),
                self.check('properties.dataFlows[0].streams[0]', f'Microsoft-ContainerLogV2'),
                self.check('properties.dataSources.extensions[0].extensionSettings.dataCollectionSettings.enableContainerLogV2', True)
            ])
        # check that the DCR-A was created
        dcra_resource_id = f"{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations/ContainerInsightsExtension"
        get_cmd = f'rest --method get --url https://management.azure.com{dcra_resource_id}?api-version=2022-06-01'
        self.cmd(get_cmd, checks=[
            self.check('properties.dataCollectionRuleId', f'{dcr_resource_id}')
        ])

        # make sure monitoring can be smoothly disabled
        self.cmd(f'aks disable-addons -a monitoring -g={resource_group} -n={aks_name}')

        # delete
        self.cmd(f'aks delete -g {resource_group} -n {aks_name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_monitoring_with_aad_auth_msi(self, resource_group, resource_group_location,):
        aks_name = self.create_random_name('cliakstest', 16)
        self.enable_monitoring_existing_cluster_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=False)

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_monitoring_with_aad_auth_uai(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.enable_monitoring_existing_cluster_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=True)

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_monitoring_with_aad_auth_msi_with_syslog(self, resource_group, resource_group_location,):
        aks_name = self.create_random_name('cliakstest', 16)
        self.enable_monitoring_existing_cluster_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=False, syslog_enabled=True)

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_enable_monitoring_with_aad_auth_uai_with_syslog(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.enable_monitoring_existing_cluster_aad_auth(resource_group, resource_group_location, aks_name, user_assigned_identity=True, syslog_enabled=True)

    def enable_monitoring_existing_cluster_aad_auth(self, resource_group, resource_group_location, aks_name, user_assigned_identity=False, syslog_enabled=False):
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        if user_assigned_identity:
            uai_cmd = f'identity create -g {resource_group} -n {aks_name}_uai'
            resp = self.cmd(uai_cmd).get_output_in_json()
            identity_id = resp["id"]
            print("********************")
            print(f"identity_id: {identity_id}")
            print("********************")

        # create
        create_cmd = f'aks create --resource-group={resource_group} --name={aks_name} --location={resource_group_location} ' \
                     '--enable-managed-identity ' \
                     '--node-count 1 ' \
                     '--ssh-key-value={ssh_key_value} '
        create_cmd += f'--assign-identity {identity_id}' if user_assigned_identity else ''
        self.cmd(create_cmd)

        enable_monitoring_cmd = f'aks enable-addons -a monitoring --resource-group={resource_group} --name={aks_name} '
        if syslog_enabled:
            enable_monitoring_cmd += f'--enable-syslog '

        response = self.cmd(enable_monitoring_cmd, checks=[
            self.check('addonProfiles.omsagent.enabled', True),
            self.check('addonProfiles.omsagent.config.useAADAuth', 'true')
        ]).get_output_in_json()

        cluster_resource_id = response["id"]
        subscription = cluster_resource_id.split("/")[2]
        workspace_resource_id = response["addonProfiles"]["omsagent"]["config"]["logAnalyticsWorkspaceResourceID"]
        workspace_name = workspace_resource_id.split("/")[-1]
        workspace_resource_group = workspace_resource_id.split("/")[4]

        # check that the DCR was created
        location = resource_group_location
        dataCollectionRuleName = f"MSCI-{location}-{aks_name}"
        dcr_resource_id = f"/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Insights/dataCollectionRules/{dataCollectionRuleName}"
        get_cmd = f'rest --method get --url https://management.azure.com{dcr_resource_id}?api-version=2022-06-01'
        self.cmd(get_cmd, checks=[
            self.check('properties.destinations.logAnalytics[0].workspaceResourceId', f'{workspace_resource_id}')
        ])

        if syslog_enabled:
            self.cmd(get_cmd, checks=[
                self.check('properties.dataSources.syslog[0].streams[0]', f'Microsoft-Syslog')
            ])

        # check that the DCR-A was created
        dcra_resource_id = f"{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations/ContainerInsightsExtension"
        get_cmd = f'rest --method get --url https://management.azure.com{dcra_resource_id}?api-version=2022-06-01'
        self.cmd(get_cmd, checks=[
            self.check('properties.dataCollectionRuleId', f'{dcr_resource_id}')
        ])

        # make sure monitoring can be smoothly disabled
        self.cmd(f'aks disable-addons -a monitoring -g={resource_group} -n={aks_name}')

        # delete
        self.cmd(f'aks delete -g {resource_group} -n {aks_name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_monitoring_legacy_auth(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-managed-identity ' \
                     '--enable-addons monitoring ' \
                     '--node-count 1 ' \
                     '--ssh-key-value={ssh_key_value} '
        response = self.cmd(create_cmd, checks=[
            self.check('addonProfiles.omsagent.enabled', True),
            self.exists('addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID')
        ]).get_output_in_json()

        # make sure a DCR was not created

        cluster_resource_id = response["id"]
        subscription = cluster_resource_id.split("/")[2]
        workspace_resource_id = response["addonProfiles"]["omsagent"]["config"]["logAnalyticsWorkspaceResourceID"]
        workspace_name = workspace_resource_id.split("/")[-1]
        workspace_resource_group = workspace_resource_id.split("/")[4]

        try:
            # check that the DCR was created
            location = resource_group_location
            dataCollectionRuleName = f"MSCI-{location}-{aks_name}"
            dataCollectionRuleName = dataCollectionRuleName[0:64]
            dcr_resource_id = f"/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Insights/dataCollectionRules/{dataCollectionRuleName}"
            get_cmd = f'rest --method get --url https://management.azure.com{dcr_resource_id}?api-version=2022-06-01'
            self.cmd(get_cmd, checks=[
                self.check('properties.destinations.logAnalytics[0].workspaceResourceId', f'{workspace_resource_id}')
            ])

            assert False
        except Exception as err:
            pass  # this is expected


        # make sure monitoring can be smoothly disabled
        self.cmd(f'aks disable-addons -a monitoring -g={resource_group} -n={aks_name}')

        # delete
        self.cmd(f'aks delete -g {resource_group} -n {aks_name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_run_command(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cmdtest', 16)
        node_pool_name = self.create_random_name('c', 6)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--nodepool-name {node_pool_name} ' \
                     '--generate-ssh-keys ' \
                     '--vm-set-type VirtualMachineScaleSets --node-count=1 ' \
                     '-o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        runCommand = 'aks command invoke -g {resource_group} -n {name} -o json -c "kubectl get pods -A"'
        self.cmd(runCommand, [
            self.check('provisioningState', 'Succeeded'),
            self.check('exitCode', 0),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_node_config(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'kc_path': get_test_data_file_path('kubeletconfig.json'),
            'oc_path': get_test_data_file_path('linuxosconfig.json'),
            'ssh_key_value': self.generate_ssh_keys()
        })

        # use custom feature so it does not require subscription to regiter the feature
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--kubelet-config=\'{kc_path}\' --linux-os-config=\'{oc_path}\' ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/CustomNodeConfigPreview ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('agentPoolProfiles[0].kubeletConfig.cpuManagerPolicy', 'static'),
            self.check('agentPoolProfiles[0].linuxOsConfig.swapFileSizeMb', 1500),
            self.check('agentPoolProfiles[0].linuxOsConfig.sysctls.netIpv4TcpTwReuse', True)
        ])

        # nodepool add
        nodepool_cmd = 'aks nodepool add --resource-group={resource_group} --cluster-name={name} ' \
                       '--name=nodepool2 --node-count=1 --kubelet-config=\'{kc_path}\' --linux-os-config=\'{oc_path}\' ' \
                       '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/CustomNodeConfigPreview'
        self.cmd(nodepool_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('kubeletConfig.cpuCfsQuotaPeriod', '200ms'),
            self.check('linuxOsConfig.sysctls.netCoreSomaxconn', 163849)
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2euap', preserve_default_location=True)
    def test_aks_create_edge_zone(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        kubernetes_version = "1.23.5"

        self.kwargs.update({
            'resource_group': resource_group,
            'edge_zone': 'microsoftrrdclab1',
            'kubernetes_version': kubernetes_version,
            'name': aks_name,
            'dns_name_prefix': self.create_random_name('cliaksdns', 16),
            'ssh_key_value': self.generate_ssh_keys(),
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters'
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--dns-name-prefix={dns_name_prefix} --node-count=1 --ssh-key-value={ssh_key_value} ' \
                     '--kubernetes-version {kubernetes_version} --edge-zone {edge_zone}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.exists('nodeResourceGroup'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # show
        self.cmd('aks show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check('location', 'eastus2euap'),
            self.check('extendedLocation.name', 'microsoftrrdclab1'),
            self.check('extendedLocation.type', 'edgezone'),
            self.exists('nodeResourceGroup'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_DS2_v2'),
            self.check('dnsPrefix', '{dns_name_prefix}'),
            self.check('kubernetesVersion', '{kubernetes_version}')
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westcentralus', preserve_default_location=True)
    def test_aks_azure_cni_overlay_migration(self, resource_group, resource_group_location):
        _, create_version = self._get_versions(resource_group_location)
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'k8s_version': create_version,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--network-plugin azure --ssh-key-value={ssh_key_value} --kubernetes-version {k8s_version} ' \
                     '--service-cidr 172.56.0.0/16 --dns-service-ip 172.56.0.10 ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AzureOverlayPreview'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.networkPlugin', 'azure'),
            self.check('networkProfile.networkPluginMode', None),
            self.check('networkProfile.podCidr', None),
            self.check('networkProfile.serviceCidr', '172.56.0.0/16'),
        ])

        # update
        update_cmd = 'aks update -g {resource_group} -n {name} --network-plugin-mode overlay --pod-cidr 100.64.0.0/10 ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AzureOverlayPreview'

        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.networkPlugin', 'azure'),
            self.check('networkProfile.networkPluginMode', 'overlay'),
            self.check('networkProfile.podCidr', '100.64.0.0/10'),
            self.check('networkProfile.serviceCidr', '172.56.0.0/16'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus2', preserve_default_location=True)
    def test_aks_kubenet_to_cni_overlay_migration(self, resource_group, resource_group_location):
        _, create_version = self._get_versions(resource_group_location)
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'k8s_version': create_version,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--network-plugin kubenet --ssh-key-value={ssh_key_value} --kubernetes-version {k8s_version} ' \
                     '--service-cidr 172.56.0.0/16 --dns-service-ip 172.56.0.10 --pod-cidr 100.112.0.0/12 ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AzureOverlayPreview'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.networkPlugin', 'kubenet'),
            self.check('networkProfile.networkPluginMode', None),
            self.check('networkProfile.podCidr', '100.112.0.0/12'),
            self.check('networkProfile.serviceCidr', '172.56.0.0/16'),
        ])

        # update
        update_cmd = 'aks update -g {resource_group} -n {name} --network-plugin azure --network-plugin-mode overlay ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AzureOverlayPreview'

        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.networkPlugin', 'azure'),
            self.check('networkProfile.networkPluginMode', 'overlay'),
            self.check('networkProfile.podCidr', '100.112.0.0/12'),
            self.check('networkProfile.serviceCidr', '172.56.0.0/16'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus', preserve_default_location=True)
    def test_aks_migrate_cluster_to_cilium_dataplane(self, resource_group, resource_group_location):
        _, create_version = self._get_versions(resource_group_location)
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'k8s_version': create_version,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create with Azure CNI overlay
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--network-plugin azure --ssh-key-value={ssh_key_value} --kubernetes-version {k8s_version} ' \
                     '--network-plugin-mode=overlay'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.networkPlugin', 'azure'),
            self.check('networkProfile.networkPluginMode', 'overlay'),
            self.check('networkProfile.networkDataplane', 'azure'),
        ])

        # update to enable cilium dataplane
        update_cmd = 'aks update -g {resource_group} -n {name} --network-dataplane=cilium --network-policy=cilium'

        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.networkPlugin', 'azure'),
            self.check('networkProfile.networkPluginMode', 'overlay'),
            self.check('networkProfile.networkDataplane', 'cilium'),
            self.check('networkProfile.networkPolicy', 'cilium'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_node_resource_group(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        node_resource_group_name = self.create_random_name('cliaksnrg', 17)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'node_resource_group': node_resource_group_name,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--ssh-key-value={ssh_key_value} --node-resource-group {node_resource_group}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('nodeResourceGroup', '{node_resource_group}')
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_create_with_azurekeyvaultkms_public_key_vault(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        kv_name = self.create_random_name('cliakstestkv', 16)
        identity_name = self.create_random_name('cliakstestidentity', 24)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            "kv_name": kv_name,
            "identity_name": identity_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create user-assigned identity
        create_identity = 'identity create --resource-group={resource_group} --name={identity_name} -o json'
        identity = self.cmd(create_identity).get_output_in_json()
        identity_id = identity['id']
        identity_object_id = identity['principalId']
        assert identity_id is not None
        assert identity_object_id is not None
        self.kwargs.update({
            'identity_id': identity_id,
            'identity_object_id': identity_object_id,
        })

        # create key vault and key
        create_keyvault = 'keyvault create --resource-group={resource_group} --name={kv_name} -o json'
        kv = self.cmd(create_keyvault, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_key = 'keyvault key create -n kms --vault-name {kv_name} -o json'
        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id_0 = key['key']['kid']
        assert key_id_0 is not None
        self.kwargs.update({
            'key_id': key_id_0,
        })

        # assign access policy
        set_policy = 'keyvault set-policy --resource-group={resource_group} --name={kv_name} ' \
                     '--object-id {identity_object_id} --key-permissions encrypt decrypt -o json'
        policy = self.cmd(set_policy, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--assign-identity {identity_id} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} --azure-keyvault-kms-key-vault-network-access=Public ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id_0),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', 'Public')
        ])

        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id_1 = key['key']['kid']
        assert key_id_1 is not None
        self.kwargs.update({
            'key_id': key_id_1,
        })

        # Rotate key
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} --azure-keyvault-kms-key-vault-network-access=Public ' \
                     '-o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id_1),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', 'Public')
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_update_with_azurekeyvaultkms_public_key_vault(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        kv_name = self.create_random_name('cliakstestkv', 16)
        identity_name = self.create_random_name('cliakstestidentity', 24)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            "kv_name": kv_name,
            "identity_name": identity_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create user-assigned identity
        create_identity = 'identity create --resource-group={resource_group} --name={identity_name} -o json'
        identity = self.cmd(create_identity).get_output_in_json()
        identity_id = identity['id']
        identity_object_id = identity['principalId']
        assert identity_id is not None
        assert identity_object_id is not None
        self.kwargs.update({
            'identity_id': identity_id,
            'identity_object_id': identity_object_id,
        })

        # create key vault and key
        create_keyvault = 'keyvault create --resource-group={resource_group} --name={kv_name} -o json'
        kv = self.cmd(create_keyvault, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_key = 'keyvault key create -n kms --vault-name {kv_name} -o json'
        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id = key['key']['kid']
        assert key_id is not None
        self.kwargs.update({
            'key_id': key_id,
        })

        # assign access policy
        set_policy = 'keyvault set-policy --resource-group={resource_group} --name={kv_name} ' \
                     '--object-id {identity_object_id} --key-permissions encrypt decrypt -o json'
        policy = self.cmd(set_policy, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--assign-identity {identity_id} ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.not_exists('securityProfile.azureKeyVaultKms')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} --azure-keyvault-kms-key-vault-network-access=Public ' \
                     '-o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', 'Public')
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap', preserve_default_location=True)
    def test_aks_create_with_azurekeyvaultkms_private_key_vault(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        kv_name = self.create_random_name('cliakstestkv', 16)
        identity_name = self.create_random_name('cliakstestidentity', 24)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            "kv_name": kv_name,
            "identity_name": identity_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create user-assigned identity
        create_identity = 'identity create --resource-group={resource_group} --name={identity_name} -o json'
        identity = self.cmd(create_identity).get_output_in_json()
        identity_id = identity['id']
        identity_object_id = identity['principalId']
        assert identity_id is not None
        assert identity_object_id is not None
        self.kwargs.update({
            'identity_id': identity_id,
            'identity_object_id': identity_object_id,
        })

        # create key vault and key
        create_keyvault = 'keyvault create --resource-group={resource_group} --name={kv_name} -o json'
        kv = self.cmd(create_keyvault, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()
        kv_resource_id = kv['id']
        assert kv_resource_id is not None
        self.kwargs.update({
            'kv_resource_id': kv_resource_id,
        })

        create_key = 'keyvault key create -n kms --vault-name {kv_name} -o json'
        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id_0 = key['key']['kid']
        assert key_id_0 is not None
        self.kwargs.update({
            'key_id': key_id_0,
        })

        # assign access policy
        set_policy = 'keyvault set-policy --resource-group={resource_group} --name={kv_name} ' \
                     '--object-id {identity_object_id} --key-permissions encrypt decrypt -o json'
        policy = self.cmd(set_policy, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        # allow the identity approve private endpoint connection (Microsoft.KeyVault/vaults/privateEndpointConnectionsApproval/action)
        create_role_assignment = 'role assignment create --role f25e0fa2-a7c8-4377-a976-54943a77a395 ' \
                     '--assignee-object-id {identity_object_id} --assignee-principal-type "ServicePrincipal" ' \
                     '--scope {kv_resource_id}'
        role_assignment = self.cmd(create_role_assignment).get_output_in_json()

        # disable public network access
        disable_public_network_access = 'keyvault update --resource-group={resource_group} --name={kv_name} --public-network-access "Disabled" -o json'
        kv = self.cmd(disable_public_network_access, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--assign-identity {identity_id} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} ' \
                     '--azure-keyvault-kms-key-vault-network-access=Private --azure-keyvault-kms-key-vault-resource-id {kv_resource_id} ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id_0),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', "Private"),
            self.check('securityProfile.azureKeyVaultKms.keyVaultResourceId', kv_resource_id)
        ])

        # enable public network access
        enable_public_network_access = 'keyvault update --resource-group={resource_group} --name={kv_name} --public-network-access "Enabled" -o json'
        kv = self.cmd(enable_public_network_access, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id_1 = key['key']['kid']
        assert key_id_1 is not None
        self.kwargs.update({
            'key_id': key_id_1,
        })

        # disable public network access
        disable_public_network_access = 'keyvault update --resource-group={resource_group} --name={kv_name} --public-network-access "Disabled" -o json'
        kv = self.cmd(disable_public_network_access, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        # Rotate key
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} ' \
                     '--azure-keyvault-kms-key-vault-network-access=Private --azure-keyvault-kms-key-vault-resource-id {kv_resource_id} ' \
                     '-o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id_1),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', "Private"),
            self.check('securityProfile.azureKeyVaultKms.keyVaultResourceId', kv_resource_id)
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap', preserve_default_location=True)
    def test_aks_update_with_azurekeyvaultkms_private_key_vault(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        kv_name = self.create_random_name('cliakstestkv', 16)
        identity_name = self.create_random_name('cliakstestidentity', 24)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            "kv_name": kv_name,
            "identity_name": identity_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create user-assigned identity
        create_identity = 'identity create --resource-group={resource_group} --name={identity_name} -o json'
        identity = self.cmd(create_identity).get_output_in_json()
        identity_id = identity['id']
        identity_object_id = identity['principalId']
        assert identity_id is not None
        assert identity_object_id is not None
        self.kwargs.update({
            'identity_id': identity_id,
            'identity_object_id': identity_object_id,
        })

        # create key vault and key
        create_keyvault = 'keyvault create --resource-group={resource_group} --name={kv_name} -o json'
        kv = self.cmd(create_keyvault, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()
        kv_resource_id = kv['id']
        assert kv_resource_id is not None
        self.kwargs.update({
            'kv_resource_id': kv_resource_id,
        })

        create_key = 'keyvault key create -n kms --vault-name {kv_name} -o json'
        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id = key['key']['kid']
        assert key_id is not None
        self.kwargs.update({
            'key_id': key_id,
        })

        # assign access policy
        set_policy = 'keyvault set-policy --resource-group={resource_group} --name={kv_name} ' \
                     '--object-id {identity_object_id} --key-permissions encrypt decrypt -o json'
        policy = self.cmd(set_policy, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        # allow the identity approve private endpoint connection (Microsoft.KeyVault/vaults/privateEndpointConnectionsApproval/action)
        create_role_assignment = 'role assignment create --role f25e0fa2-a7c8-4377-a976-54943a77a395 ' \
                     '--assignee-object-id {identity_object_id} --assignee-principal-type "ServicePrincipal" ' \
                     '--scope {kv_resource_id}'
        role_assignment = self.cmd(create_role_assignment).get_output_in_json()

        # disable public network access
        disable_public_network_access = 'keyvault update --resource-group={resource_group} --name={kv_name} --public-network-access "Disabled" -o json'
        kv = self.cmd(disable_public_network_access, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--assign-identity {identity_id} ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.not_exists('securityProfile.azureKeyVaultKms')
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} ' \
                     '--azure-keyvault-kms-key-vault-network-access=Private --azure-keyvault-kms-key-vault-resource-id {kv_resource_id} ' \
                     '-o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', "Private"),
            self.check('securityProfile.azureKeyVaultKms.keyVaultResourceId', kv_resource_id)
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap', preserve_default_location=True)
    def test_aks_create_with_azurekeyvaultkms_private_cluster_v1_private_key_vault(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        kv_name = self.create_random_name('cliakstestkv', 16)
        identity_name = self.create_random_name('cliakstestidentity', 24)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            "kv_name": kv_name,
            "identity_name": identity_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create user-assigned identity
        create_identity = 'identity create --resource-group={resource_group} --name={identity_name} -o json'
        identity = self.cmd(create_identity).get_output_in_json()
        identity_id = identity['id']
        identity_object_id = identity['principalId']
        assert identity_id is not None
        assert identity_object_id is not None
        self.kwargs.update({
            'identity_id': identity_id,
            'identity_object_id': identity_object_id,
        })

        # create key vault and key
        create_keyvault = 'keyvault create --resource-group={resource_group} --name={kv_name} -o json'
        kv = self.cmd(create_keyvault, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()
        kv_resource_id = kv['id']
        assert kv_resource_id is not None
        self.kwargs.update({
            'kv_resource_id': kv_resource_id,
        })

        create_key = 'keyvault key create -n kms --vault-name {kv_name} -o json'
        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id_0 = key['key']['kid']
        assert key_id_0 is not None
        self.kwargs.update({
            'key_id': key_id_0,
        })

        # assign access policy
        set_policy = 'keyvault set-policy --resource-group={resource_group} --name={kv_name} ' \
                     '--object-id {identity_object_id} --key-permissions encrypt decrypt -o json'
        policy = self.cmd(set_policy, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        # allow the identity approve private endpoint connection (Microsoft.KeyVault/vaults/privateEndpointConnectionsApproval/action)
        create_role_assignment = 'role assignment create --role f25e0fa2-a7c8-4377-a976-54943a77a395 ' \
                     '--assignee-object-id {identity_object_id} --assignee-principal-type "ServicePrincipal" ' \
                     '--scope {kv_resource_id}'
        role_assignment = self.cmd(create_role_assignment).get_output_in_json()

        # disable public network access
        disable_public_network_access = 'keyvault update --resource-group={resource_group} --name={kv_name} --public-network-access "Disabled" -o json'
        kv = self.cmd(disable_public_network_access, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--assign-identity {identity_id} --enable-private-cluster ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} ' \
                     '--azure-keyvault-kms-key-vault-network-access=Private --azure-keyvault-kms-key-vault-resource-id {kv_resource_id} ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('apiServerAccessProfile.enablePrivateCluster', 'True'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id_0),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', "Private"),
            self.check('securityProfile.azureKeyVaultKms.keyVaultResourceId', kv_resource_id)
        ])

        # enable public network access
        enable_public_network_access = 'keyvault update --resource-group={resource_group} --name={kv_name} --public-network-access "Enabled" -o json'
        kv = self.cmd(enable_public_network_access, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id_1 = key['key']['kid']
        assert key_id_1 is not None
        self.kwargs.update({
            'key_id': key_id_1,
        })

        # disable public network access
        disable_public_network_access = 'keyvault update --resource-group={resource_group} --name={kv_name} --public-network-access "Disabled" -o json'
        kv = self.cmd(disable_public_network_access, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        # Rotate key
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} ' \
                     '--azure-keyvault-kms-key-vault-network-access=Private --azure-keyvault-kms-key-vault-resource-id {kv_resource_id} ' \
                     '-o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id_1),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', "Private"),
            self.check('securityProfile.azureKeyVaultKms.keyVaultResourceId', kv_resource_id)
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_image_cleaner_enabled_with_default_interval_hours(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'vm_size': 'Standard_D4s_v3',
            'node_count': 1,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = ' '.join([
            'aks', 'create', '--resource-group={resource_group}', '--name={name}', '--location={location}',
            '--node-vm-size {vm_size}',
            '--node-count {node_count}',
            '--enable-image-cleaner',
            '--ssh-key-value={ssh_key_value}',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableImageCleanerPreview',
        ])

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.imageCleaner.enabled', True),
            self.check('securityProfile.imageCleaner.intervalHours', 7*24),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_image_cleaner_enabled_with_interval_hours(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'vm_size': 'Standard_D4s_v3',
            'node_count': 1,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = ' '.join([
            'aks', 'create', '--resource-group={resource_group}', '--name={name}', '--location={location}',
            '--node-vm-size {vm_size}',
            '--node-count {node_count}',
            '--enable-image-cleaner',
            '--image-cleaner-interval-hours 24',
            '--ssh-key-value={ssh_key_value}',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableImageCleanerPreview',
        ])

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.imageCleaner.enabled', True),
            self.check('securityProfile.imageCleaner.intervalHours', 24),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_update_with_image_cleaner(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'vm_size': 'Standard_D4s_v3',
            'node_count': 1,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = ' '.join([
            'aks', 'create', '--resource-group={resource_group}', '--name={name}', '--location={location}',
            '--node-vm-size {vm_size}',
            '--node-count {node_count}',
            '--enable-image-cleaner',
            '--ssh-key-value={ssh_key_value}',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableImageCleanerPreview',
        ])
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.imageCleaner.enabled', True),
            self.check('securityProfile.imageCleaner.intervalHours', 7*24),
        ])

        update_interval_cmd = ' '.join([
            'aks', 'update', '--resource-group={resource_group}', '--name={name}',
            '--image-cleaner-interval-hours 24',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableImageCleanerPreview',
        ])
        self.cmd(update_interval_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.imageCleaner.enabled', True),
            self.check('securityProfile.imageCleaner.intervalHours', 24),
        ])

        disable_cmd = ' '.join([
            'aks', 'update', '--resource-group={resource_group}', '--name={name}',
            '--disable-image-cleaner',
            '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/EnableImageCleanerPreview',
        ])
        self.cmd(disable_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.imageCleaner.enabled', False),
            self.check('securityProfile.imageCleaner.intervalHours', 24),
        ])

    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='centraluseuap')
    def test_aks_disable_azurekeyvaultkms(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        kv_name = self.create_random_name('cliakstestkv', 16)
        identity_name = self.create_random_name('cliakstestidentity', 24)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            "kv_name": kv_name,
            "identity_name": identity_name,
            'ssh_key_value': self.generate_ssh_keys()
        })

        # create user-assigned identity
        create_identity = 'identity create --resource-group={resource_group} --name={identity_name} -o json'
        identity = self.cmd(create_identity).get_output_in_json()
        identity_id = identity['id']
        identity_object_id = identity['principalId']
        assert identity_id is not None
        assert identity_object_id is not None
        self.kwargs.update({
            'identity_id': identity_id,
            'identity_object_id': identity_object_id,
        })

        # create key vault and key
        create_keyvault = 'keyvault create --resource-group={resource_group} --name={kv_name} -o json'
        kv = self.cmd(create_keyvault, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_key = 'keyvault key create -n kms --vault-name {kv_name} -o json'
        key = self.cmd(create_key, checks=[
            self.check('attributes.enabled', True)
        ]).get_output_in_json()
        key_id = key['key']['kid']
        assert key_id is not None
        self.kwargs.update({
            'key_id': key_id,
        })

        # assign access policy
        set_policy = 'keyvault set-policy --resource-group={resource_group} --name={kv_name} ' \
                     '--object-id {identity_object_id} --key-permissions encrypt decrypt -o json'
        policy = self.cmd(set_policy, checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ]).get_output_in_json()

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--assign-identity {identity_id} ' \
                     '--enable-azure-keyvault-kms --azure-keyvault-kms-key-id={key_id} --azure-keyvault-kms-key-vault-network-access=Public ' \
                     '--ssh-key-value={ssh_key_value} -o json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', True),
            self.check('securityProfile.azureKeyVaultKms.keyId', key_id),
            self.check('securityProfile.azureKeyVaultKms.keyVaultNetworkAccess', "Public")
        ])

        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--disable-azure-keyvault-kms ' \
                     '-o json'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('securityProfile.azureKeyVaultKms.enabled', False),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_network_plugin_none(self, resource_group, resource_group_location):
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--ssh-key-value={ssh_key_value} --network-plugin=none'

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.networkPlugin', 'none'),
        ])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus', preserve_default_location=True)
    def test_aks_nodepool_add_with_gpu_instance_profile(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('c', 6)
        node_pool_name_second = self.create_random_name('c', 6)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'node_pool_name': node_pool_name,
            'node_pool_name_second': node_pool_name_second,
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--nodepool-name {node_pool_name} -c 1 ' \
                     '--network-plugin azure ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # nodepool get-upgrades
        self.cmd('aks nodepool add '
                 '--resource-group={resource_group} '
                 '--cluster-name={name} '
                 '--name={node_pool_name_second} '
                 '--gpu-instance-profile=MIG3g '
                 '-c 1 '
                 '--node-vm-size=standard_nd96asr_v4',
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('gpuInstanceProfile', 'MIG3g'),
                 ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2', preserve_default_location=True)
    def test_aks_create_with_overlay_network_plugin_mode(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--network-plugin azure --network-plugin-mode overlay --ssh-key-value={ssh_key_value} ' \
                     '--pod-cidr 100.64.0.0/10 --node-count 1 ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AzureOverlayPreview'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.podCidr', '100.64.0.0/10'),
            self.check('networkProfile.networkPlugin', 'azure'),
            self.check('networkProfile.networkPluginMode', 'overlay'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2', preserve_default_location=True)
    def test_aks_create_dualstack_with_default_network(self, resource_group, resource_group_location):
        _, create_version = self._get_versions(resource_group_location)
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'k8s_version': create_version,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--ip-families IPv4,IPv6 --ssh-key-value={ssh_key_value} --kubernetes-version {k8s_version} ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AKS-EnableDualStack'

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.podCidrs[] | length(@)', 2),
            self.check('networkProfile.serviceCidrs[] | length(@)', 2),
            self.check('networkProfile.ipFamilies', ['IPv4', 'IPv6'])
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2', preserve_default_location=True)
    def test_aks_create_and_update_ipv6_count(self, resource_group, resource_group_location):
        _, create_version = self._get_versions(resource_group_location)
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'k8s_version': create_version,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--pod-cidr 172.126.0.0/16 --service-cidr 172.56.0.0/16 --dns-service-ip 172.56.0.10 ' \
                     '--pod-cidrs 172.126.0.0/16,2001:abcd:1234::/64 --service-cidrs 172.56.0.0/16,2001:ffff::/108 ' \
                     '--ip-families IPv4,IPv6 --load-balancer-managed-outbound-ipv6-count 2 ' \
                     '--network-plugin kubenet --ssh-key-value={ssh_key_value} --kubernetes-version {k8s_version} ' \
                     '--aks-custom-headers AKSHTTPCustomFeatures=Microsoft.ContainerService/AKS-EnableDualStack'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.podCidr', '172.126.0.0/16'),
            self.check('networkProfile.podCidrs', [
                       '172.126.0.0/16', '2001:abcd:1234::/64']),
            self.check('networkProfile.serviceCidr', '172.56.0.0/16'),
            self.check('networkProfile.serviceCidrs', [
                       '172.56.0.0/16', '2001:ffff::/108']),
            self.check('networkProfile.ipFamilies', ['IPv4', 'IPv6']),
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.countIpv6', 2),
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
            self.check(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs[] | length(@)', 3)
        ])

        # update
        update_cmd = 'aks update -g {resource_group} -n {name} --load-balancer-managed-outbound-ipv6-count 4'

        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('networkProfile.podCidr', '172.126.0.0/16'),
            self.check('networkProfile.podCidrs', [
                       '172.126.0.0/16', '2001:abcd:1234::/64']),
            self.check('networkProfile.serviceCidr', '172.56.0.0/16'),
            self.check('networkProfile.serviceCidrs', [
                       '172.56.0.0/16', '2001:ffff::/108']),
            self.check('networkProfile.ipFamilies', ['IPv4', 'IPv6']),
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.countIpv6', 4),
            self.check(
                'networkProfile.loadBalancerProfile.managedOutboundIPs.count', 1),
            self.check(
                'networkProfile.loadBalancerProfile.effectiveOutboundIPs[] | length(@)', 5)
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # The fix on the rp side has not been released yet
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_keda(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create: enable-keda
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} --ssh-key-value={ssh_key_value} --output=json ' \
                     '--aks-custom-headers=AKSHTTPCustomFeatures=Microsoft.ContainerService/AKS-KedaPreview ' \
                     '--enable-keda'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('workloadAutoScalerProfile.keda.enabled', True),
        ])

        # delete
        delete_cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(delete_cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_update_with_keda(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create: without enable-keda
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} --ssh-key-value={ssh_key_value} --output=json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.not_exists('workloadAutoScalerProfile.keda'),
        ])

        # update: enable-keda
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --yes --output=json ' \
                     '--aks-custom-headers=AKSHTTPCustomFeatures=Microsoft.ContainerService/AKS-KedaPreview ' \
                     '--enable-keda'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('workloadAutoScalerProfile.keda.enabled', True),
        ])

        # update: disable-keda
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --yes --output=json ' \
                     '--disable-keda'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('workloadAutoScalerProfile.keda.enabled', False),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_vpa(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create: enable-vpa
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} --ssh-key-value={ssh_key_value} --output=json ' \
                     '--aks-custom-headers=AKSHTTPCustomFeatures=Microsoft.ContainerService/AKS-VPAPreview ' \
                     '--enable-vpa'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('workloadAutoScalerProfile.verticalPodAutoscaler.enabled', True),
        ])

        # delete
        delete_cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(delete_cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_update_with_vpa(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create: without enable-vpa
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} --ssh-key-value={ssh_key_value} --output=json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.not_exists('workloadAutoScalerProfile.verticalPodAutoscaler'),
        ])

        # update: enable-vpa
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --yes --output=json ' \
                     '--aks-custom-headers=AKSHTTPCustomFeatures=Microsoft.ContainerService/AKS-VPAPreview ' \
                     '--enable-vpa'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('workloadAutoScalerProfile.verticalPodAutoscaler.enabled', True),
        ])

        # update: disable-vpa
        update_cmd = 'aks update --resource-group={resource_group} --name={name} --yes --output=json ' \
                     '--disable-vpa'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('workloadAutoScalerProfile.verticalPodAutoscaler.enabled', False),
        ])

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_again_should_fail(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                     '--location={location} --ssh-key-value={ssh_key_value} --output=json'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # create again should fail
        create_again_cmd = 'aks create --resource-group={resource_group} --name={name} ' \
                           '--location={location} --ssh-key-value={ssh_key_value} --output=json'
        try:
            self.cmd(create_again_cmd, checks=[
                self.check('provisioningState', 'Succeeded'),
            ])
        except ClientRequestError as ex:
            if "already exists" not in str(ex):
                raise AssertionError(
                    "Actual error '{}' does not contain '{}'".format(
                        ex, "already exists"
                    )
                )

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    # live only due to dependency `_add_role_assignment` is not mocked
    @live_only()
    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_update_attach_acr(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        acr_name = self.create_random_name('cliaksacr', 16)
        self.kwargs.update({
            'name': aks_name,
            'resource_group': resource_group,
            'ssh_key_value': self.generate_ssh_keys(),
            'acr_name': acr_name
        })

        # create acr
        create_acr_cmd = 'acr create -g {resource_group} -n {acr_name} --sku basic'
        self.cmd(create_acr_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} -c 1 ' \
                     '--ssh-key-value={ssh_key_value} --attach-acr={acr_name}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # update
        update_cmd = 'aks update --resource-group={resource_group} --name={name} ' \
                     '--attach-acr={acr_name}'
        self.cmd(update_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_maintenancewindow(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'mc_path': get_test_data_file_path('maintenancewindow.json'),
            'auto_upgrade_config_name': 'aksManagedAutoUpgradeSchedule',
            'node_os_upgrade_config_name': 'aksManagedNodeOSUpgradeSchedule',
            'ssh_key_value': self.generate_ssh_keys(),
            'future_date': "2123-01-01"
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # add dedicated maintenanceconfiguration for cluster autoupgrade
        maintenance_configuration_add_cmd = 'aks maintenanceconfiguration add ' \
            '-g {resource_group} --cluster-name {name} ' \
            '-n {auto_upgrade_config_name} ' \
            '--schedule-type Weekly ' \
            '--day-of-week Friday ' \
            '--interval-weeks 3 ' \
            '--duration 8 ' \
            '--utc-offset +05:30 ' \
            '--start-date {future_date} ' \
            '--start-time 00:00 '

        self.cmd(
            maintenance_configuration_add_cmd, checks=[
                self.exists('maintenanceWindow.schedule.weekly'),
                self.check('maintenanceWindow.schedule.weekly.dayOfWeek', 'Friday'),
                self.check('maintenanceWindow.schedule.weekly.intervalWeeks', 3),
                self.check('maintenanceWindow.durationHours', 8),
                self.check('maintenanceWindow.utcOffset', '+05:30'),
                self.check('maintenanceWindow.startDate', '{future_date}'),
                self.check('maintenanceWindow.startTime', '00:00')]
        )

        # add dedicated maintenanceconfiguration for node os autoupgrade
        maintenance_configuration_add_cmd = 'aks maintenanceconfiguration add ' \
            '-g {resource_group} --cluster-name {name} ' \
            '-n {node_os_upgrade_config_name} ' \
            '--schedule-type RelativeMonthly ' \
            '--day-of-week Tuesday ' \
            '--week-index Last ' \
            '--interval-months 1 ' \
            '--duration 12 ' \
            '--start-time 09:00 ' \
            '--utc-offset=-08:00 ' \
            '--start-date {future_date} '

        self.cmd(
            maintenance_configuration_add_cmd, checks=[
                self.exists('maintenanceWindow.schedule.relativeMonthly'),
                self.check('maintenanceWindow.schedule.relativeMonthly.dayOfWeek', 'Tuesday'),
                self.check('maintenanceWindow.schedule.relativeMonthly.intervalMonths', 1),
                self.check('maintenanceWindow.durationHours', 12),
                self.check('maintenanceWindow.utcOffset', '-08:00'),
                self.check('maintenanceWindow.startDate', '{future_date}'),
                self.check('maintenanceWindow.startTime', '09:00')]
        )

        # maintenanceconfiguration list
        maintenance_configuration_list_cmd = 'aks maintenanceconfiguration list ' \
            '-g {resource_group} --cluster-name {name}'
        self.cmd(maintenance_configuration_list_cmd, checks=[self.check('length(@)', 2)])

        # update maintenanceconfiguration from config file
        maintenance_configuration_update_cmd = 'aks maintenanceconfiguration update ' \
            '-g {resource_group} --cluster-name {name} ' \
            '-n {auto_upgrade_config_name} ' \
            '--config-file {mc_path}'

        self.cmd(
            maintenance_configuration_update_cmd, checks=[
                self.exists('maintenanceWindow.schedule.absoluteMonthly'),
                self.check('maintenanceWindow.schedule.absoluteMonthly.dayOfMonth', 1),
                self.check('maintenanceWindow.schedule.absoluteMonthly.intervalMonths', 3),
                self.check('maintenanceWindow.durationHours', 4),
                self.check('maintenanceWindow.utcOffset', '-08:00'),
                self.check('maintenanceWindow.startTime', '09:00'),
                self.check('maintenanceWindow.notAllowedDates | length(@)', 2)]
        )

        # maintenanceconfiguration show
        maintenance_configuration_show_cmd = 'aks maintenanceconfiguration show ' \
            '-g {resource_group} --cluster-name {name} ' \
            '-n {auto_upgrade_config_name}'
        self.cmd(
            maintenance_configuration_show_cmd, checks=[
                self.check("name == '{auto_upgrade_config_name}'", True)]
        )

        # maintenanceconfiguration delete
        maintenance_configuration_delete_cmd = 'aks maintenanceconfiguration delete ' \
            '-g {resource_group} --cluster-name {name} ' \
            '-n {auto_upgrade_config_name}'
        self.cmd(maintenance_configuration_delete_cmd, checks=[self.is_empty()])

        maintenance_configuration_delete_cmd = 'aks maintenanceconfiguration delete ' \
            '-g {resource_group} --cluster-name {name} ' \
            '-n {node_os_upgrade_config_name}'
        self.cmd(maintenance_configuration_delete_cmd, checks=[self.is_empty()])

        # maintenanceconfiguration list
        maintenance_configuration_list_cmd = 'aks maintenanceconfiguration list ' \
            '-g {resource_group} --cluster-name {name}'
        self.cmd(maintenance_configuration_list_cmd, checks=[self.is_empty()])

        # delete
        self.cmd('aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_maintenanceconfiguration(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'mc_path': get_test_data_file_path('maintenanceconfig.json'),
            'ssh_key_value': self.generate_ssh_keys()
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # maintenanceconfiguration add
        maintenance_configuration_add_cmd = 'aks maintenanceconfiguration add -g {resource_group} --cluster-name {name} -n default --weekday Monday --start-hour 1'
        self.cmd(
            maintenance_configuration_add_cmd, checks=[
                self.check('timeInWeek[0].day', 'Monday'),
                self.check('timeInWeek[0].day', 'Monday'),
                self.check('timeInWeek[0].hourSlots | contains(@, `1`)', True)]
        )

        # maintenanceconfiguration update (from config file)
        maintenance_configuration_update_cmd = 'aks maintenanceconfiguration update -g {resource_group} --cluster-name {name} -n default --config-file {mc_path}'
        self.cmd(
            maintenance_configuration_update_cmd, checks=[
                self.check(
                    "timeInWeek[*].day | contains(@, 'Tuesday') && contains(@, 'Wednesday')", True),
                self.check(
                    "timeInWeek[*].hourSlots[*] | contains([0], `2`) && contains([1], `6`)", True),
                self.check("notAllowedTime | length(@) == `2`", True)]
        )

        # maintenanceconfiguration show
        maintenance_configuration_show_cmd = 'aks maintenanceconfiguration show -g {resource_group} --cluster-name {name} -n default'
        self.cmd(
            maintenance_configuration_show_cmd, checks=[
                self.check("name == 'default'", True)]
        )

        # maintenanceconfiguration delete
        maintenance_configuration_delete_cmd = 'aks maintenanceconfiguration delete -g {resource_group} --cluster-name {name} -n default'
        self.cmd(
            maintenance_configuration_delete_cmd, checks=[self.is_empty()])

        # maintenanceconfiguration list
        maintenance_configuration_list_cmd = 'aks maintenanceconfiguration list -g {resource_group} --cluster-name {name}'
        self.cmd(
            maintenance_configuration_list_cmd, checks=[self.is_empty()])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_update_upgrade_settings(self, resource_group, resource_group_location):
        """ This test case exercises enabling and disabling forceUpgrade override in cluster upgradeSettings.
        """

        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
        'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        # create
        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--enable-managed-identity ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
            self.not_exists('upgradeSettings')
        ])

        # update upgrade settings
        self.cmd('aks update --resource-group={resource_group} --name={name} --upgrade-override-until 2020-01-01T22:30:17+00:00', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.not_exists('upgradeSettings.overrideSettings.forceUpgrade'),
            self.exists('upgradeSettings.overrideSettings.until')
        ])
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-force-upgrade', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('upgradeSettings.overrideSettings.forceUpgrade', True),
            self.exists('upgradeSettings.overrideSettings.until')
        ])
        self.cmd('aks update --resource-group={resource_group} --name={name} --enable-force-upgrade --upgrade-override-until 2020-02-22T22:30:17+00:00', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('upgradeSettings.overrideSettings.forceUpgrade', True),
            self.check('upgradeSettings.overrideSettings.until', '2020-02-22T22:30:17+00:00')
        ])
        self.cmd('aks update --resource-group={resource_group} --name={name} --disable-force-upgrade', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('upgradeSettings.overrideSettings.forceUpgrade', False),
            self.check('upgradeSettings.overrideSettings.until', '2020-02-22T22:30:17+00:00')
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_create_with_nsg_control(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)

        port_ranges = [
            {
                'portEnd': 53,
                'portStart': 53,
                'protocol': 'UDP',
            },
            {
                'portEnd': 80,
                'portStart': 80,
                'protocol': 'TCP',
            },
            {
                'portEnd': 443,
                'portStart': 443,
                'protocol': 'TCP',
            },
            {
                'portEnd': 5000,
                'portStart': 4000,
                'protocol': 'TCP',
            },
            {
                'portEnd': 6000,
                'portStart': 4000,
                'protocol': "UDP",
            }
        ]

        allowed_host_ports_arguments = []
        for i, port_range in enumerate(port_ranges):
            start, end, protocol = port_range['portStart'], port_range['portEnd'], port_range['protocol']
            if start == end:
                v = '{}/{}'.format(start, protocol)
            else:
                v = '{}-{}/{}'.format(start, end, protocol)
            allowed_host_ports_arguments.append(v)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
            'node_vm_size': 'standard_d2s_v3',
            'asg1': 'asg1',
            'asg2': 'asg2',
            'allowed_host_ports_argument': '--nodepool-allowed-host-ports {}'.format(' '.join(allowed_host_ports_arguments)),
        })

        create_asg1 = 'network asg create --name {asg1} --resource-group {resource_group} -o json'
        create_asg2 = 'network asg create --name {asg2} --resource-group {resource_group} -o json'
        asg1 = self.cmd(create_asg1, checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        asg2 = self.cmd(create_asg2, checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        asg_ids = [asg1['id'], asg2['id']]

        self.kwargs.update({
            'asg_ids_argument': '--nodepool-asg-ids {}'.format(' '.join(asg_ids)),
        })

        self.cmd(
            'aks create '
            '--resource-group={resource_group} '
            '--name={name} '
            '--location={location} '
            '--ssh-key-value={ssh_key_value} '
            '--node-count=1 '
            '--node-vm-size={node_vm_size} ' 
            '{asg_ids_argument} '
            '{allowed_host_ports_argument}',
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('agentPoolProfiles[0].networkProfile.applicationSecurityGroups', asg_ids),
                self.check('agentPoolProfiles[0].networkProfile.allowedHostPorts', port_ranges),
            ],
        )

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_nodepool_create_with_nsg_control(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool_name = self.create_random_name('n', 6)

        port_ranges = [
            {
                'portEnd': 53,
                'portStart': 53,
                'protocol': 'UDP',
            },
            {
                'portEnd': 80,
                'portStart': 80,
                'protocol': 'TCP',
            },
            {
                'portEnd': 443,
                'portStart': 443,
                'protocol': 'TCP',
            },
            {
                'portEnd': 5000,
                'portStart': 4000,
                'protocol': 'TCP',
            },
            {
                'portEnd': 6000,
                'portStart': 4000,
                'protocol': "UDP",
            }
        ]

        allowed_host_ports_arguments = []
        for i, port_range in enumerate(port_ranges):
            start, end, protocol = port_range['portStart'], port_range['portEnd'], port_range['protocol']
            if start == end:
                v = '{}/{}'.format(start, protocol)
            else:
                v = '{}-{}/{}'.format(start, end, protocol)
            allowed_host_ports_arguments.append(v)


        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
            'node_pool_name': nodepool_name,
            'node_vm_size': 'standard_d2s_v3',
            'asg1': 'asg1',
            'asg2': 'asg2',
            'allowed_host_ports_argument': '--allowed-host-ports {}'.format(' '.join(allowed_host_ports_arguments)),
        })
        create_asg1 = 'network asg create --name {asg1} --resource-group {resource_group} -o json'
        create_asg2 = 'network asg create --name {asg2} --resource-group {resource_group} -o json'
        asg1 = self.cmd(create_asg1, checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        asg2 = self.cmd(create_asg2, checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        asg_ids = [asg1['id'], asg2['id']]

        self.kwargs.update({
            'asg_ids_argument': '--asg-ids {}'.format(' '.join(asg_ids)),
        })

        self.cmd(
            'aks create '
            '--resource-group={resource_group} '
            '--name={name} '
            '--location={location} '
            '--ssh-key-value={ssh_key_value} '
            '--node-count=1 '
            '--node-vm-size={node_vm_size} ',
            checks=[
                self.check('provisioningState', 'Succeeded'),
            ],
        )

        self.cmd(
            'aks nodepool add '
            '--resource-group={resource_group} '
            '--cluster-name={name} '
            '--name={node_pool_name} '
            '--node-vm-size={node_vm_size} '
            '--node-count=1 '
            '{asg_ids_argument} '
            '{allowed_host_ports_argument}',
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('networkProfile.applicationSecurityGroups', asg_ids),
                self.check('networkProfile.allowedHostPorts', port_ranges),
            ],
        )

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    def test_aks_nodepool_update_with_nsg_control(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool_name = self.create_random_name('n', 6)

        port_ranges = [
            {
                'portEnd': 53,
                'portStart': 53,
                'protocol': 'UDP',
            },
            {
                'portEnd': 80,
                'portStart': 80,
                'protocol': 'TCP',
            },
            {
                'portEnd': 443,
                'portStart': 443,
                'protocol': 'TCP',
            },
            {
                'portEnd': 5000,
                'portStart': 4000,
                'protocol': 'TCP',
            },
            {
                'portEnd': 6000,
                'portStart': 4000,
                'protocol': "UDP",
            }
        ]

        allowed_host_ports_arguments = []
        for i, port_range in enumerate(port_ranges):
            start, end, protocol = port_range['portStart'], port_range['portEnd'], port_range['protocol']
            if start == end:
                v = '{}/{}'.format(start, protocol)
            else:
                v = '{}-{}/{}'.format(start, end, protocol)
            allowed_host_ports_arguments.append(v)


        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
            'node_pool_name': nodepool_name,
            'node_vm_size': 'standard_d2s_v3',
            'asg1': 'asg1',
            'asg2': 'asg2',
            'allowed_host_ports_argument': '--allowed-host-ports {}'.format(' '.join(allowed_host_ports_arguments)),
        })
        create_asg1 = 'network asg create --name {asg1} --resource-group {resource_group} -o json'
        create_asg2 = 'network asg create --name {asg2} --resource-group {resource_group} -o json'
        asg1 = self.cmd(create_asg1, checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        asg2 = self.cmd(create_asg2, checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        asg_ids = [asg1['id'], asg2['id']]

        self.kwargs.update({
            'asg_ids_argument': '--asg-ids {}'.format(' '.join(asg_ids)),
        })

        self.cmd(
            'aks create '
            '--resource-group={resource_group} '
            '--name={name} '
            '--location={location} '
            '--ssh-key-value={ssh_key_value} '
            '--nodepool-name={node_pool_name} '
            '--node-count=1 '
            '--node-vm-size={node_vm_size} ',
            checks=[
                self.check('provisioningState', 'Succeeded'),
            ],
        )

        self.cmd(
            'aks nodepool update '
            '--resource-group={resource_group} '
            '--cluster-name={name} '
            '--name={node_pool_name} '
            '{asg_ids_argument} '
            '{allowed_host_ports_argument}',
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('networkProfile.applicationSecurityGroups', asg_ids),
                self.check('networkProfile.allowedHostPorts', port_ranges),
            ],
        )

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    # TODO(nilo19): uncomment this when the RP API is ready. The newly added field `backendPoolType` cannot be shown
    # in the response body but the feature works.
    # @AllowLargeResponse()
    # @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    # def test_aks_create_or_update_with_load_balancer_backend_pool_type(self, resource_group, resource_group_location):
    #     _, create_version = self._get_versions(resource_group_location)
    #     aks_name = self.create_random_name('cliakstest', 16)
    #     self.kwargs.update({
    #         'resource_group': resource_group,
    #         'name': aks_name,
    #         'location': resource_group_location,
    #         'k8s_version': create_version,
    #         'ssh_key_value': self.generate_ssh_keys(),
    #     })
    #
    #     # create
    #     create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
    #                  '--ssh-key-value={ssh_key_value} ' \
    #                  '--kubernetes-version={k8s_version} ' \
    #                  '--load-balancer-backend-pool-type=nodeIP'
    #     self.cmd(create_cmd, checks=[
    #         self.check('networkProfile.loadBalancerProfile.backendPoolType', 'nodeIP'),
    #     ])
    #
    #     # update
    #     update_cmd = 'aks update -g {resource_group} -n {name} --load-balancer-backend-pool-type=nodeIPConfiguration'
    #     self.cmd(update_cmd, checks=[
    #         self.check('networkProfile.loadBalancerProfile.backendPoolType', 'nodeIPConfiguration'),
    #     ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_node_public_ip_tags(self, resource_group, resource_group_location):
        aks_name = self.create_random_name('cliakstest', 16)
        nodepool_name = self.create_random_name('n', 6)
        nodepool_name_1 = self.create_random_name('n', 6)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'ssh_key_value': self.generate_ssh_keys(),
            'node_pool_name': nodepool_name,
            'node_vm_size': 'standard_d2a_v4',
            "node_public_ip_tags": "RoutingPreference=Internet"
        })

        self.cmd(
            'aks create '
            '--resource-group={resource_group} '
            '--name={name} '
            '--location={location} '
            '--ssh-key-value={ssh_key_value} '
            '--nodepool-name={node_pool_name} '
            '--node-count=1 '
            '--node-vm-size={node_vm_size} '
            '--enable-node-public-ip '
            '--node-public-ip-tags={node_public_ip_tags} ',
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('agentPoolProfiles[0].networkProfile.nodePublicIpTags[0].ipTagType', "RoutingPreference"),
                self.check('agentPoolProfiles[0].networkProfile.nodePublicIpTags[0].tag', "Internet"),
            ],
        )

        self.kwargs.update({
            'node_pool_name': nodepool_name_1,
        })

        self.cmd(
            'aks nodepool add '
            '--resource-group={resource_group} '
            '--cluster-name={name} '
            '--name={node_pool_name} '
            '--node-vm-size={node_vm_size} '
            '--enable-node-public-ip '
            '--node-public-ip-tags={node_public_ip_tags} '
            '--aks-custom-headers=AKSHTTPCustomFeatures=Microsoft.ContainerService/NodePublicIPTagsPreview',
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('networkProfile.nodePublicIpTags[0].ipTagType', "RoutingPreference"),
                self.check('networkProfile.nodePublicIpTags[0].tag', "Internet"),
            ],
        )

        # delete
        cmd = 'aks delete --resource-group={resource_group} --name={name} --yes --no-wait'
        self.cmd(cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    def test_list_trustedaccess_roles(self):
        cmd = 'aks trustedaccess role list -l westus2'
        self.cmd(cmd, checks=[
            StringContainCheck("sourceResourceType"),
            StringContainCheck("apiGroups"),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_trustedaccess_rolebinding(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'vm_size': 'Standard_D4s_v3',
            'node_count': 1,
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = ' '.join([
            'aks', 'create', '--resource-group={resource_group}', '--name={name}', '--location={location}',
            '--node-vm-size {vm_size}',
            '--node-count {node_count}',
            '--ssh-key-value={ssh_key_value}'
        ])

        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        nodeRG = self.cmd('az aks show -g {resource_group} -n {name}'). \
            get_output_in_json().get("nodeResourceGroup")
        self.kwargs.update({
            'nodeRG': nodeRG
        })

        vmss_id = self.cmd('az vmss list -g {nodeRG}').get_output_in_json()[0]['id']
        self.kwargs.update({
            'vmss_id': vmss_id
        })

        list_binding_cmd = 'aks trustedaccess rolebinding list ' \
            '--cluster-name={name} ' \
            '--resource-group={resource_group}'
        self.cmd(list_binding_cmd, checks=[
            self.is_empty(),
        ])

        create_binding_cmd = 'aks trustedaccess rolebinding create ' \
            '--resource-group={resource_group} ' \
            '--cluster-name={name} ' \
            '-n testbinding ' \
            '-r {vmss_id} ' \
            '--roles Microsoft.Compute/virtualMachineScaleSets/test-node-reader '
        self.cmd(create_binding_cmd)
        self.cmd(list_binding_cmd, checks=[
            self.check('[0].type', 'Microsoft.ContainerService/managedClusters/trustedAccessRoleBindings'),
            self.check('[0].name', 'testbinding'),
        ])

        get_binding_cmd = 'aks trustedaccess rolebinding show ' \
            '-n testbinding ' \
            '--resource-group={resource_group} ' \
            '--cluster-name={name}'
        self.cmd(get_binding_cmd, checks=[
            self.check('type', 'Microsoft.ContainerService/managedClusters/trustedAccessRoleBindings'),
            self.check('name', 'testbinding'),
            self.check('provisioningState', 'Succeeded'),
        ])

        update_binding_cmd = 'aks trustedaccess rolebinding update ' \
            '--cluster-name={name} ' \
            '-n testbinding ' \
            '--resource-group={resource_group} ' \
            '--roles Microsoft.Compute/virtualMachineScaleSets/test-pod-reader '
        self.cmd(update_binding_cmd, checks=[
            self.check('roles[0]', 'Microsoft.Compute/virtualMachineScaleSets/test-pod-reader'),
        ])

        delete_binding_cmd = 'aks trustedaccess rolebinding delete ' \
            '--cluster-name={name} ' \
            '-n testbinding ' \
            '--resource-group={resource_group} -y'
        self.cmd(delete_binding_cmd)
        self.cmd(list_binding_cmd, checks=[
            self.is_empty(),
        ])

    @AllowLargeResponse()
    @AKSCustomResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='westus2')
    def test_aks_create_with_crg_id(self, resource_group, resource_group_location):
        # reset the count so in replay mode the random names will start with 0
        self.test_resources_count = 0
        # kwargs for string formatting
        aks_name = self.create_random_name('cliakstest', 16)
        node_pool_name = self.create_random_name('c', 6)
        node_pool_name_second = self.create_random_name('c', 6)
        crg_id = '/subscriptions/26fe00f8-9173-4872-9134-bb1d2e00343a/resourceGroups/STAGING-CRG-RG/providers/Microsoft.Compute/capacityReservationGroups/crg-1'
        vm_size = 'Standard_D2s_v3'
        count = 1
        identity = '/subscriptions/26fe00f8-9173-4872-9134-bb1d2e00343a/resourceGroups/STAGING-CRG-RG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/crg-1-id'

        self.kwargs.update({
            'resource_group': resource_group,
            'name': aks_name,
            'count': count,
            'location': resource_group_location,
            'crg_id': crg_id,
            'vm_size': vm_size,
            'identity': identity,
            'node_pool_name': node_pool_name,
            'node_pool_name_second': node_pool_name_second,
            'resource_type': 'Microsoft.ContainerService/ManagedClusters',
            'ssh_key_value': self.generate_ssh_keys(),
        })

        create_cmd = 'aks create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--node-vm-size {vm_size} ' \
                     '--nodepool-name {node_pool_name} -c 1 ' \
                     '--enable-managed-identity ' \
                     '--assign-identity {identity} ' \
                     '--crg-id={crg_id} ' \
                     '--ssh-key-value={ssh_key_value}'
        self.cmd(create_cmd, checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # nodepool get-upgrades
        self.cmd('aks nodepool add '
                 '--resource-group={resource_group} '
                 '--cluster-name={name} '
                 '--name={node_pool_name_second} '
                 '--node-vm-size {vm_size} '
                 '--crg-id={crg_id} '
                 '-c 1 ',
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
        ])

        # delete
        self.cmd(
            'aks delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty(),
        ])

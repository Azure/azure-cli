# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import tempfile
import unittest
import yaml
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, live_only, record_only


class AzureContainerInstanceScenarioTest(ScenarioTest):
    # Test create container with image, os type, ip address type, port, dns name label, cpu,
    # memory, command line and environment variables specified.
    @ResourceGroupPreparer()
    def test_container_create(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        dns_name_label = container_group_name
        fqdn = '{}.{}.azurecontainer.io'.format(
            container_group_name, resource_group_location)
        port1 = 8000
        port2 = 8001
        ports = '{} {}'.format(port1, port2)
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='
        restart_policy = 'Never'
        secrets = 'secret1=superawesomesecret secret2="nothing to see"'
        secret_path = '/s'
        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type,
            'dns_name_label': dns_name_label,
            'fqdn': fqdn,
            'ip_address_type': ip_address_type,
            'port1': port1,
            'port2': port2,
            'ports': ports,
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'env': env,
            'restart_policy': restart_policy,
            'secrets': secrets,
            'secrets_mount_path': secret_path
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --dns-name-label {dns_name_label} --ports {ports} --cpu {cpu} --memory {memory} '
                 '--command-line {command} -e {env} --restart-policy {restart_policy} '
                 '--secrets {secrets} --secrets-mount-path {secrets_mount_path}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('ipAddress.dnsNameLabel',
                                    '{container_group_name}'),
                         self.check('ipAddress.fqdn', '{fqdn}'),
                         self.exists('ipAddress.ip'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.exists('volumes'),
                         self.check('volumes[0].secret', {})])

        # Test show
        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.exists('ipAddress.ip'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check('containers[0].resources.requests.memoryInGb', memory)])

        # Test list
        self.cmd('container list -g {rg}',
                 checks=[self.check('[0].name', '{container_group_name}'),
                         self.check('[0].location',
                                    '{resource_group_location}'),
                         self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[0].osType', '{os_type}'),
                         self.check('[0].restartPolicy', '{restart_policy}'),
                         self.exists('[0].ipAddress.ip'),
                         self.exists('[0].ipAddress.ports'),
                         self.check('[0].ipAddress.ports[0].port', '{port1}'),
                         self.check('[0].ipAddress.ports[1].port', '{port2}'),
                         self.check('[0].containers[0].image', '{image}'),
                         self.exists('[0].containers[0].command'),
                         self.exists('[0].containers[0].environmentVariables'),
                         self.check(
                             '[0].containers[0].resources.requests.cpu', cpu),
                         self.check('[0].containers[0].resources.requests.memoryInGb', memory)])

        # Test logs
        self.cmd('container logs -g {rg} -n {container_group_name}')

        # Test delete
        self.cmd('container delete -g {rg} -n {container_group_name} -y',
            checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('ipAddress.dnsNameLabel',
                                    '{container_group_name}'),
                         self.check('ipAddress.fqdn', '{fqdn}'),
                         self.exists('ipAddress.ip'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.exists('volumes'),
                         self.check('volumes[0].secret', {})])
						 
    # Test create container with Spot Priority
    @ResourceGroupPreparer()
    def test_container_create_spot_priority(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='
        restart_policy = 'Never'
        priority = 'Spot'
        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type, 
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'env': env,
            'restart_policy': restart_policy,
            'priority' : priority
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --os-type {os_type} '
                 '--cpu {cpu} --memory {memory} --priority {priority} '
                 '--command-line {command} -e {env} --restart-policy {restart_policy}  ',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test show
        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test logs
        self.cmd('container logs -g {rg} -n {container_group_name}')

        # Test delete
        self.cmd('container delete -g {rg} -n {container_group_name} -y',
            checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

    # Test create container with Regular Priority
    @ResourceGroupPreparer()
    def test_container_create_regular_priority(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='
        restart_policy = 'Never'
        priority = 'Regular'
        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type, 
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'env': env,
            'restart_policy': restart_policy,
            'priority' : priority
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --os-type {os_type} '
                 '--cpu {cpu} --memory {memory} --priority {priority} '
                 '--command-line {command} -e {env} --restart-policy {restart_policy}  ',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test show
        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test logs
        self.cmd('container logs -g {rg} -n {container_group_name}')

        # Test delete
        self.cmd('container delete -g {rg} -n {container_group_name} -y',
            checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

    # Test create container using managed identities.
    @ResourceGroupPreparer()
    def test_container_create_with_msi(self, resource_group, resource_group_location):
        container_group_name1 = self.create_random_name('clicontainer', 16)
        container_group_name2 = self.create_random_name('clicontainer', 16)
        container_group_name3 = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        user_assigned_identity_name = self.create_random_name('cliaciidentity', 20)
        system_assigned_identity = '[system]'
        cpu = 1
        memory = 1

        self.kwargs.update({
            'user_assigned_identity_name': user_assigned_identity_name,
        })

        msi_identity_result = self.cmd('identity create -g {rg} -n {user_assigned_identity_name}').get_output_in_json()

        self.kwargs.update({
            'container_group_name1': container_group_name1,
            'container_group_name2': container_group_name2,
            'container_group_name3': container_group_name3,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'user_assigned_identity': msi_identity_result['id'],
            'system_assigned_identity': system_assigned_identity,
            'cpu': 1,
            'memory': 1
        })

        # Test create system assigned identity
        self.cmd('container create -g {rg} -n {container_group_name1} --image {image} --os-type {os_type} --cpu {cpu} --memory {memory} '
                 '--ip-address {ip_address_type} --assign-identity',
                 checks=[self.check('name', '{container_group_name1}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('identity.type', 'SystemAssigned'),
                         self.exists('ipAddress.ip'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('containers[0].image', '{image}')])

        # Test create user assigned identity
        self.cmd('container create -g {rg} -n {container_group_name2} --image {image} --os-type {os_type} --cpu {cpu} --memory {memory} '
                 '--ip-address {ip_address_type} --assign-identity {user_assigned_identity}',
                 checks=[self.check('name', '{container_group_name2}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('identity.type', 'UserAssigned'),
                         self.exists('ipAddress.ip'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('containers[0].image', '{image}')])

        # Test create system user assigned identity
        self.cmd('container create -g {rg} -n {container_group_name3} --image {image} --os-type {os_type} --cpu {cpu} --memory {memory} '
                 '--ip-address {ip_address_type} --assign-identity {system_assigned_identity} {user_assigned_identity}',
                 checks=[self.check('name', '{container_group_name3}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('identity.type', 'SystemAssigned, UserAssigned'),
                         self.exists('ipAddress.ip'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('containers[0].image', '{image}')])

    # Test create container using managed identities with scope.
    @live_only()
    @ResourceGroupPreparer()
    def test_container_create_with_msi_scope(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        cpu = 1
        memory = 1
        storage_account_name = self.create_random_name('clistorage', 16)

        self.kwargs.update({
            'storage_account_name': storage_account_name
        })

        storage_account_result = self.cmd('az storage account create -n {storage_account_name} -g {rg} ').get_output_in_json()

        self.kwargs.update({
            'container_group_name1': container_group_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'cpu': cpu,
            'memory': memory,
            'msi_scope': storage_account_result['id']
        })

        # Test create system assigned identity with scope
        self.cmd('container create -g {rg} -n {container_group_name1} --image {image} --os-type {os_type} --cpu {cpu} --memory {memory} '
                 '--ip-address {ip_address_type} --assign-identity --scope {msi_scope}',
                 checks=[self.check('name', '{container_group_name1}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('identity.type', 'SystemAssigned'),
                         self.exists('ipAddress.ip'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('containers[0].image', '{image}')])

    # Test create container with azure container registry image.
    # An ACR instance is required to re-record this test with 'nginx:latest' image available in the url.
    # see https://learn.microsoft.com/azure/container-registry/container-registry-get-started-docker-cli
    # After recording, regenerate the password for the acr instance.
    @record_only()  # This test relies on existing ACR image
    @ResourceGroupPreparer()
    def test_container_create_with_acr(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        registry_username = 'azclitest'
        registry_server = '{}.azurecr.io'.format(registry_username)
        image = '{}/nginx:latest'.format(registry_server)
        password = 'passplaceholder'
        cpu = 1
        memory = 1
        os_type = 'Linux'

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'registry_username': registry_username,
            'registry_server': registry_server,
            'image': image,
            'password': password,
            'cpu': cpu,
            'memory': memory,
            'os_type': os_type
        })

        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --registry-username {registry_username} --registry-password {password} --cpu {cpu} --memory {memory} --os-type {os_type}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('containers[0].image', '{image}'),
                         self.check(
                             'imageRegistryCredentials[0].server', '{registry_server}'),
                         self.check(
                             'imageRegistryCredentials[0].username', '{registry_username}'),
                         self.exists('containers[0].resources.requests.cpu'),
                         self.exists('containers[0].resources.requests.memoryInGb')])

        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('containers[0].image', '{image}'),
                         self.check(
                             'imageRegistryCredentials[0].server', '{registry_server}'),
                         self.check(
                             'imageRegistryCredentials[0].username', '{registry_username}'),
                         self.exists('containers[0].resources.requests.cpu'),
                         self.exists('containers[0].resources.requests.memoryInGb')])

    # Test create container with VNET argument validations.
    @ResourceGroupPreparer()
    def test_container_create_with_vnet(self, resource_group, resource_group_location):
        from azure.core.exceptions import HttpResponseError
        from knack.util import CLIError

        test_sub_id = '00000000-0000-0000-0000-000000000000'
        container_group_name = self.create_random_name('clicontainer', 16)
        vnet_name = self.create_random_name('vent', 16)
        subnet_name = self.create_random_name('subnet', 16)
        ip_address_type = "Private"

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'vnet_name': vnet_name,
            'subnet_name': subnet_name,
            'ip_addresss': ip_address_type
        })

        # Create NSG
        self.cmd('network nsg create -g {rg} -n {vnet_name}nsg')

        # Create VNET
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name} --address-prefixes 10.0.0.0/24 --network-security-group {vnet_name}nsg')

        # Vnet name with no subnet
        with self.assertRaisesRegex(CLIError, "usage error: --vnet NAME --subnet NAME | --vnet ID --subnet NAME | --subnet ID"):
            self.cmd('container create -g {rg} -n {container_group_name} --image mcr.microsoft.com/azuredocs/aci-helloworld:latest --vnet {vnet_name} --cpu 1 --memory 1 --os-type Linux')

        # Subnet name with no vnet name
        with self.assertRaisesRegex(CLIError, "usage error: --vnet NAME --subnet NAME | --vnet ID --subnet NAME | --subnet ID"):
            self.cmd('container create -g {rg} -n {container_group_name} --image mcr.microsoft.com/azuredocs/aci-helloworld:latest --cpu 1 --memory 1 --os-type Linux '
                     '--subnet {subnet_name} ')

        self.cmd('container create -g {rg} -n {container_group_name} --image mcr.microsoft.com/azuredocs/aci-helloworld:latest --vnet {vnet_name} --subnet {subnet_name} --ip-address {ip_addresss} --cpu 1 --memory 1 --os-type Linux',
            checks=[self.exists('subnetIds[0].id')])


    # Test export container.
    @ResourceGroupPreparer()
    def test_container_export(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        cpu = 1
        memory = 1

        _, output_file = tempfile.mkstemp()

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'output_file': output_file,
            'image': image,
            'cpu': cpu,
            'memory': memory,
            'os_type': os_type
        })

        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --cpu {cpu} --memory {memory} --os-type {os_type}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].resources.requests.cpu'),
                         self.exists('containers[0].resources.requests.memoryInGb')])
        self.cmd('container export -g {rg} -n {container_group_name} -f "{output_file}"')

        cg_definition = None
        with open(output_file, 'r') as f:
            cg_definition = yaml.safe_load(f)

        self.check(cg_definition["name"], container_group_name)
        self.check(cg_definition['properties']['containers'][0]['properties']['image'], image)
        self.check(cg_definition['location'], resource_group_location)
        self.check(cg_definition['properties']['containers'][0]['properties']['resources']['requests']['cpu'], 1.0)
        self.check(cg_definition['properties']['containers'][0]['properties']['resources']['requests']['memoryInGB'], 1.5)

    # Test export container with identity.
    @ResourceGroupPreparer()
    def test_container_export_with_identity(self, resource_group, resource_group_location):
        container_group_name1 = self.create_random_name('clicontainer', 16)
        container_group_name2 = self.create_random_name('clicontainer', 16)
        container_group_name3 = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        user_assigned_identity_name = self.create_random_name('cliaciidentity', 20)
        system_assigned_identity = '[system]'
        os_type = 'Linux'
        cpu = 1
        memory = 1

        self.kwargs.update({
            'user_assigned_identity_name': user_assigned_identity_name,
        })

        msi_identity_result = self.cmd('identity create -g {rg} -n {user_assigned_identity_name}').get_output_in_json()

        _, output_file = tempfile.mkstemp()

        def check_export_with_identity(container_group_name, identity_type):
            cg_definition = None
            with open(output_file, 'r') as f:
                cg_definition = yaml.safe_load(f)

            self.check(cg_definition["name"], container_group_name)
            self.check(cg_definition['properties']['containers'][0]['properties']['image'], image)
            self.check(cg_definition['location'], resource_group_location)
            self.check(cg_definition['identity']['type'], identity_type)
            if 'UserAssigned' in identity_type:
                self.exists(cg_definition['identity']['user_assigned_identities'])

        self.kwargs.update({
            'container_group_name1': container_group_name1,
            'container_group_name2': container_group_name2,
            'container_group_name3': container_group_name3,
            'resource_group_location': resource_group_location,
            'output_file': output_file,
            'image': image,
            'cpu': cpu,
            'memory': memory,
            'os_type': os_type,
            'user_assigned_identity': msi_identity_result['id'],
            'system_assigned_identity': system_assigned_identity,
        })

        # Test create system assigned identity
        self.cmd('container create -g {rg} -n {container_group_name1} --image {image} --cpu {cpu} --memory {memory} --os-type {os_type} --assign-identity',
                 checks=[self.check('name', '{container_group_name1}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('containers[0].image', '{image}'),
                         self.check('identity.type', 'SystemAssigned')])
        self.cmd('container export -g {rg} -n {container_group_name1} -f "{output_file}"')
        check_export_with_identity(container_group_name1, 'SystemAssigned')

        # Test create user assigned identity
        self.cmd('container create -g {rg} -n {container_group_name2} --image {image} --cpu {cpu} --memory {memory} --os-type {os_type} --assign-identity {user_assigned_identity}',
                 checks=[self.check('name', '{container_group_name2}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('containers[0].image', '{image}'),
                         self.check('identity.type', 'UserAssigned')])
        self.cmd('container export -g {rg} -n {container_group_name2} -f "{output_file}"')
        check_export_with_identity(container_group_name2, 'UserAssigned')

        # Test create system user assigned identity
        self.cmd('container create -g {rg} -n {container_group_name3} --image {image} --cpu {cpu} --memory {memory} --os-type {os_type} --assign-identity {system_assigned_identity} {user_assigned_identity}',
                 checks=[self.check('name', '{container_group_name3}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('containers[0].image', '{image}'),
                         self.check('identity.type', 'SystemAssigned, UserAssigned')])
        self.cmd('container export -g {rg} -n {container_group_name3} -f "{output_file}"')
        check_export_with_identity(container_group_name3, 'SystemAssigned, UserAssigned')

    # Test create container with azure file volume
    @ResourceGroupPreparer()
    @unittest.skip("Skip test as unable to re-record due to missing pre-req. resources.")
    def test_container_azure_file_volume_mount(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        azure_file_volume_share_name = 'testshare'
        azure_file_volume_account_name = 'ccondemostore1'
        azure_file_volume_account_key = 'mockstorageaccountkey'
        azure_file_volume_mount_path = '/mnt/azfile'

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'azure_file_volume_share_name': azure_file_volume_share_name,
            'azure_file_volume_account_name': azure_file_volume_account_name,
            'azure_file_volume_account_key': azure_file_volume_account_key,
            'azure_file_volume_mount_path': azure_file_volume_mount_path,
        })

        self.cmd('container create -g {rg} -n {container_group_name} --image nginx '
                 '--azure-file-volume-share-name {azure_file_volume_share_name} '
                 '--azure-file-volume-account-name {azure_file_volume_account_name} '
                 '--azure-file-volume-account-key {azure_file_volume_account_key} '
                 '--azure-file-volume-mount-path {azure_file_volume_mount_path}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].azureFile'),
                         self.check(
                             'volumes[0].azureFile.shareName', '{azure_file_volume_share_name}'),
                         self.check(
                             'volumes[0].azureFile.storageAccountName', '{azure_file_volume_account_name}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{azure_file_volume_mount_path}')])

        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].azureFile'),
                         self.check(
                             'volumes[0].azureFile.shareName', '{azure_file_volume_share_name}'),
                         self.check(
                             'volumes[0].azureFile.storageAccountName', '{azure_file_volume_account_name}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{azure_file_volume_mount_path}')])

    # Test create container with git repo volume
    @ResourceGroupPreparer()
    @unittest.skip("Skip test as unable to re-record due to missing pre-req. resources.")
    def test_container_git_repo_volume_mount(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        gitrepo_url = 'https://github.com/yolo3301/dumb-flow.git'
        gitrepo_dir = './test'
        gitrepo_revision = '5604f0a8f11bfe13e621418ab6f6a71973e208ce'
        gitrepo_mount_path = '/src'

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'gitrepo_url': gitrepo_url,
            'gitrepo_dir': gitrepo_dir,
            'gitrepo_revision': gitrepo_revision,
            'gitrepo_mount_path': gitrepo_mount_path,
        })

        self.cmd('container create -g {rg} -n {container_group_name} --image nginx '
                 '--gitrepo-url {gitrepo_url} '
                 '--gitrepo-dir {gitrepo_dir} '
                 '--gitrepo-revision {gitrepo_revision} '
                 '--gitrepo-mount-path {gitrepo_mount_path}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].gitRepo'),
                         self.check(
                             'volumes[0].gitRepo.repository', '{gitrepo_url}'),
                         self.check(
                             'volumes[0].gitRepo.directory', '{gitrepo_dir}'),
                         self.check(
                             'volumes[0].gitRepo.revision', '{gitrepo_revision}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{gitrepo_mount_path}')])

        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].gitRepo'),
                         self.check(
                             'volumes[0].gitRepo.repository', '{gitrepo_url}'),
                         self.check(
                             'volumes[0].gitRepo.directory', '{gitrepo_dir}'),
                         self.check(
                             'volumes[0].gitRepo.revision', '{gitrepo_revision}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{gitrepo_mount_path}')])

    # Changing to live only because of intermittent test failures: https://github.com/Azure/azure-cli/issues/19804
    @live_only()
    @ResourceGroupPreparer()
    def test_container_attach(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'echo hello; sleep 15; done\'"'
        restart_policy = 'Never'

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'restart_policy': restart_policy,
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --cpu {cpu} --memory {memory} '
                 '--command-line {command} --restart-policy {restart_policy} ',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        self.cmd('container attach -g {rg} -n {container_group_name}')

    # test is live only because repo test environment does not have a stdin file pointer
    # ie. "UnsupportedOperation("redirected stdin is pseudofile, has no fileno()")"
    @live_only()
    @ResourceGroupPreparer()
    def test_container_exec(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'echo hello; sleep 15; done\'"'
        restart_policy = 'Never'

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'restart_policy': restart_policy,
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --cpu {cpu} --memory {memory} '
                 '--command-line {command} --restart-policy {restart_policy} ',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test exec
        self.cmd('container exec -g {rg} -n {container_group_name} --exec-command \"ls\"')


    # Test container create with a zone specified
    @ResourceGroupPreparer()
    def test_container_create_with_zone(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        restart_policy = 'Never'
        zone = '1'
        location = "eastus"

        self.kwargs.update({
            'container_group_name': container_group_name,
            'location': location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'restart_policy': restart_policy,
            'zone': zone
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --cpu {cpu} --memory {memory} --zone {zone} '
                 '--command-line {command} --restart-policy {restart_policy} --location {location}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('zones[0]', zone)])

    # Test container with Confidential SKU
    @ResourceGroupPreparer()
    def test_container_create_with_confidential_sku(self, resource_group, resource_group_location):

        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        restart_policy = 'Never'
        location = "northeurope"
        sku="Confidential"
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='

        self.kwargs.update({
            'container_group_name': container_group_name,
            'location': location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'restart_policy': restart_policy,
            'sku': sku,
            'env': env
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --cpu {cpu} --memory {memory} --sku {sku} '
                 '--command-line {command} --restart-policy {restart_policy} --location {location} -e {env} '
                 '--privileged --allow-escalation',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.exists('containers[0].securityContext'),
                         self.check('containers[0].securityContext.privileged', True),
                         self.check('sku', sku),
                         self.exists('confidentialComputeProperties.ccePolicy')])
        # Test show
        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.exists('containers[0].securityContext'),
                         self.check('containers[0].securityContext.privileged', True),
                         self.check('containers[0].securityContext.allowPrivilegeEscalation', True),
                         self.check('sku', sku),
                         self.exists('confidentialComputeProperties.ccePolicy')])

        # Test logs
        self.cmd('container logs -g {rg} -n {container_group_name}')

        # Test delete
        self.cmd('container delete -g {rg} -n {container_group_name} -y',
            checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.check('sku', sku),
                         self.exists('confidentialComputeProperties.ccePolicy')])

    # Test container reuse from standby pool with config maps
    # This test relies on existing container group profile and standby pool profile
    @ResourceGroupPreparer()
    def test_container_reuse_from_standbypool(self, resource_group, resource_group_location):

        container_group_name = self.create_random_name('clicontainer', 16)
        container_group_profile_id = '/subscriptions/da28f5e5-aa45-46fe-90c8-053ca49ab4b5/resourceGroups/azcliresources/providers/Microsoft.ContainerInstance/containerGroupProfiles/testcg'
        container_group_profile_revision = '1'
        standby_pool_profile_id = '/subscriptions/da28f5e5-aa45-46fe-90c8-053ca49ab4b5/resourceGroups/azcliresources/providers/Microsoft.StandbyPool/standbyContainerGroupPools/testpool'
        location = "eastus"
        config_map = 'KEY1=VALUE1 KEY2=VALUE2'
        cpu = 1
        memory = 1
        os_type = 'Linux'
        image = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        
        self.kwargs.update({
            'container_group_name': container_group_name,
            'location': location,
            'container_group_profile_id': container_group_profile_id,
            'container_group_profile_revision': container_group_profile_revision,
            'standby_pool_profile_id': standby_pool_profile_id,
            'config_map': config_map,
            'cpu': cpu,
            'memory': memory,
            'os_type': os_type,
            'image': image
        })

        # Test create
        self.cmd('container create -g {rg} -n {container_group_name} --config-map {config_map} '
                 '--container-group-profile-id {container_group_profile_id} --container-group-profile-revision {container_group_profile_revision} '
                 '--standby-pool-profile-id {standby_pool_profile_id} --location {location} ',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('isCreatedFromStandbyPool','True'),
                         self.check('osType', '{os_type}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].configMap'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])
        
        # Test show
        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('isCreatedFromStandbyPool','True'),
                         self.check('osType', '{os_type}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].configMap'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test delete
        self.cmd('container delete -g {rg} -n {container_group_name} -y',
            checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('isCreatedFromStandbyPool','True'),
                         self.check('osType', '{os_type}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].configMap'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

    # Test create container container-group-profile with image, os type, ip address type, port, cpu,
    # memory, command line and environment variables specified.
    @ResourceGroupPreparer()
    def test_container_group_profile_create(self, resource_group, resource_group_location):
        container_group_profile_name = self.create_random_name('clicgp', 16)
        image = 'alpine:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        port1 = 8000
        port2 = 8001
        ports = '{} {}'.format(port1, port2)
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='
        restart_policy = 'Never'
        secrets = 'secret1=superawesomesecret secret2="nothing to see"'
        secret_path = '/s'
        self.kwargs.update({
            'container_group_profile_name': container_group_profile_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'port1': port1,
            'port2': port2,
            'ports': ports,
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'env': env,
            'restart_policy': restart_policy,
            'secrets': secrets,
            'secrets_mount_path': secret_path
        })

        # Test create
        self.cmd('container container-group-profile create -g {rg} -n {container_group_profile_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --ports {ports} --cpu {cpu} --memory {memory} '
                 '--command-line {command} -e {env} --restart-policy {restart_policy} '
                 '--secrets {secrets} --secrets-mount-path {secrets_mount_path}',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.exists('volumes'),
                         self.check('volumes[0].secret', {})])

        # Test show
        self.cmd('container container-group-profile show -g {rg} -n {container_group_profile_name}',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check('containers[0].resources.requests.memoryInGb', memory)])
        
        # Test show by revision number 
        self.cmd('container container-group-profile show-revision -g {rg} -n {container_group_profile_name} -r 1',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check('containers[0].resources.requests.memoryInGb', memory)])
        
        # Test delete
        self.cmd('container container-group-profile delete -g {rg} -n {container_group_profile_name} -y')
        
    # Test create container container-group-profile with Confidential SKU
    @ResourceGroupPreparer()
    def test_container_group_profile_create_with_confidential_sku(self, resource_group, resource_group_location):

        container_group_profile_name = self.create_random_name('clicgp', 16)
        image = 'alpine:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        cpu = 1
        memory = 1
        restart_policy = 'Never'
        location = "northeurope"
        sku="Confidential"
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='
        cce_policy = "eyJhbGxvd19hbGwiOiB0cnVlLCAiY29udGFpbmVycyI6IHsibGVuZ3RoIjogMCwgImVsZW1lbnRzIjogbnVsbH19"

        self.kwargs.update({
            'container_group_profile_name': container_group_profile_name,
            'location': location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'cpu': cpu,
            'memory': memory,
            'restart_policy': restart_policy,
            'sku': sku,
            'env': env,
            'cce_policy': cce_policy
        })

        # Test create
        self.cmd('container container-group-profile create -g {rg} -n {container_group_profile_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --cpu {cpu} --memory {memory} --sku {sku} '
                 '--restart-policy {restart_policy} --location {location} -e {env} --cce-policy {cce_policy} '
                 '--privileged --allow-escalation',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.exists('containers[0].securityContext'),
                         self.check('containers[0].securityContext.privileged', True),
                         self.check('sku', sku),
                         self.exists('confidentialComputeProperties.ccePolicy')])
        
        # Test show
        self.cmd('container container-group-profile show -g {rg} -n {container_group_profile_name}',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory),
                         self.exists('containers[0].securityContext'),
                         self.check('containers[0].securityContext.privileged', True),
                         self.check('containers[0].securityContext.allowPrivilegeEscalation', True),
                         self.check('sku', sku),
                         self.exists('confidentialComputeProperties.ccePolicy')])

        # Test delete
        self.cmd('container container-group-profile delete -g {rg} -n {container_group_profile_name} -y')
        

    # Test create container container-group-profile with Spot Priority
    @ResourceGroupPreparer()
    def test_container_group_profile_create_spot_priority(self, resource_group, resource_group_location):
        container_group_profile_name = self.create_random_name('clicgp', 16)
        image = 'alpine:latest'
        os_type = 'Linux'
        cpu = 1
        memory = 1
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='
        restart_policy = 'Never'
        priority = 'Spot'
        self.kwargs.update({
            'container_group_profile_name': container_group_profile_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type, 
            'cpu': cpu,
            'memory': memory,
            'env': env,
            'restart_policy': restart_policy,
            'priority' : priority
        })

        # Test create
        self.cmd('container container-group-profile create -g {rg} -n {container_group_profile_name} --image {image} --os-type {os_type} '
                 '--cpu {cpu} --memory {memory} --priority {priority} '
                 '-e {env} --restart-policy {restart_policy}  ',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test show
        self.cmd('container container-group-profile show -g {rg} -n {container_group_profile_name}',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('priority', '{priority}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].environmentVariables'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])

        # Test delete
        self.cmd('container container-group-profile delete -g {rg} -n {container_group_profile_name} -y')

    @ResourceGroupPreparer()
    # Test container container-group-profile create with varied restart policies
    def test_container_group_profile_update(self, resource_group, resource_group_location):
        container_group_profile_name = self.create_random_name('clicgp', 16)
        image = 'alpine:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        port1 = 8000
        port2 = 8001
        ports = '{} {}'.format(port1, port2)
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='
        restart_policy1 = 'Never'
        restart_policy2 = 'OnFailure'
        self.kwargs.update({
            'container_group_profile_name': container_group_profile_name,
            'resource_group_location': resource_group_location,
            'image': image,
            'os_type': os_type,
            'ip_address_type': ip_address_type,
            'port1': port1,
            'port2': port2,
            'ports': ports,
            'cpu': cpu,
            'memory': memory,
            'command': command,
            'env': env,
            'restart_policy1': restart_policy1,
            'restart_policy2': restart_policy2
        })

        # Test create with restart policy Never
        self.cmd('container container-group-profile create -g {rg} -n {container_group_profile_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --ports {ports} --cpu {cpu} --memory {memory} '
                 '--command-line {command} -e {env} --restart-policy {restart_policy1} ',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy1}'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])
        
        # Test create with restart policy OnFailure
        self.cmd('container container-group-profile create -g {rg} -n {container_group_profile_name} --image {image} --os-type {os_type} '
                 '--ip-address {ip_address_type} --ports {ports} --cpu {cpu} --memory {memory} '
                 '--command-line {command} -e {env} --restart-policy {restart_policy2} ',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '2'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy2}'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check(
                             'containers[0].resources.requests.memoryInGb', memory)])
    
        # Test show by revision number 
        self.cmd('container container-group-profile show-revision -g {rg} -n {container_group_profile_name} -r 1',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '1'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy1}'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check('containers[0].resources.requests.memoryInGb', memory)])
        
        self.cmd('container container-group-profile show-revision -g {rg} -n {container_group_profile_name} -r 2',
                 checks=[self.check('name', '{container_group_profile_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('revision', '2'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy2}'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.check(
                             'containers[0].resources.requests.cpu', cpu),
                         self.check('containers[0].resources.requests.memoryInGb', memory)])
        
        # Test delete
        self.cmd('container container-group-profile delete -g {rg} -n {container_group_profile_name} -y')

    
        
    
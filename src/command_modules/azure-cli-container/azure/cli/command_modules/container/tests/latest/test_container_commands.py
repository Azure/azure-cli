# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AzureContainerInstanceScenarioTest(ScenarioTest):
    # Test create container with image, os type, ip address type, port, dns name label, cpu,
    # memory, command line and environment variables specified.
    @ResourceGroupPreparer()
    def test_container_create(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        image = 'alpine:latest'
        os_type = 'Linux'
        ip_address_type = 'Public'
        dns_name_label = container_group_name
        fqdn = '{}.{}.azurecontainer.io'.format(container_group_name, resource_group_location)
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
                         self.check('provisioningState', 'Creating'),
                         self.check('osType', '{os_type}'),
                         self.check('restartPolicy', '{restart_policy}'),
                         self.check('ipAddress.dnsNameLabel', '{container_group_name}'),
                         self.check('ipAddress.fqdn', '{fqdn}'),
                         self.exists('ipAddress.ip'),
                         self.exists('ipAddress.ports'),
                         self.check('ipAddress.ports[0].port', '{port1}'),
                         self.check('ipAddress.ports[1].port', '{port2}'),
                         self.check('containers[0].image', '{image}'),
                         self.exists('containers[0].command'),
                         self.exists('containers[0].environmentVariables'),
                         self.check('containers[0].resources.requests.cpu', cpu),
                         self.check('containers[0].resources.requests.memoryInGb', memory),
                         self.exists('volumes'),
                         self.check('volumes[0].secret', {})])

        # Wait for container to be provisioned
        time.sleep(30)

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
                         self.check('containers[0].resources.requests.cpu', cpu),
                         self.check('containers[0].resources.requests.memoryInGb', memory)])

        # Test list
        self.cmd('container list -g {rg}',
                 checks=[self.check('[0].name', '{container_group_name}'),
                         self.check('[0].location', '{resource_group_location}'),
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
                         self.check('[0].containers[0].resources.requests.cpu', cpu),
                         self.check('[0].containers[0].resources.requests.memoryInGb', memory)])

    # Test create container with azure container registry image.
    # An ACR instance is required to re-record this test with 'nginx:latest' image available in the url.
    # see https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-docker-cli
    # After recording, regenerate the password for the acr instance.
    @ResourceGroupPreparer()
    def test_container_create_with_acr(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        registry_username = 'clitestregistry1'
        registry_server = '{}.azurecr.io'.format(registry_username)
        image = '{}/nginx:latest'.format(registry_server)
        password = '0IS50p79+vNF6Kt7nm33iNn0Q9Ds2T41'

        self.kwargs.update({
            'container_group_name': container_group_name,
            'resource_group_location': resource_group_location,
            'registry_username': registry_username,
            'registry_server': registry_server,
            'image': image,
            'password': password
        })

        self.cmd('container create -g {rg} -n {container_group_name} --image {image} --registry-username {registry_username} --registry-password {password}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Creating'),
                         self.check('osType', 'Linux'),
                         self.check('containers[0].image', '{image}'),
                         self.check('imageRegistryCredentials[0].server', '{registry_server}'),
                         self.check('imageRegistryCredentials[0].username', '{registry_username}'),
                         self.exists('containers[0].resources.requests.cpu'),
                         self.exists('containers[0].resources.requests.memoryInGb')])

        # Wait for container to be provisioned
        time.sleep(60)

        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.check('containers[0].image', '{image}'),
                         self.check('imageRegistryCredentials[0].server', '{registry_server}'),
                         self.check('imageRegistryCredentials[0].username', '{registry_username}'),
                         self.exists('containers[0].resources.requests.cpu'),
                         self.exists('containers[0].resources.requests.memoryInGb')])

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
                         self.check('provisioningState', 'Creating'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].azureFile'),
                         self.check('volumes[0].azureFile.shareName', '{azure_file_volume_share_name}'),
                         self.check('volumes[0].azureFile.storageAccountName', '{azure_file_volume_account_name}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{azure_file_volume_mount_path}')])

        # Wait for container to be provisioned
        time.sleep(60)

        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].azureFile'),
                         self.check('volumes[0].azureFile.shareName', '{azure_file_volume_share_name}'),
                         self.check('volumes[0].azureFile.storageAccountName', '{azure_file_volume_account_name}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{azure_file_volume_mount_path}')])

        # Test create container with git repo volume
    @ResourceGroupPreparer()
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
                         self.check('provisioningState', 'Creating'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].gitRepo'),
                         self.check('volumes[0].gitRepo.repository', '{gitrepo_url}'),
                         self.check('volumes[0].gitRepo.directory', '{gitrepo_dir}'),
                         self.check('volumes[0].gitRepo.revision', '{gitrepo_revision}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{gitrepo_mount_path}')])

        # Wait for container to be provisioned
        time.sleep(60)

        self.cmd('container show -g {rg} -n {container_group_name}',
                 checks=[self.check('name', '{container_group_name}'),
                         self.check('location', '{resource_group_location}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('osType', 'Linux'),
                         self.exists('volumes'),
                         self.exists('volumes[0].gitRepo'),
                         self.check('volumes[0].gitRepo.repository', '{gitrepo_url}'),
                         self.check('volumes[0].gitRepo.directory', '{gitrepo_dir}'),
                         self.check('volumes[0].gitRepo.revision', '{gitrepo_revision}'),
                         self.exists('containers[0].volumeMounts'),
                         self.check('containers[0].volumeMounts[0].mountPath', '{gitrepo_mount_path}')])

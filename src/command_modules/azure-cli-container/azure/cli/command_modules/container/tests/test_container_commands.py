# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, JMESPathCheckExists, ResourceGroupPreparer)


class AzureContainerInstanceScenarioTest(ScenarioTest):
    # Test create container with image, os type, ip address type, port, cpu,
    # memory, command line and environment variables specified.
    @ResourceGroupPreparer()
    def test_container_create(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
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

        create_cmd = 'container create -g {} -n {} --image {} --os-type {} --ip-address {} --ports {} ' \
            '--cpu {} --memory {} --command-line {} -e {} --restart-policy {}'.format(resource_group,
                                                                                      container_group_name,
                                                                                      image,
                                                                                      os_type,
                                                                                      ip_address_type,
                                                                                      ports,
                                                                                      cpu,
                                                                                      memory,
                                                                                      command,
                                                                                      env,
                                                                                      restart_policy)
        # Test create
        self.cmd(create_cmd, checks=[
            JMESPathCheck('name', container_group_name),
            JMESPathCheck('location', resource_group_location),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('osType', os_type),
            JMESPathCheck('restartPolicy', restart_policy),
            JMESPathCheckExists('ipAddress.ip'),
            JMESPathCheckExists('ipAddress.ports'),
            JMESPathCheck('ipAddress.ports[0].port', port1),
            JMESPathCheck('ipAddress.ports[1].port', port2),
            JMESPathCheck('containers[0].image', image),
            JMESPathCheckExists('containers[0].command'),
            JMESPathCheckExists('containers[0].environmentVariables'),
            JMESPathCheck('containers[0].resources.requests.cpu', cpu),
            JMESPathCheck('containers[0].resources.requests.memoryInGb', memory)])

        # Test show
        self.cmd('container show -g {} -n {}'.format(resource_group, container_group_name),
                 checks=[
                     JMESPathCheck('name', container_group_name),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('provisioningState', 'Succeeded'),
                     JMESPathCheck('osType', os_type),
                     JMESPathCheck('restartPolicy', restart_policy),
                     JMESPathCheckExists('ipAddress.ip'),
                     JMESPathCheckExists('ipAddress.ports'),
                     JMESPathCheck('ipAddress.ports[0].port', port1),
                     JMESPathCheck('ipAddress.ports[1].port', port2),
                     JMESPathCheck('containers[0].image', image),
                     JMESPathCheckExists('containers[0].command'),
                     JMESPathCheckExists('containers[0].environmentVariables'),
                     JMESPathCheck('containers[0].resources.requests.cpu', cpu),
                     JMESPathCheck('containers[0].resources.requests.memoryInGb', memory)])

        # Test list
        self.cmd('container list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].name', container_group_name),
            JMESPathCheck('[0].location', resource_group_location),
            JMESPathCheck('[0].provisioningState', 'Succeeded'),
            JMESPathCheck('[0].osType', os_type),
            JMESPathCheck('[0].restartPolicy', restart_policy),
            JMESPathCheckExists('[0].ipAddress.ip'),
            JMESPathCheckExists('[0].ipAddress.ports'),
            JMESPathCheck('[0].ipAddress.ports[0].port', port1),
            JMESPathCheck('[0].ipAddress.ports[1].port', port2),
            JMESPathCheck('[0].containers[0].image', image),
            JMESPathCheckExists('[0].containers[0].command'),
            JMESPathCheckExists('[0].containers[0].environmentVariables'),
            JMESPathCheck('[0].containers[0].resources.requests.cpu', cpu),
            JMESPathCheck('[0].containers[0].resources.requests.memoryInGb', memory)])

    # Test create container with azure container registry image.
    @ResourceGroupPreparer()
    def test_container_create_with_acr(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        registry_username = 'testregistry'
        registry_server = '{}.azurecr.io'.format(registry_username)
        image = '{}/nginx:latest'.format(registry_server)
        password = 'passwordmock'

        self.cmd('container create -g {} -n {} --image {} --registry-password {}'.format(
            resource_group,
            container_group_name,
            image,
            password), checks=[
                JMESPathCheck('name', container_group_name),
                JMESPathCheck('location', resource_group_location),
                JMESPathCheck('provisioningState', 'Succeeded'),
                JMESPathCheck('osType', 'Linux'),
                JMESPathCheck('containers[0].image', image),
                JMESPathCheck('imageRegistryCredentials[0].server', registry_server),
                JMESPathCheck('imageRegistryCredentials[0].username', registry_username),
                JMESPathCheckExists('containers[0].resources.requests.cpu'),
                JMESPathCheckExists('containers[0].resources.requests.memoryInGb')])

    # Test create container with azure file volume
    @ResourceGroupPreparer()
    def test_container_azure_file_volume_mount(self, resource_group, resource_group_location):
        container_group_name = self.create_random_name('clicontainer', 16)
        azure_file_volume_share_name = 'testshare'
        azure_file_volume_account_name = 'ccondemostore1'
        azure_file_volume_account_key = 'mockstorageaccountkey'
        azure_file_volume_mount_path = '/mnt/azfile'

        create_cmd = 'container create -g {} -n {} --image nginx --azure-file-volume-share-name {} ' \
            '--azure-file-volume-account-name {} --azure-file-volume-account-key {} ' \
            '--azure-file-volume-mount-path {}'.format(resource_group,
                                                       container_group_name,
                                                       azure_file_volume_share_name,
                                                       azure_file_volume_account_name,
                                                       azure_file_volume_account_key,
                                                       azure_file_volume_mount_path)

        self.cmd(create_cmd, checks=[
            JMESPathCheck('name', container_group_name),
            JMESPathCheck('location', resource_group_location),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('osType', 'Linux'),
            JMESPathCheckExists('volumes'),
            JMESPathCheckExists('volumes[0].azureFile'),
            JMESPathCheck('volumes[0].azureFile.shareName', azure_file_volume_share_name),
            JMESPathCheck('volumes[0].azureFile.storageAccountName', azure_file_volume_account_name),
            JMESPathCheckExists('containers[0].volumeMounts'),
            JMESPathCheck('containers[0].volumeMounts[0].mountPath', azure_file_volume_mount_path)])

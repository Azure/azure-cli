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
        port = 8080
        cpu = 1
        memory = 1
        command = '"/bin/sh -c \'while true; do echo hello; sleep 20; done\'"'
        env = 'KEY1=VALUE1 KEY2=FOO=BAR='

        create_cmd = 'container create -g {} -n {} --image {} --os-type {} --ip-address {} --port {} ' \
            '--cpu {} --memory {} --command-line {} -e {}'.format(resource_group,
                                                                  container_group_name,
                                                                  image,
                                                                  os_type,
                                                                  ip_address_type,
                                                                  port,
                                                                  cpu,
                                                                  memory,
                                                                  command,
                                                                  env)
        # Test create
        self.cmd(create_cmd, checks=[
            JMESPathCheck('name', container_group_name),
            JMESPathCheck('location', resource_group_location),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('osType', os_type),
            JMESPathCheckExists('ipAddress.ip'),
            JMESPathCheckExists('ipAddress.ports'),
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
                     JMESPathCheckExists('ipAddress.ip'),
                     JMESPathCheckExists('ipAddress.ports'),
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
            JMESPathCheckExists('[0].ipAddress.ip'),
            JMESPathCheckExists('[0].ipAddress.ports'),
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

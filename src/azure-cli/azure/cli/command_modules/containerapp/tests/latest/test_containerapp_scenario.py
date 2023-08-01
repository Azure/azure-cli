# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
from unittest import mock
import time
import unittest
from azext_containerapp.custom import containerapp_ssh

from azure.cli.testsdk.reverse_dependency import get_dummy_cli
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only)
from knack.util import CLIError

from azext_containerapp.tests.latest.common import TEST_LOCATION

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ContainerappScenarioTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-e2e-env', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))

        # Ensure environment is completed
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)

        # Create basic Container App with default image
        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, containerapp_name, env_name), checks=[
            JMESPathCheck('name', containerapp_name)
        ])

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, containerapp_name), checks=[
            JMESPathCheck('name', containerapp_name),
        ])

        self.cmd('containerapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', containerapp_name),
        ])

        # Create Container App with image, resource and replica limits
        create_string = "containerapp create -g {} -n {} --environment {} --image nginx --cpu 0.5 --memory 1.0Gi --min-replicas 2 --max-replicas 4".format(resource_group, containerapp_name, env_name)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.template.containers[0].image', 'nginx'),
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.5'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1Gi'),
            JMESPathCheck('properties.template.scale.minReplicas', '2'),
            JMESPathCheck('properties.template.scale.maxReplicas', '4')
        ])

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 8080'.format(resource_group, containerapp_name, env_name), checks=[
            JMESPathCheck('properties.configuration.ingress.external', True),
            JMESPathCheck('properties.configuration.ingress.targetPort', 8080)
        ])

        # Container App with ingress should fail unless target port is specified
        with self.assertRaises(CLIError):
            self.cmd('containerapp create -g {} -n {} --environment {} --ingress external'.format(resource_group, containerapp_name, env_name))

        # Create Container App with secrets and environment variables
        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        create_string = 'containerapp create -g {} -n {} --environment {} --secrets mysecret=secretvalue1 anothersecret="secret value 2" --env-vars GREETING="Hello, world" SECRETENV=secretref:anothersecret'.format(
            resource_group, containerapp_name, env_name)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers[0].env)', 2),
            JMESPathCheck('length(properties.configuration.secrets)', 2)
        ])


    # TODO rename
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_container_acr(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-e2e-env', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))

        # Ensure environment is completed
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        registry_name = self.create_random_name(prefix='containerapp', length=24)

        # Create ACR
        acr = self.cmd('acr create -g {} -n {} --sku Basic --admin-enabled'.format(resource_group, registry_name)).get_output_in_json()
        registry_server = acr["loginServer"]

        acr_credentials = self.cmd('acr credential show -g {} -n {}'.format(resource_group, registry_name)).get_output_in_json()
        registry_username = acr_credentials["username"]
        registry_password = acr_credentials["passwords"][0]["value"]

        # Create Container App with ACR
        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        create_string = 'containerapp create -g {} -n {} --environment {} --registry-username {} --registry-server {} --registry-password {}'.format(
            resource_group, containerapp_name, env_name, registry_username, registry_server, registry_password)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.registries[0].server', registry_server),
            JMESPathCheck('properties.configuration.registries[0].username', registry_username),
            JMESPathCheck('length(properties.configuration.secrets)', 1),
        ])


    # TODO rename
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_update(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-e2e-env', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))

        # Ensure environment is completed
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        # Create basic Container App with default image
        containerapp_name = self.create_random_name(prefix='containerapp-update', length=24)

        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, containerapp_name, env_name), checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers)', 1),
            JMESPathCheck('properties.template.containers[0].name', containerapp_name)
        ])

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, containerapp_name), checks=[
            JMESPathCheck('name', containerapp_name),
        ])

        self.cmd('containerapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', containerapp_name),
        ])

        # Create Container App with image, resource and replica limits
        create_string = "containerapp create -g {} -n {} --environment {} --image nginx --cpu 0.5 --memory 1.0Gi --min-replicas 2 --max-replicas 4".format(resource_group, containerapp_name, env_name)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.template.containers[0].image', 'nginx'),
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.5'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1Gi'),
            JMESPathCheck('properties.template.scale.minReplicas', '2'),
            JMESPathCheck('properties.template.scale.maxReplicas', '4')
        ])

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 8080'.format(resource_group, containerapp_name, env_name), checks=[
            JMESPathCheck('properties.configuration.ingress.external', True),
            JMESPathCheck('properties.configuration.ingress.targetPort', 8080)
        ])

        # Container App with ingress should fail unless target port is specified
        with self.assertRaises(CLIError):
            self.cmd('containerapp create -g {} -n {} --environment {} --ingress external'.format(resource_group, containerapp_name, env_name))

        # Create Container App with secrets and environment variables
        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        create_string = 'containerapp create -g {} -n {} --environment {} --secrets mysecret=secretvalue1 anothersecret="secret value 2" --env-vars GREETING="Hello, world" SECRETENV=secretref:anothersecret'.format(
            resource_group, containerapp_name, env_name)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers[0].env)', 2),
            JMESPathCheck('length(properties.configuration.secrets)', 2)
        ])


    # TODO rename
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_container_acr(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-e2e-env', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))

        # Ensure environment is completed
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        registry_name = self.create_random_name(prefix='containerapp', length=24)

        # Create ACR
        acr = self.cmd('acr create -g {} -n {} --sku Basic --admin-enabled'.format(resource_group, registry_name)).get_output_in_json()
        registry_server = acr["loginServer"]

        acr_credentials = self.cmd('acr credential show -g {} -n {}'.format(resource_group, registry_name)).get_output_in_json()
        registry_username = acr_credentials["username"]
        registry_password = acr_credentials["passwords"][0]["value"]

        # Create Container App with ACR
        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        create_string = 'containerapp create -g {} -n {} --environment {} --registry-username {} --registry-server {} --registry-password {}'.format(
            resource_group, containerapp_name, env_name, registry_username, registry_server, registry_password)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.registries[0].server', registry_server),
            JMESPathCheck('properties.configuration.registries[0].username', registry_username),
            JMESPathCheck('length(properties.configuration.secrets)', 1),
        ])

        # Update Container App with ACR
        update_string = 'containerapp update -g {} -n {} --min-replicas 0 --max-replicas 1 --set-env-vars testenv=testing'.format(
            resource_group, containerapp_name)
        self.cmd(update_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.registries[0].server', registry_server),
            JMESPathCheck('properties.configuration.registries[0].username', registry_username),
            JMESPathCheck('length(properties.configuration.secrets)', 1),
            JMESPathCheck('properties.template.scale.minReplicas', '0'),
            JMESPathCheck('properties.template.scale.maxReplicas', '1'),
            JMESPathCheck('length(properties.template.containers[0].env)', 1),
        ])

        # Add secrets to Container App with ACR
        containerapp_secret = self.cmd('containerapp secret list -g {} -n {}'.format(resource_group, containerapp_name)).get_output_in_json()
        secret_name = containerapp_secret[0]["name"]
        secret_string = 'containerapp secret set -g {} -n {} --secrets newsecret=test'.format(resource_group, containerapp_name)
        self.cmd(secret_string, checks=[
            JMESPathCheck('length(@)', 2),
        ])

        with self.assertRaises(CLIError):
            # Removing ACR password should fail since it is needed for ACR
            self.cmd('containerapp secret remove -g {} -n {} --secret-names {}'.format(resource_group, containerapp_name, secret_name))

    # TODO rename
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_update_containers(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-e2e-env', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))

        # Ensure environment is completed
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        # Create basic Container App with default image
        containerapp_name = self.create_random_name(prefix='containerapp-update', length=24)
        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, containerapp_name, env_name), checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers)', 1),
            JMESPathCheck('properties.template.containers[0].name', containerapp_name)
        ])

        # Update existing Container App that has a single container

        update_string = 'containerapp update -g {} -n {} --image {} --cpu 0.5 --memory 1.0Gi --args mycommand mycommand2 --command "mycommand" --revision-suffix suffix --min-replicas 2 --max-replicas 34'.format(
            resource_group, containerapp_name, 'nginx')
        self.cmd(update_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers)', 1),
            JMESPathCheck('properties.template.containers[0].name', containerapp_name),
            JMESPathCheck('properties.template.containers[0].image', 'nginx'),
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.5'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1Gi'),
            JMESPathCheck('properties.template.scale.minReplicas', '2'),
            JMESPathCheck('properties.template.scale.maxReplicas', '34'),
            JMESPathCheck('properties.template.containers[0].command[0]', "mycommand"),
            JMESPathCheck('length(properties.template.containers[0].args)', 2)
        ])

        # Add new container to existing Container App
        update_string = 'containerapp update -g {} -n {} --container-name {} --image {}'.format(
            resource_group, containerapp_name, "newcontainer", "nginx")
        self.cmd(update_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers)', 2)
        ])

        # Updating container properties in a Container App with multiple containers, without providing container name should error
        update_string = 'containerapp update -g {} -n {} --cpu {} --memory {}'.format(
            resource_group, containerapp_name, '1.0', '2.0Gi')
        with self.assertRaises(CLIError):
            self.cmd(update_string)

        # Updating container properties in a Container App with multiple containers, should work when container name provided
        update_string = 'containerapp update -g {} -n {} --container-name {} --cpu {} --memory {}'.format(
            resource_group, containerapp_name, 'newcontainer', '0.75', '1.5Gi')
        self.cmd(update_string)

        update_string = 'containerapp update -g {} -n {} --container-name {} --cpu {} --memory {}'.format(
            resource_group, containerapp_name, containerapp_name, '0.75', '1.5Gi')
        self.cmd(update_string, checks=[
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.75'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1.5Gi'),
            JMESPathCheck('properties.template.containers[1].resources.cpu', '0.75'),
            JMESPathCheck('properties.template.containers[1].resources.memory', '1.5Gi'),
        ])

    # TODO fix and enable
    @unittest.skip("API only on stage currently")
    @live_only()  # VCR.py can't seem to handle websockets (only --live works)
    # @ResourceGroupPreparer(location="centraluseuap")
    @mock.patch("azext_containerapp._ssh_utils._resize_terminal")
    @mock.patch("sys.stdin")
    def test_containerapp_ssh(self, resource_group=None, *args):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        # containerapp_name = self.create_random_name(prefix='capp', length=24)
        # env_name = self.create_random_name(prefix='env', length=24)

        # self.cmd(f'containerapp env create -g {resource_group} -n {env_name}')
        # self.cmd(f'containerapp create -g {resource_group} -n {containerapp_name} --environment {env_name} --min-replicas 1 --ingress external')

        # TODO remove hardcoded app info (currently the SSH feature is only enabled in stage)
        # these are only in my sub so they won't work on the CI / other people's machines
        containerapp_name = "stage"
        resource_group = "sca"

        stdout_buff = []

        def mock_print(*args, end="\n", **kwargs):
            out = " ".join([str(a) for a in args])
            if not stdout_buff:
                stdout_buff.append(out)
            elif end != "\n":
                stdout_buff[-1] = f"{stdout_buff[-1]}{out}"
            else:
                stdout_buff.append(out)

        commands = "\n".join(["whoami", "pwd", "ls -l | grep index.js", "exit\n"])
        expected_output = ["root", "/usr/src/app", "-rw-r--r--    1 root     root           267 Oct 15 00:21 index.js"]

        idx = [0]
        def mock_getch():
            ch = commands[idx[0]].encode("utf-8")
            idx[0] = (idx[0] + 1) % len(commands)
            return ch

        cmd = mock.MagicMock()
        cmd.cli_ctx = get_dummy_cli()
        from azext_containerapp._validators import validate_ssh
        from azext_containerapp.custom import containerapp_ssh

        class Namespace: pass
        namespace = Namespace()
        setattr(namespace, "name", containerapp_name)
        setattr(namespace, "resource_group_name", resource_group)
        setattr(namespace, "revision", None)
        setattr(namespace, "replica", None)
        setattr(namespace, "container", None)

        validate_ssh(cmd=cmd, namespace=namespace)  # needed to set values for container, replica, revision

        mock_lib = "tty.setcbreak"
        if platform.system() == "Windows":
            mock_lib = "azext_containerapp._ssh_utils.enable_vt_mode"

        with mock.patch("builtins.print", side_effect=mock_print), mock.patch(mock_lib):
            with mock.patch("azext_containerapp._ssh_utils._getch_unix", side_effect=mock_getch), mock.patch("azext_containerapp._ssh_utils._getch_windows", side_effect=mock_getch):
                containerapp_ssh(cmd=cmd, resource_group_name=namespace.resource_group_name, name=namespace.name,
                                    container=namespace.container, revision=namespace.revision, replica=namespace.replica, startup_command="sh")
        for line in expected_output:
            self.assertIn(line, expected_output)

    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_logstream(self, resource_group):
        containerapp_name = self.create_random_name(prefix='capp', length=24)
        env_name = self.create_random_name(prefix='env', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        self.cmd(f'containerapp create -g {resource_group} -n {containerapp_name} --environment {env_name} --min-replicas 1 --ingress external --target-port 80')

        self.cmd(f'containerapp logs show -n {containerapp_name} -g {resource_group}')

    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_eventstream(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        containerapp_name = self.create_random_name(prefix='capp', length=24)
        env_name = self.create_random_name(prefix='env', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        self.cmd(f'containerapp create -g {resource_group} -n {containerapp_name} --environment {env_name} --min-replicas 1 --ingress external --target-port 80')

        self.cmd(f'containerapp logs show -n {containerapp_name} -g {resource_group} --type system')
        self.cmd(f'containerapp env logs show -n {env_name} -g {resource_group}')

    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_registry_msi(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        logs = self.create_random_name(prefix='logs', length=24)
        app = self.create_random_name(prefix='app', length=24)
        acr = self.create_random_name(prefix='acr', length=24)

        logs_id = self.cmd(f"monitor log-analytics workspace create -g {resource_group} -n {logs} -l eastus").get_output_in_json()["customerId"]
        logs_key = self.cmd(f'monitor log-analytics workspace get-shared-keys -g {resource_group} -n {logs}').get_output_in_json()["primarySharedKey"]

        self.cmd(f'containerapp env create -g {resource_group} -n {env} --logs-workspace-id {logs_id} --logs-workspace-key {logs_key}')

        containerapp_env = self.cmd(f'containerapp env show -g {resource_group} -n {env}').get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd(f'containerapp env show -g {resource_group} -n {env}').get_output_in_json()

        self.cmd(f'containerapp create -g {resource_group} -n {app} --environment {env} --min-replicas 1 --ingress external --target-port 80')
        self.cmd(f'acr create -g {resource_group} -n {acr} --sku basic --admin-enabled')
        # self.cmd(f'acr credential renew -n {acr} ')
        self.cmd(f'containerapp registry set --server {acr}.azurecr.io -g {resource_group} -n {app}')
        app_data = self.cmd(f'containerapp show -g {resource_group} -n {app}').get_output_in_json()
        self.assertEqual(app_data["properties"]["configuration"]["registries"][0].get("server"), f'{acr}.azurecr.io')
        self.assertIsNotNone(app_data["properties"]["configuration"]["registries"][0].get("passwordSecretRef"))
        self.assertIsNotNone(app_data["properties"]["configuration"]["registries"][0].get("username"))
        self.assertEqual(app_data["properties"]["configuration"]["registries"][0].get("identity"), "")

        self.cmd(f'containerapp registry set --server {acr}.azurecr.io -g {resource_group} -n {app} --identity system')
        app_data = self.cmd(f'containerapp show -g {resource_group} -n {app}').get_output_in_json()
        self.assertEqual(app_data["properties"]["configuration"]["registries"][0].get("server"), f'{acr}.azurecr.io')
        self.assertEqual(app_data["properties"]["configuration"]["registries"][0].get("passwordSecretRef"), "")
        self.assertEqual(app_data["properties"]["configuration"]["registries"][0].get("username"), "")
        self.assertEqual(app_data["properties"]["configuration"]["registries"][0].get("identity"), "system")

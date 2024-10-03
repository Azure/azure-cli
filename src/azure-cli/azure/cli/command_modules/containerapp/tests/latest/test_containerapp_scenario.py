# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
from unittest import mock
import time
import unittest

from msrestazure.tools import parse_resource_id

from azure.cli.command_modules.containerapp.custom import containerapp_ssh
from azure.cli.command_modules.containerapp.tests.latest.utils import create_containerapp_env, \
    prepare_containerapp_env_for_app_e2e_tests

from azure.cli.testsdk.reverse_dependency import get_dummy_cli
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, StringCheck, live_only,
                               JMESPathCheckNotExists, LogAnalyticsWorkspacePreparer)
from knack.util import CLIError

from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION, write_test_file, \
    clean_up_test_file

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerappScenarioTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = prepare_containerapp_env_for_app_e2e_tests(self)

        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)

        # Create basic Container App with default image
        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, containerapp_name, env), checks=[
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
        create_string = "containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest --cpu 0.5 --memory 1.0Gi --min-replicas 2 --max-replicas 4".format(resource_group, containerapp_name, env)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.template.containers[0].image', 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'),
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.5'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1Gi'),
            JMESPathCheck('properties.template.scale.minReplicas', '2'),
            JMESPathCheck('properties.template.scale.maxReplicas', '4')
        ])

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 8080'.format(resource_group, containerapp_name, env), checks=[
            JMESPathCheck('properties.configuration.ingress.external', True),
            JMESPathCheck('properties.configuration.ingress.targetPort', 8080)
        ])

        # target port is optional
        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external'.format(resource_group, containerapp_name, env), checks=[
            JMESPathCheck('properties.configuration.ingress.external', True),
            JMESPathCheck('properties.configuration.ingress.targetPort', 0)
        ])

        # Create Container App with secrets and environment variables
        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        create_string = 'containerapp create -g {} -n {} --environment {} --secrets mysecret=secretvalue1 anothersecret="secret value 2" --env-vars GREETING="Hello, world" SECRETENV=secretref:anothersecret'.format(
            resource_group, containerapp_name, env)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers[0].env)', 2),
            JMESPathCheck('length(properties.configuration.secrets)', 2)
        ])

    @live_only()  # Pass lively, But failed in playback mode with error: WebSocketBadStatusException: Handshake status 401 Unauthorized
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_exec(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = prepare_containerapp_env_for_app_e2e_tests(self)

        containerapp_name = self.create_random_name(prefix='containerapp-e2e1', length=24)
        # create an app with ingress is None
        app = self.cmd(f'containerapp create -g {resource_group} -n {containerapp_name} --environment {env}', checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.ingress', None),

        ]).get_output_in_json()

        self.containerapp_exec_test_helper(resource_group, containerapp_name, app["properties"]["latestRevisionName"])

        #  Test external App
        external_containerapp_name = self.create_random_name(prefix='containerapp-e2e2', length=24)
        # create an app with ingress is None
        external_containerapp = self.cmd(f'containerapp create -g {resource_group} -n {external_containerapp_name} --environment {env} --ingress external --target-port 8080', checks=[
            JMESPathCheck('name', external_containerapp_name),
            JMESPathCheck('properties.configuration.ingress.external', True),
            JMESPathCheck('properties.configuration.ingress.targetPort', 8080)
        ]).get_output_in_json()

        self.containerapp_exec_test_helper(resource_group, external_containerapp_name, external_containerapp["properties"]["latestRevisionName"])

        #  Test internal App
        # update ingress to internal
        self.cmd(
            f'containerapp ingress update -g {resource_group} -n {external_containerapp_name} --type internal',
            checks=[
                JMESPathCheck('external', False),
            ]).get_output_in_json()
        internal_containerapp = self.cmd(f'containerapp show -g {resource_group} -n {external_containerapp_name}').get_output_in_json()
        self.containerapp_exec_test_helper(resource_group, external_containerapp_name, internal_containerapp["properties"]["latestRevisionName"])

    def containerapp_exec_test_helper(self, resource_group, containerapp_name, latest_revision_name):
        self.cmd(f'containerapp exec -g {resource_group} -n {containerapp_name}')

        self.cmd(f'containerapp exec -g {resource_group} -n {containerapp_name} --command ls')

        replica_list = self.cmd(
            f'containerapp replica list -g {resource_group} -n {containerapp_name} --revision {latest_revision_name}',
            expect_failure=False).get_output_in_json()

        self.cmd(
            f'containerapp exec -g {resource_group} -n {containerapp_name} --replica {replica_list[0]["name"]} --revision {latest_revision_name} --command ls',
            expect_failure=False)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_container_acr(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

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
            resource_group, containerapp_name, env_id, registry_username, registry_server, registry_password)
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
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        # Create basic Container App with default image
        containerapp_name = self.create_random_name(prefix='containerapp-update', length=24)

        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, containerapp_name, env_id), checks=[
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
        create_string = "containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest --cpu 0.5 --memory 1.0Gi --min-replicas 2 --max-replicas 4".format(resource_group, containerapp_name, env_id)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.template.containers[0].image', 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'),
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.5'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1Gi'),
            JMESPathCheck('properties.template.scale.minReplicas', '2'),
            JMESPathCheck('properties.template.scale.maxReplicas', '4')
        ])

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 8080'.format(resource_group, containerapp_name, env_id), checks=[
            JMESPathCheck('properties.configuration.ingress.external', True),
            JMESPathCheck('properties.configuration.ingress.targetPort', 8080)
        ])

        # target port is optional
        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external'.format(resource_group, containerapp_name, env_id), checks=[
            JMESPathCheck('properties.configuration.ingress.external', True),
            JMESPathCheck('properties.configuration.ingress.targetPort', 0)
        ])

        self.cmd('containerapp ingress disable -g {} -n {}'.format(resource_group, containerapp_name), checks=[
            StringCheck('')
        ])

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, containerapp_name), checks=[
            JMESPathCheckNotExists('properties.configuration.ingress'),
        ])

        self.cmd('containerapp ingress enable -g {} -n {} --type external --target-port 8080'.format(resource_group, containerapp_name), checks=[
            JMESPathCheck('external', True),
            JMESPathCheck('targetPort', 8080)
        ])

        self.cmd('containerapp ingress disable -g {} -n {}'.format(resource_group, containerapp_name), checks=[
            StringCheck('')
        ])

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, containerapp_name), checks=[
            JMESPathCheckNotExists('properties.configuration.ingress'),
        ])

        self.cmd('containerapp ingress enable -g {} -n {} --type external'.format(resource_group, containerapp_name), checks=[
            JMESPathCheck('external', True),
            JMESPathCheck('targetPort', 0)
        ])

        # Create Container App with secrets and environment variables
        containerapp_name = self.create_random_name(prefix='containerapp-e2e', length=24)
        create_string = 'containerapp create -g {} -n {} --environment {} --secrets mysecret=secretvalue1 anothersecret="secret value 2" --env-vars GREETING="Hello, world" SECRETENV=secretref:anothersecret'.format(
            resource_group, containerapp_name, env_id)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('length(properties.template.containers[0].env)', 2),
            JMESPathCheck('length(properties.configuration.secrets)', 2)
        ])


    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_container_acr_env_var(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = prepare_containerapp_env_for_app_e2e_tests(self)

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
            resource_group, containerapp_name, env, registry_username, registry_server, registry_password)
        self.cmd(create_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.registries[0].server', registry_server),
            JMESPathCheck('properties.configuration.registries[0].username', registry_username),
            JMESPathCheck('length(properties.configuration.secrets)', 1),
        ])

        # Update Container App with ACR, set --min-replicas 1
        update_string = 'containerapp update -g {} -n {} --min-replicas 1 --max-replicas 1 --set-env-vars testenv=testing'.format(
            resource_group, containerapp_name)
        self.cmd(update_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.registries[0].server', registry_server),
            JMESPathCheck('properties.configuration.registries[0].username', registry_username),
            JMESPathCheck('length(properties.configuration.secrets)', 1),
            JMESPathCheck('properties.template.scale.minReplicas', '1'),
            JMESPathCheck('properties.template.scale.maxReplicas', '1'),
            JMESPathCheck('length(properties.template.containers[0].env)', 1),
            JMESPathCheck('properties.template.containers[0].env[0].name', "testenv"),
            JMESPathCheck('properties.template.containers[0].env[0].value', None),
        ])

        # Add secrets to Container App with ACR
        containerapp_secret = self.cmd('containerapp secret list -g {} -n {}'.format(resource_group, containerapp_name)).get_output_in_json()
        secret_name = containerapp_secret[0]["name"]
        secret_string = 'containerapp secret set -g {} -n {} --secrets newsecret=test'.format(resource_group, containerapp_name)
        self.cmd(secret_string, checks=[
            JMESPathCheck('length(@)', 2),
        ])

        self.cmd('containerapp secret show -g {} -n {} --secret-name {}'.format(resource_group, containerapp_name, secret_name), checks=[
            JMESPathCheck('name', secret_name),
        ])

        with self.assertRaises(CLIError):
            # Removing ACR password should fail since it is needed for ACR
            self.cmd('containerapp secret remove -g {} -n {} --secret-names {}'.format(resource_group, containerapp_name, secret_name))

        # Update Container App with ACR, --min-replicas 0
        update_string = 'containerapp update -g {} -n {} --min-replicas 0 --max-replicas 1 --replace-env-vars testenv=testing2'.format(
            resource_group, containerapp_name)
        self.cmd(update_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.registries[0].server', registry_server),
            JMESPathCheck('properties.configuration.registries[0].username', registry_username),
            JMESPathCheck('properties.template.scale.minReplicas', '0'),
            JMESPathCheck('properties.template.scale.maxReplicas', '1'),
            JMESPathCheck('length(properties.template.containers[0].env)', 1),
            JMESPathCheck('properties.template.containers[0].env[0].name', "testenv"),
            JMESPathCheck('properties.template.containers[0].env[0].value', None),
        ])
        update_string = 'containerapp update -g {} -n {} --min-replicas 0 --max-replicas 1 --remove-env-vars testenv --remove-all-env-vars'.format(resource_group, containerapp_name)
        self.cmd(update_string, checks=[
            JMESPathCheck('name', containerapp_name),
            JMESPathCheck('properties.configuration.registries[0].server', registry_server),
            JMESPathCheck('properties.configuration.registries[0].username', registry_username),
            JMESPathCheck('properties.template.scale.minReplicas', '0'),
            JMESPathCheck('properties.template.scale.maxReplicas', '1'),
            JMESPathCheck('properties.template.containers[0].env', None),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_containerapp_update_containers(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = prepare_containerapp_env_for_app_e2e_tests(self)

        # Create basic Container App with default image
        containerapp_name = self.create_random_name(prefix='containerapp-update', length=24)
        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, containerapp_name, env), checks=[
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
    @mock.patch("azure.cli.command_modules.containerapp._ssh_utils._resize_terminal")
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
        from azure.cli.command_modules.containerapp._validators import validate_ssh
        from azure.cli.command_modules.containerapp.custom import containerapp_ssh

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
            mock_lib = "azure.cli.command_modules.containerapp._ssh_utils.enable_vt_mode"

        with mock.patch("builtins.print", side_effect=mock_print), mock.patch(mock_lib):
            with mock.patch("azure.cli.command_modules.containerapp._ssh_utils._getch_unix", side_effect=mock_getch), mock.patch("azure.cli.command_modules.containerapp._ssh_utils._getch_windows", side_effect=mock_getch):
                containerapp_ssh(cmd=cmd, resource_group_name=namespace.resource_group_name, name=namespace.name,
                                    container=namespace.container, revision=namespace.revision, replica=namespace.replica, startup_command="sh")
        for line in expected_output:
            self.assertIn(line, expected_output)

    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_logstream(self, resource_group):
        containerapp_name = self.create_random_name(prefix='capp', length=24)
        env = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(f'containerapp create -g {resource_group} -n {containerapp_name} --environment {env} --min-replicas 1 --ingress external --target-port 80')

        self.cmd(f'containerapp logs show -n {containerapp_name} -g {resource_group} --follow false --format json --tail 10', expect_failure=False)

    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_eventstream(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        containerapp_name = self.create_random_name(prefix='capp', length=24)
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)
        env_rg = parse_resource_id(env_id).get('resource_group')
        env_name = parse_resource_id(env_id).get('name')

        self.cmd(f'containerapp create -g {resource_group} -n {containerapp_name} --environment {env_id} --min-replicas 1 --ingress external --target-port 80')

        self.cmd(f'containerapp logs show -n {containerapp_name} -g {resource_group} --type system')
        self.cmd(f'containerapp env logs show -n {env_name} -g {env_rg} --tail 15 --follow false')

    @ResourceGroupPreparer(location="northeurope")
    @AllowLargeResponse()
    def test_containerapp_registry_msi(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        app = self.create_random_name(prefix='app', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        env = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(f'containerapp create -g {resource_group} -n {app} --environment {env} --min-replicas 1 --ingress external --target-port 80')
        self.cmd(f'acr create -g {resource_group} -n {acr} --sku basic --admin-enabled')
        # self.cmd(f'acr credential renew -n {acr} ')
        self.cmd(f'containerapp registry set --server {acr}.azurecr.io -g {resource_group} -n {app}')
        registry_list = self.cmd(f'containerapp registry list -g {resource_group} -n {app}', checks=[
            JMESPathCheck('length(@)', 1),
        ]).get_output_in_json()

        self.cmd(f'containerapp registry show -g {resource_group} -n {app} --server {registry_list[0]["server"]}', checks=[
            JMESPathCheck('server', acr+'.azurecr.io'),
        ])

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

        self.cmd(f'containerapp registry remove -g {resource_group} -n {app} --server {registry_list[0]["server"]}',expect_failure=False)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_containerapp_create_with_environment_id(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env1 = self.create_random_name(prefix='env1', length=24)
        env2 = self.create_random_name(prefix='env2', length=24)

        app = self.create_random_name(prefix='yaml1', length=24)

        create_containerapp_env(self, env1, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)
        containerapp_env1 = self.cmd(
            'containerapp env show -g {} -n {}'.format(resource_group, env1)).get_output_in_json()

        create_containerapp_env(self, env2, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)
        containerapp_env2 = self.cmd(
            'containerapp env show -g {} -n {}'.format(resource_group, env2)).get_output_in_json()
        # test `az containerapp up` with --environment
        image = 'mcr.microsoft.com/azuredocs/aks-helloworld:v1'
        ca_name = self.create_random_name(prefix='containerapp', length=24)
        self.cmd('containerapp up -g {} -n {} --environment {} --image {}'.format(resource_group, ca_name, env2, image), expect_failure=False)
        self.cmd(f'containerapp show -g {resource_group} -n {ca_name}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.environmentId", containerapp_env2["id"]),
            JMESPathCheck('properties.template.containers[0].image', image),
        ])
        # test `az containerapp up` for existing containerapp without --environment
        image2 = 'mcr.microsoft.com/k8se/quickstart:latest'
        self.cmd('containerapp up -g {} -n {} --image {}'.format(resource_group, ca_name, image2), expect_failure=False)
        self.cmd(f'containerapp show -g {resource_group} -n {ca_name}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.environmentId", containerapp_env2["id"]),
            JMESPathCheck('properties.template.containers[0].image', image2),
        ])

        user_identity_name = self.create_random_name(prefix='containerapp-user', length=24)
        user_identity = self.cmd(
            'identity create -g {} -n {}'.format(resource_group, user_identity_name)).get_output_in_json()
        user_identity_id = user_identity['id']

        # the value in --yaml is used, warning for different value in --environmentId
        containerapp_yaml_text = f"""
                                    location: {TEST_LOCATION}
                                    type: Microsoft.App/containerApps
                                    tags:
                                        tagname: value
                                    properties:
                                      environmentId: {containerapp_env1["id"]}
                                      configuration:
                                        activeRevisionsMode: Multiple
                                        ingress:
                                          external: false
                                          allowInsecure: false
                                          targetPort: 80
                                          traffic:
                                            - latestRevision: true
                                              weight: 100
                                          transport: Auto
                                          ipSecurityRestrictions:
                                            - name: name
                                              ipAddressRange: "1.1.1.1/10"
                                              action: "Allow"
                                      template:
                                        revisionSuffix: myrevision
                                        terminationGracePeriodSeconds: 90
                                        containers:
                                          - image: nginx
                                            name: nginx
                                            env:
                                              - name: HTTP_PORT
                                                value: 80
                                            command:
                                              - npm
                                              - start
                                            resources:
                                              cpu: 0.5
                                              memory: 1Gi
                                        scale:
                                          minReplicas: 1
                                          maxReplicas: 3
                                          rules:
                                          - http:
                                              auth:
                                              - secretRef: secretref
                                                triggerParameter: trigger
                                              metadata:
                                                concurrentRequests: '50'
                                                key: value
                                            name: http-scale-rule
                                    identity:
                                      type: UserAssigned
                                      userAssignedIdentities:
                                        {user_identity_id}: {{}}
                                    """
        containerapp_file_name = f"{self._testMethodName}_containerapp.yml"

        write_test_file(containerapp_file_name, containerapp_yaml_text)
        self.cmd(
            f'containerapp create -n {app} -g {resource_group} --environment {env2} --yaml {containerapp_file_name}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.environmentId", containerapp_env1["id"]),
            JMESPathCheck("properties.configuration.ingress.external", False),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].name", "name"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].ipAddressRange",
                          "1.1.1.1/10"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].action", "Allow"),
            JMESPathCheck("properties.environmentId", containerapp_env1["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision"),
            JMESPathCheck("properties.template.terminationGracePeriodSeconds", 90),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3),
            JMESPathCheck("properties.template.scale.rules[0].name", "http-scale-rule"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.concurrentRequests", "50"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.key", "value"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].triggerParameter", "trigger"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].secretRef", "secretref"),
        ])

        containerapp_yaml_text = f"""
                                            location: {TEST_LOCATION}
                                            type: Microsoft.App/containerApps
                                            tags:
                                                tagname: value
                                            properties:
                                              configuration:
                                                activeRevisionsMode: Multiple
                                                ingress:
                                                  external: false
                                                  allowInsecure: false
                                                  targetPort: 80
                                                  traffic:
                                                    - latestRevision: true
                                                      weight: 100
                                                  transport: Auto
                                                  ipSecurityRestrictions:
                                                    - name: name
                                                      ipAddressRange: "1.1.1.1/10"
                                                      action: "Allow"
                                              template:
                                                revisionSuffix: myrevision
                                                terminationGracePeriodSeconds: 90
                                                containers:
                                                  - image: nginx
                                                    name: nginx
                                                    env:
                                                      - name: HTTP_PORT
                                                        value: 80
                                                    command:
                                                      - npm
                                                      - start
                                                    resources:
                                                      cpu: 0.5
                                                      memory: 1Gi
                                                scale:
                                                  minReplicas: 1
                                                  maxReplicas: 3
                                                  rules:
                                                  - http:
                                                      auth:
                                                      - secretRef: secretref
                                                        triggerParameter: trigger
                                                      metadata:
                                                        concurrentRequests: '50'
                                                        key: value
                                                    name: http-scale-rule
                                            identity:
                                              type: UserAssigned
                                              userAssignedIdentities:
                                                {user_identity_id}: {{}}
                                            """

        write_test_file(containerapp_file_name, containerapp_yaml_text)
        app2 = self.create_random_name(prefix='yaml2', length=24)
        self.cmd(
            f'containerapp create -n {app2} -g {resource_group} --environment {env2} --yaml {containerapp_file_name}')
        self.cmd(f'containerapp show -g {resource_group} -n {app2}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.environmentId", containerapp_env2["id"]),
            JMESPathCheck("properties.configuration.ingress.external", False),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].name", "name"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].ipAddressRange",
                          "1.1.1.1/10"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].action", "Allow"),
            JMESPathCheck("properties.environmentId", containerapp_env2["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision"),
            JMESPathCheck("properties.template.terminationGracePeriodSeconds", 90),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3),
            JMESPathCheck("properties.template.scale.rules[0].name", "http-scale-rule"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.concurrentRequests", "50"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.key", "value"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].triggerParameter", "trigger"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].secretRef", "secretref"),
        ])
        clean_up_test_file(containerapp_file_name)

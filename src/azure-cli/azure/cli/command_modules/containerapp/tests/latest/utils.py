# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import requests
from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION


def prepare_containerapp_env_for_app_e2e_tests(test_cls):
    from azure.cli.core.azclierror import CLIInternalError
    from .common import TEST_LOCATION
    rg_name = f'client.env_rg_{TEST_LOCATION}'.lower().replace(" ", "").replace("(", "").replace(")", "")
    env_name = f'env-{TEST_LOCATION}'.lower().replace(" ", "").replace("(", "").replace(")", "")
    managed_env = None
    try:
        managed_env = test_cls.cmd('containerapp env show -g {} -n {}'.format(rg_name, env_name)).get_output_in_json()
    except CLIInternalError as e:
        if 'ResourceGroupNotFound' in e.error_msg or 'ResourceNotFound' in e.error_msg:
            test_cls.cmd(f'group create -n {rg_name}')
            test_cls.cmd(f'containerapp env create -g {rg_name} -n {env_name} --logs-destination none')
            managed_env = test_cls.cmd('containerapp env show -g {} -n {}'.format(rg_name, env_name)).get_output_in_json()

            while managed_env["properties"]["provisioningState"].lower() == "waiting":
                time.sleep(5)
                managed_env = test_cls.cmd('containerapp env show -g {} -n {}'.format(rg_name, env_name)).get_output_in_json()
    return managed_env["id"]


def create_containerapp_env(test_cls, env_name, resource_group, location=None, logs_workspace=None, logs_workspace_shared_key=None):
    if logs_workspace is None:
        logs_workspace_name = test_cls.create_random_name(prefix='containerapp-env', length=24)
        logs_workspace = test_cls.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_shared_key = test_cls.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

    if location:
        test_cls.cmd(f'containerapp env create -g {resource_group} -n {env_name} --logs-workspace-id {logs_workspace} --logs-workspace-key {logs_workspace_shared_key} -l {location}')
    else:
        test_cls.cmd(f'containerapp env create -g {resource_group} -n {env_name} --logs-workspace-id {logs_workspace} --logs-workspace-key {logs_workspace_shared_key}')

    containerapp_env = test_cls.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

    while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
        time.sleep(5)
        containerapp_env = test_cls.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()


def create_and_verify_containerapp_up(
            test_cls,
            resource_group,
            env_name=None,
            source_path=None,
            image=None,
            location=None,
            ingress=None,
            target_port=None,
            app_name=None):
        # Configure the default location
        test_cls.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        # Ensure that the Container App environment is created
        if env_name is None:
           env_name = test_cls.create_random_name(prefix='env', length=24)
           test_cls.cmd(f'containerapp env create -g {resource_group} -n {env_name}')

        if app_name is None:
            # Generate a name for the Container App
            app_name = test_cls.create_random_name(prefix='containerapp', length=24)

        # Construct the 'az containerapp up' command
        up_cmd = f"containerapp up -g {resource_group} -n {app_name} --environment {env_name}"
        if source_path:
            up_cmd += f" --source \"{source_path}\""
        if image:
            up_cmd += f" --image {image}"
        if ingress:
            up_cmd += f" --ingress {ingress}"
        if target_port:
            up_cmd += f" --target-port {target_port}"

        # Execute the 'az containerapp up' command
        test_cls.cmd(up_cmd)

        # Verify that the Container App is running
        app = test_cls.cmd(f"containerapp show -g {resource_group} -n {app_name}").get_output_in_json()
        url = app["properties"]["configuration"]["ingress"]["fqdn"]
        url = url if url.startswith("http") else f"http://{url}"
        resp = requests.get(url)
        test_cls.assertTrue(resp.ok)

        # Re-run the 'az containerapp up' command with the location parameter if provided
        if location:
            up_cmd += f" -l {location.upper()}"
            test_cls.cmd(up_cmd)


def create_vnet_subnet(self, resource_group, vnet, delegations='Microsoft.App/environments', location="centralus"):
    self.cmd(f"az network vnet create --address-prefixes '14.0.0.0/23' -g {resource_group} -n {vnet} --location {location}")
    subnet_command = f"az network vnet subnet create --address-prefixes '14.0.0.0/23' -n sub -g {resource_group} --vnet-name {vnet}"
    if delegations is not None:
        subnet_command += f' --delegations {delegations}'
    sub_id = self.cmd(subnet_command).get_output_in_json()["id"]
    return sub_id
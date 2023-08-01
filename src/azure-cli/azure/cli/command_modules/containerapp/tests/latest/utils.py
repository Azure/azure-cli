# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import requests
from azext_containerapp.tests.latest.common import TEST_LOCATION

def create_containerapp_env(test_cls, env_name, resource_group, location=None):
    logs_workspace_name = test_cls.create_random_name(prefix='containerapp-env', length=24)
    logs_workspace_id = test_cls.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
    logs_workspace_key = test_cls.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

    if location:
        test_cls.cmd(f'containerapp env create -g {resource_group} -n {env_name} --logs-workspace-id {logs_workspace_id} --logs-workspace-key {logs_workspace_key} -l {location}')
    else:
        test_cls.cmd(f'containerapp env create -g {resource_group} -n {env_name} --logs-workspace-id {logs_workspace_id} --logs-workspace-key {logs_workspace_key}')

    containerapp_env = test_cls.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

    while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
        time.sleep(5)
        containerapp_env = test_cls.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

def create_and_verify_containerapp_up(
            test_cls,
            resource_group,
            env_name = None,
            source_path = None,
            image = None,
            location = None,
            ingress = None,
            target_port = None,
            app_name = None):
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
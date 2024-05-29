# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest  # pylint: disable=unused-import

from azure.cli.testsdk import (ResourceGroupPreparer, LogAnalyticsWorkspacePreparer, JMESPathCheck, live_only)
from azure.cli.testsdk.decorators import serial_test
from azure.cli.command_modules.containerapp.tests.latest.common import (
    ContainerappComposePreviewScenarioTest,  # pylint: disable=unused-import
    write_test_file,
    clean_up_test_file,
    TEST_DIR, TEST_LOCATION)

from .utils import create_containerapp_env, prepare_containerapp_env_for_app_e2e_tests


# flake8: noqa
# noqa
# pylint: skip-file


class ContainerappComposeBaseScenarioTest(ContainerappComposePreviewScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_basic_no_existing_resources(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: smurawski/printenv:latest
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.kwargs.update({
            'environment': env_id,
            'compose': compose_file_name,
        })

        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        self.cmd(command_string, checks=[
            self.check('[].name', ['foo']),
            self.check('[] | length(@)', 1),
        ])
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)

    # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    # During create an environment, it created a log workspace with a random name, which cause the test cannot find the match Url
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_environment_to_target_location(self, resource_group):
        location = "East US"
        app = self.create_random_name(prefix='composeapp', length=24)
        env = self.create_random_name(prefix='env', length=24)
        compose_text = f"""
services:
  {app}:
    image: smurawski/printenv:latest
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)

        self.kwargs.update({
            'environment': env,
            'location': location,
            'compose': compose_file_name,
        })

        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        command_string += ' --location "{location}"'
        self.cmd(command_string, checks=[
            self.check('[].name', [app]),
            self.check('[] | length(@)', 1),
        ])
        env_json = self.cmd(f'containerapp env show -g {resource_group} -n {env}', checks=[
            JMESPathCheck("name", env),
            JMESPathCheck("resourceGroup", resource_group),
            JMESPathCheck("location", location),
            JMESPathCheck("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("name", app),
            JMESPathCheck("resourceGroup", resource_group),
            JMESPathCheck("location", location),
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.environmentId", env_json.get("id")),
        ])
        self.cmd(f'containerapp delete -n {app} -g {resource_group} --yes', expect_failure=False)
        self.cmd(f'containerapp env delete -n {env} -g {resource_group} --yes --no-wait', expect_failure=False)
        clean_up_test_file(compose_file_name)

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest  # pylint: disable=unused-import

from azure.cli.testsdk import (ResourceGroupPreparer, LogAnalyticsWorkspacePreparer)
from azure.cli.testsdk.decorators import serial_test
from azure.cli.command_modules.containerapp.tests.latest.common import (
    ContainerappComposePreviewScenarioTest,  # pylint: disable=unused-import
    write_test_file,
    clean_up_test_file,
    TEST_DIR, TEST_LOCATION)

from .utils import create_containerapp_env
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerappComposePreviewEnvironmentSettingsScenarioTest(ContainerappComposePreviewScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_containerapp_compose_create_with_environment(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    environment:
      - RACK_ENV=development
      - SHOW=true
      - BAZ="snafu"
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        
        env_name = self.create_random_name(prefix='containerapp-compose', length=24)

        self.kwargs.update({
            'environment': env_name,
            'compose': compose_file_name,
        })

        create_containerapp_env(self, env_name, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)


        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        self.cmd(command_string, checks=[
            self.check('[?name==`foo`].properties.template.containers[0].env[0].name', ["RACK_ENV"]),
            self.check('[?name==`foo`].properties.template.containers[0].env[0].value', ["development"]),
            self.check('[?name==`foo`].properties.template.containers[0].env[1].name', ["SHOW"]),
            self.check('[?name==`foo`].properties.template.containers[0].env[1].value', ["true"]),
            self.check('[?name==`foo`].properties.template.containers[0].env[2].name', ["BAZ"]),
            self.check('[?name==`foo`].properties.template.containers[0].env[2].value', ['"snafu"'])
        ])

        clean_up_test_file(compose_file_name)


class ContainerappComposePreviewEnvironmentSettingsExpectedExceptionScenarioTest(ContainerappComposePreviewScenarioTest):  # pylint: disable=line-too-long
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_containerapp_compose_create_with_environment_prompt(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    environment:
      - LOREM=
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_name = self.create_random_name(prefix='containerapp-compose', length=24)

        self.kwargs.update({
            'environment': env_name,
            'compose': compose_file_name,
        })

        create_containerapp_env(self, env_name, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)

        
        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'

        # This test fails because prompts are not supported in NoTTY environments
        self.cmd(command_string, expect_failure=True)

        clean_up_test_file(compose_file_name)

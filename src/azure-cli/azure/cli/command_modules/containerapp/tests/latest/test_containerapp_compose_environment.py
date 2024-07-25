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

from .utils import create_containerapp_env, prepare_containerapp_env_for_app_e2e_tests


# flake8: noqa
# noqa
# pylint: skip-file


class ContainerappComposePreviewEnvironmentSettingsScenarioTest(ContainerappComposePreviewScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_environment(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        app1 = self.create_random_name(prefix='aca1', length=24)
        app2 = self.create_random_name(prefix='aca2', length=24)
        app3 = self.create_random_name(prefix='aca2', length=24)

        compose_text = f"""
services:
  {app1}:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    environment:
      - RACK_ENV1=development1
      - SHOW1=true
      - BAZ1="snafu1"
  {app2}:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    environment:
      - RACK_ENV2=development2
      - SHOW2=false
      - BAZ2="snafu2"
  {app3}:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    expose:
    - 8080
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
        result = self.cmd(command_string, checks=[
            self.check(f'length(@)', 3),
            self.check(f'length([?name==`{app1}`].properties.template.containers)', 1),
            self.check(f'length([?name==`{app1}`].properties.template.containers[0].env)', 1),
            self.check(f'[?name==`{app1}`].properties.template.containers[0].env[0].name', ["RACK_ENV1"]),
            self.check(f'[?name==`{app1}`].properties.template.containers[0].env[0].value', ["development1"]),
            self.check(f'[?name==`{app1}`].properties.template.containers[0].env[1].name', ["SHOW1"]),
            self.check(f'[?name==`{app1}`].properties.template.containers[0].env[1].value', ["true"]),
            self.check(f'[?name==`{app1}`].properties.template.containers[0].env[2].name', ["BAZ1"]),
            self.check(f'[?name==`{app1}`].properties.template.containers[0].env[2].value', ['"snafu1"']),
            self.check(f'length([?name==`{app2}`].properties.template.containers)', 1),
            self.check(f'length([?name==`{app2}`].properties.template.containers[0].env)', 1),
            self.check(f'[?name==`{app2}`].properties.template.containers[0].env[0].name', ["RACK_ENV2"]),
            self.check(f'[?name==`{app2}`].properties.template.containers[0].env[0].value', ["development2"]),
            self.check(f'[?name==`{app2}`].properties.template.containers[0].env[1].name', ["SHOW2"]),
            self.check(f'[?name==`{app2}`].properties.template.containers[0].env[1].value', ["false"]),
            self.check(f'[?name==`{app2}`].properties.template.containers[0].env[2].name', ["BAZ2"]),
            self.check(f'[?name==`{app2}`].properties.template.containers[0].env[2].value', ['"snafu2"']),
            self.check(f'length([?name==`{app3}`].properties.template.containers)', 1),
        ]).get_output_in_json()
        self.assertEqual(result[2].get('properties').get('template').get('containers')[0].get('name'), app3)
        self.assertEqual(result[2].get('properties').get('template').get('containers')[0].get('env'), None)

        self.cmd(f'containerapp delete -n {app1} -g {resource_group} --yes', expect_failure=False)
        self.cmd(f'containerapp delete -n {app2} -g {resource_group} --yes', expect_failure=False)
        self.cmd(f'containerapp delete -n {app3} -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)


class ContainerappComposePreviewEnvironmentSettingsExpectedExceptionScenarioTest(ContainerappComposePreviewScenarioTest):  # pylint: disable=line-too-long
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_environment_prompt(self, resource_group):
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
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.kwargs.update({
            'environment': env_id,
            'compose': compose_file_name,
        })
        
        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'

        # This test fails because prompts are not supported in NoTTY environments
        self.cmd(command_string, expect_failure=True)
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)

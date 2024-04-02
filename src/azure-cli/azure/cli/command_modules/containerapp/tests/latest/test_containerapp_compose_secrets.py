# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest  # pylint: disable=unused-import

from azure.cli.testsdk import (ResourceGroupPreparer)
from azure.cli.testsdk.decorators import serial_test
from azure.cli.command_modules.containerapp.tests.latest.common import (
    ContainerappComposePreviewScenarioTest,  # pylint: disable=unused-import
    write_test_file,
    clean_up_test_file,
    TEST_DIR, TEST_LOCATION)

from .utils import prepare_containerapp_env_for_app_e2e_tests


# flake8: noqa
# noqa
# pylint: skip-file


class ContainerappComposePreviewSecretsScenarioTest(ContainerappComposePreviewScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_secrets(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    secrets:
      - source: my_secret
        target: redis_secret
        uid: '103'
        gid: '103'
        mode: 0440
secrets:
  my_secret:
    file: ./my_secret.txt
  my_other_secret:
    external: true
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        
        secrets_file_name = "./my_secret.txt"
        secrets_text = "Lorem Ipsum\n"
        write_test_file(secrets_file_name, secrets_text)
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
            self.check('[?name==`foo`].properties.configuration.secrets[0].name', ["redis-secret"]),
            self.check('[?name==`foo`].properties.template.containers[0].env[0].name', ["redis-secret"]),
            self.check('[?name==`foo`].properties.template.containers[0].env[0].secretRef', ["redis-secret"])  # pylint: disable=C0301
        ])
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)
        clean_up_test_file(secrets_file_name)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_secrets_and_existing_environment(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    environment:
      database__client: mysql
      database__connection__host: db
      database__connection__user: root
      database__connection__password: example
      database__connection__database: snafu
    secrets:
      - source: my_secret
        target: redis_secret
        uid: '103'
        gid: '103'
        mode: 0440
secrets:
  my_secret:
    file: ./snafu.txt
  my_other_secret:
    external: true
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)

        secrets_file_name = "./snafu.txt"
        secrets_text = "Lorem Ipsum\n"
        write_test_file(secrets_file_name, secrets_text)

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
            self.check('length([?name==`foo`].properties.template.containers[0].env[].name)', 6),
        ])
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)
        clean_up_test_file(secrets_file_name)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_secrets_and_existing_environment_conflict(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    environment:
      database--client: mysql
    secrets:
      -  database__client
secrets:
  database__client:
    file: ./database__client.txt
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)

        secrets_file_name = "./database__client.txt"
        secrets_text = "Lorem Ipsum\n"
        write_test_file(secrets_file_name, secrets_text)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.kwargs.update({
            'environment': env_id,
            'compose': compose_file_name,
        })
        
        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'

        # This test fails with duplicate environment variable names
        self.cmd(command_string, expect_failure=True)
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)
        clean_up_test_file(secrets_file_name)

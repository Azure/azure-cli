# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest  # pylint: disable=unused-import

from azure.cli.testsdk import (ResourceGroupPreparer)
from azure.cli.testsdk.decorators import serial_test
from azext_containerapp.tests.latest.common import (
    ContainerappComposePreviewScenarioTest,  # pylint: disable=unused-import
    write_test_file,
    clean_up_test_file,
    TEST_DIR, TEST_LOCATION)

from .utils import create_containerapp_env


class ContainerappComposePreviewReplicasScenarioTest(ContainerappComposePreviewScenarioTest):
    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_replicas_global_scale(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    ports: 8080:80
    scale: 4
    deploy:
      mode: global
      replicas: 6
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_name = self.create_random_name(prefix='containerapp-compose', length=24)

        self.kwargs.update({
            'environment': env_name,
            'compose': compose_file_name,
        })

        create_containerapp_env(self, env_name, resource_group)

        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'

        self.cmd(command_string, checks=[
            self.check('[?name==`foo`].properties.template.scale.minReplicas', [1]),
            self.check('[?name==`foo`].properties.template.scale.maxReplicas', [1]),
        ])

        clean_up_test_file(compose_file_name)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_replicas_replicated_mode(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    ports: 8080:80
    deploy:
      mode: replicated
      replicas: 6
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_name = self.create_random_name(prefix='containerapp-compose', length=24)

        self.kwargs.update({
            'environment': env_name,
            'compose': compose_file_name,
        })

        create_containerapp_env(self, env_name, resource_group, 'eastus')
        
        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'

        self.cmd(command_string, checks=[
            self.check('[?name==`foo`].properties.template.scale.minReplicas', [6]),
            self.check('[?name==`foo`].properties.template.scale.maxReplicas', [6]),
        ])

        clean_up_test_file(compose_file_name)

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


class ContainerappComposePreviewTransportOverridesScenarioTest(ContainerappComposePreviewScenarioTest):
    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_containerapp_compose_create_with_transport_arg(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    ports: 8080:80
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_name = self.create_random_name(prefix='containerapp-compose', length=24)
        
        self.kwargs.update({
            'environment': env_name,
            'compose': compose_file_name,
            'transport': "foo=http2 bar=auto",
            'second_transport': "baz=http",
        })

        create_containerapp_env(self, env_name, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)
        
        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        command_string += ' --transport-mapping {transport}'
        command_string += ' --transport-mapping {second_transport}'
        self.cmd(command_string, checks=[
            self.check('[?name==`foo`].properties.configuration.ingress.transport', ["Http2"]),
        ])

        clean_up_test_file(compose_file_name)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_containerapp_compose_create_with_transport_mapping_arg(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/k8se/quickstart:latest
    ports: 8080:80
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_name = self.create_random_name(prefix='containerapp-compose', length=24)

        create_containerapp_env(self, env_name, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)

        self.kwargs.update({
            'environment': env_name,
            'compose': compose_file_name,
            'transport': "foo=http2 bar=auto",
            'second_transport': "baz=http",
        })

        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        command_string += ' --transport-mapping {transport}'
        command_string += ' --transport-mapping {second_transport}'
        self.cmd(command_string, checks=[
            self.check('[?name==`foo`].properties.configuration.ingress.transport', ["Http2"]),
        ])

        clean_up_test_file(compose_file_name)
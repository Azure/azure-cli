# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest  # pylint: disable=unused-import

from azure.cli.testsdk import (ResourceGroupPreparer, JMESPathCheck, live_only)
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


class ContainerappComposePreviewRegistryAllArgsScenarioTest(ContainerappComposePreviewScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_registry_all_args(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    ports: 8080:80
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.kwargs.update({
            'environment': env_id,
            'compose': compose_file_name,
            'registry_server': "foobar.azurecr.io",
            'registry_user': "foobar",
            'registry_pass': "snafu",
        })

        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        command_string += ' --registry-server {registry_server}'
        command_string += ' --registry-username {registry_user}'
        command_string += ' --registry-password {registry_pass}'

        self.cmd(command_string, checks=[
            self.check('[?name==`foo`].properties.configuration.registries[0].server', ["foobar.azurecr.io"]),
            self.check('[?name==`foo`].properties.configuration.registries[0].username', ["foobar"]),
            self.check('[?name==`foo`].properties.configuration.registries[0].passwordSecretRef', ["foobarazurecrio-foobar"]),  # pylint: disable=C0301
        ])
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)


class ContainerappComposePreviewRegistryServerArgOnlyScenarioTest(ContainerappComposePreviewScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_registry_server_arg_only(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        compose_text = """
services:
  foo:
    image: mcr.microsoft.com/azuredocs/aks-helloworld:v1
    ports: 8080:80
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.kwargs.update({
            'environment': env_id,
            'compose': compose_file_name,
            'registry_server': "foobar.azurecr.io",
        })
        
        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        command_string += ' --registry-server {registry_server}'

        # This test fails because prompts are not supported in NoTTY environments
        self.cmd(command_string, expect_failure=True)
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)

    @serial_test()
    @live_only()  # Pass lively, But failed in playback mode when execute queue_acr_build
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_image_tag_and_use_existing_registry_server_from_image(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        acr = self.create_random_name(prefix='acr', length=24)
        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        image = f"{acr}.azurecr.io/azuredocs/aks-helloworld:v1"
        source_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_dockerfile"))
        dockerfile_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_dockerfile", "Dockerfile"))
        compose_text = f"""
services:
  foo:
    image: {image}
    build:
     context: {source_path}
     dockerfile: {dockerfile_path}
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

        self.cmd(command_string, expect_failure=False)
        self.cmd(f'containerapp show -n foo -g {resource_group}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.template.containers[0].image", image),
        ])
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)

    @serial_test()
    @live_only()  # Pass lively, But failed in playback mode when execute queue_acr_build
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_with_image_tag_and_use_existing_registry_server_and_password(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        acr = self.create_random_name(prefix='acr', length=24)
        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        password = self.cmd(f'acr credential show -n {acr} --query passwords[0].value').get_output_in_json()
        image = f"{acr}.azurecr.io/azuredocs/aks-helloworld:v1"
        source_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_dockerfile"))
        dockerfile_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_dockerfile", "Dockerfile"))
        compose_text = f"""
services:
  foo:
    image: azuredocs/aks-helloworld:v1
    build:
     context: {source_path}
     dockerfile: {dockerfile_path}
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.kwargs.update({
            'environment': env_id,
            'compose': compose_file_name,
            'registry_server': f"{acr}.azurecr.io",
            'registry_username': acr,
            'registry_password': password,
        })

        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        command_string += ' --registry-server {registry_server} --registry-username {registry_username} --registry-password {registry_password}'

        self.cmd(command_string, expect_failure=False)
        self.cmd(f'containerapp show -n foo -g {resource_group}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.template.containers[0].image", image),
        ])
        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)

    @serial_test()
    @live_only()  # Pass lively, But failed in playback mode when execute queue_acr_build
    @ResourceGroupPreparer(name_prefix='cli_test_containerapp_preview', location='eastus')
    def test_containerapp_compose_create_without_image_tag_and_use_existing_registry_server_and_password(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        acr = self.create_random_name(prefix='acr', length=24)
        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        password = self.cmd(f'acr credential show -n {acr} --query passwords[0].value').get_output_in_json()
        image = f"{acr}.azurecr.io/azuredocs/aks-helloworld:"
        source_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_dockerfile"))
        dockerfile_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_dockerfile", "Dockerfile"))
        compose_text = f"""
services:
  foo:
    image: azuredocs/aks-helloworld
    build:
     context: {source_path}
     dockerfile: {dockerfile_path}
"""
        compose_file_name = f"{self._testMethodName}_compose.yml"
        write_test_file(compose_file_name, compose_text)
        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.kwargs.update({
            'environment': env_id,
            'compose': compose_file_name,
            'registry_server': f"{acr}.azurecr.io",
            'registry_username': acr,
            'registry_password': password,
        })

        command_string = 'containerapp compose create'
        command_string += ' --compose-file-path {compose}'
        command_string += ' --resource-group {rg}'
        command_string += ' --environment {environment}'
        command_string += ' --registry-server {registry_server} --registry-username {registry_username} --registry-password {registry_password}'

        self.cmd(command_string, expect_failure=False)
        app_json = self.cmd(f'containerapp show -n foo -g {resource_group}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("length(properties.template.containers)", 1),
        ]).get_output_in_json()
        image_from_app = app_json["properties"]["template"]["containers"][0]["image"]
        self.assertTrue(image_from_app.startswith(image))

        self.cmd(f'containerapp delete -n foo -g {resource_group} --yes', expect_failure=False)
        clean_up_test_file(compose_file_name)

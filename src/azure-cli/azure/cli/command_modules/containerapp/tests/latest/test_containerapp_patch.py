# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from unittest import mock
import time
import requests

from azure.cli.testsdk.reverse_dependency import get_dummy_cli
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only)
from knack.util import CLIError

from azext_containerapp.tests.latest.common import TEST_LOCATION
from azext_containerapp import _utils
from azext_containerapp.tests.latest.utils import create_and_verify_containerapp_up
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        pip.main(['install --user', package])
    finally:
        globals()[package] = importlib.import_module(package)


install_and_import('docker')


class ContainerAppPatchTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(location = "eastus2")
    def test_containerapp_patch_list_and_apply_with_resource_group_e2e(self, resource_group):
        source_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_buildpack"))
        ingress = 'external'
        target_port = '8080'

        # Generate a name for the Container App
        app_name = self.create_random_name(prefix='containerapp', length=24)

        # Create container app and re-tag image to an older version to simulate patch list
        old_tag = "run-dotnet-aspnet-7.0.1-cbl-mariner2.0"
        create_and_verify_containerapp_up(self,resource_group,source_path=source_path,ingress=ingress,target_port=target_port,app_name=app_name)
        self._retag_image_to_older_version_and_push(resource_group=resource_group,app_name=app_name,old_tag=old_tag)

        # Execute and verify patch list command
        patchable_images = self.cmd(f'containerapp patch list -g {resource_group}').get_output_in_json()
        newRunImageTag = patchable_images[0]["newRunImage"].split(':')[1]
        self.assertEquals(newRunImageTag,_utils.get_latest_buildpack_run_tag("aspnet", "7.0"))
        self.assertEquals(patchable_images[0]["oldRunImage"], old_tag)

        # Execute and verify patch apply command
        self.cmd(f'containerapp patch apply -g {resource_group}')
        app = self.cmd(f"containerapp show -g {resource_group} -n {app_name}").get_output_in_json()
        patched_image = app["properties"]["template"]["containers"][0]["image"]
        patched_image_tag = patched_image.split(':')[1]
        self.assertEquals(patched_image_tag,_utils.get_latest_buildpack_run_tag("aspnet", "7.0"))

    @live_only()
    @ResourceGroupPreparer(location = "eastus2")
    def test_containerapp_patch_list_and_apply_with_environment_e2e(self, resource_group):
        source_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_buildpack"))
        ingress = 'external'
        target_port = '80'

        # Generate a name for the Container App
        app_name = self.create_random_name(prefix='containerapp', length=24)

        # Create managed environment
        env_name = self.create_random_name(prefix='env', length=24)
        self.cmd(f'containerapp env create -g {resource_group} -n {env_name}')

        # Create container app and re-tag image to an older version to simulate patch list
        old_tag = "run-dotnet-aspnet-7.0.1-cbl-mariner2.0"
        create_and_verify_containerapp_up(self,resource_group,env_name=env_name,source_path=source_path,ingress=ingress,target_port=target_port,app_name=app_name)
        self._retag_image_to_older_version_and_push(resource_group=resource_group,app_name=app_name,old_tag=old_tag)

        # Execute and verify patch list command
        patchable_images = self.cmd(f'containerapp patch list -g {resource_group} --environment {env_name}').get_output_in_json()
        newRunImageTag = patchable_images[0]["newRunImage"].split(':')[1]
        self.assertEquals(newRunImageTag,_utils.get_latest_buildpack_run_tag("aspnet", "7.0"))
        self.assertEquals(patchable_images[0]["oldRunImage"], old_tag)

        # Execute and verify patch apply command
        self.cmd(f'containerapp patch apply -g {resource_group} --environment {env_name}')
        app = self.cmd(f"containerapp show -g {resource_group} -n {app_name}").get_output_in_json()
        patched_image = app["properties"]["template"]["containers"][0]["image"]
        patched_image_tag = patched_image.split(':')[1]
        self.assertEquals(patched_image_tag,_utils.get_latest_buildpack_run_tag("aspnet", "7.0"))

    @live_only()
    @ResourceGroupPreparer(location = "eastus2")
    def test_containerapp_patch_list_and_apply_with_show_all_e2e(self, resource_group):
        image = "mcr.microsoft.com/k8se/quickstart:latest"

        # Generate a name for the Container App
        app_name = self.create_random_name(prefix='containerapp', length=24)

        # Create managed environment
        env_name = self.create_random_name(prefix='env', length=24)
        self.cmd(f'containerapp env create -g {resource_group} -n {env_name}')

        create_and_verify_containerapp_up(self,resource_group,env_name=env_name,image=image,app_name=app_name)

        # Execute and verify patch list command
        patch_cmd = f'containerapp patch list -g {resource_group} --environment {env_name} --show-all'
        output = self.cmd(patch_cmd).get_output_in_json()
        self.assertEquals(output[0]["targetImageName"],"mcr.microsoft.com/k8se/quickstart:latest")

        # Execute and verify patch apply command
        self.cmd(f'containerapp patch apply -g {resource_group} --environment {env_name} --show-all')
        app = self.cmd(f"containerapp show -g {resource_group} -n {app_name}").get_output_in_json()
        image = app["properties"]["template"]["containers"][0]["image"]
        self.assertEquals(image,"mcr.microsoft.com/k8se/quickstart:latest")

    # @live_only()
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_patch_list_and_apply_without_arguments_e2e(self, resource_group):
        import docker

        client = docker.from_env()


    @live_only()
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location = "eastus2")
    def test_containerapp_patch_list_and_apply_without_arguments_e2e2(self, resource_group):
        source_path = os.path.join(TEST_DIR, os.path.join("data", "source_built_using_buildpack"))
        ingress = 'external'
        target_port = '80'

        # Generate a name for the Container App
        app_name = self.create_random_name(prefix='containerapp', length=24)

        # Create container app and re-tag image to an older version to simulate patch list
        old_tag = "run-dotnet-aspnet-7.0.1-cbl-mariner2.0"
        create_and_verify_containerapp_up(self,resource_group,source_path=source_path,ingress=ingress,target_port=target_port,app_name=app_name)
        self._retag_image_to_older_version_and_push(resource_group=resource_group,app_name=app_name,old_tag=old_tag)

        # Execute and verify patch list command
        self.cmd(f'configure --defaults group={resource_group}')
        patch_cmd = f'containerapp patch list'
        patchable_images = self.cmd(patch_cmd).get_output_in_json()
        newRunImageTag = patchable_images[0]["newRunImage"].split(':')[1]
        self.assertEquals(newRunImageTag,_utils.get_latest_buildpack_run_tag("aspnet", "7.0"))
        self.assertEquals(patchable_images[0]["oldRunImage"], old_tag)

        # Execute and verify patch apply command
        self.cmd(f'containerapp patch apply')
        app = self.cmd(f"containerapp show -g {resource_group} -n {app_name}").get_output_in_json()
        patched_image = app["properties"]["template"]["containers"][0]["image"]
        patched_image_tag = patched_image.split(':')[1]
        self.assertEquals(patched_image_tag,_utils.get_latest_buildpack_run_tag("aspnet", "7.0"))

    def _retag_image_to_older_version_and_push(self,resource_group,app_name,old_tag):
        return


# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from msrestazure.tools import parse_resource_id

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only, StorageAccountPreparer,
                               LogAnalyticsWorkspacePreparer)

from .utils import prepare_containerapp_env_for_app_e2e_tests

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppMountSecretTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    def test_container_app_mount_secret_e2e(self, resource_group):

        app = self.create_random_name(prefix='app1', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)
        env_rg = parse_resource_id(env_id).get('resource_group')
        env_name = parse_resource_id(env_id).get('name')

        self.cmd('containerapp env show -n {} -g {}'.format(env_name, env_rg), checks=[
            JMESPathCheck('name', env_name)
        ])

        secretRef1 = "mysecret"
        secretValue1 = "secretvalue1"
        secretRef2 = "anothersecret"
        secretValue2 = "secretvalue2"

        self.cmd(f'az containerapp create -g {resource_group} --environment {env_id} -n {app} --secrets {secretRef1}={secretValue1} {secretRef2}={secretValue2} --secret-volume-mount "mnt/secrets"')
        
        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.template.volumes[0].storageType', 'Secret'), 
            # --secret-volume-mount mounts all secrets, not specific secrets, therefore no secrets should be returned.
            JMESPathCheck('properties.template.volumes[0].secrets', None)
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    def test_container_app_mount_secret_update_e2e(self, resource_group):
        # test creating a container app that does not have a secret volume mount, then uses update to add a secret volume mount
        app = self.create_random_name(prefix='app2', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)
        env_rg = parse_resource_id(env_id).get('resource_group')
        env_name = parse_resource_id(env_id).get('name')

        secretRef1 = "mysecret"
        secretValue1 = "secretvalue1"
        secretRef2 = "anothersecret"
        secretValue2 = "secretvalue2"

        self.cmd('containerapp env show -n {} -g {}'.format(env_name, env_rg), checks=[
            JMESPathCheck('name', env_name)
        ])

        self.cmd(
            f'az containerapp create -g {resource_group} --environment {env_id} -n {app} --secrets {secretRef1}={secretValue1} {secretRef2}={secretValue2}')

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.template.volumes', None),
        ])

        self.cmd(f'az containerapp update -n {app} -g {resource_group} --secret-volume-mount "mnt/secrets"')

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.template.volumes[0].storageType', 'Secret'),
            JMESPathCheck('properties.template.volumes[0].secrets', None),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].mountPath', 'mnt/secrets'),
        ])
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only, StorageAccountPreparer,
                               LogAnalyticsWorkspacePreparer)

from .utils import create_containerapp_env

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppIngressStickySessionsTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_ingress_sticky_sessions_e2e(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        import requests

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='app2', length=24)

        create_containerapp_env(self, env, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)

        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env)            
        ])
        self.cmd("az containerapp create -g {} --target-port 80 --ingress external --image mcr.microsoft.com/k8se/quickstart:latest --environment {} -n {} ".format(resource_group, env, app))        
        self.cmd("az containerapp ingress sticky-sessions set -n {} -g {} --affinity sticky".format(app, resource_group), expect_failure=False, checks=[
            JMESPathCheck('stickySessions.affinity', "sticky")
        ])
        self.cmd("az containerapp ingress sticky-sessions show -n {} -g {}".format(app, resource_group), expect_failure=False, checks=[
            JMESPathCheck('stickySessions.affinity', "sticky")
        ])
        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.configuration.ingress.stickySessions.affinity', "sticky"),        
        ])
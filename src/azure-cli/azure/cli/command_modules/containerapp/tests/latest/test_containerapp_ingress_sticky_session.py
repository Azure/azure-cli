# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only, StorageAccountPreparer)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

from .utils import create_containerapp_env

class ContainerAppIngressStickySessionsTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_ingress_sticky_sessions_e2e(self, resource_group):
        import requests

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='app2', length=24)

        create_containerapp_env(self, env, resource_group)

        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env)            
        ])

        self.cmd("az containerapp create -g {} --target-port 80 --ingress external --image mcr.microsoft.com/k8se/quickstart:latest --environment {} -n {} ".format(resource_group, env, app))        
        self.cmd("az containerapp ingress sticky-sessions set -n {} -g {} --affinity sticky".format(app, resource_group))        
        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.configuration.ingress.stickySessions.affinity', "sticky"),        
        ])
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.mgmt.core.tools import parse_resource_id

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only)

from .utils import prepare_containerapp_env_for_app_e2e_tests

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppIngressStickySessionsTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_ingress_sticky_sessions_e2e(self, resource_group):

        app = self.create_random_name(prefix='app2', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)
        env_rg = parse_resource_id(env_id).get('resource_group')
        env_name = parse_resource_id(env_id).get('name')

        self.cmd('containerapp env show -n {} -g {}'.format(env_name, env_rg), checks=[
            JMESPathCheck('name', env_name)
        ])
        self.cmd("az containerapp create -g {} --target-port 80 --ingress external --image mcr.microsoft.com/k8se/quickstart:latest --environment {} -n {} ".format(resource_group, env_id, app))
        self.cmd("az containerapp ingress sticky-sessions set -n {} -g {} --affinity sticky".format(app, resource_group), expect_failure=False, checks=[
            JMESPathCheck('stickySessions.affinity', "sticky")
        ])
        self.cmd("az containerapp ingress sticky-sessions show -n {} -g {}".format(app, resource_group), expect_failure=False, checks=[
            JMESPathCheck('stickySessions.affinity', "sticky")
        ])
        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.configuration.ingress.stickySessions.affinity', "sticky"),        
        ])
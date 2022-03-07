# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import unittest
from unittest.mock import Mock, call, patch

from azure.cli.command_modules.acs._consts import (
    DecoratorEarlyExitException,
    DecoratorMode,
)
from azure.cli.command_modules.acs.agentpool_decorator import (
    AKSAgentPoolContext,
    AKSAgentPoolAddDecorator,
    AKSAgentPoolModels,
    AKSAgentPoolUpdateDecorator,
)
from azure.cli.command_modules.acs.tests.latest.mocks import (
    MockCLI,
    MockClient,
    MockCmd,
)
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    AzCLIError,
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    NoTTYError,
    RequiredArgumentMissingError,
    UnknownError,
)
from azure.cli.core.profiles import ResourceType
from azure.core.exceptions import HttpResponseError
from knack.prompting import NoTTYException
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError


class AKSAgentPoolModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)

    def test_models(self):
        models = AKSAgentPoolModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

        # load models directly (instead of through the `get_sdk` method provided by the cli component)
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES

        sdk_profile = AZURE_API_PROFILES["latest"][ResourceType.MGMT_CONTAINERSERVICE]
        api_version = sdk_profile.default_api_version
        module_name = "azure.mgmt.containerservice.v{}.models".format(api_version.replace("-", "_"))
        module = importlib.import_module(module_name)

        self.assertEqual(models.AgentPool, getattr(module, "AgentPool"))
        self.assertEqual(
            models.AgentPoolUpgradeSettings,
            getattr(module, "AgentPoolUpgradeSettings"),
        )


class AKSAgentPoolContextTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSAgentPoolModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

    def test__init__(self):
        # fail on not passing dictionary-like parameters
        with self.assertRaises(CLIInternalError):
            AKSAgentPoolContext(self.cmd, [], self.models, decorator_mode=DecoratorMode.CREATE)
        # fail on not passing decorator_mode with Enum type DecoratorMode
        with self.assertRaises(CLIInternalError):
            AKSAgentPoolContext(self.cmd, {}, self.models, decorator_mode=1)

    def test_attach_agentpool(self):
        ctx_1 = AKSAgentPoolContext(self.cmd, {}, self.models, decorator_mode=DecoratorMode.CREATE)
        agentpool = self.models.AgentPool()
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.agentpool, agentpool)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_agentpool(agentpool)

    def test_get_resource_group_name(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            {"resource_group_name": "test_rg_name"},
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_resource_group_name(), "test_rg_name")

    def test_get_cluster_name(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            {"cluster_name": "test_cluster_name"},
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_cluster_name(), "test_cluster_name")

    def test_get_nodepool_name(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            {"nodepool_name": "test_nodepool_name"},
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(),
        ):
            self.assertEqual(ctx_1.get_nodepool_name(), "test_nodepool_name")

        agentpool_1 = self.models.AgentPool()
        agentpool_1.name = "test_ap_name"
        ctx_1.attach_agentpool(agentpool_1)
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(),
        ):
            self.assertEqual(ctx_1.get_nodepool_name(), "test_ap_name")

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            {"nodepool_name": "test_nodepool_name"},
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        mock_agentpool_instance_1 = Mock()
        mock_agentpool_instance_1.name = "test_nodepool_name"
        mock_agentpool_operations = Mock(list=Mock(return_value=[mock_agentpool_instance_1]))
        # fail on existing nodepool name
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            mock_agentpool_operations,
        ), self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_nodepool_name()

    def test_get_max_surge(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            {
                "max_surge": None,
            },
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_max_surge(), None)

        upgrade_settings_1 = self.models.AgentPoolUpgradeSettings(max_surge="test_max_surge")
        agentpool_1 = self.models.AgentPool(upgrade_settings=upgrade_settings_1)
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(ctx_1.get_max_surge(), "test_max_surge")

    def test_get_aks_custom_headers(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            {
                "aks_custom_headers": None,
            },
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_aks_custom_headers(), {})

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            {
                "aks_custom_headers": "abc=def,xyz=123",
            },
            self.models,
            decorator_mode=DecoratorMode.UPDATE,
        )
        self.assertEqual(ctx_2.get_aks_custom_headers(), {"abc": "def", "xyz": "123"})

    def test_get_no_wait(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            {"no_wait": False},
            self.models,
            decorator_mode=DecoratorMode.CREATE,
        )
        self.assertEqual(ctx_1.get_no_wait(), False)


class AKSAgentPoolAddDecoratorTestCase(unittest.TestCase):
    def test(self):
        pass


class AKSAgentPoolUpdateDecoratorTestCase(unittest.TestCase):
    def test(self):
        pass


if __name__ == "__main__":
    unittest.main()

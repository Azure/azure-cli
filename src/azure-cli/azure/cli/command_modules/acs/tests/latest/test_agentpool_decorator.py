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
    AKSAgentPoolCreateDecorator,
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

        sdk_profile = AZURE_API_PROFILES["latest"][
            ResourceType.MGMT_CONTAINERSERVICE
        ]
        api_version = sdk_profile.default_api_version
        module_name = "azure.mgmt.containerservice.v{}.models".format(
            api_version.replace("-", "_")
        )
        module = importlib.import_module(module_name)

        self.assertEqual(
            models.AgentPool, getattr(module, "AgentPool")
        )
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
            AKSAgentPoolContext(
                self.cmd, [], self.models, decorator_mode=DecoratorMode.CREATE
            )
        # fail on not passing decorator_mode with Enum type DecoratorMode
        with self.assertRaises(CLIInternalError):
            AKSAgentPoolContext(self.cmd, {}, self.models, decorator_mode=1)

    def test_attach_agentpool(self):
        ctx_1 = AKSAgentPoolContext(
            self.cmd, {}, self.models, decorator_mode=DecoratorMode.CREATE
        )
        agentpool = self.models.AgentPool()
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.agentpool, agentpool)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_agentpool(agentpool)


if __name__ == "__main__":
    unittest.main()

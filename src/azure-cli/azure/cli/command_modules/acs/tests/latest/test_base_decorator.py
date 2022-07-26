# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import unittest

from azure.cli.command_modules.acs._consts import DecoratorMode
from azure.cli.command_modules.acs.base_decorator import (
    BaseAKSContext,
    BaseAKSManagedClusterDecorator,
    BaseAKSModels,
    BaseAKSParamDict,
    validate_decorator_mode,
)
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockClient, MockCmd
from azure.cli.core.azclierror import CLIInternalError
from azure.cli.core.profiles import ResourceType
from msrest.exceptions import ValidationError


class BaseDecoratorHelperFunctionsTestCase(unittest.TestCase):
    def test_validate_decorator_mode(self):
        self.assertEqual(validate_decorator_mode(DecoratorMode.CREATE), True)
        self.assertEqual(validate_decorator_mode(DecoratorMode.UPDATE), True)
        self.assertEqual(validate_decorator_mode(DecoratorMode), False)
        self.assertEqual(validate_decorator_mode(1), False)
        self.assertEqual(validate_decorator_mode("1"), False)
        self.assertEqual(validate_decorator_mode(True), False)
        self.assertEqual(validate_decorator_mode({}), False)


class BaseAKSModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)

    def test_models(self):
        # load models directly (instead of through the `get_sdk` method provided by the cli component)
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES

        sdk_profile = AZURE_API_PROFILES["latest"][ResourceType.MGMT_CONTAINERSERVICE]
        api_version = sdk_profile.default_api_version
        module_name = "azure.mgmt.containerservice.v{}.models".format(api_version.replace("-", "_"))
        module = importlib.import_module(module_name)

        models = BaseAKSModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)
        self.assertEqual(models.model_module, module)
        self.assertEqual(models.AgentPool, module.AgentPool)

    def test_serialize(self):
        models = BaseAKSModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

        agentpool = models.AgentPool(os_disk_size_gb=2049)
        # fail on os_disk_size_gb > 2048
        with self.assertRaises(ValidationError):
            models.serialize(agentpool, "AgentPool")

        agentpool_upgrade_settings = models.AgentPoolUpgradeSettings()
        self.assertEqual(models.serialize(agentpool_upgrade_settings, "AgentPoolUpgradeSettings"), {})


class BaseAKSParamDictTestCase(unittest.TestCase):
    def test__init__(self):
        # fail on not passing dictionary-like parameters
        with self.assertRaises(CLIInternalError):
            BaseAKSParamDict([])

    def test_get(self):
        param_dict = BaseAKSParamDict({"abc": "xyz"})
        self.assertEqual(param_dict.get("abc"), "xyz")

        param_dict_2 = BaseAKSParamDict({"a": None, "ab": False, "abc": ""})
        self.assertEqual(param_dict_2.get("a", True), True)
        self.assertEqual(param_dict_2.get("a", "xyz"), "xyz")
        self.assertEqual(param_dict_2.get("ab", True), False)
        self.assertEqual(param_dict_2.get("abc", True), "")
        self.assertEqual(param_dict_2.get("abcd", True), True)

    def test_keys(self):
        param_dict = BaseAKSParamDict({"abc": "xyz"})
        self.assertEqual(list(param_dict.keys()), ["abc"])

    def test_values(self):
        param_dict = BaseAKSParamDict({"abc": "xyz"})
        self.assertEqual(list(param_dict.values()), ["xyz"])

    def test_items(self):
        param_dict = BaseAKSParamDict({"abc": "xyz"})
        self.assertEqual(list(param_dict.items()), [("abc", "xyz")])

    def test_print_usage_statistics(self):
        param_dict = BaseAKSParamDict({"abc": "xyz", "def": 100})
        param_dict.print_usage_statistics()


class BaseAKSContextTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = BaseAKSModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

    def test__init__(self):
        # fail on not passing dictionary-like parameters
        with self.assertRaises(CLIInternalError):
            BaseAKSContext(self.cmd, [], self.models, decorator_mode=DecoratorMode.CREATE)
        # fail on not passing decorator_mode with Enum type DecoratorMode
        with self.assertRaises(CLIInternalError):
            BaseAKSContext(self.cmd, BaseAKSParamDict({}), self.models, decorator_mode=1)

    def test_get_intermediate(self):
        ctx_1 = BaseAKSContext(self.cmd, BaseAKSParamDict({}), self.models, decorator_mode=DecoratorMode.CREATE)
        self.assertEqual(
            ctx_1.get_intermediate("fake-intermediate", "not found"),
            "not found",
        )

    def test_set_intermediate(self):
        ctx_1 = BaseAKSContext(self.cmd, BaseAKSParamDict({}), self.models, decorator_mode=DecoratorMode.CREATE)
        ctx_1.set_intermediate("test-intermediate", "test-intermediate-value")
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "test-intermediate-value",
        )
        ctx_1.set_intermediate("test-intermediate", "new-test-intermediate-value")
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "test-intermediate-value",
        )
        ctx_1.set_intermediate(
            "test-intermediate",
            "new-test-intermediate-value",
            overwrite_exists=True,
        )
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "new-test-intermediate-value",
        )

    def test_remove_intermediate(self):
        ctx_1 = BaseAKSContext(self.cmd, BaseAKSParamDict({}), self.models, decorator_mode=DecoratorMode.CREATE)
        ctx_1.set_intermediate("test-intermediate", "test-intermediate-value")
        self.assertEqual(
            ctx_1.get_intermediate("test-intermediate"),
            "test-intermediate-value",
        )
        ctx_1.remove_intermediate("test-intermediate")
        self.assertEqual(ctx_1.get_intermediate("test-intermediate"), None)


class BaseAKSManagedClusterDecoratorTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.client = MockClient()
        self.test_models = BaseAKSModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

    def test_init(self):
        dec_1 = BaseAKSManagedClusterDecorator(self.cmd, self.client)
        self.assertEqual(dec_1.cmd, self.cmd)
        self.assertEqual(dec_1.client, self.client)

    def test_init_models(self):
        dec_1 = BaseAKSManagedClusterDecorator(self.cmd, self.client)
        with self.assertRaises(NotImplementedError):
            dec_1.init_models()

    def test_init_context(self):
        dec_1 = BaseAKSManagedClusterDecorator(self.cmd, self.client)
        with self.assertRaises(NotImplementedError):
            dec_1.init_context()

    def test_check_is_postprocessing_required(self):
        dec_1 = BaseAKSManagedClusterDecorator(self.cmd, self.client)
        mc_1 = self.test_models.ManagedCluster(location="test_location")
        with self.assertRaises(NotImplementedError):
            dec_1.check_is_postprocessing_required(mc_1)

    def test_immediate_processing_after_request(self):
        dec_1 = BaseAKSManagedClusterDecorator(self.cmd, self.client)
        mc_1 = self.test_models.ManagedCluster(location="test_location")
        with self.assertRaises(NotImplementedError):
            dec_1.immediate_processing_after_request(mc_1)

    def test_postprocessing_after_mc_created(self):
        dec_1 = BaseAKSManagedClusterDecorator(self.cmd, self.client)
        mc_1 = self.test_models.ManagedCluster(location="test_location")
        with self.assertRaises(NotImplementedError):
            dec_1.postprocessing_after_mc_created(mc_1)

    def test_put_mc(self):
        dec_1 = BaseAKSManagedClusterDecorator(self.cmd, self.client)
        mc_1 = self.test_models.ManagedCluster(location="test_location")
        with self.assertRaises(NotImplementedError):
            dec_1.put_mc(mc_1)


if __name__ == "__main__":
    unittest.main()

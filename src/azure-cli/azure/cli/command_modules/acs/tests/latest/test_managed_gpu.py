# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from azure.cli.command_modules.acs import ContainerServiceCommandsLoader
from azure.cli.command_modules.acs._consts import AgentPoolDecoratorMode, DecoratorMode
from azure.cli.command_modules.acs.agentpool_decorator import (
    AKSAgentPoolAddDecorator,
    AKSAgentPoolContext,
    AKSAgentPoolModels,
    AKSAgentPoolParamDict,
    AKSAgentPoolUpdateDecorator,
)
from azure.cli.command_modules.acs.custom import aks_agentpool_add, aks_agentpool_update
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockCmd
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.core.mock import DummyCli
from azure.cli.core.profiles import ResourceType


class ManagedGPUArgumentTestCase(unittest.TestCase):
    """Check the core command registration without loading aks-preview."""

    def _arguments(self, command_name):
        cli_ctx = DummyCli()
        cli_ctx.invocation = SimpleNamespace(
            data={"command_string": command_name}, parser=argparse.ArgumentParser()
        )
        loader = ContainerServiceCommandsLoader(cli_ctx)
        loader.load_command_table(command_name.split())
        loader.command_table[command_name].load_arguments()
        loader.load_arguments(command_name)
        return loader.argument_registry.arguments.get(command_name, {})

    def test_add_accepts_bare_true_false_and_omitted(self):
        settings = self._arguments("aks nodepool add")["enable_managed_gpu"].settings
        self.assertFalse(settings.get("is_preview", False))
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--enable-managed-gpu",
            **{key: settings[key] for key in ("action", "choices", "nargs", "default") if key in settings}
        )
        for arguments, expected in (
            ([], None),
            (["--enable-managed-gpu"], True),
            (["--enable-managed-gpu", "true"], True),
            (["--enable-managed-gpu", "false"], False),
        ):
            with self.subTest(arguments=arguments):
                self.assertIs(parser.parse_args(arguments).enable_managed_gpu, expected)

    def test_update_does_not_offer_management_mode_changes(self):
        self.assertNotIn("enable_managed_gpu", self._arguments("aks nodepool update"))

    def test_preview_only_gpu_options_are_not_promoted(self):
        arguments = self._arguments("aks nodepool add")
        for name in ("managed_gpu_driver_mode", "gpu_mig_strategy", "gpu_mig_profiles"):
            with self.subTest(name=name):
                self.assertNotIn(name, arguments)


class ManagedGPUProfileTestCase(unittest.TestCase):
    """Exercise the stable models and full command handlers with SDK calls mocked."""

    def setUp(self):
        self.cmd = MockCmd(MockCLI())
        self.client = Mock()
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
        self.models = AKSAgentPoolModels(
            self.cmd, self.resource_type, AgentPoolDecoratorMode.STANDALONE
        )
        self.pool_list = patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(list=Mock(return_value=[])),
        )
        self.pool_list.start()
        self.addCleanup(self.pool_list.stop)

    def _add(self, **kwargs):
        self.client.reset_mock()
        aks_agentpool_add(
            self.cmd, self.client, "test-rg", "test-cluster", "gpunp",
            node_vm_size="Standard_NC4as_T4_v3", no_wait=True, **kwargs
        )
        self.client.begin_create_or_update.assert_called_once()
        return self.client.begin_create_or_update.call_args.args[3]

    def test_add_serializes_managed_gpu_with_driver_install(self):
        for driver in (None, "Install"):
            with self.subTest(driver=driver):
                pool = self._add(enable_managed_gpu=True, gpu_driver=driver)
                self.assertEqual(pool.gpu_profile.as_dict(), {
                    "driver": "Install", "nvidia": {"managementMode": "Managed"}
                })

    def test_add_keeps_existing_defaults_and_driver_only_options(self):
        for enable_args in ({}, {"enable_managed_gpu": False}, {"enable_managed_gpu": None}):
            for driver in (None, "Install", "None"):
                with self.subTest(enable_args=enable_args, driver=driver):
                    pool = self._add(gpu_driver=driver, **enable_args)
                    if driver is None:
                        self.assertIsNone(pool.gpu_profile)
                    else:
                        self.assertEqual(pool.gpu_profile.as_dict(), {"driver": driver})

    def test_add_rejects_conflicting_driver_before_sdk_write(self):
        for driver in ("None", "none", "NONE"):
            with self.subTest(driver=driver):
                self.client.reset_mock()
                with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "requires GPU driver installation"):
                    self._add(enable_managed_gpu=True, gpu_driver=driver)
                self.client.begin_create_or_update.assert_not_called()

    def test_creation_context_preserves_attached_management_mode(self):
        for pool_mode in AgentPoolDecoratorMode:
            models = AKSAgentPoolModels(self.cmd, self.resource_type, pool_mode)
            for management_mode in ("Managed", "Unmanaged"):
                with self.subTest(pool_mode=pool_mode, management_mode=management_mode):
                    context = AKSAgentPoolContext(
                        self.cmd, AKSAgentPoolParamDict({}), models, DecoratorMode.CREATE, pool_mode
                    )
                    self.assertIsNone(context.get_enable_managed_gpu())
                    pool = models.UnifiedAgentPoolModel(
                        gpu_profile=models.GPUProfile(
                            nvidia=models.NvidiaGPUProfile(management_mode=management_mode)
                        )
                    )
                    context.attach_agentpool(pool)
                    self.assertIs(context.get_enable_managed_gpu(), management_mode == "Managed")

    def test_add_decorator_preserves_gpu_profile_and_unknown_fields(self):
        for pool_mode in AgentPoolDecoratorMode:
            with self.subTest(pool_mode=pool_mode):
                models = AKSAgentPoolModels(self.cmd, self.resource_type, pool_mode)
                profile = models.GPUProfile({
                    "driver": "Install",
                    "nvidia": {"managementMode": "Managed", "futureSetting": "keep"},
                })
                pool = models.UnifiedAgentPoolModel(gpu_profile=profile)
                decorator = AKSAgentPoolAddDecorator(
                    self.cmd, self.client, {"gpu_driver": "Install"}, self.resource_type, pool_mode
                )
                decorator.context.attach_agentpool(pool)
                before = copy.deepcopy(profile.as_dict())
                result = decorator.set_up_gpu_profile(pool)
                self.assertIs(result.gpu_profile, profile)
                self.assertEqual(result.gpu_profile.as_dict(), before)

    def test_update_driver_preserves_management_mode_and_unknown_fields(self):
        for pool_mode in AgentPoolDecoratorMode:
            for driver in (None, "Install"):
                with self.subTest(pool_mode=pool_mode, driver=driver):
                    models = AKSAgentPoolModels(self.cmd, self.resource_type, pool_mode)
                    profile = models.GPUProfile({
                        "driver": "Install",
                        "nvidia": {"managementMode": "Managed", "futureSetting": "keep"},
                    })
                    pool = models.UnifiedAgentPoolModel(gpu_profile=profile)
                    decorator = AKSAgentPoolUpdateDecorator(
                        self.cmd, self.client, {"gpu_driver": driver}, self.resource_type, pool_mode
                    )
                    decorator.context.attach_agentpool(pool)
                    before = copy.deepcopy(profile.as_dict())
                    result = decorator.update_gpu_profile(pool)
                    self.assertIs(result.gpu_profile, profile)
                    self.assertEqual(result.gpu_profile.as_dict(), before)

    def test_unrelated_updates_preserve_complete_gpu_profile(self):
        changes = (
            {},
            {"enable_cluster_autoscaler": True, "min_count": 1, "max_count": 3},
            {"update_cluster_autoscaler": True, "min_count": 2, "max_count": 5},
            {"disable_cluster_autoscaler": True},
            {"labels": {"team": "gpu"}},
            {"tags": {"team": "gpu"}},
            {"gpu_driver": "Install"},
        )
        for change in changes:
            with self.subTest(change=change):
                profile = self.models.GPUProfile({
                    "driver": "Install",
                    "nvidia": {"managementMode": "Managed", "futureSetting": "keep"},
                })
                pool = self.models.AgentPool(
                    name="gpunp", type="VirtualMachineScaleSets", mode="User",
                    count=2, enable_auto_scaling=not change.get("enable_cluster_autoscaler", False),
                    min_count=1, max_count=3,
                    gpu_profile=profile,
                )
                before = copy.deepcopy(profile.as_dict())
                self.client.reset_mock()
                self.client.get.return_value = pool
                aks_agentpool_update(
                    self.cmd, self.client, "test-rg", "test-cluster", "gpunp", no_wait=True, **change
                )
                self.client.begin_create_or_update.assert_called_once()
                submitted = self.client.begin_create_or_update.call_args.args[3]
                self.assertEqual(submitted.gpu_profile.as_dict(), before)


if __name__ == "__main__":
    unittest.main()

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import unittest
from unittest.mock import Mock, patch

from azure.cli.command_modules.acs._consts import (
    CONST_DEFAULT_NODE_OS_TYPE,
    CONST_DEFAULT_NODE_VM_SIZE,
    CONST_DEFAULT_WINDOWS_NODE_VM_SIZE,
    AgentPoolDecoratorMode,
    DecoratorEarlyExitException,
    DecoratorMode,
)
from azure.cli.command_modules.acs.agentpool_decorator import (
    AKSAgentPoolAddDecorator,
    AKSAgentPoolContext,
    AKSAgentPoolModels,
    AKSAgentPoolParamDict,
    AKSAgentPoolUpdateDecorator,
)
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockClient, MockCmd
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


class AKSAgentPoolModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE

    def test__init__(self):
        # load models directly (instead of through the `get_sdk` method provided by the cli component)
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES

        sdk_profile = AZURE_API_PROFILES["latest"][self.resource_type]
        api_version = sdk_profile.default_api_version
        module_name = "azure.mgmt.containerservice.v{}.models".format(api_version.replace("-", "_"))
        module = importlib.import_module(module_name)

        standalone_models = AKSAgentPoolModels(self.cmd, self.resource_type, AgentPoolDecoratorMode.STANDALONE)
        self.assertEqual(standalone_models.UnifiedAgentPoolModel, getattr(module, "AgentPool"))
        managedcluster_models = AKSAgentPoolModels(self.cmd, self.resource_type, AgentPoolDecoratorMode.MANAGED_CLUSTER)
        self.assertEqual(managedcluster_models.UnifiedAgentPoolModel, getattr(module, "ManagedClusterAgentPoolProfile"))


class AKSAgentPoolContextCommonTestCase(unittest.TestCase):
    def create_initialized_agentpool_instance(self, nodepool_name="nodepool1", **kwargs):
        # helper function to create a properly initialized agentpool instance
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            agentpool = self.models.UnifiedAgentPoolModel(name=nodepool_name)
        else:
            agentpool = self.models.UnifiedAgentPoolModel()
            agentpool.name = nodepool_name
        for key, value in kwargs.items():
            setattr(agentpool, key, value)
        return agentpool

    def common__init__(self):
        # fail on not passing dictionary-like parameters
        with self.assertRaises(CLIInternalError):
            AKSAgentPoolContext(self.cmd, [], self.models, DecoratorMode.CREATE, self.agentpool_decorator_mode)
        # fail on not passing decorator_mode with Enum type DecoratorMode
        with self.assertRaises(CLIInternalError):
            AKSAgentPoolContext(self.cmd, AKSAgentPoolParamDict({}), self.models, 1, self.agentpool_decorator_mode)

    def common_attach_agentpool(self):
        ctx_1 = AKSAgentPoolContext(
            self.cmd, AKSAgentPoolParamDict({}), self.models, DecoratorMode.CREATE, self.agentpool_decorator_mode
        )
        agentpool = self.create_initialized_agentpool_instance()
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.agentpool, agentpool)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_agentpool(agentpool)

    def common_validate_counts_in_autoscaler(self):
        ctx = AKSAgentPoolContext(
            self.cmd, AKSAgentPoolParamDict({}), self.models, DecoratorMode.CREATE, self.agentpool_decorator_mode
        )
        # default
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(3, False, None, None, DecoratorMode.CREATE)

        # custom value
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 1, 10, DecoratorMode.CREATE)

        # fail on min_count/max_count not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, None, None, DecoratorMode.CREATE)

        # fail on min_count > max_count
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 3, 1, DecoratorMode.CREATE)

        # fail on node_count < min_count in create mode
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 7, 10, DecoratorMode.CREATE)

        # skip node_count check in update mode
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 7, 10, DecoratorMode.UPDATE)
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(None, True, 7, 10, DecoratorMode.UPDATE)

        # fail on enable_cluster_autoscaler not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, False, 3, None, DecoratorMode.UPDATE)

    def common_get_resource_group_name(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"resource_group_name": "test_rg_name"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_resource_group_name(), "test_rg_name")

    def common_get_cluster_name(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"cluster_name": "test_cluster_name"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_cluster_name(), "test_cluster_name")

    def common_get_nodepool_name(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_name": "test_nodepool_name"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(),
        ):
            self.assertEqual(ctx_1.get_nodepool_name(), "test_nodepool_name")

        agentpool_1 = self.create_initialized_agentpool_instance("test_ap_name")
        ctx_1.attach_agentpool(agentpool_1)
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(),
        ):
            self.assertEqual(ctx_1.get_nodepool_name(), "test_ap_name")

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_name": "test_nodepool_name"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
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

    def common_get_max_surge(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "max_surge": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_max_surge(), None)

        upgrade_settings_1 = self.models.AgentPoolUpgradeSettings(max_surge="test_max_surge")
        agentpool_1 = self.create_initialized_agentpool_instance(upgrade_settings=upgrade_settings_1)
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(ctx_1.get_max_surge(), "test_max_surge")

    def common_get_node_count_and_enable_cluster_autoscaler_min_max_count(
        self,
    ):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "node_count": 3,
                    "enable_cluster_autoscaler": False,
                    "min_count": None,
                    "max_count": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(
            ctx_1.get_node_count_and_enable_cluster_autoscaler_min_max_count(),
            (3, False, None, None),
        )
        agentpool = self.create_initialized_agentpool_instance(
            count=5,
            enable_auto_scaling=True,
            min_count=1,
            max_count=10,
        )
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(
            ctx_1.get_node_count_and_enable_cluster_autoscaler_min_max_count(),
            (5, True, 1, 10),
        )

    def common_get_node_osdisk_size(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"node_osdisk_size": 0}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_node_osdisk_size(), 0)
        agentpool = self.create_initialized_agentpool_instance(os_disk_size_gb=10)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_node_osdisk_size(), 10)

    def common_get_node_osdisk_type(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"node_osdisk_type": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_node_osdisk_type(), None)
        agentpool = self.create_initialized_agentpool_instance(os_disk_type="test_mc_node_osdisk_type")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_node_osdisk_type(), "test_mc_node_osdisk_type")

    def common_get_aks_custom_headers(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "aks_custom_headers": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_aks_custom_headers(), {})

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "aks_custom_headers": "abc=def,xyz=123",
                }
            ),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_2.get_aks_custom_headers(), {"abc": "def", "xyz": "123"})

    def common_get_no_wait(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"no_wait": False}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_no_wait(), False)


class AKSAgentPoolContextStandaloneModeTestCase(AKSAgentPoolContextCommonTestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.STANDALONE
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)

    def test__init__(self):
        self.common__init__()

    def test_attach_agentpool(self):
        self.common_attach_agentpool()

    def test_validate_counts_in_autoscaler(self):
        self.common_validate_counts_in_autoscaler()

    def test_get_resource_group_name(self):
        self.common_get_resource_group_name()

    def test_get_cluster_name(self):
        self.common_get_cluster_name()

    def test_get_nodepool_name(self):
        self.common_get_nodepool_name()

    def test_get_max_surge(self):
        self.common_get_max_surge()

    def test_get_node_count_and_enable_cluster_autoscaler_min_max_count(
        self,
    ):
        self.common_get_node_count_and_enable_cluster_autoscaler_min_max_count()

    def test_get_node_osdisk_size(self):
        self.common_get_node_osdisk_size()

    def test_get_node_osdisk_type(self):
        self.common_get_node_osdisk_type()

    def test_get_aks_custom_headers(self):
        self.common_get_aks_custom_headers()

    def test_get_no_wait(self):
        self.common_get_no_wait()


class AKSAgentPoolContextManagedClusterModeTestCase(AKSAgentPoolContextCommonTestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.MANAGED_CLUSTER
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)

    def test__init__(self):
        self.common__init__()

    def test_attach_agentpool(self):
        self.common_attach_agentpool()

    def test_validate_counts_in_autoscaler(self):
        self.common_validate_counts_in_autoscaler()

    def test_get_resource_group_name(self):
        self.common_get_resource_group_name()

    def test_get_cluster_name(self):
        self.common_get_cluster_name()

    def test_get_nodepool_name(self):
        self.common_get_nodepool_name()

    def test_get_max_surge(self):
        self.common_get_max_surge()

    def test_get_node_count_and_enable_cluster_autoscaler_min_max_count(
        self,
    ):
        self.common_get_node_count_and_enable_cluster_autoscaler_min_max_count()

    def test_get_node_osdisk_size(self):
        self.common_get_node_osdisk_size()

    def test_get_node_osdisk_type(self):
        self.common_get_node_osdisk_type()

    def test_get_aks_custom_headers(self):
        self.common_get_aks_custom_headers()

    def test_get_no_wait(self):
        self.common_get_no_wait()


class AKSAgentPoolAddDecoratorCommonTestCase(unittest.TestCase):
    def create_initialized_agentpool_instance(self, nodepool_name="nodepool1", **kwargs):
        # helper function to create a properly initialized agentpool instance
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            agentpool = self.models.UnifiedAgentPoolModel(name=nodepool_name)
        else:
            agentpool = self.models.UnifiedAgentPoolModel()
            agentpool.name = nodepool_name
        for key, value in kwargs.items():
            setattr(agentpool, key, value)
        return agentpool

    def common_ensure_agentpool(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong mc object
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_agentpool(None)
        agentpool_1 = self.create_initialized_agentpool_instance()
        # fail on inconsistent mc with internal context
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_agentpool(agentpool_1)

    def common_init_agentpool(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {"nodepool_name": "test_nodepool_name"},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(),
        ):
            dec_agentpool_1 = dec_1.init_agentpool()
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance("test_nodepool_name")
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)
        self.assertEqual(dec_agentpool_1, dec_1.context.agentpool)

    def common_set_up_upgrade_settings(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {"max_surge": "test_max_surge"},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_upgrade_settings(None)
        agentpool_1 = self.create_initialized_agentpool_instance()
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_upgrade_settings(agentpool_1)
        ground_truth_upgrade_settings_1 = self.models.AgentPoolUpgradeSettings(max_surge="test_max_surge")
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            upgrade_settings=ground_truth_upgrade_settings_1
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

    def common_construct_default_agentpool(self):
        import inspect

        from azure.cli.command_modules.acs.custom import aks_agentpool_add

        optional_params = {}
        positional_params = []
        for _, v in inspect.signature(aks_agentpool_add).parameters.items():
            if v.default != v.empty:
                optional_params[v.name] = v.default
            else:
                positional_params.append(v.name)
        ground_truth_positional_params = [
            "cmd",
            "client",
            "resource_group_name",
            "cluster_name",
            "nodepool_name",
        ]
        self.assertEqual(positional_params, ground_truth_positional_params)

        # prepare a dictionary of default parameters
        raw_param_dict = {
            "resource_group_name": "test_rg_name",
            "cluster_name": "test_cluster_name",
            "nodepool_name": "test_nodepool_name",
        }
        raw_param_dict.update(optional_params)

        # default value in `aks_create`
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            raw_param_dict,
            self.resource_type,
            self.agentpool_decorator_mode,
        )

        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(),
        ):
            dec_agentpool_1 = dec_1.construct_default_agentpool_profile()

        upgrade_settings_1 = self.models.AgentPoolUpgradeSettings()
        agentpool_1 = self.create_initialized_agentpool_instance(
            upgrade_settings=upgrade_settings_1, count=3, enable_auto_scaling=False, os_disk_size_gb=0
        )
        agentpool_1.name = "test_nodepool_name"
        agentpool_1.os_type = CONST_DEFAULT_NODE_OS_TYPE
        agentpool_1.vm_size = CONST_DEFAULT_NODE_VM_SIZE
        self.assertEqual(dec_agentpool_1, agentpool_1)
        dec_1.context.raw_param.print_usage_statistics()


class AKSAgentPoolAddDecoratorStandaloneModeTestCase(AKSAgentPoolAddDecoratorCommonTestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.STANDALONE
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)
        self.client = MockClient()

    def test_ensure_agentpool(self):
        self.common_ensure_agentpool()

    def test_init_agentpool(self):
        self.common_init_agentpool()

    def test_set_up_upgrade_settings(self):
        self.common_set_up_upgrade_settings()

    def test_construct_default_agentpool(self):
        self.common_construct_default_agentpool()


class AKSAgentPoolAddDecoratorManagedClusterModeTestCase(AKSAgentPoolAddDecoratorCommonTestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.MANAGED_CLUSTER
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)
        self.client = MockClient()

    def test_ensure_agentpool(self):
        self.common_ensure_agentpool()

    def test_init_agentpool(self):
        self.common_init_agentpool()

    def test_set_up_upgrade_settings(self):
        self.common_set_up_upgrade_settings()

    def test_construct_default_agentpool(self):
        self.common_construct_default_agentpool()


class AKSAgentPoolUpdateDecoratorTestCase(unittest.TestCase):
    def test(self):
        pass


if __name__ == "__main__":
    unittest.main()

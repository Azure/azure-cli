# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import unittest
from unittest.mock import Mock, patch

from azure.cli.command_modules.acs._consts import (
    CONST_AVAILABILITY_SET,
    CONST_DEFAULT_NODE_OS_TYPE,
    CONST_DEFAULT_NODE_VM_SIZE,
    CONST_DEFAULT_WINDOWS_NODE_VM_SIZE,
    CONST_NODEPOOL_MODE_SYSTEM,
    CONST_NODEPOOL_MODE_USER,
    CONST_SCALE_DOWN_MODE_DEALLOCATE,
    CONST_SCALE_DOWN_MODE_DELETE,
    CONST_SCALE_SET_PRIORITY_REGULAR,
    CONST_SCALE_SET_PRIORITY_SPOT,
    CONST_SPOT_EVICTION_POLICY_DEALLOCATE,
    CONST_SPOT_EVICTION_POLICY_DELETE,
    CONST_VIRTUAL_MACHINE_SCALE_SETS,
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
from azure.cli.command_modules.acs.tests.latest.utils import get_test_data_file_path
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import get_file_json


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
    def _remove_defaults_in_agentpool(self, agentpool):
        self.defaults_in_agentpool = {}
        for attr_name, attr_value in vars(agentpool).items():
            if not attr_name.startswith("_") and attr_name != "name" and attr_value is not None:
                self.defaults_in_agentpool[attr_name] = attr_value
                setattr(agentpool, attr_name, None)
        return agentpool

    def _restore_defaults_in_agentpool(self, agentpool):
        for key, value in self.defaults_in_agentpool.items():
            if getattr(agentpool, key, None) is None:
                setattr(agentpool, key, value)
        return agentpool

    def create_initialized_agentpool_instance(
        self, nodepool_name="nodepool1", remove_defaults=True, restore_defaults=True, **kwargs
    ):
        """Helper function to create a properly initialized agentpool instance.

        :return: the AgentPool object
        """
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            agentpool = self.models.UnifiedAgentPoolModel(name=nodepool_name)
        else:
            agentpool = self.models.UnifiedAgentPoolModel()
            agentpool.name = nodepool_name

        # remove defaults
        if remove_defaults:
            self._remove_defaults_in_agentpool(agentpool)

        # set properties
        for key, value in kwargs.items():
            setattr(agentpool, key, value)

        # resote defaults
        if restore_defaults:
            self._restore_defaults_in_agentpool(agentpool)
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
        self.assertEqual(ctx_1.existing_agentpool, None)

    def common_attach_existing_agentpool(self):
        ctx_1 = AKSAgentPoolContext(
            self.cmd, AKSAgentPoolParamDict({}), self.models, DecoratorMode.UPDATE, self.agentpool_decorator_mode
        )
        agentpool = self.create_initialized_agentpool_instance()
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.existing_agentpool, agentpool)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_existing_agentpool(agentpool)

    def common_attach_agentpools(self):
        ctx_1 = AKSAgentPoolContext(
            self.cmd, AKSAgentPoolParamDict({}), self.models, DecoratorMode.CREATE, self.agentpool_decorator_mode
        )
        agentpool_1 = self.create_initialized_agentpool_instance()
        agentpool_2 = self.create_initialized_agentpool_instance()
        agentpools = [agentpool_1, agentpool_2]
        ctx_1.attach_agentpools(agentpools)
        self.assertEqual(ctx_1._agentpools, agentpools)
        # fail on attach again
        with self.assertRaises(CLIInternalError):
            ctx_1.attach_agentpools(agentpools)

    def common_validate_counts_in_autoscaler(self):
        ctx = AKSAgentPoolContext(
            self.cmd, AKSAgentPoolParamDict({}), self.models, DecoratorMode.CREATE, self.agentpool_decorator_mode
        )
        # default
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(3, False, None, None, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.CREATE)

        # custom value
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 1, 10, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.CREATE)

        # fail on min_count/max_count not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, None, None, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.CREATE)

        # fail on min_count > max_count
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 3, 1, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.CREATE)

        # fail on node_count < min_count in create mode
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 7, 10, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.CREATE)

        # skip node_count check in update mode
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, True, 7, 10, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.UPDATE)
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(None, True, 7, 10, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.UPDATE)

        # fail on enable_cluster_autoscaler not specified
        with self.assertRaises(RequiredArgumentMissingError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(5, False, 3, None, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.UPDATE)

        # min_count set to 0 for user node pools
        ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(0, True, 0, 1, CONST_NODEPOOL_MODE_USER, DecoratorMode.CREATE)

        # fail on min_count < 1 for system node pools
        with self.assertRaises(InvalidArgumentValueError):
            ctx._AKSAgentPoolContext__validate_counts_in_autoscaler(1, True, 0, 1, CONST_NODEPOOL_MODE_SYSTEM, DecoratorMode.CREATE)

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
            AKSAgentPoolParamDict({"cluster_name": "test_cluster_name", "name": "test_name"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_1.get_cluster_name(), "test_name")
        else:
            self.assertEqual(ctx_1.get_cluster_name(), "test_cluster_name")

    def common_get_snapshot_id(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "snapshot_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_snapshot_id(), None)
        creation_data = self.models.CreationData(source_resource_id="test_source_resource_id")
        agentpool = self.create_initialized_agentpool_instance(creation_data=creation_data)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_snapshot_id(), "test_source_resource_id")

    def common_get_snapshot(self):
        # custom value
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "snapshot_id": "test_source_resource_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock()
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_1.get_snapshot(), mock_snapshot)
        # test cache
        self.assertEqual(ctx_1.get_snapshot(), mock_snapshot)

    def common_get_host_group_id(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "host_group_id": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_host_group_id(), None)
        # custom
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "host_group_id": "test_host_group_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_host_group_id(), "test_host_group_id")

    def common_get_crg_id(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"crg_id": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_crg_id(), None)
        # custom
        agentpool_1 = self.create_initialized_agentpool_instance(
            capacity_reservation_group_id="test_crg_id"
        )
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(ctx_1.get_crg_id(), "test_crg_id")

    def common_get_kubernetes_version(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"kubernetes_version": ""}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_kubernetes_version(), "")
        agentpool = self.create_initialized_agentpool_instance(orchestrator_version="test_kubernetes_version")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_kubernetes_version(), "test_kubernetes_version")

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"kubernetes_version": "", "snapshot_id": "test_snapshot_id"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(kubernetes_version="test_kubernetes_version")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_2.get_kubernetes_version(), "test_kubernetes_version")

        # custom value
        ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "kubernetes_version": "custom_kubernetes_version",
                    "snapshot_id": "test_snapshot_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(kubernetes_version="test_kubernetes_version")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_3.get_kubernetes_version(), "custom_kubernetes_version")

    def common_get_node_vm_size(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"node_vm_size": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_node_vm_size(), CONST_DEFAULT_NODE_VM_SIZE)
        agentpool = self.create_initialized_agentpool_instance(vm_size="Standard_ABCD_v2")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_node_vm_size(), "Standard_ABCD_v2")

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"node_vm_size": None, "snapshot_id": "test_snapshot_id"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(vm_size="test_vm_size")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_2.get_node_vm_size(), "test_vm_size")

        # custom value
        ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "node_vm_size": "custom_node_vm_size",
                    "snapshot_id": "test_snapshot_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(vm_size="test_vm_size")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_3.get_node_vm_size(), "custom_node_vm_size")

        # custom value
        ctx_4 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "node_vm_size": None,
                    "os_type": "WINDOWS",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            # fail on windows os type for ManagedCluster mode (aks create)
            with self.assertRaises(InvalidArgumentValueError):
                ctx_4.get_node_vm_size()
        else:
            self.assertEqual(ctx_4.get_node_vm_size(), CONST_DEFAULT_WINDOWS_NODE_VM_SIZE)

    def common_get_os_type(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"os_type": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_os_type(), CONST_DEFAULT_NODE_OS_TYPE)
        agentpool = self.create_initialized_agentpool_instance(os_type="test_os_type")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_os_type(), "test_os_type")

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"os_type": None, "snapshot_id": "test_snapshot_id"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(os_type="test_os_type")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_2.get_os_type(), "test_os_type")

        # custom value
        ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "os_type": "custom_os_type",
                    "snapshot_id": "test_snapshot_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(os_type="test_os_type")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_3.get_os_type(), "custom_os_type")

        # custom value
        ctx_4 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "os_type": "windows",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            # fail on windows os type for ManagedCluster mode (aks create)
            with self.assertRaises(InvalidArgumentValueError):
                ctx_4.get_os_type()
        else:
            self.assertEqual(ctx_4.get_os_type(), "windows")

    def common_get_os_sku(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"os_sku": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_os_sku(), None)
        agentpool = self.create_initialized_agentpool_instance(os_sku="test_os_sku")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_os_sku(), "test_os_sku")

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"os_sku": None, "snapshot_id": "test_snapshot_id"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(os_sku="test_os_sku")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_2.get_os_sku(), "test_os_sku")

        # custom value
        ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "os_sku": "custom_os_sku",
                    "snapshot_id": "test_snapshot_id",
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        mock_snapshot = Mock(os_sku="test_os_sku")
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot,
        ):
            self.assertEqual(ctx_3.get_os_sku(), "custom_os_sku")

    def common_get_vnet_subnet_id(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"vnet_subnet_id": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_vnet_subnet_id(), None)
        agentpool = self.create_initialized_agentpool_instance(vnet_subnet_id="test_vnet_subnet_id")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_vnet_subnet_id(), "test_vnet_subnet_id")

    def common_get_pod_subnet_id(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"pod_subnet_id": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_pod_subnet_id(), None)
        agentpool = self.create_initialized_agentpool_instance(pod_subnet_id="test_pod_subnet_id")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_pod_subnet_id(), "test_pod_subnet_id")

    def common_get_enable_node_public_ip(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"enable_node_public_ip": False}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_enable_node_public_ip(), False)
        agentpool = self.create_initialized_agentpool_instance(enable_node_public_ip=True)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_enable_node_public_ip(), True)

    def common_get_node_public_ip_prefix_id(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"node_public_ip_prefix_id": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_node_public_ip_prefix_id(), None)
        agentpool = self.create_initialized_agentpool_instance(node_public_ip_prefix_id="test_node_public_ip_prefix_id")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_node_public_ip_prefix_id(), "test_node_public_ip_prefix_id")

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

    def common_get_update_enable_disable_cluster_autoscaler_and_min_max_count(
        self,
    ):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "update_cluster_autoscaler": False,
                    "enable_cluster_autoscaler": False,
                    "disable_cluster_autoscaler": False,
                    "min_count": None,
                    "max_count": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        agentpool_1 = self.create_initialized_agentpool_instance(count=3)
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(
            ctx_1.get_update_enable_disable_cluster_autoscaler_and_min_max_count(),
            (False, False, False, None, None),
        )

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "update_cluster_autoscaler": True,
                    "enable_cluster_autoscaler": False,
                    "disable_cluster_autoscaler": False,
                    "min_count": None,
                    "max_count": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        agentpool_2 = self.create_initialized_agentpool_instance(count=3)
        ctx_2.attach_agentpool(agentpool_2)
        ctx_2._agentpools = [agentpool_2, agentpool_2]
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            # fail on multi-agent pool
            with self.assertRaises(ArgumentUsageError):
                ctx_2.get_update_enable_disable_cluster_autoscaler_and_min_max_count()
        else:
            # fail on min count and max count not specifed
            with self.assertRaises(RequiredArgumentMissingError):
                ctx_2.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "update_cluster_autoscaler": False,
                    "enable_cluster_autoscaler": True,
                    "disable_cluster_autoscaler": True,
                    "min_count": None,
                    "max_count": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        agentpool_3 = self.create_initialized_agentpool_instance(count=3)
        ctx_3.attach_agentpool(agentpool_3)
        # fail on mutually exclusive update_cluster_autoscaler, enable_cluster_autoscaler and disable_cluster_autoscaler
        with self.assertRaises(MutuallyExclusiveArgumentError):
            ctx_3.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_4 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "update_cluster_autoscaler": False,
                    "enable_cluster_autoscaler": True,
                    "disable_cluster_autoscaler": False,
                    "min_count": 1,
                    "max_count": 5,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        agentpool_4 = self.create_initialized_agentpool_instance(count=3, enable_auto_scaling=True)
        ctx_4.attach_agentpool(agentpool_4)
        # fail on cluster autoscaler already enabled
        with self.assertRaises(DecoratorEarlyExitException):
            ctx_4.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_5 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "update_cluster_autoscaler": True,
                    "enable_cluster_autoscaler": False,
                    "disable_cluster_autoscaler": False,
                    "min_count": 1,
                    "max_count": 5,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        agentpool_5 = self.create_initialized_agentpool_instance(count=3, enable_auto_scaling=False)
        ctx_5.attach_agentpool(agentpool_5)
        # fail on cluster autoscaler not enabled
        with self.assertRaises(InvalidArgumentValueError):
            ctx_5.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

        # custom value
        ctx_6 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(
                {
                    "update_cluster_autoscaler": False,
                    "enable_cluster_autoscaler": False,
                    "disable_cluster_autoscaler": True,
                    "min_count": None,
                    "max_count": None,
                }
            ),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )

        agentpool_6 = self.create_initialized_agentpool_instance(count=3, enable_auto_scaling=False)
        ctx_6.attach_agentpool(agentpool_6)
        # fail on cluster autoscaler already disabled
        with self.assertRaises(DecoratorEarlyExitException):
            ctx_6.get_update_enable_disable_cluster_autoscaler_and_min_max_count()

    def common_get_priority(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"priority": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_priority(), CONST_SCALE_SET_PRIORITY_REGULAR)
        agentpool = self.create_initialized_agentpool_instance(scale_set_priority="test_priority")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_priority(), "test_priority")

    def common_get_eviction_policy(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"eviction_policy": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_eviction_policy(), CONST_SPOT_EVICTION_POLICY_DELETE)
        agentpool = self.create_initialized_agentpool_instance(scale_set_eviction_policy="test_eviction_policy")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_eviction_policy(), "test_eviction_policy")

    def common_get_spot_max_price(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"spot_max_price": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_spot_max_price(), -1)
        agentpool = self.create_initialized_agentpool_instance(spot_max_price=1.2345)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_spot_max_price(), 1.2345)

    def common_get_nodepool_labels(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_labels": "test_nodepool_labels", "labels": "test_labels"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_1.get_nodepool_labels(), "test_nodepool_labels")
        else:
            self.assertEqual(ctx_1.get_nodepool_labels(), "test_labels")
        agentpool = self.create_initialized_agentpool_instance(node_labels={"key1": "value1", "key2": "value2"})
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_nodepool_labels(), {"key1": "value1", "key2": "value2"})

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_labels": "test_nodepool_labels", "labels": "test_labels"}),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_2.get_nodepool_labels(), "test_nodepool_labels")
        else:
            self.assertEqual(ctx_2.get_nodepool_labels(), "test_labels")
        agentpool_2 = self.create_initialized_agentpool_instance(node_labels={"key1": "value1", "key2": "value2"})
        ctx_2.attach_agentpool(agentpool_2)
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_2.get_nodepool_labels(), "test_nodepool_labels")
        else:
            self.assertEqual(ctx_2.get_nodepool_labels(), "test_labels")

    def common_get_nodepool_tags(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_tags": "test_nodepool_tags", "tags": "test_tags"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_1.get_nodepool_tags(), "test_nodepool_tags")
        else:
            self.assertEqual(ctx_1.get_nodepool_tags(), "test_tags")
        agentpool = self.create_initialized_agentpool_instance(tags={})
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_nodepool_tags(), {})

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_tags": "test_nodepool_tags", "tags": "test_tags"}),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_2.get_nodepool_tags(), "test_nodepool_tags")
        else:
            self.assertEqual(ctx_2.get_nodepool_tags(), "test_tags")
        agentpool_2 = self.create_initialized_agentpool_instance(tags={})
        ctx_2.attach_agentpool(agentpool_2)
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_2.get_nodepool_tags(), "test_nodepool_tags")
        else:
            self.assertEqual(ctx_2.get_nodepool_tags(), "test_tags")

    def common_get_node_taints(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_taints": "abc=xyz:123,123=456:abc", "node_taints": "abc2=xyz2:123"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.assertEqual(ctx_1.get_node_taints(), ["abc=xyz:123", "123=456:abc"])
        else:
            self.assertEqual(ctx_1.get_node_taints(), ["abc2=xyz2:123"])
        agentpool = self.create_initialized_agentpool_instance(node_taints=[])
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_node_taints(), [])

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"nodepool_taints": "", "node_taints": ""}),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_2.get_node_taints(), [])
        agentpool_2 = self.create_initialized_agentpool_instance(node_taints=["abc=xyz:123", "123=456:abc"])
        ctx_2.attach_agentpool(agentpool_2)
        self.assertEqual(ctx_2.get_node_taints(), [])

    def common_get_node_osdisk_size(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"node_osdisk_size": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_node_osdisk_size(), None)
        agentpool = self.create_initialized_agentpool_instance(os_disk_size_gb=30)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_node_osdisk_size(), 30)

        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"node_osdisk_size": 0}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_2.get_node_osdisk_size(), 0)
        agentpool = self.create_initialized_agentpool_instance(os_disk_size_gb=100)
        ctx_2.attach_agentpool(agentpool)
        self.assertEqual(ctx_2.get_node_osdisk_size(), 100)

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
        agentpool = self.create_initialized_agentpool_instance(os_disk_type="test_node_osdisk_type")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_node_osdisk_type(), "test_node_osdisk_type")

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

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"max_surge": "test_max_surge"}),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_2.get_max_surge(), "test_max_surge")
        upgrade_settings_2 = self.models.AgentPoolUpgradeSettings(max_surge="test_ap_max_surge")
        agentpool_2 = self.create_initialized_agentpool_instance(upgrade_settings=upgrade_settings_2)
        ctx_2.attach_agentpool(agentpool_2)
        self.assertEqual(ctx_2.get_max_surge(), "test_max_surge")

    def common_get_vm_set_type(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"vm_set_type": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_vm_set_type(), CONST_VIRTUAL_MACHINE_SCALE_SETS)
        agentpool = self.create_initialized_agentpool_instance(
            type=CONST_AVAILABILITY_SET, type_properties_type=CONST_AVAILABILITY_SET
        )
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_vm_set_type(), CONST_AVAILABILITY_SET)

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"vm_set_type": "test_vm_set_type"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        # fail on invalid vm_set_type
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_vm_set_type()

    def common_get_ppg(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"ppg": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_ppg(), None)
        agentpool = self.create_initialized_agentpool_instance(
            proximity_placement_group_id="test_proximity_placement_group_id"
        )
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_ppg(), "test_proximity_placement_group_id")

    def common_get_enable_encryption_at_host(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"enable_encryption_at_host": False}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_enable_encryption_at_host(), False)
        agentpool = self.create_initialized_agentpool_instance(enable_encryption_at_host=True)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_enable_encryption_at_host(), True)

    def common_get_enable_ultra_ssd(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"enable_ultra_ssd": False}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_enable_ultra_ssd(), False)
        agentpool = self.create_initialized_agentpool_instance(enable_ultra_ssd=True)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_enable_ultra_ssd(), True)

    def common_get_enable_fips_image(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"enable_fips_image": False}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_enable_fips_image(), False)
        agentpool = self.create_initialized_agentpool_instance(enable_fips=True)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_enable_fips_image(), True)

    def common_get_zones(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"zones": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_zones(), None)
        agentpool = self.create_initialized_agentpool_instance(availability_zones=[1, 2, 3])
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_zones(), [1, 2, 3])

    def common_get_max_pods(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"max_pods": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_max_pods(), None)
        agentpool = self.create_initialized_agentpool_instance(max_pods=110)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_max_pods(), 110)

        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"max_pods": 0}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_2.get_max_pods(), None)
        agentpool = self.create_initialized_agentpool_instance(max_pods=250)
        ctx_2.attach_agentpool(agentpool)
        self.assertEqual(ctx_2.get_max_pods(), 250)

    def common_get_mode(self):
        # default
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            ctx_1 = AKSAgentPoolContext(
                self.cmd,
                AKSAgentPoolParamDict({"mode": None}),
                self.models,
                DecoratorMode.CREATE,
                self.agentpool_decorator_mode,
            )
            self.assertEqual(ctx_1.get_mode(), CONST_NODEPOOL_MODE_SYSTEM)
        else:
            ctx_1 = AKSAgentPoolContext(
                self.cmd,
                AKSAgentPoolParamDict({"mode": CONST_NODEPOOL_MODE_USER}),
                self.models,
                DecoratorMode.CREATE,
                self.agentpool_decorator_mode,
            )
            self.assertEqual(ctx_1.get_mode(), CONST_NODEPOOL_MODE_USER)
        agentpool = self.create_initialized_agentpool_instance(mode="test_mode")
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_mode(), "test_mode")

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"mode": "test_mode"}),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_2.get_mode(), "test_mode")
        agentpool_2 = self.create_initialized_agentpool_instance(mode="test_ap_mode")
        ctx_2.attach_agentpool(agentpool_2)
        self.assertEqual(ctx_2.get_mode(), "test_mode")

    def common_get_scale_down_mode(self):
        # default
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            ctx_1 = AKSAgentPoolContext(
                self.cmd,
                AKSAgentPoolParamDict({"scale_down_mode": None}),
                self.models,
                DecoratorMode.CREATE,
                self.agentpool_decorator_mode,
            )
            self.assertEqual(ctx_1.get_scale_down_mode(), None)
        else:
            ctx_1 = AKSAgentPoolContext(
                self.cmd,
                AKSAgentPoolParamDict({"scale_down_mode": CONST_SCALE_DOWN_MODE_DELETE}),
                self.models,
                DecoratorMode.CREATE,
                self.agentpool_decorator_mode,
            )
            self.assertEqual(ctx_1.get_scale_down_mode(), CONST_SCALE_DOWN_MODE_DELETE)
        agentpool = self.create_initialized_agentpool_instance(scale_down_mode=CONST_SCALE_DOWN_MODE_DEALLOCATE)
        ctx_1.attach_agentpool(agentpool)
        self.assertEqual(ctx_1.get_scale_down_mode(), CONST_SCALE_DOWN_MODE_DEALLOCATE)

        # custom
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"scale_down_mode": "test_scale_down_mode"}),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_2.get_scale_down_mode(), "test_scale_down_mode")
        agentpool_2 = self.create_initialized_agentpool_instance(scale_down_mode="test_ap_scale_down_mode")
        ctx_2.attach_agentpool(agentpool_2)
        self.assertEqual(ctx_2.get_scale_down_mode(), "test_scale_down_mode")

    def common_get_kubelet_config(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"kubelet_config": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_kubelet_config(), None)
        agentpool_1 = self.create_initialized_agentpool_instance(
            kubelet_config=self.models.KubeletConfig(pod_max_pids=100)
        )
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(
            ctx_1.get_kubelet_config(),
            self.models.KubeletConfig(pod_max_pids=100),
        )

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"kubelet_config": "fake-path"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        # fail on invalid file path
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_kubelet_config()

        # custom value
        ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"kubelet_config": get_test_data_file_path("invalidconfig.json")}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        # fail on invalid file content
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_kubelet_config()

    def common_get_linux_os_config(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"linux_os_config": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_linux_os_config(), None)
        agentpool_1 = self.create_initialized_agentpool_instance(
            linux_os_config=self.models.LinuxOSConfig(swap_file_size_mb=200)
        )
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(
            ctx_1.get_linux_os_config(),
            self.models.LinuxOSConfig(swap_file_size_mb=200),
        )

        # custom value
        ctx_2 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"linux_os_config": "fake-path"}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        # fail on invalid file path
        with self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_linux_os_config()

        # custom value
        ctx_3 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"linux_os_config": get_test_data_file_path("invalidconfig.json")}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        # fail on invalid file content
        with self.assertRaises(InvalidArgumentValueError):
            ctx_3.get_linux_os_config()

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

    def common_get_gpu_instance_profile(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"gpu_instance_profile": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_gpu_instance_profile(), None)
        agentpool_1 = self.create_initialized_agentpool_instance(gpu_instance_profile="test_gpu_instance_profile")
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(ctx_1.get_gpu_instance_profile(), "test_gpu_instance_profile")

    def common_get_drain_timeout(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({"drain_timeout": None}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_drain_timeout(), None)
        agentpool_1 = self.create_initialized_agentpool_instance(upgrade_settings=self.models.AgentPoolUpgradeSettings(drain_timeout_in_minutes=123))
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(ctx_1.get_drain_timeout(), 123)

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

    def test_attach_existing_agentpool(self):
        self.common_attach_existing_agentpool()

    def test_attach_agentpools(self):
        self.common_attach_agentpools()

    def test_validate_counts_in_autoscaler(self):
        self.common_validate_counts_in_autoscaler()

    def test_get_resource_group_name(self):
        self.common_get_resource_group_name()

    def test_get_cluster_name(self):
        self.common_get_cluster_name()

    def test_get_nodepool_name(self):
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
            return_value=Mock(list=Mock(return_value=[])),
        ):
            self.assertEqual(ctx_1.get_nodepool_name(), "test_nodepool_name")

        agentpool_1 = self.create_initialized_agentpool_instance("test_ap_name")
        ctx_1.attach_agentpool(agentpool_1)
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(list=Mock(return_value=[])),
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
            return_value=mock_agentpool_operations,
        ), self.assertRaises(InvalidArgumentValueError):
            ctx_2.get_nodepool_name()

    def test_get_snapshot_id(self):
        self.common_get_snapshot_id()

    def test_get_snapshot(self):
        self.common_get_snapshot()

    def test_get_host_group_id(self):
        self.common_get_host_group_id()

    def test_get_kubernetes_version(self):
        self.common_get_kubernetes_version()

    def test_get_node_vm_size(self):
        self.common_get_node_vm_size()

    def test_get_os_type(self):
        self.common_get_os_type()

    def test_get_os_sku(self):
        self.common_get_os_sku()

    def test_get_vnet_subnet_id(self):
        self.common_get_vnet_subnet_id()

    def test_get_pod_subnet_id(self):
        self.common_get_pod_subnet_id()

    def test_get_enable_node_public_ip(self):
        self.common_get_enable_node_public_ip()

    def test_get_node_public_ip_prefix_id(self):
        self.common_get_node_public_ip_prefix_id()

    def test_get_node_count_and_enable_cluster_autoscaler_min_max_count(
        self,
    ):
        self.common_get_node_count_and_enable_cluster_autoscaler_min_max_count()

    def test_get_update_enable_disable_cluster_autoscaler_and_min_max_count(self):
        self.common_get_update_enable_disable_cluster_autoscaler_and_min_max_count()

    def test_get_priority(self):
        self.common_get_priority()

    def test_get_eviction_policy(self):
        self.common_get_eviction_policy()

    def test_get_spot_max_price(self):
        self.common_get_spot_max_price()

    def test_get_nodepool_labels(self):
        self.common_get_nodepool_labels()

    def test_get_nodepool_tags(self):
        self.common_get_nodepool_tags()

    def test_get_node_taints(self):
        self.common_get_node_taints()

    def test_get_node_osdisk_size(self):
        self.common_get_node_osdisk_size()

    def test_get_node_osdisk_type(self):
        self.common_get_node_osdisk_type()

    def test_get_max_surge(self):
        self.common_get_max_surge()

    def test_get_vm_set_type(self):
        self.common_get_vm_set_type()

    def test_get_ppg(self):
        self.common_get_ppg()

    def test_get_enable_encryption_at_host(self):
        self.common_get_enable_encryption_at_host()

    def test_get_enable_ultra_ssd(self):
        self.common_get_enable_ultra_ssd()

    def test_get_enable_fips_image(self):
        self.common_get_enable_fips_image()

    def test_get_zones(self):
        self.common_get_zones()

    def test_get_max_pods(self):
        self.common_get_max_pods()

    def test_get_mode(self):
        self.common_get_mode()

    def test_get_scale_down_mode(self):
        self.common_get_scale_down_mode()

    def test_get_kubelet_config(self):
        self.common_get_kubelet_config()

    def test_get_linux_os_config(self):
        self.common_get_linux_os_config()

    def test_get_aks_custom_headers(self):
        self.common_get_aks_custom_headers()

    def test_get_no_wait(self):
        self.common_get_no_wait()

    def test_get_gpu_instance_profile(self):
        self.common_get_gpu_instance_profile()

    def test_get_drain_timeout(self):
        self.common_get_drain_timeout()

    def test_get_crg_id(self):
        self.common_get_crg_id()

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

    def test_attach_existing_agentpool(self):
        self.common_attach_existing_agentpool()

    def test_attach_agentpools(self):
        self.common_attach_agentpools()

    def test_validate_counts_in_autoscaler(self):
        self.common_validate_counts_in_autoscaler()

    def test_get_resource_group_name(self):
        self.common_get_resource_group_name()

    def test_get_cluster_name(self):
        self.common_get_cluster_name()

    def test_get_nodepool_name(self):
        # default
        ctx_1 = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({}),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )
        self.assertEqual(ctx_1.get_nodepool_name(), "nodepool1")

        agentpool_1 = self.create_initialized_agentpool_instance("test_ap_name")
        ctx_1.attach_agentpool(agentpool_1)
        self.assertEqual(ctx_1.get_nodepool_name(), "test_ap_name")

    def test_get_snapshot_id(self):
        self.common_get_snapshot_id()

    def test_get_snapshot(self):
        self.common_get_snapshot()

    def test_get_host_group_id(self):
        self.common_get_host_group_id()

    def test_get_kubernetes_version(self):
        self.common_get_kubernetes_version()

    def test_get_node_vm_size(self):
        self.common_get_node_vm_size()

    def test_get_os_type(self):
        self.common_get_os_type()

    def test_get_os_sku(self):
        self.common_get_os_sku()

    def test_get_vnet_subnet_id(self):
        self.common_get_vnet_subnet_id()

    def test_get_pod_subnet_id(self):
        self.common_get_pod_subnet_id()

    def test_get_enable_node_public_ip(self):
        self.common_get_enable_node_public_ip()

    def test_get_node_public_ip_prefix_id(self):
        self.common_get_node_public_ip_prefix_id()

    def test_get_node_count_and_enable_cluster_autoscaler_min_max_count(
        self,
    ):
        self.common_get_node_count_and_enable_cluster_autoscaler_min_max_count()

    def test_get_update_enable_disable_cluster_autoscaler_and_min_max_count(self):
        self.common_get_update_enable_disable_cluster_autoscaler_and_min_max_count()

    def test_get_priority(self):
        self.common_get_priority()

    def test_get_eviction_policy(self):
        self.common_get_eviction_policy()

    def test_get_spot_max_price(self):
        self.common_get_spot_max_price()

    def test_get_nodepool_labels(self):
        self.common_get_nodepool_labels()

    def test_get_nodepool_tags(self):
        self.common_get_nodepool_tags()

    def test_get_node_taints(self):
        self.common_get_node_taints()

    def test_get_node_osdisk_size(self):
        self.common_get_node_osdisk_size()

    def test_get_node_osdisk_type(self):
        self.common_get_node_osdisk_type()

    def test_get_max_surge(self):
        self.common_get_max_surge()

    def test_get_vm_set_type(self):
        self.common_get_vm_set_type()

    def test_get_ppg(self):
        self.common_get_ppg()

    def test_get_enable_encryption_at_host(self):
        self.common_get_enable_encryption_at_host()

    def test_get_enable_ultra_ssd(self):
        self.common_get_enable_ultra_ssd()

    def test_get_enable_fips_image(self):
        self.common_get_enable_fips_image()

    def test_get_zones(self):
        self.common_get_zones()

    def test_get_max_pods(self):
        self.common_get_max_pods()

    def test_get_mode(self):
        self.common_get_mode()

    def test_get_scale_down_mode(self):
        self.common_get_scale_down_mode()

    def test_get_kubelet_config(self):
        self.common_get_kubelet_config()

    def test_get_linux_os_config(self):
        self.common_get_linux_os_config()

    def test_get_aks_custom_headers(self):
        self.common_get_aks_custom_headers()

    def test_get_no_wait(self):
        self.common_get_no_wait()

    def test_get_gpu_instance_profile(self):
        self.common_get_gpu_instance_profile()

    def test_get_drain_timeout(self):
        self.common_get_drain_timeout()

    def test_get_crg_id(self):
        self.common_get_crg_id()

class AKSAgentPoolAddDecoratorCommonTestCase(unittest.TestCase):
    def _remove_defaults_in_agentpool(self, agentpool):
        self.defaults_in_agentpool = {}
        for attr_name, attr_value in vars(agentpool).items():
            if not attr_name.startswith("_") and attr_name != "name" and attr_value is not None:
                self.defaults_in_agentpool[attr_name] = attr_value
                setattr(agentpool, attr_name, None)
        return agentpool

    def _restore_defaults_in_agentpool(self, agentpool):
        for key, value in self.defaults_in_agentpool.items():
            if getattr(agentpool, key, None) is None:
                setattr(agentpool, key, value)
        return agentpool

    def create_initialized_agentpool_instance(
        self, nodepool_name="nodepool1", remove_defaults=True, restore_defaults=True, **kwargs
    ):
        """Helper function to create a properly initialized agentpool instance.

        :return: the AgentPool object
        """
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            agentpool = self.models.UnifiedAgentPoolModel(name=nodepool_name)
        else:
            agentpool = self.models.UnifiedAgentPoolModel()
            agentpool.name = nodepool_name

        # remove defaults
        if remove_defaults:
            self._remove_defaults_in_agentpool(agentpool)

        # set properties
        for key, value in kwargs.items():
            setattr(agentpool, key, value)

        # resote defaults
        if restore_defaults:
            self._restore_defaults_in_agentpool(agentpool)
        return agentpool

    def common_ensure_agentpool(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_agentpool(None)
        agentpool_1 = self.create_initialized_agentpool_instance()
        # fail on inconsistent agentpool with internal context
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_agentpool(agentpool_1)

    def common_remove_restore_defaults_in_agentpool(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1._remove_defaults_in_agentpool(None)
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1._restore_defaults_in_agentpool(None)
        agentpool_1 = self.create_initialized_agentpool_instance(remove_defaults=False, restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1._remove_defaults_in_agentpool(agentpool_1)
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)
        self.assertEqual(dec_1.context.get_intermediate("defaults_in_agentpool"), self.defaults_in_agentpool)

        dec_agentpool_2 = dec_1._restore_defaults_in_agentpool(dec_agentpool_1)
        ground_truth_agentpool_2 = self.create_initialized_agentpool_instance()
        self.assertEqual(dec_agentpool_2, ground_truth_agentpool_2)

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
            return_value=Mock(list=Mock(return_value=[])),
        ):
            dec_agentpool_1 = dec_1.init_agentpool()
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            "test_nodepool_name", remove_defaults=False, restore_defaults=False
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)
        self.assertEqual(dec_agentpool_1, dec_1.context.agentpool)

    def common_set_up_snapshot_properties(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {"kubernetes_version": "test_kubernetes_version", "os_type": None, "os_sku": None, "node_vm_size": None},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_snapshot_properties(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_snapshot_properties(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            orchestrator_version="test_kubernetes_version",
            vm_size=CONST_DEFAULT_NODE_VM_SIZE,
            os_type=CONST_DEFAULT_NODE_OS_TYPE,
            os_sku=None,
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

        dec_2 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "kubernetes_version": "",
                "os_type": None,
                "os_sku": None,
                "node_vm_size": None,
                "snapshot_id": "test_snapshot_id",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_2.set_up_snapshot_properties(None)
        agentpool_2 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_2.context.attach_agentpool(agentpool_2)
        mock_snapshot_2 = Mock(
            kubernetes_version="test_kubernetes_version",
            os_type="test_os_type",
            os_sku="test_os_sku",
            vm_size="test_vm_size",
        )
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.get_snapshot_by_snapshot_id",
            return_value=mock_snapshot_2,
        ):
            dec_agentpool_2 = dec_2.set_up_snapshot_properties(agentpool_2)
        dec_agentpool_2 = self._restore_defaults_in_agentpool(dec_agentpool_2)
        ground_truth_creation_data_2 = dec_2.models.CreationData(source_resource_id="test_snapshot_id")
        ground_truth_agentpool_2 = self.create_initialized_agentpool_instance(
            orchestrator_version="test_kubernetes_version",
            vm_size="test_vm_size",
            os_type="test_os_type",
            os_sku="test_os_sku",
            creation_data=ground_truth_creation_data_2,
        )
        self.assertEqual(dec_agentpool_2, ground_truth_agentpool_2)

    def common_set_up_node_network_properties(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "vnet_subnet_id": "test_vnet_subnet_id",
                "pod_subnet_id": "test_pod_subnet_id",
                "enable_node_public_ip": True,
                "node_public_ip_prefix_id": "test_node_public_ip_prefix_id",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_label_tag_taint(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_node_network_properties(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)

        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            vnet_subnet_id="test_vnet_subnet_id",
            pod_subnet_id="test_pod_subnet_id",
            enable_node_public_ip=True,
            node_public_ip_prefix_id="test_node_public_ip_prefix_id",
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

    def common_set_up_auto_scaler_properties(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "node_count": 3,
                "enable_cluster_autoscaler": True,
                "min_count": 1,
                "max_count": 5,
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_auto_scaler_properties(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_auto_scaler_properties(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)

        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            count=3, enable_auto_scaling=True, min_count=1, max_count=5
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

    def common_set_up_priority_properties(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "priority": CONST_SCALE_SET_PRIORITY_SPOT,
                "eviction_policy": CONST_SPOT_EVICTION_POLICY_DEALLOCATE,
                "spot_max_price": float(1.2345),
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_label_tag_taint(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_priority_properties(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)

        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            scale_set_priority=CONST_SCALE_SET_PRIORITY_SPOT,
            scale_set_eviction_policy=CONST_SPOT_EVICTION_POLICY_DEALLOCATE,
            spot_max_price=float(1.2345),
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

    def common_set_up_label_tag_taint(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "nodepool_labels": "test_nodepool_labels",
                "labels": "test_labels",
                "nodepool_tags": "test_nodepool_tags",
                "tags": "test_tags",
                "node_taints": "abc=xyz:123,123=456:abc",
                "nodepool_taints": "abc=xyz:123,123=456:abc",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_label_tag_taint(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_label_tag_taint(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)

        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            ground_truth_mc_agentpool_1 = self.create_initialized_agentpool_instance(
                node_labels="test_nodepool_labels",
                tags="test_nodepool_tags",
                node_taints=["abc=xyz:123", "123=456:abc"],
            )
            self.assertEqual(dec_agentpool_1, ground_truth_mc_agentpool_1)
        else:
            ground_truth_sd_agentpool_1 = self.create_initialized_agentpool_instance(
                node_labels="test_labels", tags="test_tags", node_taints=["abc=xyz:123", "123=456:abc"]
            )
            self.assertEqual(dec_agentpool_1, ground_truth_sd_agentpool_1)

    def common_set_up_osdisk_properties(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "node_osdisk_size": 123,
                "node_osdisk_type": "test_node_osdisk_type",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_osdisk_properties(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_osdisk_properties(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)

        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            os_disk_size_gb=123, os_disk_type="test_node_osdisk_type"
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

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
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_upgrade_settings(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)
        ground_truth_upgrade_settings_1 = self.models.AgentPoolUpgradeSettings(max_surge="test_max_surge")
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            upgrade_settings=ground_truth_upgrade_settings_1
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

    def common_set_up_vm_properties(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "vm_set_type": CONST_VIRTUAL_MACHINE_SCALE_SETS.lower(),
                "ppg": "test_ppg",
                "enable_encryption_at_host": True,
                "enable_ultra_ssd": True,
                "enable_fips_image": True,
                "zones": [1, 2, 3],
                "max_pods": 110,
                "mode": "test_mode",
                "scale_down_mode": "test_scale_down_mode",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_label_tag_taint(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_vm_properties(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)

        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            proximity_placement_group_id="test_ppg",
            enable_encryption_at_host=True,
            enable_ultra_ssd=True,
            enable_fips=True,
            availability_zones=[1, 2, 3],
            max_pods=110,
            mode="test_mode",
            scale_down_mode="test_scale_down_mode",
        )
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            ground_truth_agentpool_1.type = CONST_VIRTUAL_MACHINE_SCALE_SETS
        else:
            ground_truth_agentpool_1.type_properties_type = CONST_VIRTUAL_MACHINE_SCALE_SETS
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

    def common_set_up_custom_node_config(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "kubelet_config": get_test_data_file_path("kubeletconfig.json"),
                "linux_os_config": get_test_data_file_path("linuxosconfig.json"),
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_label_tag_taint(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_custom_node_config(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)

        ground_truth_kubelet_config_1 = get_file_json(get_test_data_file_path("kubeletconfig.json"))
        ground_truth_linux_os_config_1 = get_file_json(get_test_data_file_path("linuxosconfig.json"))
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            kubelet_config=ground_truth_kubelet_config_1,
            linux_os_config=ground_truth_linux_os_config_1,
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

    def common_set_up_gpu_propertes(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {"gpu_instance_profile": "test_gpu_instance_profile"},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.set_up_gpu_properties(None)
        agentpool_1 = self.create_initialized_agentpool_instance(restore_defaults=False)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.set_up_gpu_properties(agentpool_1)
        dec_agentpool_1 = self._restore_defaults_in_agentpool(dec_agentpool_1)
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            gpu_instance_profile="test_gpu_instance_profile",
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

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

    def test_remove_resotre_defaults_in_agentpool(self):
        self.common_remove_restore_defaults_in_agentpool()

    def test_init_agentpool(self):
        self.common_init_agentpool()

    def test_set_up_snapshot_properties(self):
        self.common_set_up_snapshot_properties()

    def test_set_up_node_network_properties(self):
        self.common_set_up_node_network_properties()

    def test_set_up_auto_scaler_properties(self):
        self.common_set_up_auto_scaler_properties()

    def test_set_up_priority_properties(self):
        self.common_set_up_priority_properties()

    def test_set_up_label_tag_taint(self):
        self.common_set_up_label_tag_taint()

    def test_set_up_osdisk_properties(self):
        self.common_set_up_osdisk_properties()

    def test_set_up_upgrade_settings(self):
        self.common_set_up_upgrade_settings()

    def test_set_up_vm_properties(self):
        self.common_set_up_vm_properties()

    def test_set_up_custom_node_config(self):
        self.common_set_up_custom_node_config()

    def test_construct_agentpool_profile_default(self):
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
            return_value=Mock(list=Mock(return_value=[])),
        ):
            dec_agentpool_1 = dec_1.construct_agentpool_profile_default()

        ground_truth_upgrade_settings_1 = self.models.AgentPoolUpgradeSettings()
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            nodepool_name="test_nodepool_name",
            os_type=CONST_DEFAULT_NODE_OS_TYPE,
            vm_size=CONST_DEFAULT_NODE_VM_SIZE,
            enable_node_public_ip=False,
            enable_auto_scaling=False,
            count=3,
            node_taints=[],
            upgrade_settings=ground_truth_upgrade_settings_1,
            type_properties_type=CONST_VIRTUAL_MACHINE_SCALE_SETS,
            enable_encryption_at_host=False,
            enable_ultra_ssd=False,
            enable_fips=False,
            mode=CONST_NODEPOOL_MODE_USER,
            scale_down_mode=CONST_SCALE_DOWN_MODE_DELETE,
            host_group_id=None,
            capacity_reservation_group_id=None,
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

        dec_1.context.raw_param.print_usage_statistics()

    def test_add_agentpool(self):
        dec_1 = AKSAgentPoolAddDecorator(
            self.cmd,
            self.client,
            {
                "resource_group_name": "test_resource_group_name",
                "cluster_name": "test_cluster_name",
                "nodepool_name": "test_nodepool_name",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.add_agentpool(None)
        agentpool_1 = self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_name")
        dec_1.context.attach_agentpool(agentpool_1)
        with patch("azure.cli.command_modules.acs.agentpool_decorator.sdk_no_wait") as put_agentpool:
            dec_1.add_agentpool(agentpool_1)
        put_agentpool.assert_called_once_with(
            False,
            self.client.begin_create_or_update,
            "test_resource_group_name",
            "test_cluster_name",
            "test_nodepool_name",
            agentpool_1,
            headers={},
        )

    def test_set_up_gpu_propertes(self):
        self.common_set_up_gpu_propertes()

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

    def test_remove_resotre_defaults_in_agentpool(self):
        self.common_remove_restore_defaults_in_agentpool()

    def test_init_agentpool(self):
        self.common_init_agentpool()

    def test_set_up_snapshot_properties(self):
        self.common_set_up_snapshot_properties()

    def test_set_up_node_network_properties(self):
        self.common_set_up_node_network_properties()

    def test_set_up_auto_scaler_properties(self):
        self.common_set_up_auto_scaler_properties()

    def test_set_up_priority_properties(self):
        self.common_set_up_priority_properties()

    def test_set_up_label_tag_taint(self):
        self.common_set_up_label_tag_taint()

    def test_set_up_osdisk_properties(self):
        self.common_set_up_osdisk_properties()

    def test_set_up_upgrade_settings(self):
        self.common_set_up_upgrade_settings()

    def test_set_up_vm_properties(self):
        self.common_set_up_vm_properties()

    def test_set_up_custom_node_config(self):
        self.common_set_up_custom_node_config()

    def test_construct_agentpool_profile_default(self):
        import inspect

        from azure.cli.command_modules.acs.custom import aks_create

        optional_params = {}
        positional_params = []
        for _, v in inspect.signature(aks_create).parameters.items():
            if v.default != v.empty:
                optional_params[v.name] = v.default
            else:
                positional_params.append(v.name)
        ground_truth_positional_params = [
            "cmd",
            "client",
            "resource_group_name",
            "name",
            "ssh_key_value",
        ]
        self.assertEqual(positional_params, ground_truth_positional_params)

        # prepare a dictionary of default parameters
        raw_param_dict = {
            "resource_group_name": "test_rg_name",
            "name": "test_cluster_name",
            "ssh_key_value": None,
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
            return_value=Mock(list=Mock(return_value=[])),
        ):
            dec_agentpool_1 = dec_1.construct_agentpool_profile_default()

        upgrade_settings_1 = self.models.AgentPoolUpgradeSettings()
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            nodepool_name="nodepool1",
            orchestrator_version="",
            vm_size=CONST_DEFAULT_NODE_VM_SIZE,
            os_type=CONST_DEFAULT_NODE_OS_TYPE,
            enable_node_public_ip=False,
            enable_auto_scaling=False,
            count=3,
            node_taints=[],
            upgrade_settings=upgrade_settings_1,
            type=CONST_VIRTUAL_MACHINE_SCALE_SETS,
            enable_encryption_at_host=False,
            enable_ultra_ssd=False,
            enable_fips=False,
            mode=CONST_NODEPOOL_MODE_SYSTEM,
            host_group_id=None,
            capacity_reservation_group_id=None,
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

        dec_1.context.raw_param.print_usage_statistics()

    def test_set_up_gpu_propertes(self):
        self.common_set_up_gpu_propertes()

class AKSAgentPoolUpdateDecoratorCommonTestCase(unittest.TestCase):
    def _remove_defaults_in_agentpool(self, agentpool):
        self.defaults_in_agentpool = {}
        for attr_name, attr_value in vars(agentpool).items():
            if not attr_name.startswith("_") and attr_name != "name" and attr_value is not None:
                self.defaults_in_agentpool[attr_name] = attr_value
                setattr(agentpool, attr_name, None)
        return agentpool

    def _restore_defaults_in_agentpool(self, agentpool):
        for key, value in self.defaults_in_agentpool.items():
            if getattr(agentpool, key, None) is None:
                setattr(agentpool, key, value)
        return agentpool

    def create_initialized_agentpool_instance(
        self, nodepool_name="nodepool1", remove_defaults=True, restore_defaults=True, **kwargs
    ):
        """Helper function to create a properly initialized agentpool instance.

        :return: the AgentPool object
        """
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            agentpool = self.models.UnifiedAgentPoolModel(name=nodepool_name)
        else:
            agentpool = self.models.UnifiedAgentPoolModel()
            agentpool.name = nodepool_name

        # remove defaults
        if remove_defaults:
            self._remove_defaults_in_agentpool(agentpool)

        # set properties
        for key, value in kwargs.items():
            setattr(agentpool, key, value)

        # resote defaults
        if restore_defaults:
            self._restore_defaults_in_agentpool(agentpool)
        return agentpool

    def common_ensure_agentpool(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {},
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_agentpool(None)
        agentpool_1 = self.create_initialized_agentpool_instance()
        # fail on inconsistent agentpool with internal context
        with self.assertRaises(CLIInternalError):
            dec_1._ensure_agentpool(agentpool_1)

    def common_update_auto_scaler_properties(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": False,
                "update_cluster_autoscaler": True,
                "min_count": 1,
                "max_count": 5,
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.update_auto_scaler_properties(None)
        agentpool_1 = self.create_initialized_agentpool_instance(
            enable_auto_scaling=True, node_count=3, min_count=2, max_count=4
        )
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.update_auto_scaler_properties(agentpool_1)
        grond_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            enable_auto_scaling=True, node_count=3, min_count=1, max_count=5
        )
        self.assertEqual(dec_agentpool_1, grond_truth_agentpool_1)

        dec_2 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "enable_cluster_autoscaler": False,
                "disable_cluster_autoscaler": True,
                "update_cluster_autoscaler": False,
                "min_count": None,
                "max_count": None,
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_2.update_auto_scaler_properties(None)
        agentpool_2 = self.create_initialized_agentpool_instance(
            enable_auto_scaling=True, node_count=3, min_count=2, max_count=4
        )
        dec_2.context.attach_agentpool(agentpool_2)
        dec_agentpool_2 = dec_2.update_auto_scaler_properties(agentpool_2)
        grond_truth_agentpool_2 = self.create_initialized_agentpool_instance(
            enable_auto_scaling=False, node_count=3, min_count=None, max_count=None
        )
        self.assertEqual(dec_agentpool_2, grond_truth_agentpool_2)

    def common_update_label_tag_taint(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "nodepool_labels": "test_nodepool_labels",
                "nodepool_tags": "test_nodepool_tags",
                "labels": "test_labels",
                "tags": "test_tags",
                "node_taints": "",
                "nodepool_taints": "",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.update_label_tag_taint(None)
        agentpool_1 = self.create_initialized_agentpool_instance(
            node_labels={"abc": "xyz"}, tags={"123": "456"}, node_taints=["test_node_taints"]
        )
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.update_label_tag_taint(agentpool_1)
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            grond_truth_agentpool_1 = self.create_initialized_agentpool_instance(
                node_labels="test_nodepool_labels", tags="test_nodepool_tags", node_taints=[]
            )
        else:
            grond_truth_agentpool_1 = self.create_initialized_agentpool_instance(
                node_labels="test_labels", tags="test_tags", node_taints=[]
            )
        self.assertEqual(dec_agentpool_1, grond_truth_agentpool_1)

    def common_update_upgrade_settings(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "max_surge": "test_max_surge",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.update_upgrade_settings(None)
        upgrade_settings_1 = self.models.AgentPoolUpgradeSettings(max_surge="test_ap_max_surge")
        agentpool_1 = self.create_initialized_agentpool_instance(upgrade_settings=upgrade_settings_1)
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.update_upgrade_settings(agentpool_1)
        ground_truth_upgrade_settings_1 = self.models.AgentPoolUpgradeSettings(max_surge="test_max_surge")
        grond_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            upgrade_settings=ground_truth_upgrade_settings_1
        )
        self.assertEqual(dec_agentpool_1, grond_truth_agentpool_1)

        dec_2 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "max_surge": "test_max_surge",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        agentpool_2 = self.create_initialized_agentpool_instance()
        dec_2.context.attach_agentpool(agentpool_2)
        dec_agentpool_2 = dec_2.update_upgrade_settings(agentpool_2)
        ground_truth_upgrade_settings_2 = self.models.AgentPoolUpgradeSettings(max_surge="test_max_surge")
        grond_truth_agentpool_2 = self.create_initialized_agentpool_instance(
            upgrade_settings=ground_truth_upgrade_settings_2
        )
        self.assertEqual(dec_agentpool_2, grond_truth_agentpool_2)

    def common_update_vm_properties(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "mode": "test_mode",
                "scale_down_mode": "test_scale_down_mode",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.update_vm_properties(None)
        agentpool_1 = self.create_initialized_agentpool_instance(
            mode="test_ap_mode", scale_down_mode="test_ap_scale_down_mode"
        )
        dec_1.context.attach_agentpool(agentpool_1)
        dec_agentpool_1 = dec_1.update_vm_properties(agentpool_1)
        grond_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            mode="test_mode", scale_down_mode="test_scale_down_mode"
        )
        self.assertEqual(dec_agentpool_1, grond_truth_agentpool_1)


class AKSAgentPoolUpdateDecoratorStandaloneModeTestCase(AKSAgentPoolUpdateDecoratorCommonTestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.STANDALONE
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)
        self.client = MockClient()

    def test_ensure_agentpool(self):
        self.common_ensure_agentpool()

    def test_fetch_agentpool(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "resource_group_name": "test_resource_group_name",
                "cluster_name": "test_cluster_name",
                "nodepool_name": "test_nodepool_name",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        self.client.get = Mock(return_value=self.create_initialized_agentpool_instance())
        with patch(
            "azure.cli.command_modules.acs.agentpool_decorator.cf_agent_pools",
            return_value=Mock(list=Mock(return_value=[])),
        ):
            dec_agentpool_1 = dec_1.fetch_agentpool()
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance()
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)
        self.assertEqual(dec_agentpool_1, dec_1.context.agentpool)
        self.client.get.assert_called_once_with("test_resource_group_name", "test_cluster_name", "test_nodepool_name")

    def test_update_auto_scaler_properties(self):
        self.common_update_auto_scaler_properties()

    def test_update_label_tag_taint(self):
        self.common_update_label_tag_taint()

    def test_update_upgrade_settings(self):
        self.common_update_upgrade_settings()

    def test_update_vm_properties(self):
        self.common_update_vm_properties()

    def test_update_agentpool_profile_default(self):
        import inspect

        from azure.cli.command_modules.acs.custom import aks_agentpool_update

        optional_params = {}
        positional_params = []
        for _, v in inspect.signature(aks_agentpool_update).parameters.items():
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
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            raw_param_dict,
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        self.client.get = Mock(
            return_value=self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_name")
        )
        dec_agentpool_1 = dec_1.update_agentpool_profile_default()
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            nodepool_name="test_nodepool_name",
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

        dec_1.context.raw_param.print_usage_statistics()

    def test_update_agentpool(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "resource_group_name": "test_resource_group_name",
                "cluster_name": "test_cluster_name",
                "nodepool_name": "test_nodepool_name",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        # fail on passing the wrong agentpool object
        with self.assertRaises(CLIInternalError):
            dec_1.update_agentpool(None)
        agentpool_1 = self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_name")
        dec_1.context.attach_agentpool(agentpool_1)
        with patch("azure.cli.command_modules.acs.agentpool_decorator.sdk_no_wait") as put_agentpool:
            dec_1.update_agentpool(agentpool_1)
        put_agentpool.assert_called_once_with(
            False,
            self.client.begin_create_or_update,
            "test_resource_group_name",
            "test_cluster_name",
            "test_nodepool_name",
            agentpool_1,
            headers={},
        )


class AKSAgentPoolUpdateDecoratorManagedClusterModeTestCase(AKSAgentPoolUpdateDecoratorCommonTestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.MANAGED_CLUSTER
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)
        self.client = MockClient()

    def test_ensure_agentpool(self):
        self.common_ensure_agentpool()

    def test_fetch_agentpool(self):
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            {
                "resource_group_name": "test_resource_group_name",
                "name": "test_cluster_name",
                "nodepool_name": "test_nodepool_name",
            },
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        agentpools = [
            self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_1"),
            self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_2"),
        ]
        dec_agentpool_1 = dec_1.fetch_agentpool(agentpools)
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_1")
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)
        self.assertEqual(dec_agentpool_1, dec_1.context.agentpool)

    def test_update_auto_scaler_properties(self):
        self.common_update_auto_scaler_properties()

    def test_update_label_tag_taint(self):
        self.common_update_label_tag_taint()

    def test_update_upgrade_settings(self):
        self.common_update_upgrade_settings()

    def test_update_agentpool_profile_default(self):
        import inspect

        from azure.cli.command_modules.acs.custom import aks_update

        optional_params = {}
        positional_params = []
        for _, v in inspect.signature(aks_update).parameters.items():
            if v.default != v.empty:
                optional_params[v.name] = v.default
            else:
                positional_params.append(v.name)
        ground_truth_positional_params = [
            "cmd",
            "client",
            "resource_group_name",
            "name",
        ]
        self.assertEqual(positional_params, ground_truth_positional_params)

        # prepare a dictionary of default parameters
        raw_param_dict = {
            "resource_group_name": "test_rg_name",
            "name": "test_cluster_name",
        }
        raw_param_dict.update(optional_params)

        # default value in `aks_create`
        dec_1 = AKSAgentPoolUpdateDecorator(
            self.cmd,
            self.client,
            raw_param_dict,
            self.resource_type,
            self.agentpool_decorator_mode,
        )
        agentpools = [
            self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_1"),
            self.create_initialized_agentpool_instance(nodepool_name="test_nodepool_2"),
        ]
        dec_agentpool_1 = dec_1.update_agentpool_profile_default(agentpools)
        ground_truth_agentpool_1 = self.create_initialized_agentpool_instance(
            nodepool_name="test_nodepool_1",
        )
        self.assertEqual(dec_agentpool_1, ground_truth_agentpool_1)

        dec_1.context.raw_param.print_usage_statistics()

    def test_update_vm_properties(self):
        self.common_update_vm_properties()


if __name__ == "__main__":
    unittest.main()

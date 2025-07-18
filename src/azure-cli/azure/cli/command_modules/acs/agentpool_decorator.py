# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import base64
from math import isnan
from types import SimpleNamespace
from typing import Dict, List, Tuple, TypeVar, Union

from azure.cli.command_modules.acs._client_factory import cf_agent_pools
from azure.cli.command_modules.acs._consts import (
    CONST_AVAILABILITY_SET,
    CONST_DEFAULT_NODE_OS_TYPE,
    CONST_DEFAULT_NODE_VM_SIZE,
    CONST_DEFAULT_WINDOWS_NODE_VM_SIZE,
    CONST_DEFAULT_VMS_VM_SIZE,
    CONST_DEFAULT_WINDOWS_VMS_VM_SIZE,
    CONST_NODEPOOL_MODE_SYSTEM,
    CONST_NODEPOOL_MODE_USER,
    CONST_SCALE_DOWN_MODE_DELETE,
    CONST_SCALE_SET_PRIORITY_REGULAR,
    CONST_SCALE_SET_PRIORITY_SPOT,
    CONST_SPOT_EVICTION_POLICY_DELETE,
    CONST_VIRTUAL_MACHINE_SCALE_SETS,
    CONST_VIRTUAL_MACHINES,
    CONST_OS_SKU_WINDOWS2019,
    CONST_OS_SKU_WINDOWS2022,
    AgentPoolDecoratorMode,
    DecoratorEarlyExitException,
    DecoratorMode,
)
from azure.cli.command_modules.acs._helpers import get_snapshot_by_snapshot_id, safe_list_get
from azure.cli.command_modules.acs._validators import extract_comma_separated_string
from azure.cli.command_modules.acs.base_decorator import BaseAKSContext, BaseAKSModels, BaseAKSParamDict
from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import get_file_json, sdk_no_wait, read_file_content
from knack.log import get_logger

logger = get_logger(__name__)

# type variables
AgentPool = TypeVar("AgentPool")
AgentPoolsOperations = TypeVar("AgentPoolsOperations")
PortRange = TypeVar("PortRange")
Snapshot = TypeVar("Snapshot")
KubeletConfig = TypeVar("KubeletConfig")
LinuxOSConfig = TypeVar("LinuxOSConfig")
IPTag = TypeVar("IPTag")

# TODO:
# 1. Add extra type checking for getter functions


# pylint: disable=too-few-public-methods
class AKSAgentPoolModels(BaseAKSModels):
    """Store the models used in aks agentpool series of commands.

    The api version of the class corresponding to a model is determined by resource_type.
    """

    def __init__(
        self,
        cmd: AzCommandsLoader,
        resource_type: ResourceType,
        agentpool_decorator_mode: AgentPoolDecoratorMode,
    ):
        super().__init__(cmd, resource_type)
        self.agentpool_decorator_mode = agentpool_decorator_mode
        self.UnifiedAgentPoolModel = self.__choose_agentpool_model_by_agentpool_decorator_mode()

    def __choose_agentpool_model_by_agentpool_decorator_mode(self):
        """Choose the model reference for agentpool based on agentpool_decorator_mode.
        """
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            return self.ManagedClusterAgentPoolProfile
        return self.AgentPool


# pylint: disable=too-few-public-methods
class AKSAgentPoolParamDict(BaseAKSParamDict):
    """Store the original parameters passed in by aks agentpool series of commands as an internal dictionary.

    Only expose the "get" method externally to obtain parameter values, while recording usage.
    """


# pylint: disable=too-many-public-methods
class AKSAgentPoolContext(BaseAKSContext):
    """Implement getter functions for all parameters in aks_agentpool_add and aks_agentpool_update.
    """
    def __init__(
        self,
        cmd: AzCliCommand,
        raw_parameters: AKSAgentPoolParamDict,
        models: AKSAgentPoolModels,
        decorator_mode: DecoratorMode,
        agentpool_decorator_mode: AgentPoolDecoratorMode,
    ):
        super().__init__(cmd, raw_parameters, models, decorator_mode)
        self.agentpool_decorator_mode = agentpool_decorator_mode
        self.agentpool = None
        # used to store origin agentpool in update mode
        self.__existing_agentpool = None
        # used to store all the agentpools in mc mode
        self._agentpools = []
        # used to store external functions
        self.__external_functions = None

    @property
    def existing_agentpool(self) -> AgentPool:
        return self.__existing_agentpool

    @property
    def external_functions(self) -> SimpleNamespace:
        if self.__external_functions is None:
            external_functions = {}
            external_functions["cf_agent_pools"] = cf_agent_pools
            external_functions["get_snapshot_by_snapshot_id"] = get_snapshot_by_snapshot_id
            self.__external_functions = SimpleNamespace(**external_functions)
        return self.__external_functions

    def attach_agentpool(self, agentpool: AgentPool) -> None:
        """Attach the AgentPool object to the context.

        The `agentpool` object is only allowed to be attached once, and attaching again will raise a CLIInternalError.

        :return: None
        """
        if self.decorator_mode == DecoratorMode.UPDATE:
            self.attach_existing_agentpool(agentpool)

        if self.agentpool is None:
            self.agentpool = agentpool
        else:
            msg = "the same" if self.agentpool == agentpool else "different"
            raise CLIInternalError(
                "Attempting to attach the `agentpool` object again, the two objects are {}.".format(
                    msg
                )
            )

    def attach_existing_agentpool(self, agentpool: AgentPool) -> None:
        if self.__existing_agentpool is None:
            self.__existing_agentpool = agentpool
        else:
            msg = "the same" if self.__existing_agentpool == agentpool else "different"
            raise CLIInternalError(
                "Attempting to attach the existing `agentpool` object again, the two objects are {}.".format(
                    msg
                )
            )

    def attach_agentpools(self, agentpools: List[AgentPool]) -> None:
        if self._agentpools == []:
            self._agentpools = agentpools
        else:
            msg = "the same" if self._agentpools == agentpools else "different"
            raise CLIInternalError(
                "Attempting to attach the `agentpools` object again, the two objects are {}.".format(
                    msg
                )
            )
        self._agentpools = agentpools

    # pylint: disable=no-self-use
    def __validate_counts_in_autoscaler(
        self,
        node_count,
        enable_cluster_autoscaler,
        min_count,
        max_count,
        mode,
        decorator_mode,
    ) -> None:
        """Helper function to check the validity of serveral count-related parameters in autoscaler.

        On the premise that enable_cluster_autoscaler (in update mode, this could be update_cluster_autoscaler) is
        enabled, it will check whether both min_count and max_count are assigned, if not, raise the
        RequiredArgumentMissingError. If min_count is less than max_count, raise the InvalidArgumentValueError. Only in
        create mode it will check whether the value of node_count is between min_count and max_count, if not, raise the
        InvalidArgumentValueError. If enable_cluster_autoscaler (in update mode, this could be
        update_cluster_autoscaler) is not enabled, it will check whether any of min_count or max_count is assigned,
        if so, raise the RequiredArgumentMissingError.

        :return: None
        """
        # validation
        if enable_cluster_autoscaler:
            if min_count is None or max_count is None:
                raise RequiredArgumentMissingError(
                    "Please specify both min-count and max-count when --enable-cluster-autoscaler enabled"
                )
            if min_count > max_count:
                raise InvalidArgumentValueError(
                    "Value of min-count should be less than or equal to value of max-count"
                )
            if decorator_mode == DecoratorMode.CREATE:
                if node_count < min_count or node_count > max_count:
                    raise InvalidArgumentValueError(
                        "node-count is not in the range of min-count and max-count"
                    )
            if mode == CONST_NODEPOOL_MODE_SYSTEM:
                if min_count < 1:
                    raise InvalidArgumentValueError(
                        "Value of min-count should be greater than or equal to 1 for System node pools"
                    )
        else:
            if min_count is not None or max_count is not None:
                option_name = "--enable-cluster-autoscaler"
                if decorator_mode == DecoratorMode.UPDATE:
                    option_name += " or --update-cluster-autoscaler"
                raise RequiredArgumentMissingError(
                    "min-count and max-count are required for {}, please use the flag".format(
                        option_name
                    )
                )

    def get_resource_group_name(self) -> str:
        """Obtain the value of resource_group_name.

        Note: resource_group_name will not be decorated into the `agentpool` object.

        This is a required parameter and its value should be provided by user explicitly.

        :return: string
        """
        # read the original value passed by the command
        resource_group_name = self.raw_param.get("resource_group_name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return resource_group_name

    def get_cluster_name(self) -> str:
        """Obtain the value of cluster_name.

        Note: cluster_name will not be decorated into the `agentpool` object.

        This is a required parameter and its value should be provided by user explicitly.

        :return: string
        """
        # read the original value passed by the command
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            cluster_name = self.raw_param.get("name")
        else:
            cluster_name = self.raw_param.get("cluster_name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return cluster_name

    def _get_nodepool_name(self, enable_validation: bool = False) -> str:
        """Internal function to obtain the value of nodepool_name.

        Note: SDK performs the following validation {'required': True, 'pattern': r'^[a-z][a-z0-9]{0,11}$'}.

        This is a required parameter and its value should be provided by user explicitly.

        This function supports the option of enable_validation. When enabled, it will check if the given nodepool name
        is used by any nodepool of the cluster, if so, raise the InvalidArgumentValueError. This verification operation
        will send a get request, skip the validation appropriately to avoid multiple api calls.

        :return: string
        """
        # read the original value passed by the command
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            nodepool_name = self.raw_param.get("nodepool_name", "nodepool1")
        else:
            nodepool_name = self.raw_param.get("nodepool_name")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.name is not None:
            nodepool_name = self.agentpool.name

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if (
                self.agentpool_decorator_mode == AgentPoolDecoratorMode.STANDALONE and
                self.decorator_mode == DecoratorMode.CREATE
            ):
                agentpool_client = self.external_functions.cf_agent_pools(self.cmd.cli_ctx)
                instances = agentpool_client.list(self.get_resource_group_name(), self.get_cluster_name())
                for agentpool_profile in instances:
                    if agentpool_profile.name == nodepool_name:
                        raise InvalidArgumentValueError(
                            "Node pool {} already exists, please try a different name, "
                            "use 'aks nodepool list' to get current list of node pool".format(
                                nodepool_name
                            )
                        )
        return nodepool_name

    def get_nodepool_name(self) -> str:
        """Obtain the value of nodepool_name.

        Note: SDK performs the following validation {'required': True, 'pattern': r'^[a-z][a-z0-9]{0,11}$'}.

        This is a required parameter and its value should be provided by user explicitly.

        This function will verify the parameter by default. It will check if the given nodepool name is used by any
        nodepool of the cluster, if so, raise the InvalidArgumentValueError. This verification operation will send a
        get request, may use the internal function to skip the validation appropriately and avoid multiple api calls.

        :return: string
        """
        return self._get_nodepool_name(enable_validation=True)

    def get_snapshot_id(self) -> Union[str, None]:
        """Obtain the values of snapshot_id.

        :return: string or None
        """
        # read the original value passed by the command
        snapshot_id = self.raw_param.get("snapshot_id")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if (
            self.agentpool and
            hasattr(self.agentpool, "creation_data") and    # backward compatibility
            self.agentpool.creation_data and
            self.agentpool.creation_data.source_resource_id is not None
        ):
            snapshot_id = self.agentpool.creation_data.source_resource_id

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return snapshot_id

    def get_snapshot(self) -> Union[Snapshot, None]:
        """Helper function to retrieve the Snapshot object corresponding to a snapshot id.

        This fuction will store an intermediate "snapshot" to avoid sending the same request multiple times.

        Function "get_snapshot_by_snapshot_id" will be called to retrieve the Snapshot object corresponding to a
        snapshot id, which internally used the snapshot client (snapshots operations belonging to container service
        client) to send the request.

        :return: Snapshot or None
        """
        # try to read from intermediates
        snapshot = self.get_intermediate("snapshot")
        if snapshot:
            return snapshot

        snapshot_id = self.get_snapshot_id()
        if snapshot_id:
            snapshot = self.external_functions.get_snapshot_by_snapshot_id(self.cmd.cli_ctx, snapshot_id)
            self.set_intermediate("snapshot", snapshot, overwrite_exists=True)
        return snapshot

    def get_host_group_id(self) -> Union[str, None]:
        return self._get_host_group_id()

    def _get_host_group_id(self) -> Union[str, None]:
        raw_value = self.raw_param.get("host_group_id")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        value_obtained_from_agentpool = None
        if self.agentpool and hasattr(self.agentpool, "host_group_id"):
            value_obtained_from_agentpool = self.agentpool.host_group_id
        if value_obtained_from_agentpool is not None:
            host_group_id = value_obtained_from_agentpool
        else:
            host_group_id = raw_value
        return host_group_id

    def get_crg_id(self) -> Union[str, None]:
        return self._get_crg_id()

    def _get_crg_id(self) -> Union[str, None]:
        """Obtain the value of crg_id.

        :return: string or None
        """
        raw_value = self.raw_param.get("crg_id")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        value_from_agentpool = None
        if self.agentpool and hasattr(self.agentpool, "capacity_reservation_group_id"):
            value_from_agentpool = self.agentpool.capacity_reservation_group_id
        if value_from_agentpool is not None:
            crg_id = value_from_agentpool
        else:
            crg_id = raw_value
        return crg_id

    def get_message_of_the_day(self) -> Union[str, None]:
        """Obtain the value of message_of_the_day.

        :return: string or None
        """
        # read the original value passed by the command
        message_of_the_day = None
        message_of_the_day_file_path = self.raw_param.get("message_of_the_day")

        if message_of_the_day_file_path:
            if not os.path.isfile(message_of_the_day_file_path):
                raise InvalidArgumentValueError(
                    f"{message_of_the_day_file_path} is not valid file, or not accessible."
                )
            message_of_the_day = read_file_content(
                message_of_the_day_file_path)
            message_of_the_day = base64.b64encode(
                bytes(message_of_the_day, 'ascii')).decode('ascii')

        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.agentpool and
            hasattr(self.agentpool, "message_of_the_day") and
            self.agentpool.message_of_the_day is not None
        ):
            message_of_the_day = self.agentpool.message_of_the_day

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return message_of_the_day

    def get_enable_vtpm(self) -> bool:
        return self._get_enable_vtpm(enable_validation=True)

    def _get_enable_vtpm(self, enable_validation: bool = False) -> bool:
        """Obtain the value of enable_vtpm, default value is False.

        :return: bool
        """
        # read the original value passed by the command
        enable_vtpm = self.raw_param.get("enable_vtpm", False)

        # In create mode, try and read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            # try to read the property value corresponding to the parameter from the `agentpool` object
            if (
                self.agentpool and
                hasattr(self.agentpool, "security_profile") and
                self.agentpool.security_profile is not None and
                self.agentpool.security_profile.enable_vtpm is not None
            ):
                enable_vtpm = self.agentpool.security_profile.enable_vtpm

        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_vtpm and self._get_disable_vtpm(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-vtpm and --disable-vtpm at the same time."
                )

        return enable_vtpm

    def _get_disable_vtpm(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_vtpm.
        This function supports the option of enable_vtpm.
        When enabled, if both enable_vtpm and disable_vtpm are specified,
        raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        # Read the original value passed by the command.
        disable_vtpm = self.raw_param.get("disable_vtpm")

        # This option is not supported in create mode, hence we do not read the property value from the `mc` object.
        # This parameter does not need dynamic completion.
        if enable_validation:
            if disable_vtpm and self._get_enable_vtpm(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-vtpm and --disable-vtpm at the same time."
                )

        return disable_vtpm

    def get_disable_vtpm(self) -> bool:
        """Obtain the value of disable_vtpm.
        This function will verify the parameter by default.
        If both enable_vtpm and disable_vtpm are specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_disable_vtpm(enable_validation=True)

    def get_enable_secure_boot(self) -> bool:
        return self._get_enable_secure_boot(enable_validation=True)

    def _get_enable_secure_boot(self, enable_validation: bool = False) -> bool:
        """Obtain the value of enable_secure_boot, default value is False.

        :return: bool
        """
        # read the original value passed by the command
        enable_secure_boot = self.raw_param.get("enable_secure_boot", False)

        # In create mode, try and read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            # try to read the property value corresponding to the parameter from the `agentpool` object
            if (
                self.agentpool and
                hasattr(self.agentpool, "security_profile") and
                self.agentpool.security_profile is not None and
                self.agentpool.security_profile.enable_secure_boot is not None
            ):
                enable_secure_boot = self.agentpool.security_profile.enable_secure_boot

        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_secure_boot and self._get_disable_secure_boot(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-secure-boot and --disable-secure-boot at the same time."
                )

        return enable_secure_boot

    def _get_disable_secure_boot(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_secure_boot.
        This function supports the option of enable_secure_boot.
        When enabled, if both enable_secure_boot and disable_secure_boot are specified,
        raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        # Read the original value passed by the command.
        disable_secure_boot = self.raw_param.get("disable_secure_boot")

        # This option is not supported in create mode, hence we do not read the property value from the `mc` object.
        # This parameter does not need dynamic completion.
        if enable_validation:
            if disable_secure_boot and self._get_enable_secure_boot(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-secure-boot and --disable-secure-boot at the same time."
                )

        return disable_secure_boot

    def get_disable_secure_boot(self) -> bool:
        """Obtain the value of disable_secure_boot.
        This function will verify the parameter by default.
        If both enable_secure_boot and disable_secure_boot are specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_disable_secure_boot(enable_validation=True)

    def _get_kubernetes_version(self, read_only: bool = False) -> str:
        """Internal function to dynamically obtain the value of kubernetes_version according to the context.

        If snapshot_id is specified, dynamic completion will be triggerd, and will try to get the corresponding value
        from the Snapshot. When determining the value of the parameter, obtaining from `agentpool` takes precedence over
        user's explicit input over snapshot over default vaule.

        :return: string
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("kubernetes_version")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        value_obtained_from_agentpool = None
        if self.agentpool:
            value_obtained_from_agentpool = self.agentpool.orchestrator_version
        # try to retrieve the value from snapshot
        value_obtained_from_snapshot = None
        # skip dynamic completion if read_only is specified
        if not read_only:
            snapshot = self.get_snapshot()
            if snapshot:
                value_obtained_from_snapshot = snapshot.kubernetes_version

        # set default value
        if value_obtained_from_agentpool is not None:
            kubernetes_version = value_obtained_from_agentpool
        elif raw_value not in [None, ""]:
            kubernetes_version = raw_value
        elif not read_only and value_obtained_from_snapshot is not None:
            kubernetes_version = value_obtained_from_snapshot
        else:
            kubernetes_version = raw_value

        # this parameter does not need validation
        return kubernetes_version

    def get_kubernetes_version(self) -> str:
        """Obtain the value of kubernetes_version.

        :return: string
        """
        return self._get_kubernetes_version(read_only=False)

    def _get_node_vm_size(self, read_only: bool = False) -> str:
        """Internal function to dynamically obtain the value of node_vm_size according to the context.

        If snapshot_id is specified, dynamic completion will be triggerd, and will try to get the corresponding value
        from the Snapshot. When determining the value of the parameter, obtaining from `agentpool` takes precedence over
        user's explicit input over snapshot over default vaule.

        :return: string
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_vm_size")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        value_obtained_from_agentpool = None
        if self.agentpool:
            value_obtained_from_agentpool = self.agentpool.vm_size
        # try to retrieve the value from snapshot
        value_obtained_from_snapshot = None
        # skip dynamic completion if read_only is specified
        if not read_only:
            snapshot = self.get_snapshot()
            if snapshot:
                value_obtained_from_snapshot = snapshot.vm_size

        # set default value
        if value_obtained_from_agentpool is not None:
            node_vm_size = value_obtained_from_agentpool
        elif raw_value is not None:
            node_vm_size = raw_value
        elif not read_only and value_obtained_from_snapshot is not None:
            node_vm_size = value_obtained_from_snapshot
        else:
            if self.get_os_type().lower() == "windows":
                node_vm_size = CONST_DEFAULT_WINDOWS_NODE_VM_SIZE
            else:
                node_vm_size = CONST_DEFAULT_NODE_VM_SIZE

        # this parameter does not need validation
        return node_vm_size

    def get_node_vm_size(self) -> str:
        """Obtain the value of node_vm_size.

        :return: string
        """
        return self._get_node_vm_size(read_only=False)

    def get_vm_sizes(self) -> List[str]:
        """Obtain the value of vm_sizes.

        :return: list of strings
        """
        raw_value = self.raw_param.get("vm_sizes")
        node_vm_size = self.raw_param.get("node_vm_size")
        if raw_value is not None:
            # vm_sizes is a comma-separated string, only used when vm_set_type is VirtualMachines
            if self.get_vm_set_type() != CONST_VIRTUAL_MACHINES:
                raise InvalidArgumentValueError("--vm-sizes can only be used with --vm-set-type VirtualMachines.")
            if node_vm_size:
                raise MutuallyExclusiveArgumentError("Cannot specify -vm-sizes and --node-vm-size at the same time.")
            vm_sizes = [x.strip() for x in raw_value.split(",")]
        else:
            # when vm_sizes is not specified, try to use the value from node_vm_size (only 1 size)
            if node_vm_size:
                vm_sizes = [node_vm_size]
            else:
                # use default value
                if self.get_os_type().lower() == "windows":
                    vm_sizes = [CONST_DEFAULT_WINDOWS_VMS_VM_SIZE]
                else:
                    vm_sizes = [CONST_DEFAULT_VMS_VM_SIZE]

        return vm_sizes

    def _get_os_type(self, read_only: bool = False) -> Union[str, None]:
        """Internal function to dynamically obtain the value of os_type according to the context.

        If snapshot_id is specified, dynamic completion will be triggerd, and will try to get the corresponding value
        from the Snapshot. When determining the value of the parameter, obtaining from `agentpool` takes precedence over
        user's explicit input over snapshot over default vaule.

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("os_type")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        value_obtained_from_agentpool = None
        if self.agentpool:
            value_obtained_from_agentpool = self.agentpool.os_type
        # try to retrieve the value from snapshot
        value_obtained_from_snapshot = None
        # skip dynamic completion if read_only is specified
        if not read_only:
            snapshot = self.get_snapshot()
            if snapshot:
                value_obtained_from_snapshot = snapshot.os_type
        # set default value
        if value_obtained_from_agentpool is not None:
            os_type = value_obtained_from_agentpool
        elif raw_value is not None:
            os_type = raw_value
        elif not read_only and value_obtained_from_snapshot is not None:
            os_type = value_obtained_from_snapshot
        else:
            os_type = CONST_DEFAULT_NODE_OS_TYPE
        # validation
        if (
            self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER and
            self.decorator_mode == DecoratorMode.CREATE
        ):
            if os_type.lower() == "windows":
                raise InvalidArgumentValueError("System node pool must be linux.")
        # validation of Windows OS SKU's against OS Type
        if (
            self.agentpool_decorator_mode == AgentPoolDecoratorMode.STANDALONE and
            self.decorator_mode == DecoratorMode.CREATE and
            os_type == CONST_DEFAULT_NODE_OS_TYPE
        ):
            # read the original value passed by the command
            raw_os_sku = self.raw_param.get("os_sku")
            sku_2019 = CONST_OS_SKU_WINDOWS2019
            sku_2022 = CONST_OS_SKU_WINDOWS2022
            if raw_os_sku == sku_2019 or raw_os_sku == sku_2022:
                raise InvalidArgumentValueError(
                    "OS SKU is invalid for Linux OS Type."
                    " Please specify '--os-type Windows' for Windows SKUs"
                )
        return os_type

    def get_os_type(self) -> Union[str, None]:
        """Obtain the value of os_type.

        :return: string or None
        """
        return self._get_os_type(read_only=False)

    def _get_os_sku(self, read_only: bool = False) -> Union[str, None]:
        """Internal function to dynamically obtain the value of os_sku according to the context.

        If snapshot_id is specified, dynamic completion will be triggerd, and will try to get the corresponding value
        from the Snapshot. When determining the value of the parameter, obtaining from `agentpool` takes precedence over
        user's explicit input over snapshot over default vaule.

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("os_sku")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        value_obtained_from_agentpool = None
        if self.agentpool and hasattr(self.agentpool, "os_sku"):    # backward compatibility
            value_obtained_from_agentpool = self.agentpool.os_sku
        # try to retrieve the value from snapshot
        value_obtained_from_snapshot = None
        # skip dynamic completion if read_only is specified
        if not read_only:
            snapshot = self.get_snapshot()
            if snapshot:
                value_obtained_from_snapshot = snapshot.os_sku

        # set default value
        if self.decorator_mode == DecoratorMode.CREATE and value_obtained_from_agentpool is not None:
            os_sku = value_obtained_from_agentpool
        elif raw_value is not None:
            os_sku = raw_value
        elif not read_only and value_obtained_from_snapshot is not None:
            os_sku = value_obtained_from_snapshot
        else:
            os_sku = raw_value
        # this parameter does not need validation
        return os_sku

    def get_os_sku(self) -> Union[str, None]:
        """Obtain the value of os_sku.

        :return: string or None
        """
        return self._get_os_sku(read_only=False)

    def get_vnet_subnet_id(self) -> Union[str, None]:
        """Obtain the value of vnet_subnet_id.

        :return: string or None
        """
        # read the original value passed by the command
        vnet_subnet_id = self.raw_param.get("vnet_subnet_id")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.vnet_subnet_id is not None:
            vnet_subnet_id = self.agentpool.vnet_subnet_id

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return vnet_subnet_id

    def get_pod_subnet_id(self) -> Union[str, None]:
        """Obtain the value of pod_subnet_id.

        :return: string or None
        """
        # read the original value passed by the command
        pod_subnet_id = self.raw_param.get("pod_subnet_id")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.pod_subnet_id is not None:
            pod_subnet_id = self.agentpool.pod_subnet_id

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return pod_subnet_id

    def get_pod_ip_allocation_mode(self: bool = False) -> Union[str, None]:
        """Get the value of pod_ip_allocation_mode.

        :return: str or None
        """

        # Get the value of pod_ip_allocation_mode from the raw parameters provided by the user
        pod_ip_allocation_mode = self.raw_param.get("pod_ip_allocation_mode")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        # if it exists and user has not provided any value in raw parameters
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                pod_ip_allocation_mode and
                self.agentpool and
                self.agentpool.pod_ip_allocation_mode is not None
            ):
                pod_ip_allocation_mode = self.agentpool.pod_ip_allocation_mode

        return pod_ip_allocation_mode

    def get_enable_node_public_ip(self) -> bool:
        """Obtain the value of enable_node_public_ip, default value is False.

        :return: bool
        """
        # read the original value passed by the command
        enable_node_public_ip = self.raw_param.get("enable_node_public_ip", False)
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.enable_node_public_ip is not None:
            enable_node_public_ip = self.agentpool.enable_node_public_ip

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_node_public_ip

    def get_node_public_ip_prefix_id(self) -> Union[str, None]:
        """Obtain the value of node_public_ip_prefix_id.

        :return: string or None
        """
        # read the original value passed by the command
        node_public_ip_prefix_id = self.raw_param.get("node_public_ip_prefix_id")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if (
            self.agentpool and
            hasattr(self.agentpool, "node_public_ip_prefix_id") and     # backward compatibility
            self.agentpool.node_public_ip_prefix_id is not None
        ):
            node_public_ip_prefix_id = self.agentpool.node_public_ip_prefix_id

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_public_ip_prefix_id

    def get_node_count_and_enable_cluster_autoscaler_min_max_count(
        self,
    ) -> Tuple[int, bool, Union[int, None], Union[int, None]]:
        """Obtain the value of node_count, enable_cluster_autoscaler, min_count and max_count.

        This function will verify the parameters through function "__validate_counts_in_autoscaler" by default.

        :return: a tuple containing four elements: node_count of int type, enable_cluster_autoscaler of bool type,
        min_count of int type or None and max_count of int type or None
        """
        # node_count
        # read the original value passed by the command
        node_count = self.raw_param.get("node_count")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.count is not None:
            node_count = self.agentpool.count

        # enable_cluster_autoscaler
        # read the original value passed by the command
        enable_cluster_autoscaler = self.raw_param.get("enable_cluster_autoscaler", False)
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.enable_auto_scaling is not None:
            enable_cluster_autoscaler = self.agentpool.enable_auto_scaling

        # min_count
        # read the original value passed by the command
        min_count = self.raw_param.get("min_count")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.min_count is not None:
            min_count = self.agentpool.min_count

        # max_count
        # read the original value passed by the command
        max_count = self.raw_param.get("max_count")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.max_count is not None:
            max_count = self.agentpool.max_count

        # these parameters do not need dynamic completion

        # validation
        self.__validate_counts_in_autoscaler(
            node_count,
            enable_cluster_autoscaler,
            min_count,
            max_count,
            mode=self.get_mode(),
            decorator_mode=DecoratorMode.CREATE,
        )
        return node_count, enable_cluster_autoscaler, min_count, max_count

    def get_update_enable_disable_cluster_autoscaler_and_min_max_count(
        self,
    ) -> Tuple[bool, bool, bool, Union[int, None], Union[int, None]]:
        """Obtain the value of update_cluster_autoscaler, enable_cluster_autoscaler, disable_cluster_autoscaler,
        min_count and max_count.

        This function will verify the parameters through function "__validate_counts_in_autoscaler" by default. Besides
        if both enable_cluster_autoscaler and update_cluster_autoscaler are specified, a MutuallyExclusiveArgumentError
        will be raised. If enable_cluster_autoscaler or update_cluster_autoscaler is specified and there are multiple
        agent pool profiles, an ArgumentUsageError will be raised. If enable_cluster_autoscaler is specified and
        autoscaler is already enabled in `mc`, it will output warning messages and exit with code 0. If
        update_cluster_autoscaler is specified and autoscaler is not enabled in `mc`, it will raise an
        InvalidArgumentValueError. If disable_cluster_autoscaler is specified and autoscaler is not enabled in `mc`,
        it will output warning messages and exit with code 0.

        :return: a tuple containing four elements: update_cluster_autoscaler of bool type, enable_cluster_autoscaler
        of bool type, disable_cluster_autoscaler of bool type, min_count of int type or None and max_count of int type
        or None
        """
        # update_cluster_autoscaler
        # read the original value passed by the command
        update_cluster_autoscaler = self.raw_param.get("update_cluster_autoscaler", False)

        # enable_cluster_autoscaler
        # read the original value passed by the command
        enable_cluster_autoscaler = self.raw_param.get("enable_cluster_autoscaler", False)

        # disable_cluster_autoscaler
        # read the original value passed by the command
        disable_cluster_autoscaler = self.raw_param.get("disable_cluster_autoscaler", False)

        # min_count
        # read the original value passed by the command
        min_count = self.raw_param.get("min_count")

        # max_count
        # read the original value passed by the command
        max_count = self.raw_param.get("max_count")

        # these parameters do not need dynamic completion

        # validation
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            # For multi-agent pool, use the az aks nodepool command
            if (enable_cluster_autoscaler or update_cluster_autoscaler) and len(self._agentpools) > 1:
                raise ArgumentUsageError(
                    'There are more than one node pool in the cluster. Please use "az aks nodepool" command '
                    "to update per node pool auto scaler settings"
                )

        if enable_cluster_autoscaler + update_cluster_autoscaler + disable_cluster_autoscaler > 1:
            raise MutuallyExclusiveArgumentError(
                "Can only specify one of --enable-cluster-autoscaler, --update-cluster-autoscaler and "
                "--disable-cluster-autoscaler"
            )

        self.__validate_counts_in_autoscaler(
            None,
            enable_cluster_autoscaler or update_cluster_autoscaler,
            min_count,
            max_count,
            mode=self.get_mode(),
            decorator_mode=DecoratorMode.UPDATE,
        )

        if enable_cluster_autoscaler and self.agentpool.enable_auto_scaling:
            logger.warning(
                "Cluster autoscaler is already enabled for this node pool.\n"
                'Please run "az aks --update-cluster-autoscaler" '
                "if you want to update min-count or max-count."
            )
            raise DecoratorEarlyExitException()

        if update_cluster_autoscaler and not self.agentpool.enable_auto_scaling:
            raise InvalidArgumentValueError(
                "Cluster autoscaler is not enabled for this node pool.\n"
                'Run "az aks nodepool update --enable-cluster-autoscaler" '
                "to enable cluster with min-count and max-count."
            )

        if disable_cluster_autoscaler and not self.agentpool.enable_auto_scaling:
            logger.warning(
                "Cluster autoscaler is already disabled for this node pool."
            )
            raise DecoratorEarlyExitException()

        return update_cluster_autoscaler, enable_cluster_autoscaler, disable_cluster_autoscaler, min_count, max_count

    def get_priority(self) -> str:
        """Obtain the value of priority, default value is CONST_SCALE_SET_PRIORITY_REGULAR.

        :return: string
        """
        # read the original value passed by the command
        priority = self.raw_param.get("priority", CONST_SCALE_SET_PRIORITY_REGULAR)
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.scale_set_priority is not None:
            priority = self.agentpool.scale_set_priority

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return priority

    def get_eviction_policy(self) -> str:
        """Obtain the value of eviction_policy, default value is CONST_SPOT_EVICTION_POLICY_DELETE.

        :return: string
        """
        # read the original value passed by the command
        eviction_policy = self.raw_param.get("eviction_policy", CONST_SPOT_EVICTION_POLICY_DELETE)
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.scale_set_eviction_policy is not None:
            eviction_policy = self.agentpool.scale_set_eviction_policy

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return eviction_policy

    def get_spot_max_price(self) -> float:
        """Obtain the value of spot_max_price, default value is float('nan').

        :return: float
        """
        # read the original value passed by the command
        spot_max_price = self.raw_param.get("spot_max_price", float('nan'))
        # normalize
        if isnan(spot_max_price):
            spot_max_price = -1

        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.spot_max_price is not None:
            spot_max_price = self.agentpool.spot_max_price

        # this parameter does not need validation
        return spot_max_price

    def get_nodepool_labels(self) -> Union[Dict[str, str], None]:
        """Obtain the value of nodepool_labels.

        :return: dictionary or None
        """
        # read the original value passed by the command
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            nodepool_labels = self.raw_param.get("nodepool_labels")
        else:
            nodepool_labels = self.raw_param.get("labels")

        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.agentpool and self.agentpool.node_labels is not None:
                nodepool_labels = self.agentpool.node_labels

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nodepool_labels

    def get_nodepool_tags(self) -> Union[Dict[str, str], None]:
        """Obtain the value of nodepool_tags.

        :return: dictionary or None
        """
        # read the original value passed by the command
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            nodepool_tags = self.raw_param.get("nodepool_tags")
        else:
            nodepool_tags = self.raw_param.get("tags")

        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.agentpool and self.agentpool.tags is not None:
                nodepool_tags = self.agentpool.tags

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nodepool_tags

    def get_node_taints(self) -> Union[List[str], None]:
        """Obtain the value of node_taints.

        :return: empty list, list of strings or None
        """
        # read the original value passed by the command
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            node_taints = self.raw_param.get("nodepool_taints")
        else:
            node_taints = self.raw_param.get("node_taints")
        # normalize, default is an empty list
        if node_taints is not None:
            node_taints = [x.strip() for x in (node_taints.split(",") if node_taints else [])]
        # keep None as None for update mode
        if node_taints is None and self.decorator_mode == DecoratorMode.CREATE:
            node_taints = []

        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.agentpool and self.agentpool.node_taints is not None:
                node_taints = self.agentpool.node_taints

        # this parameter does not need validation
        return node_taints

    def get_node_osdisk_size(self) -> Union[int, None]:
        """Obtain the value of node_osdisk_size.

        Note: SDK performs the following validation {'maximum': 2048, 'minimum': 0}.

        This function will normalize the parameter by default. The parameter will be converted to int.

        :return: int or None
        """
        # read the original value passed by the command
        node_osdisk_size = self.raw_param.get("node_osdisk_size")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.os_disk_size_gb is not None:
            node_osdisk_size = self.agentpool.os_disk_size_gb

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_osdisk_size

    def get_node_osdisk_type(self) -> Union[str, None]:
        """Obtain the value of node_osdisk_type.

        :return: string or None
        """
        # read the original value passed by the command
        node_osdisk_type = self.raw_param.get("node_osdisk_type")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.os_disk_type is not None:
            node_osdisk_type = self.agentpool.os_disk_type

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_osdisk_type

    def get_max_surge(self):
        """Obtain the value of max_surge.

        :return: string
        """
        # read the original value passed by the command
        max_surge = self.raw_param.get("max_surge")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                self.agentpool.upgrade_settings and
                self.agentpool.upgrade_settings.max_surge is not None
            ):
                max_surge = self.agentpool.upgrade_settings.max_surge

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return max_surge

    def get_max_unavailable(self):
        """Obtain the value of max_unavailable.
        :return: string
        """
        # read the original value passed by the command
        max_unavailable = self.raw_param.get("max_unavailable")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                self.agentpool.upgrade_settings and
                self.agentpool.upgrade_settings.max_unavailable is not None
            ):
                max_unavailable = self.agentpool.upgrade_settings.max_unavailable

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return max_unavailable

    def get_drain_timeout(self):
        """Obtain the value of drain_timeout.

        :return: int
        """
        # read the original value passed by the command
        drain_timeout = self.raw_param.get("drain_timeout")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                self.agentpool.upgrade_settings and
                self.agentpool.upgrade_settings.drain_timeout_in_minutes is not None
            ):
                drain_timeout = self.agentpool.upgrade_settings.drain_timeout_in_minutes

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return drain_timeout

    def get_node_soak_duration(self):
        """Obtain the value of node_soak_duration.

        :return: int
        """
        # read the original value passed by the command
        node_soak_duration = self.raw_param.get("node_soak_duration")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                self.agentpool.upgrade_settings and
                self.agentpool.upgrade_settings.node_soak_duration_in_minutes is not None
            ):
                node_soak_duration = self.agentpool.upgrade_settings.node_soak_duration_in_minutes

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_soak_duration

    def get_undrainable_node_behavior(self) -> str:
        """Obtain the value of undrainable_node_behavior.

        :return: string
        """
        # read the original value passed by the command
        undrainable_node_behavior = self.raw_param.get("undrainable_node_behavior")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                self.agentpool.upgrade_settings and
                self.agentpool.upgrade_settings.undrainable_node_behavior is not None
            ):
                undrainable_node_behavior = self.agentpool.upgrade_settings.undrainable_node_behavior

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return undrainable_node_behavior

    def get_vm_set_type(self) -> str:
        """Obtain the value of vm_set_type, default value is CONST_VIRTUAL_MACHINE_SCALE_SETS.

        :return: string
        """
        # read the original value passed by the command
        vm_set_type = self.raw_param.get("vm_set_type", CONST_VIRTUAL_MACHINE_SCALE_SETS)
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            if self.agentpool and self.agentpool.type is not None:
                vm_set_type = self.agentpool.type
        else:
            if self.agentpool and self.agentpool.type_properties_type is not None:
                vm_set_type = self.agentpool.type_properties_type

        # normalize
        if vm_set_type.lower() == CONST_VIRTUAL_MACHINE_SCALE_SETS.lower():
            vm_set_type = CONST_VIRTUAL_MACHINE_SCALE_SETS
        elif vm_set_type.lower() == CONST_AVAILABILITY_SET.lower():
            vm_set_type = CONST_AVAILABILITY_SET
        elif vm_set_type.lower() == CONST_VIRTUAL_MACHINES.lower():
            vm_set_type = CONST_VIRTUAL_MACHINES
        else:
            raise InvalidArgumentValueError(
                "--vm-set-type can only be VirtualMachineScaleSets or AvailabilitySet or VirtualMachines"
            )
        # this parameter does not need validation
        return vm_set_type

    def get_ppg(self) -> Union[str, None]:
        """Obtain the value of ppg (proximity_placement_group_id).

        :return: string or None
        """
        # read the original value passed by the command
        ppg = self.raw_param.get("ppg")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.proximity_placement_group_id is not None:
            ppg = self.agentpool.proximity_placement_group_id

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return ppg

    def get_enable_encryption_at_host(self) -> bool:
        """Obtain the value of enable_encryption_at_host, default value is False.

        :return: bool
        """
        # read the original value passed by the command
        enable_encryption_at_host = self.raw_param.get("enable_encryption_at_host", False)
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if (
            self.agentpool and
            hasattr(self.agentpool, "enable_encryption_at_host") and     # backward compatibility
            self.agentpool.enable_encryption_at_host is not None
        ):
            enable_encryption_at_host = self.agentpool.enable_encryption_at_host

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_encryption_at_host

    def get_enable_ultra_ssd(self) -> bool:
        """Obtain the value of enable_ultra_ssd, default value is False.

        :return: bool
        """
        # read the original value passed by the command
        enable_ultra_ssd = self.raw_param.get("enable_ultra_ssd", False)
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if (
            self.agentpool and
            hasattr(self.agentpool, "enable_ultra_ssd") and     # backward compatibility
            self.agentpool.enable_ultra_ssd is not None
        ):
            enable_ultra_ssd = self.agentpool.enable_ultra_ssd

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_ultra_ssd

    # Mutable Fips now allows changes after create
    def get_enable_fips_image(self) -> bool:
        """Obtain the value of enable_fips_image, default value is False.
        :return: bool
        """

        # read the original value passed by the command
        enable_fips_image = self.raw_param.get("enable_fips_image", False)
        # In create mode, try and read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                hasattr(self.agentpool, "enable_fips") and      # backward compatibility
                self.agentpool.enable_fips is not None
            ):
                enable_fips_image = self.agentpool.enable_fips

        # Verify both flags have not been set
        if enable_fips_image and self.get_disable_fips_image():
            raise MutuallyExclusiveArgumentError(
                'Cannot specify "--enable-fips-image" and "--disable-fips-image" at the same time'
            )

        return enable_fips_image

    def get_disable_fips_image(self) -> bool:
        """Obtain the value of disable_fips_image.
        :return: bool
        """
        # read the original value passed by the command
        return self.raw_param.get("disable_fips_image")

    def get_zones(self) -> Union[List[str], None]:
        """Obtain the value of zones.

        :return: list of strings or None
        """
        # read the original value passed by the command
        zones = self.raw_param.get("zones")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.availability_zones is not None:
            zones = self.agentpool.availability_zones

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return zones

    def get_max_pods(self) -> Union[int, None]:
        """Obtain the value of max_pods.

        This function will normalize the parameter by default. Int 0 would be converted to None.

        :return: int or None
        """
        # read the original value passed by the command
        max_pods = self.raw_param.get("max_pods")
        # normalize
        if max_pods == 0:  # 0 is not a valid value
            max_pods = None

        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.max_pods is not None:
            max_pods = self.agentpool.max_pods

        # this parameter does not need validation
        return max_pods

    def get_mode(self) -> str:
        """Obtain the value of mode, default value is CONST_NODEPOOL_MODE_SYSTEM for managed cluster mode,
        CONST_NODEPOOL_MODE_USER for standalone mode.

        :return: string
        """
        # read the original value passed by the command
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
                mode = self.raw_param.get("mode", CONST_NODEPOOL_MODE_SYSTEM)
            else:
                mode = self.raw_param.get("mode", CONST_NODEPOOL_MODE_USER)
        else:
            mode = self.raw_param.get("mode")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.agentpool and self.agentpool.mode is not None:
                mode = self.agentpool.mode

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return mode

    def get_scale_down_mode(self) -> str:
        """Obtain the value of scale_down_mode, default value is CONST_SCALE_DOWN_MODE_DELETE for standalone mode.

        :return: string
        """
        # read the original value passed by the command
        if (
            self.decorator_mode == DecoratorMode.CREATE and
            self.agentpool_decorator_mode == AgentPoolDecoratorMode.STANDALONE
        ):
            scale_down_mode = self.raw_param.get("scale_down_mode", CONST_SCALE_DOWN_MODE_DELETE)
        else:
            scale_down_mode = self.raw_param.get("scale_down_mode")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                hasattr(self.agentpool, "scale_down_mode") and      # backward compatibility
                self.agentpool.scale_down_mode is not None
            ):
                scale_down_mode = self.agentpool.scale_down_mode

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return scale_down_mode

    def get_kubelet_config(self) -> Union[Dict, KubeletConfig, None]:
        """Obtain the value of kubelet_config.

        :return: dictionary, KubeletConfig or None
        """
        # read the original value passed by the command
        kubelet_config = None
        kubelet_config_file_path = self.raw_param.get("kubelet_config")
        # validate user input
        if kubelet_config_file_path:
            if not os.path.isfile(kubelet_config_file_path):
                raise InvalidArgumentValueError(
                    "{} is not valid file, or not accessable.".format(
                        kubelet_config_file_path
                    )
                )
            kubelet_config = get_file_json(kubelet_config_file_path)
            if not isinstance(kubelet_config, dict):
                raise InvalidArgumentValueError(
                    "Error reading kubelet configuration from {}. "
                    "Please see https://aka.ms/CustomNodeConfig for correct format.".format(
                        kubelet_config_file_path
                    )
                )

        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.kubelet_config is not None:
            kubelet_config = self.agentpool.kubelet_config

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return kubelet_config

    def get_linux_os_config(self) -> Union[Dict, LinuxOSConfig, None]:
        """Obtain the value of linux_os_config.

        :return: dictionary, LinuxOSConfig or None
        """
        # read the original value passed by the command
        linux_os_config = None
        linux_os_config_file_path = self.raw_param.get("linux_os_config")
        # validate user input
        if linux_os_config_file_path:
            if not os.path.isfile(linux_os_config_file_path):
                raise InvalidArgumentValueError(
                    "{} is not valid file, or not accessable.".format(
                        linux_os_config_file_path
                    )
                )
            linux_os_config = get_file_json(linux_os_config_file_path)
            if not isinstance(linux_os_config, dict):
                raise InvalidArgumentValueError(
                    "Error reading Linux OS configuration from {}. "
                    "Please see https://aka.ms/CustomNodeConfig for correct format.".format(
                        linux_os_config_file_path
                    )
                )

        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.linux_os_config:
            linux_os_config = self.agentpool.linux_os_config

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return linux_os_config

    def get_aks_custom_headers(self) -> Dict[str, str]:
        """Obtain the value of aks_custom_headers.

        Note: aks_custom_headers will not be decorated into the `agentpool` object.

        This function will normalize the parameter by default. It will call "extract_comma_separated_string" to extract
        comma-separated key value pairs from the string.

        :return: dictionary
        """
        # read the original value passed by the command
        aks_custom_headers = self.raw_param.get("aks_custom_headers")
        # normalize user-provided header, extract key-value pairs with comma as separator
        # used to enable (preview) features through custom header field or AKSHTTPCustomFeatures (internal only)
        aks_custom_headers = extract_comma_separated_string(
            aks_custom_headers,
            enable_strip=True,
            extract_kv=True,
            default_value={},
            allow_appending_values_to_same_key=True,
        )

        # this parameter does not need validation
        return aks_custom_headers

    def get_no_wait(self) -> bool:
        """Obtain the value of no_wait, default value is False.

        Note: no_wait will not be decorated into the `agentpool` object.

        :return: bool
        """
        # read the original value passed by the command
        no_wait = self.raw_param.get("no_wait", False)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return no_wait

    def get_gpu_instance_profile(self) -> Union[str, None]:
        """Obtain the value of gpu_instance_profile.

        :return: string or None
        """
        # read the original value passed by the command
        gpu_instance_profile = self.raw_param.get("gpu_instance_profile")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.agentpool and
            hasattr(self.agentpool, "gpu_instance_profile") and
            self.agentpool.gpu_instance_profile is not None
        ):
            gpu_instance_profile = self.agentpool.gpu_instance_profile

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return gpu_instance_profile

    def get_asg_ids(self) -> Union[List[str], None]:
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            asg_ids = self.raw_param.get('nodepool_asg_ids')
        else:
            asg_ids = self.raw_param.get('asg_ids')

        return asg_ids

    def get_allowed_host_ports(self) -> Union[List[PortRange], None]:
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            ports = self.raw_param.get('nodepool_allowed_host_ports')
        else:
            ports = self.raw_param.get('allowed_host_ports')

        if ports is None:
            return None

        port_ranges = []
        import re
        # Parse the port range. The format is either `<int>/<protocol>` or `<int>-<int>/<protocol>`.
        # e.g. `80/tcp` | `22/udp` | `4000-5000/tcp`
        regex = re.compile(r'^((\d+)|((\d+)-(\d+)))/(tcp|udp)$')
        for port in ports:
            r = regex.findall(port.lower())
            if r[0][1] != '':
                # single port
                port_start, port_end = int(r[0][1]), int(r[0][1])
            else:
                # port range
                port_start, port_end = int(r[0][3]), int(r[0][4])
            port_ranges.append(self.models.PortRange(
                port_start=port_start,
                port_end=port_end,
                protocol=r[0][5].upper(),
            ))
        return port_ranges

    def get_ip_tags(self) -> Union[List[IPTag], None]:
        ip_tags = self.raw_param.get("node_public_ip_tags")
        res = []
        if ip_tags:
            for k, v in ip_tags.items():
                res.append(self.models.IPTag(
                    ip_tag_type=k,
                    tag=v,
                ))
        return res

    def _get_disable_windows_outbound_nat(self) -> bool:
        """Internal function to obtain the value of disable_windows_outbound_nat.

        :return: bool
        """
        # read the original value passed by the command
        disable_windows_outbound_nat = self.raw_param.get("disable_windows_outbound_nat")
        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                hasattr(self.agentpool, "windows_profile") and
                self.agentpool.windows_profile and
                self.agentpool.windows_profile.disable_outbound_nat is not None
            ):
                disable_windows_outbound_nat = self.agentpool.windows_profile.disable_outbound_nat

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return disable_windows_outbound_nat

    def get_disable_windows_outbound_nat(self) -> bool:
        """Obtain the value of disable_windows_outbound_nat.

        :return: bool
        """
        return self._get_disable_windows_outbound_nat()

    def get_if_match(self) -> str:
        """Obtain the value of if_match.

        :return: string
        """
        return self.raw_param.get("if_match")

    def get_if_none_match(self) -> str:
        """Obtain the value of if_none_match.

        :return: string
        """
        return self.raw_param.get("if_none_match")

    def _get_gpu_driver(self) -> Union[str, None]:
        """Obtain the value of gpu_driver.

        :return: string
        """
        # read the original value passed by the command
        gpu_driver = self.raw_param.get("gpu_driver")

        # In create mode, try to read the property value corresponding to the parameter from the `agentpool` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.agentpool and
                hasattr(self.agentpool, "gpu_profile") and      # backward compatibility
                self.agentpool.gpu_profile and
                self.agentpool.gpu_profile.driver is not None
            ):
                gpu_driver = self.agentpool.gpu_profile.driver

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return gpu_driver

    def get_gpu_driver(self) -> Union[str, None]:
        """Obtain the value of gpu_driver.

        :return: string or None
        """
        return self._get_gpu_driver()

    def get_gateway_prefix_size(self) -> Union[int, None]:
        """Obtain the value of gateway_prefix_size.

        :return: int or None
        """
        return self.raw_param.get('gateway_prefix_size')


class AKSAgentPoolAddDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client: AgentPoolsOperations,
        raw_parameters: Dict,
        resource_type: ResourceType,
        agentpool_decorator_mode: AgentPoolDecoratorMode,
    ):
        """Internal controller of aks_agentpool_add.

        Break down the all-in-one aks_agentpool_add function into several relatively independent functions (some of
        them have a certain order dependency) that only focus on a specific profile or process a specific piece of
        logic. In addition, an overall control function is provided. By calling the aforementioned independent functions
        one by one, a complete AgentPool object is gradually decorated and finally requests are sent to create a node
        pool.
        """
        self.cmd = cmd
        self.client = client
        self.__raw_parameters = raw_parameters
        self.resource_type = resource_type
        self.agentpool_decorator_mode = agentpool_decorator_mode
        self.init_models()
        self.init_context()

    def init_models(self) -> None:
        """Initialize an AKSAgentPoolModels object to store the models.

        :return: None
        """
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)

    def init_context(self) -> None:
        """Initialize an AKSManagedClusterContext object to store the context in the process of assemble the
        AgentPool object.

        :return: None
        """
        self.context = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(self.__raw_parameters),
            self.models,
            DecoratorMode.CREATE,
            self.agentpool_decorator_mode,
        )

    def _ensure_agentpool(self, agentpool: AgentPool) -> None:
        """Internal function to ensure that the incoming `agentpool` object is valid and the same as the attached
        `agentpool` object in the context.

        If the incoming `agentpool` is not valid or is inconsistent with the `agentpool` in the context, raise a
        CLIInternalError.

        :return: None
        """
        if not isinstance(agentpool, self.models.UnifiedAgentPoolModel):
            raise CLIInternalError(
                "Unexpected agentpool object with type '{}'.".format(type(agentpool))
            )

        if self.context.agentpool != agentpool:
            raise CLIInternalError(
                "Inconsistent state detected. The incoming `agentpool` "
                "is not the same as the `agentpool` in the context."
            )

    def _remove_defaults_in_agentpool(self, agentpool: AgentPool) -> AgentPool:
        """Internal function to remove values from properties with default values of the `agentpool` object.

        Removing default values is to prevent getters from mistakenly overwriting user provided values with default
        values in the object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        defaults_in_agentpool = {}
        for attr_name, attr_value in vars(agentpool).items():
            if not attr_name.startswith("_") and attr_name != "name" and attr_value is not None:
                defaults_in_agentpool[attr_name] = attr_value
                setattr(agentpool, attr_name, None)
        self.context.set_intermediate("defaults_in_agentpool", defaults_in_agentpool, overwrite_exists=True)
        return agentpool

    def _restore_defaults_in_agentpool(self, agentpool: AgentPool) -> AgentPool:
        """Internal function to restore values of properties with default values of the `agentpool` object.

        Restoring default values is to keep the content of the request sent by cli consistent with that before the
        refactoring.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        defaults_in_agentpool = self.context.get_intermediate("defaults_in_agentpool", {})
        for key, value in defaults_in_agentpool.items():
            if getattr(agentpool, key, None) is None:
                setattr(agentpool, key, value)
        return agentpool

    def init_agentpool(self) -> AgentPool:
        """Initialize an AgentPool object with name and attach it to internal context.

        :return: the AgentPool object
        """
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            # Note: As a required property, name must be provided during initialization.
            agentpool = self.models.UnifiedAgentPoolModel(name=self.context.get_nodepool_name())
        else:
            # Note: As a read only property, name would be ignored when serialized.
            # Set the name property by explicit assignment, otherwise it will be ignored by initialization.
            agentpool = self.models.UnifiedAgentPoolModel()
            agentpool.name = self.context.get_nodepool_name()

        # attach agentpool to AKSAgentPoolContext
        self.context.attach_agentpool(agentpool)
        return agentpool

    def set_up_snapshot_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up auto snapshot related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        creation_data = None
        snapshot_id = self.context.get_snapshot_id()
        if snapshot_id:
            creation_data = self.models.CreationData(
                source_resource_id=snapshot_id
            )
        agentpool.creation_data = creation_data

        agentpool.orchestrator_version = self.context.get_kubernetes_version()
        agentpool.vm_size = self.context.get_node_vm_size()
        agentpool.os_type = self.context.get_os_type()
        agentpool.os_sku = self.context.get_os_sku()
        return agentpool

    def set_up_host_group_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up host group related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.host_group_id = self.context.get_host_group_id()
        return agentpool

    def set_up_node_network_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up priority related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.vnet_subnet_id = self.context.get_vnet_subnet_id()
        agentpool.pod_subnet_id = self.context.get_pod_subnet_id()
        agentpool.pod_ip_allocation_mode = self.context.get_pod_ip_allocation_mode()
        agentpool.enable_node_public_ip = self.context.get_enable_node_public_ip()
        agentpool.node_public_ip_prefix_id = self.context.get_node_public_ip_prefix_id()
        return agentpool

    def set_up_auto_scaler_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up auto scaler related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        (
            node_count,
            enable_auto_scaling,
            min_count,
            max_count,
        ) = (
            self.context.get_node_count_and_enable_cluster_autoscaler_min_max_count()
        )
        agentpool.count = node_count
        agentpool.enable_auto_scaling = enable_auto_scaling
        agentpool.min_count = min_count
        agentpool.max_count = max_count
        return agentpool

    def set_up_priority_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up priority related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        priority = self.context.get_priority()
        agentpool.scale_set_priority = priority
        if priority == CONST_SCALE_SET_PRIORITY_SPOT:
            agentpool.scale_set_eviction_policy = self.context.get_eviction_policy()
            agentpool.spot_max_price = self.context.get_spot_max_price()
        return agentpool

    def set_up_label_tag_taint(self, agentpool: AgentPool) -> AgentPool:
        """Set up label, tag, taint for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.tags = self.context.get_nodepool_tags()
        agentpool.node_labels = self.context.get_nodepool_labels()
        agentpool.node_taints = self.context.get_node_taints()
        return agentpool

    def set_up_osdisk_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up os disk related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.os_disk_size_gb = self.context.get_node_osdisk_size()
        agentpool.os_disk_type = self.context.get_node_osdisk_type()
        return agentpool

    def set_up_upgrade_settings(self, agentpool: AgentPool) -> AgentPool:
        """Set up upgrade settings for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        upgrade_settings = self.models.AgentPoolUpgradeSettings()
        max_surge = self.context.get_max_surge()
        if max_surge:
            upgrade_settings.max_surge = max_surge

        max_unavailable = self.context.get_max_unavailable()
        if max_unavailable:
            upgrade_settings.max_unavailable = max_unavailable

        drain_timeout = self.context.get_drain_timeout()
        if drain_timeout:
            upgrade_settings.drain_timeout_in_minutes = drain_timeout

        node_soak_duration = self.context.get_node_soak_duration()
        if node_soak_duration:
            upgrade_settings.node_soak_duration_in_minutes = node_soak_duration

        undrainable_node_behavior = self.context.get_undrainable_node_behavior()
        if undrainable_node_behavior:
            upgrade_settings.undrainable_node_behavior = undrainable_node_behavior

        agentpool.upgrade_settings = upgrade_settings
        return agentpool

    def set_up_vm_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up vm related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            agentpool.type = self.context.get_vm_set_type()
        else:
            agentpool.type_properties_type = self.context.get_vm_set_type()

        agentpool.proximity_placement_group_id = self.context.get_ppg()
        agentpool.enable_encryption_at_host = self.context.get_enable_encryption_at_host()
        agentpool.enable_ultra_ssd = self.context.get_enable_ultra_ssd()
        agentpool.enable_fips = self.context.get_enable_fips_image()
        agentpool.availability_zones = self.context.get_zones()

        agentpool.max_pods = self.context.get_max_pods()
        agentpool.mode = self.context.get_mode()
        agentpool.scale_down_mode = self.context.get_scale_down_mode()
        return agentpool

    def set_up_custom_node_config(self, agentpool: AgentPool) -> AgentPool:
        """Set up custom node config for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.kubelet_config = self.context.get_kubelet_config()
        agentpool.linux_os_config = self.context.get_linux_os_config()
        return agentpool

    def set_up_motd(self, agentpool: AgentPool) -> AgentPool:
        """Set up message of the day for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.message_of_the_day = self.context.get_message_of_the_day()
        return agentpool

    def set_up_gpu_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up gpu related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.gpu_instance_profile = self.context.get_gpu_instance_profile()
        return agentpool

    def set_up_crg_id(self, agentpool: AgentPool) -> AgentPool:
        """Set up crg related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)
        agentpool.capacity_reservation_group_id = self.context.get_crg_id()
        return agentpool

    def set_up_agentpool_security_profile(self, agentpool: AgentPool) -> AgentPool:
        """Set up security profile for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        enable_vtpm = self.context.get_enable_vtpm()
        enable_secure_boot = self.context.get_enable_secure_boot()

        # Construct AgentPoolSecurityProfile if one of the fields has been set
        if enable_vtpm:
            agentpool.security_profile = self.models.AgentPoolSecurityProfile()  # pylint: disable=no-member
            agentpool.security_profile.enable_vtpm = enable_vtpm

        if enable_secure_boot:
            if not agentpool.security_profile:
                agentpool.security_profile = self.models.AgentPoolSecurityProfile()  # pylint: disable=no-member
            agentpool.security_profile.enable_secure_boot = enable_secure_boot

        return agentpool

    def set_up_agentpool_network_profile(self, agentpool: AgentPool) -> AgentPool:
        self._ensure_agentpool(agentpool)

        asg_ids = self.context.get_asg_ids()
        allowed_host_ports = self.context.get_allowed_host_ports()
        if allowed_host_ports is not None:
            agentpool.network_profile = self.models.AgentPoolNetworkProfile()
            agentpool.network_profile.allowed_host_ports = allowed_host_ports
            agentpool.network_profile.application_security_groups = asg_ids

        ip_tags = self.context.get_ip_tags()
        if ip_tags:
            if not agentpool.network_profile:
                agentpool.network_profile = self.models.AgentPoolNetworkProfile()
            agentpool.network_profile.node_public_ip_tags = ip_tags

        return agentpool

    def set_up_agentpool_windows_profile(self, agentpool: AgentPool) -> AgentPool:
        """Set up windows profile for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        disable_windows_outbound_nat = self.context.get_disable_windows_outbound_nat()

        # Construct AgentPoolWindowsProfile if one of the fields has been set
        if disable_windows_outbound_nat:
            agentpool.windows_profile = self.models.AgentPoolWindowsProfile(  # pylint: disable=no-member
                disable_outbound_nat=disable_windows_outbound_nat
            )

        return agentpool

    def set_up_gpu_profile(self, agentpool: AgentPool) -> AgentPool:
        """Set up gpu profile for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        gpu_driver = self.context.get_gpu_driver()

        # Construct AgentPoolGPUProfile if one of the fields has been set
        if gpu_driver:
            agentpool.gpu_profile = self.models.GPUProfile()
            agentpool.gpu_profile.driver = gpu_driver

        return agentpool

    def set_up_agentpool_gateway_profile(self, agentpool: AgentPool) -> AgentPool:
        """Set up agentpool gateway profile for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        gateway_prefix_size = self.context.get_gateway_prefix_size()
        if gateway_prefix_size is not None:
            if agentpool.gateway_profile is None:
                agentpool.gateway_profile = self.models.AgentPoolGatewayProfile()  # pylint: disable=no-member

            agentpool.gateway_profile.public_ip_prefix_size = gateway_prefix_size

        return agentpool

    def set_up_pod_ip_allocation_mode(self, agentpool: AgentPool) -> AgentPool:
        """Set up pod ip allocation mode for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        pod_ip_allocation_mode = self.context.get_pod_ip_allocation_mode()
        if pod_ip_allocation_mode is not None:
            agentpool.pod_ip_allocation_mode = pod_ip_allocation_mode

        return agentpool

    def set_up_virtual_machines_profile(self, agentpool: AgentPool) -> AgentPool:
        """Set up virtual machines profile for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        # validate vm_sizes first, then skip if not Virtual Machines
        sizes = self.context.get_vm_sizes()
        if len(sizes) != 1:
            raise InvalidArgumentValueError(f"We only accept single sku size for manual profile. {sizes} is invalid.")

        if self.context.get_vm_set_type() != CONST_VIRTUAL_MACHINES:
            return agentpool

        count, _, _, _ = self.context.get_node_count_and_enable_cluster_autoscaler_min_max_count()
        agentpool.virtual_machines_profile = self.models.VirtualMachinesProfile(
            scale=self.models.ScaleProfile(
                manual=[
                    self.models.ManualScaleProfile(
                        size=sizes[0],
                        count=count,
                    )
                ]
            )
        )
        agentpool.vm_size = None
        agentpool.count = None

        return agentpool

    def construct_agentpool_profile_default(self, bypass_restore_defaults: bool = False) -> AgentPool:
        """The overall controller used to construct the AgentPool profile by default.

        The completely constructed AgentPool object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the AgentPool object
        """
        # initialize the AgentPool object
        agentpool = self.init_agentpool()
        # remove defaults
        self._remove_defaults_in_agentpool(agentpool)
        # set up snapshot properties
        agentpool = self.set_up_snapshot_properties(agentpool)
        # set up host group properties
        agentpool = self.set_up_host_group_properties(agentpool)
        # set up node network properties
        agentpool = self.set_up_node_network_properties(agentpool)
        # set up auto scaler properties
        agentpool = self.set_up_auto_scaler_properties(agentpool)
        # set up priority properties
        agentpool = self.set_up_priority_properties(agentpool)
        # set up label, tag, taint
        agentpool = self.set_up_label_tag_taint(agentpool)
        # set up osdisk properties
        agentpool = self.set_up_osdisk_properties(agentpool)
        # set up upgrade settings
        agentpool = self.set_up_upgrade_settings(agentpool)
        # set up misc vm properties
        agentpool = self.set_up_vm_properties(agentpool)
        # set up custom node config
        agentpool = self.set_up_custom_node_config(agentpool)
        # set up gpu instance profile
        agentpool = self.set_up_gpu_properties(agentpool)
        # set up agentpool network profile
        agentpool = self.set_up_agentpool_network_profile(agentpool)
        # set up agentpool pod ip allocation mode
        agentpool = self.set_up_pod_ip_allocation_mode(agentpool)
        # set up agentpool windows profile
        agentpool = self.set_up_agentpool_windows_profile(agentpool)
        # set up crg id
        agentpool = self.set_up_crg_id(agentpool)
        # set up agentpool security profile
        agentpool = self.set_up_agentpool_security_profile(agentpool)
        # set up message of the day
        agentpool = self.set_up_motd(agentpool)
        # set up gpu profile
        agentpool = self.set_up_gpu_profile(agentpool)
        # set up agentpool gateway profile
        agentpool = self.set_up_agentpool_gateway_profile(agentpool)
        # set up virtual machines profile
        agentpool = self.set_up_virtual_machines_profile(agentpool)
        # restore defaults
        if not bypass_restore_defaults:
            agentpool = self._restore_defaults_in_agentpool(agentpool)
        return agentpool

    # pylint: disable=protected-access
    def add_agentpool(self, agentpool: AgentPool) -> AgentPool:
        """Send request to add a new agentpool.

        The function "sdk_no_wait" will be called to use the Agentpool operations of ContainerServiceClient to send a
        reqeust to add a new agent pool to the cluster.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        active_cloud = get_active_cloud(self.cmd.cli_ctx)
        if active_cloud.profile != "latest":
            return sdk_no_wait(
                self.context.get_no_wait(),
                self.client.begin_create_or_update,
                self.context.get_resource_group_name(),
                self.context.get_cluster_name(),
                self.context._get_nodepool_name(enable_validation=False),
                agentpool,
                headers=self.context.get_aks_custom_headers(),
            )

        return sdk_no_wait(
            self.context.get_no_wait(),
            self.client.begin_create_or_update,
            self.context.get_resource_group_name(),
            self.context.get_cluster_name(),
            # validated in "init_agentpool", skip to avoid duplicate api calls
            self.context._get_nodepool_name(enable_validation=False),
            agentpool,
            if_match=self.context.get_if_match(),
            if_none_match=self.context.get_if_none_match(),
            headers=self.context.get_aks_custom_headers(),
        )


class AKSAgentPoolUpdateDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client: AgentPoolsOperations,
        raw_parameters: Dict,
        resource_type: ResourceType,
        agentpool_decorator_mode: AgentPoolDecoratorMode,
    ):
        """Internal controller of aks_agentpool_update.

        Break down the all-in-one aks_agentpool_update function into several relatively independent functions (some of
        them have a certain order dependency) that only focus on a specific profile or process a specific piece of
        logic. In addition, an overall control function is provided. By calling the aforementioned independent functions
        one by one, a complete AgentPool object is gradually decorated and finally requests are sent to update an
        existing node pool.
        """
        self.cmd = cmd
        self.client = client
        self.__raw_parameters = raw_parameters
        self.resource_type = resource_type
        self.agentpool_decorator_mode = agentpool_decorator_mode
        self.init_models()
        self.init_context()

    def init_models(self) -> None:
        """Initialize an AKSAgentPoolModels object to store the models.

        :return: None
        """
        self.models = AKSAgentPoolModels(self.cmd, self.resource_type, self.agentpool_decorator_mode)

    def init_context(self) -> None:
        """Initialize an AKSManagedClusterContext object to store the context in the process of assemble the
        AgentPool object.

        :return: None
        """
        self.context = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict(self.__raw_parameters),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )

    def _ensure_agentpool(self, agentpool: AgentPool) -> None:
        """Internal function to ensure that the incoming `agentpool` object is valid and the same as the attached
        `agentpool` object in the context.

        If the incoming `agentpool` is not valid or is inconsistent with the `agentpool` in the context, raise a
        CLIInternalError.

        :return: None
        """
        if not isinstance(agentpool, self.models.UnifiedAgentPoolModel):
            raise CLIInternalError(
                "Unexpected agentpool object with type '{}'.".format(type(agentpool))
            )

        if self.context.agentpool != agentpool:
            raise CLIInternalError(
                "Inconsistent state detected. The incoming `agentpool` "
                "is not the same as the `agentpool` in the context."
            )

    def fetch_agentpool(self, agentpools: List[AgentPool] = None) -> AgentPool:
        """Get the AgentPool object currently in use and attach it to internal context.

        Internally send request using Agentpool operations of ContainerServiceClient.

        :return: the AgentPool object
        """
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            self.context.attach_agentpools(agentpools)
            agentpool = safe_list_get(agentpools, 0)
        else:
            agentpool = self.client.get(
                self.context.get_resource_group_name(),
                self.context.get_cluster_name(),
                self.context.get_nodepool_name(),
            )

        # attach agentpool to AKSAgentPoolContext
        self.context.attach_agentpool(agentpool)
        return agentpool

    def update_auto_scaler_properties(self, agentpool: AgentPool) -> AgentPool:
        """Update auto scaler related properties for the Agentpool object.

        :return: the Agentpool object
        """
        self._ensure_agentpool(agentpool)

        (
            update_cluster_autoscaler,
            enable_cluster_autoscaler,
            disable_cluster_autoscaler,
            min_count,
            max_count,
        ) = (
            self.context.get_update_enable_disable_cluster_autoscaler_and_min_max_count()
        )

        if update_cluster_autoscaler or enable_cluster_autoscaler:
            agentpool.enable_auto_scaling = True
            agentpool.min_count = min_count
            agentpool.max_count = max_count

        if disable_cluster_autoscaler:
            agentpool.enable_auto_scaling = False
            agentpool.min_count = None
            agentpool.max_count = None
        return agentpool

    def update_label_tag_taint(self, agentpool: AgentPool) -> AgentPool:
        """Set up label, tag, taint for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        labels = self.context.get_nodepool_labels()
        if labels is not None:
            agentpool.node_labels = labels

        tags = self.context.get_nodepool_tags()
        if tags is not None:
            agentpool.tags = tags

        node_taints = self.context.get_node_taints()
        if node_taints is not None:
            agentpool.node_taints = node_taints
        return agentpool

    def update_upgrade_settings(self, agentpool: AgentPool) -> AgentPool:
        """Update upgrade settings for the Agentpool object.

        :return: the Agentpool object
        """
        self._ensure_agentpool(agentpool)

        upgrade_settings = agentpool.upgrade_settings
        if upgrade_settings is None:
            upgrade_settings = self.models.AgentPoolUpgradeSettings()

        max_surge = self.context.get_max_surge()
        if max_surge:
            upgrade_settings.max_surge = max_surge
            # why not always set this? so we don't wipe out a preview feaure in upgrade settigns like NodeSoakDuration?
            agentpool.upgrade_settings = upgrade_settings

        max_unavailable = self.context.get_max_unavailable()
        if max_unavailable:
            upgrade_settings.max_unavailable = max_unavailable

        drain_timeout = self.context.get_drain_timeout()
        if drain_timeout:
            upgrade_settings.drain_timeout_in_minutes = drain_timeout
            agentpool.upgrade_settings = upgrade_settings

        node_soak_duration = self.context.get_node_soak_duration()
        if node_soak_duration:
            upgrade_settings.node_soak_duration_in_minutes = node_soak_duration
            agentpool.upgrade_settings = upgrade_settings

        undrainable_node_behavior = self.context.get_undrainable_node_behavior()
        if undrainable_node_behavior:
            upgrade_settings.undrainable_node_behavior = undrainable_node_behavior
            agentpool.upgrade_settings = upgrade_settings

        return agentpool

    def update_vm_properties(self, agentpool: AgentPool) -> AgentPool:
        """Update vm related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        scale_down_mode = self.context.get_scale_down_mode()
        if scale_down_mode is not None:
            agentpool.scale_down_mode = scale_down_mode

        mode = self.context.get_mode()
        if mode is not None:
            agentpool.mode = mode
        return agentpool

    def update_network_profile(self, agentpool: AgentPool) -> AgentPool:
        self._ensure_agentpool(agentpool)

        asg_ids = self.context.get_asg_ids()
        allowed_host_ports = self.context.get_allowed_host_ports()
        if (asg_ids or allowed_host_ports) and not agentpool.network_profile:
            agentpool.network_profile = self.models.AgentPoolNetworkProfile()
        if asg_ids is not None:
            agentpool.network_profile.application_security_groups = asg_ids
        if allowed_host_ports is not None:
            agentpool.network_profile.allowed_host_ports = allowed_host_ports
        return agentpool

    def update_os_sku(self, agentpool: AgentPool) -> AgentPool:
        self._ensure_agentpool(agentpool)

        os_sku = self.context.get_os_sku()
        if os_sku:
            agentpool.os_sku = os_sku
        return agentpool

    def update_fips_image(self, agentpool: AgentPool) -> AgentPool:
        """Update fips image property for the AgentPool object.
        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        # Updates enable_fips property allowing switching of fips mode
        if self.context.get_enable_fips_image():
            agentpool.enable_fips = True

        if self.context.get_disable_fips_image():
            agentpool.enable_fips = False

        return agentpool

    def update_secure_boot(self, agentpool: AgentPool) -> AgentPool:
        """Update secure boot property for the AgentPool object.
        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        if self.context.get_enable_secure_boot():
            if agentpool.security_profile is None:
                agentpool.secure_boot = self.models.AgentPoolSecurityProfile()  # pylint: disable=no-member
            agentpool.security_profile.enable_secure_boot = True

        if self.context.get_disable_secure_boot():
            if agentpool.security_profile is None:
                agentpool.security_profile = self.models.AgentPoolSecurityProfile()  # pylint: disable=no-member
            agentpool.security_profile.enable_secure_boot = False

        return agentpool

    def update_vtpm(self, agentpool: AgentPool) -> AgentPool:
        """Update vtpm property for the AgentPool object.
        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        if self.context.get_enable_vtpm():
            if agentpool.security_profile is None:
                agentpool.security_profile = self.models.AgentPoolSecurityProfile()  # pylint: disable=no-member
            agentpool.security_profile.enable_vtpm = True

        if self.context.get_disable_vtpm():
            if agentpool.security_profile is None:
                agentpool.security_profile = self.models.AgentPoolSecurityProfile()  # pylint: disable=no-member
            agentpool.security_profile.enable_vtpm = False

        return agentpool

    def update_agentpool_profile_default(self, agentpools: List[AgentPool] = None) -> AgentPool:
        """The overall controller used to update AgentPool profile by default.

        The completely constructed AgentPool object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the AgentPool object
        """
        # fetch the Agentpool object
        agentpool = self.fetch_agentpool(agentpools)
        # update auto scaler properties
        agentpool = self.update_auto_scaler_properties(agentpool)
        # update label, tag, taint
        agentpool = self.update_label_tag_taint(agentpool)
        # update upgrade settings
        agentpool = self.update_upgrade_settings(agentpool)
        # update misc vm properties
        agentpool = self.update_vm_properties(agentpool)
        # update network profile
        agentpool = self.update_network_profile(agentpool)
        # update os sku
        agentpool = self.update_os_sku(agentpool)
        # update fips image
        agentpool = self.update_fips_image(agentpool)

        # update vtpm
        agentpool = self.update_vtpm(agentpool)
        # update secure boot
        agentpool = self.update_secure_boot(agentpool)
        return agentpool

    def update_agentpool(self, agentpool: AgentPool) -> AgentPool:
        """Send request to add a new agentpool.

        The function "sdk_no_wait" will be called to use the Agentpool operations of ContainerServiceClient to send a
        reqeust to update an existing agent pool of the cluster.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        active_cloud = get_active_cloud(self.cmd.cli_ctx)
        if active_cloud.profile != "latest":
            return sdk_no_wait(
                self.context.get_no_wait(),
                self.client.begin_create_or_update,
                self.context.get_resource_group_name(),
                self.context.get_cluster_name(),
                self.context.get_nodepool_name(),
                agentpool,
                headers=self.context.get_aks_custom_headers(),
            )

        return sdk_no_wait(
            self.context.get_no_wait(),
            self.client.begin_create_or_update,
            self.context.get_resource_group_name(),
            self.context.get_cluster_name(),
            self.context.get_nodepool_name(),
            agentpool,
            if_match=self.context.get_if_match(),
            if_none_match=self.context.get_if_none_match(),
            headers=self.context.get_aks_custom_headers(),
        )

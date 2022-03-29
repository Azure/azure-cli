# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict, List, Tuple, TypeVar, Union

from azure.cli.command_modules.acs._client_factory import cf_agent_pools
from azure.cli.command_modules.acs._consts import (
    CONST_DEFAULT_NODE_OS_TYPE,
    CONST_DEFAULT_NODE_VM_SIZE,
    CONST_DEFAULT_WINDOWS_NODE_VM_SIZE,
    AgentPoolDecoratorMode,
    DecoratorMode,
)
from azure.cli.command_modules.acs._helpers import get_snapshot_by_snapshot_id
from azure.cli.command_modules.acs._validators import extract_comma_separated_string
from azure.cli.command_modules.acs.base_decorator import BaseAKSContext, BaseAKSModels, BaseAKSParamDict
from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import CLIInternalError, InvalidArgumentValueError, RequiredArgumentMissingError
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait
from knack.log import get_logger

logger = get_logger(__name__)

# type variables
AgentPool = TypeVar("AgentPool")
AgentPoolsOperations = TypeVar("AgentPoolsOperations")
Snapshot = TypeVar("Snapshot")


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

    # pylint: disable=no-self-use
    def __validate_counts_in_autoscaler(
        self,
        node_count,
        enable_cluster_autoscaler,
        min_count,
        max_count,
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

    def attach_agentpool(self, agentpool: AgentPool) -> None:
        """Attach the AgentPool object to the context.

        The `agentpool` object is only allowed to be attached once, and attaching again will raise a CLIInternalError.

        :return: None
        """
        if self.agentpool is None:
            self.agentpool = agentpool
        else:
            msg = "the same" if self.agentpool == agentpool else "different"
            raise CLIInternalError(
                "Attempting to attach the `agentpool` object again, the two objects are {}.".format(
                    msg
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
        nodepool_name = self.raw_param.get("nodepool_name")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.name is not None:
            nodepool_name = self.agentpool.name

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            instances = cf_agent_pools.list(self.get_resource_group_name, self.get_cluster_name)
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

    def get_max_surge(self):
        """Obtain the value of max_surge.

        :return: string
        """
        # read the original value passed by the command
        max_surge = self.raw_param.get("max_surge")
        # try to read the property value corresponding to the parameter from the `agentpool` object.
        if (
            self.agentpool and
            self.agentpool.upgrade_settings and
            self.agentpool.upgrade_settings.max_surge is not None
        ):
            max_surge = self.agentpool.upgrade_settings.max_surge

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return max_surge

    # pylint: disable=too-many-branches
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
        enable_cluster_autoscaler = self.raw_param.get("enable_cluster_autoscaler")
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
            decorator_mode=DecoratorMode.CREATE,
        )
        return node_count, enable_cluster_autoscaler, min_count, max_count

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

        # normalize
        if node_osdisk_size:
            node_osdisk_size = int(node_osdisk_size)

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

    def get_snapshot_id(self) -> Union[str, None]:
        """Obtain the values of snapshot_id.

        :return: string or None
        """
        # read the original value passed by the command
        snapshot_id = self.raw_param.get("snapshot_id")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if (
            self.agentpool and
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
            snapshot = get_snapshot_by_snapshot_id(self.cmd.cli_ctx, snapshot_id)
            self.set_intermediate("snapshot", snapshot, overwrite_exists=True)
        return snapshot

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
        if self.agentpool:
            value_obtained_from_agentpool = self.agentpool.os_sku
        # try to retrieve the value from snapshot
        value_obtained_from_snapshot = None
        # skip dynamic completion if read_only is specified
        if not read_only:
            snapshot = self.get_snapshot()
            if snapshot:
                value_obtained_from_snapshot = snapshot.os_sku

        # set default value
        if value_obtained_from_agentpool is not None:
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

    def get_nodepool_labels(self) -> Union[Dict[str, str], None]:
        """Obtain the value of nodepool_labels.

        :return: dictionary or None
        """
        # read the original value passed by the command
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            nodepool_labels = self.raw_param.get("nodepool_labels")
        else:
            nodepool_labels = self.raw_param.get("labels")

        # try to read the property value corresponding to the parameter from the `agentpool` object
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

        # try to read the property value corresponding to the parameter from the `agentpool` object
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
        node_taints = self.raw_param.get("node_taints")
        # normalize, keep None as None
        if node_taints is not None:
            node_taints = [x.strip() for x in (node_taints.split(",") if node_taints else [])]

        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.node_taints is not None:
            node_taints = self.agentpool.node_taints

        # this parameter does not need validation
        return node_taints

    def get_aks_custom_headers(self) -> Dict[str, str]:
        """Obtain the value of aks_custom_headers.

        Note: aks_custom_headers will not be decorated into the `agentpool` object.

        This function will normalize the parameter by default. It will call "extract_comma_separated_string" to extract
        comma-separated key value pairs from the string.

        :return: dictionary
        """
        # read the original value passed by the command
        aks_custom_headers = self.raw_param.get("aks_custom_headers")
        # normalize user-provided header
        # usually the purpose is to enable (preview) features through AKSHTTPCustomFeatures
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
        """Obtain the value of no_wait.

        Note: no_wait will not be decorated into the `agentpool` object.

        :return: bool
        """
        # read the original value passed by the command
        no_wait = self.raw_param.get("no_wait")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return no_wait


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
        self.agentpool_decorator_mode = agentpool_decorator_mode
        self.models = AKSAgentPoolModels(cmd, resource_type, agentpool_decorator_mode)
        # store the context in the process of assemble the AgentPool object
        self.context = AKSAgentPoolContext(
            cmd, AKSAgentPoolParamDict(raw_parameters), self.models, DecoratorMode.CREATE, agentpool_decorator_mode
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

    def init_agentpool(self) -> AgentPool:
        """Initialize an AgentPool object with name and attach it to internal context.

        :return: the AgentPool object
        """
        if self.agentpool_decorator_mode == AgentPoolDecoratorMode.MANAGED_CLUSTER:
            # Note: As a required property, name must be provided during initialization.
            agentpool = self.models.UnifiedAgentPoolModel(name=self.context.get_nodepool_name(), os_type=None)
        else:
            # Note: As a read only property, name would be ignored when serialized.
            # Set the name property by explicit assignment, otherwise it will be ignored by initialization.
            agentpool = self.models.UnifiedAgentPoolModel(os_type=None)
            agentpool.name = self.context.get_nodepool_name()

        # attach agentpool to AKSAgentPoolContext
        self.context.attach_agentpool(agentpool)
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
        agentpool.upgrade_settings = upgrade_settings
        return agentpool

    def set_up_osdisk_properties(self, agentpool: AgentPool) -> AgentPool:
        """Set up os disk related properties for the AgentPool object.

        :return: the AgentPool object
        """
        self._ensure_agentpool(agentpool)

        agentpool.os_disk_size_gb = self.context.get_node_osdisk_size()
        agentpool.os_disk_type = self.context.get_node_osdisk_type()
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
        agentpool.os_type = self.context.get_os_type()
        agentpool.os_sku = self.context.get_os_sku()
        agentpool.vm_size = self.context.get_node_vm_size()
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

    def construct_default_agentpool_profile(self) -> AgentPool:
        """The overall controller used to construct the default AgentPool profile.

        The completely constructed AgentPool object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the AgentPool object
        """
        # initialize the AgentPool object
        agentpool = self.init_agentpool()
        # set up upgrade settings
        agentpool = self.set_up_upgrade_settings(agentpool)
        # set up osdisk properties
        agentpool = self.set_up_osdisk_properties(agentpool)
        # set up auto scaler properties
        agentpool = self.set_up_auto_scaler_properties(agentpool)
        # set up snapshot properties
        agentpool = self.set_up_snapshot_properties(agentpool)
        # set up label, tag, taint
        agentpool = self.set_up_label_tag_taint(agentpool)
        return agentpool

    # pylint: disable=protected-access
    def add_agentpool(self, agentpool: AgentPool) -> AgentPool:
        """Send request to add a new agentpool.

        The function "sdk_no_wait" will be called to use the ContainerServiceClient to send a reqeust to add a new agent
        pool to the cluster.

        :return: the ManagedCluster object
        """
        self._ensure_agentpool(agentpool)

        return sdk_no_wait(
            self.context.get_no_wait(),
            self.client.begin_create_or_update,
            self.context.get_resource_group_name(),
            self.context.get_cluster_name(),
            # validated in "init_agentpool", skip to avoid duplicate api calls
            self.context._get_nodepool_name(enable_validation=False),
            agentpool,
            headers=self.context.get_aks_custom_headers(),
        )


class AKSAgentPoolUpdateDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client: AgentPoolsOperations,
        raw_parameters: Dict,
        resource_type: ResourceType,
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
        self.models = AKSAgentPoolModels(cmd, resource_type)
        # store the context in the process of assemble the AgentPool object
        self.context = AKSAgentPoolContext(
            cmd, AKSAgentPoolParamDict(raw_parameters), self.models, decorator_mode=DecoratorMode.UPDATE
        )

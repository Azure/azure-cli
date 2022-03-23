# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict, Tuple, TypeVar, Union

from azure.cli.command_modules.acs._client_factory import cf_agent_pools
from azure.cli.command_modules.acs._consts import DecoratorMode
from azure.cli.command_modules.acs._validators import extract_comma_separated_string
from azure.cli.command_modules.acs.base_decorator import BaseAKSContext, BaseAKSModels, BaseAKSParamDict
from azure.cli.core.azclierror import CLIInternalError, InvalidArgumentValueError, RequiredArgumentMissingError
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait
from knack.log import get_logger

logger = get_logger(__name__)

# type variables
AgentPool = TypeVar("AgentPool")
AgentPoolsOperations = TypeVar("AgentPoolsOperations")


# pylint: disable=too-few-public-methods
class AKSAgentPoolModels(BaseAKSModels):
    """Store the models used in aks agentpool series of commands.

    The api version of the class corresponding to a model is determined by resource_type.
    """


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
    ):
        super().__init__(cmd, raw_parameters, models, decorator_mode)
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
        # try to read the property value corresponding to the parameter from the `mc` object.
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
        self.models = AKSAgentPoolModels(cmd, resource_type)
        # store the context in the process of assemble the AgentPool object
        self.context = AKSAgentPoolContext(
            cmd, AKSAgentPoolParamDict(raw_parameters), self.models, decorator_mode=DecoratorMode.CREATE
        )

    def _ensure_agentpool(self, agentpool: AgentPool) -> None:
        """Internal function to ensure that the incoming `agentpool` object is valid and the same as the attached
        `agentpool` object in the context.

        If the incoming `agentpool` is not valid or is inconsistent with the `agentpool` in the context, raise a
        CLIInternalError.

        :return: None
        """
        if not isinstance(agentpool, self.models.AgentPool):
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

        Note: As a read only property, name would be ignored when serialized.

        :return: the AgentPool object
        """
        # Initialize a AgentPool object with name.
        agentpool = self.models.AgentPool()
        # Note: As a read only property, name would be ignored when serialized.
        # Set the name property by explicit assignment, otherwise it will be ignored by initialization.
        agentpool.name = self.context.get_nodepool_name()

        # attach mc to AKSContext
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

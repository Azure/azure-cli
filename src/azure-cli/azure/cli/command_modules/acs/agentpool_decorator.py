# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands import AzCliCommand
from azure.cli.command_modules.acs._client_factory import cf_agent_pools
from typing import Dict, TypeVar
from azure.cli.command_modules.acs._consts import (
    DecoratorMode,
)
from knack.log import get_logger
from azure.cli.core.azclierror import (
    CLIInternalError,
    InvalidArgumentValueError,
)
from azure.cli.command_modules.acs.decorator import validate_decorator_mode

logger = get_logger(__name__)

# type variables
AgentPool = TypeVar("AgentPool")
AgentPoolsOperations = TypeVar("AgentPoolsOperations")


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class AKSAgentPoolModels:
    """Store the models used in aks_agentpool_create and aks_agentpool_update.

    The api version of the class corresponding to a model is determined by resource_type.
    """

    def __init__(
        self,
        cmd: AzCommandsLoader,
        resource_type: ResourceType,
    ):
        self.__cmd = cmd
        self.resource_type = resource_type
        self.AgentPool = self.__cmd.get_models(
            "AgentPool",
            resource_type=self.resource_type,
            operation_group="agent_pools",
        )
        self.AgentPoolUpgradeSettings = self.__cmd.get_models(
            "AgentPoolUpgradeSettings",
            resource_type=self.resource_type,
            operation_group="agent_pools",
        )


# pylint: disable=too-many-public-methods
class AKSAgentPoolContext:
    """Implement getter functions for all parameters in aks_agentpool_create and aks_agentpool_update.
    """
    def __init__(self, cmd: AzCliCommand, raw_parameters: Dict, models: AKSAgentPoolModels, decorator_mode: DecoratorMode):
        if not isinstance(raw_parameters, dict):
            raise CLIInternalError(
                "Unexpected raw_parameters object with type '{}'.".format(
                    type(raw_parameters)
                )
            )
        if not validate_decorator_mode(decorator_mode):
            raise CLIInternalError(
                "Unexpected decorator_mode '{}' with type '{}'.".format(
                    decorator_mode, type(decorator_mode)
                )
            )
        self.cmd = cmd
        self.raw_param = raw_parameters
        self.models = models
        self.decorator_mode = decorator_mode
        self.intermediates = dict()
        self.agentpool = None

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

    def get_nodepool_name(self) -> str:
        """Obtain the value of nodepool_name.

        Note: SDK performs the following validation {'required': True, 'pattern': r'^[a-z][a-z0-9]{0,11}$'}.

        This is a required parameter and its value should be provided by user explicitly.

        :return: string
        """
        # read the original value passed by the command
        nodepool_name = self.raw_param.get("nodepool_name")
        # try to read the property value corresponding to the parameter from the `agentpool` object
        if self.agentpool and self.agentpool.name is not None:
            nodepool_name = self.agentpool.name

        # this parameter does not need dynamic completion
        # validation
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


class AKSAgentPoolCreateDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client: AgentPoolsOperations,
        raw_parameters: Dict,
        resource_type: ResourceType,
    ):
        """Internal controller of aks_agentpool_create.

        Break down the all-in-one aks_agentpool_create function into several relatively independent functions (some of
        them have a certain order dependency) that only focus on a specific profile or process a specific piece of
        logic. In addition, an overall control function is provided. By calling the aforementioned independent functions
        one by one, a complete AgentPool object is gradually decorated and finally requests are sent to create a node
        pool.
        """
        self.cmd = cmd
        self.client = client
        self.models = AKSAgentPoolModels(cmd, resource_type)
        # store the context in the process of assemble the AgentPool object
        self.context = AKSAgentPoolContext(cmd, raw_parameters, self.models, decorator_mode=DecoratorMode.CREATE)

    def init_agentpool(self) -> AgentPool:
        """Initialize an AgentPool object with name and attach it to internal context.

        :return: the AgentPool object
        """
        # Initialize a AgentPool object with name.
        agentpool = self.models.AgentPool(
            name=self.context.get_nodepool_name(),
        )

        # attach mc to AKSContext
        self.context.attach_agentpool(agentpool)
        return agentpool


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
        self.context = AKSAgentPoolContext(cmd, raw_parameters, self.models, decorator_mode=DecoratorMode.UPDATE)

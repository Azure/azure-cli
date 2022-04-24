# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from types import ModuleType
from typing import Any, Dict, Type, TypeVar

from azure.cli.command_modules.acs._consts import DecoratorMode
from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import CLIInternalError
from azure.cli.core.commands import AzCliCommand, LongRunningOperation
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait
from knack.log import get_logger
from msrest import Serializer

logger = get_logger(__name__)

# type variables
ContainerServiceClient = TypeVar("ContainerServiceClient")
ManagedCluster = TypeVar("ManagedCluster")


def validate_decorator_mode(decorator_mode) -> bool:
    """Check if decorator_mode is a value of enum type DecoratorMode.

    :return: bool
    """
    is_valid_decorator_mode = False
    try:
        is_valid_decorator_mode = decorator_mode in DecoratorMode
    # will raise TypeError in Python >= 3.8
    except TypeError:
        pass

    return is_valid_decorator_mode


# pylint: disable=too-few-public-methods
class BaseAKSModels:
    """A base class for storing the models used by aks commands.

    The api version of the class corresponding to a model is determined by resource_type.
    """
    def __init__(
        self,
        cmd: AzCommandsLoader,
        resource_type: ResourceType,
    ):
        self.__cmd = cmd
        self.__model_module = None
        self.__model_dict = None
        self.__serializer = None
        self.resource_type = resource_type
        self.__set_up_base_aks_models()

    @property
    def model_module(self) -> ModuleType:
        """Load the module that stores all aks models.

        :return: the models module in SDK
        """
        if self.__model_module is None:
            self.__model_module = self.__cmd.get_models(
                resource_type=self.resource_type,
                operation_group="managed_clusters",
            ).models
        return self.__model_module

    @property
    def models_dict(self) -> Dict[str, Type]:
        """Filter out aks models from the model module and store it as a dictionary with the model name-class as
        the key-value pair.

        :return: dictionary
        """
        if self.__model_dict is None:
            self.__model_dict = {}
            for k, v in vars(self.model_module).items():
                if isinstance(v, type):
                    self.__model_dict[k] = v
        return self.__model_dict

    def __set_up_base_aks_models(self) -> None:
        """Expose all aks models as properties of the class.
        """
        for model_name, model_class in self.models_dict.items():
            setattr(self, model_name, model_class)

    def serialize(self, data: Any, model_type: str) -> Dict:
        """Serialize the data according to the provided model type.

        :return: dictionary
        """
        if self.__serializer is None:
            self.__serializer = Serializer(self.models_dict)
        # will also perfrom client side validation
        return self.__serializer.body(data, model_type)


class BaseAKSParamDict:
    """A base class for storing the original parameters passed in by the aks commands as an internal dictionary.

    Only expose the "get" method externally to obtain parameter values, while recording usage.
    """
    def __init__(self, param_dict):
        if not isinstance(param_dict, dict):
            raise CLIInternalError(
                "Unexpected param_dict object with type '{}'.".format(
                    type(param_dict)
                )
            )
        self.__store = param_dict.copy()
        self.__count = {}

    def __increase(self, key):
        self.__count[key] = self.__count.get(key, 0) + 1

    def get(self, key, default=None):
        self.__increase(key)
        value = self.__store.get(key)
        if value is None:
            return default
        return value

    def keys(self):
        return self.__store.keys()

    def values(self):
        return self.__store.values()

    def items(self):
        return self.__store.items()

    def __format_count(self):
        untouched_keys = [x for x in self.__store.keys() if x not in self.__count.keys()]
        for k in untouched_keys:
            self.__count[k] = 0

    def print_usage_statistics(self):
        self.__format_count()
        print("\nParameter usage statistics:")
        for k, v in self.__count.items():
            print(k, v)
        print("Total: {}".format(len(self.__count.keys())))


class BaseAKSContext:
    """A base class for holding raw parameters, models and methods to get and store intermediates that will be used by
    the decorators of aks commands.

    Note: This is a base class and should not be used directly, you need to implement getter functions in inherited
    classes.

    Each getter function is responsible for obtaining the corresponding one or more parameter values, and perform
    necessary parameter value completion or normalization and validation checks.
    """
    def __init__(
        self, cmd: AzCliCommand, raw_parameters: BaseAKSParamDict, models: BaseAKSModels, decorator_mode: DecoratorMode
    ):
        if not isinstance(raw_parameters, BaseAKSParamDict):
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

    def get_intermediate(self, variable_name: str, default_value: Any = None) -> Any:
        """Get the value of an intermediate by its name.

        Get the value from the intermediates dictionary with variable_name as the key. If variable_name does not exist,
        default_value will be returned.

        :return: Any
        """
        if variable_name not in self.intermediates:
            logger.debug(
                "The intermediate '%s' does not exist. Return default value '%s'.",
                variable_name,
                default_value,
            )
        intermediate_value = self.intermediates.get(variable_name, default_value)
        return intermediate_value

    def set_intermediate(
        self, variable_name: str, value: Any, overwrite_exists: bool = False
    ) -> None:
        """Set the value of an intermediate by its name.

        In the case that the intermediate value already exists, if overwrite_exists is enabled, the value will be
        overwritten and the log will be output at the debug level, otherwise the value will not be overwritten and
        the log will be output at the warning level, which by default will be output to stderr and seen by user.

        :return: None
        """
        if variable_name in self.intermediates:
            if overwrite_exists:
                msg = "The intermediate '{}' is overwritten. Original value: '{}', new value: '{}'.".format(
                    variable_name, self.intermediates.get(variable_name), value
                )
                logger.debug(msg)
                self.intermediates[variable_name] = value
            elif self.intermediates.get(variable_name) != value:
                msg = "The intermediate '{}' already exists, but overwrite is not enabled. " \
                    "Original value: '{}', candidate value: '{}'.".format(
                        variable_name,
                        self.intermediates.get(variable_name),
                        value,
                    )
                # warning level log will be output to the console, which may cause confusion to users
                logger.warning(msg)
        else:
            self.intermediates[variable_name] = value

    def remove_intermediate(self, variable_name: str) -> None:
        """Remove the value of an intermediate by its name.

        No exception will be raised if the intermediate does not exist.

        :return: None
        """
        self.intermediates.pop(variable_name, None)


class BaseAKSManagedClusterDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client: ContainerServiceClient,
    ):
        """A basic controller that follows the decorator pattern, used to compose the ManagedCluster profile and
        send requests.

        Note: This is a base class and should not be used directly.
        """
        self.cmd = cmd
        self.client = client

    def init_models(self):
        raise NotImplementedError()

    def init_context(self):
        raise NotImplementedError()

    # pylint: disable=unused-argument
    def check_is_postprocessing_required(self, mc: ManagedCluster) -> bool:
        raise NotImplementedError()

    # pylint: disable=unused-argument
    def immediate_processing_after_request(self, mc: ManagedCluster) -> None:
        raise NotImplementedError()

    # pylint: disable=unused-argument
    def postprocessing_after_mc_created(self, cluster: ManagedCluster) -> None:
        raise NotImplementedError()

    # pylint: disable=unused-argument
    def put_mc(self, mc: ManagedCluster) -> ManagedCluster:
        raise NotImplementedError()

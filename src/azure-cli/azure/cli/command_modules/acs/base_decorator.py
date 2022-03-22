# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any

from azure.cli.command_modules.acs._consts import DecoratorMode
from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import CLIInternalError
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType
from knack.log import get_logger

logger = get_logger(__name__)


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
        self.__raw_models = None
        self.resource_type = resource_type
        self.__set_up_base_aks_models()

    @property
    def raw_models(self):
        """Load the module that stores all aks models.
        """
        if self.__raw_models is None:
            self.__raw_models = self.__cmd.get_models(
                resource_type=self.resource_type,
                operation_group="managed_clusters",
            ).models
        return self.__raw_models

    def __set_up_base_aks_models(self):
        """Expose all aks models as properties of the class.
        """
        for model_name, model_class in vars(self.raw_models).items():
            if not model_name.startswith('_'):
                setattr(self, model_name, model_class)


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

    def get(self, key):
        self.__increase(key)
        return self.__store.get(key)

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

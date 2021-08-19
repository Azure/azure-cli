# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from typing import Any, List, Dict

from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import (
    CLIInternalError,
    ResourceNotFoundError,
    ClientRequestError,
    ArgumentUsageError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    ValidationError,
    UnauthorizedError,
)
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType

from .custom import (
    _get_rg_location,
    _validate_ssh_key,
    _get_default_dns_prefix,
    _set_vm_set_type,
    set_load_balancer_sku,
    get_subscription_id,
)

logger = get_logger(__name__)


def safe_list_get(li: List, idx: int, default: Any = None):
    # Attempt to get the element with index `idx` from an object `li` (which should be a list),
    # if the index is invalid (like out of range), return `default` (whose default value is None)
    if isinstance(li, list):
        try:
            return li[idx]
        except IndexError:
            return default
    return None


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class AKSCreateModels:
    # Used to store models (i.e. the corresponding class of a certain api version specified by `resource_type`)
    # which would be used during the creation process.
    def __init__(
        self,
        cmd: AzCommandsLoader,
        resource_type: ResourceType = ResourceType.MGMT_CONTAINERSERVICE,
    ):
        self.__cmd = cmd
        self.resource_type = resource_type
        self.ManagedClusterWindowsProfile = self.__cmd.get_models(
            "ManagedClusterWindowsProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterSKU = self.__cmd.get_models(
            "ManagedClusterSKU",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceNetworkProfile = self.__cmd.get_models(
            "ContainerServiceNetworkProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceLinuxProfile = self.__cmd.get_models(
            "ContainerServiceLinuxProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterServicePrincipalProfile = self.__cmd.get_models(
            "ManagedClusterServicePrincipalProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceSshConfiguration = self.__cmd.get_models(
            "ContainerServiceSshConfiguration",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceSshPublicKey = self.__cmd.get_models(
            "ContainerServiceSshPublicKey",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterAADProfile = self.__cmd.get_models(
            "ManagedClusterAADProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterAutoUpgradeProfile = self.__cmd.get_models(
            "ManagedClusterAutoUpgradeProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterAgentPoolProfile = self.__cmd.get_models(
            "ManagedClusterAgentPoolProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterIdentity = self.__cmd.get_models(
            "ManagedClusterIdentity",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.UserAssignedIdentity = self.__cmd.get_models(
            "UserAssignedIdentity",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedCluster = self.__cmd.get_models(
            "ManagedCluster",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedServiceIdentityUserAssignedIdentitiesValue = self.__cmd.get_models(
            "ManagedServiceIdentityUserAssignedIdentitiesValue",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ExtendedLocation = self.__cmd.get_models(
            "ExtendedLocation",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ExtendedLocationTypes = self.__cmd.get_models(
            "ExtendedLocationTypes",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )


# pylint: disable=too-few-public-methods
class AKSCreateParameters:
    # Used to store original function parameters, in the form of attributes of this class, which can be
    # obtained through a.xxx (a is an instance of this class, xxx is the original parameter name).
    # Note: The attributes of this class should not be modified once they are initialized.
    def __init__(self, data: Dict):
        for name, value in data.items():
            setattr(self, name, value)


class AKSCreateContext:
    # Used to store dynamically inferred/completed parameters (i.e. not specified by the user), intermediate
    # variables and a copy of the original function parameters.
    # To dynamically infer/complete a parameter or check the validity of a parameter, please provide a function
    # named `get_xxx`, where `xxx` is the parameter name.
    # Attention: When checking the validity of parameters in the `get_xxx` function, please use the `get_param`
    # function to obtain the values of other parameters to be checked to avoid circular calls.
    # Note: The update of parameters and intermediate variables in the command implementation should be achieved
    # by operating the instance of this class.
    def __init__(self, cmd: AzCliCommand, raw_parameters: Dict):
        self.cmd = cmd
        self.raw_param = AKSCreateParameters(raw_parameters)
        self.intermediates = dict()
        self.mc = None

    def attach_mc(self, mc):
        self.mc = mc

    def get_intermediate(self, variable_name: str, default_value: Any = None):
        if variable_name not in self.intermediates:
            msg = "The intermediate '{}' does not exist! Return default value '{}'!".format(
                variable_name, default_value
            )
            logger.debug(msg)
        return self.intermediates.get(variable_name, default_value)

    def set_intermediate(
        self, variable_name: str, value: Any, overwrite_exists: bool = False
    ):
        if variable_name in self.intermediates:
            if overwrite_exists:
                msg = "The intermediate '{}' is overwritten! Original value: '{}', new value: '{}'!".format(
                    variable_name, self.intermediates.get(variable_name), value
                )
                logger.debug(msg)
                self.intermediates[variable_name] = value
            elif self.intermediates.get(variable_name) != value:
                msg = "The intermediate '{}' already exists, but overwrite is not enabled! " "Original value: '{}', candidate value: '{}'!".format(
                    variable_name,
                    self.intermediates.get(variable_name),
                    value,
                )
                # warning level log will be output to the console, which may cause confusion to users
                logger.warning(msg)
        else:
            self.intermediates[variable_name] = value

    def remove_intermediate(self, variable_name: str):
        self.intermediates.pop(variable_name, None)

    def get_resource_group_name(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        # Note: This parameter will not be decorated into the `mc` object.
        # read the original value passed by the command
        resource_group_name = getattr(self.raw_param, "resource_group_name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return resource_group_name

    def get_name(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        # Note: This parameter will not be decorated into the `mc` object.
        # read the original value passed by the command
        name = getattr(self.raw_param, "name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return name

    def get_ssh_key_value(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        # read the original value passed by the command
        ssh_key_value = getattr(self.raw_param, "ssh_key_value")

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            _validate_ssh_key(
                no_ssh_key=self.get_no_ssh_key(), ssh_key_value=ssh_key_value
            )
        return ssh_key_value

    def get_dns_name_prefix(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        parameter_name = "dns_name_prefix"

        # read the original value passed by the command
        raw_value = getattr(self.raw_param, parameter_name)
        # Try to read from intermediates, the intermediate only exists when the parameter value has been
        # dynamically completed but has not been decorated into the `mc` object.
        # Note: The intermediate value should be cleared immediately after it is decorated into the
        # `mc` object.
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.dns_prefix:
            mc_property = self.mc.dns_prefix

        # set defautl value
        if mc_property is not None:
            dns_name_prefix = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
        elif intermediate is not None:
            dns_name_prefix = intermediate
        else:
            dns_name_prefix = raw_value

        # enable dynamic completion if the `force_update` parameter is specified when calling this getter
        dynamic_completion = force_update
        # check whether the parameter meet the conditions of dynamic completion
        if not dns_name_prefix and not self.get_fqdn_subdomain():
            dynamic_completion = True
        # In case the user does not specify the parameter and it meets the conditions of automatic completion,
        # necessary information is dynamically completed.
        if dynamic_completion:
            dns_name_prefix = _get_default_dns_prefix(
                name=self.get_name(),
                resource_group_name=self.get_resource_group_name(),
                subscription_id=self.get_intermediate("subscription_id"),
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, dns_name_prefix, overwrite_exists=True
            )

        # validation
        if enable_validation:
            if dns_name_prefix and self.get_fqdn_subdomain():
                raise MutuallyExclusiveArgumentError(
                    "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                )
        return dns_name_prefix

    def get_location(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        parameter_name = "location"

        # read the original value passed by the command
        raw_value = getattr(self.raw_param, parameter_name)
        # try to read from intermediates
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc:
            mc_property = self.mc.location

        # set defautl value
        if mc_property is not None:
            location = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
        elif intermediate is not None:
            location = intermediate
        else:
            location = raw_value

        # enable dynamic completion if the `force_update` parameter is specified when calling this getter
        dynamic_completion = force_update
        # check whether the parameter meet the conditions of dynamic completion
        if location is None:
            dynamic_completion = True
        # In case the user does not specify the parameter and it meets the conditions of automatic completion,
        # necessary information is dynamically completed.
        if dynamic_completion:
            location = _get_rg_location(
                self.cmd.cli_ctx, self.get_resource_group_name()
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, location, overwrite_exists=True
            )

        # this parameter does not need validation
        return location

    def get_kubernetes_version(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        # Note: This parameter will not be decorated into the `mc` object.
        # read the original value passed by the command
        kubernetes_version = getattr(self.raw_param, "kubernetes_version")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return kubernetes_version

    def get_no_ssh_key(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        # read the original value passed by the command
        no_ssh_key = getattr(self.raw_param, "no_ssh_key")

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            _validate_ssh_key(
                no_ssh_key=no_ssh_key, ssh_key_value=self.get_ssh_key_value()
            )
        return no_ssh_key

    def get_vm_set_type(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        parameter_name = "vm_set_type"

        # read the original value passed by the command
        raw_value = getattr(self.raw_param, parameter_name)
        # try to read from intermediates
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.type

        # set defautl value
        if mc_property is not None:
            vm_set_type = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
        elif intermediate is not None:
            vm_set_type = intermediate
        else:
            vm_set_type = raw_value

        # enable dynamic completion if the `force_update` parameter is specified when calling this getter
        dynamic_completion = force_update
        # check whether the parameter meet the conditions of dynamic completion
        if not vm_set_type:
            dynamic_completion = True
        if dynamic_completion:
            vm_set_type = _set_vm_set_type(
                vm_set_type=vm_set_type,
                kubernetes_version=self.get_kubernetes_version(),
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, vm_set_type, overwrite_exists=True
            )

        # this parameter does not need validation
        return vm_set_type

    def get_load_balancer_sku(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        parameter_name = "load_balancer_sku"

        # read the original value passed by the command
        raw_value = getattr(self.raw_param, parameter_name)
        # try to read from intermediates
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.network_profile:
            mc_property = self.mc.network_profile.load_balancer_sku

        # set defautl value
        if mc_property is not None:
            load_balancer_sku = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
        elif intermediate is not None:
            load_balancer_sku = intermediate
        else:
            load_balancer_sku = raw_value

        # enable dynamic completion if the `force_update` parameter is specified when calling this getter
        dynamic_completion = force_update
        # check whether the parameter meet the conditions of dynamic completion
        if not load_balancer_sku:
            dynamic_completion = True
        if dynamic_completion:
            load_balancer_sku = set_load_balancer_sku(
                sku=load_balancer_sku,
                kubernetes_version=self.get_kubernetes_version(),
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, load_balancer_sku, overwrite_exists=True
            )

        # validation
        if enable_validation:
            if (
                load_balancer_sku == "basic"
                and self.get_api_server_authorized_ip_ranges()
            ):
                raise MutuallyExclusiveArgumentError(
                    "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                )
        return load_balancer_sku

    def get_api_server_authorized_ip_ranges(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        parameter_name = "api_server_authorized_ip_ranges"

        # read the original value passed by the command
        raw_value = getattr(self.raw_param, parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.api_server_access_profile:
            mc_property = self.mc.api_server_access_profile.authorized_ip_ranges

        # set defautl value
        if mc_property is not None:
            api_server_authorized_ip_ranges = mc_property
        else:
            api_server_authorized_ip_ranges = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            if (
                api_server_authorized_ip_ranges
                and self.get_load_balancer_sku() == "basic"
            ):
                raise MutuallyExclusiveArgumentError(
                    "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                )
        return api_server_authorized_ip_ranges

    def get_fqdn_subdomain(
        self,
        enable_validation: bool = False,
        force_update: bool = False,
        **kwargs
    ):
        # read the original value passed by the command
        fqdn_subdomain = getattr(self.raw_param, "fqdn_subdomain")

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            if fqdn_subdomain and self.get_dns_name_prefix():
                raise MutuallyExclusiveArgumentError(
                    "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                )
        return fqdn_subdomain


class AKSCreateDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client,
        models: AKSCreateModels,
        raw_parameters: Dict,
        resource_type: ResourceType = ResourceType.MGMT_CONTAINERSERVICE,
    ):
        self.cmd = cmd
        self.client = client
        self.models = models
        # store the context in the process of assemble the ManagedCluster object
        self.context = AKSCreateContext(cmd, raw_parameters)
        # `resource_type` is used to dynamically find the model (of a specific api version) provided by the
        # containerservice SDK, most models have been passed through the `modles` parameter (instantiatied
        # from `AKSCreateModels` (or `PreviewAKSCreateModels` in aks-preview), where resource_type (i.e.,
        # api version) has been specified), a very small number of models are instantiated through internal
        # functions, one use case is that `api_server_access_profile` is initialized by function
        # `_populate_api_server_access_profile` defined in `_helpers.py`
        self.resource_type = resource_type

    def init_mc(self):
        # get subscription id and store as intermediate
        subscription_id = get_subscription_id(self.cmd.cli_ctx)
        self.context.set_intermediate(
            "subscription_id", subscription_id, overwrite_exists=True
        )

        # initialize the `ManagedCluster` object with mandatory parameters (i.e. location)
        mc = self.models.ManagedCluster(location=self.context.get_location())
        return mc

    def construct_default_mc(self):
        # An all-in-one function used to create the complete `ManagedCluster` object, which will later be
        # passed as a parameter to the underlying SDK (mgmt-containerservice) to send the actual request.
        # Note: to reduce the risk of regression introduced by refactoring, this function is not complete
        # and is being implemented gradually.
        # initialize the `ManagedCluster` object
        mc = self.init_mc()
        return mc

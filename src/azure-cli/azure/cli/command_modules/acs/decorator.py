# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.prompting import NoTTYException, prompt, prompt_pass, prompt_y_n
from knack.log import get_logger
from typing import Any, List, Dict, Tuple, Union

from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import (
    CLIInternalError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
    InvalidArgumentValueError,
    NoTTYError,
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
    _ensure_aks_service_principal,
    _get_user_assigned_identity,
    subnet_role_assignment_exists,
    _add_role_assignment,
)

logger = get_logger(__name__)


def safe_list_get(li: List, idx: int, default: Any = None) -> Any:
    """Get an element from a list without raising IndexError.

    Attempt to get the element with index idx from a list-like object li, and if the index is invalid (such as out of
    range), return default (whose default value is None).

    :return: an element of any type
    """
    if isinstance(li, list):
        try:
            return li[idx]
        except IndexError:
            return default
    return None


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class AKSCreateModels:
    """Store the models used in aks_create.

    The api version of the class corresponding to a model is determined by resource_type.
    """
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
        self.ManagedServiceIdentityUserAssignedIdentitiesValue = (
            self.__cmd.get_models(
                "ManagedServiceIdentityUserAssignedIdentitiesValue",
                resource_type=self.resource_type,
                operation_group="managed_clusters",
            )
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
        # not directly used
        self.ManagedClusterAPIServerAccessProfile = self.__cmd.get_models(
            "ManagedClusterAPIServerAccessProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )


# pylint: disable=too-many-public-methods
class AKSCreateContext:
    """Implement getter functions for all parameters in aks_create.

    Note: One of the most basic principles is that when parameters are put into a certain profile, and then
    decorated into the ManagedCluster object, it shouldn't and can't be modified, only read-only operations
    (e.g. validation) can be performed.

    This class also stores a copy of the original function parameters, some intermediate variables (such as the
    subscription ID) and a reference of the ManagedCluster object.

    When adding a new parameter for aks_create, please also provide a "getter" function named `get_xxx`, where `xxx` is
    the parameter name. In this function, the process of obtaining parameter values, dynamic completion (optional),
    and validation (optional) should be followed. The obtaining of parameter values should further follow the order
    of obtaining from the ManagedCluster object or from the original value.

    Attention: In case of checking the validity of parameters, make sure enable_validation is never set to True and
    read_only is set to True when necessary to avoid loop calls, when using the getter function to obtain the value of
    other parameters.
    """
    def __init__(self, cmd: AzCliCommand, raw_parameters: Dict):
        self.cmd = cmd
        if not isinstance(raw_parameters, dict):
            raise CLIInternalError(
                "Unexpected raw_parameters object with type '{}'.".format(
                    type(raw_parameters)
                )
            )
        self.raw_param = raw_parameters
        self.intermediates = dict()
        self.mc = None

    def attach_mc(self, mc):
        if self.mc is None:
            self.mc = mc
        else:
            msg = "the same" if self.mc == mc else "different"
            raise CLIInternalError(
                "Attempting to attach the `mc` object again, the two objects are {}.".format(
                    msg
                )
            )

    def get_intermediate(self, variable_name: str, default_value: Any = None):
        if variable_name not in self.intermediates:
            msg = "The intermediate '{}' does not exist, return default value '{}'.".format(
                variable_name, default_value
            )
            logger.debug(msg)
        return self.intermediates.get(variable_name, default_value)

    def set_intermediate(
        self, variable_name: str, value: Any, overwrite_exists: bool = False
    ):
        if variable_name in self.intermediates:
            if overwrite_exists:
                msg = "The intermediate '{}' is overwritten. Original value: '{}', new value: '{}'.".format(
                    variable_name, self.intermediates.get(variable_name), value
                )
                logger.debug(msg)
                self.intermediates[variable_name] = value
            elif self.intermediates.get(variable_name) != value:
                msg = "The intermediate '{}' already exists, but overwrite is not enabled." \
                    "Original value: '{}', candidate value: '{}'.".format(
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

    # pylint: disable=unused-argument
    def get_resource_group_name(self, **kwargs) -> str:
        """Obtain the value of resource_group_name.

        Note: resource_group_name will not be decorated into the `mc` object.

        The value of this parameter should be provided by user explicitly.

        :return: string
        """
        # read the original value passed by the command
        resource_group_name = self.raw_param.get("resource_group_name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return resource_group_name

    # pylint: disable=unused-argument
    def get_name(self, **kwargs) -> str:
        """Obtain the value of name.

        Note: name will not be decorated into the `mc` object.

        The value of this parameter should be provided by user explicitly.

        :return: string
        """
        # read the original value passed by the command
        name = self.raw_param.get("name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return name

    # pylint: disable=unused-argument
    def get_ssh_key_value(
        self, enable_validation: bool = False, **kwargs
    ) -> str:
        """Obtain the value of ssh_key_value.

        If the user does not specify this parameter, the validator function "validate_ssh_key" checks the default file
        location "~/.ssh/id_rsa.pub", if the file exists, read its content and return; otherise, create a key pair at
        "~/.ssh/id_rsa.pub" and return the public key.
        If the user provides a string-like input, the validator function "validate_ssh_key" checks whether it is a file
        path, if so, read its content and return; if it is a valid public key, return it; otherwise, create a key pair
        there and return the public key.

        This function supports the option of enable_validation. When enabled, it will call "_validate_ssh_key" to
        verify the validity of ssh_key_value. If parameter no_ssh_key is set to True, verification will be skipped;
        otherwise, a CLIError will be raised when the value of ssh_key_value is invalid.

        :return: string
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("ssh_key_value")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if (
            self.mc and
            self.mc.linux_profile and
            self.mc.linux_profile.ssh and
            self.mc.linux_profile.ssh.public_keys
        ):
            public_key_obj = safe_list_get(
                self.mc.linux_profile.ssh.public_keys, 0, None
            )
            if public_key_obj:
                value_obtained_from_mc = public_key_obj.key_data

        # set default value
        if value_obtained_from_mc is not None:
            ssh_key_value = value_obtained_from_mc
        else:
            ssh_key_value = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            _validate_ssh_key(
                no_ssh_key=self.get_no_ssh_key(), ssh_key_value=ssh_key_value
            )
        return ssh_key_value

    # pylint: disable=unused-argument
    def get_dns_name_prefix(
        self, enable_validation: bool = False, **kwargs
    ) -> Union[str, None]:
        """Dynamically obtain the value of ssh_key_value according to the context.

        When both dns_name_prefix and fqdn_subdomain are not assigned, dynamic completion will be triggerd. Function
        "_get_default_dns_prefix" will be called to create a default dns_name_prefix composed of name (cluster),
        resource_group_name, and subscription_id.

        This function supports the option of enable_validation. When enabled, it will check if both dns_name_prefix and
        fqdn_subdomain are assigend, if so, raise the MutuallyExclusiveArgumentError.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        parameter_name = "dns_name_prefix"
        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc:
            value_obtained_from_mc = self.mc.dns_prefix

        # set default value
        read_from_mc = False
        if value_obtained_from_mc is not None:
            dns_name_prefix = value_obtained_from_mc
            read_from_mc = True
        else:
            dns_name_prefix = raw_value

        # skip dynamic completion & validation if option read_only is specified
        if kwargs.get("read_only"):
            return dns_name_prefix

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if not dns_name_prefix and not self.get_fqdn_subdomain():
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        # In case the user does not specify the parameter and it meets the conditions of automatic completion,
        # necessary information is dynamically completed.
        if dynamic_completion:
            dns_name_prefix = _get_default_dns_prefix(
                name=self.get_name(),
                resource_group_name=self.get_resource_group_name(),
                subscription_id=self.get_intermediate("subscription_id"),
            )

        # validation
        if enable_validation:
            if dns_name_prefix and self.get_fqdn_subdomain():
                raise MutuallyExclusiveArgumentError(
                    "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                )
        return dns_name_prefix

    # pylint: disable=unused-argument
    def get_location(self, **kwargs) -> str:
        """Dynamically obtain the value of location according to the context.

        When location is not assigned, dynamic completion will be triggerd. Function "_get_rg_location" will be called
        to get the location of the provided resource group, which internally used ResourceManagementClient to send
        the request.

        :return: string
        """
        parameter_name = "location"
        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc:
            value_obtained_from_mc = self.mc.location

        # set default value
        read_from_mc = False
        if value_obtained_from_mc is not None:
            location = value_obtained_from_mc
            read_from_mc = True
        else:
            location = raw_value

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if location is None:
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            location = _get_rg_location(
                self.cmd.cli_ctx, self.get_resource_group_name()
            )

        # this parameter does not need validation
        return location

    # pylint: disable=unused-argument
    def get_kubernetes_version(self, **kwargs) -> str:
        """Obtain the value of kubernetes_version.

        :return: string
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("kubernetes_version")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc:
            value_obtained_from_mc = self.mc.kubernetes_version

        # set default value
        if value_obtained_from_mc is not None:
            kubernetes_version = value_obtained_from_mc
        else:
            kubernetes_version = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return kubernetes_version

    # pylint: disable=unused-argument
    def get_no_ssh_key(self, enable_validation: bool = False, **kwargs) -> bool:
        """Obtain the value of name.

        Note: no_ssh_key will not be decorated into the `mc` object.

        This function supports the option of enable_validation. When enabled, it will check if both dns_name_prefix and
        fqdn_subdomain are assigend, if so, raise the MutuallyExclusiveArgumentError.
        This function supports the option of enable_validation. When enabled, it will call "_validate_ssh_key" to
        verify the validity of ssh_key_value. If parameter no_ssh_key is set to True, verification will be skipped;
        otherwise, a CLIError will be raised when the value of ssh_key_value is invalid.

        :return: bool
        """
        # read the original value passed by the command
        no_ssh_key = self.raw_param.get("no_ssh_key")

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            _validate_ssh_key(
                no_ssh_key=no_ssh_key, ssh_key_value=self.get_ssh_key_value()
            )
        return no_ssh_key

    # pylint: disable=unused-argument
    def get_vm_set_type(self, **kwargs) -> str:
        """Dynamically obtain the value of vm_set_type according to the context.

        Dynamic completion will be triggerd by default. Function "_set_vm_set_type" will be called and the
        corresponding vm set type will be returned according to the value of kubernetes_version. It will also
        normalize the value as server validation is case-sensitive.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string
        """
        parameter_name = "vm_set_type"
        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.type

        # set default value
        read_from_mc = False
        if value_obtained_from_mc is not None:
            vm_set_type = value_obtained_from_mc
            read_from_mc = True
        else:
            vm_set_type = raw_value

        # skip dynamic completion & validation if option read_only is specified
        if kwargs.get("read_only"):
            return vm_set_type

        # the value verified by the validator may have case problems, and the
        # "_set_vm_set_type" function will adjust it
        dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            vm_set_type = _set_vm_set_type(
                vm_set_type=vm_set_type,
                kubernetes_version=self.get_kubernetes_version(),
            )

        # this parameter does not need validation
        return vm_set_type

    # pylint: disable=unused-argument
    def get_load_balancer_sku(
        self, enable_validation: bool = False, **kwargs
    ) -> str:
        """Dynamically obtain the value of load_balancer_sku according to the context.

        When load_balancer_sku is not assigned, dynamic completion will be triggerd. Function "set_load_balancer_sku"
        will be called and the corresponding load balancer sku will be returned according to the value of
        kubernetes_version.

        This function supports the option of enable_validation. When enabled, it will check if load_balancer_sku equals
        to "basic" when api_server_authorized_ip_ranges is assigned, if so, raise the MutuallyExclusiveArgumentError.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string
        """
        parameter_name = "load_balancer_sku"
        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.network_profile:
            value_obtained_from_mc = self.mc.network_profile.load_balancer_sku

        # set default value
        read_from_mc = False
        if value_obtained_from_mc is not None:
            load_balancer_sku = value_obtained_from_mc
            read_from_mc = True
        else:
            load_balancer_sku = raw_value

        # skip dynamic completion & validation if option read_only is specified
        if kwargs.get("read_only"):
            return load_balancer_sku

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if not load_balancer_sku:
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            load_balancer_sku = set_load_balancer_sku(
                sku=load_balancer_sku,
                kubernetes_version=self.get_kubernetes_version(),
            )

        # validation
        if enable_validation:
            if (
                load_balancer_sku == "basic" and
                self.get_api_server_authorized_ip_ranges()
            ):
                raise MutuallyExclusiveArgumentError(
                    "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                )
        return load_balancer_sku

    # pylint: disable=unused-argument
    def get_api_server_authorized_ip_ranges(
        self, enable_validation: bool = False, **kwargs
    ) -> Union[str, List[str], None]:
        """Obtain the value of api_server_authorized_ip_ranges.

        This function supports the option of enable_validation. When enabled, it will check if load_balancer_sku equals
        to "basic" when api_server_authorized_ip_ranges is assigned, if so, raise the MutuallyExclusiveArgumentError.

        :return: string, empty list or list of strings, or None
        """
        parameter_name = "api_server_authorized_ip_ranges"
        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.api_server_access_profile:
            value_obtained_from_mc = (
                self.mc.api_server_access_profile.authorized_ip_ranges
            )

        # set default value
        if value_obtained_from_mc is not None:
            api_server_authorized_ip_ranges = value_obtained_from_mc
        else:
            api_server_authorized_ip_ranges = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            if (
                api_server_authorized_ip_ranges and
                self.get_load_balancer_sku() == "basic"
            ):
                raise MutuallyExclusiveArgumentError(
                    "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                )
        return api_server_authorized_ip_ranges

    # pylint: disable=unused-argument
    def get_fqdn_subdomain(
        self, enable_validation: bool = False, **kwargs
    ) -> Union[str, None]:
        """Obtain the value of fqdn_subdomain.

        This function supports the option of enable_validation. When enabled, it will check if both dns_name_prefix and
        fqdn_subdomain are assigend, if so, raise the MutuallyExclusiveArgumentError.

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("fqdn_subdomain")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc:
            value_obtained_from_mc = self.mc.fqdn_subdomain

        # set default value
        if value_obtained_from_mc is not None:
            fqdn_subdomain = value_obtained_from_mc
        else:
            fqdn_subdomain = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            if fqdn_subdomain and self.get_dns_name_prefix(read_only=True):
                raise MutuallyExclusiveArgumentError(
                    "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                )
        return fqdn_subdomain

    # pylint: disable=unused-argument
    def get_nodepool_name(self, **kwargs) -> str:
        """Dynamically obtain the value of nodepool_name according to the context.

        When additional option enable_trim is enabled, dynamic completion will be triggerd.

        This function supports the option of enable_trim. When enabled, it will normalize the value of nodepool_name.
        If no value is assigned, the default value "nodepool1" is set, and if the string length is greater than 12,
        it is truncated.

        :return: string
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("nodepool_name")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.name

        # set default value
        read_from_mc = False
        if value_obtained_from_mc is not None:
            nodepool_name = value_obtained_from_mc
            read_from_mc = True
        else:
            nodepool_name = raw_value

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if kwargs.get("enable_trim", False):
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            if not nodepool_name:
                nodepool_name = "nodepool1"
            else:
                nodepool_name = nodepool_name[:12]

        # this parameter does not need validation
        return nodepool_name

    # pylint: disable=unused-argument
    def get_nodepool_tags(self, **kwargs) -> Union[Dict[str, str], None]:
        """Obtain the value of nodepool_tags.

        :return: Dictionary or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("nodepool_tags")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.tags

        # set default value
        if value_obtained_from_mc is not None:
            nodepool_tags = value_obtained_from_mc
        else:
            nodepool_tags = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nodepool_tags

    # pylint: disable=unused-argument
    def get_nodepool_labels(self, **kwargs) -> Union[Dict[str, str], None]:
        """Obtain the value of nodepool_labels.

        :return: Dictionary or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("nodepool_labels")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.node_labels

        # set default value
        if value_obtained_from_mc is not None:
            nodepool_labels = value_obtained_from_mc
        else:
            nodepool_labels = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nodepool_labels

    # pylint: disable=unused-argument
    def get_node_count(self, enable_validation: bool = False, **kwargs) -> int:
        """Obtain the value of node_count.

        This function supports the option of enable_validation. When enabled, on the premise that
        enable_cluster_autoscaler is enabled, it will check whether both min_count and max_count are assigned, if not,
        raise the RequiredArgumentMissingError; if will also check whether node_count is between min_count and
        max_count, if not, raise the InvalidArgumentValueError.

        :return: int
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_count")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.count

        # set default value
        if value_obtained_from_mc is not None:
            node_count = value_obtained_from_mc
        else:
            node_count = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            enable_cluster_autoscaler = self.get_enable_cluster_autoscaler()
            min_count = self.get_min_count()
            max_count = self.get_max_count()
            if enable_cluster_autoscaler:
                if min_count is None or max_count is None:
                    raise RequiredArgumentMissingError(
                        "Please specify both min-count and max-count when --enable-cluster-autoscaler enabled"
                    )
                if node_count < min_count or node_count > max_count:
                    raise InvalidArgumentValueError(
                        "node-count is not in the range of min-count and max-count"
                    )

        return int(node_count)

    # pylint: disable=unused-argument
    def get_node_vm_size(self, **kwargs) -> str:
        """Obtain the value of node_vm_size.

        :return: string
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_vm_size")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.vm_size

        # set default value
        if value_obtained_from_mc is not None:
            node_vm_size = value_obtained_from_mc
        else:
            node_vm_size = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_vm_size

    # pylint: disable=unused-argument
    def get_vnet_subnet_id(self, **kwargs) -> Union[str, None]:
        """Obtain the value of vnet_subnet_id.

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("vnet_subnet_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.vnet_subnet_id

        # set default value
        if value_obtained_from_mc is not None:
            vnet_subnet_id = value_obtained_from_mc
        else:
            vnet_subnet_id = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return vnet_subnet_id

    # pylint: disable=unused-argument
    def get_ppg(self, **kwargs) -> Union[str, None]:
        """Obtain the value of ppg(proximity_placement_group_id).

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("ppg")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = (
                    agent_pool_profile.proximity_placement_group_id
                )

        # set default value
        if value_obtained_from_mc is not None:
            ppg = value_obtained_from_mc
        else:
            ppg = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return ppg

    # pylint: disable=unused-argument
    def get_zones(self, **kwargs) -> Union[List[str], None]:
        """Obtain the value of zones.

        :return: list of strings or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("zones")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.availability_zones

        # set default value
        if value_obtained_from_mc is not None:
            zones = value_obtained_from_mc
        else:
            zones = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return zones

    # pylint: disable=unused-argument
    def get_enable_node_public_ip(self, **kwargs) -> bool:
        """Obtain the value of enable_node_public_ip.

        :return: bool
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_node_public_ip")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = (
                    agent_pool_profile.enable_node_public_ip
                )

        # set default value
        if value_obtained_from_mc is not None:
            enable_node_public_ip = value_obtained_from_mc
        else:
            enable_node_public_ip = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_node_public_ip

    # pylint: disable=unused-argument
    def get_node_public_ip_prefix_id(self, **kwargs) -> Union[str, None]:
        """Obtain the value of node_public_ip_prefix_id.

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_public_ip_prefix_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = (
                    agent_pool_profile.node_public_ip_prefix_id
                )

        # set default value
        if value_obtained_from_mc is not None:
            node_public_ip_prefix_id = value_obtained_from_mc
        else:
            node_public_ip_prefix_id = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_public_ip_prefix_id

    # pylint: disable=unused-argument
    def get_enable_encryption_at_host(self, **kwargs) -> bool:
        """Obtain the value of enable_encryption_at_host.

        :return: bool
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_encryption_at_host")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = (
                    agent_pool_profile.enable_encryption_at_host
                )

        # set default value
        if value_obtained_from_mc is not None:
            enable_encryption_at_host = value_obtained_from_mc
        else:
            enable_encryption_at_host = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_encryption_at_host

    # pylint: disable=unused-argument
    def get_enable_ultra_ssd(self, **kwargs) -> bool:
        """Obtain the value of enable_ultra_ssd.

        :return: bool
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_ultra_ssd")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.enable_ultra_ssd

        # set default value
        if value_obtained_from_mc is not None:
            enable_ultra_ssd = value_obtained_from_mc
        else:
            enable_ultra_ssd = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_ultra_ssd

    # pylint: disable=unused-argument
    def get_max_pods(self, **kwargs) -> Union[int, None]:
        """Obtain the value of max_pods.

        Note: int 0 is converted to None.

        :return: int or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("max_pods")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.max_pods

        # set default value
        if value_obtained_from_mc is not None:
            max_pods = value_obtained_from_mc
        else:
            max_pods = raw_value
            # Note: int 0 is converted to None
            if max_pods:
                max_pods = int(max_pods)
            else:
                max_pods = None

        # this parameter does not need validation
        return max_pods

    # pylint: disable=unused-argument
    def get_node_osdisk_size(self, **kwargs) -> Union[int, None]:
        """Obtain the value of node_osdisk_size.

        Note: int 0 is converted to None.

        :return: int or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_osdisk_size")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.os_disk_size_gb

        # set default value
        if value_obtained_from_mc is not None:
            node_osdisk_size = value_obtained_from_mc
        else:
            node_osdisk_size = raw_value
            # Note: 0 is converted to None
            if node_osdisk_size:
                node_osdisk_size = int(node_osdisk_size)
            else:
                node_osdisk_size = None

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_osdisk_size

    # pylint: disable=unused-argument
    def get_node_osdisk_type(self, **kwargs) -> Union[str, None]:
        """Obtain the value of node_osdisk_size.

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_osdisk_type")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.os_disk_type

        # set default value
        if value_obtained_from_mc is not None:
            node_osdisk_type = value_obtained_from_mc
        else:
            node_osdisk_type = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_osdisk_type

    # pylint: disable=unused-argument
    def get_enable_cluster_autoscaler(
        self, enable_validation: bool = False, **kwargs
    ) -> bool:
        """Obtain the value of enable_cluster_autoscaler.

        This function supports the option of enable_validation. When enabled, on the premise that
        enable_cluster_autoscaler is enabled, it will check whether both min_count and max_count are assigned, if not,
        raise the RequiredArgumentMissingError; if will also check whether min_count is less than max_count and
        node_count is between min_count and max_count, if not, raise the InvalidArgumentValueError. If
        enable_cluster_autoscaler is not enabled, it will check whether any of min_count or max_count is assigned,
        if so, raise the RequiredArgumentMissingError.

        :return: bool
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_cluster_autoscaler")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.enable_auto_scaling

        # set default value
        if value_obtained_from_mc is not None:
            enable_cluster_autoscaler = value_obtained_from_mc
        else:
            enable_cluster_autoscaler = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            min_count = self.get_min_count()
            max_count = self.get_max_count()
            node_count = self.get_node_count()
            if enable_cluster_autoscaler:
                if min_count is None or max_count is None:
                    raise RequiredArgumentMissingError(
                        "Please specify both min-count and max-count when --enable-cluster-autoscaler enabled"
                    )
                if min_count > max_count:
                    raise InvalidArgumentValueError(
                        "Value of min-count should be less than or equal to value of max-count"
                    )
                if node_count < min_count or node_count > max_count:
                    raise InvalidArgumentValueError(
                        "node-count is not in the range of min-count and max-count"
                    )
            else:
                if min_count is not None or max_count is not None:
                    raise RequiredArgumentMissingError(
                        "min-count and max-count are required for --enable-cluster-autoscaler, please use the flag"
                    )
        return enable_cluster_autoscaler

    # pylint: disable=unused-argument
    def get_min_count(
        self, enable_validation: bool = False, **kwargs
    ) -> Union[int, None]:
        """Obtain the value of min_count.

        This function supports the option of enable_validation. When enabled, on the premise that
        enable_cluster_autoscaler is enabled, it will check whether both min_count and max_count are assigned, if not,
        raise the RequiredArgumentMissingError; if will also check whether min_count is less than max_count and
        node_count is between min_count and max_count, if not, raise the InvalidArgumentValueError. If
        enable_cluster_autoscaler is not enabled, it will check whether any of min_count or max_count is assigned,
        if so, raise the RequiredArgumentMissingError.

        :return: int or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("min_count")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.min_count

        # set default value
        if value_obtained_from_mc is not None:
            min_count = value_obtained_from_mc
        else:
            min_count = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            enable_cluster_autoscaler = self.get_enable_cluster_autoscaler()
            max_count = self.get_max_count()
            node_count = self.get_node_count()
            if enable_cluster_autoscaler:
                if min_count is None or max_count is None:
                    raise RequiredArgumentMissingError(
                        "Please specify both min-count and max-count when --enable-cluster-autoscaler enabled"
                    )
                if min_count > max_count:
                    raise InvalidArgumentValueError(
                        "Value of min-count should be less than or equal to value of max-count"
                    )
                if node_count < min_count or node_count > max_count:
                    raise InvalidArgumentValueError(
                        "node-count is not in the range of min-count and max-count"
                    )
            else:
                if min_count is not None or max_count is not None:
                    raise RequiredArgumentMissingError(
                        "min-count and max-count are required for --enable-cluster-autoscaler, please use the flag"
                    )
        return min_count

    # pylint: disable=unused-argument
    def get_max_count(
        self, enable_validation: bool = False, **kwargs
    ) -> Union[int, None]:
        """Obtain the value of max_count.

        This function supports the option of enable_validation. When enabled, on the premise that
        enable_cluster_autoscaler is enabled, it will check whether both min_count and max_count are assigned, if not,
        raise the RequiredArgumentMissingError; if will also check whether min_count is less than max_count and
        node_count is between min_count and max_count, if not, raise the InvalidArgumentValueError. If
        enable_cluster_autoscaler is not enabled, it will check whether any of min_count or max_count is assigned,
        if so, raise the RequiredArgumentMissingError.

        :return: int or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("max_count")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                value_obtained_from_mc = agent_pool_profile.max_count

        # set default value
        if value_obtained_from_mc is not None:
            max_count = value_obtained_from_mc
        else:
            max_count = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            enable_cluster_autoscaler = self.get_enable_cluster_autoscaler()
            min_count = self.get_min_count()
            node_count = self.get_node_count()
            if enable_cluster_autoscaler:
                if min_count is None or max_count is None:
                    raise RequiredArgumentMissingError(
                        "Please specify both min-count and max-count when --enable-cluster-autoscaler enabled"
                    )
                if min_count > max_count:
                    raise InvalidArgumentValueError(
                        "Value of min-count should be less than or equal to value of max-count"
                    )
                if node_count < min_count or node_count > max_count:
                    raise InvalidArgumentValueError(
                        "node-count is not in the range of min-count and max-count"
                    )
            else:
                if min_count is not None or max_count is not None:
                    raise RequiredArgumentMissingError(
                        "min-count and max-count are required for --enable-cluster-autoscaler, please use the flag"
                    )
        return max_count

    # pylint: disable=unused-argument
    def get_admin_username(self, **kwargs) -> str:
        """Obtain the value of admin_username.

        :return: str
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("admin_username")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.linux_profile:
            value_obtained_from_mc = self.mc.linux_profile.admin_username

        # set default value
        if value_obtained_from_mc is not None:
            admin_username = value_obtained_from_mc
        else:
            admin_username = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return admin_username

    # pylint: disable=unused-argument
    def get_windows_admin_username_and_password(
        self, **kwargs
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Dynamically obtain the value of windows_admin_username and windows_admin_password according to the context.

        When ont of windows_admin_username and windows_admin_password is not assigned, dynamic completion will be
        triggerd. The user will be prompted to enter the missing windows_admin_username or windows_admin_password in
        tty (pseudo terminal). If the program is running in a non-interactive environment, a NoTTYError error will be
        raised.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: a tuple containing two elements of string or None
        """
        # windows_admin_username
        # read the original value passed by the command
        username_raw_value = self.raw_param.get("windows_admin_username")
        # try to read the property value corresponding to the parameter from the `mc` object
        username_value_obtained_from_mc = None
        if self.mc and self.mc.windows_profile:
            username_value_obtained_from_mc = (
                self.mc.windows_profile.admin_username
            )

        # set default value
        username_read_from_mc = False
        if username_value_obtained_from_mc is not None:
            windows_admin_username = username_value_obtained_from_mc
            username_read_from_mc = True
        else:
            windows_admin_username = username_raw_value

        # windows_admin_password
        # read the original value passed by the command
        password_raw_value = self.raw_param.get("windows_admin_password")
        # try to read the property value corresponding to the parameter from the `mc` object
        password_value_obtained_from_mc = None
        if self.mc and self.mc.windows_profile:
            password_value_obtained_from_mc = (
                self.mc.windows_profile.admin_password
            )

        # set default value
        password_read_from_mc = False
        if password_value_obtained_from_mc is not None:
            windows_admin_password = password_value_obtained_from_mc
            password_read_from_mc = True
        else:
            windows_admin_password = password_raw_value

        # consistent check
        if username_read_from_mc != password_read_from_mc:
            raise CLIInternalError(
                "Inconsistent state detected, one of windows admin name and password is read from the `mc` object."
            )

        # skip dynamic completion & validation if option read_only is specified
        if kwargs.get("read_only"):
            return windows_admin_username, windows_admin_password

        username_dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        # to avoid that windows_admin_password is set but windows_admin_username is not
        if windows_admin_username is None and windows_admin_password:
            username_dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        username_dynamic_completion = (
            username_dynamic_completion and not username_read_from_mc
        )
        if username_dynamic_completion:
            try:
                windows_admin_username = prompt("windows_admin_username: ")
                # The validation for admin_username in ManagedClusterWindowsProfile will fail even if
                # users still set windows_admin_username to empty here
            except NoTTYException:
                raise NoTTYError(
                    "Please specify username for Windows in non-interactive mode."
                )

        password_dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        # to avoid that windows_admin_username is set but windows_admin_password is not
        if windows_admin_password is None and windows_admin_username:
            password_dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        password_dynamic_completion = (
            password_dynamic_completion and not password_read_from_mc
        )
        if password_dynamic_completion:
            try:
                windows_admin_password = prompt_pass(
                    msg="windows-admin-password: ", confirm=True
                )
            except NoTTYException:
                raise NoTTYError(
                    "Please specify both username and password in non-interactive mode."
                )

        # these parameters does not need validation
        return windows_admin_username, windows_admin_password

    # pylint: disable=unused-argument
    def get_enable_ahub(self, **kwargs) -> bool:
        """Obtain the value of enable_ahub.

        Note: enable_ahub will not be directly decorated into the `mc` object.

        :return: bool
        """
        # read the original value passed by the command
        enable_ahub = self.raw_param.get("enable_ahub")

        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_ahub")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.windows_profile:
            value_obtained_from_mc = self.mc.windows_profile.license_type == "Windows_Server"

        # set default value
        if value_obtained_from_mc is not None:
            enable_ahub = value_obtained_from_mc
        else:
            enable_ahub = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_ahub

    # pylint: disable=unused-argument,too-many-statements
    def get_service_principal_and_client_secret(
        self, **kwargs
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Dynamically obtain the values of service_principal and client_secret according to the context.

        When service_principal and client_secret are not assigned and enable_managed_identity is True, dynamic
        completion will not be triggered. For other cases, dynamic completion will be triggered.
        When client_secret is given but service_principal is not, dns_name_prefix or fqdn_subdomain will be used to
        create a service principal. The parameters subscription_id, location and name (cluster) are also required when
        calling function "_ensure_aks_service_principal", which internally used GraphRbacManagementClient to send
        the request.
        When service_principal is given but client_secret is not, function "_ensure_aks_service_principal" would raise
        CLIError.

        :return: a tuple containing two elements of string or None
        """
        # service_principal
        sp_parameter_name = "service_principal"
        sp_property_name_in_mc = "client_id"
        # read the original value passed by the command
        sp_raw_value = self.raw_param.get(sp_parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        sp_value_obtained_from_mc = None
        if self.mc and self.mc.service_principal_profile:
            sp_value_obtained_from_mc = getattr(
                self.mc.service_principal_profile, sp_property_name_in_mc
            )
        # set default value
        sp_read_from_mc = False
        if sp_value_obtained_from_mc is not None:
            service_principal = sp_value_obtained_from_mc
            sp_read_from_mc = True
        else:
            service_principal = sp_raw_value

        # client_secret
        secret_parameter_name = "client_secret"
        secret_property_name_in_mc = "secret"
        # read the original value passed by the command
        secret_raw_value = self.raw_param.get(secret_parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        secret_value_obtained_from_mc = None
        if self.mc and self.mc.service_principal_profile:
            secret_value_obtained_from_mc = getattr(
                self.mc.service_principal_profile, secret_property_name_in_mc
            )
        # set default value
        secret_read_from_mc = False
        if secret_value_obtained_from_mc is not None:
            client_secret = secret_value_obtained_from_mc
            secret_read_from_mc = True
        else:
            client_secret = secret_raw_value

        # consistent check
        if sp_read_from_mc != secret_read_from_mc:
            raise CLIInternalError(
                "Inconsistent state detected, one of sp and secret is read from the `mc` object."
            )

        # skip dynamic completion & validation if option read_only is specified
        if kwargs.get("read_only"):
            return service_principal, client_secret

        # dynamic completion for service_principal and client_secret
        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        enable_managed_identity = self.get_enable_managed_identity(read_only=True)
        if not (
            enable_managed_identity and
            not service_principal and
            not client_secret
        ):
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = (
            dynamic_completion and
            not sp_read_from_mc and
            not secret_read_from_mc
        )
        if dynamic_completion:
            principal_obj = _ensure_aks_service_principal(
                cli_ctx=self.cmd.cli_ctx,
                service_principal=service_principal,
                client_secret=client_secret,
                subscription_id=self.get_intermediate(
                    "subscription_id", None
                ),
                dns_name_prefix=self.get_dns_name_prefix(),
                fqdn_subdomain=self.get_fqdn_subdomain(),
                location=self.get_location(),
                name=self.get_name(),
            )
            service_principal = principal_obj.get("service_principal")
            client_secret = principal_obj.get("client_secret")

        # these parameters do not need validation
        return service_principal, client_secret

    # pylint: disable=unused-argument
    def get_enable_managed_identity(
        self, enable_validation: bool = False, **kwargs
    ) -> bool:
        """Dynamically obtain the values of service_principal and client_secret according to the context.

        Note: enable_managed_identity will not be directly decorated into the `mc` object.

        When both service_principal and client_secret are assigned and enable_managed_identity is True, dynamic
        completion will be triggered. The value of enable_managed_identity will be set to False.

        :return: bool
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_managed_identity")
        # try to read the property value corresponding to the parameter from the `mc` object
        value_obtained_from_mc = None
        if self.mc and self.mc.identity:
            value_obtained_from_mc = self.mc.identity.type is not None

        # set default value
        read_from_mc = False
        if value_obtained_from_mc is not None:
            enable_managed_identity = value_obtained_from_mc
            read_from_mc = True
        else:
            enable_managed_identity = raw_value

        # skip dynamic completion & validation if option read_only is specified
        if kwargs.get("read_only"):
            return enable_managed_identity

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        (
            service_principal,
            client_secret,
        ) = self.get_service_principal_and_client_secret(read_only=True)
        if service_principal and client_secret:
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            enable_managed_identity = False

        # validation
        if enable_validation:
            # TODO: add validation
            pass
        return enable_managed_identity

    # pylint: disable=unused-argument
    def get_skip_subnet_role_assignment(self, **kwargs) -> bool:
        """Obtain the value of skip_subnet_role_assignment.

        Note: skip_subnet_role_assignment will not be decorated into the `mc` object.

        :return: bool
        """
        # read the original value passed by the command
        skip_subnet_role_assignment = self.raw_param.get("skip_subnet_role_assignment")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return skip_subnet_role_assignment

    # pylint: disable=unused-argument
    def get_assign_identity(self, **kwargs) -> Union[str, None]:
        """Obtain the value of assign_identity.

        Note: assign_identity will not be decorated into the `mc` object.

        :return: string or None
        """
        # read the original value passed by the command
        assign_identity = self.raw_param.get("assign_identity")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return assign_identity

    # pylint: disable=unused-argument
    def get_user_assigned_identity_client_id(self, **kwargs) -> str:
        """Obtain the client_id of user assigned identity.

        Note: this is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the client_id field in the
        returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = self.get_assign_identity()
        if assigned_identity is None or assigned_identity == "":
            raise RequiredArgumentMissingError("No assigned identity provided.")
        return _get_user_assigned_identity(self.cmd.cli_ctx, assigned_identity).client_id

    # pylint: disable=unused-argument
    def get_user_assigned_identity_object_id(self, **kwargs) -> str:
        """Obtain the principal_id of user assigned identity.

        Note: this is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the principal_id field in
        the returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = self.get_assign_identity()
        if assigned_identity is None or assigned_identity == "":
            raise RequiredArgumentMissingError("No assigned identity provided.")
        return _get_user_assigned_identity(self.cmd.cli_ctx, assigned_identity).principal_id

    # pylint: disable=unused-argument
    def get_yes(self, **kwargs) -> bool:
        """Obtain the value of yes.

        Note: yes will not be decorated into the `mc` object.

        :return: yes
        """
        # read the original value passed by the command
        yes = self.raw_param.get("yes")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return yes


class AKSCreateDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client,
        models: AKSCreateModels,
        raw_parameters: Dict,
        resource_type: ResourceType = ResourceType.MGMT_CONTAINERSERVICE,
    ):
        """Internal controller of aks_create.

        Break down the all-in-one aks_create function into several relatively independent functions (some of them have
        a certain order dependency) that only focus on a specific profile or process a specific piece of logic.
        In addition, an overall control function is provided. By calling the aforementioned independent functions one
        by one, a complete ManagedCluster object is gradually decorated and finally requests are sent to create a
        cluster.
        """
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
        """Initialize the ManagedCluster object with required parameter location.

        The function "get_subscription_id" will be called, which depends on "az login" in advance, the returned
        subscription_id will be stored as an intermediate.

        :return: the ManagedCluster object
        """
        # get subscription id and store as intermediate
        subscription_id = get_subscription_id(self.cmd.cli_ctx)
        self.context.set_intermediate(
            "subscription_id", subscription_id, overwrite_exists=True
        )

        # initialize the `ManagedCluster` object with mandatory parameters (i.e. location)
        mc = self.models.ManagedCluster(location=self.context.get_location())
        return mc

    def set_up_agent_pool_profiles(self, mc):
        """Set up agent pool profiles for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            # Must be 12 chars or less before ACS RP adds to it
            name=self.context.get_nodepool_name(enable_trim=True),
            tags=self.context.get_nodepool_tags(),
            node_labels=self.context.get_nodepool_labels(),
            count=self.context.get_node_count(enable_validation=True),
            vm_size=self.context.get_node_vm_size(),
            os_type="Linux",
            vnet_subnet_id=self.context.get_vnet_subnet_id(),
            proximity_placement_group_id=self.context.get_ppg(),
            availability_zones=self.context.get_zones(),
            enable_node_public_ip=self.context.get_enable_node_public_ip(),
            node_public_ip_prefix_id=self.context.get_node_public_ip_prefix_id(),
            enable_encryption_at_host=self.context.get_enable_encryption_at_host(),
            enable_ultra_ssd=self.context.get_enable_ultra_ssd(),
            max_pods=self.context.get_max_pods(),
            type=self.context.get_vm_set_type(),
            mode="System",
            os_disk_size_gb=self.context.get_node_osdisk_size(),
            os_disk_type=self.context.get_node_osdisk_type(),
            min_count=self.context.get_min_count(enable_validation=True),
            max_count=self.context.get_max_count(enable_validation=True),
            enable_auto_scaling=self.context.get_enable_cluster_autoscaler(
                enable_validation=True
            ),
        )
        mc.agent_pool_profiles = [agent_pool_profile]
        return mc

    def set_up_linux_profile(self, mc):
        """Set up linux profile for the ManagedCluster object.

        Linux profile is just used for SSH access to VMs, so it will be omitted if --no-ssh-key option was specified.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        if not self.context.get_no_ssh_key(enable_validation=True):
            ssh_config = self.models.ContainerServiceSshConfiguration(
                public_keys=[
                    self.models.ContainerServiceSshPublicKey(
                        key_data=self.context.get_ssh_key_value(
                            enable_validation=True
                        )
                    )
                ]
            )
            linux_profile = self.models.ContainerServiceLinuxProfile(
                admin_username=self.context.get_admin_username(), ssh=ssh_config
            )
            mc.linux_profile = linux_profile
        return mc

    def set_up_windows_profile(self, mc):
        """Set up windows profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )
        (
            windows_admin_username,
            windows_admin_password,
        ) = self.context.get_windows_admin_username_and_password()
        if windows_admin_username or windows_admin_password:
            windows_license_type = None
            if self.context.get_enable_ahub():
                windows_license_type = "Windows_Server"

            # this would throw an error if windows_admin_username is empty (the user enters an empty
            # string after being prompted), since admin_username is a required parameter
            windows_profile = self.models.ManagedClusterWindowsProfile(
                admin_username=windows_admin_username,
                admin_password=windows_admin_password,
                license_type=windows_license_type,
            )

            mc.windows_profile = windows_profile
            # clean up intermediate after `mc` is decorated
            self.context.remove_intermediate("windows_admin_username")
            self.context.remove_intermediate("windows_admin_password")
        return mc

    def set_up_service_principal_profile(self, mc):
        """Set up service principal profile for the ManagedCluster object.

        The function "_ensure_aks_service_principal" will be called if the user provides an incomplete sp and secret
        pair, which internally used GraphRbacManagementClient to send the request to create sp.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        # If customer explicitly provide a service principal, disable managed identity.
        (
            service_principal,
            client_secret,
        ) = self.context.get_service_principal_and_client_secret()
        enable_managed_identity = self.context.get_enable_managed_identity()
        # Skip create service principal profile for the cluster if the cluster enables managed identity
        # and customer doesn't explicitly provide a service principal.
        if not (
            enable_managed_identity and
            not service_principal and
            not client_secret
        ):
            service_principal_profile = (
                self.models.ManagedClusterServicePrincipalProfile(
                    client_id=service_principal, secret=client_secret
                )
            )
            mc.service_principal_profile = service_principal_profile
            # clean up intermediates after `mc` is decorated
            self.context.remove_intermediate("service_principal")
            self.context.remove_intermediate("client_secret")
        return mc

    def process_add_role_assignment_for_vnet_subnet(self, mc) -> None:
        """Add role assignment for vent subnet.

        The function "subnet_role_assignment_exists" will be called to verfiy if the role assignment already exists for
        the subnet, which internally used AuthorizationManagementClient to send the request.
        The function "_get_user_assigned_identity" will be called to get the client id of the user assigned identity,
        which internally used ManagedServiceIdentityClient to send the request.
        The function "_add_role_assignment" will be called to add role assignment for the subnet, which internally used
        AuthorizationManagementClient to send the request.

        This function will store an intermediate need_post_creation_vnet_permission_granting.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        need_post_creation_vnet_permission_granting = False
        vnet_subnet_id = self.context.get_vnet_subnet_id()
        skip_subnet_role_assignment = (
            self.context.get_skip_subnet_role_assignment()
        )
        if (
            vnet_subnet_id and
            not skip_subnet_role_assignment and
            not subnet_role_assignment_exists(self.cmd, vnet_subnet_id)
        ):
            # if service_principal_profile is None, then this cluster is an MSI cluster,
            # and the service principal does not exist. Two cases:
            # 1. For system assigned identity, we just tell user to grant the
            # permission after the cluster is created to keep consistent with portal experience.
            # 2. For user assigned identity, we can grant needed permission to
            # user provided user assigned identity before creating managed cluster.
            service_principal_profile = mc.service_principal_profile
            assign_identity = self.context.get_assign_identity()
            if service_principal_profile is None and not assign_identity:
                msg = (
                    "It is highly recommended to use USER assigned identity "
                    "(option --assign-identity) when you want to bring your own"
                    "subnet, which will have no latency for the role assignment to "
                    "take effect. When using SYSTEM assigned identity, "
                    "azure-cli will grant Network Contributor role to the "
                    "system assigned identity after the cluster is created, and "
                    "the role assignment will take some time to take effect, see "
                    "https://docs.microsoft.com/en-us/azure/aks/use-managed-identity, "
                    "proceed to create cluster with system assigned identity?"
                )
                if not self.context.get_yes() and not prompt_y_n(
                    msg, default="n"
                ):
                    return None
                need_post_creation_vnet_permission_granting = True
            else:
                scope = vnet_subnet_id
                identity_client_id = ""
                if assign_identity:
                    identity_client_id = (
                        self.context.get_user_assigned_identity_client_id()
                    )
                else:
                    identity_client_id = service_principal_profile.client_id
                if not _add_role_assignment(
                    self.cmd,
                    "Network Contributor",
                    identity_client_id,
                    scope=scope,
                ):
                    logger.warning(
                        "Could not create a role assignment for subnet. "
                        "Are you an Owner on this subscription?"
                    )
        # store need_post_creation_vnet_permission_granting as an intermediate
        self.context.set_intermediate(
            "need_post_creation_vnet_permission_granting",
            need_post_creation_vnet_permission_granting,
            overwrite_exists=True,
        )

    def construct_default_mc(self):
        """The overall control function used to construct the default ManagedCluster object.

        Note: To reduce the risk of regression introduced by refactoring, this function is not complete
        and is being implemented gradually.

        The complete ManagedCluster object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the ManagedCluster object
        """
        # initialize the ManagedCluster object
        mc = self.init_mc()
        # set up agent pool profile(s)
        mc = self.set_up_agent_pool_profiles(mc)
        # set up linux profile (for ssh access)
        mc = self.set_up_linux_profile(mc)
        # set up windows profile
        mc = self.set_up_windows_profile(mc)
        # set up service principal profile
        mc = self.set_up_service_principal_profile(mc)
        # add role assignment for vent subnet
        self.process_add_role_assignment_for_vnet_subnet(mc)

        # TODO: set up other profiles
        return mc

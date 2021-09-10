# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Dict, List, Tuple, TypeVar, Union

from azure.cli.command_modules.acs._consts import (
    ADDONS,
    CONST_ACC_SGX_QUOTE_HELPER_ENABLED,
    CONST_AZURE_POLICY_ADDON_NAME,
    CONST_CONFCOM_ADDON_NAME,
    CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    CONST_INGRESS_APPGW_ADDON_NAME,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME,
    CONST_INGRESS_APPGW_SUBNET_CIDR,
    CONST_INGRESS_APPGW_SUBNET_ID,
    CONST_INGRESS_APPGW_WATCH_NAMESPACE,
    CONST_KUBE_DASHBOARD_ADDON_NAME,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
    CONST_OUTBOUND_TYPE_LOAD_BALANCER,
    CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
    CONST_VIRTUAL_NODE_ADDON_NAME,
    CONST_VIRTUAL_NODE_SUBNET_NAME,
)
from azure.cli.command_modules.acs.custom import (
    _add_role_assignment,
    _ensure_aks_acr,
    _ensure_aks_service_principal,
    _ensure_container_insights_for_monitoring,
    _ensure_default_log_analytics_workspace_for_monitoring,
    _get_default_dns_prefix,
    _get_rg_location,
    _get_user_assigned_identity,
    _set_vm_set_type,
    _validate_ssh_key,
    create_load_balancer_profile,
    get_subscription_id,
    set_load_balancer_sku,
    subnet_role_assignment_exists,
)
from azure.cli.core import AzCommandsLoader
from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import (
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    NoTTYError,
    RequiredArgumentMissingError,
)
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt, prompt_pass, prompt_y_n

logger = get_logger(__name__)

# type variables
ContainerServiceClient = TypeVar("ContainerServiceClient")
ManagedCluster = TypeVar("ManagedCluster")
ManagedClusterLoadBalancerProfile = TypeVar("ManagedClusterLoadBalancerProfile")
ResourceReference = TypeVar("ResourceReference")


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


def safe_lower(obj: Any) -> Any:
    """Return lowercase string if the provided obj is a string, otherwise return the object itself.

    :return: Any
    """
    if isinstance(obj, str):
        return obj.lower()
    return obj


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
        self.ManagedClusterAddonProfile = self.__cmd.get_models(
            "ManagedClusterAddonProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        # not directly used
        self.ManagedClusterAPIServerAccessProfile = self.__cmd.get_models(
            "ManagedClusterAPIServerAccessProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        # init load balancer models
        self.init_lb_models()

    def init_lb_models(self) -> None:
        """Initialize models used by load balancer.

        The models are stored in a dictionary, the key is the model name and the value is the model type.

        :return: None
        """
        lb_models = {}
        lb_models["ManagedClusterLoadBalancerProfile"] = self.__cmd.get_models(
            "ManagedClusterLoadBalancerProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        lb_models[
            "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
        ] = self.__cmd.get_models(
            "ManagedClusterLoadBalancerProfileManagedOutboundIPs",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        lb_models[
            "ManagedClusterLoadBalancerProfileOutboundIPs"
        ] = self.__cmd.get_models(
            "ManagedClusterLoadBalancerProfileOutboundIPs",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        lb_models[
            "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
        ] = self.__cmd.get_models(
            "ManagedClusterLoadBalancerProfileOutboundIPPrefixes",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        lb_models["ResourceReference"] = self.__cmd.get_models(
            "ResourceReference",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.lb_models = lb_models
        # uncomment the followings to add these models as class attributes
        # for model_name, model_type in lb_models.items():
        #     setattr(self, model_name, model_type)


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

    def attach_mc(self, mc: ManagedCluster) -> None:
        """Attach the ManagedCluster object to the context.

        The `mc` object is only allowed to be attached once, and attaching again will raise a CLIInternalError.

        :return: None
        """
        if self.mc is None:
            self.mc = mc
        else:
            msg = "the same" if self.mc == mc else "different"
            raise CLIInternalError(
                "Attempting to attach the `mc` object again, the two objects are {}.".format(
                    msg
                )
            )

    def get_intermediate(self, variable_name: str, default_value: Any = None) -> Any:
        """Get the value of an intermediate by its name.

        Get the value from the intermediates dictionary with variable_name as the key. If variable_name does not exist,
        default_value will be returned.

        :return: Any
        """
        if variable_name not in self.intermediates:
            msg = "The intermediate '{}' does not exist, return default value '{}'.".format(
                variable_name, default_value
            )
            logger.debug(msg)
        return self.intermediates.get(variable_name, default_value)

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

        No exception will be raised if the intermediate does not exist,

        :return: None
        """
        self.intermediates.pop(variable_name, None)

    def get_resource_group_name(self) -> str:
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

    def get_name(self) -> str:
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

    def get_ssh_key_value_and_no_ssh_key(self) -> Tuple[str, bool]:
        """Obtain the value of ssh_key_value and no_ssh_key.

        Note: no_ssh_key will not be decorated into the `mc` object.

        If the user does not explicitly specify --ssh-key-value, the validator function "validate_ssh_key" will check
        the default file location "~/.ssh/id_rsa.pub", if the file exists, read its content and return. Otherise,
        create a key pair at "~/.ssh/id_rsa.pub" and return the public key.
        If the user provides a string-like input for --ssh-key-value, the validator function "validate_ssh_key" will
        check whether it is a file path, if so, read its content and return; if it is a valid public key, return it.
        Otherwise, create a key pair there and return the public key.

        This function will verify the parameters by default. It will call "_validate_ssh_key" to verify the validity of
        ssh_key_value. If parameter no_ssh_key is set to True, verification will be skipped. Otherwise, a CLIError will
        be raised when the value of ssh_key_value is invalid.

        :return: a tuple containing two elements: ssh_key_value of string type and no_ssh_key of bool type
        """
        # ssh_key_value
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
        read_from_mc = False
        if value_obtained_from_mc is not None:
            ssh_key_value = value_obtained_from_mc
            read_from_mc = True
        else:
            ssh_key_value = raw_value

        # no_ssh_key
        # read the original value passed by the command
        no_ssh_key = self.raw_param.get("no_ssh_key")

        # consistent check
        if read_from_mc and no_ssh_key:
            raise CLIInternalError(
                "Inconsistent state detected, ssh_key_value is read from the `mc` object while no_ssh_key is enabled."
            )

        # these parameters do not need dynamic completion

        # validation
        _validate_ssh_key(
            no_ssh_key=no_ssh_key, ssh_key_value=ssh_key_value
        )
        return ssh_key_value, no_ssh_key

    # pylint: disable=unused-argument
    def _get_dns_name_prefix(
        self, enable_validation: bool = False, read_only: bool = False, **kwargs
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of dns_name_prefix according to the context.

        When both dns_name_prefix and fqdn_subdomain are not assigned, dynamic completion will be triggerd. Function
        "_get_default_dns_prefix" will be called to create a default dns_name_prefix composed of name (cluster),
        resource_group_name, and subscription_id.

        This function supports the option of enable_validation. When enabled, it will check if both dns_name_prefix and
        fqdn_subdomain are assigend, if so, raise the MutuallyExclusiveArgumentError.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        dns_name_prefix = self.raw_param.get("dns_name_prefix")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if self.mc and self.mc.dns_prefix:
            dns_name_prefix = self.mc.dns_prefix
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
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

    def get_dns_name_prefix(self) -> Union[str, None]:
        """Dynamically obtain the value of dns_name_prefix according to the context.

        When both dns_name_prefix and fqdn_subdomain are not assigned, dynamic completion will be triggerd. Function
        "_get_default_dns_prefix" will be called to create a default dns_name_prefix composed of name (cluster),
        resource_group_name, and subscription_id.

        This function will verify the parameter by default. It will check if both dns_name_prefix and fqdn_subdomain
        are assigend, if so, raise the MutuallyExclusiveArgumentError.

        :return: string or None
        """

        return self._get_dns_name_prefix(enable_validation=True)

    # pylint: disable=unused-argument
    def _get_location(self, read_only: bool = False, **kwargs) -> Union[str, None]:
        """Internal function to dynamically obtain the value of location according to the context.

        When location is not assigned, dynamic completion will be triggerd. Function "_get_rg_location" will be called
        to get the location of the provided resource group, which internally used ResourceManagementClient to send
        the request.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        location = self.raw_param.get("location")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if self.mc and self.mc.location:
            location = self.mc.location
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return location

        # dynamic completion
        if not read_from_mc and location is None:
            location = _get_rg_location(
                self.cmd.cli_ctx, self.get_resource_group_name()
            )

        # this parameter does not need validation
        return location

    def get_location(self) -> Union[str, None]:
        """Dynamically obtain the value of location according to the context.

        When location is not assigned, dynamic completion will be triggerd. Function "_get_rg_location" will be called
        to get the location of the provided resource group, which internally used ResourceManagementClient to send
        the request.

        :return: string or None
        """

        return self._get_location()

    def get_kubernetes_version(self) -> str:
        """Obtain the value of kubernetes_version.

        :return: string
        """
        # read the original value passed by the command
        kubernetes_version = self.raw_param.get("kubernetes_version")
        # try to read the property value corresponding to the parameter from the `mc` object
        if self.mc and self.mc.kubernetes_version:
            kubernetes_version = self.mc.kubernetes_version

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return kubernetes_version

    # pylint: disable=unused-argument
    def _get_vm_set_type(self, read_only: bool = False, **kwargs) -> Union[str, None]:
        """Internal function to dynamically obtain the value of vm_set_type according to the context.

        Dynamic completion will be triggerd by default. Function "_set_vm_set_type" will be called and the
        corresponding vm set type will be returned according to the value of kubernetes_version. It will also
        normalize the value as server validation is case-sensitive.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        raw_value = self.raw_param.get("vm_set_type")
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
        if read_only:
            return vm_set_type

        # dynamic completion
        # the value verified by the validator may have case problems, and function "_set_vm_set_type" will adjust it
        if not read_from_mc:
            vm_set_type = _set_vm_set_type(
                vm_set_type=vm_set_type,
                kubernetes_version=self.get_kubernetes_version(),
            )

        # this parameter does not need validation
        return vm_set_type

    def get_vm_set_type(self) -> Union[str, None]:
        """Dynamically obtain the value of vm_set_type according to the context.

        Dynamic completion will be triggerd by default. Function "_set_vm_set_type" will be called and the
        corresponding vm set type will be returned according to the value of kubernetes_version. It will also
        normalize the value as server validation is case-sensitive.

        :return: string or None
        """

        # this parameter does not need validation
        return self._get_vm_set_type()

    # pylint: disable=unused-argument
    def _get_load_balancer_sku(
        self, enable_validation: bool = False, read_only: bool = False, **kwargs
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of load_balancer_sku according to the context.

        Note: When returning a string, it will always be lowercase.

        When load_balancer_sku is not assigned, dynamic completion will be triggerd. Function "set_load_balancer_sku"
        will be called and the corresponding load balancer sku will be returned according to the value of
        kubernetes_version.

        This function supports the option of enable_validation. When enabled, it will check if load_balancer_sku equals
        to "basic" when api_server_authorized_ip_ranges is assigned, if so, raise the MutuallyExclusiveArgumentError.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        load_balancer_sku = safe_lower(self.raw_param.get("load_balancer_sku"))
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_sku
        ):
            load_balancer_sku = safe_lower(
                self.mc.network_profile.load_balancer_sku
            )
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return load_balancer_sku

        # dynamic completion
        if not read_from_mc and load_balancer_sku is None:
            load_balancer_sku = safe_lower(
                set_load_balancer_sku(
                    sku=load_balancer_sku,
                    kubernetes_version=self.get_kubernetes_version(),
                )
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

    def get_load_balancer_sku(self) -> Union[str, None]:
        """Dynamically obtain the value of load_balancer_sku according to the context.

        Note: When returning a string, it will always be lowercase.

        When load_balancer_sku is not assigned, dynamic completion will be triggerd. Function "set_load_balancer_sku"
        will be called and the corresponding load balancer sku will be returned according to the value of
        kubernetes_version.

        This function will verify the parameter by default. It will check if load_balancer_sku equals to "basic" when
        api_server_authorized_ip_ranges is assigned, if so, raise the MutuallyExclusiveArgumentError.

        :return: string or None
        """

        return self._get_load_balancer_sku(enable_validation=True)

    def get_api_server_authorized_ip_ranges(self) -> Union[str, List[str], None]:
        """Obtain the value of api_server_authorized_ip_ranges.

        This function will verify the parameter by default. It will check if load_balancer_sku equals to "basic" when
        api_server_authorized_ip_ranges is assigned, if so, raise the MutuallyExclusiveArgumentError.

        :return: string, empty list or list of strings, or None
        """
        # read the original value passed by the command
        api_server_authorized_ip_ranges = self.raw_param.get(
            "api_server_authorized_ip_ranges"
        )
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.api_server_access_profile and
            self.mc.api_server_access_profile.authorized_ip_ranges
        ):
            api_server_authorized_ip_ranges = (
                self.mc.api_server_access_profile.authorized_ip_ranges
            )

        # this parameter does not need dynamic completion

        # validation
        if (
            api_server_authorized_ip_ranges and
            self._get_load_balancer_sku(enable_validation=False) == "basic"
        ):
            raise MutuallyExclusiveArgumentError(
                "--api-server-authorized-ip-ranges can only be used with standard load balancer"
            )
        return api_server_authorized_ip_ranges

    def get_fqdn_subdomain(self) -> Union[str, None]:
        """Obtain the value of fqdn_subdomain.

        This function will verify the parameter by default. It will check if both dns_name_prefix and fqdn_subdomain
        are assigend, if so, raise the MutuallyExclusiveArgumentError.

        :return: string or None
        """
        # read the original value passed by the command
        fqdn_subdomain = self.raw_param.get("fqdn_subdomain")
        # try to read the property value corresponding to the parameter from the `mc` object
        if self.mc and self.mc.fqdn_subdomain:
            fqdn_subdomain = self.mc.fqdn_subdomain

        # this parameter does not need dynamic completion

        # validation
        if fqdn_subdomain and self._get_dns_name_prefix(read_only=True):
            raise MutuallyExclusiveArgumentError(
                "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
            )
        return fqdn_subdomain

    def get_nodepool_name(self) -> str:
        """Dynamically obtain the value of nodepool_name according to the context.

        Note: SDK performs the following validation {'required': True, 'pattern': r'^[a-z][a-z0-9]{0,11}$'}.

        This function will normalize the parameter by default. If no value is assigned, the default value "nodepool1"
        is set, and if the string length is greater than 12, it is truncated.

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
        if value_obtained_from_mc is not None:
            nodepool_name = value_obtained_from_mc
        else:
            nodepool_name = raw_value
            # normalize
            if not nodepool_name:
                nodepool_name = "nodepool1"
            else:
                nodepool_name = nodepool_name[:12]

        # this parameter does not need validation
        return nodepool_name

    def get_nodepool_tags(self) -> Union[Dict[str, str], None]:
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

    def get_nodepool_labels(self) -> Union[Dict[str, str], None]:
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

    def get_node_vm_size(self) -> str:
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

    def get_vnet_subnet_id(self) -> Union[str, None]:
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

    def get_ppg(self) -> Union[str, None]:
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

    def get_zones(self) -> Union[List[str], None]:
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

    def get_enable_node_public_ip(self) -> bool:
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

    def get_node_public_ip_prefix_id(self) -> Union[str, None]:
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

    def get_enable_encryption_at_host(self) -> bool:
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

    def get_enable_ultra_ssd(self) -> bool:
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

    def get_max_pods(self) -> Union[int, None]:
        """Obtain the value of max_pods.

        This function will normalize the parameter by default. The parameter will be converted to int, but int 0 is
        converted to None.

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

    def get_node_osdisk_size(self) -> Union[int, None]:
        """Obtain the value of node_osdisk_size.

        Note: SDK performs the following validation {'maximum': 2048, 'minimum': 0}.

        This function will normalize the parameter by default. The parameter will be converted to int, but int 0 is
        converted to None.

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

        # this parameter does not need validation
        return node_osdisk_size

    def get_node_osdisk_type(self) -> Union[str, None]:
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

    # pylint: disable=too-many-branches
    def get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count(
        self,
    ) -> Tuple[int, bool, Union[int, None], Union[int, None]]:
        """Obtain the value of node_count, enable_cluster_autoscaler, min_count and max_count.

        This function will verify the parameter by default. On the premise that enable_cluster_autoscaler is enabled,
        it will check whether both min_count and max_count are assigned, if not, raise the RequiredArgumentMissingError;
        if will also check whether min_count is less than max_count and node_count is between min_count and max_count,
        if not, raise the InvalidArgumentValueError. If enable_cluster_autoscaler is not enabled, it will check whether
        any of min_count or max_count is assigned, if so, raise the RequiredArgumentMissingError.

        :return: a tuple containing four elements: node_count of int type, enable_cluster_autoscaler of bool type,
        min_count of int type or None and max_count of int type or None
        """
        # node_count
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

        # enable_cluster_autoscaler
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

        # min_count
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

        # max_count
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

        # these parameters do not need dynamic completion

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
            if node_count < min_count or node_count > max_count:
                raise InvalidArgumentValueError(
                    "node-count is not in the range of min-count and max-count"
                )
        else:
            if min_count is not None or max_count is not None:
                raise RequiredArgumentMissingError(
                    "min-count and max-count are required for --enable-cluster-autoscaler, please use the flag"
                )
        return node_count, enable_cluster_autoscaler, min_count, max_count

    def get_admin_username(self) -> str:
        """Obtain the value of admin_username.

        Note: SDK performs the following validation {'required': True, 'pattern': r'^[A-Za-z][-A-Za-z0-9_]*$'}.

        :return: str
        """
        # read the original value passed by the command
        admin_username = self.raw_param.get("admin_username")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.linux_profile and
            self.mc.linux_profile.admin_username
        ):
            admin_username = self.mc.linux_profile.admin_username

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return admin_username

    # pylint: disable=unused-argument
    def _get_windows_admin_username_and_password(
        self, read_only: bool = False, **kwargs
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Internal function to dynamically obtain the value of windows_admin_username and windows_admin_password
        according to the context.

        When ont of windows_admin_username and windows_admin_password is not assigned, dynamic completion will be
        triggerd. The user will be prompted to enter the missing windows_admin_username or windows_admin_password in
        tty (pseudo terminal). If the program is running in a non-interactive environment, a NoTTYError error will be
        raised.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: a tuple containing two elements: windows_admin_username of string type or None and
        windows_admin_password of string type or None
        """
        # windows_admin_username
        # read the original value passed by the command
        windows_admin_username = self.raw_param.get("windows_admin_username")
        # try to read the property value corresponding to the parameter from the `mc` object
        username_read_from_mc = False
        if (
            self.mc and
            self.mc.windows_profile and
            self.mc.windows_profile.admin_username
        ):
            windows_admin_username = self.mc.windows_profile.admin_username
            username_read_from_mc = True

        # windows_admin_password
        # read the original value passed by the command
        windows_admin_password = self.raw_param.get("windows_admin_password")
        # try to read the property value corresponding to the parameter from the `mc` object
        password_read_from_mc = False
        if (
            self.mc and
            self.mc.windows_profile and
            self.mc.windows_profile.admin_password
        ):
            windows_admin_password = self.mc.windows_profile.admin_password
            password_read_from_mc = True

        # consistent check
        if username_read_from_mc != password_read_from_mc:
            raise CLIInternalError(
                "Inconsistent state detected, one of windows admin name and password is read from the `mc` object."
            )

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
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

    def get_windows_admin_username_and_password(
        self,
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Dynamically obtain the value of windows_admin_username and windows_admin_password according to the context.

        When ont of windows_admin_username and windows_admin_password is not assigned, dynamic completion will be
        triggerd. The user will be prompted to enter the missing windows_admin_username or windows_admin_password in
        tty (pseudo terminal). If the program is running in a non-interactive environment, a NoTTYError error will be
        raised.

        :return: a tuple containing two elements: windows_admin_username of string type or None and
        windows_admin_password of string type or None
        """

        return self._get_windows_admin_username_and_password()

    def get_enable_ahub(self) -> bool:
        """Obtain the value of enable_ahub.

        Note: enable_ahub will not be directly decorated into the `mc` object.

        :return: bool
        """
        # read the original value passed by the command
        enable_ahub = self.raw_param.get("enable_ahub")
        # try to read the property value corresponding to the parameter from the `mc` object
        if self.mc and self.mc.windows_profile:
            enable_ahub = self.mc.windows_profile.license_type == "Windows_Server"

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_ahub

    # pylint: disable=unused-argument,too-many-statements
    def _get_service_principal_and_client_secret(
        self, read_only: bool = False, **kwargs
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Internal function to dynamically obtain the values of service_principal and client_secret according to the
        context.

        When service_principal and client_secret are not assigned and enable_managed_identity is True, dynamic
        completion will not be triggered. For other cases, dynamic completion will be triggered.
        When client_secret is given but service_principal is not, dns_name_prefix or fqdn_subdomain will be used to
        create a service principal. The parameters subscription_id, location and name (cluster) are also required when
        calling function "_ensure_aks_service_principal", which internally used GraphRbacManagementClient to send
        the request.
        When service_principal is given but client_secret is not, function "_ensure_aks_service_principal" would raise
        CLIError.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: a tuple containing two elements: service_principal of string type or None and client_secret of
        string type or None
        """
        # service_principal
        # read the original value passed by the command
        service_principal = self.raw_param.get("service_principal")
        # try to read the property value corresponding to the parameter from the `mc` object
        sp_read_from_mc = False
        if (
            self.mc and
            self.mc.service_principal_profile and
            self.mc.service_principal_profile.client_id
        ):
            service_principal = self.mc.service_principal_profile.client_id
            sp_read_from_mc = True

        # client_secret
        # read the original value passed by the command
        client_secret = self.raw_param.get("client_secret")
        # try to read the property value corresponding to the parameter from the `mc` object
        secret_read_from_mc = False
        if (
            self.mc and
            self.mc.service_principal_profile and
            self.mc.service_principal_profile.secret
        ):
            client_secret = self.mc.service_principal_profile.secret
            secret_read_from_mc = True

        # consistent check
        if sp_read_from_mc != secret_read_from_mc:
            raise CLIInternalError(
                "Inconsistent state detected, one of sp and secret is read from the `mc` object."
            )

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return service_principal, client_secret

        # dynamic completion for service_principal and client_secret
        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        enable_managed_identity = self._get_enable_managed_identity(read_only=True)
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
                dns_name_prefix=self._get_dns_name_prefix(enable_validation=False),
                fqdn_subdomain=self.get_fqdn_subdomain(),
                location=self.get_location(),
                name=self.get_name(),
            )
            service_principal = principal_obj.get("service_principal")
            client_secret = principal_obj.get("client_secret")

        # these parameters do not need validation
        return service_principal, client_secret

    def get_service_principal_and_client_secret(
        self
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

        :return: a tuple containing two elements: service_principal of string type or None and client_secret of
        string type or None
        """

        return self._get_service_principal_and_client_secret()

    # pylint: disable=unused-argument
    def _get_enable_managed_identity(
        self, enable_validation: bool = False, read_only: bool = False, **kwargs
    ) -> bool:
        """Internal function to dynamically obtain the values of service_principal and client_secret according to the
        context.

        Note: enable_managed_identity will not be directly decorated into the `mc` object.

        When both service_principal and client_secret are assigned and enable_managed_identity is True, dynamic
        completion will be triggered. The value of enable_managed_identity will be set to False.

        This function supports the option of enable_validation. When enabled, it will ...
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: bool
        """
        # read the original value passed by the command
        enable_managed_identity = self.raw_param.get("enable_managed_identity")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if self.mc and self.mc.identity:
            enable_managed_identity = self.mc.identity.type is not None
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return enable_managed_identity

        # dynamic completion
        (
            service_principal,
            client_secret,
        ) = self._get_service_principal_and_client_secret(read_only=True)
        if not read_from_mc and service_principal and client_secret:
            enable_managed_identity = False

        # validation
        if enable_validation:
            # TODO: add validation
            pass
        return enable_managed_identity

    def get_enable_managed_identity(self) -> bool:
        """Dynamically obtain the values of service_principal and client_secret according to the context.

        Note: enable_managed_identity will not be directly decorated into the `mc` object.

        When both service_principal and client_secret are assigned and enable_managed_identity is True, dynamic
        completion will be triggered. The value of enable_managed_identity will be set to False.

        :return: bool
        """

        return self._get_enable_managed_identity(enable_validation=True)

    def get_skip_subnet_role_assignment(self) -> bool:
        """Obtain the value of skip_subnet_role_assignment.

        Note: skip_subnet_role_assignment will not be decorated into the `mc` object.

        :return: bool
        """
        # read the original value passed by the command
        skip_subnet_role_assignment = self.raw_param.get("skip_subnet_role_assignment")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return skip_subnet_role_assignment

    def get_assign_identity(self) -> Union[str, None]:
        """Obtain the value of assign_identity.

        Note: assign_identity will not be decorated into the `mc` object.

        :return: string or None
        """
        # read the original value passed by the command
        assign_identity = self.raw_param.get("assign_identity")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return assign_identity

    def get_user_assigned_identity_client_id(self) -> str:
        """Obtain the client_id of user assigned identity.

        Note: This is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the client_id field in the
        returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = self.get_assign_identity()
        if assigned_identity is None or assigned_identity == "":
            raise RequiredArgumentMissingError("No assigned identity provided.")
        return _get_user_assigned_identity(self.cmd.cli_ctx, assigned_identity).client_id

    def get_user_assigned_identity_object_id(self) -> str:
        """Obtain the principal_id of user assigned identity.

        Note: This is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the principal_id field in
        the returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = self.get_assign_identity()
        if assigned_identity is None or assigned_identity == "":
            raise RequiredArgumentMissingError("No assigned identity provided.")
        return _get_user_assigned_identity(self.cmd.cli_ctx, assigned_identity).principal_id

    def get_yes(self) -> bool:
        """Obtain the value of yes.

        Note: yes will not be decorated into the `mc` object.

        :return: bool
        """
        # read the original value passed by the command
        yes = self.raw_param.get("yes")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return yes

    def get_attach_acr(self) -> Union[str, None]:
        """Obtain the value of attach_acr.

        Note: attach_acr will not be decorated into the `mc` object.

        :return: string
        """
        # read the original value passed by the command
        attach_acr = self.raw_param.get("attach_acr")

        # this parameter does not need dynamic completion
        # validation
        if attach_acr:
            if self.get_enable_managed_identity() and self.get_no_wait():
                raise MutuallyExclusiveArgumentError(
                    "When --attach-acr and --enable-managed-identity are both specified, "
                    "--no-wait is not allowed, please wait until the whole operation succeeds."
                )
                # Attach acr operation will be handled after the cluster is created
            # newly added check, check whether client_id exists before creating role assignment
            service_principal, _ = self._get_service_principal_and_client_secret(read_only=True)
            if not service_principal:
                raise CLIInternalError(
                    "No service principal provided to create the acrpull role assignment for acr."
                )
        return attach_acr

    def get_no_wait(self) -> bool:
        """Obtain the value of no_wait.

        Note: no_wait will not be decorated into the `mc` object.

        :return: bool
        """
        # read the original value passed by the command
        no_wait = self.raw_param.get("no_wait")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return no_wait

    def get_load_balancer_managed_outbound_ip_count(self) -> Union[int, None]:
        """Obtain the value of load_balancer_managed_outbound_ip_count.

        Note: SDK performs the following validation {'maximum': 100, 'minimum': 1}.

        :return: int or None
        """
        # read the original value passed by the command
        load_balancer_managed_outbound_ip_count = self.raw_param.get(
            "load_balancer_managed_outbound_ip_count"
        )
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_profile and
            self.mc.network_profile.load_balancer_profile.managed_outbound_i_ps and
            self.mc.network_profile.load_balancer_profile.managed_outbound_i_ps.count
        ):
            load_balancer_managed_outbound_ip_count = (
                self.mc.network_profile.load_balancer_profile.managed_outbound_i_ps.count
            )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return load_balancer_managed_outbound_ip_count

    def get_load_balancer_outbound_ips(self) -> Union[str, List[ResourceReference], None]:
        """Obtain the value of load_balancer_outbound_ips.

        Note: SDK performs the following validation {'maximum': 16, 'minimum': 1}.

        :return: string, list of ResourceReference, or None
        """
        # read the original value passed by the command
        load_balancer_outbound_ips = self.raw_param.get(
            "load_balancer_outbound_ips"
        )
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_profile and
            self.mc.network_profile.load_balancer_profile.outbound_i_ps and
            self.mc.network_profile.load_balancer_profile.outbound_i_ps.public_i_ps
        ):
            load_balancer_outbound_ips = (
                self.mc.network_profile.load_balancer_profile.outbound_i_ps.public_i_ps
            )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return load_balancer_outbound_ips

    def get_load_balancer_outbound_ip_prefixes(self) -> Union[str, List[ResourceReference], None]:
        """Obtain the value of load_balancer_outbound_ip_prefixes.

        :return: string, list of ResourceReference, or None
        """
        # read the original value passed by the command
        load_balancer_outbound_ip_prefixes = self.raw_param.get(
            "load_balancer_outbound_ip_prefixes"
        )
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_profile and
            self.mc.network_profile.load_balancer_profile.outbound_ip_prefixes and
            self.mc.network_profile.load_balancer_profile.outbound_ip_prefixes.public_ip_prefixes
        ):
            load_balancer_outbound_ip_prefixes = (
                self.mc.network_profile.load_balancer_profile.outbound_ip_prefixes.public_ip_prefixes
            )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return load_balancer_outbound_ip_prefixes

    def get_load_balancer_outbound_ports(self) -> Union[int, None]:
        """Obtain the value of load_balancer_outbound_ports.

        Note: SDK performs the following validation {'maximum': 64000, 'minimum': 0}.

        :return: int or None
        """
        # read the original value passed by the command
        load_balancer_outbound_ports = self.raw_param.get(
            "load_balancer_outbound_ports"
        )
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_profile and
            self.mc.network_profile.load_balancer_profile.allocated_outbound_ports
        ):
            load_balancer_outbound_ports = (
                self.mc.network_profile.load_balancer_profile.allocated_outbound_ports
            )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return load_balancer_outbound_ports

    def get_load_balancer_idle_timeout(self) -> Union[int, None]:
        """Obtain the value of load_balancer_idle_timeout.

        Note: SDK performs the following validation {'maximum': 120, 'minimum': 4}.

        :return: int or None
        """
        # read the original value passed by the command
        load_balancer_idle_timeout = self.raw_param.get(
            "load_balancer_idle_timeout"
        )
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_profile and
            self.mc.network_profile.load_balancer_profile.idle_timeout_in_minutes
        ):
            load_balancer_idle_timeout = (
                self.mc.network_profile.load_balancer_profile.idle_timeout_in_minutes
            )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return load_balancer_idle_timeout

    # pylint: disable=unused-argument
    def _get_outbound_type(
        self,
        enable_validation: bool = False,
        read_only: bool = False,
        load_balancer_profile: ManagedClusterLoadBalancerProfile = None,
        **kwargs
    ) -> Union[str, None]:
        """Internal functin to dynamically obtain the value of outbound_type according to the context.

        Note: All the external parameters involved in the validation are not verified in their own getters.

        When outbound_type is not assigned, dynamic completion will be triggerd. By default, the value is set to
        CONST_OUTBOUND_TYPE_LOAD_BALANCER.

        This function supports the option of enable_validation. When enabled, if the value of outbound_type is
        userDefinedRouting (CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING), the following checks will be performed. If
        load_balancer_sku is set to basic, an InvalidArgumentValueError will be raised. If vnet_subnet_id is not
        assigned, a RequiredArgumentMissingError will be raised. If any of load_balancer_managed_outbound_ip_count,
        load_balancer_outbound_ips or load_balancer_outbound_ip_prefixes is assigned, a MutuallyExclusiveArgumentError
        will be raised.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.
        This function supports the option of load_balancer_profile, if provided, when verifying loadbalancer-related
        parameters, the value in load_balancer_profile will be used for validation.

        :return: string or None
        """
        # read the original value passed by the command
        outbound_type = self.raw_param.get("outbound_type")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.outbound_type
        ):
            outbound_type = (self.mc.network_profile.outbound_type)
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return outbound_type

        # dynamic completion
        if not read_from_mc and outbound_type != CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING:
            outbound_type = CONST_OUTBOUND_TYPE_LOAD_BALANCER

        # validation
        # Note: The parameters involved in the validation are not verified in their own getters.
        if enable_validation:
            if outbound_type == CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING:
                # Should not enable read_only for get_load_balancer_sku, since its default value is None, and it has
                # not been decorated into the mc object at this time, only the value after dynamic completion is
                # meaningful here.
                if self._get_load_balancer_sku(enable_validation=False) == "basic":
                    raise InvalidArgumentValueError(
                        "userDefinedRouting doesn't support basic load balancer sku"
                    )

                if self.get_vnet_subnet_id() in ["", None]:
                    raise RequiredArgumentMissingError(
                        "--vnet-subnet-id must be specified for userDefinedRouting and it must "
                        "be pre-configured with a route table with egress rules"
                    )

                if load_balancer_profile:
                    if (
                        load_balancer_profile.managed_outbound_i_ps or
                        load_balancer_profile.outbound_i_ps or
                        load_balancer_profile.outbound_ip_prefixes
                    ):
                        raise MutuallyExclusiveArgumentError(
                            "userDefinedRouting doesn't support customizing a standard load balancer with IP addresses"
                        )
                else:
                    if (
                        self.get_load_balancer_managed_outbound_ip_count() or
                        self.get_load_balancer_outbound_ips() or
                        self.get_load_balancer_outbound_ip_prefixes()
                    ):
                        raise MutuallyExclusiveArgumentError(
                            "userDefinedRouting doesn't support customizing a standard load balancer with IP addresses"
                        )

        return outbound_type

    def get_outbound_type(
        self,
        load_balancer_profile: ManagedClusterLoadBalancerProfile = None
    ) -> Union[str, None]:
        """Dynamically obtain the value of outbound_type according to the context.

        Note: The parameters involved in the validation are not verified in their own getters.

        When outbound_type is not assigned, dynamic completion will be triggerd. By default, the value is set to
        CONST_OUTBOUND_TYPE_LOAD_BALANCER.

        This function supports the option of load_balancer_profile, if provided, when verifying loadbalancer-related
        parameters, the value in load_balancer_profile will be used for validation.

        :return: string or None
        """

        return self._get_outbound_type(
            enable_validation=True, load_balancer_profile=load_balancer_profile
        )

    # pylint: disable=unused-argument
    def _get_network_plugin(self, enable_validation: bool = False, **kwargs) -> Union[str, None]:
        """Internal function to Obtain the value of network_plugin.

        Note: SDK provides default value "kubenet" for network_plugin.

        This function supports the option of enable_validation. When enabled, in case network_plugin is assigned, if
        pod_cidr is assigned and the value of network_plugin is azure, a MutuallyExclusiveArgumentError will be
        raised; otherwise, if any of pod_cidr, service_cidr, dns_service_ip, docker_bridge_address or network_policy
        is assigned, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """
        # read the original value passed by the command
        network_plugin = self.raw_param.get("network_plugin")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.network_plugin
        ):
            network_plugin = self.mc.network_profile.network_plugin

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            (
                pod_cidr,
                service_cidr,
                dns_service_ip,
                docker_bridge_address,
                network_policy,
            ) = (
                self.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()
            )
            if network_plugin:
                if network_plugin == "azure" and pod_cidr:
                    raise MutuallyExclusiveArgumentError(
                        "Please use kubenet as the network plugin type when pod_cidr is specified"
                    )
            else:
                if (
                    pod_cidr or
                    service_cidr or
                    dns_service_ip or
                    docker_bridge_address or
                    network_policy
                ):
                    raise RequiredArgumentMissingError(
                        "Please explicitly specify the network plugin type"
                    )
        return network_plugin

    def get_network_plugin(self) -> Union[str, None]:
        """Obtain the value of network_plugin.

        Note: SDK provides default value "kubenet" for network_plugin.

        This function will verify the parameter by default. When enabled, in case network_plugin is assigned, if
        pod_cidr is assigned and the value of network_plugin is azure, a MutuallyExclusiveArgumentError will be
        raised; otherwise, if any of pod_cidr, service_cidr, dns_service_ip, docker_bridge_address or network_policy
        is assigned, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """

        return self._get_network_plugin(enable_validation=True)

    def get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
        self,
    ) -> Tuple[
        Union[str, None],
        Union[str, None],
        Union[str, None],
        Union[str, None],
        Union[str, None],
    ]:
        """Obtain the value of pod_cidr, service_cidr, dns_service_ip, docker_bridge_address and network_policy.

        Note: SDK provides default value "10.244.0.0/16" and performs the following validation
        {'pattern': r'^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$'} for pod_cidr.
        Note: SDK provides default value "10.0.0.0/16" and performs the following validation
        {'pattern': r'^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$'} for service_cidr.
        Note: SDK provides default value "10.0.0.10" and performs the following validation
        {'pattern': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'}
        for dns_service_ip.
        Note: SDK provides default value "172.17.0.1/16" and performs the following validation
        {'pattern': r'^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$'} for docker_bridge_address.

        This function will verify the parameters by default. If pod_cidr is assigned and the value of network_plugin
        is azure, a MutuallyExclusiveArgumentError will be raised; otherwise, if any of pod_cidr, service_cidr,
        dns_service_ip, docker_bridge_address or network_policy is assigned, a RequiredArgumentMissingError will be
        raised.

        :return: a tuple of five elements: pod_cidr of string type or None, service_cidr of string type or None,
        dns_service_ip of string type or None, docker_bridge_address of string type or None, network_policy of
        string type or None.
        """
        # pod_cidr
        # read the original value passed by the command
        pod_cidr = self.raw_param.get("pod_cidr")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.pod_cidr
        ):
            pod_cidr = self.mc.network_profile.pod_cidr

        # service_cidr
        # read the original value passed by the command
        service_cidr = self.raw_param.get("service_cidr")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.service_cidr
        ):
            service_cidr = self.mc.network_profile.service_cidr

        # dns_service_ip
        # read the original value passed by the command
        dns_service_ip = self.raw_param.get("dns_service_ip")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.dns_service_ip
        ):
            dns_service_ip = self.mc.network_profile.dns_service_ip

        # docker_bridge_address
        # read the original value passed by the command
        docker_bridge_address = self.raw_param.get("docker_bridge_address")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.docker_bridge_cidr
        ):
            docker_bridge_address = self.mc.network_profile.docker_bridge_cidr

        # network_policy
        # read the original value passed by the command
        network_policy = self.raw_param.get("network_policy")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.network_policy
        ):
            network_policy = self.mc.network_profile.network_policy

        # these parameters do not need dynamic completion

        # validation
        network_plugin = self._get_network_plugin(enable_validation=False)
        if network_plugin:
            if network_plugin == "azure" and pod_cidr:
                raise MutuallyExclusiveArgumentError(
                    "Please use kubenet as the network plugin type when pod_cidr is specified"
                )
        else:
            if (
                pod_cidr or
                service_cidr or
                dns_service_ip or
                docker_bridge_address or
                network_policy
            ):
                raise RequiredArgumentMissingError(
                    "Please explicitly specify the network plugin type"
                )
        return pod_cidr, service_cidr, dns_service_ip, docker_bridge_address, network_policy

    def get_enable_addons(self) -> List[str]:
        """Obtain the value of enable_addons.

        Note: enable_addons will not be decorated into the `mc` object.
        Note: Some of the external parameters involved in the validation are not verified in their own getters.

        This function will verify the parameters by default. It will check whether the provided addons have duplicate or
        invalid values, and raise a InvalidArgumentValueError if found.
        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.

        :return: empty list or list of strings
        """
        # read the original value passed by the command
        enable_addons = self.raw_param.get("enable_addons")

        # normalize
        enable_addons = enable_addons.split(',') if enable_addons else []

        # validation
        # check duplicate addons
        duplicate_addons_set = {
            x for x in enable_addons if enable_addons.count(x) >= 2
        }
        if len(duplicate_addons_set) != 0:
            raise InvalidArgumentValueError(
                "Duplicate addon{} '{}' found in option --enable-addons.".format(
                    "s" if len(duplicate_addons_set) > 1 else "",
                    ",".join(duplicate_addons_set),
                )
            )

        # check unrecognized addons
        enable_addons_set = set(enable_addons)
        invalid_addons_set = enable_addons_set.difference(ADDONS.keys())
        if len(invalid_addons_set) != 0:
            raise InvalidArgumentValueError(
                "'{}' {} not recognized by the --enable-addons argument.".format(
                    ",".join(invalid_addons_set),
                    "are" if len(invalid_addons_set) > 1 else "is",
                )
            )

        # check monitoring/workspace_resource_id
        workspace_resource_id = self._get_workspace_resource_id(read_only=True)
        if "monitoring" not in enable_addons and workspace_resource_id:
            raise RequiredArgumentMissingError(
                '"--workspace-resource-id" requires "--enable-addons monitoring".')

        # check virtual node/aci_subnet_name/vnet_subnet_id
        # Note: The external parameters involved in the validation are not verified in their own getters.
        aci_subnet_name = self.get_aci_subnet_name()
        vnet_subnet_id = self.get_vnet_subnet_id()
        if "virtual-node" in enable_addons and not (aci_subnet_name and vnet_subnet_id):
            raise RequiredArgumentMissingError(
                '"--enable-addons virtual-node" requires "--aci-subnet-name" and "--vnet-subnet-id".')
        return enable_addons

    # pylint: disable=unused-argument
    def _get_workspace_resource_id(
        self, enable_validation: bool = False, read_only: bool = False, **kwargs
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of workspace_resource_id according to the context.

        When both workspace_resource_id is not assigned, dynamic completion will be triggerd. Function
        "_ensure_default_log_analytics_workspace_for_monitoring" will be called to create a workspace with
        subscription_id and resource_group_name.

        This function supports the option of enable_validation. When enabled, it will check if workspace_resource_id is
        assigned but 'monitoring' is not specified in enable_addons, if so, raise a RequiredArgumentMissingError.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        workspace_resource_id = self.raw_param.get("workspace_resource_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_MONITORING_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_MONITORING_ADDON_NAME
            ).config.get(CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID)
        ):
            workspace_resource_id = self.mc.addon_profiles.get(
                CONST_MONITORING_ADDON_NAME
            ).config.get(CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID)
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return workspace_resource_id

        # dynamic completion
        if not read_from_mc:
            if workspace_resource_id is None:
                # use default workspace if exists else create default workspace
                workspace_resource_id = (
                    _ensure_default_log_analytics_workspace_for_monitoring(
                        self.cmd,
                        self.intermediates.get("subscription_id", None),
                        self.get_resource_group_name(),
                    )
                )
            # normalize
            workspace_resource_id = "/" + workspace_resource_id.strip(" /")

        # validation
        if enable_validation:
            enable_addons = self.get_enable_addons()
            if workspace_resource_id and "monitoring" not in enable_addons:
                raise RequiredArgumentMissingError(
                    '"--workspace-resource-id" requires "--enable-addons monitoring".')

        # this parameter does not need validation
        return workspace_resource_id

    def get_workspace_resource_id(self) -> Union[str, None]:
        """Dynamically obtain the value of workspace_resource_id according to the context.

        When both workspace_resource_id is not assigned, dynamic completion will be triggerd. Function
        "_ensure_default_log_analytics_workspace_for_monitoring" will be called to create a workspace with
        subscription_id and resource_group_name.

        :return: string or None
        """

        return self._get_workspace_resource_id(enable_validation=True)

    # pylint: disable=no-self-use
    def get_virtual_node_addon_os_type(self) -> str:
        """Obtain the os_type of virtual node addon.

        Note: This is not a parameter of aks_create.

        :return: string
        """
        return "Linux"

    def get_aci_subnet_name(self) -> Union[str, None]:
        """Obtain the value of aci_subnet_name.

        :return: string or None
        """
        # read the original value passed by the command
        aci_subnet_name = self.raw_param.get("aci_subnet_name")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_VIRTUAL_NODE_ADDON_NAME +
            self.get_virtual_node_addon_os_type()
            in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_VIRTUAL_NODE_ADDON_NAME +
                self.get_virtual_node_addon_os_type()
            ).config.get(CONST_VIRTUAL_NODE_SUBNET_NAME)
        ):
            aci_subnet_name = self.mc.addon_profiles.get(
                CONST_VIRTUAL_NODE_ADDON_NAME +
                self.get_virtual_node_addon_os_type()
            ).config.get(CONST_VIRTUAL_NODE_SUBNET_NAME)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return aci_subnet_name

    def get_appgw_name(self) -> Union[str, None]:
        """Obtain the value of appgw_name.

        :return: string or None
        """
        # read the original value passed by the command
        appgw_name = self.raw_param.get("appgw_name")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME)
        ):
            appgw_name = self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return appgw_name

    def get_appgw_subnet_cidr(self) -> Union[str, None]:
        """Obtain the value of appgw_subnet_cidr.

        :return: string or None
        """
        # read the original value passed by the command
        appgw_subnet_cidr = self.raw_param.get("appgw_subnet_cidr")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_SUBNET_CIDR)
        ):
            appgw_subnet_cidr = self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_SUBNET_CIDR)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return appgw_subnet_cidr

    def get_appgw_id(self) -> Union[str, None]:
        """Obtain the value of appgw_id.

        :return: string or None
        """
        # read the original value passed by the command
        appgw_id = self.raw_param.get("appgw_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID)
        ):
            appgw_id = self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return appgw_id

    def get_appgw_subnet_id(self) -> Union[str, None]:
        """Obtain the value of appgw_subnet_id.

        :return: string or None
        """
        # read the original value passed by the command
        appgw_subnet_id = self.raw_param.get("appgw_subnet_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_SUBNET_ID)
        ):
            appgw_subnet_id = self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_SUBNET_ID)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return appgw_subnet_id

    def get_appgw_watch_namespace(self) -> Union[str, None]:
        """Obtain the value of appgw_watch_namespace.

        :return: string or None
        """
        # read the original value passed by the command
        appgw_watch_namespace = self.raw_param.get("appgw_watch_namespace")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_WATCH_NAMESPACE)
        ):
            appgw_watch_namespace = self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_WATCH_NAMESPACE)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return appgw_watch_namespace

    def get_enable_sgxquotehelper(self) -> bool:
        """Obtain the value of enable_sgxquotehelper.

        :return: bool
        """
        # read the original value passed by the command
        enable_sgxquotehelper = self.raw_param.get("enable_sgxquotehelper")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_CONFCOM_ADDON_NAME in self.mc.addon_profiles and
            CONST_ACC_SGX_QUOTE_HELPER_ENABLED in
            self.mc.addon_profiles.get(CONST_CONFCOM_ADDON_NAME).config
        ):
            enable_sgxquotehelper = self.mc.addon_profiles.get(
                CONST_CONFCOM_ADDON_NAME
            ).config.get(CONST_ACC_SGX_QUOTE_HELPER_ENABLED)

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_sgxquotehelper

    # pylint: disable=unused-argument
    def _get_enable_aad(self, enable_validation: bool = False, **kwargs) -> bool:
        """Internal function to obtain the value of enable_aad.

        This function supports the option of enable_validation. When enabled, if the value of enable_aad is True and
        any of aad_client_app_id, aad_server_app_id or aad_server_app_secret is asssigned, a
        MutuallyExclusiveArgumentError will be raised. If the value of enable_aad is False and the value of
        enable_azure_rbac is True, a RequiredArgumentMissingError will be raised.

        :return: bool
        """
        # read the original value passed by the command
        enable_aad = self.raw_param.get("enable_aad")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.aad_profile
        ):
            enable_aad = True if self.mc.aad_profile.managed else False

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            (
                aad_client_app_id,
                aad_server_app_id,
                aad_server_app_secret,
            ) = (
                self.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret()
            )
            if enable_aad:
                if any(
                    [
                        aad_client_app_id,
                        aad_server_app_id,
                        aad_server_app_secret,
                    ]
                ):
                    raise MutuallyExclusiveArgumentError(
                        "--enable-aad cannot be used together with --aad-client-app-id, --aad-server-app-id or "
                        "--aad-server-app-secret"
                    )
            if not enable_aad and self._get_enable_azure_rbac(enable_validation=False):
                raise RequiredArgumentMissingError(
                    "--enable-azure-rbac can only be used together with --enable-aad"
                )
        return enable_aad

    def get_enable_aad(self) -> bool:
        """Obtain the value of enable_aad.

        This function will verify the parameter by default. If the value of enable_aad is True and any of
        aad_client_app_id, aad_server_app_id or aad_server_app_secret is asssigned, a MutuallyExclusiveArgumentError
        will be raised. If the value of enable_aad is False and the value of enable_azure_rbac is True,
        a RequiredArgumentMissingError will be raised.

        :return: bool
        """

        return self._get_enable_aad(enable_validation=True)

    def get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(
        self,
    ) -> Tuple[Union[str, None], Union[str, None], Union[str, None]]:
        """Obtain the value of aad_client_app_id, aad_server_app_id and aad_server_app_secret.

        This function will verify the parameters by default. If the value of enable_aad is True and any of
        aad_client_app_id, aad_server_app_id or aad_server_app_secret is asssigned, a MutuallyExclusiveArgumentError
        will be raised.

        :return: a tuple of three elements: aad_client_app_id of string type or None, aad_server_app_id of string type
        or None and aad_server_app_secret of string type or None.
        """
        # read the original value passed by the command
        aad_client_app_id = self.raw_param.get("aad_client_app_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.aad_profile and
            self.mc.aad_profile.client_app_id
        ):
            aad_client_app_id = self.mc.aad_profile.client_app_id

        # read the original value passed by the command
        aad_server_app_id = self.raw_param.get("aad_server_app_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.aad_profile and
            self.mc.aad_profile.server_app_id
        ):
            aad_server_app_id = self.mc.aad_profile.server_app_id

        # read the original value passed by the command
        aad_server_app_secret = self.raw_param.get("aad_server_app_secret")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.aad_profile and
            self.mc.aad_profile.server_app_secret
        ):
            aad_server_app_secret = self.mc.aad_profile.server_app_secret

        # these parameters do not need dynamic completion

        # validation
        enable_aad = self._get_enable_aad(enable_validation=False)
        if enable_aad:
            if any(
                [
                    aad_client_app_id,
                    aad_server_app_id,
                    aad_server_app_secret,
                ]
            ):
                raise MutuallyExclusiveArgumentError(
                    "--enable-aad cannot be used together with --aad-client-app-id, --aad-server-app-id or "
                    "--aad-server-app-secret"
                )
        return aad_client_app_id, aad_server_app_id, aad_server_app_secret

    # pylint: disable=unused-argument
    def _get_aad_tenant_id(self, read_only: bool = False, **kwargs) -> Union[str, None]:
        """Internal function to dynamically obtain the value of aad_server_app_secret according to the context.

        When both aad_tenant_id and enable_aad are not assigned, and any of aad_client_app_id, aad_server_app_id or
        aad_server_app_secret is asssigned, dynamic completion will be triggerd. Class
        "azure.cli.core._profile.Profile" will be instantiated, and then call its "get_login_credentials" method to
        get the tenant of the deployment subscription.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        aad_tenant_id = self.raw_param.get("aad_tenant_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if (
            self.mc and
            self.mc.aad_profile and
            self.mc.aad_profile.tenant_id
        ):
            aad_tenant_id = self.mc.aad_profile.tenant_id
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return aad_tenant_id

        # dynamic completion
        if not read_from_mc and not self._get_enable_aad(
            enable_validation=False
        ):
            if aad_tenant_id is None and any(
                self.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret()
            ):
                profile = Profile(cli_ctx=self.cmd.cli_ctx)
                _, _, aad_tenant_id = profile.get_login_credentials()

        # this parameter does not need validation
        return aad_tenant_id

    def get_aad_tenant_id(self) -> Union[str, None]:
        """Dynamically obtain the value of aad_server_app_secret according to the context.

        When both aad_tenant_id and enable_aad are not assigned, and any of aad_client_app_id, aad_server_app_id or
        aad_server_app_secret is asssigned, dynamic completion will be triggerd. Class
        "azure.cli.core._profile.Profile" will be instantiated, and then call its "get_login_credentials" method to
        get the tenant of the deployment subscription.

        :return: string or None
        """

        return self._get_aad_tenant_id()

    def get_aad_admin_group_object_ids(self) -> Union[str, List[str], None]:
        """Obtain the value of aad_admin_group_object_ids.

        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.

        :return: empty list or list of strings, or None
        """
        # read the original value passed by the command
        aad_admin_group_object_ids = self.raw_param.get("aad_admin_group_object_ids")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if (
            self.mc and
            self.mc.aad_profile and
            self.mc.aad_profile.admin_group_object_i_ds
        ):
            aad_admin_group_object_ids = self.mc.aad_profile.admin_group_object_i_ds
            read_from_mc = True

        if not read_from_mc and aad_admin_group_object_ids is not None:
            aad_admin_group_object_ids = aad_admin_group_object_ids.split(',') if aad_admin_group_object_ids else []

        # this parameter does not need validation
        return aad_admin_group_object_ids

    def get_disable_rbac(self) -> bool:
        """Obtain the value of disable_rbac.

        This function will verify the parameter by default. If the values of disable_rbac and enable_azure_rbac are
        both True, a MutuallyExclusiveArgumentError will be raised.

        :return: bool
        """
        # read the original value passed by the command
        disable_rbac = self.raw_param.get("disable_rbac")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.enable_rbac is not None
        ):
            disable_rbac = False if self.mc.enable_rbac else True

        # this parameter does not need dynamic completion

        # validation
        if disable_rbac and self._get_enable_azure_rbac(enable_validation=False):
            raise MutuallyExclusiveArgumentError(
                "--enable-azure-rbac cannot be used together with --disable-rbac"
            )
        return disable_rbac

    # pylint: disable=unused-argument
    def _get_enable_azure_rbac(self, enable_validation: bool = False, **kwargs) -> bool:
        """Internal function to obtain the value of enable_azure_rbac.

        This function supports the option of enable_validation. When enabled, if the values of disable_rbac and
        enable_azure_rbac are both True, a MutuallyExclusiveArgumentError will be raised. If the value of enable_aad
        is False and the value of enable_azure_rbac is True, a RequiredArgumentMissingError will be raised.

        :return: bool
        """
        # read the original value passed by the command
        enable_azure_rbac = self.raw_param.get("enable_azure_rbac")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.aad_profile
        ):
            enable_azure_rbac = True if self.mc.aad_profile.enable_azure_rbac else False

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            if enable_azure_rbac and self.get_disable_rbac():
                raise MutuallyExclusiveArgumentError(
                    "--enable-azure-rbac cannot be used together with --disable-rbac"
                )
            if enable_azure_rbac and not self._get_enable_aad(enable_validation=False):
                raise RequiredArgumentMissingError(
                    "--enable-azure-rbac can only be used together with --enable-aad"
                )
        return enable_azure_rbac

    # pylint: disable=unused-argument
    def get_enable_azure_rbac(self, enable_validation: bool = False, **kwargs) -> bool:
        """Obtain the value of enable_azure_rbac.

        This function will verify the parameter by default. If the values of disable_rbac and enable_azure_rbac are
        both True, a MutuallyExclusiveArgumentError will be raised. If the value of enable_aad is False and the value
        of enable_azure_rbac is True, a RequiredArgumentMissingError will be raised.

        :return: bool
        """

        return self._get_enable_azure_rbac(enable_validation=True)


class AKSCreateDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client: ContainerServiceClient,
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

    def init_mc(self) -> ManagedCluster:
        """Initialize the ManagedCluster object with required parameter location and attach it to internal context.

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

        # attach mc to AKSCreateContext
        self.context.attach_mc(mc)
        return mc

    def set_up_agent_pool_profiles(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up agent pool profiles for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        (
            node_count,
            enable_auto_scaling,
            min_count,
            max_count,
        ) = (
            self.context.get_node_count_and_enable_cluster_autoscaler_and_min_count_and_max_count()
        )
        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            # Must be 12 chars or less before ACS RP adds to it
            name=self.context.get_nodepool_name(),
            tags=self.context.get_nodepool_tags(),
            node_labels=self.context.get_nodepool_labels(),
            count=node_count,
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
            min_count=min_count,
            max_count=max_count,
            enable_auto_scaling=enable_auto_scaling,
        )
        mc.agent_pool_profiles = [agent_pool_profile]
        return mc

    def set_up_linux_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up linux profile for the ManagedCluster object.

        Linux profile is just used for SSH access to VMs, so it will be omitted if --no-ssh-key option was specified.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        ssh_key_value, no_ssh_key = self.context.get_ssh_key_value_and_no_ssh_key()
        if not no_ssh_key:
            ssh_config = self.models.ContainerServiceSshConfiguration(
                public_keys=[
                    self.models.ContainerServiceSshPublicKey(
                        key_data=ssh_key_value
                    )
                ]
            )
            linux_profile = self.models.ContainerServiceLinuxProfile(
                admin_username=self.context.get_admin_username(), ssh=ssh_config
            )
            mc.linux_profile = linux_profile
        return mc

    def set_up_windows_profile(self, mc: ManagedCluster) -> ManagedCluster:
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
        return mc

    def set_up_service_principal_profile(self, mc: ManagedCluster) -> ManagedCluster:
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
        return mc

    def process_add_role_assignment_for_vnet_subnet(self, mc: ManagedCluster) -> None:
        """Add role assignment for vent subnet.

        The function "subnet_role_assignment_exists" will be called to verify if the role assignment already exists for
        the subnet, which internally used AuthorizationManagementClient to send the request.
        The function "_get_user_assigned_identity" will be called to get the client id of the user assigned identity,
        which internally used ManagedServiceIdentityClient to send the request.
        The function "_add_role_assignment" will be called to add role assignment for the subnet, which internally used
        AuthorizationManagementClient to send the request.

        This function will store an intermediate need_post_creation_vnet_permission_granting.

        :return: None
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

    def process_attach_acr(self, mc: ManagedCluster) -> None:
        """Attach acr for the cluster.

        The function "_ensure_aks_acr" will be called to create an AcrPull role assignment for the acr, which
        internally used AuthorizationManagementClient to send the request.

        :return: None
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        attach_acr = self.context.get_attach_acr()
        if attach_acr:
            # If enable_managed_identity, attach acr operation will be handled after the cluster is created
            if not self.context.get_enable_managed_identity():
                service_principal_profile = mc.service_principal_profile
                _ensure_aks_acr(
                    self.cmd,
                    client_id=service_principal_profile.client_id,
                    acr_name_or_id=attach_acr,
                    subscription_id=self.context.get_intermediate(
                        "subscription_id"
                    ),
                )

    def set_up_network_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up network profile for the ManagedCluster object.

        Build load balancer profile, verify outbound type and load balancer sku first, then set up network profile.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        # build load balancer profile, which is part of the network profile
        load_balancer_profile = create_load_balancer_profile(
            self.context.get_load_balancer_managed_outbound_ip_count(),
            self.context.get_load_balancer_outbound_ips(),
            self.context.get_load_balancer_outbound_ip_prefixes(),
            self.context.get_load_balancer_outbound_ports(),
            self.context.get_load_balancer_idle_timeout(),
            models=self.models.lb_models,
        )

        # verify outbound type
        # Note: Validation internally depends on load_balancer_sku, which is a temporary value that is
        # dynamically completed.
        outbound_type = self.context.get_outbound_type(
            load_balancer_profile=load_balancer_profile
        )

        # verify load balancer sku
        load_balancer_sku = self.context.get_load_balancer_sku()

        # verify network_plugin, pod_cidr, service_cidr, dns_service_ip, docker_bridge_address, network_policy
        network_plugin = self.context.get_network_plugin()
        (
            pod_cidr,
            service_cidr,
            dns_service_ip,
            docker_bridge_address,
            network_policy,
        ) = (
            self.context.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()
        )
        network_profile = None
        if any(
            [
                network_plugin,
                pod_cidr,
                service_cidr,
                dns_service_ip,
                docker_bridge_address,
                network_policy,
            ]
        ):
            # Attention: RP would return UnexpectedLoadBalancerSkuForCurrentOutboundConfiguration internal server error
            # if load_balancer_sku is set to basic and load_balancer_profile is assigned.
            # Attention: SDK provides default values for pod_cidr, service_cidr, dns_service_ip, docker_bridge_cidr
            # and outbound_type, and they might be overwritten to None.
            network_profile = self.models.ContainerServiceNetworkProfile(
                network_plugin=network_plugin,
                pod_cidr=pod_cidr,
                service_cidr=service_cidr,
                dns_service_ip=dns_service_ip,
                docker_bridge_cidr=docker_bridge_address,
                network_policy=network_policy,
                load_balancer_sku=load_balancer_sku,
                load_balancer_profile=load_balancer_profile,
                outbound_type=outbound_type,
            )
        else:
            if load_balancer_sku == "standard" or load_balancer_profile:
                network_profile = self.models.ContainerServiceNetworkProfile(
                    network_plugin="kubenet",
                    load_balancer_sku=load_balancer_sku,
                    load_balancer_profile=load_balancer_profile,
                    outbound_type=outbound_type,
                )
            if load_balancer_sku == "basic":
                # load balancer sku must be standard when load balancer profile is provided
                network_profile = self.models.ContainerServiceNetworkProfile(
                    load_balancer_sku=load_balancer_sku,
                )
        mc.network_profile = network_profile
        return mc

    # pylint: disable=too-many-statements
    def set_up_addon_profiles(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up addon profiles for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        ManagedClusterAddonProfile = self.models.ManagedClusterAddonProfile
        addon_profiles = {}
        # error out if any unrecognized or duplicate addon provided
        # error out if '--enable-addons=monitoring' isn't set but workspace_resource_id is
        # error out if '--enable-addons=virtual-node' is set but aci_subnet_name and vnet_subnet_id are not
        addons = self.context.get_enable_addons()
        if 'http_application_routing' in addons:
            addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME] = ManagedClusterAddonProfile(
                enabled=True)
            addons.remove('http_application_routing')
        if 'kube-dashboard' in addons:
            addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME] = ManagedClusterAddonProfile(
                enabled=True)
            addons.remove('kube-dashboard')
        # TODO: can we help the user find a workspace resource ID?
        if 'monitoring' in addons:
            workspace_resource_id = self.context.get_workspace_resource_id()
            addon_profiles[CONST_MONITORING_ADDON_NAME] = ManagedClusterAddonProfile(
                enabled=True, config={CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: workspace_resource_id})
            # post-process
            _ensure_container_insights_for_monitoring(self.cmd, addon_profiles[CONST_MONITORING_ADDON_NAME])
            # set intermediate
            self.context.set_intermediate("monitoring", True, overwrite_exists=True)
            addons.remove('monitoring')
        if 'azure-policy' in addons:
            addon_profiles[CONST_AZURE_POLICY_ADDON_NAME] = ManagedClusterAddonProfile(
                enabled=True)
            addons.remove('azure-policy')
        if 'virtual-node' in addons:
            aci_subnet_name = self.context.get_aci_subnet_name()
            # TODO: how about aciConnectorwindows, what is its addon name?
            os_type = self.context.get_virtual_node_addon_os_type()
            addon_profiles[CONST_VIRTUAL_NODE_ADDON_NAME + os_type] = ManagedClusterAddonProfile(
                enabled=True,
                config={CONST_VIRTUAL_NODE_SUBNET_NAME: aci_subnet_name}
            )
            # set intermediate
            self.context.set_intermediate("enable_virtual_node", True, overwrite_exists=True)
            addons.remove('virtual-node')
        if 'ingress-appgw' in addons:
            addon_profile = ManagedClusterAddonProfile(enabled=True, config={})
            appgw_name = self.context.get_appgw_name()
            appgw_subnet_cidr = self.context.get_appgw_subnet_cidr()
            appgw_id = self.context.get_appgw_id()
            appgw_subnet_id = self.context.get_appgw_subnet_id()
            appgw_watch_namespace = self.context.get_appgw_watch_namespace()
            if appgw_name is not None:
                addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME] = appgw_name
            if appgw_subnet_cidr is not None:
                addon_profile.config[CONST_INGRESS_APPGW_SUBNET_CIDR] = appgw_subnet_cidr
            if appgw_id is not None:
                addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID] = appgw_id
            if appgw_subnet_id is not None:
                addon_profile.config[CONST_INGRESS_APPGW_SUBNET_ID] = appgw_subnet_id
            if appgw_watch_namespace is not None:
                addon_profile.config[CONST_INGRESS_APPGW_WATCH_NAMESPACE] = appgw_watch_namespace
            addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME] = addon_profile
            # set intermediate
            self.context.set_intermediate("ingress_appgw_addon_enabled", True, overwrite_exists=True)
            addons.remove('ingress-appgw')
        if 'confcom' in addons:
            addon_profile = ManagedClusterAddonProfile(
                enabled=True, config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "false"})
            if self.context.get_enable_sgxquotehelper():
                addon_profile.config[CONST_ACC_SGX_QUOTE_HELPER_ENABLED] = "true"
            addon_profiles[CONST_CONFCOM_ADDON_NAME] = addon_profile
            addons.remove('confcom')
        mc.addon_profiles = addon_profiles
        return mc

    def set_up_aad_profile(self, mc) -> ManagedCluster:
        """Set up aad profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )
        aad_profile = None
        enable_aad = self.context.get_enable_aad()
        if enable_aad:
            aad_profile = self.models.ManagedClusterAADProfile(
                managed=True,
                enable_azure_rbac=self.context.get_enable_azure_rbac(),
                # ids -> i_ds due to track 2 naming issue
                admin_group_object_i_ds=self.context.get_aad_admin_group_object_ids(),
                tenant_id=self.context.get_aad_tenant_id()
            )
        else:
            (
                aad_client_app_id,
                aad_server_app_id,
                aad_server_app_secret,
            ) = (
                self.context.get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret()
            )
            aad_tenant_id = self.context.get_aad_tenant_id()
            if any([aad_client_app_id, aad_server_app_id, aad_server_app_secret, aad_tenant_id]):
                aad_profile = self.models.ManagedClusterAADProfile(
                    client_app_id=aad_client_app_id,
                    server_app_id=aad_server_app_id,
                    server_app_secret=aad_server_app_secret,
                    tenant_id=aad_tenant_id
                )
        mc.aad_profile = aad_profile
        return mc

    def construct_default_mc(self) -> ManagedCluster:
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
        # attach acr (add role assignment for acr)
        self.process_attach_acr(mc)
        # set up network profile
        mc = self.set_up_network_profile(mc)
        # set up addon profiles
        mc = self.set_up_addon_profiles(mc)
        # set up aad profile
        mc = self.set_up_aad_profile(mc)

        # TODO: set up other profiles
        return mc

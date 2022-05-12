# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import time
from types import SimpleNamespace
from typing import Dict, List, Tuple, TypeVar, Union

from azure.cli.command_modules.acs._consts import (
    CONST_LOAD_BALANCER_SKU_BASIC,
    CONST_LOAD_BALANCER_SKU_STANDARD,
    CONST_OUTBOUND_TYPE_LOAD_BALANCER,
    CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY,
    CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY,
    CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
    CONST_PRIVATE_DNS_ZONE_NONE,
    CONST_PRIVATE_DNS_ZONE_SYSTEM,
    AgentPoolDecoratorMode,
    DecoratorEarlyExitException,
    DecoratorMode,
)
from azure.cli.command_modules.acs._graph import ensure_aks_service_principal
from azure.cli.command_modules.acs._helpers import (
    check_is_msi_cluster,
    check_is_private_cluster,
    get_user_assigned_identity_by_resource_id,
    map_azure_error_to_cli_error,
    safe_list_get,
    safe_lower,
)
from azure.cli.command_modules.acs._loadbalancer import create_load_balancer_profile
from azure.cli.command_modules.acs._loadbalancer import update_load_balancer_profile as _update_load_balancer_profile
from azure.cli.command_modules.acs._natgateway import create_nat_gateway_profile, is_nat_gateway_profile_provided
from azure.cli.command_modules.acs._natgateway import update_nat_gateway_profile as _update_nat_gateway_profile
from azure.cli.command_modules.acs._resourcegroup import get_rg_location
from azure.cli.command_modules.acs._roleassignments import (
    add_role_assignment,
    ensure_aks_acr,
    ensure_cluster_identity_permission_on_kubelet_identity,
    subnet_role_assignment_exists,
)
from azure.cli.command_modules.acs._validators import extract_comma_separated_string
from azure.cli.command_modules.acs.addonconfiguration import (
    add_ingress_appgw_addon_role_assignment,
    add_monitoring_role_assignment,
    add_virtual_node_role_assignment,
    ensure_container_insights_for_monitoring,
    ensure_default_log_analytics_workspace_for_monitoring,
)
from azure.cli.command_modules.acs.agentpool_decorator import (
    AKSAgentPoolAddDecorator,
    AKSAgentPoolContext,
    AKSAgentPoolModels,
    AKSAgentPoolUpdateDecorator,
)
from azure.cli.command_modules.acs.base_decorator import (
    BaseAKSContext,
    BaseAKSManagedClusterDecorator,
    BaseAKSParamDict,
)
from azure.cli.core import AzCommandsLoader
from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import (
    AzCLIError,
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    NoTTYError,
    RequiredArgumentMissingError,
    UnknownError,
)
from azure.cli.core.commands import AzCliCommand, LongRunningOperation
from azure.cli.core.keys import is_valid_ssh_rsa_public_key
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait, truncate_text
from azure.core.exceptions import HttpResponseError
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt, prompt_pass, prompt_y_n
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import is_valid_resource_id

logger = get_logger(__name__)

# type variables
ContainerServiceClient = TypeVar("ContainerServiceClient")
Identity = TypeVar("Identity")
ManagedCluster = TypeVar("ManagedCluster")
ManagedClusterLoadBalancerProfile = TypeVar("ManagedClusterLoadBalancerProfile")
ManagedClusterPropertiesAutoScalerProfile = TypeVar("ManagedClusterPropertiesAutoScalerProfile")
ResourceReference = TypeVar("ResourceReference")
ManagedClusterAddonProfile = TypeVar("ManagedClusterAddonProfile")
Snapshot = TypeVar("Snapshot")
KubeletConfig = TypeVar("KubeletConfig")
LinuxOSConfig = TypeVar("LinuxOSConfig")

# TODO
# 1. remove enable_rbac related implementation
# 2. add validation for all/some of the parameters involved in the getter of outbound_type/enable_addons


# pylint: disable=too-few-public-methods
class AKSManagedClusterModels(AKSAgentPoolModels):
    """Store the models used in aks series of commands.

    The api version of the class corresponding to a model is determined by resource_type.
    """
    def __init__(self, cmd: AzCommandsLoader, resource_type: ResourceType):
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.MANAGED_CLUSTER
        super().__init__(cmd, resource_type, self.agentpool_decorator_mode)
        # holder for load balancer models
        self.__loadbalancer_models = None
        # holder for nat gateway related models
        self.__nat_gateway_models = None

    @property
    def load_balancer_models(self) -> SimpleNamespace:
        """Get load balancer related models.

        The models are stored in a SimpleNamespace object, could be accessed by the dot operator like
        `load_balancer_models.ManagedClusterLoadBalancerProfile`.

        :return: SimpleNamespace
        """
        if self.__loadbalancer_models is None:
            load_balancer_models = {}
            load_balancer_models["ManagedClusterLoadBalancerProfile"] = self.ManagedClusterLoadBalancerProfile
            load_balancer_models[
                "ManagedClusterLoadBalancerProfileManagedOutboundIPs"
            ] = self.ManagedClusterLoadBalancerProfileManagedOutboundIPs
            load_balancer_models[
                "ManagedClusterLoadBalancerProfileOutboundIPs"
            ] = self.ManagedClusterLoadBalancerProfileOutboundIPs
            load_balancer_models[
                "ManagedClusterLoadBalancerProfileOutboundIPPrefixes"
            ] = self.ManagedClusterLoadBalancerProfileOutboundIPPrefixes
            load_balancer_models["ResourceReference"] = self.ResourceReference
            self.__loadbalancer_models = SimpleNamespace(**load_balancer_models)
        return self.__loadbalancer_models

    @property
    def nat_gateway_models(self) -> SimpleNamespace:
        """Get nat gateway related models.

        The models are stored in a SimpleNamespace object, could be accessed by the dot operator like
        `nat_gateway_models.ManagedClusterNATGatewayProfile`.

        :return: SimpleNamespace
        """
        if self.__nat_gateway_models is None:
            nat_gateway_models = {}
            nat_gateway_models["ManagedClusterNATGatewayProfile"] = (
                self.ManagedClusterNATGatewayProfile if hasattr(self, "ManagedClusterNATGatewayProfile") else None
            )  # backward compatibility
            nat_gateway_models["ManagedClusterManagedOutboundIPProfile"] = (
                self.ManagedClusterManagedOutboundIPProfile
                if hasattr(self, "ManagedClusterManagedOutboundIPProfile")
                else None
            )   # backward compatibility
            self.__nat_gateway_models = SimpleNamespace(**nat_gateway_models)
        return self.__nat_gateway_models


# pylint: disable=too-few-public-methods
class AKSManagedClusterParamDict(BaseAKSParamDict):
    """Store the original parameters passed in by aks series of commands as an internal dictionary.

    Only expose the "get" method externally to obtain parameter values, while recording usage.
    """


# pylint: disable=too-many-public-methods
class AKSManagedClusterContext(BaseAKSContext):
    """Implement getter functions for all parameters in aks_create and aks_update.

    Each getter function is responsible for obtaining the corresponding one or more parameter values, and perform
    necessary parameter value completion or normalization and validation checks.

    This class also stores a copy of the original function parameters, some intermediate variables (such as the
    subscription ID), a reference of the ManagedCluster object and an indicator that specifies the current decorator
    mode (currently supports create and update).

    In the create mode, the most basic principles is that when parameters are put into a certain profile (and further
    decorated into the ManagedCluster object by AKSCreateDecorator), it shouldn't be modified any more, only read-only
    operations (e.g. validation) can be performed. In other words, when we try to get the value of a parameter, we
    should use its attribute value in the `mc` object as a preference. Only when the value has not been set in the `mc`
    object, we could return the user input value.

    In the update mode, in contrast to the create mode, we should use the value provided by the user to update the
    corresponding attribute value in the `mc` object.

    When adding support for a new parameter, you need to provide a "getter" function named `get_xxx`, where `xxx` is
    the parameter name. In this function, the process of obtaining parameter values, dynamic completion (optional),
    and validation (optional) should be followed. The obtaining of parameter values should further follow the order
    of obtaining from the ManagedCluster object or from the original value.

    When checking the validity of parameter values, a pair of parameters checking each other will cause a loop call.
    To avoid this problem, we can implement a new internal function. In the newly added internal function, we can
    easily skip the value completion and validation check by setting the `read_only` and `enable_validation` options
    respectively.
    """
    def __init__(
        self,
        cmd: AzCliCommand,
        raw_parameters: AKSManagedClusterParamDict,
        models: AKSManagedClusterModels,
        decorator_mode: DecoratorMode,
    ):
        super().__init__(cmd, raw_parameters, models, decorator_mode)
        self.mc = None
        # used to store origin mc in update mode
        self.__existing_mc = None
        # store the context, and used later to get agentpool related properties
        self.agentpool_context = None
        # used to store external functions
        self.__external_functions = None

    @property
    def existing_mc(self) -> ManagedCluster:
        """Get the existing ManagedCluster object in update mode.

        :return: ManagedCluster
        """
        return self.__existing_mc

    @property
    def external_functions(self) -> SimpleNamespace:
        if self.__external_functions is None:
            external_functions = {}
            external_functions["get_user_assigned_identity_by_resource_id"] = get_user_assigned_identity_by_resource_id
            external_functions["get_rg_location"] = get_rg_location
            external_functions["add_role_assignment"] = add_role_assignment
            external_functions["add_ingress_appgw_addon_role_assignment"] = add_ingress_appgw_addon_role_assignment
            external_functions["add_monitoring_role_assignment"] = add_monitoring_role_assignment
            external_functions["add_virtual_node_role_assignment"] = add_virtual_node_role_assignment
            external_functions["ensure_container_insights_for_monitoring"] = ensure_container_insights_for_monitoring
            external_functions[
                "ensure_default_log_analytics_workspace_for_monitoring"
            ] = ensure_default_log_analytics_workspace_for_monitoring
            external_functions["ensure_aks_acr"] = ensure_aks_acr
            external_functions["ensure_aks_service_principal"] = ensure_aks_service_principal
            external_functions[
                "ensure_cluster_identity_permission_on_kubelet_identity"
            ] = ensure_cluster_identity_permission_on_kubelet_identity
            external_functions["subnet_role_assignment_exists"] = subnet_role_assignment_exists
            self.__external_functions = SimpleNamespace(**external_functions)
        return self.__external_functions

    def attach_mc(self, mc: ManagedCluster) -> None:
        """Attach the ManagedCluster object to the context.

        The `mc` object is only allowed to be attached once, and attaching again will raise a CLIInternalError.

        :return: None
        """
        if self.decorator_mode == DecoratorMode.UPDATE:
            self.attach_existing_mc(mc)

        if self.mc is None:
            self.mc = mc
        else:
            msg = "the same" if self.mc == mc else "different"
            raise CLIInternalError(
                "Attempting to attach the `mc` object again, the two objects are {}.".format(
                    msg
                )
            )

    def attach_existing_mc(self, mc: ManagedCluster) -> None:
        """Attach the existing ManagedCluster object to the context in update mode.

        The `mc` object is only allowed to be attached once, and attaching again will raise a CLIInternalError.

        :return: None
        """
        if self.__existing_mc is None:
            self.__existing_mc = mc
        else:
            msg = "the same" if self.__existing_mc == mc else "different"
            raise CLIInternalError(
                "Attempting to attach the existing `mc` object again, the two objects are {}.".format(
                    msg
                )
            )

    def attach_agentpool_context(self, agentpool_context: AKSAgentPoolContext) -> None:
        """Attach the AKSAgentPoolContext object to the context.

        The `agentpool_context` object is only allowed to be attached once, and attaching again will raise a
        CLIInternalError.

        :return: None
        """
        if self.agentpool_context is None:
            self.agentpool_context = agentpool_context
        else:
            msg = "the same" if self.agentpool_context == agentpool_context else "different"
            raise CLIInternalError(
                "Attempting to attach the `agentpool_context` object again, the two objects are {}.".format(
                    msg
                )
            )

    def __validate_cluster_autoscaler_profile(
        self, cluster_autoscaler_profile: Union[List, Dict, None]
    ) -> Union[Dict, None]:
        """Helper function to parse and verify cluster_autoscaler_profile.

        If the user input is a list, parse it with function "extract_comma_separated_string". If the type of user input
        or parsed value is not a dictionary, raise an InvalidArgumentValueError. Otherwise, take the keys from the
        attribute map of ManagedClusterPropertiesAutoScalerProfile to verify whether the keys in the key-value pairs
        provided by the user are valid. If not, raise an InvalidArgumentValueError.

        :return: dictionary or None
        """
        if cluster_autoscaler_profile is not None:
            # convert list to dict
            if isinstance(cluster_autoscaler_profile, list):
                params_dict = {}
                for item in cluster_autoscaler_profile:
                    params_dict.update(
                        extract_comma_separated_string(
                            item,
                            extract_kv=True,
                            allow_empty_value=True,
                            default_value={},
                        )
                    )
                cluster_autoscaler_profile = params_dict
            # check if the type is dict
            if not isinstance(cluster_autoscaler_profile, dict):
                raise InvalidArgumentValueError(
                    "Unexpected input cluster-autoscaler-profile, value: '{}', type '{}'.".format(
                        cluster_autoscaler_profile,
                        type(cluster_autoscaler_profile),
                    )
                )
            # verify keys
            # pylint: disable=protected-access
            valid_keys = list(
                k.replace("_", "-") for k in self.models.ManagedClusterPropertiesAutoScalerProfile._attribute_map.keys()
            )
            for key in cluster_autoscaler_profile.keys():
                if not key:
                    raise InvalidArgumentValueError("Empty key specified for cluster-autoscaler-profile")
                if key not in valid_keys:
                    raise InvalidArgumentValueError(
                        "'{}' is an invalid key for cluster-autoscaler-profile. Valid keys are {}.".format(
                            key, ", ".join(valid_keys)
                        )
                    )
        return cluster_autoscaler_profile

    # pylint: disable=no-self-use
    def __validate_gmsa_options(
        self,
        enable_windows_gmsa,
        gmsa_dns_server,
        gmsa_root_domain_name,
        yes,
    ) -> None:
        """Helper function to validate gmsa related options.

        When enable_windows_gmsa is specified, if both gmsa_dns_server and gmsa_root_domain_name are not assigned and
        user does not confirm the operation, a DecoratorEarlyExitException will be raised; if only one of
        gmsa_dns_server or gmsa_root_domain_name is assigned, raise a RequiredArgumentMissingError. When
        enable_windows_gmsa is not specified, if any of gmsa_dns_server or gmsa_root_domain_name is assigned, raise
        a RequiredArgumentMissingError.

        :return: bool
        """
        if enable_windows_gmsa:
            if gmsa_dns_server is None and gmsa_root_domain_name is None:
                msg = (
                    "Please assure that you have set the DNS server in the vnet used by the cluster "
                    "when not specifying --gmsa-dns-server and --gmsa-root-domain-name"
                )
                if not yes and not prompt_y_n(msg, default="n"):
                    raise DecoratorEarlyExitException()
            elif not all([gmsa_dns_server, gmsa_root_domain_name]):
                raise RequiredArgumentMissingError(
                    "You must set or not set --gmsa-dns-server and --gmsa-root-domain-name at the same time."
                )
        else:
            if any([gmsa_dns_server, gmsa_root_domain_name]):
                raise RequiredArgumentMissingError(
                    "You only can set --gmsa-dns-server and --gmsa-root-domain-name "
                    "when setting --enable-windows-gmsa."
                )

    def get_subscription_id(self):
        """Helper function to obtain the value of subscription_id.

        Note: This is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        If no corresponding intermediate exists, method "get_subscription_id" of class "Profile" will be called, which
        depends on "az login" in advance, the returned subscription_id will be stored as an intermediate.

        :return: string
        """
        subscription_id = self.get_intermediate("subscription_id", None)
        if not subscription_id:
            subscription_id = self.cmd.cli_ctx.data.get('subscription_id')
            if not subscription_id:
                subscription_id = Profile(cli_ctx=self.cmd.cli_ctx).get_subscription_id()
                self.cmd.cli_ctx.data['subscription_id'] = subscription_id
            self.set_intermediate("subscription_id", subscription_id, overwrite_exists=True)
        return subscription_id

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

    def _get_location(self, read_only: bool = False) -> Union[str, None]:
        """Internal function to dynamically obtain the value of location according to the context.

        When location is not assigned, dynamic completion will be triggerd. Function "get_rg_location" will be called
        to get the location of the provided resource group, which internally used ResourceManagementClient to send
        the request.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        location = self.raw_param.get("location")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if self.mc and self.mc.location is not None:
            location = self.mc.location
            read_from_mc = True
        # try to read from intermediate
        if location is None and self.get_intermediate("location"):
            location = self.get_intermediate("location")

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return location

        # dynamic completion
        if not read_from_mc and location is None:
            location = self.external_functions.get_rg_location(
                self.cmd.cli_ctx, self.get_resource_group_name()
            )
            self.set_intermediate("location", location, overwrite_exists=True)

        # this parameter does not need validation
        return location

    def get_location(self) -> Union[str, None]:
        """Dynamically obtain the value of location according to the context.

        When location is not assigned, dynamic completion will be triggerd. Function "get_rg_location" will be called
        to get the location of the provided resource group, which internally used ResourceManagementClient to send
        the request.

        :return: string or None
        """
        return self._get_location()

    def get_tags(self) -> Union[Dict[str, str], None]:
        """Obtain the value of tags.

        :return: dictionary or None
        """
        # read the original value passed by the command
        tags = self.raw_param.get("tags")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.mc and self.mc.tags is not None:
                tags = self.mc.tags

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return tags

    def get_kubernetes_version(self) -> str:
        """Obtain the value of kubernetes_version.

        :return: string
        """
        return self.agentpool_context.get_kubernetes_version()

    def get_vnet_subnet_id(self) -> Union[str, None]:
        """Obtain the value of vnet_subnet_id.

        :return: string or None
        """
        return self.agentpool_context.get_vnet_subnet_id()

    def get_nodepool_labels(self) -> Union[Dict[str, str], None]:
        """Obtain the value of nodepool_labels.

        :return: dictionary or None
        """
        return self.agentpool_context.get_nodepool_labels()

    def _get_dns_name_prefix(
        self, enable_validation: bool = False, read_only: bool = False
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of dns_name_prefix according to the context.

        When both dns_name_prefix and fqdn_subdomain are not assigned, dynamic completion will be triggerd. A default
        dns_name_prefix composed of name (cluster), resource_group_name, and subscription_id will be created.

        This function supports the option of enable_validation. When enabled, it will check if both dns_name_prefix and
        fqdn_subdomain are assigend, if so, raise the MutuallyExclusiveArgumentError.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        dns_name_prefix = self.raw_param.get("dns_name_prefix")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if self.mc and self.mc.dns_prefix is not None:
            dns_name_prefix = self.mc.dns_prefix
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return dns_name_prefix

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if not dns_name_prefix and not self._get_fqdn_subdomain(enable_validation=False):
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        # In case the user does not specify the parameter and it meets the conditions of automatic completion,
        # necessary information is dynamically completed.
        if dynamic_completion:
            name = self.get_name()
            resource_group_name = self.get_resource_group_name()
            subscription_id = self.get_subscription_id()
            # Use subscription id to provide uniqueness and prevent DNS name clashes
            name_part = re.sub('[^A-Za-z0-9-]', '', name)[0:10]
            if not name_part[0].isalpha():
                name_part = (str('a') + name_part)[0:10]
            resource_group_part = re.sub(
                '[^A-Za-z0-9-]', '', resource_group_name)[0:16]
            dns_name_prefix = '{}-{}-{}'.format(name_part, resource_group_part, subscription_id[0:6])

        # validation
        if enable_validation:
            if dns_name_prefix and self._get_fqdn_subdomain(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                )
        return dns_name_prefix

    def get_dns_name_prefix(self) -> Union[str, None]:
        """Dynamically obtain the value of dns_name_prefix according to the context.

        When both dns_name_prefix and fqdn_subdomain are not assigned, dynamic completion will be triggerd. A default
        dns_name_prefix composed of name (cluster), resource_group_name, and subscription_id will be created.

        This function will verify the parameter by default. It will check if both dns_name_prefix and fqdn_subdomain
        are assigend, if so, raise the MutuallyExclusiveArgumentError.

        :return: string or None
        """
        return self._get_dns_name_prefix(enable_validation=True)

    def get_node_osdisk_diskencryptionset_id(self) -> Union[str, None]:
        """Obtain the value of node_osdisk_diskencryptionset_id.

        :return: string or None
        """
        # read the original value passed by the command
        node_osdisk_diskencryptionset_id = self.raw_param.get("node_osdisk_diskencryptionset_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.disk_encryption_set_id is not None
        ):
            node_osdisk_diskencryptionset_id = self.mc.disk_encryption_set_id

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_osdisk_diskencryptionset_id

    def get_ssh_key_value_and_no_ssh_key(self) -> Tuple[str, bool]:
        """Obtain the value of ssh_key_value and no_ssh_key.

        Note: no_ssh_key will not be decorated into the `mc` object.

        If the user does not explicitly specify --ssh-key-value, the validator function "validate_ssh_key" will check
        the default file location "~/.ssh/id_rsa.pub", if the file exists, read its content and return. Otherise,
        create a key pair at "~/.ssh/id_rsa.pub" and return the public key.
        If the user provides a string-like input for --ssh-key-value, the validator function "validate_ssh_key" will
        check whether it is a file path, if so, read its content and return; if it is a valid public key, return it.
        Otherwise, create a key pair there and return the public key.

        This function will verify the parameters by default. It will verify the validity of ssh_key_value. If parameter
        no_ssh_key is set to True, verification will be skipped. Otherwise, an InvalidArgumentValueError will be raised
        when the value of ssh_key_value is invalid.

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
        if not no_ssh_key:
            try:
                if not ssh_key_value or not is_valid_ssh_rsa_public_key(
                    ssh_key_value
                ):
                    raise ValueError()
            except (TypeError, ValueError):
                shortened_key = truncate_text(ssh_key_value)
                raise InvalidArgumentValueError(
                    "Provided ssh key ({}) is invalid or non-existent".format(
                        shortened_key
                    )
                )
        return ssh_key_value, no_ssh_key

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
            self.mc.linux_profile.admin_username is not None
        ):
            admin_username = self.mc.linux_profile.admin_username

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return admin_username

    def _get_windows_admin_username_and_password(
        self, read_only: bool = False, enable_validation: bool = False
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Internal function to dynamically obtain the value of windows_admin_username and windows_admin_password
        according to the context.

        Note: This function is intended to be used in create mode.
        Note: All the external parameters involved in the validation are not verified in their own getters.

        When one of windows_admin_username and windows_admin_password is not assigned, dynamic completion will be
        triggerd. The user will be prompted to enter the missing windows_admin_username or windows_admin_password in
        tty (pseudo terminal). If the program is running in a non-interactive environment, a NoTTYError error will be
        raised.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.
        This function supports the option of enable_validation. When enabled, if neither windows_admin_username or
        windows_admin_password is specified and any of enable_windows_gmsa, gmsa_dns_server or gmsa_root_domain_name is
        specified, raise a RequiredArgumentMissingError.

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
            self.mc.windows_profile.admin_username is not None
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
            self.mc.windows_profile.admin_password is not None
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

        # validation
        # Note: The external parameters involved in the validation are not verified in their own getters.
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                if not any([windows_admin_username, windows_admin_password]):
                    if self._get_enable_windows_gmsa(
                        enable_validation=False
                    ) or any(self._get_gmsa_dns_server_and_root_domain_name(
                        enable_validation=False
                    )):
                        raise RequiredArgumentMissingError(
                            "Please set windows admin username and password before setting gmsa related configs."
                        )
        return windows_admin_username, windows_admin_password

    def get_windows_admin_username_and_password(
        self,
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Dynamically obtain the value of windows_admin_username and windows_admin_password according to the context.

        Note: This function is intended to be used in create mode.
        Note: All the external parameters involved in the validation are not verified in their own getters.

        When one of windows_admin_username and windows_admin_password is not assigned, dynamic completion will be
        triggerd. The user will be prompted to enter the missing windows_admin_username or windows_admin_password in
        tty (pseudo terminal). If the program is running in a non-interactive environment, a NoTTYError error will be
        raised.

        This function will verify the parameter by default. If neither windows_admin_username or windows_admin_password
        is specified and any of enable_windows_gmsa, gmsa_dns_server or gmsa_root_domain_name is specified, raise a
        RequiredArgumentMissingError.

        :return: a tuple containing two elements: windows_admin_username of string type or None and
        windows_admin_password of string type or None
        """
        return self._get_windows_admin_username_and_password(enable_validation=True)

    def get_windows_admin_password(self) -> Union[str, None]:
        """Obtain the value of windows_admin_password.

        Note: This function is intended to be used in update mode.

        :return: string or None
        """
        # read the original value passed by the command
        windows_admin_password = self.raw_param.get("windows_admin_password")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return windows_admin_password

    def _get_enable_ahub(
        self, enable_validation: bool = False
    ) -> bool:
        """Internal function to obtain the value of enable_ahub.

        Note: enable_ahub will not be directly decorated into the `mc` object.

        This function supports the option of enable_validation. When enabled, if both enable_ahub and disable_ahub are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        enable_ahub = self.raw_param.get("enable_ahub")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.mc and self.mc.windows_profile:
                enable_ahub = self.mc.windows_profile.license_type == "Windows_Server"

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if enable_ahub and self._get_disable_ahub(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    'Cannot specify "--enable-ahub" and "--disable-ahub" at the same time'
                )
        return enable_ahub

    def get_enable_ahub(self) -> bool:
        """Obtain the value of enable_ahub.

        Note: enable_ahub will not be directly decorated into the `mc` object.

        This function will verify the parameter by default. If both enable_ahub and disable_ahub are specified,
        raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_enable_ahub(enable_validation=True)

    def _get_disable_ahub(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_ahub.

        Note: disable_ahub will not be directly decorated into the `mc` object.

        This function supports the option of enable_validation. When enabled, if both enable_ahub and disable_ahub are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        disable_ahub = self.raw_param.get("disable_ahub")
        # We do not support this option in create mode, therefore we do not read the value from `mc`.

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if disable_ahub and self._get_enable_ahub(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    'Cannot specify "--enable-ahub" and "--disable-ahub" at the same time'
                )
        return disable_ahub

    def get_disable_ahub(self) -> bool:
        """Obtain the value of disable_ahub.

        Note: disable_ahub will not be directly decorated into the `mc` object.

        This function will verify the parameter by default. If both enable_ahub and disable_ahub are specified,
        raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_disable_ahub(enable_validation=True)

    def _get_enable_windows_gmsa(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_windows_gmsa.

        This function supports the option of enable_validation. Please refer to function __validate_gmsa_options for
        details of validation.

        :return: bool
        """
        # read the original value passed by the command
        enable_windows_gmsa = self.raw_param.get("enable_windows_gmsa")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.windows_profile and
                hasattr(self.mc.windows_profile, "gmsa_profile") and  # backward compatibility
                self.mc.windows_profile.gmsa_profile and
                self.mc.windows_profile.gmsa_profile.enabled is not None
            ):
                enable_windows_gmsa = self.mc.windows_profile.gmsa_profile.enabled

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            (
                gmsa_dns_server,
                gmsa_root_domain_name,
            ) = self._get_gmsa_dns_server_and_root_domain_name(
                enable_validation=False
            )
            self.__validate_gmsa_options(
                enable_windows_gmsa, gmsa_dns_server, gmsa_root_domain_name, self.get_yes()
            )
        return enable_windows_gmsa

    def get_enable_windows_gmsa(self) -> bool:
        """Obtain the value of enable_windows_gmsa.

        This function will verify the parameter by default. When enable_windows_gmsa is specified, if both
        gmsa_dns_server and gmsa_root_domain_name are not assigned and user does not confirm the operation,
        a DecoratorEarlyExitException will be raised; if only one of gmsa_dns_server or gmsa_root_domain_name is
        assigned, raise a RequiredArgumentMissingError. When enable_windows_gmsa is not specified, if any of
        gmsa_dns_server or gmsa_root_domain_name is assigned, raise a RequiredArgumentMissingError.

        :return: bool
        """
        return self._get_enable_windows_gmsa(enable_validation=True)

    def _get_gmsa_dns_server_and_root_domain_name(self, enable_validation: bool = False):
        """Internal function to obtain the values of gmsa_dns_server and gmsa_root_domain_name.

        This function supports the option of enable_validation. Please refer to function __validate_gmsa_options for
        details of validation.

        :return: a tuple containing two elements: gmsa_dns_server of string type or None and gmsa_root_domain_name of
        string type or None
        """
        # gmsa_dns_server
        # read the original value passed by the command
        gmsa_dns_server = self.raw_param.get("gmsa_dns_server")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        gmsa_dns_read_from_mc = False
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.windows_profile and
                hasattr(self.mc.windows_profile, "gmsa_profile") and  # backward compatibility
                self.mc.windows_profile.gmsa_profile and
                self.mc.windows_profile.gmsa_profile.dns_server is not None
            ):
                gmsa_dns_server = self.mc.windows_profile.gmsa_profile.dns_server
                gmsa_dns_read_from_mc = True

        # gmsa_root_domain_name
        # read the original value passed by the command
        gmsa_root_domain_name = self.raw_param.get("gmsa_root_domain_name")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        gmsa_root_read_from_mc = False
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.windows_profile and
                hasattr(self.mc.windows_profile, "gmsa_profile") and  # backward compatibility
                self.mc.windows_profile.gmsa_profile and
                self.mc.windows_profile.gmsa_profile.root_domain_name is not None
            ):
                gmsa_root_domain_name = self.mc.windows_profile.gmsa_profile.root_domain_name
                gmsa_root_read_from_mc = True

        # consistent check
        if gmsa_dns_read_from_mc != gmsa_root_read_from_mc:
            raise CLIInternalError(
                "Inconsistent state detected, one of gmsa_dns_server and gmsa_root_domain_name "
                "is read from the `mc` object."
            )

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            self.__validate_gmsa_options(
                self._get_enable_windows_gmsa(enable_validation=False),
                gmsa_dns_server,
                gmsa_root_domain_name,
                self.get_yes(),
            )
        return gmsa_dns_server, gmsa_root_domain_name

    def get_gmsa_dns_server_and_root_domain_name(self) -> Tuple[Union[str, None], Union[str, None]]:
        """Obtain the values of gmsa_dns_server and gmsa_root_domain_name.

        This function will verify the parameter by default. When enable_windows_gmsa is specified, if both
        gmsa_dns_server and gmsa_root_domain_name are not assigned and user does not confirm the operation,
        a DecoratorEarlyExitException will be raised; if only one of gmsa_dns_server or gmsa_root_domain_name is
        assigned, raise a RequiredArgumentMissingError. When enable_windows_gmsa is not specified, if any of
        gmsa_dns_server or gmsa_root_domain_name is assigned, raise a RequiredArgumentMissingError.

        :return: a tuple containing two elements: gmsa_dns_server of string type or None and gmsa_root_domain_name of
        string type or None
        """
        return self._get_gmsa_dns_server_and_root_domain_name(enable_validation=True)

    # pylint: disable=too-many-statements
    def _get_service_principal_and_client_secret(
        self, read_only: bool = False
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Internal function to dynamically obtain the values of service_principal and client_secret according to the
        context.

        When service_principal and client_secret are not assigned and enable_managed_identity is True, dynamic
        completion will not be triggered. For other cases, dynamic completion will be triggered.
        When client_secret is given but service_principal is not, dns_name_prefix or fqdn_subdomain will be used to
        create a service principal. The parameters subscription_id, location and name (cluster) are also required when
        calling function "ensure_aks_service_principal", which internally used GraphRbacManagementClient to send
        the request.
        When service_principal is given but client_secret is not, function "ensure_aks_service_principal" would raise
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
            self.mc.service_principal_profile.client_id is not None
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
            self.mc.service_principal_profile.secret is not None
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
            principal_obj = self.external_functions.ensure_aks_service_principal(
                cli_ctx=self.cmd.cli_ctx,
                service_principal=service_principal,
                client_secret=client_secret,
                subscription_id=self.get_subscription_id(),
                dns_name_prefix=self._get_dns_name_prefix(enable_validation=False),
                fqdn_subdomain=self._get_fqdn_subdomain(enable_validation=False),
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
        calling function "ensure_aks_service_principal", which internally used GraphRbacManagementClient to send
        the request.
        When service_principal is given but client_secret is not, function "ensure_aks_service_principal" would raise
        CLIError.

        :return: a tuple containing two elements: service_principal of string type or None and client_secret of
        string type or None
        """
        return self._get_service_principal_and_client_secret()

    def _get_enable_managed_identity(
        self, enable_validation: bool = False, read_only: bool = False
    ) -> bool:
        """Internal function to dynamically obtain the values of service_principal and client_secret according to the
        context.

        Note: enable_managed_identity will not be directly decorated into the `mc` object.

        When both service_principal and client_secret are assigned and enable_managed_identity is True, dynamic
        completion will be triggered. The value of enable_managed_identity will be set to False.

        This function supports the option of enable_validation. When enabled, if enable_managed_identity is not
        specified and assign_identity is assigned, a RequiredArgumentMissingError will be raised.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: bool
        """
        # read the original value passed by the command
        enable_managed_identity = self.raw_param.get("enable_managed_identity")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.mc and self.mc.identity:
                enable_managed_identity = check_is_msi_cluster(self.mc)
                read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return enable_managed_identity

        # dynamic completion for create mode only
        if self.decorator_mode == DecoratorMode.CREATE:
            (
                service_principal,
                client_secret,
            ) = self._get_service_principal_and_client_secret(read_only=True)
            if not read_from_mc and service_principal and client_secret:
                enable_managed_identity = False

        # validation
        if enable_validation:
            if not enable_managed_identity and self._get_assign_identity(enable_validation=False):
                raise RequiredArgumentMissingError(
                    "--assign-identity can only be specified when --enable-managed-identity is specified"
                )
        return enable_managed_identity

    def get_enable_managed_identity(self) -> bool:
        """Dynamically obtain the values of service_principal and client_secret according to the context.

        Note: enable_managed_identity will not be directly decorated into the `mc` object.

        When both service_principal and client_secret are assigned and enable_managed_identity is True, dynamic
        completion will be triggered. The value of enable_managed_identity will be set to False.

        This function will verify the parameter by default. If enable_managed_identity is not specified and
        assign_identity is assigned, a RequiredArgumentMissingError will be raised.

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

    def _get_assign_identity(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of assign_identity.

        This function supports the option of enable_validation. When enabled, if enable_managed_identity is not
        specified and assign_identity is assigned, a RequiredArgumentMissingError will be raised. Besides, if
        assign_identity is not assigned but assign_kubelet_identity is, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """
        # read the original value passed by the command
        assign_identity = self.raw_param.get("assign_identity")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.identity and
                self.mc.identity.user_assigned_identities is not None
            ):
                value_obtained_from_mc = safe_list_get(
                    list(self.mc.identity.user_assigned_identities.keys()), 0, None
                )
                if value_obtained_from_mc is not None:
                    assign_identity = value_obtained_from_mc

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if assign_identity:
                if not self._get_enable_managed_identity(enable_validation=False):
                    raise RequiredArgumentMissingError(
                        "--assign-identity can only be specified when --enable-managed-identity is specified"
                    )
            else:
                if self.decorator_mode == DecoratorMode.CREATE:
                    if self._get_assign_kubelet_identity(enable_validation=False):
                        raise RequiredArgumentMissingError(
                            "--assign-kubelet-identity can only be specified when --assign-identity is specified"
                        )
        return assign_identity

    def get_assign_identity(self) -> Union[str, None]:
        """Obtain the value of assign_identity.

        This function will verify the parameter by default. If enable_managed_identity is not specified and
        assign_identity is assigned, a RequiredArgumentMissingError will be raised. Besides, if assign_identity is not
        assigned but assign_kubelet_identity is, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """

        return self._get_assign_identity(enable_validation=True)

    def get_identity_by_msi_client(self, assigned_identity: str) -> Identity:
        """Helper function to obtain the identity object by msi client.

        Note: This is a wrapper of the external function "get_user_assigned_identity_by_resource_id", and the return
        value of this function will not be directly decorated into the `mc` object.

        This function will use ManagedServiceIdentityClient to send the request, and return an identity object.
        ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions might be raised in the above
        process.

        :return: string
        """
        return self.external_functions.get_user_assigned_identity_by_resource_id(self.cmd.cli_ctx, assigned_identity)

    def get_user_assigned_identity_client_id(self) -> str:
        """Helper function to obtain the client_id of user assigned identity.

        Note: This is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the client_id field in the
        returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = self.get_assign_identity()
        if assigned_identity is None or assigned_identity == "":
            raise RequiredArgumentMissingError("No assigned identity provided.")
        return self.get_identity_by_msi_client(assigned_identity).client_id

    def get_user_assigned_identity_object_id(self) -> str:
        """Helper function to obtain the principal_id of user assigned identity.

        Note: This is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the principal_id field in
        the returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = self.get_assign_identity()
        if assigned_identity is None or assigned_identity == "":
            raise RequiredArgumentMissingError("No assigned identity provided.")
        return self.get_identity_by_msi_client(assigned_identity).principal_id

    def get_attach_acr(self) -> Union[str, None]:
        """Obtain the value of attach_acr.

        Note: attach_acr will not be decorated into the `mc` object.

        This function will verify the parameter by default in create mode. When attach_acr is assigned, if both
        enable_managed_identity and no_wait are assigned, a MutuallyExclusiveArgumentError will be raised; if
        service_principal is not assigned, raise a RequiredArgumentMissingError.

        :return: string or None
        """
        # read the original value passed by the command
        attach_acr = self.raw_param.get("attach_acr")

        # this parameter does not need dynamic completion
        # validation
        if self.decorator_mode == DecoratorMode.CREATE and attach_acr:
            if self._get_enable_managed_identity(enable_validation=False):
                # Attach acr operation will be handled after the cluster is created
                if self.get_no_wait():
                    raise MutuallyExclusiveArgumentError(
                        "When --attach-acr and --enable-managed-identity are both specified, "
                        "--no-wait is not allowed, please wait until the whole operation succeeds."
                    )
            else:
                # newly added check, check whether client_id exists before creating role assignment
                service_principal, _ = self._get_service_principal_and_client_secret(read_only=True)
                if not service_principal:
                    raise RequiredArgumentMissingError(
                        "No service principal provided to create the acrpull role assignment for acr."
                    )
        return attach_acr

    def get_detach_acr(self) -> Union[str, None]:
        """Obtain the value of detach_acr.

        Note: detach_acr will not be decorated into the `mc` object.

        :return: string or None
        """
        # read the original value passed by the command
        detach_acr = self.raw_param.get("detach_acr")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return detach_acr

    def get_assignee_from_identity_or_sp_profile(self) -> Tuple[str, bool]:
        """Helper function to obtain the value of assignee from identity_profile or service_principal_profile.

        Note: This is not a parameter of aks_update, and it will not be decorated into the `mc` object.

        If assignee cannot be obtained, raise an UnknownError.

        :return: string, bool
        """
        assignee = None
        is_service_principal = False
        if check_is_msi_cluster(self.mc):
            if self.mc.identity_profile is None or self.mc.identity_profile["kubeletidentity"] is None:
                raise UnknownError(
                    "Unexpected error getting kubelet's identity for the cluster. "
                    "Please do not set --attach-acr or --detach-acr. "
                    "You can manually grant or revoke permission to the identity named "
                    "<ClUSTER_NAME>-agentpool in MC_ resource group to access ACR."
                )
            assignee = self.mc.identity_profile["kubeletidentity"].object_id
            is_service_principal = False
        elif self.mc and self.mc.service_principal_profile is not None:
            assignee = self.mc.service_principal_profile.client_id
            is_service_principal = True

        if not assignee:
            raise UnknownError('Cannot get the AKS cluster\'s service principal.')
        return assignee, is_service_principal

    def _get_load_balancer_sku(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of load_balancer_sku, default value is
        CONST_LOAD_BALANCER_SKU_STANDARD.

        Note: When returning a string, it will always be lowercase.

        This function supports the option of enable_validation. When enabled, it will check if load_balancer_sku equals
        to CONST_LOAD_BALANCER_SKU_BASIC, if so, when api_server_authorized_ip_ranges is assigned or
        enable_private_cluster is specified, raise an InvalidArgumentValueError.

        :return: string or None
        """
        # read the original value passed by the command
        load_balancer_sku = safe_lower(self.raw_param.get("load_balancer_sku", CONST_LOAD_BALANCER_SKU_STANDARD))
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_sku is not None
        ):
            load_balancer_sku = safe_lower(
                self.mc.network_profile.load_balancer_sku
            )

        # validation
        if enable_validation:
            if load_balancer_sku == CONST_LOAD_BALANCER_SKU_BASIC:
                if self._get_api_server_authorized_ip_ranges(enable_validation=False):
                    raise InvalidArgumentValueError(
                        "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                    )
                if self._get_enable_private_cluster(enable_validation=False):
                    raise InvalidArgumentValueError(
                        "Please use standard load balancer for private cluster"
                    )

        return load_balancer_sku

    def get_load_balancer_sku(self) -> Union[str, None]:
        """Obtain the value of load_balancer_sku, default value is CONST_LOAD_BALANCER_SKU_STANDARD.

        Note: When returning a string, it will always be lowercase.

        This function will verify the parameter by default. It will check if load_balancer_sku equals to
        CONST_LOAD_BALANCER_SKU_BASIC, if so, when api_server_authorized_ip_ranges is assigned or
        enable_private_cluster is specified, raise an InvalidArgumentValueError.

        :return: string or None
        """
        return safe_lower(self._get_load_balancer_sku(enable_validation=True))

    def get_load_balancer_managed_outbound_ip_count(self) -> Union[int, None]:
        """Obtain the value of load_balancer_managed_outbound_ip_count.

        Note: SDK performs the following validation {'maximum': 100, 'minimum': 1}.

        :return: int or None
        """
        # read the original value passed by the command
        load_balancer_managed_outbound_ip_count = self.raw_param.get(
            "load_balancer_managed_outbound_ip_count"
        )
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.network_profile and
                self.mc.network_profile.load_balancer_profile and
                self.mc.network_profile.load_balancer_profile.managed_outbound_i_ps and
                self.mc.network_profile.load_balancer_profile.managed_outbound_i_ps.count is not None
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
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.network_profile and
                self.mc.network_profile.load_balancer_profile and
                self.mc.network_profile.load_balancer_profile.outbound_i_ps and
                self.mc.network_profile.load_balancer_profile.outbound_i_ps.public_i_ps is not None
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
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.network_profile and
                self.mc.network_profile.load_balancer_profile and
                self.mc.network_profile.load_balancer_profile.outbound_ip_prefixes and
                self.mc.network_profile.load_balancer_profile.outbound_ip_prefixes.public_ip_prefixes is not None
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
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.network_profile and
                self.mc.network_profile.load_balancer_profile and
                self.mc.network_profile.load_balancer_profile.allocated_outbound_ports is not None
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
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.network_profile and
                self.mc.network_profile.load_balancer_profile and
                self.mc.network_profile.load_balancer_profile.idle_timeout_in_minutes is not None
            ):
                load_balancer_idle_timeout = (
                    self.mc.network_profile.load_balancer_profile.idle_timeout_in_minutes
                )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return load_balancer_idle_timeout

    def get_nat_gateway_managed_outbound_ip_count(self) -> Union[int, None]:
        """Obtain the value of nat_gateway_managed_outbound_ip_count.

        Note: SDK provides default value 1 and performs the following validation {'maximum': 16, 'minimum': 1}.

        :return: int or None
        """
        # read the original value passed by the command
        nat_gateway_managed_outbound_ip_count = self.raw_param.get("nat_gateway_managed_outbound_ip_count")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.network_profile and
                self.mc.network_profile.nat_gateway_profile and
                self.mc.network_profile.nat_gateway_profile.managed_outbound_ip_profile and
                self.mc.network_profile.nat_gateway_profile.managed_outbound_ip_profile.count is not None
            ):
                nat_gateway_managed_outbound_ip_count = (
                    self.mc.network_profile.nat_gateway_profile.managed_outbound_ip_profile.count
                )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nat_gateway_managed_outbound_ip_count

    def get_nat_gateway_idle_timeout(self) -> Union[int, None]:
        """Obtain the value of nat_gateway_idle_timeout.

        Note: SDK provides default value 4 and performs the following validation {'maximum': 120, 'minimum': 4}.

        :return: int or None
        """
        # read the original value passed by the command
        nat_gateway_idle_timeout = self.raw_param.get("nat_gateway_idle_timeout")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.network_profile and
                self.mc.network_profile.nat_gateway_profile and
                self.mc.network_profile.nat_gateway_profile.idle_timeout_in_minutes is not None
            ):
                nat_gateway_idle_timeout = (
                    self.mc.network_profile.nat_gateway_profile.idle_timeout_in_minutes
                )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nat_gateway_idle_timeout

    def _get_outbound_type(
        self,
        enable_validation: bool = False,
        read_only: bool = False,
        load_balancer_profile: ManagedClusterLoadBalancerProfile = None,
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of outbound_type according to the context.

        Note: All the external parameters involved in the validation are not verified in their own getters.

        When outbound_type is not assigned, dynamic completion will be triggerd. By default, the value is set to
        CONST_OUTBOUND_TYPE_LOAD_BALANCER.

        This function supports the option of enable_validation. When enabled, if the value of outbound_type is
        CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY, CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY or
        CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING, the following checks will be performed. If load_balancer_sku is set
        to basic, an InvalidArgumentValueError will be raised. If vnet_subnet_id is not assigned,
        a RequiredArgumentMissingError will be raised. If any of load_balancer_managed_outbound_ip_count,
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
            self.mc.network_profile.outbound_type is not None
        ):
            outbound_type = self.mc.network_profile.outbound_type
            read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return outbound_type

        # dynamic completion
        if (
            not read_from_mc and
            outbound_type != CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY and
            outbound_type != CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY and
            outbound_type != CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING
        ):
            outbound_type = CONST_OUTBOUND_TYPE_LOAD_BALANCER

        # validation
        # Note: The parameters involved in the validation are not verified in their own getters.
        if enable_validation:
            if outbound_type in [
                CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY,
                CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY,
            ]:
                if safe_lower(self._get_load_balancer_sku(enable_validation=False)) == CONST_LOAD_BALANCER_SKU_BASIC:
                    raise InvalidArgumentValueError(
                        "userDefinedRouting doesn't support basic load balancer sku"
                    )

                if outbound_type in [
                    CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                    CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY,
                ]:
                    if self.get_vnet_subnet_id() in ["", None]:
                        raise RequiredArgumentMissingError(
                            "--vnet-subnet-id must be specified for userDefinedRouting and it must "
                            "be pre-configured with a route table with egress rules"
                        )

                if outbound_type == CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING:
                    if load_balancer_profile:
                        if (
                            load_balancer_profile.managed_outbound_i_ps or
                            load_balancer_profile.outbound_i_ps or
                            load_balancer_profile.outbound_ip_prefixes
                        ):
                            raise MutuallyExclusiveArgumentError(
                                "userDefinedRouting doesn't support customizing \
                                a standard load balancer with IP addresses"
                            )
                    else:
                        if (
                            self.get_load_balancer_managed_outbound_ip_count() or
                            self.get_load_balancer_outbound_ips() or
                            self.get_load_balancer_outbound_ip_prefixes()
                        ):
                            raise MutuallyExclusiveArgumentError(
                                "userDefinedRouting doesn't support customizing \
                                a standard load balancer with IP addresses"
                            )

        return outbound_type

    def get_outbound_type(
        self,
        load_balancer_profile: ManagedClusterLoadBalancerProfile = None
    ) -> Union[str, None]:
        """Dynamically obtain the value of outbound_type according to the context.

        Note: All the external parameters involved in the validation are not verified in their own getters.

        When outbound_type is not assigned, dynamic completion will be triggerd. By default, the value is set to
        CONST_OUTBOUND_TYPE_LOAD_BALANCER.

        This function will verify the parameter by default. If the value of outbound_type is
        CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING, the following checks will be performed. If load_balancer_sku is set
        to basic, an InvalidArgumentValueError will be raised. If vnet_subnet_id is not assigned,
        a RequiredArgumentMissingError will be raised. If any of load_balancer_managed_outbound_ip_count,
        load_balancer_outbound_ips or load_balancer_outbound_ip_prefixes is assigned, a MutuallyExclusiveArgumentError
        will be raised.

        This function supports the option of load_balancer_profile, if provided, when verifying loadbalancer-related
        parameters, the value in load_balancer_profile will be used for validation.

        :return: string or None
        """
        return self._get_outbound_type(
            enable_validation=True, load_balancer_profile=load_balancer_profile
        )

    def _get_network_plugin(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of network_plugin.

        Note: SDK provides default value "kubenet" for network_plugin.

        This function supports the option of enable_validation. When enabled, in case network_plugin is assigned, if
        pod_cidr is assigned and the value of network_plugin is azure, an InvalidArgumentValueError will be
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
            self.mc.network_profile.network_plugin is not None
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
            ) = self._get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
                enable_validation=False
            )
            if network_plugin:
                if network_plugin == "azure" and pod_cidr:
                    raise InvalidArgumentValueError(
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

        This function will verify the parameter by default. In case network_plugin is assigned, if pod_cidr is assigned
        and the value of network_plugin is azure, an InvalidArgumentValueError will be raised; otherwise, if any of
        pod_cidr, service_cidr, dns_service_ip, docker_bridge_address or network_policy is assigned, a
        RequiredArgumentMissingError will be raised.

        :return: string or None
        """

        return self._get_network_plugin(enable_validation=True)

    def _get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
        self, enable_validation: bool = False
    ) -> Tuple[
        Union[str, None],
        Union[str, None],
        Union[str, None],
        Union[str, None],
        Union[str, None],
    ]:
        """Internal function to obtain the value of pod_cidr, service_cidr, dns_service_ip, docker_bridge_address and
        network_policy.

        Note: SDK provides default value "10.244.0.0/16" and performs the following validation
        {'pattern': r'^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$'} for pod_cidr.
        Note: SDK provides default value "10.0.0.0/16" and performs the following validation
        {'pattern': r'^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$'} for service_cidr.
        Note: SDK provides default value "10.0.0.10" and performs the following validation
        {'pattern': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'}
        for dns_service_ip.
        Note: SDK provides default value "172.17.0.1/16" and performs the following validation
        {'pattern': r'^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$'} for docker_bridge_address.

        This function supports the option of enable_validation. When enabled, if pod_cidr is assigned and the value of
        network_plugin is azure, an InvalidArgumentValueError will be raised; otherwise, if any of pod_cidr,
        service_cidr, dns_service_ip, docker_bridge_address or network_policy is assigned, a
        RequiredArgumentMissingError will be raised.

        :return: a tuple of five elements: pod_cidr of string type or None, service_cidr of string type or None,
        dns_service_ip of string type or None, docker_bridge_address of string type or None, network_policy of
        string type or None.
        """
        # get network profile from `mc`
        network_profile = None
        if self.mc:
            network_profile = self.mc.network_profile

        # pod_cidr
        # read the original value passed by the command
        pod_cidr = self.raw_param.get("pod_cidr")
        # try to read the property value corresponding to the parameter from the `mc` object
        if network_profile and network_profile.pod_cidr is not None:
            pod_cidr = network_profile.pod_cidr

        # service_cidr
        # read the original value passed by the command
        service_cidr = self.raw_param.get("service_cidr")
        # try to read the property value corresponding to the parameter from the `mc` object
        if network_profile and network_profile.service_cidr is not None:
            service_cidr = network_profile.service_cidr

        # dns_service_ip
        # read the original value passed by the command
        dns_service_ip = self.raw_param.get("dns_service_ip")
        # try to read the property value corresponding to the parameter from the `mc` object
        if network_profile and network_profile.dns_service_ip is not None:
            dns_service_ip = network_profile.dns_service_ip

        # docker_bridge_address
        # read the original value passed by the command
        docker_bridge_address = self.raw_param.get("docker_bridge_address")
        # try to read the property value corresponding to the parameter from the `mc` object
        if network_profile and network_profile.docker_bridge_cidr is not None:
            docker_bridge_address = network_profile.docker_bridge_cidr

        # network_policy
        # read the original value passed by the command
        network_policy = self.raw_param.get("network_policy")
        # try to read the property value corresponding to the parameter from the `mc` object
        if network_profile and network_profile.network_policy is not None:
            network_policy = network_profile.network_policy

        # these parameters do not need dynamic completion

        # validation
        if enable_validation:
            network_plugin = self._get_network_plugin(enable_validation=False)
            if network_plugin:
                if network_plugin == "azure" and pod_cidr:
                    raise InvalidArgumentValueError(
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
        is azure, an InvalidArgumentValueError will be raised; otherwise, if any of pod_cidr, service_cidr,
        dns_service_ip, docker_bridge_address or network_policy is assigned, a RequiredArgumentMissingError will be
        raised.

        :return: a tuple of five elements: pod_cidr of string type or None, service_cidr of string type or None,
        dns_service_ip of string type or None, docker_bridge_address of string type or None, network_policy of
        string type or None.
        """
        return self._get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
            enable_validation=True
        )

    # pylint: disable=no-self-use
    def get_addon_consts(self) -> Dict[str, str]:
        """Helper function to obtain the constants used by addons.

        Note: This is not a parameter of aks commands.

        :return: dict
        """
        from azure.cli.command_modules.acs._consts import (
            ADDONS, CONST_ACC_SGX_QUOTE_HELPER_ENABLED,
            CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME,
            CONST_AZURE_POLICY_ADDON_NAME, CONST_CONFCOM_ADDON_NAME,
            CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
            CONST_INGRESS_APPGW_ADDON_NAME,
            CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
            CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME,
            CONST_INGRESS_APPGW_SUBNET_CIDR, CONST_INGRESS_APPGW_SUBNET_ID,
            CONST_INGRESS_APPGW_WATCH_NAMESPACE,
            CONST_KUBE_DASHBOARD_ADDON_NAME, CONST_MONITORING_ADDON_NAME,
            CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
            CONST_MONITORING_USING_AAD_MSI_AUTH,
            CONST_OPEN_SERVICE_MESH_ADDON_NAME, CONST_ROTATION_POLL_INTERVAL,
            CONST_SECRET_ROTATION_ENABLED, CONST_VIRTUAL_NODE_ADDON_NAME,
            CONST_VIRTUAL_NODE_SUBNET_NAME)

        addon_consts = {}
        addon_consts["ADDONS"] = ADDONS
        addon_consts[
            "CONST_ACC_SGX_QUOTE_HELPER_ENABLED"
        ] = CONST_ACC_SGX_QUOTE_HELPER_ENABLED
        addon_consts[
            "CONST_AZURE_POLICY_ADDON_NAME"
        ] = CONST_AZURE_POLICY_ADDON_NAME
        addon_consts["CONST_CONFCOM_ADDON_NAME"] = CONST_CONFCOM_ADDON_NAME
        addon_consts[
            "CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME"
        ] = CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME
        addon_consts[
            "CONST_INGRESS_APPGW_ADDON_NAME"
        ] = CONST_INGRESS_APPGW_ADDON_NAME
        addon_consts[
            "CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID"
        ] = CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID
        addon_consts[
            "CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME"
        ] = CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME
        addon_consts[
            "CONST_INGRESS_APPGW_SUBNET_CIDR"
        ] = CONST_INGRESS_APPGW_SUBNET_CIDR
        addon_consts[
            "CONST_INGRESS_APPGW_SUBNET_ID"
        ] = CONST_INGRESS_APPGW_SUBNET_ID
        addon_consts[
            "CONST_INGRESS_APPGW_WATCH_NAMESPACE"
        ] = CONST_INGRESS_APPGW_WATCH_NAMESPACE
        addon_consts[
            "CONST_KUBE_DASHBOARD_ADDON_NAME"
        ] = CONST_KUBE_DASHBOARD_ADDON_NAME
        addon_consts[
            "CONST_MONITORING_ADDON_NAME"
        ] = CONST_MONITORING_ADDON_NAME
        addon_consts[
            "CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID"
        ] = CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
        addon_consts[
            "CONST_OPEN_SERVICE_MESH_ADDON_NAME"
        ] = CONST_OPEN_SERVICE_MESH_ADDON_NAME
        addon_consts[
            "CONST_VIRTUAL_NODE_ADDON_NAME"
        ] = CONST_VIRTUAL_NODE_ADDON_NAME
        addon_consts[
            "CONST_VIRTUAL_NODE_SUBNET_NAME"
        ] = CONST_VIRTUAL_NODE_SUBNET_NAME
        addon_consts[
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME"
        ] = CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
        addon_consts[
            "CONST_SECRET_ROTATION_ENABLED"
        ] = CONST_SECRET_ROTATION_ENABLED
        addon_consts[
            "CONST_ROTATION_POLL_INTERVAL"
        ] = CONST_ROTATION_POLL_INTERVAL

        addon_consts[
            "CONST_MONITORING_USING_AAD_MSI_AUTH"
        ] = CONST_MONITORING_USING_AAD_MSI_AUTH
        return addon_consts

    def _get_enable_addons(self, enable_validation: bool = False) -> List[str]:
        """Internal function to obtain the value of enable_addons.

        Note: enable_addons will not be directly decorated into the `mc` object and we do not support to fetch it from
        `mc`.
        Note: Some of the external parameters involved in the validation are not verified in their own getters.

        This function supports the option of enable_validation. When enabled, it will check whether the provided addons
        have duplicate or invalid values, and raise an InvalidArgumentValueError if found. Besides, if monitoring is
        specified in enable_addons but workspace_resource_id is not assigned, or virtual-node is specified but
        aci_subnet_name or vnet_subnet_id is not, a RequiredArgumentMissingError will be raised.
        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.

        :return: empty list or list of strings
        """
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        valid_addon_keys = addon_consts.get("ADDONS").keys()

        # read the original value passed by the command
        enable_addons = self.raw_param.get("enable_addons")

        # normalize
        enable_addons = enable_addons.split(',') if enable_addons else []

        # validation
        if enable_validation:
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
            invalid_addons_set = enable_addons_set.difference(valid_addon_keys)
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

    def get_enable_addons(self) -> List[str]:
        """Obtain the value of enable_addons.

        Note: enable_addons will not be directly decorated into the `mc` object and we do not support to fetch it from
        `mc`.
        Note: Some of the external parameters involved in the validation are not verified in their own getters.

        This function will verify the parameters by default. It will check whether the provided addons have duplicate
        or invalid values, and raise an InvalidArgumentValueError if found. Besides, if monitoring is specified in
        enable_addons but workspace_resource_id is not assigned, or virtual-node is specified but aci_subnet_name or
        vnet_subnet_id is not, a RequiredArgumentMissingError will be raised.
        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.

        :return: empty list or list of strings
        """

        return self._get_enable_addons(enable_validation=True)

    def _get_workspace_resource_id(
        self, enable_validation: bool = False, read_only: bool = False
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of workspace_resource_id according to the context.

        When workspace_resource_id is not assigned, dynamic completion will be triggerd. Function
        "ensure_default_log_analytics_workspace_for_monitoring" will be called to create a workspace with
        subscription_id and resource_group_name, which internally used ResourceManagementClient to send the request.

        This function supports the option of enable_validation. When enabled, it will check if workspace_resource_id is
        assigned but 'monitoring' is not specified in enable_addons, if so, raise a RequiredArgumentMissingError.
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_MONITORING_ADDON_NAME = addon_consts.get("CONST_MONITORING_ADDON_NAME")
        CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID = addon_consts.get(
            "CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID"
        )

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
            ).config.get(CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID) is not None
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
                    self.external_functions.ensure_default_log_analytics_workspace_for_monitoring(
                        self.cmd,
                        self.get_subscription_id(),
                        self.get_resource_group_name(),
                    )
                )
            # normalize
            workspace_resource_id = "/" + workspace_resource_id.strip(" /")

        # validation
        if enable_validation:
            enable_addons = self._get_enable_addons(enable_validation=False)
            if workspace_resource_id and "monitoring" not in enable_addons:
                raise RequiredArgumentMissingError(
                    '"--workspace-resource-id" requires "--enable-addons monitoring".')

        # this parameter does not need validation
        return workspace_resource_id

    def get_workspace_resource_id(self) -> Union[str, None]:
        """Dynamically obtain the value of workspace_resource_id according to the context.

        When workspace_resource_id is not assigned, dynamic completion will be triggerd. Function
        "ensure_default_log_analytics_workspace_for_monitoring" will be called to create a workspace with
        subscription_id and resource_group_name, which internally used ResourceManagementClient to send the request.

        :return: string or None
        """
        return self._get_workspace_resource_id(enable_validation=True)

    def get_enable_msi_auth_for_monitoring(self) -> Union[bool, None]:
        """Obtain the value of enable_msi_auth_for_monitoring.

        Note: The arg type of this parameter supports three states (True, False or None), but the corresponding default
        value in entry function is not None.

        :return: bool or None
        """
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_MONITORING_ADDON_NAME = addon_consts.get("CONST_MONITORING_ADDON_NAME")
        CONST_MONITORING_USING_AAD_MSI_AUTH = addon_consts.get("CONST_MONITORING_USING_AAD_MSI_AUTH")

        # read the original value passed by the command
        enable_msi_auth_for_monitoring = self.raw_param.get("enable_msi_auth_for_monitoring")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_MONITORING_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_MONITORING_ADDON_NAME
            ).config.get(CONST_MONITORING_USING_AAD_MSI_AUTH) is not None
        ):
            enable_msi_auth_for_monitoring = (
                safe_lower(
                    self.mc.addon_profiles.get(CONST_MONITORING_ADDON_NAME).config.get(
                        CONST_MONITORING_USING_AAD_MSI_AUTH
                    )
                ) == "true"
            )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_msi_auth_for_monitoring

    # pylint: disable=no-self-use
    def get_virtual_node_addon_os_type(self) -> str:
        """Helper function to obtain the os_type of virtual node addon.

        Note: This is not a parameter of aks_create.

        :return: string
        """
        return "Linux"

    def get_aci_subnet_name(self) -> Union[str, None]:
        """Obtain the value of aci_subnet_name.

        :return: string or None
        """
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_VIRTUAL_NODE_ADDON_NAME = addon_consts.get("CONST_VIRTUAL_NODE_ADDON_NAME")
        CONST_VIRTUAL_NODE_SUBNET_NAME = addon_consts.get("CONST_VIRTUAL_NODE_SUBNET_NAME")

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
            ).config.get(CONST_VIRTUAL_NODE_SUBNET_NAME) is not None
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
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_INGRESS_APPGW_ADDON_NAME = addon_consts.get("CONST_INGRESS_APPGW_ADDON_NAME")
        CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME = addon_consts.get(
            "CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME"
        )

        # read the original value passed by the command
        appgw_name = self.raw_param.get("appgw_name")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME) is not None
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
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_INGRESS_APPGW_ADDON_NAME = addon_consts.get("CONST_INGRESS_APPGW_ADDON_NAME")
        CONST_INGRESS_APPGW_SUBNET_CIDR = addon_consts.get("CONST_INGRESS_APPGW_SUBNET_CIDR")

        # read the original value passed by the command
        appgw_subnet_cidr = self.raw_param.get("appgw_subnet_cidr")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_SUBNET_CIDR) is not None
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
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_INGRESS_APPGW_ADDON_NAME = addon_consts.get("CONST_INGRESS_APPGW_ADDON_NAME")
        CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID = addon_consts.get("CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID")

        # read the original value passed by the command
        appgw_id = self.raw_param.get("appgw_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID) is not None
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
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_INGRESS_APPGW_ADDON_NAME = addon_consts.get("CONST_INGRESS_APPGW_ADDON_NAME")
        CONST_INGRESS_APPGW_SUBNET_ID = addon_consts.get("CONST_INGRESS_APPGW_SUBNET_ID")

        # read the original value passed by the command
        appgw_subnet_id = self.raw_param.get("appgw_subnet_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_SUBNET_ID) is not None
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
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_INGRESS_APPGW_ADDON_NAME = addon_consts.get("CONST_INGRESS_APPGW_ADDON_NAME")
        CONST_INGRESS_APPGW_WATCH_NAMESPACE = addon_consts.get("CONST_INGRESS_APPGW_WATCH_NAMESPACE")

        # read the original value passed by the command
        appgw_watch_namespace = self.raw_param.get("appgw_watch_namespace")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_INGRESS_APPGW_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_INGRESS_APPGW_ADDON_NAME
            ).config.get(CONST_INGRESS_APPGW_WATCH_NAMESPACE) is not None
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
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_CONFCOM_ADDON_NAME = addon_consts.get("CONST_CONFCOM_ADDON_NAME")
        CONST_ACC_SGX_QUOTE_HELPER_ENABLED = addon_consts.get("CONST_ACC_SGX_QUOTE_HELPER_ENABLED")

        # read the original value passed by the command
        enable_sgxquotehelper = self.raw_param.get("enable_sgxquotehelper")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.addon_profiles and
            CONST_CONFCOM_ADDON_NAME in self.mc.addon_profiles and
            self.mc.addon_profiles.get(
                CONST_CONFCOM_ADDON_NAME
            ).config.get(CONST_ACC_SGX_QUOTE_HELPER_ENABLED) is not None
        ):
            enable_sgxquotehelper = self.mc.addon_profiles.get(
                CONST_CONFCOM_ADDON_NAME
            ).config.get(CONST_ACC_SGX_QUOTE_HELPER_ENABLED) == "true"

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_sgxquotehelper

    def _get_enable_secret_rotation(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_secret_rotation.

        This function supports the option of enable_validation. When enabled, in update mode, if enable_secret_rotation
        is specified but azure keyvault secret provider addon is not enabled, an InvalidArgumentValueError
        will be raised.

        :return: bool
        """
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME = addon_consts.get(
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME"
        )
        CONST_SECRET_ROTATION_ENABLED = addon_consts.get(
            "CONST_SECRET_ROTATION_ENABLED"
        )

        # read the original value passed by the command
        enable_secret_rotation = self.raw_param.get("enable_secret_rotation")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.addon_profiles and
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME in self.mc.addon_profiles and
                self.mc.addon_profiles.get(
                    CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
                ).config.get(CONST_SECRET_ROTATION_ENABLED) is not None
            ):
                enable_secret_rotation = self.mc.addon_profiles.get(
                    CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
                ).config.get(CONST_SECRET_ROTATION_ENABLED) == "true"

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.UPDATE:
                if enable_secret_rotation:
                    azure_keyvault_secrets_provider_enabled = (
                        self.mc and
                        self.mc.addon_profiles and
                        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME in self.mc.addon_profiles and
                        self.mc.addon_profiles.get(CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME).enabled
                    )
                    if not azure_keyvault_secrets_provider_enabled:
                        raise InvalidArgumentValueError(
                            "--enable-secret-rotation can only be specified "
                            "when azure-keyvault-secrets-provider is enabled"
                        )
        return enable_secret_rotation

    def get_enable_secret_rotation(self) -> bool:
        """Obtain the value of enable_secret_rotation.

        This function will verify the parameter by default. In update mode, if enable_secret_rotation is specified
        but azure keyvault secret provider addon is not enabled, an InvalidArgumentValueError will be raised.

        :return: bool
        """
        return self._get_enable_secret_rotation(enable_validation=True)

    def _get_disable_secret_rotation(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_secret_rotation.

        This function supports the option of enable_validation. When enabled, in update mode, if disable_secret_rotation
        is specified but azure keyvault secret provider addon is not enabled, an InvalidArgumentValueError
        will be raised.

        :return: bool
        """
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME = addon_consts.get(
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME"
        )

        # read the original value passed by the command
        disable_secret_rotation = self.raw_param.get("disable_secret_rotation")
        # We do not support this option in create mode, therefore we do not read the value from `mc`.

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.UPDATE:
                if disable_secret_rotation:
                    azure_keyvault_secrets_provider_enabled = (
                        self.mc and
                        self.mc.addon_profiles and
                        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME in self.mc.addon_profiles and
                        self.mc.addon_profiles.get(CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME).enabled
                    )
                    if not azure_keyvault_secrets_provider_enabled:
                        raise InvalidArgumentValueError(
                            "--disable-secret-rotation can only be specified "
                            "when azure-keyvault-secrets-provider is enabled"
                        )
        return disable_secret_rotation

    def get_disable_secret_rotation(self) -> bool:
        """Obtain the value of disable_secret_rotation.

        This function will verify the parameter by default. In update mode, if disable_secret_rotation is specified
        but azure keyvault secret provider addon is not enabled, an InvalidArgumentValueError will be raised.

        :return: bool
        """
        return self._get_disable_secret_rotation(enable_validation=True)

    def _get_rotation_poll_interval(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of rotation_poll_interval.

        This function supports the option of enable_validation. When enabled, in update mode, if rotation_poll_interval
        is specified but azure keyvault secret provider addon is not enabled, an InvalidArgumentValueError
        will be raised.

        :return: string or None
        """
        # determine the value of constants
        addon_consts = self.get_addon_consts()
        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME = addon_consts.get(
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME"
        )
        CONST_ROTATION_POLL_INTERVAL = addon_consts.get(
            "CONST_ROTATION_POLL_INTERVAL"
        )

        # read the original value passed by the command
        rotation_poll_interval = self.raw_param.get("rotation_poll_interval")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.addon_profiles and
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME in self.mc.addon_profiles and
                self.mc.addon_profiles.get(
                    CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
                ).config.get(CONST_ROTATION_POLL_INTERVAL) is not None
            ):
                rotation_poll_interval = self.mc.addon_profiles.get(
                    CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
                ).config.get(CONST_ROTATION_POLL_INTERVAL)

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.UPDATE:
                if rotation_poll_interval:
                    azure_keyvault_secrets_provider_enabled = (
                        self.mc and
                        self.mc.addon_profiles and
                        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME in self.mc.addon_profiles and
                        self.mc.addon_profiles.get(CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME).enabled
                    )
                    if not azure_keyvault_secrets_provider_enabled:
                        raise InvalidArgumentValueError(
                            "--rotation-poll-interval can only be specified "
                            "when azure-keyvault-secrets-provider is enabled"
                        )
        return rotation_poll_interval

    def get_rotation_poll_interval(self) -> Union[str, None]:
        """Obtain the value of rotation_poll_interval.

        This function will verify the parameter by default. In update mode, if rotation_poll_interval is specified
        but azure keyvault secret provider addon is not enabled, an InvalidArgumentValueError will be raised.

        :return: string or None
        """
        return self._get_rotation_poll_interval(enable_validation=True)

    def _get_enable_aad(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_aad.

        This function supports the option of enable_validation. When enabled, in create mode, if the value of
        enable_aad is True and any of aad_client_app_id, aad_server_app_id or aad_server_app_secret is asssigned, a
        MutuallyExclusiveArgumentError will be raised. If the value of enable_aad is False and the value of
        enable_azure_rbac is True, a RequiredArgumentMissingError will be raised. In update mode, if enable_aad is
        specified and managed aad has been enabled, an InvalidArgumentValueError will be raised.

        :return: bool
        """
        # read the original value passed by the command
        enable_aad = self.raw_param.get("enable_aad")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.aad_profile and
                self.mc.aad_profile.managed is not None
            ):
                enable_aad = self.mc.aad_profile.managed

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                (
                    aad_client_app_id,
                    aad_server_app_id,
                    aad_server_app_secret,
                ) = self._get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(
                    enable_validation=False
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
            elif self.decorator_mode == DecoratorMode.UPDATE:
                if enable_aad:
                    if (
                        self.mc and
                        self.mc.aad_profile is not None and
                        self.mc.aad_profile.managed
                    ):
                        raise InvalidArgumentValueError(
                            'Cannot specify "--enable-aad" if managed AAD is already enabled'
                        )
        return enable_aad

    def get_enable_aad(self) -> bool:
        """Obtain the value of enable_aad.

        This function will verify the parameter by default. In create mode, if the value of enable_aad is True and
        any of aad_client_app_id, aad_server_app_id or aad_server_app_secret is asssigned, a
        MutuallyExclusiveArgumentError will be raised. If the value of enable_aad is False and the value of
        enable_azure_rbac is True, a RequiredArgumentMissingError will be raised. In update mode, if enable_aad is
        specified and managed aad has been enabled, an InvalidArgumentValueError will be raised.

        :return: bool
        """

        return self._get_enable_aad(enable_validation=True)

    def _get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(
        self, enable_validation: bool = False
    ) -> Tuple[Union[str, None], Union[str, None], Union[str, None]]:
        """Internal function to obtain the value of aad_client_app_id, aad_server_app_id and aad_server_app_secret.

        This function supports the option of enable_validation. When enabled, if the value of enable_aad is True and any
        of aad_client_app_id, aad_server_app_id or aad_server_app_secret is asssigned, a MutuallyExclusiveArgumentError
        will be raised.

        :return: a tuple of three elements: aad_client_app_id of string type or None, aad_server_app_id of string type
        or None and aad_server_app_secret of string type or None.
        """
        # get aad profile from `mc`
        aad_profile = None
        if self.mc:
            aad_profile = self.mc.aad_profile

        # read the original value passed by the command
        aad_client_app_id = self.raw_param.get("aad_client_app_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if aad_profile and aad_profile.client_app_id is not None:
            aad_client_app_id = aad_profile.client_app_id

        # read the original value passed by the command
        aad_server_app_id = self.raw_param.get("aad_server_app_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if aad_profile and aad_profile.server_app_id is not None:
            aad_server_app_id = aad_profile.server_app_id

        # read the original value passed by the command
        aad_server_app_secret = self.raw_param.get("aad_server_app_secret")
        # try to read the property value corresponding to the parameter from the `mc` object
        if aad_profile and aad_profile.server_app_secret is not None:
            aad_server_app_secret = aad_profile.server_app_secret

        # these parameters do not need dynamic completion

        # validation
        if enable_validation:
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
        return self._get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(enable_validation=True)

    def _get_aad_tenant_id(
        self, enable_validation: bool = False, read_only: bool = False
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of aad_server_app_secret according to the context.
        When both aad_tenant_id and enable_aad are not assigned, and any of aad_client_app_id, aad_server_app_id or
        aad_server_app_secret is asssigned, dynamic completion will be triggerd. Class
        "azure.cli.core._profile.Profile" will be instantiated, and then call its "get_login_credentials" method to
        get the tenant of the deployment subscription.

        This function supports the option of enable_validation. When enabled in update mode, if aad_tenant_id
        is specified, while aad_profile is not set or managed aad is not enabled, raise an InvalidArgumentValueError.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.
        :return: string or None
        """
        # read the original value passed by the command
        aad_tenant_id = self.raw_param.get("aad_tenant_id")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        read_from_mc = False
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.aad_profile and
                self.mc.aad_profile.tenant_id is not None
            ):
                aad_tenant_id = self.mc.aad_profile.tenant_id
                read_from_mc = True

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return aad_tenant_id

        # dynamic completion for create mode only
        if self.decorator_mode == DecoratorMode.CREATE:
            if not read_from_mc and not self._get_enable_aad(
                enable_validation=False
            ):
                if aad_tenant_id is None and any(
                    self._get_aad_client_app_id_and_aad_server_app_id_and_aad_server_app_secret(enable_validation=False)
                ):
                    profile = Profile(cli_ctx=self.cmd.cli_ctx)
                    _, _, aad_tenant_id = profile.get_login_credentials()

        # validation
        if enable_validation:
            if aad_tenant_id:
                if self.decorator_mode == DecoratorMode.UPDATE:
                    if self.mc is None or self.mc.aad_profile is None or not self.mc.aad_profile.managed:
                        raise InvalidArgumentValueError(
                            'Cannot specify "--aad-tenant-id" if managed AAD is not enabled'
                        )
        return aad_tenant_id

    def get_aad_tenant_id(self) -> Union[str, None]:
        """Dynamically obtain the value of aad_server_app_secret according to the context.
        When both aad_tenant_id and enable_aad are not assigned, and any of aad_client_app_id, aad_server_app_id or
        aad_server_app_secret is asssigned, dynamic completion will be triggerd. Class
        "azure.cli.core._profile.Profile" will be instantiated, and then call its "get_login_credentials" method to
        get the tenant of the deployment subscription.

        This function will verify the parameter by default. In update mode, if aad_tenant_id is specified,
        while aad_profile is not set or managed aad is not enabled, raise an InvalidArgumentValueError.

        :return: string or None
        """
        return self._get_aad_tenant_id(enable_validation=True)

    def _get_aad_admin_group_object_ids(self, enable_validation: bool = False) -> Union[List[str], None]:
        """Internal function to obtain the value of aad_admin_group_object_ids.

        This function supports the option of enable_validation. When enabled in update mode, if
        aad_admin_group_object_ids is specified, while aad_profile is not set or managed aad is not enabled,
        raise an InvalidArgumentValueError.

        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.
        :return: empty list or list of strings, or None
        """
        # read the original value passed by the command
        aad_admin_group_object_ids = self.raw_param.get("aad_admin_group_object_ids")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        read_from_mc = False
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.aad_profile and
                self.mc.aad_profile.admin_group_object_i_ds is not None
            ):
                aad_admin_group_object_ids = self.mc.aad_profile.admin_group_object_i_ds
                read_from_mc = True

        # keep None as None, but empty string ("") to empty list ([])
        if not read_from_mc and aad_admin_group_object_ids is not None:
            aad_admin_group_object_ids = aad_admin_group_object_ids.split(',') if aad_admin_group_object_ids else []

        # validation
        if enable_validation:
            if aad_admin_group_object_ids:
                if self.decorator_mode == DecoratorMode.UPDATE:
                    if self.mc is None or self.mc.aad_profile is None or not self.mc.aad_profile.managed:
                        raise InvalidArgumentValueError(
                            'Cannot specify "--aad-admin-group-object-ids" if managed AAD is not enabled'
                        )

        return aad_admin_group_object_ids

    def get_aad_admin_group_object_ids(self) -> Union[List[str], None]:
        """Obtain the value of aad_admin_group_object_ids.

        This function will verify the parameter by default. In update mode, if aad_admin_group_object_ids is specified,
        while aad_profile is not set or managed aad is not enabled, raise an InvalidArgumentValueError.

        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.

        :return: empty list or list of strings, or None
        """
        return self._get_aad_admin_group_object_ids(enable_validation=True)

    def _get_disable_rbac(self, enable_validation: bool = False) -> Union[bool, None]:
        """Internal function to obtain the value of disable_rbac.

        This function supports the option of enable_validation. When enabled, if the values of disable_rbac and
        enable_azure_rbac are both True, a MutuallyExclusiveArgumentError will be raised. Besides, if the values of
        enable_rbac and disable_rbac are both True, a MutuallyExclusiveArgumentError will be raised.

        :return: bool or None
        """
        # read the original value passed by the command
        disable_rbac = self.raw_param.get("disable_rbac")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.enable_rbac is not None
        ):
            disable_rbac = not self.mc.enable_rbac

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if disable_rbac and self._get_enable_azure_rbac(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "--enable-azure-rbac cannot be used together with --disable-rbac"
                )
            if disable_rbac and self._get_enable_rbac(enable_validation=False):
                raise MutuallyExclusiveArgumentError("specify either '--disable-rbac' or '--enable-rbac', not both.")
        return disable_rbac

    def get_disable_rbac(self) -> Union[bool, None]:
        """Obtain the value of disable_rbac.

        This function will verify the parameter by default. If the values of disable_rbac and enable_azure_rbac are
        both True, a MutuallyExclusiveArgumentError will be raised. Besides, if the values of enable_rbac and
        disable_rbac are both True, a MutuallyExclusiveArgumentError will be raised.

        :return: bool or None
        """

        return self._get_disable_rbac(enable_validation=True)

    def _get_enable_rbac(self, enable_validation: bool = False) -> Union[bool, None]:
        """Internal function to obtain the value of enable_rbac.

        This function supports the option of enable_validation. When enabled, if the values of enable_rbac and
        disable_rbac are both True, a MutuallyExclusiveArgumentError will be raised.

        :return: bool or None
        """
        # read the original value passed by the command
        enable_rbac = self.raw_param.get("enable_rbac")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.enable_rbac is not None
        ):
            enable_rbac = self.mc.enable_rbac

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if enable_rbac and self._get_disable_rbac(enable_validation=False):
                raise MutuallyExclusiveArgumentError("specify either '--disable-rbac' or '--enable-rbac', not both.")
        return enable_rbac

    def get_enable_rbac(self) -> Union[bool, None]:
        """Obtain the value of enable_rbac.

        This function will verify the parameter by default. If the values of enable_rbac and disable_rbac are both True,
        a MutuallyExclusiveArgumentError will be raised.

        :return: bool or None
        """
        return self._get_enable_rbac(enable_validation=True)

    def _get_enable_azure_rbac(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_azure_rbac.

        This function supports the option of enable_validation. When enabled and enable_azure_rbac is specified,
        in create mode, if the value of enable_aad is not True, a RequiredArgumentMissingError will be raised.
        If disable_rbac is specified, a MutuallyExclusiveArgumentError will be raised. In update mode, if
        enable_azure_rbac is specified, while aad_profile is not set or managed aad is not enabled,
        raise an InvalidArgumentValueError. If both disable_azure_rbac and enable_azure_rbac are specified,
        raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        enable_azure_rbac = self.raw_param.get("enable_azure_rbac")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.aad_profile and
                self.mc.aad_profile.enable_azure_rbac is not None
            ):
                enable_azure_rbac = self.mc.aad_profile.enable_azure_rbac

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if enable_azure_rbac:
                if self.decorator_mode == DecoratorMode.CREATE:
                    if not self._get_enable_aad(enable_validation=False):
                        raise RequiredArgumentMissingError(
                            "--enable-azure-rbac can only be used together with --enable-aad"
                        )
                    if self._get_disable_rbac(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            "--enable-azure-rbac cannot be used together with --disable-rbac"
                        )
                elif self.decorator_mode == DecoratorMode.UPDATE:
                    if self.mc is None or self.mc.aad_profile is None or not self.mc.aad_profile.managed:
                        raise InvalidArgumentValueError(
                            'Cannot specify "--enable-azure-rbac" if managed AAD is not enabled'
                        )
                    if self._get_disable_azure_rbac(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            'Cannot specify "--enable-azure-rbac" and "--disable-azure-rbac" at the same time'
                        )
        return enable_azure_rbac

    def get_enable_azure_rbac(self) -> bool:
        """Obtain the value of enable_azure_rbac.

        This function will verify the parameter by default. If enable_azure_rbac is specified, in create mode,
        if the value of enable_aad is not True, a RequiredArgumentMissingError will be raised. If disable_rbac
        is specified, a MutuallyExclusiveArgumentError will be raised. In update mode, if enable_azure_rbac
        is specified, while aad_profile is not set or managed aad is not enabled, raise an InvalidArgumentValueError.
        If both disable_azure_rbac and enable_azure_rbac are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """

        return self._get_enable_azure_rbac(enable_validation=True)

    def _get_disable_azure_rbac(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_azure_rbac.

        This function supports the option of enable_validation. When enabled, in update mode, if disable_azure_rbac
        is specified, while aad_profile is not set or managed aad is not enabled, raise an InvalidArgumentValueError.
        If both disable_azure_rbac and enable_azure_rbac are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        disable_azure_rbac = self.raw_param.get("disable_azure_rbac")
        # We do not support this option in create mode, therefore we do not read the value from `mc`.

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if disable_azure_rbac:
                if self.decorator_mode == DecoratorMode.UPDATE:
                    if self.mc is None or self.mc.aad_profile is None or not self.mc.aad_profile.managed:
                        raise InvalidArgumentValueError(
                            'Cannot specify "--disable-azure-rbac" if managed AAD is not enabled'
                        )
                    if self._get_enable_azure_rbac(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            'Cannot specify "--enable-azure-rbac" and "--disable-azure-rbac" at the same time'
                        )
        return disable_azure_rbac

    def get_disable_azure_rbac(self) -> bool:
        """Obtain the value of disable_azure_rbac.

        This function will verify the parameter by default. In update mode, if disable_azure_rbac is specified,
        while aad_profile is not set or managed aad is not enabled, raise an InvalidArgumentValueError.
        If both disable_azure_rbac and enable_azure_rbac are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_disable_azure_rbac(enable_validation=True)

    def _get_api_server_authorized_ip_ranges(self, enable_validation: bool = False) -> List[str]:
        """Internal function to obtain the value of api_server_authorized_ip_ranges.

        This function supports the option of enable_validation. When enabled and api_server_authorized_ip_ranges is
        assigned, if load_balancer_sku equals to CONST_LOAD_BALANCER_SKU_BASIC, raise an InvalidArgumentValueError;
        if enable_private_cluster is specified, raise a MutuallyExclusiveArgumentError.
        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.

        :return: empty list or list of strings
        """
        # read the original value passed by the command
        api_server_authorized_ip_ranges = self.raw_param.get(
            "api_server_authorized_ip_ranges"
        )
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            read_from_mc = False
            if (
                self.mc and
                self.mc.api_server_access_profile and
                self.mc.api_server_access_profile.authorized_ip_ranges is not None
            ):
                api_server_authorized_ip_ranges = (
                    self.mc.api_server_access_profile.authorized_ip_ranges
                )
                read_from_mc = True

            # normalize
            if not read_from_mc:
                api_server_authorized_ip_ranges = [
                    x.strip()
                    for x in (
                        api_server_authorized_ip_ranges.split(",")
                        if api_server_authorized_ip_ranges
                        else []
                    )
                ]
        elif self.decorator_mode == DecoratorMode.UPDATE:
            # normalize, keep None as None
            if api_server_authorized_ip_ranges is not None:
                api_server_authorized_ip_ranges = [
                    x.strip()
                    for x in (
                        api_server_authorized_ip_ranges.split(",")
                        if api_server_authorized_ip_ranges
                        else []
                    )
                ]

        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                if api_server_authorized_ip_ranges:
                    if (
                        safe_lower(self._get_load_balancer_sku(enable_validation=False)) ==
                        CONST_LOAD_BALANCER_SKU_BASIC
                    ):
                        raise InvalidArgumentValueError(
                            "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                        )
                    if self._get_enable_private_cluster(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            "--api-server-authorized-ip-ranges is not supported for private cluster"
                        )
            elif self.decorator_mode == DecoratorMode.UPDATE:
                if api_server_authorized_ip_ranges:
                    if check_is_private_cluster(self.mc):
                        raise MutuallyExclusiveArgumentError(
                            "--api-server-authorized-ip-ranges is not supported for private cluster"
                        )
        return api_server_authorized_ip_ranges

    def get_api_server_authorized_ip_ranges(self) -> List[str]:
        """Obtain the value of api_server_authorized_ip_ranges.

        This function will verify the parameter by default. When api_server_authorized_ip_ranges is assigned, if
        load_balancer_sku equals to CONST_LOAD_BALANCER_SKU_BASIC, raise an InvalidArgumentValueError; if
        enable_private_cluster is specified, raise a MutuallyExclusiveArgumentError.
        This function will normalize the parameter by default. It will split the string into a list with "," as the
        delimiter.

        :return: empty list or list of strings
        """
        return self._get_api_server_authorized_ip_ranges(enable_validation=True)

    def _get_fqdn_subdomain(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of fqdn_subdomain.

        This function supports the option of enable_validation. When enabled, it will check if both dns_name_prefix and
        fqdn_subdomain are assigend, if so, raise the MutuallyExclusiveArgumentError. It will also check when both
        private_dns_zone and fqdn_subdomain are assigned, if the value of private_dns_zone is
        CONST_PRIVATE_DNS_ZONE_SYSTEM, raise an InvalidArgumentValueError; Otherwise if the value of private_dns_zone
        is not a valid resource ID, raise an InvalidArgumentValueError.

        :return: string or None
        """
        # read the original value passed by the command
        fqdn_subdomain = self.raw_param.get("fqdn_subdomain")
        # try to read the property value corresponding to the parameter from the `mc` object
        # Backward Compatibility: We also support api version v2020.11.01 in profile 2020-09-01-hybrid and there is
        # no such attribute.
        if (
            self.mc and
            hasattr(self.mc, "fqdn_subdomain") and
            self.mc.fqdn_subdomain is not None
        ):
            fqdn_subdomain = self.mc.fqdn_subdomain

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if fqdn_subdomain:
                if self._get_dns_name_prefix(read_only=True):
                    raise MutuallyExclusiveArgumentError(
                        "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                    )
                private_dns_zone = self._get_private_dns_zone(enable_validation=False)
                if private_dns_zone:
                    if private_dns_zone.lower() != CONST_PRIVATE_DNS_ZONE_SYSTEM:
                        if not is_valid_resource_id(private_dns_zone):
                            raise InvalidArgumentValueError(
                                private_dns_zone + " is not a valid Azure resource ID."
                            )
                    else:
                        raise InvalidArgumentValueError(
                            "--fqdn-subdomain should only be used for private cluster with custom private dns zone"
                        )
        return fqdn_subdomain

    def get_fqdn_subdomain(self) -> Union[str, None]:
        """Obtain the value of fqdn_subdomain.

        This function will verify the parameter by default. It will check if both dns_name_prefix and fqdn_subdomain
        are assigend, if so, raise the MutuallyExclusiveArgumentError. It will also check when both private_dns_zone
        and fqdn_subdomain are assigned, if the value of private_dns_zone is CONST_PRIVATE_DNS_ZONE_SYSTEM, raise an
        InvalidArgumentValueError; Otherwise if the value of private_dns_zone is not a valid resource ID, raise an
        InvalidArgumentValueError.

        :return: string or None
        """

        return self._get_fqdn_subdomain(enable_validation=True)

    def _get_enable_private_cluster(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_private_cluster.

        This function supports the option of enable_validation. When enabled and enable_private_cluster is specified,
        if load_balancer_sku equals to basic, raise an InvalidArgumentValueError; if api_server_authorized_ip_ranges
        is assigned, raise an MutuallyExclusiveArgumentError; Otherwise when enable_private_cluster is not specified
        and disable_public_fqdn, enable_public_fqdn or private_dns_zone is assigned, raise an InvalidArgumentValueError.

        :return: bool
        """
        # read the original value passed by the command
        enable_private_cluster = self.raw_param.get("enable_private_cluster")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.api_server_access_profile and
                self.mc.api_server_access_profile.enable_private_cluster is not None
            ):
                enable_private_cluster = self.mc.api_server_access_profile.enable_private_cluster

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                if enable_private_cluster:
                    if (
                        safe_lower(self._get_load_balancer_sku(enable_validation=False)) ==
                        CONST_LOAD_BALANCER_SKU_BASIC
                    ):
                        raise InvalidArgumentValueError(
                            "Please use standard load balancer for private cluster"
                        )
                    if self._get_api_server_authorized_ip_ranges(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            "--api-server-authorized-ip-ranges is not supported for private cluster"
                        )
                else:
                    if self._get_disable_public_fqdn(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "--disable-public-fqdn should only be used with --enable-private-cluster"
                        )
                    if self._get_private_dns_zone(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "Invalid private dns zone for public cluster. It should always be empty for public cluster"
                        )
            elif self.decorator_mode == DecoratorMode.UPDATE:
                is_private_cluster = check_is_private_cluster(self.mc)
                if is_private_cluster:
                    if self._get_api_server_authorized_ip_ranges(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            "--api-server-authorized-ip-ranges is not supported for private cluster"
                        )
                else:
                    if self._get_disable_public_fqdn(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "--disable-public-fqdn can only be used for private cluster"
                        )
                    if self._get_enable_public_fqdn(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "--enable-public-fqdn can only be used for private cluster"
                        )
        return enable_private_cluster

    def get_enable_private_cluster(self) -> bool:
        """Obtain the value of enable_private_cluster.

        This function will verify the parameter by default. When enable_private_cluster is specified, if
        load_balancer_sku equals to basic, raise an InvalidArgumentValueError; if api_server_authorized_ip_ranges
        is assigned, raise an MutuallyExclusiveArgumentError; Otherwise when enable_private_cluster is not specified
        and disable_public_fqdn, enable_public_fqdn or private_dns_zone is assigned, raise an InvalidArgumentValueError.

        :return: bool
        """

        return self._get_enable_private_cluster(enable_validation=True)

    def _get_disable_public_fqdn(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_public_fqdn.

        This function supports the option of enable_validation. When enabled, if enable_private_cluster is not specified
        and disable_public_fqdn is assigned, raise an InvalidArgumentValueError. If both disable_public_fqdn and
        enable_public_fqdn are assigned, raise a MutuallyExclusiveArgumentError. In update mode, if
        disable_public_fqdn is assigned and private_dns_zone equals to CONST_PRIVATE_DNS_ZONE_NONE, raise an
        InvalidArgumentValueError.

        :return: bool
        """
        # read the original value passed by the command
        disable_public_fqdn = self.raw_param.get("disable_public_fqdn")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.api_server_access_profile and
                self.mc.api_server_access_profile.enable_private_cluster_public_fqdn is not None
            ):
                disable_public_fqdn = not self.mc.api_server_access_profile.enable_private_cluster_public_fqdn

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                if disable_public_fqdn and not self._get_enable_private_cluster(enable_validation=False):
                    raise InvalidArgumentValueError(
                        "--disable-public-fqdn should only be used with --enable-private-cluster"
                    )
            if self.decorator_mode == DecoratorMode.UPDATE:
                if disable_public_fqdn:
                    if self._get_enable_public_fqdn(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            "Cannot specify '--enable-public-fqdn' and '--disable-public-fqdn' at the same time"
                        )
                    if safe_lower(self._get_private_dns_zone(enable_validation=False)) == CONST_PRIVATE_DNS_ZONE_NONE:
                        raise InvalidArgumentValueError(
                            "--disable-public-fqdn cannot be applied for none mode private dns zone cluster"
                        )
                    if not check_is_private_cluster(self.mc):
                        raise InvalidArgumentValueError(
                            "--disable-public-fqdn can only be used for private cluster"
                        )

        return disable_public_fqdn

    def get_disable_public_fqdn(self) -> bool:
        """Obtain the value of disable_public_fqdn.

        This function will verify the parameter by default. If enable_private_cluster is not specified and
        disable_public_fqdn is assigned, raise an InvalidArgumentValueError. If both disable_public_fqdn and
        enable_public_fqdn are assigned, raise a MutuallyExclusiveArgumentError. In update mode, if
        disable_public_fqdn is assigned and private_dns_zone equals to CONST_PRIVATE_DNS_ZONE_NONE, raise an
        InvalidArgumentValueError.

        :return: bool
        """
        return self._get_disable_public_fqdn(enable_validation=True)

    def _get_enable_public_fqdn(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_public_fqdn.

        This function supports the option of enable_validation. When enabled, if private cluster is not enabled and
        enable_public_fqdn is assigned, raise an InvalidArgumentValueError. If both disable_public_fqdn and
        enable_public_fqdn are assigned, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        enable_public_fqdn = self.raw_param.get("enable_public_fqdn")
        # We do not support this option in create mode, therefore we do not read the value from `mc`.

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.UPDATE:
                if enable_public_fqdn:
                    if self._get_disable_public_fqdn(enable_validation=False):
                        raise MutuallyExclusiveArgumentError(
                            "Cannot specify '--enable-public-fqdn' and '--disable-public-fqdn' at the same time"
                        )
                    if not check_is_private_cluster(self.mc):
                        raise InvalidArgumentValueError(
                            "--enable-public-fqdn can only be used for private cluster"
                        )
        return enable_public_fqdn

    def get_enable_public_fqdn(self) -> bool:
        """Obtain the value of enable_public_fqdn.

        This function will verify the parameter by default. If private cluster is not enabled and enable_public_fqdn
        is assigned, raise an InvalidArgumentValueError. If both disable_public_fqdn and enable_private_cluster are
        assigned, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_enable_public_fqdn(enable_validation=True)

    def _get_private_dns_zone(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of private_dns_zone.

        This function supports the option of enable_validation. When enabled and private_dns_zone is assigned, if
        enable_private_cluster is not specified raise an InvalidArgumentValueError. It will also check when both
        private_dns_zone and fqdn_subdomain are assigned, if the value of private_dns_zone is
        CONST_PRIVATE_DNS_ZONE_SYSTEM or CONST_PRIVATE_DNS_ZONE_NONE, raise an InvalidArgumentValueError; Otherwise if
        the value of private_dns_zone is not a valid resource ID, raise an InvalidArgumentValueError. In update mode,
        if disable_public_fqdn is assigned and private_dns_zone equals to CONST_PRIVATE_DNS_ZONE_NONE, raise an
        InvalidArgumentValueError.

        :return: string or None
        """
        # read the original value passed by the command
        private_dns_zone = self.raw_param.get("private_dns_zone")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.api_server_access_profile and
            self.mc.api_server_access_profile.private_dns_zone is not None
        ):
            private_dns_zone = self.mc.api_server_access_profile.private_dns_zone

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                if private_dns_zone:
                    if not self._get_enable_private_cluster(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "Invalid private dns zone for public cluster. It should always be empty for public cluster"
                        )
                    if (
                        private_dns_zone.lower() != CONST_PRIVATE_DNS_ZONE_SYSTEM and
                        private_dns_zone.lower() != CONST_PRIVATE_DNS_ZONE_NONE
                    ):
                        if not is_valid_resource_id(private_dns_zone):
                            raise InvalidArgumentValueError(
                                private_dns_zone + " is not a valid Azure resource ID."
                            )
                    else:
                        if self._get_fqdn_subdomain(enable_validation=False):
                            raise InvalidArgumentValueError(
                                "--fqdn-subdomain should only be used for private cluster with custom private dns zone"
                            )
            elif self.decorator_mode == DecoratorMode.UPDATE:
                if (
                    self.mc and
                    self.mc.api_server_access_profile and
                    self.mc.api_server_access_profile.private_dns_zone == CONST_PRIVATE_DNS_ZONE_NONE
                ):
                    if self._get_disable_public_fqdn(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "--disable-public-fqdn cannot be applied for none mode private dns zone cluster"
                        )
        return private_dns_zone

    def get_private_dns_zone(self) -> Union[str, None]:
        """Obtain the value of private_dns_zone.

        This function will verify the parameter by default. When private_dns_zone is assigned, if enable_private_cluster
        is not specified raise an InvalidArgumentValueError. It will also check when both private_dns_zone and
        fqdn_subdomain are assigned, if the value of private_dns_zone is CONST_PRIVATE_DNS_ZONE_SYSTEM or
        CONST_PRIVATE_DNS_ZONE_NONE, raise an InvalidArgumentValueError; Otherwise if the value of private_dns_zone is
        not a valid resource ID, raise an InvalidArgumentValueError. In update mode, if disable_public_fqdn is assigned
        and private_dns_zone equals to CONST_PRIVATE_DNS_ZONE_NONE, raise an InvalidArgumentValueError.

        :return: string or None
        """
        return self._get_private_dns_zone(enable_validation=True)

    def _get_assign_kubelet_identity(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of assign_kubelet_identity.

        This function supports the option of enable_validation. When enabled, if assign_identity is not assigned but
        assign_kubelet_identity is, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """
        # read the original value passed by the command
        assign_kubelet_identity = self.raw_param.get("assign_kubelet_identity")
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.identity_profile and
            self.mc.identity_profile.get("kubeletidentity", None) and
            getattr(self.mc.identity_profile.get("kubeletidentity"), "resource_id") is not None
        ):
            assign_kubelet_identity = getattr(self.mc.identity_profile.get("kubeletidentity"), "resource_id")

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if assign_kubelet_identity and not self._get_assign_identity(enable_validation=False):
                raise RequiredArgumentMissingError(
                    "--assign-kubelet-identity can only be specified when --assign-identity is specified"
                )
        return assign_kubelet_identity

    def get_assign_kubelet_identity(self) -> Union[str, None]:
        """Obtain the value of assign_kubelet_identity.

        This function will verify the parameter by default. If assign_identity is not assigned but
        assign_kubelet_identity is, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """
        return self._get_assign_kubelet_identity(enable_validation=True)

    def get_auto_upgrade_channel(self) -> Union[str, None]:
        """Obtain the value of auto_upgrade_channel.

        :return: string or None
        """
        # read the original value passed by the command
        auto_upgrade_channel = self.raw_param.get("auto_upgrade_channel")

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.auto_upgrade_profile and
                self.mc.auto_upgrade_profile.upgrade_channel is not None
            ):
                auto_upgrade_channel = self.mc.auto_upgrade_profile.upgrade_channel

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return auto_upgrade_channel

    def _get_cluster_autoscaler_profile(self, read_only: bool = False) -> Union[Dict[str, str], None]:
        """Internal function to dynamically obtain the value of cluster_autoscaler_profile according to the context.

        This function will call function "__validate_cluster_autoscaler_profile" to parse and verify the parameter
        by default.

        In update mode, when cluster_autoscaler_profile is assigned and auto_scaler_profile in the `mc` object has also
        been set, dynamic completion will be triggerd. We will first make a copy of the original configuration
        (extract the dictionary from the ManagedClusterPropertiesAutoScalerProfile object), and then update the copied
        dictionary with the dictionary of new options.

        :return: dictionary or None
        """
        # read the original value passed by the command
        cluster_autoscaler_profile = self.raw_param.get("cluster_autoscaler_profile")
        # parse and validate user input
        cluster_autoscaler_profile = self.__validate_cluster_autoscaler_profile(cluster_autoscaler_profile)

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.mc and self.mc.auto_scaler_profile is not None:
                cluster_autoscaler_profile = self.mc.auto_scaler_profile

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return cluster_autoscaler_profile

        # dynamic completion for update mode only
        if not read_only and self.decorator_mode == DecoratorMode.UPDATE:
            if cluster_autoscaler_profile and self.mc and self.mc.auto_scaler_profile:
                # shallow copy should be enough for string-to-string dictionary
                copy_of_raw_dict = self.mc.auto_scaler_profile.__dict__.copy()
                new_options_dict = dict(
                    (key.replace("-", "_"), value)
                    for (key, value) in cluster_autoscaler_profile.items()
                )
                copy_of_raw_dict.update(new_options_dict)
                cluster_autoscaler_profile = copy_of_raw_dict

        # this parameter does not need validation
        return cluster_autoscaler_profile

    def get_cluster_autoscaler_profile(self) -> Union[Dict[str, str], None]:
        """Dynamically obtain the value of cluster_autoscaler_profile according to the context.

        This function will call function "__validate_cluster_autoscaler_profile" to parse and verify the parameter
        by default.

        In update mode, when cluster_autoscaler_profile is assigned and auto_scaler_profile in the `mc` object has also
        been set, dynamic completion will be triggerd. We will first make a copy of the original configuration
        (extract the dictionary from the ManagedClusterPropertiesAutoScalerProfile object), and then update the copied
        dictionary with the dictionary of new options.

        :return: dictionary or None
        """
        return self._get_cluster_autoscaler_profile()

    def _get_uptime_sla(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of uptime_sla.

        This function supports the option of enable_validation. When enabled, if both uptime_sla and no_uptime_sla are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        uptime_sla = self.raw_param.get("uptime_sla")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.sku and
                self.mc.sku.tier is not None
            ):
                uptime_sla = self.mc.sku.tier == "Paid"

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if uptime_sla and self._get_no_uptime_sla(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    'Cannot specify "--uptime-sla" and "--no-uptime-sla" at the same time.'
                )
        return uptime_sla

    def get_uptime_sla(self) -> bool:
        """Obtain the value of uptime_sla.

        This function will verify the parameter by default. If both uptime_sla and no_uptime_sla are specified, raise
        a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_uptime_sla(enable_validation=True)

    def _get_no_uptime_sla(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of no_uptime_sla.

        This function supports the option of enable_validation. When enabled, if both uptime_sla and no_uptime_sla are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        no_uptime_sla = self.raw_param.get("no_uptime_sla")
        # We do not support this option in create mode, therefore we do not read the value from `mc`.

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if no_uptime_sla and self._get_uptime_sla(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    'Cannot specify "--uptime-sla" and "--no-uptime-sla" at the same time.'
                )
        return no_uptime_sla

    def get_no_uptime_sla(self) -> bool:
        """Obtain the value of no_uptime_sla.

        This function will verify the parameter by default. If both uptime_sla and no_uptime_sla are specified, raise
        a MutuallyExclusiveArgumentError.

        :return: bool
        """

        return self._get_no_uptime_sla(enable_validation=True)

    def _get_disable_local_accounts(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_local_accounts.

        This function supports the option of enable_validation. When enabled, if both disable_local_accounts and
        enable_local_accounts are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        disable_local_accounts = self.raw_param.get("disable_local_accounts")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "disable_local_accounts") and      # backward compatibility
                self.mc.disable_local_accounts is not None
            ):
                disable_local_accounts = self.mc.disable_local_accounts

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.UPDATE:
                if disable_local_accounts and self._get_enable_local_accounts(enable_validation=False):
                    raise MutuallyExclusiveArgumentError(
                        "Cannot specify --disable-local-accounts and "
                        "--enable-local-accounts at the same time."
                    )
        return disable_local_accounts

    def get_disable_local_accounts(self) -> bool:
        """Obtain the value of disable_local_accounts.

        This function will verify the parameter by default. If both disable_local_accounts and enable_local_accounts
        are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_disable_local_accounts(enable_validation=True)

    def _get_enable_local_accounts(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_local_accounts.

        This function supports the option of enable_validation. When enabled, if both disable_local_accounts and
        enable_local_accounts are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # read the original value passed by the command
        enable_local_accounts = self.raw_param.get("enable_local_accounts")
        # We do not support this option in create mode, therefore we do not read the value from `mc`.

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if enable_local_accounts and self._get_disable_local_accounts(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --disable-local-accounts and "
                    "--enable-local-accounts at the same time."
                )
        return enable_local_accounts

    def get_enable_local_accounts(self) -> bool:
        """Obtain the value of enable_local_accounts.

        This function will verify the parameter by default. If both disable_local_accounts and enable_local_accounts
        are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_enable_local_accounts(enable_validation=True)

    def get_edge_zone(self) -> Union[str, None]:
        """Obtain the value of edge_zone.

        :return: string or None
        """
        # read the original value passed by the command
        edge_zone = self.raw_param.get("edge_zone")
        # try to read the property value corresponding to the parameter from the `mc` object
        # Backward Compatibility: We also support api version v2020.11.01 in profile 2020-09-01-hybrid and there is
        # no such attribute.
        if (
            self.mc and
            hasattr(self.mc, "extended_location") and
            self.mc.extended_location and
            self.mc.extended_location.name is not None
        ):
            edge_zone = self.mc.extended_location.name

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return edge_zone

    def get_node_resource_group(self) -> Union[str, None]:
        """Obtain the value of node_resource_group.

        :return: string or None
        """
        # read the original value passed by the command
        node_resource_group = self.raw_param.get("node_resource_group")
        # try to read the property value corresponding to the parameter from the `mc` object
        if self.mc and self.mc.node_resource_group is not None:
            node_resource_group = self.mc.node_resource_group

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_resource_group

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

    def get_aks_custom_headers(self) -> Dict[str, str]:
        """Obtain the value of aks_custom_headers.

        Note: aks_custom_headers will not be decorated into the `mc` object.

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


class AKSManagedClusterCreateDecorator(BaseAKSManagedClusterDecorator):
    def __init__(
        self, cmd: AzCliCommand, client: ContainerServiceClient, raw_parameters: Dict, resource_type: ResourceType
    ):
        """Internal controller of aks_create.

        Break down the all-in-one aks_create function into several relatively independent functions (some of them have
        a certain order dependency) that only focus on a specific profile or process a specific piece of logic.
        In addition, an overall control function is provided. By calling the aforementioned independent functions one
        by one, a complete ManagedCluster object is gradually decorated and finally requests are sent to create a
        cluster.
        """
        super().__init__(cmd, client)
        self.__raw_parameters = raw_parameters
        self.resource_type = resource_type
        self.init_models()
        self.init_context()
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.MANAGED_CLUSTER
        self.init_agentpool_decorator_context()

    def init_models(self) -> None:
        """Initialize an AKSManagedClusterModels object to store the models.

        :return: None
        """
        self.models = AKSManagedClusterModels(self.cmd, self.resource_type)

    def init_context(self) -> None:
        """Initialize an AKSManagedClusterContext object to store the context in the process of assemble the
        ManagedCluster object.

        :return: None
        """
        self.context = AKSManagedClusterContext(
            self.cmd, AKSManagedClusterParamDict(self.__raw_parameters), self.models, DecoratorMode.CREATE
        )

    def init_agentpool_decorator_context(self) -> None:
        """Initialize an AKSAgentPoolAddDecorator object to assemble the AgentPool profile.

        :return: None
        """
        self.agentpool_decorator = AKSAgentPoolAddDecorator(
            self.cmd, self.client, self.__raw_parameters, self.resource_type, self.agentpool_decorator_mode
        )
        self.agentpool_context = self.agentpool_decorator.context
        self.context.attach_agentpool_context(self.agentpool_context)

    def _ensure_mc(self, mc: ManagedCluster) -> None:
        """Internal function to ensure that the incoming `mc` object is valid and the same as the attached
        `mc` object in the context.

        If the incoming `mc` is not valid or is inconsistent with the `mc` in the context, raise a CLIInternalError.

        :return: None
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        if self.context.mc != mc:
            raise CLIInternalError(
                "Inconsistent state detected. The incoming `mc` "
                "is not the same as the `mc` in the context."
            )

    def _remove_defaults_in_mc(self, mc: ManagedCluster) -> ManagedCluster:
        """Internal function to remove values from properties with default values of the `mc` object.

        Removing default values is to prevent getters from mistakenly overwriting user provided values with default
        values in the object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        defaults_in_mc = {}
        for attr_name, attr_value in vars(mc).items():
            if not attr_name.startswith("_") and attr_name != "location" and attr_value is not None:
                defaults_in_mc[attr_name] = attr_value
                setattr(mc, attr_name, None)
        self.context.set_intermediate("defaults_in_mc", defaults_in_mc, overwrite_exists=True)
        return mc

    def _restore_defaults_in_mc(self, mc: ManagedCluster) -> ManagedCluster:
        """Internal function to restore values of properties with default values of the `mc` object.

        Restoring default values is to keep the content of the request sent by cli consistent with that before the
        refactoring.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        defaults_in_mc = self.context.get_intermediate("defaults_in_mc", {})
        for key, value in defaults_in_mc.items():
            if getattr(mc, key, None) is None:
                setattr(mc, key, value)
        return mc

    def init_mc(self) -> ManagedCluster:
        """Initialize a ManagedCluster object with required parameter location and attach it to internal context.

        When location is not assigned, function "get_rg_location" will be called to get the location of the provided
        resource group, which internally used ResourceManagementClient to send the request.

        :return: the ManagedCluster object
        """
        # Initialize a ManagedCluster object with mandatory parameter location.
        mc = self.models.ManagedCluster(
            location=self.context.get_location(),
        )

        # attach mc to AKSContext
        self.context.attach_mc(mc)
        return mc

    def set_up_agentpool_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up agent pool profiles for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        agentpool_profile = self.agentpool_decorator.construct_agentpool_profile_default()
        mc.agent_pool_profiles = [agentpool_profile]
        return mc

    def set_up_mc_properties(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up misc direct properties for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc.tags = self.context.get_tags()
        mc.kubernetes_version = self.context.get_kubernetes_version()
        mc.dns_prefix = self.context.get_dns_name_prefix()
        mc.disk_encryption_set_id = self.context.get_node_osdisk_diskencryptionset_id()
        mc.disable_local_accounts = self.context.get_disable_local_accounts()
        mc.enable_rbac = not self.context.get_disable_rbac()
        return mc

    def set_up_linux_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up linux profile for the ManagedCluster object.

        Linux profile is just used for SSH access to VMs, so it will be omitted if --no-ssh-key option was specified.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

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
        self._ensure_mc(mc)

        (
            windows_admin_username,
            windows_admin_password,
        ) = self.context.get_windows_admin_username_and_password()
        if windows_admin_username or windows_admin_password:
            # license
            windows_license_type = None
            if self.context.get_enable_ahub():
                windows_license_type = "Windows_Server"

            # gmsa
            gmsa_profile = None
            if self.context.get_enable_windows_gmsa():
                gmsa_dns_server, gmsa_root_domain_name = self.context.get_gmsa_dns_server_and_root_domain_name()
                gmsa_profile = self.models.WindowsGmsaProfile(
                    enabled=True,
                    dns_server=gmsa_dns_server,
                    root_domain_name=gmsa_root_domain_name,
                )

            # this would throw an error if windows_admin_username is empty (the user enters an empty
            # string after being prompted), since admin_username is a required parameter
            windows_profile = self.models.ManagedClusterWindowsProfile(
                # [SuppressMessage("Microsoft.Security", "CS002:SecretInNextLine", Justification="variable name")]
                admin_username=windows_admin_username,
                admin_password=windows_admin_password,
                license_type=windows_license_type,
                gmsa_profile=gmsa_profile,
            )

            mc.windows_profile = windows_profile
        return mc

    def set_up_service_principal_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up service principal profile for the ManagedCluster object.

        The function "ensure_aks_service_principal" will be called if the user provides an incomplete sp and secret
        pair, which internally used GraphRbacManagementClient to send the request to create sp.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

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

        This function will store an intermediate need_post_creation_vnet_permission_granting.

        The function "subnet_role_assignment_exists" will be called to verify if the role assignment already exists for
        the subnet, which internally used AuthorizationManagementClient to send the request.
        The wrapper function "get_identity_by_msi_client" will be called by "get_user_assigned_identity_client_id" to
        get the identity object, which internally use ManagedServiceIdentityClient to send the request.
        The function "add_role_assignment" will be called to add role assignment for the subnet, which internally used
        AuthorizationManagementClient to send the request.

        :return: None
        """
        self._ensure_mc(mc)

        need_post_creation_vnet_permission_granting = False
        vnet_subnet_id = self.context.get_vnet_subnet_id()
        skip_subnet_role_assignment = (
            self.context.get_skip_subnet_role_assignment()
        )
        if (
            vnet_subnet_id and
            not skip_subnet_role_assignment and
            not self.context.external_functions.subnet_role_assignment_exists(self.cmd, vnet_subnet_id)
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
                    "https://docs.microsoft.com/azure/aks/use-managed-identity, "
                    "proceed to create cluster with system assigned identity?"
                )
                if not self.context.get_yes() and not prompt_y_n(
                    msg, default="n"
                ):
                    raise DecoratorEarlyExitException()
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
                if not self.context.external_functions.add_role_assignment(
                    self.cmd,
                    "Network Contributor",
                    identity_client_id,
                    scope=scope,
                ):
                    logger.warning(
                        "Could not create a role assignment for subnet. Are you an Owner on this subscription?"
                    )
        # store need_post_creation_vnet_permission_granting as an intermediate
        self.context.set_intermediate(
            "need_post_creation_vnet_permission_granting",
            need_post_creation_vnet_permission_granting,
            overwrite_exists=True,
        )

    def process_attach_acr(self, mc: ManagedCluster) -> None:
        """Attach acr for the cluster.

        The function "ensure_aks_acr" will be called to create an AcrPull role assignment for the acr, which
        internally used AuthorizationManagementClient to send the request.

        :return: None
        """
        self._ensure_mc(mc)

        attach_acr = self.context.get_attach_acr()
        if attach_acr:
            # If enable_managed_identity, attach acr operation will be handled after the cluster is created
            if not self.context.get_enable_managed_identity():
                service_principal_profile = mc.service_principal_profile
                self.context.external_functions.ensure_aks_acr(
                    self.cmd,
                    assignee=service_principal_profile.client_id,
                    acr_name_or_id=attach_acr,
                    # not actually used
                    subscription_id=self.context.get_subscription_id(),
                )

    def set_up_network_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up network profile for the ManagedCluster object.

        Build load balancer profile, verify outbound type and load balancer sku first, then set up network profile.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # build load balancer profile, which is part of the network profile
        load_balancer_profile = create_load_balancer_profile(
            self.context.get_load_balancer_managed_outbound_ip_count(),
            self.context.get_load_balancer_outbound_ips(),
            self.context.get_load_balancer_outbound_ip_prefixes(),
            self.context.get_load_balancer_outbound_ports(),
            self.context.get_load_balancer_idle_timeout(),
            models=self.models.load_balancer_models,
        )

        # verify outbound type
        # Note: Validation internally depends on load_balancer_sku, which is a temporary value that is
        # dynamically completed.
        outbound_type = self.context.get_outbound_type(
            load_balancer_profile=load_balancer_profile
        )

        # verify load balancer sku
        load_balancer_sku = safe_lower(self.context.get_load_balancer_sku())

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
            if load_balancer_sku == CONST_LOAD_BALANCER_SKU_STANDARD or load_balancer_profile:
                network_profile = self.models.ContainerServiceNetworkProfile(
                    network_plugin="kubenet",
                    load_balancer_sku=load_balancer_sku,
                    load_balancer_profile=load_balancer_profile,
                    outbound_type=outbound_type,
                )
            if load_balancer_sku == CONST_LOAD_BALANCER_SKU_BASIC:
                # load balancer sku must be standard when load balancer profile is provided
                network_profile = self.models.ContainerServiceNetworkProfile(
                    load_balancer_sku=load_balancer_sku,
                )

        # build nat gateway profile, which is part of the network profile
        nat_gateway_profile = create_nat_gateway_profile(
            self.context.get_nat_gateway_managed_outbound_ip_count(),
            self.context.get_nat_gateway_idle_timeout(),
            models=self.models.nat_gateway_models,
        )
        load_balancer_sku = self.context.get_load_balancer_sku()
        if load_balancer_sku != CONST_LOAD_BALANCER_SKU_BASIC:
            network_profile.nat_gateway_profile = nat_gateway_profile
        mc.network_profile = network_profile
        return mc

    def build_http_application_routing_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build http application routing addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        http_application_routing_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
        )
        return http_application_routing_addon_profile

    def build_kube_dashboard_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build kube dashboard addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        kube_dashboard_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
        )
        return kube_dashboard_addon_profile

    def build_monitoring_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build monitoring addon profile.

        The function "ensure_container_insights_for_monitoring" will be called to create a deployment which publishes
        the Container Insights solution to the Log Analytics workspace.
        When workspace_resource_id is not assigned, function "ensure_default_log_analytics_workspace_for_monitoring"
        will be called to create a workspace, which internally used ResourceManagementClient to send the request.

        :return: a ManagedClusterAddonProfile object
        """
        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID = addon_consts.get(
            "CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID"
        )
        CONST_MONITORING_USING_AAD_MSI_AUTH = addon_consts.get(
            "CONST_MONITORING_USING_AAD_MSI_AUTH"
        )

        # TODO: can we help the user find a workspace resource ID?
        monitoring_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={
                CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: self.context.get_workspace_resource_id(),
                CONST_MONITORING_USING_AAD_MSI_AUTH: "True"
                if self.context.get_enable_msi_auth_for_monitoring()
                else "False",
            },
        )
        # post-process, create a deployment
        self.context.external_functions.ensure_container_insights_for_monitoring(
            self.cmd, monitoring_addon_profile,
            self.context.get_subscription_id(),
            self.context.get_resource_group_name(),
            self.context.get_name(),
            self.context.get_location(),
            remove_monitoring=False,
            aad_route=self.context.get_enable_msi_auth_for_monitoring(),
            create_dcr=True,
            create_dcra=False,
        )
        # set intermediate
        self.context.set_intermediate("monitoring_addon_enabled", True, overwrite_exists=True)
        return monitoring_addon_profile

    def build_azure_policy_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build azure policy addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        azure_policy_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
        )
        return azure_policy_addon_profile

    def build_virtual_node_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build virtual node addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_VIRTUAL_NODE_SUBNET_NAME = addon_consts.get(
            "CONST_VIRTUAL_NODE_SUBNET_NAME"
        )

        virtual_node_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={CONST_VIRTUAL_NODE_SUBNET_NAME: self.context.get_aci_subnet_name()}
        )
        # set intermediate
        self.context.set_intermediate("virtual_node_addon_enabled", True, overwrite_exists=True)
        return virtual_node_addon_profile

    def build_ingress_appgw_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build ingress appgw addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME = addon_consts.get(
            "CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME"
        )
        CONST_INGRESS_APPGW_SUBNET_CIDR = addon_consts.get(
            "CONST_INGRESS_APPGW_SUBNET_CIDR"
        )
        CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID = addon_consts.get(
            "CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID"
        )
        CONST_INGRESS_APPGW_SUBNET_ID = addon_consts.get(
            "CONST_INGRESS_APPGW_SUBNET_ID"
        )
        CONST_INGRESS_APPGW_WATCH_NAMESPACE = addon_consts.get(
            "CONST_INGRESS_APPGW_WATCH_NAMESPACE"
        )

        ingress_appgw_addon_profile = self.models.ManagedClusterAddonProfile(enabled=True, config={})
        appgw_name = self.context.get_appgw_name()
        appgw_subnet_cidr = self.context.get_appgw_subnet_cidr()
        appgw_id = self.context.get_appgw_id()
        appgw_subnet_id = self.context.get_appgw_subnet_id()
        appgw_watch_namespace = self.context.get_appgw_watch_namespace()
        if appgw_name is not None:
            ingress_appgw_addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME] = appgw_name
        if appgw_subnet_cidr is not None:
            ingress_appgw_addon_profile.config[CONST_INGRESS_APPGW_SUBNET_CIDR] = appgw_subnet_cidr
        if appgw_id is not None:
            ingress_appgw_addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID] = appgw_id
        if appgw_subnet_id is not None:
            ingress_appgw_addon_profile.config[CONST_INGRESS_APPGW_SUBNET_ID] = appgw_subnet_id
        if appgw_watch_namespace is not None:
            ingress_appgw_addon_profile.config[CONST_INGRESS_APPGW_WATCH_NAMESPACE] = appgw_watch_namespace
        # set intermediate
        self.context.set_intermediate("ingress_appgw_addon_enabled", True, overwrite_exists=True)
        return ingress_appgw_addon_profile

    def build_confcom_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build confcom addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_ACC_SGX_QUOTE_HELPER_ENABLED = addon_consts.get(
            "CONST_ACC_SGX_QUOTE_HELPER_ENABLED"
        )

        confcom_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True, config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "false"})
        if self.context.get_enable_sgxquotehelper():
            confcom_addon_profile.config[CONST_ACC_SGX_QUOTE_HELPER_ENABLED] = "true"
        return confcom_addon_profile

    def build_open_service_mesh_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build open service mesh addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        open_service_mesh_addon_profile = self.models.ManagedClusterAddonProfile(
            enabled=True,
            config={},
        )
        return open_service_mesh_addon_profile

    def build_azure_keyvault_secrets_provider_addon_profile(self) -> ManagedClusterAddonProfile:
        """Build azure keyvault secrets provider addon profile.

        :return: a ManagedClusterAddonProfile object
        """
        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_SECRET_ROTATION_ENABLED = addon_consts.get(
            "CONST_SECRET_ROTATION_ENABLED"
        )
        CONST_ROTATION_POLL_INTERVAL = addon_consts.get(
            "CONST_ROTATION_POLL_INTERVAL"
        )

        azure_keyvault_secrets_provider_addon_profile = (
            self.models.ManagedClusterAddonProfile(
                enabled=True,
                config={
                    CONST_SECRET_ROTATION_ENABLED: "false",
                    CONST_ROTATION_POLL_INTERVAL: "2m",
                },
            )
        )
        if self.context.get_enable_secret_rotation():
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_SECRET_ROTATION_ENABLED
            ] = "true"
        if self.context.get_rotation_poll_interval() is not None:
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_ROTATION_POLL_INTERVAL
            ] = self.context.get_rotation_poll_interval()
        return azure_keyvault_secrets_provider_addon_profile

    # pylint: disable=too-many-statements
    def set_up_addon_profiles(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up addon profiles for the ManagedCluster object.

        This function will store following intermediates: monitoring_addon_enabled, virtual_node_addon_enabled and
        ingress_appgw_addon_enabled.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_MONITORING_ADDON_NAME = addon_consts.get(
            "CONST_MONITORING_ADDON_NAME"
        )
        CONST_VIRTUAL_NODE_ADDON_NAME = addon_consts.get(
            "CONST_VIRTUAL_NODE_ADDON_NAME"
        )
        CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME = addon_consts.get(
            "CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME"
        )
        CONST_KUBE_DASHBOARD_ADDON_NAME = addon_consts.get(
            "CONST_KUBE_DASHBOARD_ADDON_NAME"
        )
        CONST_AZURE_POLICY_ADDON_NAME = addon_consts.get(
            "CONST_AZURE_POLICY_ADDON_NAME"
        )
        CONST_INGRESS_APPGW_ADDON_NAME = addon_consts.get(
            "CONST_INGRESS_APPGW_ADDON_NAME"
        )
        CONST_CONFCOM_ADDON_NAME = addon_consts.get("CONST_CONFCOM_ADDON_NAME")
        CONST_OPEN_SERVICE_MESH_ADDON_NAME = addon_consts.get(
            "CONST_OPEN_SERVICE_MESH_ADDON_NAME"
        )
        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME = addon_consts.get(
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME"
        )

        addon_profiles = {}
        # error out if any unrecognized or duplicate addon provided
        # error out if '--enable-addons=monitoring' isn't set but workspace_resource_id is
        # error out if '--enable-addons=virtual-node' is set but aci_subnet_name and vnet_subnet_id are not
        addons = self.context.get_enable_addons()
        if "http_application_routing" in addons:
            addon_profiles[
                CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME
            ] = self.build_http_application_routing_addon_profile()
        if "kube-dashboard" in addons:
            addon_profiles[
                CONST_KUBE_DASHBOARD_ADDON_NAME
            ] = self.build_kube_dashboard_addon_profile()
        if "monitoring" in addons:
            addon_profiles[
                CONST_MONITORING_ADDON_NAME
            ] = self.build_monitoring_addon_profile()
        if "azure-policy" in addons:
            addon_profiles[
                CONST_AZURE_POLICY_ADDON_NAME
            ] = self.build_azure_policy_addon_profile()
        if "virtual-node" in addons:
            # TODO: how about aciConnectorwindows, what is its addon name?
            os_type = self.context.get_virtual_node_addon_os_type()
            addon_profiles[
                CONST_VIRTUAL_NODE_ADDON_NAME + os_type
            ] = self.build_virtual_node_addon_profile()
        if "ingress-appgw" in addons:
            addon_profiles[
                CONST_INGRESS_APPGW_ADDON_NAME
            ] = self.build_ingress_appgw_addon_profile()
        if "confcom" in addons:
            addon_profiles[
                CONST_CONFCOM_ADDON_NAME
            ] = self.build_confcom_addon_profile()
        if "open-service-mesh" in addons:
            addon_profiles[
                CONST_OPEN_SERVICE_MESH_ADDON_NAME
            ] = self.build_open_service_mesh_addon_profile()
        if "azure-keyvault-secrets-provider" in addons:
            addon_profiles[
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
            ] = self.build_azure_keyvault_secrets_provider_addon_profile()
        mc.addon_profiles = addon_profiles
        return mc

    def set_up_aad_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up aad profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

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

    def set_up_api_server_access_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up api server access profile and fqdn subdomain for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        api_server_access_profile = None
        api_server_authorized_ip_ranges = self.context.get_api_server_authorized_ip_ranges()
        enable_private_cluster = self.context.get_enable_private_cluster()
        disable_public_fqdn = self.context.get_disable_public_fqdn()
        private_dns_zone = self.context.get_private_dns_zone()
        if api_server_authorized_ip_ranges or enable_private_cluster:
            api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile(
                authorized_ip_ranges=api_server_authorized_ip_ranges,
                enable_private_cluster=True if enable_private_cluster else None,
                enable_private_cluster_public_fqdn=False if disable_public_fqdn else None,
                private_dns_zone=private_dns_zone
            )
        mc.api_server_access_profile = api_server_access_profile

        fqdn_subdomain = self.context.get_fqdn_subdomain()
        mc.fqdn_subdomain = fqdn_subdomain
        return mc

    def set_up_identity(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up identity for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        identity = None
        enable_managed_identity = self.context.get_enable_managed_identity()
        assign_identity = self.context.get_assign_identity()
        if enable_managed_identity and not assign_identity:
            identity = self.models.ManagedClusterIdentity(
                type="SystemAssigned"
            )
        elif enable_managed_identity and assign_identity:
            user_assigned_identity = {
                assign_identity: self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
            }
            identity = self.models.ManagedClusterIdentity(
                type="UserAssigned",
                user_assigned_identities=user_assigned_identity
            )
        mc.identity = identity
        return mc

    def set_up_identity_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up identity profile for the ManagedCluster object.

        The wrapper function "get_identity_by_msi_client" will be called (by "get_user_assigned_identity_object_id") to
        get the identity object, which internally use ManagedServiceIdentityClient to send the request.
        The function "ensure_cluster_identity_permission_on_kubelet_identity" will be called to create a role
        assignment if necessary, which internally used AuthorizationManagementClient to send the request.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        identity_profile = None
        assign_kubelet_identity = self.context.get_assign_kubelet_identity()
        if assign_kubelet_identity:
            kubelet_identity = self.context.get_identity_by_msi_client(assign_kubelet_identity)
            identity_profile = {
                'kubeletidentity': self.models.UserAssignedIdentity(
                    resource_id=assign_kubelet_identity,
                    client_id=kubelet_identity.client_id,
                    object_id=kubelet_identity.principal_id
                )
            }
            cluster_identity_object_id = self.context.get_user_assigned_identity_object_id()
            # ensure the cluster identity has "Managed Identity Operator" role at the scope of kubelet identity
            self.context.external_functions.ensure_cluster_identity_permission_on_kubelet_identity(
                self.cmd,
                cluster_identity_object_id,
                assign_kubelet_identity)
        mc.identity_profile = identity_profile
        return mc

    def set_up_auto_upgrade_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up auto upgrade profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        auto_upgrade_profile = None
        auto_upgrade_channel = self.context.get_auto_upgrade_channel()
        if auto_upgrade_channel:
            auto_upgrade_profile = self.models.ManagedClusterAutoUpgradeProfile(upgrade_channel=auto_upgrade_channel)
        mc.auto_upgrade_profile = auto_upgrade_profile
        return mc

    def set_up_auto_scaler_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up autoscaler profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        cluster_autoscaler_profile = self.context.get_cluster_autoscaler_profile()
        mc.auto_scaler_profile = cluster_autoscaler_profile
        return mc

    def set_up_sku(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up sku (uptime sla) for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_uptime_sla():
            mc.sku = self.models.ManagedClusterSKU(
                name="Basic",
                tier="Paid"
            )
        return mc

    def set_up_extended_location(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up extended location (edge zone) for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        edge_zone = self.context.get_edge_zone()
        if edge_zone:
            mc.extended_location = self.models.ExtendedLocation(
                name=edge_zone,
                type=self.models.ExtendedLocationTypes.EDGE_ZONE
            )
        return mc

    def set_up_node_resource_group(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up node resource group for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc.node_resource_group = self.context.get_node_resource_group()
        return mc

    def construct_mc_profile_default(self, bypass_restore_defaults: bool = False) -> ManagedCluster:
        """The overall controller used to construct the default ManagedCluster profile.

        The completely constructed ManagedCluster object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the ManagedCluster object
        """
        # initialize the ManagedCluster object
        mc = self.init_mc()
        # remove defaults
        self._remove_defaults_in_mc(mc)
        # set up agentpool profile
        mc = self.set_up_agentpool_profile(mc)
        # set up misc direct mc properties
        mc = self.set_up_mc_properties(mc)
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
        # set up api server access profile and fqdn subdomain
        mc = self.set_up_api_server_access_profile(mc)
        # set up identity
        mc = self.set_up_identity(mc)
        # set up identity profile
        mc = self.set_up_identity_profile(mc)
        # set up auto upgrade profile
        mc = self.set_up_auto_upgrade_profile(mc)
        # set up auto scaler profile
        mc = self.set_up_auto_scaler_profile(mc)
        # set up sku
        mc = self.set_up_sku(mc)
        # set up extended location
        mc = self.set_up_extended_location(mc)
        # set up node resource group
        mc = self.set_up_node_resource_group(mc)

        # restore defaults
        if not bypass_restore_defaults:
            mc = self._restore_defaults_in_mc(mc)
        return mc

    # pylint: disable=unused-argument,too-many-boolean-expressions
    def check_is_postprocessing_required(self, mc: ManagedCluster) -> bool:
        """Helper function to check if postprocessing is required after sending a PUT request to create the cluster.

        :return: bool
        """
        # some addons require post cluster creation role assigment
        monitoring_addon_enabled = self.context.get_intermediate("monitoring_addon_enabled", default_value=False)
        ingress_appgw_addon_enabled = self.context.get_intermediate("ingress_appgw_addon_enabled", default_value=False)
        virtual_node_addon_enabled = self.context.get_intermediate("virtual_node_addon_enabled", default_value=False)
        enable_managed_identity = self.context.get_enable_managed_identity()
        attach_acr = self.context.get_attach_acr()
        need_grant_vnet_permission_to_cluster_identity = self.context.get_intermediate(
            "need_post_creation_vnet_permission_granting", default_value=False
        )

        if (
            monitoring_addon_enabled or
            ingress_appgw_addon_enabled or
            virtual_node_addon_enabled or
            (enable_managed_identity and attach_acr) or
            need_grant_vnet_permission_to_cluster_identity
        ):
            return True
        return False

    # pylint: disable=unused-argument
    def immediate_processing_after_request(self, mc: ManagedCluster) -> None:
        """Immediate processing performed when the cluster has not finished creating after a PUT request to the cluster
        has been sent.

        :return: None
        """
        # vnet
        need_grant_vnet_permission_to_cluster_identity = self.context.get_intermediate(
            "need_post_creation_vnet_permission_granting", default_value=False
        )
        if need_grant_vnet_permission_to_cluster_identity:
            # Grant vnet permission to system assigned identity RIGHT AFTER the cluster is put, this operation can
            # reduce latency for the role assignment take effect
            instant_cluster = self.client.get(self.context.get_resource_group_name(), self.context.get_name())
            if not self.context.external_functions.add_role_assignment(
                self.cmd,
                "Network Contributor",
                instant_cluster.identity.principal_id,
                scope=self.context.get_vnet_subnet_id(),
                is_service_principal=False,
            ):
                logger.warning(
                    "Could not create a role assignment for subnet. Are you an Owner on this subscription?"
                )

    def postprocessing_after_mc_created(self, cluster: ManagedCluster) -> None:
        """Postprocessing performed after the cluster is created.

        :return: None
        """
        # monitoring addon
        monitoring_addon_enabled = self.context.get_intermediate("monitoring_addon_enabled", default_value=False)
        if monitoring_addon_enabled:
            enable_msi_auth_for_monitoring = self.context.get_enable_msi_auth_for_monitoring()
            if not enable_msi_auth_for_monitoring:
                # add cluster spn/msi Monitoring Metrics Publisher role assignment to publish metrics to MDM
                # mdm metrics is supported only in azure public cloud, so add the role assignment only in this cloud
                cloud_name = self.cmd.cli_ctx.cloud.name
                if cloud_name.lower() == "azurecloud":
                    from msrestazure.tools import resource_id

                    cluster_resource_id = resource_id(
                        subscription=self.context.get_subscription_id(),
                        resource_group=self.context.get_resource_group_name(),
                        namespace="Microsoft.ContainerService",
                        type="managedClusters",
                        name=self.context.get_name(),
                    )
                    self.context.external_functions.add_monitoring_role_assignment(
                        cluster, cluster_resource_id, self.cmd
                    )
            else:
                # Create the DCR Association here
                addon_consts = self.context.get_addon_consts()
                CONST_MONITORING_ADDON_NAME = addon_consts.get("CONST_MONITORING_ADDON_NAME")
                self.context.external_functions.ensure_container_insights_for_monitoring(
                    self.cmd,
                    cluster.addon_profiles[CONST_MONITORING_ADDON_NAME],
                    self.context.get_subscription_id(),
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    self.context.get_location(),
                    remove_monitoring=False,
                    aad_route=self.context.get_enable_msi_auth_for_monitoring(),
                    create_dcr=False,
                    create_dcra=True,
                )

        # ingress appgw addon
        ingress_appgw_addon_enabled = self.context.get_intermediate("ingress_appgw_addon_enabled", default_value=False)
        if ingress_appgw_addon_enabled:
            self.context.external_functions.add_ingress_appgw_addon_role_assignment(cluster, self.cmd)

        # virtual node addon
        virtual_node_addon_enabled = self.context.get_intermediate("virtual_node_addon_enabled", default_value=False)
        if virtual_node_addon_enabled:
            self.context.external_functions.add_virtual_node_role_assignment(
                self.cmd, cluster, self.context.get_vnet_subnet_id()
            )

        # attach acr
        enable_managed_identity = self.context.get_enable_managed_identity()
        attach_acr = self.context.get_attach_acr()
        if enable_managed_identity and attach_acr:
            # Attach ACR to cluster enabled managed identity
            if cluster.identity_profile is None or cluster.identity_profile["kubeletidentity"] is None:
                logger.warning(
                    "Your cluster is successfully created, but we failed to attach "
                    "acr to it, you can manually grant permission to the identity "
                    "named <ClUSTER_NAME>-agentpool in MC_ resource group to give "
                    "it permission to pull from ACR."
                )
            else:
                kubelet_identity_object_id = cluster.identity_profile["kubeletidentity"].object_id
                self.context.external_functions.ensure_aks_acr(
                    self.cmd,
                    assignee=kubelet_identity_object_id,
                    acr_name_or_id=attach_acr,
                    subscription_id=self.context.get_subscription_id(),
                    is_service_principal=False,
                )

    def put_mc(self, mc: ManagedCluster) -> ManagedCluster:
        if self.check_is_postprocessing_required(mc):
            # send request
            poller = self.client.begin_create_or_update(
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
            )
            self.immediate_processing_after_request(mc)
            # poll until the result is returned
            cluster = LongRunningOperation(self.cmd.cli_ctx)(poller)
            self.postprocessing_after_mc_created(cluster)
        else:
            cluster = sdk_no_wait(
                self.context.get_no_wait(),
                self.client.begin_create_or_update,
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
            )
        return cluster

    def create_mc(self, mc: ManagedCluster) -> ManagedCluster:
        """Send request to create a real managed cluster.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # Due to SPN replication latency, we do a few retries here
        max_retry = 30
        error_msg = ""
        for _ in range(0, max_retry):
            try:
                cluster = self.put_mc(mc)
                return cluster
            # CloudError was raised before, but since the adoption of track 2 SDK,
            # HttpResponseError would be raised instead
            except (CloudError, HttpResponseError) as ex:
                error_msg = str(ex)
                if "not found in Active Directory tenant" in ex.message:
                    time.sleep(3)
                else:
                    raise map_azure_error_to_cli_error(ex)
        raise AzCLIError("Maximum number of retries exceeded. " + error_msg)


class AKSManagedClusterUpdateDecorator(BaseAKSManagedClusterDecorator):
    def __init__(
        self, cmd: AzCliCommand, client: ContainerServiceClient, raw_parameters: Dict, resource_type: ResourceType
    ):
        """Internal controller of aks_update.

        Break down the all-in-one aks_update function into several relatively independent functions (some of them have
        a certain order dependency) that only focus on a specific profile or process a specific piece of logic.
        In addition, an overall control function is provided. By calling the aforementioned independent functions one
        by one, a complete ManagedCluster object is gradually updated and finally requests are sent to update an
        existing cluster.
        """
        super().__init__(cmd, client)
        self.__raw_parameters = raw_parameters
        self.resource_type = resource_type
        self.init_models()
        self.init_context()
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.MANAGED_CLUSTER
        self.init_agentpool_decorator_context()

    def init_models(self) -> None:
        """Initialize an AKSManagedClusterModels object to store the models.

        :return: None
        """
        self.models = AKSManagedClusterModels(self.cmd, self.resource_type)

    def init_context(self) -> None:
        """Initialize an AKSManagedClusterContext object to store the context in the process of assemble the
        ManagedCluster object.

        :return: None
        """
        self.context = AKSManagedClusterContext(
            self.cmd, AKSManagedClusterParamDict(self.__raw_parameters), self.models, DecoratorMode.UPDATE
        )

    def init_agentpool_decorator_context(self) -> None:
        """Initialize an AKSAgentPoolAddDecorator object to assemble the AgentPool profile.

        :return: None
        """
        self.agentpool_decorator = AKSAgentPoolUpdateDecorator(
            self.cmd, self.client, self.__raw_parameters, self.resource_type, self.agentpool_decorator_mode
        )
        self.agentpool_context = self.agentpool_decorator.context
        self.context.attach_agentpool_context(self.agentpool_context)

    def check_raw_parameters(self):
        """Helper function to check whether any parameters are set.

        If the values of all the parameters are the default values, the command execution will be terminated early and
        raise a RequiredArgumentMissingError. Neither the request to fetch or update the ManagedCluster object will be
        sent.

        :return: None
        """
        # exclude some irrelevant or mandatory parameters
        excluded_keys = ("cmd", "client", "resource_group_name", "name")
        # check whether the remaining parameters are set
        # the default value None or False (and other empty values, like empty string) will be considered as not set
        is_changed = any(v for k, v in self.context.raw_param.items() if k not in excluded_keys)

        # special cases
        # some parameters support the use of empty string or dictionary to update/remove previously set values
        is_default = (
            self.context.get_cluster_autoscaler_profile() is None and
            self.context.get_api_server_authorized_ip_ranges() is None and
            self.context.get_nodepool_labels() is None
        )

        if not is_changed and is_default:
            # Note: Uncomment the followings to automatically generate the error message.
            # option_names = [
            #     '"{}"'.format(format_parameter_name_to_option_name(x))
            #     for x in self.context.raw_param.keys()
            #     if x not in excluded_keys
            # ]
            # error_msg = "Please specify one or more of {}.".format(
            #     " or ".join(option_names)
            # )
            # raise RequiredArgumentMissingError(error_msg)
            raise RequiredArgumentMissingError(
                'Please specify one or more of "--enable-cluster-autoscaler" or '
                '"--disable-cluster-autoscaler" or '
                '"--update-cluster-autoscaler" or '
                '"--cluster-autoscaler-profile" or '
                '"--load-balancer-managed-outbound-ip-count" or '
                '"--load-balancer-outbound-ips" or '
                '"--load-balancer-outbound-ip-prefixes" or '
                '"--load-balancer-outbound-ports" or '
                '"--load-balancer-idle-timeout" or '
                '"--nat-gateway-managed-outbound-ip-count" or '
                '"--nat-gateway-idle-timeout" or '
                '"--auto-upgrade-channel" or '
                '"--attach-acr" or "--detach-acr" or '
                '"--uptime-sla" or '
                '"--no-uptime-sla" or '
                '"--api-server-authorized-ip-ranges" or '
                '"--enable-aad" or '
                '"--aad-tenant-id" or '
                '"--aad-admin-group-object-ids" or '
                '"--enable-ahub" or '
                '"--disable-ahub" or '
                '"--windows-admin-password" or '
                '"--enable-managed-identity" or '
                '"--assign-identity" or '
                '"--enable-azure-rbac" or '
                '"--disable-azure-rbac" or '
                '"--enable-public-fqdn" or '
                '"--disable-public-fqdn" or '
                '"--tags" or '
                '"--nodepool-labels" or '
                '"--enble-windows-gmsa".'
            )

    def _ensure_mc(self, mc: ManagedCluster) -> None:
        """Internal function to ensure that the incoming `mc` object is valid and the same as the attached `mc` object
        in the context.

        If the incomding `mc` is not valid or is inconsistent with the `mc` in the context, raise a CLIInternalError.

        :return: None
        """
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        if self.context.mc != mc:
            raise CLIInternalError(
                "Inconsistent state detected. The incoming `mc` is not the same as the `mc` in the context."
            )

    def fetch_mc(self) -> ManagedCluster:
        """Get the ManagedCluster object currently in use and attach it to internal context.

        Internally send request using ContainerServiceClient and parameters name (cluster) and resource group name.

        :return: the ManagedCluster object
        """
        mc = self.client.get(self.context.get_resource_group_name(), self.context.get_name())

        # attach mc to AKSContext
        self.context.attach_mc(mc)
        return mc

    def update_agentpool_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update agentpool profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if not mc.agent_pool_profiles:
            raise UnknownError(
                "Encounter an unexpected error while getting agent pool profiles from the cluster in the process of "
                "updating agentpool profile."
            )

        agentpool_profile = self.agentpool_decorator.update_agentpool_profile_default(mc.agent_pool_profiles)
        mc.agent_pool_profiles[0] = agentpool_profile

        # update nodepool labels for all nodepools
        nodepool_labels = self.context.get_nodepool_labels()
        if nodepool_labels is not None:
            for agent_profile in mc.agent_pool_profiles:
                agent_profile.node_labels = nodepool_labels
        return mc

    def update_auto_scaler_profile(self, mc):
        """Update autoscaler profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        cluster_autoscaler_profile = self.context.get_cluster_autoscaler_profile()
        if cluster_autoscaler_profile is not None:
            # update profile (may clear profile with empty dictionary)
            mc.auto_scaler_profile = cluster_autoscaler_profile
        return mc

    def update_tags(self, mc: ManagedCluster) -> ManagedCluster:
        """Update tags for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        tags = self.context.get_tags()
        if tags is not None:
            mc.tags = tags
        return mc

    def process_attach_detach_acr(self, mc: ManagedCluster) -> None:
        """Attach or detach acr for the cluster.

        The function "ensure_aks_acr" will be called to create or delete an AcrPull role assignment for the acr, which
        internally used AuthorizationManagementClient to send the request.

        :return: None
        """
        self._ensure_mc(mc)

        subscription_id = self.context.get_subscription_id()
        assignee, is_service_principal = self.context.get_assignee_from_identity_or_sp_profile()
        attach_acr = self.context.get_attach_acr()
        detach_acr = self.context.get_detach_acr()

        if attach_acr:
            self.context.external_functions.ensure_aks_acr(
                self.cmd,
                assignee=assignee,
                acr_name_or_id=attach_acr,
                subscription_id=subscription_id,
                is_service_principal=is_service_principal,
            )

        if detach_acr:
            self.context.external_functions.ensure_aks_acr(
                self.cmd,
                assignee=assignee,
                acr_name_or_id=detach_acr,
                subscription_id=subscription_id,
                detach=True,
                is_service_principal=is_service_principal,
            )

    def update_sku(self, mc: ManagedCluster) -> ManagedCluster:
        """Update sku (uptime sla) for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_uptime_sla():
            mc.sku = self.models.ManagedClusterSKU(
                name="Basic",
                tier="Paid"
            )

        if self.context.get_no_uptime_sla():
            mc.sku = self.models.ManagedClusterSKU(
                name="Basic",
                tier="Free"
            )
        return mc

    def update_load_balancer_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update load balancer profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if not mc.network_profile:
            raise UnknownError(
                "Encounter an unexpected error while getting network profile from the cluster in the process of "
                "updating its load balancer profile."
            )

        load_balancer_managed_outbound_ip_count = self.context.get_load_balancer_managed_outbound_ip_count()
        load_balancer_outbound_ips = self.context.get_load_balancer_outbound_ips()
        load_balancer_outbound_ip_prefixes = self.context.get_load_balancer_outbound_ip_prefixes()
        load_balancer_outbound_ports = self.context.get_load_balancer_outbound_ports()
        load_balancer_idle_timeout = self.context.get_load_balancer_idle_timeout()
        # In the internal function "_update_load_balancer_profile", it will check whether the provided parameters
        # have been assigned, and if there are any, the corresponding profile will be modified; otherwise, it will
        # remain unchanged.
        mc.network_profile.load_balancer_profile = _update_load_balancer_profile(
            managed_outbound_ip_count=load_balancer_managed_outbound_ip_count,
            outbound_ips=load_balancer_outbound_ips,
            outbound_ip_prefixes=load_balancer_outbound_ip_prefixes,
            outbound_ports=load_balancer_outbound_ports,
            idle_timeout=load_balancer_idle_timeout,
            profile=mc.network_profile.load_balancer_profile,
            models=self.models.load_balancer_models)
        return mc

    def update_nat_gateway_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update nat gateway profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        nat_gateway_managed_outbound_ip_count = self.context.get_nat_gateway_managed_outbound_ip_count()
        nat_gateway_idle_timeout = self.context.get_nat_gateway_idle_timeout()
        if is_nat_gateway_profile_provided(nat_gateway_managed_outbound_ip_count, nat_gateway_idle_timeout):
            if not mc.network_profile:
                raise UnknownError(
                    "Unexpectedly get an empty network profile in the process of updating nat gateway profile."
                )

            mc.network_profile.nat_gateway_profile = _update_nat_gateway_profile(
                nat_gateway_managed_outbound_ip_count,
                nat_gateway_idle_timeout,
                mc.network_profile.nat_gateway_profile,
                models=self.models.nat_gateway_models,
            )
        return mc

    def update_disable_local_accounts(self, mc: ManagedCluster) -> ManagedCluster:
        """Update disable/enable local accounts for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_disable_local_accounts():
            mc.disable_local_accounts = True

        if self.context.get_enable_local_accounts():
            mc.disable_local_accounts = False
        return mc

    def update_api_server_access_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update api server access profile and fqdn subdomain for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if mc.api_server_access_profile is None:
            profile_holder = self.models.ManagedClusterAPIServerAccessProfile()
        else:
            profile_holder = mc.api_server_access_profile

        api_server_authorized_ip_ranges = self.context.get_api_server_authorized_ip_ranges()
        disable_public_fqdn = self.context.get_disable_public_fqdn()
        enable_public_fqdn = self.context.get_enable_public_fqdn()
        if api_server_authorized_ip_ranges is not None:
            # empty string is valid as it disables ip whitelisting
            profile_holder.authorized_ip_ranges = api_server_authorized_ip_ranges
        if disable_public_fqdn:
            profile_holder.enable_private_cluster_public_fqdn = False
        if enable_public_fqdn:
            profile_holder.enable_private_cluster_public_fqdn = True

        # keep api_server_access_profile empty if none of its properties are updated
        if (
            profile_holder != mc.api_server_access_profile and
            profile_holder == self.models.ManagedClusterAPIServerAccessProfile()
        ):
            profile_holder = None
        mc.api_server_access_profile = profile_holder
        return mc

    def update_windows_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update windows profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        enable_ahub = self.context.get_enable_ahub()
        disable_ahub = self.context.get_disable_ahub()
        windows_admin_password = self.context.get_windows_admin_password()
        enable_windows_gmsa = self.context.get_enable_windows_gmsa()

        if any([enable_ahub, disable_ahub, windows_admin_password, enable_windows_gmsa]) and not mc.windows_profile:
            raise UnknownError(
                "Encounter an unexpected error while getting windows profile from the cluster in the process of update."
            )

        if enable_ahub:
            mc.windows_profile.license_type = 'Windows_Server'
        if disable_ahub:
            mc.windows_profile.license_type = 'None'
        if windows_admin_password:
            mc.windows_profile.admin_password = windows_admin_password
        if enable_windows_gmsa:
            gmsa_dns_server, gmsa_root_domain_name = self.context.get_gmsa_dns_server_and_root_domain_name()
            mc.windows_profile.gmsa_profile = self.models.WindowsGmsaProfile(
                enabled=True,
                dns_server=gmsa_dns_server,
                root_domain_name=gmsa_root_domain_name,
            )
        return mc

    def update_aad_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update aad profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_enable_aad():
            mc.aad_profile = self.models.ManagedClusterAADProfile(
                managed=True
            )

        aad_tenant_id = self.context.get_aad_tenant_id()
        aad_admin_group_object_ids = self.context.get_aad_admin_group_object_ids()
        enable_azure_rbac = self.context.get_enable_azure_rbac()
        disable_azure_rbac = self.context.get_disable_azure_rbac()
        if aad_tenant_id is not None:
            mc.aad_profile.tenant_id = aad_tenant_id
        if aad_admin_group_object_ids is not None:
            # ids -> i_ds due to track 2 naming issue
            mc.aad_profile.admin_group_object_i_ds = aad_admin_group_object_ids
        if enable_azure_rbac:
            mc.aad_profile.enable_azure_rbac = True
        if disable_azure_rbac:
            mc.aad_profile.enable_azure_rbac = False
        return mc

    def update_auto_upgrade_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update auto upgrade profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        auto_upgrade_channel = self.context.get_auto_upgrade_channel()
        if auto_upgrade_channel is not None:
            if mc.auto_upgrade_profile is None:
                mc.auto_upgrade_profile = self.models.ManagedClusterAutoUpgradeProfile()
            mc.auto_upgrade_profile.upgrade_channel = auto_upgrade_channel
        return mc

    def update_identity(self, mc: ManagedCluster) -> ManagedCluster:
        """Update identity for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        current_identity_type = "spn"
        if mc.identity is not None:
            current_identity_type = mc.identity.type.casefold()

        goal_identity_type = current_identity_type
        assign_identity = self.context.get_assign_identity()
        if self.context.get_enable_managed_identity():
            if not assign_identity:
                goal_identity_type = "systemassigned"
            else:
                goal_identity_type = "userassigned"

        if current_identity_type != goal_identity_type:
            if current_identity_type == "spn":
                msg = (
                    "Your cluster is using service principal, and you are going to update "
                    "the cluster to use {} managed identity.\nAfter updating, your "
                    "cluster's control plane and addon pods will switch to use managed "
                    "identity, but kubelet will KEEP USING SERVICE PRINCIPAL "
                    "until you upgrade your agentpool.\n"
                    "Are you sure you want to perform this operation?"
                ).format(goal_identity_type)
            else:
                msg = (
                    "Your cluster is already using {} managed identity, and you are going to "
                    "update the cluster to use {} managed identity.\n"
                    "Are you sure you want to perform this operation?"
                ).format(current_identity_type, goal_identity_type)
            # gracefully exit if user does not confirm
            if not self.context.get_yes() and not prompt_y_n(msg, default="n"):
                raise DecoratorEarlyExitException
            # update identity
            if goal_identity_type == "systemassigned":
                identity = self.models.ManagedClusterIdentity(
                    type="SystemAssigned"
                )
            elif goal_identity_type == "userassigned":
                user_assigned_identity = {
                    assign_identity: self.models.ManagedServiceIdentityUserAssignedIdentitiesValue()
                }
                identity = self.models.ManagedClusterIdentity(
                    type="UserAssigned",
                    user_assigned_identities=user_assigned_identity
                )
            mc.identity = identity
        return mc

    def update_azure_keyvault_secrets_provider_addon_profile(
        self,
        azure_keyvault_secrets_provider_addon_profile: ManagedClusterAddonProfile,
    ) -> None:
        """Update azure keyvault secrets provider addon profile in-place.

        :return: None
        """
        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_SECRET_ROTATION_ENABLED = addon_consts.get(
            "CONST_SECRET_ROTATION_ENABLED"
        )
        CONST_ROTATION_POLL_INTERVAL = addon_consts.get(
            "CONST_ROTATION_POLL_INTERVAL"
        )

        if self.context.get_enable_secret_rotation():
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_SECRET_ROTATION_ENABLED
            ] = "true"

        if self.context.get_disable_secret_rotation():
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_SECRET_ROTATION_ENABLED
            ] = "false"

        if self.context.get_rotation_poll_interval() is not None:
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_ROTATION_POLL_INTERVAL
            ] = self.context.get_rotation_poll_interval()

    def update_addon_profiles(self, mc: ManagedCluster) -> ManagedCluster:
        """Update addon profiles for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_MONITORING_ADDON_NAME = addon_consts.get(
            "CONST_MONITORING_ADDON_NAME"
        )
        CONST_INGRESS_APPGW_ADDON_NAME = addon_consts.get(
            "CONST_INGRESS_APPGW_ADDON_NAME"
        )
        CONST_VIRTUAL_NODE_ADDON_NAME = addon_consts.get(
            "CONST_VIRTUAL_NODE_ADDON_NAME"
        )
        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME = addon_consts.get(
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME"
        )

        azure_keyvault_secrets_provider_addon_profile = None
        if mc.addon_profiles is not None:
            monitoring_addon_enabled = (
                CONST_MONITORING_ADDON_NAME in mc.addon_profiles and
                mc.addon_profiles[CONST_MONITORING_ADDON_NAME].enabled
            )
            ingress_appgw_addon_enabled = (
                CONST_INGRESS_APPGW_ADDON_NAME in mc.addon_profiles and
                mc.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME].enabled
            )
            virtual_node_addon_enabled = (
                CONST_VIRTUAL_NODE_ADDON_NAME + self.context.get_virtual_node_addon_os_type() in mc.addon_profiles and
                mc.addon_profiles[CONST_VIRTUAL_NODE_ADDON_NAME + self.context.get_virtual_node_addon_os_type()].enabled
            )
            # set intermediates, used later to ensure role assignments
            self.context.set_intermediate(
                "monitoring_addon_enabled", monitoring_addon_enabled, overwrite_exists=True
            )
            self.context.set_intermediate(
                "ingress_appgw_addon_enabled", ingress_appgw_addon_enabled, overwrite_exists=True
            )
            self.context.set_intermediate(
                "virtual_node_addon_enabled", virtual_node_addon_enabled, overwrite_exists=True
            )
            # get azure keyvault secrets provider profile
            azure_keyvault_secrets_provider_addon_profile = mc.addon_profiles.get(
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
            )

        # update azure keyvault secrets provider profile in-place
        self.update_azure_keyvault_secrets_provider_addon_profile(azure_keyvault_secrets_provider_addon_profile)
        return mc

    def update_mc_profile_default(self) -> ManagedCluster:
        """The overall controller used to update the default ManagedCluster profile.

        Note: To reduce the risk of regression introduced by refactoring, this function is not complete and is being
        implemented gradually.

        The completely updated ManagedCluster object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the ManagedCluster object
        """
        # check raw parameters
        self.check_raw_parameters()
        # fetch the ManagedCluster object
        mc = self.fetch_mc()
        # update agentpool profile
        mc = self.update_agentpool_profile(mc)
        # update auto scaler profile
        mc = self.update_auto_scaler_profile(mc)
        # update tags
        mc = self.update_tags(mc)
        # attach or detach acr (add or delete role assignment for acr)
        self.process_attach_detach_acr(mc)
        # update sku (uptime sla)
        mc = self.update_sku(mc)
        # update load balancer profile
        mc = self.update_load_balancer_profile(mc)
        # update nat gateway profile
        mc = self.update_nat_gateway_profile(mc)
        # update disable/enable local accounts
        mc = self.update_disable_local_accounts(mc)
        # update api server access profile
        mc = self.update_api_server_access_profile(mc)
        # update windows profile
        mc = self.update_windows_profile(mc)
        # update aad profile
        mc = self.update_aad_profile(mc)
        # update auto upgrade profile
        mc = self.update_auto_upgrade_profile(mc)
        # update identity
        mc = self.update_identity(mc)
        # update addon profiles
        mc = self.update_addon_profiles(mc)
        return mc

    # pylint: disable=unused-argument
    def check_is_postprocessing_required(self, mc: ManagedCluster) -> bool:
        """Helper function to check if postprocessing is required after sending a PUT request to create the cluster.

        :return: bool
        """
        # some addons require post cluster creation role assigment
        monitoring_addon_enabled = self.context.get_intermediate("monitoring_addon_enabled", default_value=False)
        ingress_appgw_addon_enabled = self.context.get_intermediate("ingress_appgw_addon_enabled", default_value=False)
        virtual_node_addon_enabled = self.context.get_intermediate("virtual_node_addon_enabled", default_value=False)
        enable_managed_identity = check_is_msi_cluster(mc)
        attach_acr = self.context.get_attach_acr()

        if (
            monitoring_addon_enabled or
            ingress_appgw_addon_enabled or
            virtual_node_addon_enabled or
            (enable_managed_identity and attach_acr)
        ):
            return True
        return False

    # pylint: disable=unused-argument
    def immediate_processing_after_request(self, mc: ManagedCluster) -> None:
        """Immediate processing performed when the cluster has not finished creating after a PUT request to the cluster
        has been sent.

        :return: None
        """
        return

    def postprocessing_after_mc_created(self, cluster: ManagedCluster) -> None:
        """Postprocessing performed after the cluster is created.

        :return: None
        """
        # monitoring addon
        monitoring_addon_enabled = self.context.get_intermediate("monitoring_addon_enabled", default_value=False)
        if monitoring_addon_enabled:
            enable_msi_auth_for_monitoring = self.context.get_enable_msi_auth_for_monitoring()
            if not enable_msi_auth_for_monitoring:
                # add cluster spn/msi Monitoring Metrics Publisher role assignment to publish metrics to MDM
                # mdm metrics is supported only in azure public cloud, so add the role assignment only in this cloud
                cloud_name = self.cmd.cli_ctx.cloud.name
                if cloud_name.lower() == "azurecloud":
                    from msrestazure.tools import resource_id

                    cluster_resource_id = resource_id(
                        subscription=self.context.get_subscription_id(),
                        resource_group=self.context.get_resource_group_name(),
                        namespace="Microsoft.ContainerService",
                        type="managedClusters",
                        name=self.context.get_name(),
                    )
                    self.context.external_functions.add_monitoring_role_assignment(
                        cluster, cluster_resource_id, self.cmd
                    )
            else:
                # Create the DCR Association here
                addon_consts = self.context.get_addon_consts()
                CONST_MONITORING_ADDON_NAME = addon_consts.get("CONST_MONITORING_ADDON_NAME")
                self.context.external_functions.ensure_container_insights_for_monitoring(
                    self.cmd,
                    cluster.addon_profiles[CONST_MONITORING_ADDON_NAME],
                    self.context.get_subscription_id(),
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    self.context.get_location(),
                    remove_monitoring=False,
                    aad_route=self.context.get_enable_msi_auth_for_monitoring(),
                    create_dcr=False,
                    create_dcra=True,
                )

        # ingress appgw addon
        ingress_appgw_addon_enabled = self.context.get_intermediate("ingress_appgw_addon_enabled", default_value=False)
        if ingress_appgw_addon_enabled:
            self.context.external_functions.add_ingress_appgw_addon_role_assignment(cluster, self.cmd)

        # virtual node addon
        virtual_node_addon_enabled = self.context.get_intermediate("virtual_node_addon_enabled", default_value=False)
        if virtual_node_addon_enabled:
            self.context.external_functions.add_virtual_node_role_assignment(
                self.cmd, cluster, self.context.get_vnet_subnet_id()
            )

        # attach acr
        enable_managed_identity = check_is_msi_cluster(cluster)
        attach_acr = self.context.get_attach_acr()
        if enable_managed_identity and attach_acr:
            # Attach ACR to cluster enabled managed identity
            if cluster.identity_profile is None or cluster.identity_profile["kubeletidentity"] is None:
                logger.warning(
                    "Your cluster is successfully created, but we failed to attach "
                    "acr to it, you can manually grant permission to the identity "
                    "named <ClUSTER_NAME>-agentpool in MC_ resource group to give "
                    "it permission to pull from ACR."
                )
            else:
                kubelet_identity_object_id = cluster.identity_profile["kubeletidentity"].object_id
                self.context.external_functions.ensure_aks_acr(
                    self.cmd,
                    assignee=kubelet_identity_object_id,
                    acr_name_or_id=attach_acr,
                    subscription_id=self.context.get_subscription_id(),
                    is_service_principal=False,
                )

    def put_mc(self, mc: ManagedCluster) -> ManagedCluster:
        if self.check_is_postprocessing_required(mc):
            # send request
            poller = self.client.begin_create_or_update(
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
            )
            self.immediate_processing_after_request(mc)
            # poll until the result is returned
            cluster = LongRunningOperation(self.cmd.cli_ctx)(poller)
            self.postprocessing_after_mc_created(cluster)
        else:
            cluster = sdk_no_wait(
                self.context.get_no_wait(),
                self.client.begin_create_or_update,
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
            )
        return cluster

    def update_mc(self, mc: ManagedCluster) -> ManagedCluster:
        """Send request to update the existing managed cluster.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        return self.put_mc(mc)

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import copy
import os
import re
import time
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple, TypeVar, Union
import datetime
from dateutil.parser import parse

from azure.mgmt.containerservice.models import KubernetesSupportPlan

from azure.cli.command_modules.acs._client_factory import get_graph_client
from azure.cli.command_modules.acs._consts import (
    CONST_LOAD_BALANCER_SKU_BASIC,
    CONST_LOAD_BALANCER_SKU_STANDARD,
    CONST_MANAGED_CLUSTER_SKU_NAME_BASE,
    CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC,
    CONST_MANAGED_CLUSTER_SKU_TIER_FREE,
    CONST_MANAGED_CLUSTER_SKU_TIER_STANDARD,
    CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM,
    CONST_OUTBOUND_TYPE_LOAD_BALANCER,
    CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY,
    CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY,
    CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
    CONST_OUTBOUND_TYPE_NONE,
    CONST_PRIVATE_DNS_ZONE_NONE,
    CONST_PRIVATE_DNS_ZONE_SYSTEM,
    CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE,
    CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PUBLIC,
    AgentPoolDecoratorMode,
    DecoratorEarlyExitException,
    DecoratorMode,
    CONST_AZURE_SERVICE_MESH_MODE_DISABLED,
    CONST_AZURE_SERVICE_MESH_MODE_ISTIO,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK,
    CONST_AZURE_SERVICE_MESH_DEFAULT_EGRESS_NAMESPACE,
    CONST_PRIVATE_DNS_ZONE_CONTRIBUTOR_ROLE,
    CONST_DNS_ZONE_CONTRIBUTOR_ROLE,
    CONST_ARTIFACT_SOURCE_CACHE,
    CONST_NONE_UPGRADE_CHANNEL,
    CONST_AVAILABILITY_SET,
    CONST_VIRTUAL_MACHINES,
)
from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
    CONST_ACSTOR_EXT_INSTALLATION_NAME,
    CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
    CONST_ACSTOR_VERSION_V1,
)
from azure.cli.command_modules.acs._helpers import (
    check_is_managed_aad_cluster,
    check_is_msi_cluster,
    check_is_apiserver_vnet_integration_cluster,
    check_is_private_cluster,
    format_parameter_name_to_option_name,
    get_user_assigned_identity_by_resource_id,
    get_shared_control_plane_identity,
    map_azure_error_to_cli_error,
    safe_list_get,
    safe_lower,
    sort_asm_revisions,
    use_shared_identity,
)
from azure.cli.command_modules.acs._loadbalancer import create_load_balancer_profile
from azure.cli.command_modules.acs._loadbalancer import update_load_balancer_profile as _update_load_balancer_profile
from azure.cli.command_modules.acs._natgateway import create_nat_gateway_profile
from azure.cli.command_modules.acs._natgateway import update_nat_gateway_profile as _update_nat_gateway_profile
from azure.cli.command_modules.acs._resourcegroup import get_rg_location
from azure.cli.command_modules.acs._roleassignments import (
    add_role_assignment,
    add_role_assignment_executor,
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
from azure.cli.command_modules.acs.azurecontainerstorage.acstor_ops import (
    perform_disable_azure_container_storage_v1,
    perform_enable_azure_container_storage_v1,
    perform_azure_container_storage_update,
)
from azure.cli.command_modules.acs.azuremonitormetrics.azuremonitorprofile import (
    ensure_azure_monitor_profile_prerequisites
)
from azure.cli.command_modules.acs.base_decorator import (
    BaseAKSContext,
    BaseAKSManagedClusterDecorator,
    BaseAKSParamDict,
)
from azure.cli.core import AzCommandsLoader
from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    AzCLIError,
    CLIInternalError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    NoTTYError,
    RequiredArgumentMissingError,
    UnknownError,
)
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.commands import AzCliCommand, LongRunningOperation
from azure.cli.core.keys import is_valid_ssh_rsa_public_key
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait, truncate_text, get_file_json, read_file_content
from azure.core.exceptions import HttpResponseError
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt, prompt_pass, prompt_y_n
from knack.util import CLIError

logger = get_logger(__name__)

# type variables
ContainerServiceClient = TypeVar("ContainerServiceClient")
Identity = TypeVar("Identity")
ManagedCluster = TypeVar("ManagedCluster")
ManagedClusterHTTPProxyConfig = TypeVar("ManagedClusterHTTPProxyConfig")
ManagedClusterLoadBalancerProfile = TypeVar("ManagedClusterLoadBalancerProfile")
ManagedClusterPropertiesAutoScalerProfile = TypeVar("ManagedClusterPropertiesAutoScalerProfile")
ResourceReference = TypeVar("ResourceReference")
ManagedClusterAddonProfile = TypeVar("ManagedClusterAddonProfile")
Snapshot = TypeVar("Snapshot")
KubeletConfig = TypeVar("KubeletConfig")
LinuxOSConfig = TypeVar("LinuxOSConfig")
ManagedClusterSecurityProfileWorkloadIdentity = TypeVar("ManagedClusterSecurityProfileWorkloadIdentity")
ManagedClusterOIDCIssuerProfile = TypeVar("ManagedClusterOIDCIssuerProfile")
ManagedClusterSecurityProfileDefender = TypeVar("ManagedClusterSecurityProfileDefender")
ManagedClusterStorageProfile = TypeVar('ManagedClusterStorageProfile')
ManagedClusterStorageProfileDiskCSIDriver = TypeVar('ManagedClusterStorageProfileDiskCSIDriver')
ManagedClusterStorageProfileFileCSIDriver = TypeVar('ManagedClusterStorageProfileFileCSIDriver')
ManagedClusterStorageProfileBlobCSIDriver = TypeVar('ManagedClusterStorageProfileBlobCSIDriver')
ManagedClusterStorageProfileSnapshotController = TypeVar('ManagedClusterStorageProfileSnapshotController')
ManagedClusterIngressProfile = TypeVar("ManagedClusterIngressProfile")
ManagedClusterIngressProfileWebAppRouting = TypeVar("ManagedClusterIngressProfileWebAppRouting")
ManagedClusterIngressProfileNginx = TypeVar("ManagedClusterIngressProfileNginx")
ServiceMeshProfile = TypeVar("ServiceMeshProfile")

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
        # holder for maintenance configuration related models
        self.__maintenance_configuration_models = None

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

    @property
    def maintenance_configuration_models(self) -> SimpleNamespace:
        """Get maintenance configuration related models.

        The models are stored in a SimpleNamespace object, could be accessed by the dot operator like
        `maintenance_configuration_models.ManagedClusterMaintenanceConfigurationProfile`.

        :return: SimpleNamespace
        """
        if self.__maintenance_configuration_models is None:
            maintenance_configuration_models = {}
            # getting maintenance configuration related models
            maintenance_configuration_models["MaintenanceConfiguration"] = self.MaintenanceConfiguration
            maintenance_configuration_models["MaintenanceConfigurationListResult"] = self.MaintenanceConfigurationListResult
            maintenance_configuration_models["MaintenanceWindow"] = self.MaintenanceWindow
            maintenance_configuration_models["Schedule"] = self.Schedule
            maintenance_configuration_models["DailySchedule"] = self.DailySchedule
            maintenance_configuration_models["WeeklySchedule"] = self.WeeklySchedule
            maintenance_configuration_models["AbsoluteMonthlySchedule"] = self.AbsoluteMonthlySchedule
            maintenance_configuration_models["RelativeMonthlySchedule"] = self.RelativeMonthlySchedule
            maintenance_configuration_models["TimeSpan"] = self.TimeSpan
            maintenance_configuration_models["TimeInWeek"] = self.TimeInWeek
            self.__maintenance_configuration_models = SimpleNamespace(**maintenance_configuration_models)
        return self.__maintenance_configuration_models


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
            external_functions["add_role_assignment_executor"] = add_role_assignment_executor
            external_functions["add_ingress_appgw_addon_role_assignment"] = add_ingress_appgw_addon_role_assignment
            external_functions["add_monitoring_role_assignment"] = add_monitoring_role_assignment
            external_functions["add_virtual_node_role_assignment"] = add_virtual_node_role_assignment
            external_functions["ensure_container_insights_for_monitoring"] = ensure_container_insights_for_monitoring
            external_functions[
                "ensure_azure_monitor_profile_prerequisites"
            ] = ensure_azure_monitor_profile_prerequisites
            external_functions[
                "ensure_default_log_analytics_workspace_for_monitoring"
            ] = ensure_default_log_analytics_workspace_for_monitoring
            external_functions["ensure_aks_acr"] = ensure_aks_acr
            external_functions[
                "ensure_cluster_identity_permission_on_kubelet_identity"
            ] = ensure_cluster_identity_permission_on_kubelet_identity
            external_functions["subnet_role_assignment_exists"] = subnet_role_assignment_exists
            # azure container storage functions
            external_functions["perform_enable_azure_container_storage_v1"] = perform_enable_azure_container_storage_v1
            external_functions["perform_disable_azure_container_storage_v1"] = perform_disable_azure_container_storage_v1
            external_functions["perform_azure_container_storage_update"] = perform_azure_container_storage_update
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
        disable_windows_gmsa,
        gmsa_dns_server,
        gmsa_root_domain_name,
        yes,
    ) -> None:
        """Helper function to validate gmsa related options.

        When enable_windows_gmsa is specified, a InvalidArgumentValueError will be raised if disable_windows_gmsa
        is also specified; if both gmsa_dns_server and gmsa_root_domain_name are not assigned and user does not
        confirm the operation, a DecoratorEarlyExitException will be raised; if only one of gmsa_dns_server or
        gmsa_root_domain_name is assigned, raise a RequiredArgumentMissingError. When enable_windows_gmsa is
        not specified, if any of gmsa_dns_server or gmsa_root_domain_name is assigned, raise a RequiredArgumentMissingError.
        When disable_windows_gmsa is specified, if gmsa_dns_server or gmsa_root_domain_name is
        assigned, raise a InvalidArgumentValueError.

        :return: bool
        """
        if enable_windows_gmsa:
            if disable_windows_gmsa:
                raise InvalidArgumentValueError(
                    "You should not set --disable-windows-gmsa "
                    "when setting --enable-windows-gmsa."
                )
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
            if not disable_windows_gmsa:
                if any([gmsa_dns_server, gmsa_root_domain_name]):
                    raise RequiredArgumentMissingError(
                        "You only can set --gmsa-dns-server and --gmsa-root-domain-name "
                        "when setting --enable-windows-gmsa."
                    )

        if disable_windows_gmsa:
            if any([gmsa_dns_server, gmsa_root_domain_name]):
                raise InvalidArgumentValueError(
                    "You should not set --gmsa-dns-server nor --gmsa-root-domain-name "
                    "when setting --disable-windows-gmsa."
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

    def get_disk_driver(self) -> Optional[ManagedClusterStorageProfileDiskCSIDriver]:
        """Obtain the value of storage_profile.disk_csi_driver

        :return: Optional[ManagedClusterStorageProfileDiskCSIDriver]
        """
        enable_disk_driver = self.raw_param.get("enable_disk_driver")
        disable_disk_driver = self.raw_param.get("disable_disk_driver")

        if not enable_disk_driver and not disable_disk_driver:
            return None
        profile = self.models.ManagedClusterStorageProfileDiskCSIDriver()

        if enable_disk_driver and disable_disk_driver:
            raise MutuallyExclusiveArgumentError(
                "Cannot specify --enable-disk-driver and "
                "--disable-disk-driver at the same time."
            )

        if self.decorator_mode == DecoratorMode.CREATE:
            if disable_disk_driver:
                profile.enabled = False
            else:
                profile.enabled = True

        if self.decorator_mode == DecoratorMode.UPDATE:
            if enable_disk_driver:
                profile.enabled = True
            elif disable_disk_driver:
                msg = (
                    "Please make sure there are no existing PVs and PVCs "
                    "that are used by AzureDisk CSI driver before disabling."
                )
                if not self.get_yes() and not prompt_y_n(msg, default="n"):
                    raise DecoratorEarlyExitException()
                profile.enabled = False

        return profile

    def get_file_driver(self) -> Optional[ManagedClusterStorageProfileFileCSIDriver]:
        """Obtain the value of storage_profile.file_csi_driver

        :return: Optional[ManagedClusterStorageProfileFileCSIDriver]
        """
        enable_file_driver = self.raw_param.get("enable_file_driver")
        disable_file_driver = self.raw_param.get("disable_file_driver")

        if not enable_file_driver and not disable_file_driver:
            return None
        profile = self.models.ManagedClusterStorageProfileFileCSIDriver()

        if enable_file_driver and disable_file_driver:
            raise MutuallyExclusiveArgumentError(
                "Cannot specify --enable-file-driver and "
                "--disable-file-driver at the same time."
            )

        if self.decorator_mode == DecoratorMode.CREATE:
            if disable_file_driver:
                profile.enabled = False

        if self.decorator_mode == DecoratorMode.UPDATE:
            if enable_file_driver:
                profile.enabled = True
            elif disable_file_driver:
                msg = (
                    "Please make sure there are no existing PVs and PVCs "
                    "that are used by AzureFile CSI driver before disabling."
                )
                if not self.get_yes() and not prompt_y_n(msg, default="n"):
                    raise DecoratorEarlyExitException()
                profile.enabled = False

        return profile

    def get_blob_driver(self) -> Optional[ManagedClusterStorageProfileBlobCSIDriver]:
        """Obtain the value of storage_profile.blob_csi_driver
        :return: Optional[ManagedClusterStorageProfileBlobCSIDriver]
        """
        enable_blob_driver = self.raw_param.get("enable_blob_driver")
        disable_blob_driver = self.raw_param.get("disable_blob_driver")

        if enable_blob_driver is None and disable_blob_driver is None:
            return None

        profile = self.models.ManagedClusterStorageProfileBlobCSIDriver()

        if enable_blob_driver and disable_blob_driver:
            raise MutuallyExclusiveArgumentError(
                "Cannot specify --enable-blob-driver and "
                "--disable-blob-driver at the same time."
            )

        if self.decorator_mode == DecoratorMode.CREATE:
            if enable_blob_driver:
                profile.enabled = True

        if self.decorator_mode == DecoratorMode.UPDATE:
            if enable_blob_driver:
                msg = "Please make sure there is no open-source Blob CSI driver installed before enabling."
                if not self.get_yes() and not prompt_y_n(msg, default="n"):
                    raise DecoratorEarlyExitException()
                profile.enabled = True
            elif disable_blob_driver:
                msg = (
                    "Please make sure there are no existing PVs and PVCs "
                    "that are used by Blob CSI driver before disabling."
                )
                if not self.get_yes() and not prompt_y_n(msg, default="n"):
                    raise DecoratorEarlyExitException()
                profile.enabled = False

        return profile

    def get_enable_app_routing(self) -> bool:
        """Obtain the value of enable_app_routing.

        :return: bool
        """
        return self.raw_param.get("enable_app_routing")

    def get_enable_kv(self) -> bool:
        """Obtain the value of enable_kv.

        :return: bool
        """
        return self.raw_param.get("enable_kv")

    def get_dns_zone_resource_ids(self) -> Union[list, None]:
        """Obtain the value of dns_zone_resource_ids.

        :return: list or None
        """
        # read the original value passed by the command
        dns_zone_resource_ids = self.raw_param.get("dns_zone_resource_ids")
        # normalize
        dns_zone_resource_ids = [
            x.strip()
            for x in (
                dns_zone_resource_ids.split(",")
                if dns_zone_resource_ids
                else []
            )
        ]
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            self.mc and
            self.mc.ingress_profile and
            self.mc.ingress_profile.web_app_routing and
            self.mc.ingress_profile.web_app_routing.dns_zone_resource_ids is not None
        ):
            dns_zone_resource_ids = self.mc.ingress_profile.web_app_routing.dns_zone_resource_ids

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return dns_zone_resource_ids

    def get_dns_zone_resource_ids_from_input(self) -> Union[List[str], None]:
        """Obtain the value of dns_zone_resource_ids from the input.

        :return: list of str or None
        """
        dns_zone_resource_ids_input = self.raw_param.get("dns_zone_resource_ids")
        dns_zone_resource_ids = []

        if dns_zone_resource_ids_input:
            for dns_zone in dns_zone_resource_ids_input.split(","):
                dns_zone = dns_zone.strip()
                if dns_zone and is_valid_resource_id(dns_zone):
                    dns_zone_resource_ids.append(dns_zone)
                else:
                    raise CLIError(dns_zone, " is not a valid Azure DNS Zone resource ID.")

        return dns_zone_resource_ids

    def get_keyvault_id(self) -> str:
        """Obtain the value of keyvault_id.

        :return: str
        """
        return self.raw_param.get("keyvault_id")

    def get_attach_zones(self) -> bool:
        """Obtain the value of attach_zones.

        :return: bool
        """
        return self.raw_param.get("attach_zones")

    def get_add_dns_zone(self) -> bool:
        """Obtain the value of add_dns_zone.

        :return: bool
        """
        return self.raw_param.get("add_dns_zone")

    def get_delete_dns_zone(self) -> bool:
        """Obtain the value of delete_dns_zone.

        :return: bool
        """
        return self.raw_param.get("delete_dns_zone")

    def get_update_dns_zone(self) -> bool:
        """Obtain the value of update_dns_zone.

        :return: bool
        """
        return self.raw_param.get("update_dns_zone")

    def get_app_routing_default_nginx_controller(self) -> str:
        """Obtain the value of app_routing_default_nginx_controller.
        :return: str
        """
        return self.raw_param.get("app_routing_default_nginx_controller")

    def get_nginx(self):
        """Obtain the value of nginx, written to the update decorator context by _aks_approuting_update
        :return: string
        """
        return self.raw_param.get("nginx")

    def get_enable_keda(self) -> bool:
        """Obtain the value of enable_keda.

        This function will verify the parameter by default. If both enable_keda and disable_keda are specified, raise a
        MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_enable_keda(enable_validation=True)

    def _get_enable_keda(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_keda.

        This function supports the option of enable_validation. When enabled, if both enable_keda and disable_keda are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # Read the original value passed by the command.
        enable_keda = self.raw_param.get("enable_keda")

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "workload_auto_scaler_profile") and  # backward compatibility
                self.mc.workload_auto_scaler_profile and
                self.mc.workload_auto_scaler_profile.keda
            ):
                enable_keda = self.mc.workload_auto_scaler_profile.keda.enabled

        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_keda and self._get_disable_keda(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-keda and --disable-keda at the same time."
                )

        return enable_keda

    def get_disable_keda(self) -> bool:
        """Obtain the value of disable_keda.

        This function will verify the parameter by default. If both enable_keda and disable_keda are specified, raise a
        MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_disable_keda(enable_validation=True)

    def _get_disable_keda(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_keda.

        This function supports the option of enable_validation. When enabled, if both enable_keda and disable_keda are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # Read the original value passed by the command.
        disable_keda = self.raw_param.get("disable_keda")

        # This option is not supported in create mode, hence we do not read the property value from the `mc` object.
        # This parameter does not need dynamic completion.
        if enable_validation:
            if disable_keda and self._get_enable_keda(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-keda and --disable-keda at the same time."
                )

        return disable_keda

    def get_custom_ca_trust_certificates(self) -> Union[List[bytes], None]:
        """Obtain the value of custom ca trust certificates.
        :return: List[str] or None
        """
        custom_ca_certs_file_path = self.raw_param.get("custom_ca_trust_certificates")
        if custom_ca_certs_file_path is None:
            return None
        # Reject empty string - user must provide a valid file path
        if custom_ca_certs_file_path == "":
            raise InvalidArgumentValueError(
                "custom_ca_trust_certificates cannot be an empty string. Please provide a valid file path."
            )
        if not os.path.isfile(custom_ca_certs_file_path):
            raise InvalidArgumentValueError(
                "{} is not valid file, or not accessible.".format(
                    custom_ca_certs_file_path
                )
            )
        # CAs are supposed to be separated with a new line, we filter out empty strings (e.g. some stray new line). We only allow up to 10 CAs
        file_content = read_file_content(custom_ca_certs_file_path).split(os.linesep + os.linesep)
        certs = [str.encode(x) for x in file_content if len(x) > 1]
        if len(certs) > 10:
            raise InvalidArgumentValueError(
                "Only up to 10 new-line separated CAs can be passed, got {} instead.".format(
                    len(certs)
                )
            )
        return certs

    def _get_enable_run_command(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_run_command.
        :return: bool
        """
        enable_run_command = self.raw_param.get("enable_run_command")

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "api_server_access_profile") and  # backward compatibility
                self.mc.api_server_access_profile and
                self.mc.api_server_access_profile.disable_run_command is not None
            ):
                enable_run_command = not self.mc.api_server_access_profile.disable_run_command

        # validation
        if enable_validation:
            if enable_run_command and self._get_disable_run_command(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-run-command and --disable-run-command at the same time."
                )

        return enable_run_command

    def get_enable_run_command(self) -> bool:
        """Obtain the value of enable_run_command.
        This function will verify the parameter by default. If both enable_run_command and disable_run_command are
        specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_enable_run_command(enable_validation=True)

    def _get_disable_run_command(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_run_command.
        :return: bool
        """
        disable_run_command = self.raw_param.get("disable_run_command")

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "api_server_access_profile") and  # backward compatibility
                self.mc.api_server_access_profile and
                self.mc.api_server_access_profile.disable_run_command is not None
            ):
                disable_run_command = self.mc.api_server_access_profile.disable_run_command

        # validation
        if enable_validation:
            if disable_run_command and self._get_enable_run_command(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-run-command and --disable-run-command at the same time."
                )
        return disable_run_command

    def get_disable_run_command(self) -> bool:
        """Obtain the value of disable_run_command.
        This function will verify the parameter by default. If both enable_run_command and disable_run_command
        are specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_disable_run_command(enable_validation=True)

    def get_snapshot_controller(self) -> Optional[ManagedClusterStorageProfileSnapshotController]:
        """Obtain the value of storage_profile.snapshot_controller

        :return: Optional[ManagedClusterStorageProfileSnapshotController]
        """
        enable_snapshot_controller = self.raw_param.get("enable_snapshot_controller")
        disable_snapshot_controller = self.raw_param.get("disable_snapshot_controller")

        if not enable_snapshot_controller and not disable_snapshot_controller:
            return None

        profile = self.models.ManagedClusterStorageProfileSnapshotController()

        if enable_snapshot_controller and disable_snapshot_controller:
            raise MutuallyExclusiveArgumentError(
                "Cannot specify --enable-snapshot_controller and "
                "--disable-snapshot_controller at the same time."
            )

        if self.decorator_mode == DecoratorMode.CREATE:
            if disable_snapshot_controller:
                profile.enabled = False

        if self.decorator_mode == DecoratorMode.UPDATE:
            if enable_snapshot_controller:
                profile.enabled = True
            elif disable_snapshot_controller:
                msg = (
                    "Please make sure there are no existing "
                    "VolumeSnapshots, VolumeSnapshotClasses and VolumeSnapshotContents "
                    "that are used by the snapshot controller before disabling."
                )
                if not self.get_yes() and not prompt_y_n(msg, default="n"):
                    raise DecoratorEarlyExitException()
                profile.enabled = False

        return profile

    def get_storage_profile(self) -> Optional[ManagedClusterStorageProfile]:
        """Obtain the value of storage_profile.

        :return: Optional[ManagedClusterStorageProfile]
        """
        profile = self.models.ManagedClusterStorageProfile()
        if self.mc.storage_profile is not None:
            profile = self.mc.storage_profile
        profile.disk_csi_driver = self.get_disk_driver()
        profile.file_csi_driver = self.get_file_driver()
        profile.blob_csi_driver = self.get_blob_driver()
        profile.snapshot_controller = self.get_snapshot_controller()

        return profile

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

    def get_nodepool_taints(self) -> Union[List[str], None]:
        """Obtain the value of nodepool_labels.

        :return: dictionary or None
        """
        return self.agentpool_context.get_node_taints()

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
                enable_windows_gmsa, self._get_disable_windows_gmsa(enable_validation=False), gmsa_dns_server, gmsa_root_domain_name, self.get_yes()
            )
        return enable_windows_gmsa

    def get_enable_windows_gmsa(self) -> bool:
        """Obtain the value of enable_windows_gmsa.

        This function will verify the parameter by default. When enable_windows_gmsa is specified, a ; if both
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
                self._get_disable_windows_gmsa(enable_validation=False),
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

    def _get_disable_windows_gmsa(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_windows_gmsa.

        This function supports the option of enable_validation. Please refer to function __validate_gmsa_options for
        details of validation.

        :return: bool
        """
        # disable_windows_gmsa is only supported in UPDATE
        if self.decorator_mode == DecoratorMode.CREATE:
            disable_windows_gmsa = False
        else:
            # read the original value passed by the command
            disable_windows_gmsa = self.raw_param.get("disable_windows_gmsa")

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
                self._get_enable_windows_gmsa(enable_validation=False),
                disable_windows_gmsa,
                gmsa_dns_server,
                gmsa_root_domain_name,
                self.get_yes(),
            )
        return disable_windows_gmsa

    def get_disable_windows_gmsa(self) -> bool:
        """Obtain the value of disable_windows_gmsa.

        This function will verify the parameter by default. When disable_windows_gmsa is specified, if
        gmsa_dns_server or gmsa_root_domain_name is assigned, a InvalidArgumentValueError will be raised;

        :return: bool
        """
        return self._get_disable_windows_gmsa(enable_validation=True)

    # pylint: disable=too-many-statements
    def _get_service_principal_and_client_secret(
        self, enable_validation: bool = False, read_only: bool = False
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Internal function to dynamically obtain the values of service_principal and client_secret according to the
        context.

        This function supports the option of enable_validation.

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

        # these parameters do not need dynamic completion

        # validation
        if enable_validation:
            # only one of service_principal and client_secret is provided, not both
            if (service_principal or client_secret) and not (service_principal and client_secret):
                raise RequiredArgumentMissingError(
                    "Please provide both --service-principal and --client-secret to use sp as the cluster identity. "
                    "An sp can be created using the 'az ad sp create-for-rbac' command."
                )
        return service_principal, client_secret

    def get_service_principal_and_client_secret(
        self
    ) -> Tuple[Union[str, None], Union[str, None]]:
        """Dynamically obtain the values of service_principal and client_secret according to the context.

        :return: a tuple containing two elements: service_principal of string type or None and client_secret of
        string type or None
        """
        return self._get_service_principal_and_client_secret(enable_validation=True)

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
        if self.decorator_mode == DecoratorMode.CREATE:
            if self.mc and self.mc.identity:
                enable_managed_identity = check_is_msi_cluster(self.mc)

        # skip dynamic completion & validation if option read_only is specified
        if read_only:
            return enable_managed_identity

        # dynamic completion for create mode only
        if self.decorator_mode == DecoratorMode.CREATE:
            # if user does not specify service principal or client secret,
            # backfill the value of enable_managed_identity to True
            (
                service_principal,
                client_secret,
            ) = self._get_service_principal_and_client_secret(read_only=True)
            if not (service_principal or client_secret) and not enable_managed_identity:
                enable_managed_identity = True

        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                (
                    service_principal,
                    client_secret,
                ) = self._get_service_principal_and_client_secret(read_only=True)
                if (service_principal or client_secret) and enable_managed_identity:
                    raise MutuallyExclusiveArgumentError(
                        "Cannot specify --enable-managed-identity and --service-principal/--client-secret at same time"
                    )
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

        # override to use shared identity in managed live test
        if use_shared_identity():
            if self._get_enable_managed_identity(enable_validation=False):
                if (
                    self.decorator_mode == DecoratorMode.CREATE or
                    (self.decorator_mode == DecoratorMode.UPDATE and not assign_identity)
                ):
                    assign_identity = get_shared_control_plane_identity(designated_identity=assign_identity)

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

    def get_user_assigned_identity_client_id(self, user_assigned_identity=None) -> str:
        """Helper function to obtain the client_id of user assigned identity.

        Note: This is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the client_id field in the
        returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = user_assigned_identity if user_assigned_identity else self.get_assign_identity()
        if assigned_identity is None or assigned_identity == "":
            raise RequiredArgumentMissingError("No assigned identity provided.")
        return self.get_identity_by_msi_client(assigned_identity).client_id

    def get_user_assigned_identity_object_id(self, user_assigned_identity=None) -> str:
        """Helper function to obtain the principal_id of user assigned identity.

        Note: This is not a parameter of aks_create, and it will not be decorated into the `mc` object.

        Parse assign_identity and use ManagedServiceIdentityClient to send the request, get the principal_id field in
        the returned identity object. ResourceNotFoundError, ClientRequestError or InvalidArgumentValueError exceptions
        may be raised in the above process.

        :return: string
        """
        assigned_identity = user_assigned_identity if user_assigned_identity else self.get_assign_identity()
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

    def get_assignee_principal_type(self) -> Union[str, None]:
        """Obtain the value of assignee_principal_type.

        This function will return the override value of the assignee principal type (e.g., User, ServicePrincipal, Group)
        to determine the type of identity being assigned for the ACR role. This is used
        during the attach ACR operation to ensure proper role assignment based on the identity type.

        :return: string or None
        """
        # read the original value passed by the command
        assignee_principal_type = self.raw_param.get("assignee_principal_type")
        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return assignee_principal_type

    def get_http_proxy_config(self) -> Union[Dict, ManagedClusterHTTPProxyConfig, None]:
        """Obtain the value of http_proxy_config.

        :return: dictionary, ManagedClusterHTTPProxyConfig or None
        """
        # read the original value passed by the command
        http_proxy_config = None
        http_proxy_config_file_path = self.raw_param.get("http_proxy_config")
        # validate user input
        if http_proxy_config_file_path:
            if not os.path.isfile(http_proxy_config_file_path):
                raise InvalidArgumentValueError(
                    "{} is not valid file, or not accessable.".format(
                        http_proxy_config_file_path
                    )
                )
            http_proxy_config = get_file_json(http_proxy_config_file_path)
            if not isinstance(http_proxy_config, dict):
                raise InvalidArgumentValueError(
                    "Error reading Http Proxy Config from {}. "
                    "Please see https://aka.ms/HttpProxyConfig for correct format.".format(
                        http_proxy_config_file_path
                    )
                )

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "http_proxy_config") and
                self.mc.http_proxy_config is not None
            ):
                http_proxy_config = self.mc.http_proxy_config

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return http_proxy_config

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
        load_balancer_sku = safe_lower(self.raw_param.get("load_balancer_sku"))
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            load_balancer_sku is None and
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.load_balancer_sku is not None
        ):
            load_balancer_sku = safe_lower(
                self.mc.network_profile.load_balancer_sku
            )
        if self.decorator_mode == DecoratorMode.CREATE and load_balancer_sku is None:
            # default value
            load_balancer_sku = CONST_LOAD_BALANCER_SKU_STANDARD

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
        return self.raw_param.get("load_balancer_managed_outbound_ip_count")

    def get_load_balancer_managed_outbound_ipv6_count(self) -> Union[int, None]:
        """Obtain the expected count of IPv6 managed outbound IPs.

        Note: SDK provides default value 0 and performs the following validation {'maximum': 100, 'minimum': 0}.

        :return: int or None
        """
        return self.raw_param.get('load_balancer_managed_outbound_ipv6_count')

    def get_load_balancer_outbound_ips(self) -> Union[str, List[ResourceReference], None]:
        """Obtain the value of load_balancer_outbound_ips.

        Note: SDK performs the following validation {'maximum': 16, 'minimum': 1}.

        :return: string, list of ResourceReference, or None
        """
        # read the original value passed by the command
        return self.raw_param.get("load_balancer_outbound_ips")

    def get_load_balancer_outbound_ip_prefixes(self) -> Union[str, List[ResourceReference], None]:
        """Obtain the value of load_balancer_outbound_ip_prefixes.

        :return: string, list of ResourceReference, or None
        """
        # read the original value passed by the command
        return self.raw_param.get("load_balancer_outbound_ip_prefixes")

    def get_load_balancer_outbound_ports(self) -> Union[int, None]:
        """Obtain the value of load_balancer_outbound_ports.

        Note: SDK performs the following validation {'maximum': 64000, 'minimum': 0}.

        :return: int or None
        """
        # read the original value passed by the command
        return self.raw_param.get(
            "load_balancer_outbound_ports"
        )

    def get_load_balancer_idle_timeout(self) -> Union[int, None]:
        """Obtain the value of load_balancer_idle_timeout.

        Note: SDK performs the following validation {'maximum': 120, 'minimum': 4}.

        :return: int or None
        """
        # read the original value passed by the command
        return self.raw_param.get(
            "load_balancer_idle_timeout"
        )

    def get_load_balancer_backend_pool_type(self) -> Union[str, None]:
        """Obtain the value of load_balancer_backend_pool_type.
        :return: string
        """
        # read the original value passed by the command
        load_balancer_backend_pool_type = self.raw_param.get(
            "load_balancer_backend_pool_type"
        )

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return load_balancer_backend_pool_type

    def get_nrg_lockdown_restriction_level(self) -> Union[str, None]:
        """Obtain the value of nrg_lockdown_restriction_level.
        :return: string or None
        """
        # read the original value passed by the command
        nrg_lockdown_restriction_level = self.raw_param.get("nrg_lockdown_restriction_level")

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "nrg_lockdown_restriction_level") and  # for backward compatibility
                self.mc.node_resource_group_profile and
                self.mc.node_resource_group_profile.restriction_level is not None
            ):
                nrg_lockdown_restriction_level = self.mc.node_resource_group_profile.restriction_level

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nrg_lockdown_restriction_level

    def get_nat_gateway_managed_outbound_ip_count(self) -> Union[int, None]:
        """Obtain the value of nat_gateway_managed_outbound_ip_count.

        Note: SDK provides default value 1 and performs the following validation {'maximum': 16, 'minimum': 1}.

        :return: int or None
        """
        # read the original value passed by the command
        nat_gateway_managed_outbound_ip_count = self.raw_param.get("nat_gateway_managed_outbound_ip_count")
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

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nat_gateway_idle_timeout

    def get_pod_cidrs_and_service_cidrs_and_ip_families(self) -> Tuple[
        Union[List[str], None],
        Union[List[str], None],
        Union[List[str], None],
    ]:
        return self.get_pod_cidrs(), self.get_service_cidrs(), self.get_ip_families()

    def get_pod_cidrs(self) -> Union[List[str], None]:
        """Obtain the CIDR ranges used for pod subnets.

        :return: List[str] or None
        """
        # read the original value passed by the command
        pod_cidrs = self.raw_param.get("pod_cidrs")
        # normalize
        pod_cidrs = extract_comma_separated_string(pod_cidrs, keep_none=True, default_value=[])
        # try to read the property value corresponding to the parameter from the `mc` object
        if self.mc and self.mc.network_profile and self.mc.network_profile.pod_cidrs is not None:
            pod_cidrs = self.mc.network_profile.pod_cidrs

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return pod_cidrs

    def get_service_cidrs(self) -> Union[List[str], None]:
        """Obtain the CIDR ranges for the service subnet.

        :return: List[str] or None
        """
        # read the original value passed by the command
        service_cidrs = self.raw_param.get("service_cidrs")
        # normalize
        service_cidrs = extract_comma_separated_string(service_cidrs, keep_none=True, default_value=[])
        # try to read the property value corresponding to the parameter from the `mc` object
        if self.mc and self.mc.network_profile and self.mc.network_profile.service_cidrs is not None:
            service_cidrs = self.mc.network_profile.service_cidrs

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return service_cidrs

    def get_ip_families(self) -> Union[List[str], None]:
        """Obtain the value of ip_families.

        :return: List[str] or None
        """
        # read the original value passed by the command
        ip_families = self.raw_param.get("ip_families")
        # normalize
        ip_families = extract_comma_separated_string(ip_families, keep_none=True, default_value=[])
        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            not ip_families and
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.ip_families is not None
        ):
            ip_families = self.mc.network_profile.ip_families

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return ip_families

    def get_sku_name(self) -> str:
        # read the original value passed by the command
        skuName = self.raw_param.get("sku")
        if skuName is None:
            if (
                self.mc and
                self.mc.sku and
                getattr(self.mc.sku, 'name', None) is not None
            ):
                skuName = vars(self.mc.sku)['name'].lower()
            else:
                skuName = CONST_MANAGED_CLUSTER_SKU_NAME_BASE
        return skuName

    def _get_outbound_type(
        self,
        enable_validation: bool = False,
        read_only: bool = False,
    ) -> Union[str, None]:
        """Internal function to dynamically obtain the value of outbound_type according to the context.

        Note: All the external parameters involved in the validation are not verified in their own getters.

        When outbound_type is not assigned, dynamic completion will be triggerd. By default, the value is set to
        CONST_OUTBOUND_TYPE_LOAD_BALANCER.

        This function supports the option of enable_validation. When enabled, if the value of outbound_type is
        CONST_OUTBOUND_TYPE_LOAD_BALANCER, CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY, CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY
        CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING or CONST_OUTBOUND_TYPE_NONE, the following checks will be performed. If load_balancer_sku is set
        to basic, an InvalidArgumentValueError will be raised. If vnet_subnet_id is not assigned,
        a RequiredArgumentMissingError will be raised. If any of load_balancer_managed_outbound_ip_count,
        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.

        :return: string or None
        """
        # read the original value passed by the command
        outbound_type = self.raw_param.get("outbound_type")
        # try to read the property value corresponding to the parameter from the `mc` object
        read_from_mc = False
        if outbound_type is None:
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

        isBasicSKULb = safe_lower(self._get_load_balancer_sku(enable_validation=False)) == CONST_LOAD_BALANCER_SKU_BASIC
        # dynamic completion
        if not read_from_mc and not isBasicSKULb and outbound_type is None:
            outbound_type = CONST_OUTBOUND_TYPE_LOAD_BALANCER

        skuName = self.get_sku_name()
        isVnetSubnetIdEmpty = self.get_vnet_subnet_id() in ["", None]
        if skuName is not None and skuName == CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC and isVnetSubnetIdEmpty:
            # outbound_type of Automatic SKU should be ManagedNATGateway if no subnet id provided.
            outbound_type = CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY

        # validation
        # Note: The parameters involved in the validation are not verified in their own getters.
        if enable_validation:
            if not read_from_mc and outbound_type is not None and outbound_type not in [
                CONST_OUTBOUND_TYPE_LOAD_BALANCER,
                CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY,
                CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY,
                CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING,
                CONST_OUTBOUND_TYPE_NONE,
            ]:
                raise InvalidArgumentValueError(
                    "Invalid outbound type, supported values are loadBalancer, managedNATGateway, userAssignedNATGateway, "
                    "userDefinedRouting and none. Please refer to "
                    "https://learn.microsoft.com/en-us/azure/aks/egress-outboundtype#updating-outboundtype-after-cluster-creation "  # pylint:disable=line-too-long
                    "for more details."
                )
            if isBasicSKULb:
                if not read_from_mc and outbound_type is not None:  # outbound type was default to loadbalancer for BLB creation
                    raise InvalidArgumentValueError(
                        "{outbound_type} doesn't support basic load balancer sku".format(outbound_type=outbound_type)
                    )
                return outbound_type  # basic sku lb doesn't support outbound type

            if outbound_type == CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING:
                if self.get_vnet_subnet_id() in ["", None]:
                    raise RequiredArgumentMissingError(
                        "--vnet-subnet-id must be specified for userDefinedRouting and it must "
                        "be pre-configured with a route table with egress rules"
                    )
            if outbound_type == CONST_OUTBOUND_TYPE_USER_ASSIGNED_NAT_GATEWAY:
                if self.get_vnet_subnet_id() in ["", None]:
                    raise RequiredArgumentMissingError(
                        "--vnet-subnet-id must be specified for userAssignedNATGateway and it must "
                        "be pre-configured with a NAT gateway with outbound ips"
                    )
            if outbound_type == CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY:
                if self.get_vnet_subnet_id() not in ["", None]:
                    raise InvalidArgumentValueError(
                        "--vnet-subnet-id cannot be specified for managedNATGateway"
                    )
            if outbound_type != CONST_OUTBOUND_TYPE_LOAD_BALANCER:
                if (
                    self.get_load_balancer_managed_outbound_ip_count() or
                    self.get_load_balancer_managed_outbound_ipv6_count() or
                    self.get_load_balancer_outbound_ips() or
                    self.get_load_balancer_outbound_ip_prefixes()
                ):
                    raise MutuallyExclusiveArgumentError(
                        outbound_type + " type doesn't support customizing "
                        "the standard load balancer ips"
                    )
                if (
                    self.get_load_balancer_idle_timeout() or
                    self.get_load_balancer_outbound_ports()
                ):
                    raise MutuallyExclusiveArgumentError(
                        outbound_type + " type doesn't support customizing "
                        "the standard load balancer config"
                    )
            if outbound_type != CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY:
                if (
                    self.get_nat_gateway_managed_outbound_ip_count() or
                    self.get_nat_gateway_idle_timeout()
                ):
                    raise MutuallyExclusiveArgumentError(
                        outbound_type + " type doesn't support customizing "
                        "the standard nat gateway ips"
                    )
        return outbound_type

    def get_outbound_type(
        self,
    ) -> Union[str, None]:
        """Dynamically obtain the value of outbound_type according to the context.

        Note: All the external parameters involved in the validation are not verified in their own getters.

        When outbound_type is not assigned, dynamic completion will be triggerd. By default, the value is set to
        CONST_OUTBOUND_TYPE_LOAD_BALANCER.

        :return: string or None
        """
        return self._get_outbound_type(
            enable_validation=True
        )

    def _get_network_plugin_mode(self, enable_validation: bool = False) -> Union[str, None]:
        # read the original value passed by the command
        network_plugin_mode = self.raw_param.get("network_plugin_mode")

        # try to read the property value corresponding to the parameter from the `mc` object
        if (
            not network_plugin_mode and
            self.mc and
            self.mc.network_profile and
            self.mc.network_profile.network_plugin_mode is not None
        ):
            network_plugin_mode = self.mc.network_profile.network_plugin_mode

        if enable_validation:
            # todo(tyler-lloyd) do we need any validation?
            pass

        return network_plugin_mode

    def get_network_plugin_mode(self) -> Union[str, None]:
        """Obtain the value of network_plugin_mode.

        :return: string or None
        """
        return self._get_network_plugin_mode(enable_validation=True)

    def _get_network_plugin(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of network_plugin.

        Note: SDK provides default value "kubenet" for network_plugin.

        This function supports the option of enable_validation. When enabled, in case network_plugin is assigned, if
        pod_cidr is assigned and the value of network_plugin is azure, an InvalidArgumentValueError will be
        raised; otherwise, if any of pod_cidr, service_cidr, dns_service_ip, docker_bridge_address or network_policy
        is assigned, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """

        network_plugin = self.raw_param.get("network_plugin")

        # try to read the property value corresponding to the parameter from the `mc` object
        # only when we are not in CREATE mode. In Create, if nothing is given from the raw
        # input, then it should be None as no defaulting should happen in the CLI.
        if (
            not network_plugin and
            self.decorator_mode != DecoratorMode.CREATE and
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
                _,
                _,
                _,
                _,
            ) = self._get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy(
                enable_validation=False
            )
            network_plugin_mode = self._get_network_plugin_mode(enable_validation=False)
            if network_plugin:
                if network_plugin == "azure" and pod_cidr and network_plugin_mode != "overlay":
                    raise InvalidArgumentValueError(
                        "Please specify network plugin mode `overlay` when using --pod-cidr or "
                        "use network plugin `kubenet`. For more information about Azure CNI "
                        "Overlay please see https://aka.ms/aks/azure-cni-overlay"
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

    def get_network_policy(self) -> Union[str, None]:
        """Get the value of network_dataplane.
        :return: str or None
        """
        return self.raw_param.get("network_policy")

    def get_network_dataplane(self) -> Union[str, None]:
        """Get the value of network_dataplane.

        :return: str or None
        """
        return self.raw_param.get("network_dataplane")

    def get_acns_enablement(self) -> Tuple[
        Union[bool, None],
        Union[bool, None],
        Union[bool, None],
    ]:
        """Get the enablement of acns

        :return: Tuple of 3 elements which can be bool or None
        """
        enable_acns = self.raw_param.get("enable_acns")
        disable_acns = self.raw_param.get("disable_acns")
        if enable_acns is None and disable_acns is None:
            return None, None, None
        if enable_acns and disable_acns:
            raise MutuallyExclusiveArgumentError(
                "Cannot specify --enable-acns and "
                "--disable-acns at the same time."
            )
        enable_acns = bool(enable_acns) if enable_acns is not None else False
        disable_acns = bool(disable_acns) if disable_acns is not None else False
        acns = enable_acns or not disable_acns
        acns_observability = self.get_acns_observability()
        acns_security = self.get_acns_security()
        if acns and (acns_observability is False and acns_security is False):
            raise MutuallyExclusiveArgumentError(
                "Cannot disable both observability and security when enabling ACNS. "
                "Please enable at least one of them or disable ACNS with --disable-acns."
            )
        if not acns and (acns_observability is not None or acns_security is not None):
            raise MutuallyExclusiveArgumentError(
                "--disable-acns does not use any additional acns arguments."
            )
        return acns, acns_observability, acns_security

    def get_acns_observability(self) -> Union[bool, None]:
        """Get the enablement of acns observability

        :return: bool or None"""
        disable_acns_observability = self.raw_param.get("disable_acns_observability")
        return not bool(disable_acns_observability) if disable_acns_observability is not None else None

    def get_acns_security(self) -> Union[bool, None]:
        """Get the enablement of acns security

        :return: bool or None"""
        disable_acns_security = self.raw_param.get("disable_acns_security")
        return not bool(disable_acns_security) if disable_acns_security is not None else None

    def get_acns_advanced_networkpolicies(self) -> Union[str, None]:
        """Get the value of acns_advanced_networkpolicies
        :return: str or None
        """
        disable_acns_security = self.raw_param.get("disable_acns_security")
        disable_acns = self.raw_param.get("disable_acns")
        acns_advanced_networkpolicies = self.raw_param.get("acns_advanced_networkpolicies")
        if acns_advanced_networkpolicies is not None:
            if disable_acns_security or disable_acns:
                raise MutuallyExclusiveArgumentError(
                    "--disable-acns-security and --disable-acns cannot be used with  --acns-advanced-networkpolicies."
                )
        return self.raw_param.get("acns_advanced_networkpolicies")

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
        # pod_cidr is allowed to be updated so only read from mc object during creates
        if self.decorator_mode == DecoratorMode.CREATE:
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
            if not network_plugin:
                # ideally, we shouldn't do any validation like this in the CLI
                # but since there is no default network_policy then if it is
                # non-None then it must mean it was provided by the user. If
                # a user provides a network policy then it is reasonable to require
                # a network_plugin to also be provided.
                if (
                    network_policy
                ):
                    raise RequiredArgumentMissingError(
                        "Please explicitly specify the network plugin type"
                    )
        return pod_cidr, service_cidr, dns_service_ip, None, network_policy

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

        sku_name = self.get_sku_name()
        if sku_name == CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC:
            enable_addons.append("monitoring")

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
        if (
            self.mc and
            self.mc.service_principal_profile and
            self.mc.service_principal_profile.client_id is not None
        ):
            return False
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

        sku_name = self.get_sku_name()
        if sku_name == CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC:
            return True
        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_msi_auth_for_monitoring

    def get_enable_syslog(self) -> Union[bool, None]:
        """Obtain the value of enable_syslog.

        Note: The arg type of this parameter supports three states (True, False or None), but the corresponding default
        value in entry function is not None.

        :return: bool or None
        """
        # read the original value passed by the command
        enable_syslog = self.raw_param.get("enable_syslog")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_syslog

    def get_enable_high_log_scale_mode(self) -> Union[bool, None]:
        """Obtain the value of enable_high_log_scale_mode.

        Note: The arg type of this parameter supports three states (True, False or None), but the corresponding default
        value in entry function is not None.

        :return: bool or None
        """
        # read the original value passed by the command
        enable_high_log_scale_mode = self.raw_param.get("enable_high_log_scale_mode")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_high_log_scale_mode

    def get_data_collection_settings(self) -> Union[str, None]:
        """Obtain the value of data_collection_settings.

        :return: string or None
        """
        # read the original value passed by the command
        data_collection_settings_file_path = self.raw_param.get("data_collection_settings")
        # validate user input
        if data_collection_settings_file_path:
            if not os.path.isfile(data_collection_settings_file_path):
                raise InvalidArgumentValueError(
                    "{} is not valid file, or not accessable.".format(
                        data_collection_settings_file_path
                    )
                )
        return data_collection_settings_file_path

    def get_ampls_resource_id(self) -> Union[str, None]:
        """Obtain the value of ampls_resource_id.

        :return: string or None
        """
        # read the original value passed by the command
        ampls_resource_id = self.raw_param.get("ampls_resource_id")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return ampls_resource_id

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
                            "when azure-keyvault-secrets-provider is enabled. "
                            "Please use command 'az aks enable-addons' to enable it."
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
                            "when azure-keyvault-secrets-provider is enabled. "
                            "Please use command 'az aks enable-addons' to enable it."
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
                            "when azure-keyvault-secrets-provider is enabled "
                            "Please use command 'az aks enable-addons' to enable it."
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

        This function supports the option of enable_validation. If the value of enable_aad is False and the value of
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
                if not enable_aad and self._get_enable_azure_rbac(enable_validation=False):
                    raise RequiredArgumentMissingError(
                        "--enable-azure-rbac can only be used together with --enable-aad"
                    )
            elif self.decorator_mode == DecoratorMode.UPDATE:
                if enable_aad:
                    if check_is_managed_aad_cluster(self.mc):
                        raise InvalidArgumentValueError(
                            'Cannot specify "--enable-aad" if managed AAD is already enabled'
                        )
        return enable_aad

    def get_enable_aad(self) -> bool:
        """Obtain the value of enable_aad.

        This function will verify the parameter by default. If the value of enable_aad is False and the value of
        enable_azure_rbac is True, a RequiredArgumentMissingError will be raised. In update mode, if enable_aad is
        specified and managed aad has been enabled, an InvalidArgumentValueError will be raised.

        :return: bool
        """

        return self._get_enable_aad(enable_validation=True)

    def _get_aad_tenant_id(
        self, enable_validation: bool = False, read_only: bool = False
    ) -> Union[str, None]:
        """Internal function to obtain the value of aad_tenant_id according to the context.

        This function supports the option of enable_validation. When enabled in update mode, if aad_tenant_id
        is specified, while aad_profile is not set or managed aad is not enabled, raise an InvalidArgumentValueError.

        This function supports the option of read_only. When enabled, it will skip dynamic completion and validation.
        :return: string or None
        """
        # read the original value passed by the command
        aad_tenant_id = self.raw_param.get("aad_tenant_id")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.aad_profile and
                self.mc.aad_profile.tenant_id is not None
            ):
                aad_tenant_id = self.mc.aad_profile.tenant_id

        # skip validation if option read_only is specified
        if read_only:
            return aad_tenant_id

        # validation
        if enable_validation:
            if aad_tenant_id:
                if self.decorator_mode == DecoratorMode.UPDATE:
                    if not check_is_managed_aad_cluster(self.mc):
                        raise InvalidArgumentValueError(
                            'Cannot specify "--aad-tenant-id" if managed AAD is not enabled'
                        )
        return aad_tenant_id

    def get_aad_tenant_id(self) -> Union[str, None]:
        """Obtain the value of aad_tenant_id according to the context.

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
                    if not check_is_managed_aad_cluster(self.mc):
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
                    if not check_is_managed_aad_cluster(self.mc):
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
                    if not check_is_managed_aad_cluster(self.mc):
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

    def get_oidc_issuer_profile(self) -> ManagedClusterOIDCIssuerProfile:
        """Obtain the value of oidc_issuer_profile based on the user input.

        :return: ManagedClusterOIDCIssuerProfile
        """
        enable_flag_value = bool(self.raw_param.get("enable_oidc_issuer"))
        if not enable_flag_value:
            # enable flag not set, return a None profile, server side will backfill the default/existing value
            return None

        profile = self.models.ManagedClusterOIDCIssuerProfile()
        if self.decorator_mode == DecoratorMode.UPDATE:
            if self.mc.oidc_issuer_profile is not None:
                profile = self.mc.oidc_issuer_profile
        profile.enabled = True

        return profile

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

    def _get_enable_apiserver_vnet_integration(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_apiserver_vnet_integration.

        This function supports the option of enable_validation. When enable_apiserver_vnet_integration is specified,
        For UPDATE: if apiserver-subnet-id is not used, raise an RequiredArgumentMissingError;

        :return: bool
        """
        # read the original value passed by the command
        enable_apiserver_vnet_integration = self.raw_param.get("enable_apiserver_vnet_integration")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.api_server_access_profile and
                "enableVnetIntegration" in self.mc.api_server_access_profile.additional_properties
            ):
                enable_apiserver_vnet_integration = self.mc.api_server_access_profile.additional_properties['enableVnetIntegration']

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.UPDATE:
                is_apiserver_vnet_integration_cluster = check_is_apiserver_vnet_integration_cluster(self.mc)
                if enable_apiserver_vnet_integration and not is_apiserver_vnet_integration_cluster:
                    if self._get_apiserver_subnet_id(enable_validation=False) is None:
                        raise RequiredArgumentMissingError(
                            "--apiserver-subnet-id is required for update with --enable-apiserver-vnet-integration."
                        )

        return enable_apiserver_vnet_integration

    def get_enable_apiserver_vnet_integration(self) -> bool:
        """Obtain the value of enable_apiserver_vnet_integration.

        This function will verify the parameter by default. When enable_apiserver_vnet_integration is specified,
        For UPDATE: if apiserver-subnet-id is not used, raise an RequiredArgumentMissingError

        :return: bool
        """
        return self._get_enable_apiserver_vnet_integration(enable_validation=True)

    def _get_apiserver_subnet_id(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of apiserver_subnet_id.

        This function supports the option of enable_validation. When apiserver_subnet_id is specified,
        if enable_apiserver_vnet_integration is not used, raise an RequiredArgumentMissingError;
        For CREATE: if vnet_subnet_id is not used, raise an RequiredArgumentMissingError;

        :return: bool
        """
        # read the original value passed by the command
        apiserver_subnet_id = self.raw_param.get("apiserver_subnet_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.api_server_access_profile and
                self.mc.api_server_access_profile.subnet_id is not None
            ):
                apiserver_subnet_id = self.mc.api_server_access_profile.subnet_id

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.CREATE:
                vnet_subnet_id = self.get_vnet_subnet_id()
                if apiserver_subnet_id and vnet_subnet_id is None:
                    raise RequiredArgumentMissingError(
                        '"--apiserver-subnet-id" requires "--vnet-subnet-id".')

            enable_apiserver_vnet_integration = self._get_enable_apiserver_vnet_integration(
                enable_validation=False)
            if (
                apiserver_subnet_id and
                (
                    enable_apiserver_vnet_integration is None or
                    enable_apiserver_vnet_integration is False
                ) and
                self.get_sku_name() != CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC
            ):
                raise RequiredArgumentMissingError(
                    '"--apiserver-subnet-id" requires "--enable-apiserver-vnet-integration".')

        return apiserver_subnet_id

    def get_apiserver_subnet_id(self) -> Union[str, None]:
        """Obtain the value of apiserver_subnet_id.

        This function will verify the parameter by default. When apiserver_subnet_id is specified,
        if enable_apiserver_vnet_integration is not specified, raise an RequiredArgumentMissingError;

        :return: bool
        """
        return self._get_apiserver_subnet_id(enable_validation=True)

    def _get_enable_private_cluster(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_private_cluster.

        This function supports the option of enable_validation. When enabled and enable_private_cluster is specified,
        if load_balancer_sku equals to basic, raise an InvalidArgumentValueError; if api_server_authorized_ip_ranges
        is assigned, raise an MutuallyExclusiveArgumentError; Otherwise when enable_private_cluster is not specified
        and disable_public_fqdn, enable_public_fqdn or private_dns_zone is assigned, raise an InvalidArgumentValueError.

        For UPDATE: if existing cluster is not using apiserver vnet integration, raise an ArgumentUsageError;

        :return: bool
        """
        # read the original value passed by the command
        enable_apiserver_vnet_integration = self.raw_param.get("enable_apiserver_vnet_integration")
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
                is_apiserver_vnet_integration_cluster = check_is_apiserver_vnet_integration_cluster(self.mc)

                if is_private_cluster or enable_private_cluster:
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

                # new validation added for vnet integration
                if enable_private_cluster and not enable_apiserver_vnet_integration:
                    if not is_apiserver_vnet_integration_cluster:
                        raise ArgumentUsageError(
                            "EEnabling private cluster requires enabling apiserver vnet integration"
                            "(--enable-apiserver-vnet-integration)."
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

    def _get_disable_private_cluster(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_private_cluster.

        This function supports the option of enable_validation.
        For UPDATE: if existing cluster is not using apiserver vnet integration, raise an ArgumentUsageError;

        :return: bool
        """
        # read the original value passed by the command
        enable_apiserver_vnet_integration = self.raw_param.get("enable_apiserver_vnet_integration")
        disable_private_cluster = self.raw_param.get("disable_private_cluster")

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if self.decorator_mode == DecoratorMode.UPDATE:
                if disable_private_cluster:
                    if self._get_disable_public_fqdn(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "--disable-public-fqdn can only be used for private cluster"
                        )
                    if self._get_enable_public_fqdn(enable_validation=False):
                        raise InvalidArgumentValueError(
                            "--enable-public-fqdn can only be used for private cluster"
                        )
                # new validation added for apiserver vnet integration
                is_apiserver_vnet_integration_cluster = check_is_apiserver_vnet_integration_cluster(self.mc)
                if disable_private_cluster and not enable_apiserver_vnet_integration:
                    if not is_apiserver_vnet_integration_cluster:
                        raise ArgumentUsageError(
                            "DDisabling private cluster requires enabling apiserver vnet integration"
                            "(--enable-apiserver-vnet-integration)."
                        )

        return disable_private_cluster

    def get_disable_private_cluster(self) -> bool:
        """Obtain the value of disable_private_cluster.

        This function will verify the parameter by default. When disable_private_cluster is specified,
        For UPDATE: if enable-apiserver-vnet-integration is not used and existing cluster is not using
        apiserver vnet integration, raise an ArgumentUsageError

        :return: bool
        """
        return self._get_disable_private_cluster(enable_validation=True)

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
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
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

    def get_user_assignd_identity_from_mc(self) -> Union[str, None]:
        """Helper function to obtain the (first) user assignd identity from ManagedCluster.

        :return: string or None
        """
        user_assigned_identity = None
        if self.mc and self.mc.identity and self.mc.identity.user_assigned_identities:
            user_assigned_identity = safe_list_get(list(self.mc.identity.user_assigned_identities.keys()), 0, None)
        return user_assigned_identity

    def _get_assign_kubelet_identity(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of assign_kubelet_identity.

        This function supports the option of enable_validation. When enabled, if assign_identity is not assigned but
        assign_kubelet_identity is, a RequiredArgumentMissingError will be raised.

        :return: string or None
        """
        # read the original value passed by the command
        assign_kubelet_identity = self.raw_param.get("assign_kubelet_identity")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object
        if self.decorator_mode == DecoratorMode.CREATE:
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
            if assign_kubelet_identity:
                if self.decorator_mode == DecoratorMode.CREATE and not self._get_assign_identity(
                    enable_validation=False
                ):
                    raise RequiredArgumentMissingError(
                        "--assign-kubelet-identity can only be specified when --assign-identity is specified"
                    )
                if self.decorator_mode == DecoratorMode.UPDATE:
                    msg = (
                        "You're going to update kubelet identity to {}, "
                        "which will upgrade every node pool in the cluster "
                        "and might take a while, do you wish to continue?".format(assign_kubelet_identity)
                    )
                    if not self.get_yes() and not prompt_y_n(msg, default="n"):
                        raise DecoratorEarlyExitException
                    if not self.get_assign_identity() and not self.get_user_assignd_identity_from_mc():
                        raise RequiredArgumentMissingError(
                            "--assign-identity is not provided and the cluster identity type "
                            "is not user assigned, cannot update kubelet identity"
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

    def get_node_os_upgrade_channel(self) -> Union[str, None]:
        """Obtain the value of node_os_upgrade_channel.
        :return: string or None
        """
        # read the original value passed by the command
        node_os_upgrade_channel = self.raw_param.get("node_os_upgrade_channel")

        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                self.mc.auto_upgrade_profile and
                self.mc.auto_upgrade_profile.node_os_upgrade_channel is not None
            ):
                node_os_upgrade_channel = self.mc.auto_upgrade_profile.node_os_upgrade_channel

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_os_upgrade_channel

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
                new_options_dict = {
                    key.replace("-", "_"): value
                    for key, value in cluster_autoscaler_profile.items()
                }
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

    def _get_k8s_support_plan(self) -> KubernetesSupportPlan:
        support_plan = self.raw_param.get("k8s_support_plan")
        return support_plan

    def get_initial_service_mesh_profile(self) -> ServiceMeshProfile:
        """ Obtain the initial service mesh profile from parameters.
        This function is used only when setting up a new AKS cluster.
        :return: initial service mesh profile
        """

        # returns a service mesh profile only if '--enable-azure-service-mesh' is applied
        enable_asm = self.raw_param.get("enable_azure_service_mesh", False)
        revision = self.raw_param.get("revision", None)
        revisions = None
        if revision is not None:
            revisions = [revision]
        if enable_asm:
            return self.models.ServiceMeshProfile(
                mode=CONST_AZURE_SERVICE_MESH_MODE_ISTIO,
                istio=self.models.IstioServiceMesh(
                    revisions=revisions
                ),  # pylint: disable=no-member
            )

        return None

    def _handle_upgrade_asm(self, new_profile: ServiceMeshProfile) -> Tuple[ServiceMeshProfile, bool]:
        mesh_upgrade_command = self.raw_param.get("mesh_upgrade_command", None)
        supress_confirmation = self.raw_param.get("yes", False)
        updated = False

        # deal with mesh upgrade commands
        if mesh_upgrade_command is not None:
            if new_profile is None or new_profile.mode == CONST_AZURE_SERVICE_MESH_MODE_DISABLED:
                raise ArgumentUsageError(
                    "Istio has not been enabled for this cluster, please refer to https://aka.ms/asm-aks-addon-docs "
                    "for more details on enabling Azure Service Mesh."
                )
            requested_revision = self.raw_param.get("revision", None)
            if mesh_upgrade_command in (
                CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE,
                CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK,
            ):
                if len(new_profile.istio.revisions) < 2:
                    raise ArgumentUsageError('Azure Service Mesh upgrade is not in progress.')

                sorted_revisons = sort_asm_revisions(new_profile.istio.revisions)
                if mesh_upgrade_command == CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE:
                    revision_to_remove = sorted_revisons[0]
                    revision_to_keep = sorted_revisons[-1]
                else:
                    revision_to_remove = sorted_revisons[-1]
                    revision_to_keep = sorted_revisons[0]
                msg = (
                    f"This operation will remove Istio control plane for revision {revision_to_remove}. "
                    f"Please ensure all data plane workloads have been rolled over to revision {revision_to_keep} "
                    "so that they are still part of the mesh.\nAre you sure you want to proceed?"
                )
                if not supress_confirmation and not prompt_y_n(msg, default="n"):
                    raise DecoratorEarlyExitException()
                new_profile.istio.revisions.remove(revision_to_remove)
                updated = True
            elif (
                mesh_upgrade_command == CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START and
                requested_revision is not None
            ):
                if new_profile.istio.revisions is None:
                    new_profile.istio.revisions = []
                new_profile.istio.revisions.append(requested_revision)
                updated = True

        return new_profile, updated

    def _handle_pluginca_asm(self, new_profile: ServiceMeshProfile) -> Tuple[ServiceMeshProfile, bool]:
        updated = False
        enable_asm = self.raw_param.get("enable_azure_service_mesh", False)

        # deal with plugin ca
        key_vault_id = self.raw_param.get("key_vault_id", None)
        ca_cert_object_name = self.raw_param.get("ca_cert_object_name", None)
        ca_key_object_name = self.raw_param.get("ca_key_object_name", None)
        root_cert_object_name = self.raw_param.get("root_cert_object_name", None)
        cert_chain_object_name = self.raw_param.get("cert_chain_object_name", None)

        if any([key_vault_id, ca_cert_object_name, ca_key_object_name, root_cert_object_name, cert_chain_object_name]):
            if key_vault_id is None:
                raise InvalidArgumentValueError(
                    '--key-vault-id is required to use Azure Service Mesh plugin CA feature.'
                )
            if ca_cert_object_name is None:
                raise InvalidArgumentValueError(
                    '--ca-cert-object-name is required to use Azure Service Mesh plugin CA feature.'
                )
            if ca_key_object_name is None:
                raise InvalidArgumentValueError(
                    '--ca-key-object-name is required to use Azure Service Mesh plugin CA feature.'
                )
            if root_cert_object_name is None:
                raise InvalidArgumentValueError(
                    '--root-cert-object-name is required to use Azure Service Mesh plugin CA feature.'
                )
            if cert_chain_object_name is None:
                raise InvalidArgumentValueError(
                    '--cert-chain-object-name is required to use Azure Service Mesh plugin CA feature.'
                )

        if key_vault_id is not None and (
                not is_valid_resource_id(key_vault_id) or "providers/Microsoft.KeyVault/vaults" not in key_vault_id):
            raise InvalidArgumentValueError(
                key_vault_id + " is not a valid Azure Keyvault resource ID."
            )

        if enable_asm and all(
            [
                key_vault_id,
                ca_cert_object_name,
                ca_key_object_name,
                root_cert_object_name,
                cert_chain_object_name,
            ]
        ):
            if new_profile.istio.certificate_authority is None:
                new_profile.istio.certificate_authority = (
                    self.models.IstioCertificateAuthority()  # pylint: disable=no-member
                )
            if new_profile.istio.certificate_authority.plugin is None:
                new_profile.istio.certificate_authority.plugin = (
                    self.models.IstioPluginCertificateAuthority()  # pylint: disable=no-member
                )
            new_profile.mode = CONST_AZURE_SERVICE_MESH_MODE_ISTIO
            new_profile.istio.certificate_authority.plugin.key_vault_id = key_vault_id
            new_profile.istio.certificate_authority.plugin.cert_object_name = ca_cert_object_name
            new_profile.istio.certificate_authority.plugin.key_object_name = ca_key_object_name
            new_profile.istio.certificate_authority.plugin.root_cert_object_name = root_cert_object_name
            new_profile.istio.certificate_authority.plugin.cert_chain_object_name = cert_chain_object_name
            updated = True

        return new_profile, updated

    def _handle_ingress_gateways_asm(self, new_profile: ServiceMeshProfile) -> Tuple[ServiceMeshProfile, bool]:
        updated = False
        enable_ingress_gateway = self.raw_param.get("enable_ingress_gateway", False)
        disable_ingress_gateway = self.raw_param.get("disable_ingress_gateway", False)
        ingress_gateway_type = self.raw_param.get("ingress_gateway_type", None)

        # disallow disable ingress gateway on a cluster with no asm enabled
        if disable_ingress_gateway:
            if new_profile is None or new_profile.mode == CONST_AZURE_SERVICE_MESH_MODE_DISABLED:
                raise ArgumentUsageError(
                    "Istio has not been enabled for this cluster, please refer to https://aka.ms/asm-aks-addon-docs "
                    "for more details on enabling Azure Service Mesh."
                )

        if enable_ingress_gateway and disable_ingress_gateway:
            raise MutuallyExclusiveArgumentError(
                "Cannot both enable and disable azure service mesh ingress gateway at the same time.",
            )

        # deal with ingress gateways
        if enable_ingress_gateway or disable_ingress_gateway:
            # if an ingress gateway is enabled, enable the mesh
            if enable_ingress_gateway:
                new_profile.mode = CONST_AZURE_SERVICE_MESH_MODE_ISTIO
                if new_profile.istio is None:
                    new_profile.istio = self.models.IstioServiceMesh()  # pylint: disable=no-member
                updated = True

            if not ingress_gateway_type:
                raise RequiredArgumentMissingError("--ingress-gateway-type is required.")

            # ensure necessary fields
            if new_profile.istio.components is None:
                new_profile.istio.components = self.models.IstioComponents()  # pylint: disable=no-member
                updated = True
            if new_profile.istio.components.ingress_gateways is None:
                new_profile.istio.components.ingress_gateways = []
                updated = True

            # make update if the ingress gateway already exist
            ingress_gateway_exists = False
            for ingress in new_profile.istio.components.ingress_gateways:
                if ingress.mode == ingress_gateway_type:
                    ingress.enabled = enable_ingress_gateway
                    ingress_gateway_exists = True
                    updated = True
                    break

            # ingress gateway not exist, append
            if not ingress_gateway_exists:
                new_profile.istio.components.ingress_gateways.append(
                    self.models.IstioIngressGateway(  # pylint: disable=no-member
                        mode=ingress_gateway_type,
                        enabled=enable_ingress_gateway,
                    )
                )
                updated = True

        return new_profile, updated

    def _handle_egress_gateways_asm(self, new_profile: ServiceMeshProfile) -> Tuple[ServiceMeshProfile, bool]:
        updated = False
        enable_egress_gateway = self.raw_param.get("enable_egress_gateway", False)
        disable_egress_gateway = self.raw_param.get("disable_egress_gateway", False)
        istio_egressgateway_name = self.raw_param.get("istio_egressgateway_name", None)
        istio_egressgateway_namespace = self.raw_param.get(
            "istio_egressgateway_namespace",
            CONST_AZURE_SERVICE_MESH_DEFAULT_EGRESS_NAMESPACE
        )
        gateway_configuration_name = self.raw_param.get("gateway_configuration_name", None)

        # disallow disable egress gateway on a cluster with no asm enabled
        if disable_egress_gateway:
            if new_profile is None or new_profile.mode == CONST_AZURE_SERVICE_MESH_MODE_DISABLED:
                raise ArgumentUsageError(
                    "Istio has not been enabled for this cluster, please refer to https://aka.ms/asm-aks-addon-docs "
                    "for more details on enabling Azure Service Mesh."
                )
        # deal with egress gateways
        if enable_egress_gateway and disable_egress_gateway:
            raise MutuallyExclusiveArgumentError(
                "Cannot both enable and disable azure service mesh egress gateway at the same time.",
            )
        if enable_egress_gateway or disable_egress_gateway:
            # if a gateway is enabled, enable the mesh
            if enable_egress_gateway:

                new_profile.mode = CONST_AZURE_SERVICE_MESH_MODE_ISTIO
                if new_profile.istio is None:
                    new_profile.istio = self.models.IstioServiceMesh()  # pylint: disable=no-member
                updated = True

                # Gateway configuration name is required for Istio egress gateway enablement
                if not gateway_configuration_name:
                    raise RequiredArgumentMissingError("--gateway-configuration-name is required.")

            if not istio_egressgateway_name:
                raise RequiredArgumentMissingError("--istio-egressgateway-name is required.")

            # ensure necessary fields
            if new_profile.istio.components is None:
                new_profile.istio.components = self.models.IstioComponents()  # pylint: disable=no-member
                updated = True
            if new_profile.istio.components.egress_gateways is None:
                new_profile.istio.components.egress_gateways = []
                updated = True
            # make update if the egress gateway already exists
            egress_gateway_exists = False
            for egress in new_profile.istio.components.egress_gateways:
                if egress.name == istio_egressgateway_name and egress.namespace == istio_egressgateway_namespace:
                    if not egress.enabled and disable_egress_gateway:
                        raise ArgumentUsageError(
                            f'Egress gateway {istio_egressgateway_name} '
                            f'in namespace {istio_egressgateway_namespace} is already disabled.'
                        )
                    if egress.enabled and enable_egress_gateway:
                        if egress.gateway_configuration_name == gateway_configuration_name:
                            raise ArgumentUsageError(
                                f'Egress gateway {istio_egressgateway_name} '
                                f'in namespace {istio_egressgateway_namespace} is already enabled '
                                f'with gateway configuration name {gateway_configuration_name}.'
                            )
                    egress.enabled = enable_egress_gateway
                    # only update gateway configuration name for enabled egress gateways
                    if enable_egress_gateway:
                        egress.gateway_configuration_name = gateway_configuration_name
                    egress_gateway_exists = True
                    updated = True
                    break

            # egress gateway doesn't exist, append
            if not egress_gateway_exists:
                if enable_egress_gateway:
                    new_profile.istio.components.egress_gateways.append(
                        self.models.IstioEgressGateway(  # pylint: disable=no-member
                            enabled=enable_egress_gateway,
                            name=istio_egressgateway_name,
                            namespace=istio_egressgateway_namespace,
                            gateway_configuration_name=gateway_configuration_name,
                        )
                    )
                elif disable_egress_gateway:
                    raise ArgumentUsageError(
                        f'Egress gateway {istio_egressgateway_name} '
                        f'in namespace {istio_egressgateway_namespace} does not exist, cannot disable.'
                    )

                updated = True

        return new_profile, updated

    def _handle_enable_disable_asm(self, new_profile: ServiceMeshProfile) -> Tuple[ServiceMeshProfile, bool]:
        updated = False
        # enable/disable
        enable_asm = self.raw_param.get("enable_azure_service_mesh", False)
        disable_asm = self.raw_param.get("disable_azure_service_mesh", False)
        mesh_upgrade_command = self.raw_param.get("mesh_upgrade_command", None)

        if enable_asm and disable_asm:
            raise MutuallyExclusiveArgumentError(
                "Cannot both enable and disable azure service mesh at the same time.",
            )

        if disable_asm:
            if new_profile is None or new_profile.mode == CONST_AZURE_SERVICE_MESH_MODE_DISABLED:
                raise ArgumentUsageError(
                    "Istio has not been enabled for this cluster, please refer to https://aka.ms/asm-aks-addon-docs "
                    "for more details on enabling Azure Service Mesh."
                )
            new_profile.mode = CONST_AZURE_SERVICE_MESH_MODE_DISABLED
            updated = True
        elif enable_asm:
            if new_profile is not None and new_profile.mode == CONST_AZURE_SERVICE_MESH_MODE_ISTIO:
                raise ArgumentUsageError(
                    "Istio has already been enabled for this cluster, please refer to "
                    "https://aka.ms/asm-aks-upgrade-docs for more details on updating the mesh profile."
                )
            requested_revision = self.raw_param.get("revision", None)
            new_profile.mode = CONST_AZURE_SERVICE_MESH_MODE_ISTIO
            if new_profile.istio is None:
                new_profile.istio = self.models.IstioServiceMesh()  # pylint: disable=no-member
            if mesh_upgrade_command is None and requested_revision is not None:
                new_profile.istio.revisions = [requested_revision]
            updated = True

        return new_profile, updated

    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    def update_azure_service_mesh_profile(self) -> ServiceMeshProfile:
        """ Update azure service mesh profile.

        This function clone the existing service mesh profile, then apply user supplied changes
        like enable or disable mesh, enable or disable internal or external ingress gateway
        then return the updated service mesh profile.

        It does not overwrite the service mesh profile attribute of the managed cluster.

        :return: updated service mesh profile
        """
        updated = False
        new_profile = (
            self.models.ServiceMeshProfile(mode=CONST_AZURE_SERVICE_MESH_MODE_DISABLED)  # pylint: disable=no-member
            if self.mc.service_mesh_profile is None
            else copy.deepcopy(self.mc.service_mesh_profile)
        )

        new_profile, updated_enable_disable_asm = self._handle_enable_disable_asm(new_profile)
        updated |= updated_enable_disable_asm

        new_profile, updated_ingress_gateways_asm = self._handle_ingress_gateways_asm(new_profile)
        updated |= updated_ingress_gateways_asm

        new_profile, updated_egress_gateways_asm = self._handle_egress_gateways_asm(new_profile)
        updated |= updated_egress_gateways_asm

        new_profile, updated_pluginca_asm = self._handle_pluginca_asm(new_profile)
        updated |= updated_pluginca_asm

        new_profile, updated_upgrade_asm = self._handle_upgrade_asm(new_profile)
        updated |= updated_upgrade_asm

        if updated:
            return new_profile
        return self.mc.service_mesh_profile

    def get_tier(self) -> str:
        """Obtain the value of tier.

        :return: str
        """
        tier = self.raw_param.get("tier")
        if not tier:
            return ""

        return tier.lower()

    def get_defender_config(self) -> Union[ManagedClusterSecurityProfileDefender, None]:
        """Obtain the value of defender.

        :return: ManagedClusterSecurityProfileDefender or None
        """
        disable_defender = self.raw_param.get("disable_defender")
        if disable_defender:
            return self.models.ManagedClusterSecurityProfileDefender(
                security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                    enabled=False
                )
            )

        enable_defender = self.raw_param.get("enable_defender")
        if not enable_defender:
            return None

        workspace = ""
        config_file_path = self.raw_param.get("defender_config")
        if config_file_path:
            if not os.path.isfile(config_file_path):
                raise InvalidArgumentValueError(
                    "{} is not valid file, or not accessable.".format(
                        config_file_path
                    )
                )
            defender_config = get_file_json(config_file_path)
            if "logAnalyticsWorkspaceResourceId" in defender_config:
                workspace = defender_config["logAnalyticsWorkspaceResourceId"]

        if workspace == "":
            workspace = self.external_functions.ensure_default_log_analytics_workspace_for_monitoring(
                self.cmd,
                self.get_subscription_id(),
                self.get_resource_group_name())

        azure_defender = self.models.ManagedClusterSecurityProfileDefender(
            log_analytics_workspace_resource_id=workspace,
            security_monitoring=self.models.ManagedClusterSecurityProfileDefenderSecurityMonitoring(
                enabled=enable_defender
            ),
        )
        return azure_defender

    def get_workload_identity_profile(self) -> Optional[ManagedClusterSecurityProfileWorkloadIdentity]:
        """Obtrain the value of security_profile.workload_identity.
        :return: Optional[ManagedClusterSecurityProfileWorkloadIdentity]
        """
        enable_workload_identity = self.raw_param.get("enable_workload_identity")
        disable_workload_identity = self.raw_param.get("disable_workload_identity")

        if not enable_workload_identity and not disable_workload_identity:
            return None

        if enable_workload_identity and disable_workload_identity:
            raise MutuallyExclusiveArgumentError(
                "Cannot specify --enable-workload-identity and "
                "--disable-workload-identity at the same time."
            )

        if not hasattr(self.models, "ManagedClusterSecurityProfileWorkloadIdentity"):
            return None

        profile = self.models.ManagedClusterSecurityProfileWorkloadIdentity()

        if self.decorator_mode == DecoratorMode.CREATE:
            profile.enabled = bool(enable_workload_identity)
        elif self.decorator_mode == DecoratorMode.UPDATE:
            if (
                hasattr(self.mc, "security_profile") and
                self.mc.security_profile is not None and
                self.mc.security_profile.workload_identity is not None
            ):
                # reuse previous profile is has been set
                profile = self.mc.security_profile.workload_identity

            if enable_workload_identity:
                profile.enabled = True
            elif disable_workload_identity:
                profile.enabled = False

        if profile.enabled:
            # in enable case, we need to check if OIDC issuer has been enabled
            oidc_issuer_profile = self.get_oidc_issuer_profile()
            if self.decorator_mode == DecoratorMode.UPDATE and oidc_issuer_profile is None:
                # if the cluster has enabled OIDC issuer before, in update call:
                #
                #    az aks update --enable-workload-identity
                #
                # we need to use previous OIDC issuer profile
                oidc_issuer_profile = self.mc.oidc_issuer_profile
            oidc_issuer_enabled = oidc_issuer_profile is not None and oidc_issuer_profile.enabled
            if not oidc_issuer_enabled:
                raise RequiredArgumentMissingError(
                    "Enabling workload identity requires enabling OIDC issuer (--enable-oidc-issuer)."
                )

        return profile

    def _get_enable_azure_keyvault_kms(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_azure_keyvault_kms.

        This function supports the option of enable_validation. When enabled, if azure_keyvault_kms_key_id is empty,
        raise a RequiredArgumentMissingError.

        :return: bool
        """
        # read the original value passed by the command
        enable_azure_keyvault_kms = self.raw_param.get("enable_azure_keyvault_kms")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "security_profile") and  # backward compatibility
                self.mc.security_profile and
                self.mc.security_profile.azure_key_vault_kms
            ):
                enable_azure_keyvault_kms = self.mc.security_profile.azure_key_vault_kms.enabled

        # this parameter does not need dynamic completion
        # validation
        if enable_validation:
            if bool(enable_azure_keyvault_kms) != bool(self._get_azure_keyvault_kms_key_id(enable_validation=False)):
                raise RequiredArgumentMissingError(
                    'You must set "--enable-azure-keyvault-kms" and "--azure-keyvault-kms-key-id" at the same time.'
                )

        return enable_azure_keyvault_kms

    def get_enable_azure_keyvault_kms(self) -> bool:
        """Obtain the value of enable_azure_keyvault_kms.

        This function will verify the parameter by default. When enabled, if azure_keyvault_kms_key_id is empty,
        raise a RequiredArgumentMissingError.

        :return: bool
        """
        return self._get_enable_azure_keyvault_kms(enable_validation=True)

    def _get_disable_azure_keyvault_kms(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_azure_keyvault_kms.

        This function supports the option of enable_validation. When enabled,
        if both enable_azure_keyvault_kms and disable_azure_keyvault_kms are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # Read the original value passed by the command.
        disable_azure_keyvault_kms = self.raw_param.get("disable_azure_keyvault_kms")

        # This option is not supported in create mode, hence we do not read the property value from the `mc` object.
        # This parameter does not need dynamic completion.
        if enable_validation:
            if disable_azure_keyvault_kms and self._get_enable_azure_keyvault_kms(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-azure-keyvault-kms and --disable-azure-keyvault-kms at the same time."
                )

        return disable_azure_keyvault_kms

    def get_disable_azure_keyvault_kms(self) -> bool:
        """Obtain the value of disable_azure_keyvault_kms.

        This function will verify the parameter by default. If both enable_azure_keyvault_kms and
        disable_azure_keyvault_kms are specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        return self._get_disable_azure_keyvault_kms(enable_validation=True)

    def _get_azure_keyvault_kms_key_id(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of azure_keyvault_kms_key_id according to the context.

        This function supports the option of enable_validation. When enabled, it will check if
        azure_keyvault_kms_key_id is assigned but enable_azure_keyvault_kms is not specified,
        if so, raise a RequiredArgumentMissingError.

        :return: string or None
        """
        # read the original value passed by the command
        azure_keyvault_kms_key_id = self.raw_param.get("azure_keyvault_kms_key_id")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "security_profile") and  # backward compatibility
                self.mc.security_profile and
                self.mc.security_profile.azure_key_vault_kms and
                self.mc.security_profile.azure_key_vault_kms.key_id is not None
            ):
                azure_keyvault_kms_key_id = self.mc.security_profile.azure_key_vault_kms.key_id

        if enable_validation:
            enable_azure_keyvault_kms = self._get_enable_azure_keyvault_kms(
                enable_validation=False)
            if (
                azure_keyvault_kms_key_id and
                (
                    enable_azure_keyvault_kms is None or
                    enable_azure_keyvault_kms is False
                )
            ):
                raise RequiredArgumentMissingError(
                    '"--azure-keyvault-kms-key-id" requires "--enable-azure-keyvault-kms".')

        return azure_keyvault_kms_key_id

    def get_azure_keyvault_kms_key_id(self) -> Union[str, None]:
        """Obtain the value of azure_keyvault_kms_key_id.

        This function will verify the parameter by default. When enabled, if enable_azure_keyvault_kms is False,
        raise a RequiredArgumentMissingError.

        :return: bool
        """
        return self._get_azure_keyvault_kms_key_id(enable_validation=True)

    def _get_azure_keyvault_kms_key_vault_network_access(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of azure_keyvault_kms_key_vault_network_access according to the
        context.

        This function supports the option of enable_validation. When enabled, it will check if
        azure_keyvault_kms_key_vault_network_access is assigned but enable_azure_keyvault_kms is not specified, if so,
        raise a RequiredArgumentMissingError.

        :return: string or None
        """
        # read the original value passed by the command
        azure_keyvault_kms_key_vault_network_access = self.raw_param.get(
            "azure_keyvault_kms_key_vault_network_access"
        )

        # validation
        if enable_validation:
            enable_azure_keyvault_kms = self._get_enable_azure_keyvault_kms(
                enable_validation=False)
            if azure_keyvault_kms_key_vault_network_access is None:
                raise RequiredArgumentMissingError(
                    '"--azure-keyvault-kms-key-vault-network-access" is required.')

            if (
                azure_keyvault_kms_key_vault_network_access and
                (
                    enable_azure_keyvault_kms is None or
                    enable_azure_keyvault_kms is False
                )
            ):
                raise RequiredArgumentMissingError(
                    '"--azure-keyvault-kms-key-vault-network-access" requires "--enable-azure-keyvault-kms".')

            if azure_keyvault_kms_key_vault_network_access == CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE:
                key_vault_resource_id = self._get_azure_keyvault_kms_key_vault_resource_id(
                    enable_validation=False)
                if (
                    key_vault_resource_id is None or
                    key_vault_resource_id == ""
                ):
                    raise RequiredArgumentMissingError(
                        '"--azure-keyvault-kms-key-vault-resource-id" is required '
                        'when "--azure-keyvault-kms-key-vault-network-access" is Private.'
                    )

        return azure_keyvault_kms_key_vault_network_access

    def get_azure_keyvault_kms_key_vault_network_access(self) -> Union[str, None]:
        """Obtain the value of azure_keyvault_kms_key_vault_network_access.

        This function will verify the parameter by default. When enabled, if enable_azure_keyvault_kms is False,
        raise a RequiredArgumentMissingError.

        :return: bool
        """
        return self._get_azure_keyvault_kms_key_vault_network_access(enable_validation=True)

    def _get_azure_keyvault_kms_key_vault_resource_id(self, enable_validation: bool = False) -> Union[str, None]:
        """Internal function to obtain the value of azure_keyvault_kms_key_vault_resource_id according to the context.

        This function supports the option of enable_validation. When enabled, it will do validation, and raise a
        RequiredArgumentMissingError.

        :return: string or None
        """
        # read the original value passed by the command
        azure_keyvault_kms_key_vault_resource_id = self.raw_param.get(
            "azure_keyvault_kms_key_vault_resource_id"
        )
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "security_profile") and  # backward compatibility
                self.mc.security_profile and
                self.mc.security_profile.azure_key_vault_kms and
                self.mc.security_profile.azure_key_vault_kms.key_vault_resource_id is not None
            ):
                azure_keyvault_kms_key_vault_resource_id = (
                    self.mc.security_profile.azure_key_vault_kms.key_vault_resource_id
                )

        # validation
        if enable_validation:
            enable_azure_keyvault_kms = self._get_enable_azure_keyvault_kms(
                enable_validation=False)
            if (
                azure_keyvault_kms_key_vault_resource_id and
                (
                    enable_azure_keyvault_kms is None or
                    enable_azure_keyvault_kms is False
                )
            ):
                raise RequiredArgumentMissingError(
                    '"--azure-keyvault-kms-key-vault-resource-id" requires "--enable-azure-keyvault-kms".'
                )

            key_vault_network_access = self._get_azure_keyvault_kms_key_vault_network_access(
                enable_validation=False)
            if (
                key_vault_network_access == CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE and
                (
                    azure_keyvault_kms_key_vault_resource_id is None or
                    azure_keyvault_kms_key_vault_resource_id == ""
                )
            ):
                raise ArgumentUsageError(
                    '"--azure-keyvault-kms-key-vault-resource-id" can not be empty if '
                    '"--azure-keyvault-kms-key-vault-network-access" is "Private".'
                )
            if (
                key_vault_network_access == CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PUBLIC and
                (
                    azure_keyvault_kms_key_vault_resource_id is not None and
                    azure_keyvault_kms_key_vault_resource_id != ""
                )
            ):
                raise ArgumentUsageError(
                    '"--azure-keyvault-kms-key-vault-resource-id" must be empty if '
                    '"--azure-keyvault-kms-key-vault-network-access" is "Public".'
                )

        return azure_keyvault_kms_key_vault_resource_id

    def get_azure_keyvault_kms_key_vault_resource_id(self) -> Union[str, None]:
        """Obtain the value of azure_keyvault_kms_key_vault_resource_id.

        This function will verify the parameter by default. When enabled, if enable_azure_keyvault_kms is False,
        raise a RequiredArgumentMissingError.

        :return: bool
        """
        return self._get_azure_keyvault_kms_key_vault_resource_id(enable_validation=True)

    def get_enable_image_cleaner(self) -> bool:
        """Obtain the value of enable_image_cleaner.
        :return: bool
        """
        # read the original value passed by the command
        enable_image_cleaner = self.raw_param.get("enable_image_cleaner")

        return enable_image_cleaner

    def get_disable_image_cleaner(self) -> bool:
        """Obtain the value of disable_image_cleaner.
        This function supports the option of enable_validation. When enabled, if both enable_image_cleaner and
        disable_image_cleaner are specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        # read the original value passed by the command
        disable_image_cleaner = self.raw_param.get("disable_image_cleaner")

        return disable_image_cleaner

    def _get_image_cleaner_interval_hours(self, enable_validation: bool = False) -> Union[int, None]:
        """Internal function to obtain the value of image_cleaner_interval_hours according to the context.
        This function supports the option of enable_validation. When enabled
          1. In Create mode
            a. if image_cleaner_interval_hours is specified but enable_image_cleaner is missed,
                 raise a RequiredArgumentMissingError.
          2. In update mode
            b. if image_cleaner_interval_hours is specified and image cleaner was not enabled,
                 raise a RequiredArgumentMissingError.
            c. if image_cleaner_interval_hours is specified and disable_image_cleaner is specified,
                  raise a MutuallyExclusiveArgumentError.
        :return: int or None
        """
        # read the original value passed by the command
        image_cleaner_interval_hours = self.raw_param.get("image_cleaner_interval_hours")

        if image_cleaner_interval_hours is not None and enable_validation:

            enable_image_cleaner = self.get_enable_image_cleaner()
            disable_image_cleaner = self.get_disable_image_cleaner()

            if self.decorator_mode == DecoratorMode.CREATE:
                if not enable_image_cleaner:
                    raise RequiredArgumentMissingError(
                        '"--image-cleaner-interval-hours" requires "--enable-image-cleaner" in create mode.')

            elif self.decorator_mode == DecoratorMode.UPDATE:
                if not enable_image_cleaner and (
                    not self.mc or
                    not self.mc.security_profile or
                    not self.mc.security_profile.image_cleaner or
                    not self.mc.security_profile.image_cleaner.enabled
                ):
                    raise RequiredArgumentMissingError(
                        'Update "--image-cleaner-interval-hours" requires specifying "--enable-image-cleaner" \
                            or ImageCleaner enabled on managed cluster.')

                if disable_image_cleaner:
                    raise MutuallyExclusiveArgumentError(
                        'Cannot specify --image-cleaner-interval-hours and --disable-image-cleaner at the same time.')

        return image_cleaner_interval_hours

    def get_image_cleaner_interval_hours(self) -> Union[int, None]:
        """Obtain the value of image_cleaner_interval_hours.
        This function supports the option of enable_validation. When enabled
          1. In Create mode
            a. if image_cleaner_interval_hours is specified but enable_image_cleaner is missed,
                 raise a RequiredArgumentMissingError.
          2. In update mode
            b. if image_cleaner_interval_hours is specified and image cleaner was not enabled,
                 raise a RequiredArgumentMissingError.
            c. if image_cleaner_interval_hours is specified and disable_image_cleaner is specified,
                raise a MutuallyExclusiveArgumentError.
        :return: int or None
        """
        interval_hours = self._get_image_cleaner_interval_hours(enable_validation=True)

        return interval_hours

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
            sku_name = self.get_sku_name()
            if sku_name == CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC:
                disable_local_accounts = True

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

    def get_k8s_support_plan(self) -> Union[str, None]:
        """Obtain the value of kubernetes_support_plan.

        :return: string or None
        """
        # take input
        support_plan = self.raw_param.get("k8s_support_plan")
        if support_plan is None:
            # user didn't update this property, load from existing ManagedCluster
            if self.mc and hasattr(self.mc, "support_plan") and self.mc.support_plan is not None:
                support_plan = self.mc.support_plan

        return support_plan

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

    def _get_enable_azure_monitor_metrics(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_azure_monitor_metrics.
        This function supports the option of enable_validation.
        When enabled, if both enable_azure_monitor_metrics and disable_azure_monitor_metrics are
        specified, raise a MutuallyExclusiveArgumentError.

        :return: bool
        """
        # print("_get_enable_azure_monitor_metrics being called...")
        # Read the original value passed by the command.
        enable_azure_monitor_metrics = self.raw_param.get("enable_azure_monitor_metrics")
        # In create mode, try to read the property value corresponding to the parameter from the `mc` object.
        if self.decorator_mode == DecoratorMode.CREATE:
            if (
                self.mc and
                hasattr(self.mc, "azure_monitor_profile") and
                self.mc.azure_monitor_profile and
                self.mc.azure_monitor_profile.metrics
            ):
                enable_azure_monitor_metrics = self.mc.azure_monitor_profile.metrics.enabled
            skuName = self.get_sku_name()
            if skuName == CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC:
                enable_azure_monitor_metrics = True
        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_azure_monitor_metrics and self._get_disable_azure_monitor_metrics(False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-azure-monitor-metrics and --disable-azure-monitor-metrics at the same time"
                )
            if enable_azure_monitor_metrics and not check_is_msi_cluster(self.mc):
                raise RequiredArgumentMissingError(
                    "--enable-azure-monitor-metrics can only be specified for clusters with managed identity enabled"
                )
        return enable_azure_monitor_metrics

    def get_enable_azure_monitor_metrics(self) -> bool:
        """Obtain the value of enable_azure_monitor_metrics.
        This function will verify the parameter by default.
        If both enable_azure_monitor_metrics and disable_azure_monitor_metrics are specified,
        raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_enable_azure_monitor_metrics(enable_validation=True)

    def _get_disable_azure_monitor_metrics(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_azure_monito4790r_metrics.
        This function supports the option of enable_validation.
        When enabled, if both enable_azure_monitor_metrics and disable_azure_monitor_metrics are
        specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        # Read the original value passed by the command.
        disable_azure_monitor_metrics = self.raw_param.get("disable_azure_monitor_metrics")
        if enable_validation:
            if disable_azure_monitor_metrics and self._get_enable_azure_monitor_metrics(False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-azure-monitor-metrics and --disable-azure-monitor-metrics at the same time"
                )
        return disable_azure_monitor_metrics

    def get_disable_azure_monitor_metrics(self) -> bool:
        """Obtain the value of disable_azure_monitor_metrics.
        This function will verify the parameter by default.
        If both enable_azure_monitor_metrics and disable_azure_monitor_metrics are specified,
        raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_disable_azure_monitor_metrics(enable_validation=True)

    def _get_enable_vpa(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_vpa.
        This function supports the option of enable_vpa. When enabled, if both enable_vpa and enable_vpa are
        specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        # Read the original value passed by the command.
        enable_vpa = self.raw_param.get("enable_vpa")

        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_vpa and self._get_disable_vpa(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-vpa and --disable-vpa at the same time."
                )

        return enable_vpa

    def get_enable_vpa(self) -> bool:
        """Obtain the value of enable_vpa.
        This function will verify the parameter by default. If both enable_vpa and disable_vpa are specified, raise
        a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_enable_vpa(enable_validation=True)

    def _get_disable_vpa(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of disable_vpa.
        This function supports the option of enable_vpa. When enabled, if both enable_vpa and disable_vpa are specified,
        raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        # Read the original value passed by the command.
        disable_vpa = self.raw_param.get("disable_vpa")

        # This option is not supported in create mode, hence we do not read the property value from the `mc` object.
        # This parameter does not need dynamic completion.
        if enable_validation:
            if disable_vpa and self._get_enable_vpa(enable_validation=False):
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-vpa and --disable-vpa at the same time."
                )

        return disable_vpa

    def get_disable_vpa(self) -> bool:
        """Obtain the value of disable_vpa.
        This function will verify the parameter by default. If both enable_vpa and disable_vpa are specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        return self._get_disable_vpa(enable_validation=True)

    def get_force_upgrade(self) -> Union[bool, None]:
        """Obtain the value of force_upgrade.
        :return: bool or None
        """
        # this parameter does not need dynamic completion
        # validation is done with param validator
        enable_force_upgrade = self.raw_param.get("enable_force_upgrade")
        disable_force_upgrade = self.raw_param.get("disable_force_upgrade")

        if enable_force_upgrade is False and disable_force_upgrade is False:
            return None
        if enable_force_upgrade is not None:
            return enable_force_upgrade
        if disable_force_upgrade is not None:
            return not disable_force_upgrade
        return None

    def get_upgrade_override_until(self) -> Union[str, None]:
        """Obtain the value of upgrade_override_until.
        :return: string or None
        """
        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return self.raw_param.get("upgrade_override_until")

    def get_ai_toolchain_operator(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_ai_toolchain_operator.
        When enabled, if both enable_ai_toolchain_operator and
        disable_ai_toolchain_operator are specified, raise
        a MutuallyExclusiveArgumentError.
        :return: bool
        """
        enable_ai_toolchain_operator = self.raw_param.get("enable_ai_toolchain_operator")
        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_ai_toolchain_operator and self.get_disable_ai_toolchain_operator():
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-ai-toolchain-operator and "
                    "--disable-ai-toolchain-operator at the same time. "
                )

        return enable_ai_toolchain_operator

    def get_disable_ai_toolchain_operator(self) -> bool:
        """Obtain the value of disable_ai_toolchain_operator.
        :return: bool
        """
        # Note: No need to check for mutually exclusive parameter with enable-ai-toolchain-operator here
        # because it's already checked in get_ai_toolchain_operator
        return self.raw_param.get("disable_ai_toolchain_operator")

    def _get_enable_cost_analysis(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_cost_analysis.
        When enabled, if both enable_cost_analysis and disable_cost_analysis are
        specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        enable_cost_analysis = self.raw_param.get("enable_cost_analysis")

        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_cost_analysis and self.get_disable_cost_analysis():
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-cost-analysis and --disable-cost-analysis at the same time."
                )

        return enable_cost_analysis

    def get_enable_cost_analysis(self) -> bool:
        """Obtain the value of enable_cost_analysis.
        :return: bool
        """
        return self._get_enable_cost_analysis(enable_validation=True)

    def get_disable_cost_analysis(self) -> bool:
        """Obtain the value of disable_cost_analysis.
        :return: bool
        """
        # Note: No need to check for mutually exclusive parameter with enable-cost-analysis here
        # because it's already checked in _get_enable_cost_analysis
        return self.raw_param.get("disable_cost_analysis")

    def get_if_match(self) -> Union[str, None]:
        """Obtain the value of if_match.
        :return: string or None
        """
        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return self.raw_param.get("if_match")

    def get_if_none_match(self) -> Union[str, None]:
        """Obtain the value of if_none_match.
        :return: string or None
        """
        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return self.raw_param.get("if_none_match")

    def get_bootstrap_artifact_source(self) -> Union[str, None]:
        """Obtain the value of bootstrap_artifact_source.
        """
        return self.raw_param.get("bootstrap_artifact_source")

    def get_bootstrap_container_registry_resource_id(self) -> Union[str, None]:
        """Obtain the value of bootstrap_container_registry_resource_id.
        """
        return self.raw_param.get("bootstrap_container_registry_resource_id")

    def _get_enable_static_egress_gateway(self, enable_validation: bool = False) -> bool:
        """Internal function to obtain the value of enable_static_egress_gateway.
        When enabled, if both enable_static_egress_gateway and disable_static_egress_gateway are
        specified, raise a MutuallyExclusiveArgumentError.
        :return: bool
        """
        enable_static_egress_gateway = self.raw_param.get("enable_static_egress_gateway")
        # This parameter does not need dynamic completion.
        if enable_validation:
            if enable_static_egress_gateway and self.get_disable_static_egress_gateway():
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --enable-static-egress-gateway and "
                    "--disable-static-egress-gateway at the same time. "
                )

        return enable_static_egress_gateway

    def get_enable_static_egress_gateway(self) -> bool:
        """Obtain the value of enable_static_egress_gateway.
        :return: bool
        """
        return self._get_enable_static_egress_gateway(enable_validation=True)

    def get_disable_static_egress_gateway(self) -> bool:
        """Obtain the value of disable_static_egress_gateway.
        :return: bool
        """
        # Note: No need to check for mutually exclusive parameter with enable-static-egress-gateway here
        # because it's already checked in get_enable_static_egress_gateway
        return self.raw_param.get("disable_static_egress_gateway")

    def get_migrate_vmas_to_vms(self) -> bool:
        """Obtain the value of migrate_vmas_to_vms.
        :return: bool
        """
        return self.raw_param.get("migrate_vmas_to_vms")

    def get_node_provisioning_mode(self) -> Union[str, None]:
        """Obtain the value of node_provisioning_mode.

        :return: string or None
        """
        return self.raw_param.get("node_provisioning_mode")

    def get_node_provisioning_default_pools(self) -> Union[str, None]:
        """Obtain the value of node_provisioning_default_pools.

        :return: string or None
        """
        return self.raw_param.get("node_provisioning_default_pools")


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

    def set_up_workload_identity_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up workload identity for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        profile = self.context.get_workload_identity_profile()
        if profile:
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()
            mc.security_profile.workload_identity = profile

        return mc

    def set_up_defender(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up defender for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        defender = self.context.get_defender_config()
        if defender:
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()

            mc.security_profile.defender = defender

        return mc

    def set_up_azure_keyvault_kms(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up security profile azureKeyVaultKms for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_enable_azure_keyvault_kms():
            key_id = self.context.get_azure_keyvault_kms_key_id()
            if key_id:
                if mc.security_profile is None:
                    mc.security_profile = self.models.ManagedClusterSecurityProfile()
                mc.security_profile.azure_key_vault_kms = self.models.AzureKeyVaultKms(
                    enabled=True,
                    key_id=key_id,
                )
                key_vault_network_access = self.context.get_azure_keyvault_kms_key_vault_network_access()
                mc.security_profile.azure_key_vault_kms.key_vault_network_access = key_vault_network_access
                if key_vault_network_access == CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE:
                    mc.security_profile.azure_key_vault_kms.key_vault_resource_id = (
                        self.context.get_azure_keyvault_kms_key_vault_resource_id()
                    )

        return mc

    def set_up_image_cleaner(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up security profile imageCleaner for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        interval_hours = self.context.get_image_cleaner_interval_hours()

        if self.context.get_enable_image_cleaner():

            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()

            if not interval_hours:
                # default value for intervalHours - one week
                interval_hours = 24 * 7

            mc.security_profile.image_cleaner = self.models.ManagedClusterSecurityProfileImageCleaner(
                enabled=True,
                interval_hours=interval_hours,
            )

        return mc

    def set_up_node_provisioning_mode(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        mode = self.context.get_node_provisioning_mode()
        if mode is not None:
            if mc.node_provisioning_profile is None:
                mc.node_provisioning_profile = (
                    self.models.ManagedClusterNodeProvisioningProfile()  # pylint: disable=no-member
                )

            # set mode
            mc.node_provisioning_profile.mode = mode

        return mc

    def set_up_node_provisioning_default_pools(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        default_pools = self.context.get_node_provisioning_default_pools()
        if default_pools is not None:
            if mc.node_provisioning_profile is None:
                mc.node_provisioning_profile = (
                    self.models.ManagedClusterNodeProvisioningProfile()  # pylint: disable=no-member
                )

            # set default_node_pools
            mc.node_provisioning_profile.default_node_pools = default_pools

        return mc

    def set_up_node_provisioning_profile(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        mc = self.set_up_node_provisioning_mode(mc)
        mc = self.set_up_node_provisioning_default_pools(mc)

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

    def set_up_storage_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up storage profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if hasattr(self.models, "ManagedClusterStorageProfile"):
            mc.storage_profile = self.context.get_storage_profile()

        return mc

    def set_up_service_principal_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up service principal profile for the ManagedCluster object.

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
                need_post_creation_vnet_permission_granting = True
            else:
                scope = vnet_subnet_id
                if assign_identity:
                    identity_object_id = self.context.get_user_assigned_identity_object_id()
                    if not self.context.external_functions.add_role_assignment(
                        self.cmd,
                        "Network Contributor",
                        identity_object_id,
                        is_service_principal=False,
                        scope=scope,
                    ):
                        logger.warning(
                            "Could not create a role assignment for subnet. Are you an Owner on this subscription?"
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
            self.context.get_load_balancer_managed_outbound_ipv6_count(),
            self.context.get_load_balancer_outbound_ips(),
            self.context.get_load_balancer_outbound_ip_prefixes(),
            self.context.get_load_balancer_outbound_ports(),
            self.context.get_load_balancer_idle_timeout(),
            self.context.get_load_balancer_backend_pool_type(),
            models=self.models.load_balancer_models,
        )

        # verify outbound type
        # Note: Validation internally depends on load_balancer_sku, which is a temporary value that is
        # dynamically completed.
        outbound_type = self.context.get_outbound_type()

        # verify load balancer sku
        load_balancer_sku = safe_lower(self.context.get_load_balancer_sku())

        # verify network_plugin, pod_cidr, service_cidr, dns_service_ip, docker_bridge_address, network_policy
        network_plugin = self.context.get_network_plugin()
        network_plugin_mode = self.context.get_network_plugin_mode()
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
        # set up pod_cidrs, service_cidrs and ip_families
        (
            pod_cidrs,
            service_cidrs,
            ip_families
        ) = (
            self.context.get_pod_cidrs_and_service_cidrs_and_ip_families()
        )

        network_dataplane = self.context.get_network_dataplane()

        (acns_enabled, acns_observability, acns_security) = self.context.get_acns_enablement()
        acns_advanced_networkpolicies = self.context.get_acns_advanced_networkpolicies()
        if acns_enabled is not None:
            acns = self.models.AdvancedNetworking(
                enabled=acns_enabled,
            )
            if acns_observability is not None:
                acns.observability = self.models.AdvancedNetworkingObservability(
                    enabled=acns_observability,
                )
            if acns_security is not None:
                acns.security = self.models.AdvancedNetworkingSecurity(
                    enabled=acns_security,
                )
            if acns_advanced_networkpolicies is not None:
                if acns.security is None:
                    acns.security = self.models.AdvancedNetworkingSecurity(
                        advanced_network_policies=acns_advanced_networkpolicies
                    )
                else:
                    acns.security.advanced_network_policies = acns_advanced_networkpolicies

        if any(
            [
                network_plugin,
                network_plugin_mode,
                pod_cidr,
                pod_cidrs,
                service_cidr,
                service_cidrs,
                ip_families,
                dns_service_ip,
                docker_bridge_address,
                network_policy,
                network_dataplane,
            ]
        ):
            # Attention: RP would return UnexpectedLoadBalancerSkuForCurrentOutboundConfiguration internal server error
            # if load_balancer_sku is set to basic and load_balancer_profile is assigned.
            # Attention: SDK provides default values for pod_cidr, service_cidr, dns_service_ip, docker_bridge_cidr
            # and outbound_type, and they might be overwritten to None.
            network_profile = self.models.ContainerServiceNetworkProfile(
                network_plugin=network_plugin,
                network_plugin_mode=network_plugin_mode,
                pod_cidr=pod_cidr,
                pod_cidrs=pod_cidrs,
                service_cidr=service_cidr,
                service_cidrs=service_cidrs,
                ip_families=ip_families,
                dns_service_ip=dns_service_ip,
                docker_bridge_cidr=docker_bridge_address,
                network_policy=network_policy,
                network_dataplane=network_dataplane,
                load_balancer_sku=load_balancer_sku,
                load_balancer_profile=load_balancer_profile,
                outbound_type=outbound_type,
            )
        else:
            if load_balancer_sku == CONST_LOAD_BALANCER_SKU_STANDARD or load_balancer_profile:
                network_profile = self.models.ContainerServiceNetworkProfile(
                    network_plugin=network_plugin,
                    load_balancer_sku=load_balancer_sku,
                    load_balancer_profile=load_balancer_profile,
                    outbound_type=outbound_type,
                )
            if load_balancer_sku == CONST_LOAD_BALANCER_SKU_BASIC:
                # load balancer sku must be standard when load balancer profile is provided
                network_profile = self.models.ContainerServiceNetworkProfile(
                    network_plugin=network_plugin,
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
        if acns_enabled is not None:
            network_profile.advanced_networking = acns
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
                CONST_MONITORING_USING_AAD_MSI_AUTH: "true"
                if self.context.get_enable_msi_auth_for_monitoring()
                else "false",
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
            enable_syslog=self.context.get_enable_syslog(),
            data_collection_settings=self.context.get_data_collection_settings(),
            is_private_cluster=self.context.get_enable_private_cluster(),
            ampls_resource_id=self.context.get_ampls_resource_id(),
            enable_high_log_scale_mode=self.context.get_enable_high_log_scale_mode(),
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
        mc.aad_profile = aad_profile
        return mc

    def set_up_oidc_issuer_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up OIDC issuer profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)
        oidc_issuer_profile = self.context.get_oidc_issuer_profile()
        if oidc_issuer_profile is not None:
            mc.oidc_issuer_profile = oidc_issuer_profile

        return mc

    def set_up_workload_auto_scaler_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up workload auto-scaler profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_enable_keda():
            if mc.workload_auto_scaler_profile is None:
                mc.workload_auto_scaler_profile = self.models.ManagedClusterWorkloadAutoScalerProfile()
            mc.workload_auto_scaler_profile.keda = self.models.ManagedClusterWorkloadAutoScalerProfileKeda(enabled=True)

        if self.context.get_enable_vpa():
            if mc.workload_auto_scaler_profile is None:
                mc.workload_auto_scaler_profile = self.models.ManagedClusterWorkloadAutoScalerProfile()
            if mc.workload_auto_scaler_profile.vertical_pod_autoscaler is None:
                mc.workload_auto_scaler_profile.vertical_pod_autoscaler = self.models.ManagedClusterWorkloadAutoScalerProfileVerticalPodAutoscaler(enabled=True)
            else:
                mc.workload_auto_scaler_profile.vertical_pod_autoscaler.enabled = True
        return mc

    def set_up_custom_ca_trust_certificates(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up Custom CA Trust Certificates for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        ca_certs = self.context.get_custom_ca_trust_certificates()
        if ca_certs:
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()  # pylint: disable=no-member

            mc.security_profile.custom_ca_trust_certificates = ca_certs

        return mc

    def set_up_run_command(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up run command for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        disable_run_command = self.context.get_disable_run_command()
        if disable_run_command:
            if mc.api_server_access_profile is None:
                mc.api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile(
                    disable_run_command=True
                )
            else:
                mc.api_server_access_profile.disable_run_command = True

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
        if self.context.get_enable_apiserver_vnet_integration():
            if api_server_access_profile is None:
                api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile()
            # todo(levimm): remove the additional_properties after 2025-03-01 sdk is generated
            api_server_access_profile.additional_properties['enableVnetIntegration'] = True
            api_server_access_profile.enable_additional_properties_sending()
        if self.context.get_apiserver_subnet_id():
            if api_server_access_profile is None:
                # pylint: disable=no-member
                api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile()
            api_server_access_profile.additional_properties['subnetId'] = self.context.get_apiserver_subnet_id()
            api_server_access_profile.enable_additional_properties_sending()
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
                    client_id=kubelet_identity.client_id,       # TODO: may remove, rp would take care of this
                    object_id=kubelet_identity.principal_id     # TODO: may remove, rp would take care of this
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

    def set_up_http_proxy_config(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up http proxy config for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc.http_proxy_config = self.context.get_http_proxy_config()
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

        node_os_upgrade_channel = self.context.get_node_os_upgrade_channel()
        if node_os_upgrade_channel:
            if mc.auto_upgrade_profile is None:
                mc.auto_upgrade_profile = self.models.ManagedClusterAutoUpgradeProfile()
            mc.auto_upgrade_profile.node_os_upgrade_channel = node_os_upgrade_channel
        return mc

    def set_up_azure_service_mesh_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up azure service mesh for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        profile = self.context.get_initial_service_mesh_profile()
        if profile is not None:
            mc.service_mesh_profile = profile
        return mc

    def set_up_auto_scaler_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up autoscaler profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        cluster_autoscaler_profile = self.context.get_cluster_autoscaler_profile()
        mc.auto_scaler_profile = cluster_autoscaler_profile
        return mc

    def set_up_azure_container_storage(self, mc: ManagedCluster) -> ManagedCluster:  # pylint: disable=too-many-locals
        """Set up azure container storage for the Managed Cluster object
        :return: ManagedCluster
        """
        self._ensure_mc(mc)

        enable_azure_container_storage_param = self.context.raw_param.get("enable_azure_container_storage")
        if enable_azure_container_storage_param:
            self.context.set_intermediate("enable_azure_container_storage", enable_azure_container_storage_param, overwrite_exists=True)
            container_storage_version = self.context.raw_param.get("container_storage_version")

            if container_storage_version is not None and container_storage_version == CONST_ACSTOR_VERSION_V1:
                # read the azure container storage values passed
                pool_type = enable_azure_container_storage_param
                enable_azure_container_storage = pool_type is not None
                ephemeral_disk_volume_type = self.context.raw_param.get("ephemeral_disk_volume_type")
                ephemeral_disk_nvme_perf_tier = self.context.raw_param.get("ephemeral_disk_nvme_perf_tier")
                if (ephemeral_disk_volume_type is not None or ephemeral_disk_nvme_perf_tier is not None) and \
                        not enable_azure_container_storage:
                    params_defined_arr = []
                    if ephemeral_disk_volume_type is not None:
                        params_defined_arr.append('--ephemeral-disk-volume-type')
                    if ephemeral_disk_nvme_perf_tier is not None:
                        params_defined_arr.append('--ephemeral-disk-nvme-perf-tier')

                    params_defined = 'and '.join(params_defined_arr)
                    raise RequiredArgumentMissingError(
                        f'Cannot set {params_defined} without the parameter --enable-azure-container-storage.'
                    )

                if enable_azure_container_storage:
                    pool_name = self.context.raw_param.get("storage_pool_name")
                    pool_option = self.context.raw_param.get("storage_pool_option")
                    pool_sku = self.context.raw_param.get("storage_pool_sku")
                    pool_size = self.context.raw_param.get("storage_pool_size")
                    if not mc.agent_pool_profiles:
                        raise UnknownError("Encountered an unexpected error while getting the agent pools from the cluster.")
                    agentpool = mc.agent_pool_profiles[0]
                    agentpool_details = {}
                    pool_details = {}
                    pool_details["vm_size"] = agentpool.vm_size
                    pool_details["count"] = agentpool.count
                    pool_details["os_type"] = agentpool.os_type
                    pool_details["mode"] = agentpool.mode
                    pool_details["node_taints"] = agentpool.node_taints
                    pool_details["zoned"] = agentpool.availability_zones is not None
                    agentpool_details[agentpool.name] = pool_details
                    # Marking the only agentpool name as the valid nodepool for
                    # installing Azure Container Storage during `az aks create`
                    nodepool_list = agentpool.name

                    from azure.cli.command_modules.acs.azurecontainerstorage._validators import (
                        validate_enable_azure_container_storage_v1_params
                    )
                    from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
                        CONST_ACSTOR_IO_ENGINE_LABEL_KEY,
                        CONST_ACSTOR_IO_ENGINE_LABEL_VAL,
                        CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY,
                        CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD,
                    )
                    from azure.cli.command_modules.acs.azurecontainerstorage._helpers import generate_vm_sku_cache_for_region
                    generate_vm_sku_cache_for_region(self.cmd.cli_ctx, self.context.get_location())

                    default_ephemeral_disk_volume_type = CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY
                    default_ephemeral_disk_nvme_perf_tier = CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
                    validate_enable_azure_container_storage_v1_params(
                        pool_type,
                        pool_name,
                        pool_sku,
                        pool_option,
                        pool_size,
                        nodepool_list,
                        agentpool_details,
                        False,
                        False,
                        "",
                        False,
                        False,
                        False,
                        False,
                        ephemeral_disk_volume_type,
                        ephemeral_disk_nvme_perf_tier,
                        default_ephemeral_disk_volume_type,
                        default_ephemeral_disk_nvme_perf_tier,
                    )

                    # Setup Azure Container Storage labels on the nodepool
                    nodepool_labels = agentpool.node_labels
                    if nodepool_labels is None:
                        nodepool_labels = {}
                    nodepool_labels[CONST_ACSTOR_IO_ENGINE_LABEL_KEY] = CONST_ACSTOR_IO_ENGINE_LABEL_VAL
                    agentpool.node_labels = nodepool_labels

                    # set intermediates
                    self.context.set_intermediate("container_storage_version", container_storage_version, overwrite_exists=True)
                    self.context.set_intermediate("azure_container_storage_nodepools", nodepool_list, overwrite_exists=True)
                    self.context.set_intermediate(
                        "current_ephemeral_nvme_perf_tier",
                        default_ephemeral_disk_nvme_perf_tier,
                        overwrite_exists=True
                    )
                    self.context.set_intermediate(
                        "existing_ephemeral_disk_volume_type",
                        default_ephemeral_disk_volume_type,
                        overwrite_exists=True
                    )
            else:
                storage_pool_name = self.context.raw_param.get("storage_pool_name")
                pool_sku = self.context.raw_param.get("storage_pool_sku")
                pool_option = self.context.raw_param.get("storage_pool_option")
                pool_size = self.context.raw_param.get("storage_pool_size")

                from azure.cli.command_modules.acs.azurecontainerstorage._validators import (
                    validate_enable_azure_container_storage_params,
                )
                validate_enable_azure_container_storage_params(
                    enable_azure_container_storage_param,
                    False,
                    False,
                    False,
                    False,
                    "",
                    storage_pool_name,
                    pool_sku,
                    pool_option,
                    pool_size,
                )

        return mc

    def set_up_sku(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up sku (uptime sla) for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc.sku = self.models.ManagedClusterSKU()
        skuName = self.context.get_sku_name()
        tier = self.context.get_tier()

        if skuName == CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC:
            mc.sku.name = "Automatic"
            # default tier for automatic sku is standard
            mc.sku.tier = "Standard"
        else:
            mc.sku.name = "Base"

        if tier == CONST_MANAGED_CLUSTER_SKU_TIER_STANDARD:
            mc.sku.tier = "Standard"
        if tier == CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM:
            mc.sku.tier = "Premium"
        # backfill the tier to "Free" if it's not set
        if mc.sku.tier is None:
            mc.sku.tier = "Free"
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

    def set_up_k8s_support_plan(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up supportPlan for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        support_plan = self.context.get_k8s_support_plan()
        if support_plan == KubernetesSupportPlan.AKS_LONG_TERM_SUPPORT:
            if mc is None or mc.sku is None or mc.sku.tier.lower() != CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM.lower():
                raise AzCLIError("Long term support is only available for premium tier clusters.")

        mc.support_plan = support_plan
        return mc

    def set_up_azure_monitor_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up azure monitor profile for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)
        # read the original value passed by the command
        ksm_metric_labels_allow_list = self.context.raw_param.get("ksm_metric_labels_allow_list")
        ksm_metric_annotations_allow_list = self.context.raw_param.get("ksm_metric_annotations_allow_list")
        if ksm_metric_labels_allow_list is None:
            ksm_metric_labels_allow_list = ""
        if ksm_metric_annotations_allow_list is None:
            ksm_metric_annotations_allow_list = ""
        if self.context.get_enable_azure_monitor_metrics():
            if mc.azure_monitor_profile is None:
                mc.azure_monitor_profile = self.models.ManagedClusterAzureMonitorProfile()
            mc.azure_monitor_profile.metrics = self.models.ManagedClusterAzureMonitorProfileMetrics(enabled=False)
            mc.azure_monitor_profile.metrics.kube_state_metrics = self.models.ManagedClusterAzureMonitorProfileKubeStateMetrics(  # pylint:disable=line-too-long
                metric_labels_allowlist=str(ksm_metric_labels_allow_list),
                metric_annotations_allow_list=str(ksm_metric_annotations_allow_list))
            # set intermediate
            self.context.set_intermediate("azuremonitormetrics_addon_enabled", True, overwrite_exists=True)
        return mc

    def set_up_ingress_web_app_routing(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up the app routing profile in the ingress profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        addons = self.context.get_enable_addons()
        if "web_application_routing" in addons or self.context.get_enable_app_routing():
            if mc.ingress_profile is None:
                mc.ingress_profile = self.models.ManagedClusterIngressProfile()  # pylint: disable=no-member
            mc.ingress_profile.web_app_routing = (
                self.models.ManagedClusterIngressProfileWebAppRouting(enabled=True)  # pylint: disable=no-member
            )

            nginx_ingress_controller = self.context.get_app_routing_default_nginx_controller()

            if nginx_ingress_controller:
                mc.ingress_profile.web_app_routing.nginx = (
                    self.models.ManagedClusterIngressProfileNginx(
                        default_ingress_controller_type=nginx_ingress_controller
                    )
                )

            if "web_application_routing" in addons:
                dns_zone_resource_ids = self.context.get_dns_zone_resource_ids()
                mc.ingress_profile.web_app_routing.dns_zone_resource_ids = dns_zone_resource_ids

        return mc

    def set_up_ai_toolchain_operator(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        if self.context.get_ai_toolchain_operator(enable_validation=True):
            if mc.ai_toolchain_operator_profile is None:
                mc.ai_toolchain_operator_profile = self.models.ManagedClusterAIToolchainOperatorProfile()  # pylint: disable=no-member
            # set enabled
            mc.ai_toolchain_operator_profile.enabled = True

        # Default is disabled so no need to worry about that here
        return mc

    def set_up_cost_analysis(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        if self.context.get_enable_cost_analysis():
            if mc.metrics_profile is None:
                mc.metrics_profile = self.models.ManagedClusterMetricsProfile()
            if mc.metrics_profile.cost_analysis is None:
                mc.metrics_profile.cost_analysis = self.models.ManagedClusterCostAnalysis()

            # set enabled
            mc.metrics_profile.cost_analysis.enabled = True

        # Default is disabled so no need to worry about that here

        return mc

    def set_up_metrics_profile(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        mc = self.set_up_cost_analysis(mc)

        return mc

    def set_up_node_resource_group_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up node resource group profile for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        node_resource_group_profile = None
        nrg_lockdown_restriction_level = self.context.get_nrg_lockdown_restriction_level()
        if nrg_lockdown_restriction_level:
            node_resource_group_profile = self.models.ManagedClusterNodeResourceGroupProfile(restriction_level=nrg_lockdown_restriction_level)
        mc.node_resource_group_profile = node_resource_group_profile
        return mc

    def set_up_bootstrap_profile(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        bootstrap_artifact_source = self.context.get_bootstrap_artifact_source()
        bootstrap_container_registry_resource_id = self.context.get_bootstrap_container_registry_resource_id()
        if hasattr(mc, "bootstrap_profile") and bootstrap_artifact_source is not None:
            if bootstrap_artifact_source != CONST_ARTIFACT_SOURCE_CACHE and bootstrap_container_registry_resource_id:
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --bootstrap-container-registry-resource-id when "
                    "--bootstrap-artifact-source is not Cache."
                )
            if mc.bootstrap_profile is None:
                mc.bootstrap_profile = self.models.ManagedClusterBootstrapProfile()  # pylint: disable=no-member
            mc.bootstrap_profile.artifact_source = bootstrap_artifact_source
            mc.bootstrap_profile.container_registry_id = bootstrap_container_registry_resource_id

        return mc

    def set_up_static_egress_gateway(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        if self.context.get_enable_static_egress_gateway():
            if not mc.network_profile:
                raise UnknownError(
                    "Unexpectedly get an empty network profile in the process of "
                    "updating enable-static-egress-gateway config."
                )
            if mc.network_profile.static_egress_gateway_profile is None:
                mc.network_profile.static_egress_gateway_profile = (
                    self.models.ManagedClusterStaticEgressGatewayProfile()  # pylint: disable=no-member
                )
            # set enabled
            mc.network_profile.static_egress_gateway_profile.enabled = True

        # Default is disabled so no need to worry about that here
        return mc

    def construct_mc_profile_default(self, bypass_restore_defaults: bool = False) -> ManagedCluster:
        """The overall controller used to construct the default ManagedCluster profile.

        The completely constructed ManagedCluster object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the ManagedCluster object
        """
        # initialize the ManagedCluster object
        mc = self.init_mc()
        # DO NOT MOVE: remove defaults
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
        # set up oidc issuer profile
        mc = self.set_up_oidc_issuer_profile(mc)
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
        # set up defender
        mc = self.set_up_defender(mc)
        # set up workload identity profile
        mc = self.set_up_workload_identity_profile(mc)
        # set up storage profile
        mc = self.set_up_storage_profile(mc)
        # set up azure keyvalut kms
        mc = self.set_up_azure_keyvault_kms(mc)
        # set up image cleaner
        mc = self.set_up_image_cleaner(mc)
        # set up http proxy config
        mc = self.set_up_http_proxy_config(mc)
        # set up workload autoscaler profile
        mc = self.set_up_workload_auto_scaler_profile(mc)
        # set up app routing profile
        mc = self.set_up_ingress_web_app_routing(mc)
        # set up custom ca trust certificates
        mc = self.set_up_custom_ca_trust_certificates(mc)
        # set up run command
        mc = self.set_up_run_command(mc)
        # setup k8s support plan
        mc = self.set_up_k8s_support_plan(mc)
        # set up azure monitor metrics profile
        mc = self.set_up_azure_monitor_profile(mc)
        # set up azure service mesh profile
        mc = self.set_up_azure_service_mesh_profile(mc)
        # set up for azure container storage
        mc = self.set_up_azure_container_storage(mc)
        # set up metrics profile
        mc = self.set_up_metrics_profile(mc)
        # set up node resource group profile
        mc = self.set_up_node_resource_group_profile(mc)
        # set up AI toolchain operator
        mc = self.set_up_ai_toolchain_operator(mc)
        # set up bootstrap profile
        mc = self.set_up_bootstrap_profile(mc)
        # set up static egress gateway profile
        mc = self.set_up_static_egress_gateway(mc)
        # set up node provisioning profile
        mc = self.set_up_node_provisioning_profile(mc)

        # DO NOT MOVE: keep this at the bottom, restore defaults
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
        azuremonitormetrics_addon_enabled = self.context.get_intermediate(
            "azuremonitormetrics_addon_enabled",
            default_value=False
        )
        enable_managed_identity = self.context.get_enable_managed_identity()
        attach_acr = self.context.get_attach_acr()
        need_grant_vnet_permission_to_cluster_identity = self.context.get_intermediate(
            "need_post_creation_vnet_permission_granting", default_value=False
        )
        enable_azure_container_storage = self.context.get_intermediate(
            "enable_azure_container_storage",
            default_value=False
        )

        # pylint: disable=too-many-boolean-expressions
        if (
            monitoring_addon_enabled or
            ingress_appgw_addon_enabled or
            virtual_node_addon_enabled or
            azuremonitormetrics_addon_enabled or
            (enable_managed_identity and attach_acr) or
            need_grant_vnet_permission_to_cluster_identity or
            enable_azure_container_storage
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

    # pylint: disable=too-many-locals
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
                    from azure.mgmt.core.tools import resource_id

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
            elif self.context.raw_param.get("enable_addons") is not None:
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
                    enable_syslog=self.context.get_enable_syslog(),
                    data_collection_settings=self.context.get_data_collection_settings(),
                    is_private_cluster=self.context.get_enable_private_cluster(),
                    ampls_resource_id=self.context.get_ampls_resource_id(),
                    enable_high_log_scale_mode=self.context.get_enable_high_log_scale_mode(),
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
                    assignee_principal_type=self.context.get_assignee_principal_type()
                )

        # azure monitor metrics addon (v2)
        azuremonitormetrics_addon_enabled = self.context.get_intermediate(
            "azuremonitormetrics_addon_enabled",
            default_value=False
        )
        if azuremonitormetrics_addon_enabled:
            # Create the DC* objects, AMW, recording rules and grafana link here
            self.context.external_functions.ensure_azure_monitor_profile_prerequisites(
                self.cmd,
                self.context.get_subscription_id(),
                self.context.get_resource_group_name(),
                self.context.get_name(),
                self.context.get_location(),
                self.__raw_parameters,
                self.context.get_disable_azure_monitor_metrics(),
                True
            )

        # enable azure container storage
        enable_azure_container_storage = self.context.get_intermediate("enable_azure_container_storage")
        container_storage_version = self.context.get_intermediate("container_storage_version")
        if enable_azure_container_storage:
            if container_storage_version is not None:
                if container_storage_version == CONST_ACSTOR_VERSION_V1:
                    if cluster.identity_profile is None or cluster.identity_profile["kubeletidentity"] is None:
                        logger.warning(
                            "Unexpected error getting kubelet's identity for the cluster. "
                            "Unable to perform the azure container storage operation."
                        )
                        return

                    # Get the node_resource_group from the cluster object since
                    # `mc` in `context` still doesn't have the updated node_resource_group.
                    if cluster.node_resource_group is None:
                        logger.warning(
                            "Unexpected error getting cluster's node resource group. "
                            "Unable to perform the azure container storage operation."
                        )
                        return

                    pool_name = self.context.raw_param.get("storage_pool_name")
                    pool_type = self.context.raw_param.get("enable_azure_container_storage")
                    pool_option = self.context.raw_param.get("storage_pool_option")
                    pool_sku = self.context.raw_param.get("storage_pool_sku")
                    pool_size = self.context.raw_param.get("storage_pool_size")
                    ephemeral_disk_volume_type = self.context.raw_param.get("ephemeral_disk_volume_type")
                    ephemeral_disk_nvme_perf_tier = self.context.raw_param.get("ephemeral_disk_nvme_perf_tier")
                    existing_ephemeral_disk_volume_type = self.context.get_intermediate("existing_ephemeral_disk_volume_type")
                    existing_ephemeral_nvme_perf_tier = self.context.get_intermediate("current_ephemeral_nvme_perf_tier")
                    kubelet_identity_object_id = cluster.identity_profile["kubeletidentity"].object_id
                    node_resource_group = cluster.node_resource_group
                    agent_pool_vm_sizes = []
                    if len(cluster.agent_pool_profiles) > 0:
                        # Cluster creation has only 1 agentpool
                        agentpool_profile = cluster.agent_pool_profiles[0]
                        agent_pool_vm_sizes.append(agentpool_profile.vm_size)

                    self.context.external_functions.perform_enable_azure_container_storage_v1(
                        self.cmd,
                        self.context.get_subscription_id(),
                        self.context.get_resource_group_name(),
                        self.context.get_name(),
                        node_resource_group,
                        kubelet_identity_object_id,
                        pool_name,
                        pool_type,
                        pool_size,
                        pool_sku,
                        pool_option,
                        agent_pool_vm_sizes,
                        ephemeral_disk_volume_type,
                        ephemeral_disk_nvme_perf_tier,
                        True,
                        existing_ephemeral_disk_volume_type,
                        existing_ephemeral_nvme_perf_tier,
                    )
            else:
                self.context.external_functions.perform_azure_container_storage_update(
                    self.cmd,
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    enable_azure_container_storage,
                )

        # Add role assignments for automatic sku
        if cluster.sku is not None and cluster.sku.name == "Automatic":
            try:
                user = get_graph_client(self.cmd.cli_ctx).signed_in_user_get()
            except Exception as e:  # pylint: disable=broad-except
                logger.warning("Could not get signed in user: %s", str(e))
            else:
                self.context.external_functions.add_role_assignment_executor(  # type: ignore # pylint: disable=protected-access
                    self.cmd,
                    "Azure Kubernetes Service RBAC Cluster Admin",
                    user["id"],
                    scope=cluster.id,
                    resolve_assignee=False,
                )

    def put_mc(self, mc: ManagedCluster) -> ManagedCluster:
        active_cloud = get_active_cloud(self.cmd.cli_ctx)
        if active_cloud.profile != "latest":
            cluster = sdk_no_wait(
                self.context.get_no_wait(),
                self.client.begin_create_or_update,
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
            )
            return cluster

        if self.check_is_postprocessing_required(mc):
            # send request
            poller = self.client.begin_create_or_update(
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
                if_match=self.context.get_if_match(),
                if_none_match=self.context.get_if_none_match(),
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
                if_match=self.context.get_if_match(),
                if_none_match=self.context.get_if_none_match(),
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
            except HttpResponseError as ex:
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
            self.context.get_nodepool_labels() is None and
            self.context.get_nodepool_taints() is None and
            self.context.get_load_balancer_managed_outbound_ip_count() is None and
            self.context.get_load_balancer_managed_outbound_ipv6_count() is None and
            self.context.get_load_balancer_idle_timeout() is None and
            self.context.get_load_balancer_outbound_ports() is None and
            self.context.get_nat_gateway_managed_outbound_ip_count() is None and
            self.context.get_nat_gateway_idle_timeout() is None
        )

        if not is_changed and is_default:
            reconcilePrompt = 'no argument specified to update would you like to reconcile to current settings?'
            if not prompt_y_n(reconcilePrompt, default="n"):
                # Note: Uncomment the followings to automatically generate the error message.
                option_names = [
                    '"{}"'.format(format_parameter_name_to_option_name(x))
                    for x in self.context.raw_param.keys()
                    if x not in excluded_keys
                ]
                error_msg = "Please specify one or more of {}.".format(
                    " or ".join(option_names)
                )
                raise RequiredArgumentMissingError(error_msg)

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

        # update nodepool taints for all nodepools
        nodepool_taints = self.context.get_nodepool_taints()
        if nodepool_taints is not None:
            for agent_profile in mc.agent_pool_profiles:
                agent_profile.node_taints = nodepool_taints
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

    def update_upgrade_settings(self, mc: ManagedCluster) -> ManagedCluster:
        """Update upgrade settings for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        existing_until = None
        if mc.upgrade_settings is not None and mc.upgrade_settings.override_settings is not None and mc.upgrade_settings.override_settings.until is not None:
            existing_until = mc.upgrade_settings.override_settings.until

        force_upgrade = self.context.get_force_upgrade()
        override_until = self.context.get_upgrade_override_until()

        if force_upgrade is not None or override_until is not None:
            if mc.upgrade_settings is None:
                mc.upgrade_settings = self.models.ClusterUpgradeSettings()
            if mc.upgrade_settings.override_settings is None:
                mc.upgrade_settings.override_settings = self.models.UpgradeOverrideSettings()
            # sets force_upgrade
            if force_upgrade is not None:
                mc.upgrade_settings.override_settings.force_upgrade = force_upgrade
            # sets until
            if override_until is not None:
                try:
                    mc.upgrade_settings.override_settings.until = parse(override_until)
                except Exception:  # pylint: disable=broad-except
                    raise InvalidArgumentValueError(
                        f"{override_until} is not a valid datatime format."
                    )
            elif force_upgrade:
                default_extended_until = datetime.datetime.utcnow() + datetime.timedelta(days=3)
                if existing_until is None or existing_until.timestamp() < default_extended_until.timestamp():
                    mc.upgrade_settings.override_settings.until = default_extended_until

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
        assignee_principal_type = self.context.get_assignee_principal_type()
        if attach_acr:
            self.context.external_functions.ensure_aks_acr(
                self.cmd,
                assignee=assignee,
                acr_name_or_id=attach_acr,
                subscription_id=subscription_id,
                is_service_principal=is_service_principal,
                assignee_principal_type=assignee_principal_type,
            )

        if detach_acr:
            self.context.external_functions.ensure_aks_acr(
                self.cmd,
                assignee=assignee,
                acr_name_or_id=detach_acr,
                subscription_id=subscription_id,
                detach=True,
                is_service_principal=is_service_principal,
                assignee_principal_type=assignee_principal_type,
            )

    def update_azure_service_mesh_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update azure service mesh profile for the ManagedCluster object.
        """
        self._ensure_mc(mc)

        mc.service_mesh_profile = self.context.update_azure_service_mesh_profile()
        return mc

    def update_sku(self, mc: ManagedCluster) -> ManagedCluster:
        """Update sku (uptime sla) for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # there are existing MCs with nil sku, that is Base/Free
        if mc.sku is None:
            mc.sku = self.models.ManagedClusterSKU()
        skuName = self.context.get_sku_name()
        tier = self.context.get_tier()
        if skuName == CONST_MANAGED_CLUSTER_SKU_NAME_AUTOMATIC:
            mc.sku.name = "Automatic"
        else:
            mc.sku.name = "Base"

        # Premium without LTS is ok (not vice versa)
        if tier == CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM:
            mc.sku.tier = "Premium"
        if tier == CONST_MANAGED_CLUSTER_SKU_TIER_STANDARD:
            mc.sku.tier = "Standard"
        if tier == CONST_MANAGED_CLUSTER_SKU_TIER_FREE:
            mc.sku.tier = "Free"
        # backfill the tier to "Free" if it's not set
        if mc.sku.tier is None:
            mc.sku.tier = "Free"
        return mc

    def update_outbound_type_in_network_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update outbound type of network profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        outboundType = self.context.get_outbound_type()
        if outboundType:
            mc.network_profile.outbound_type = outboundType
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
        outbound_type = self.context.get_outbound_type()
        if outbound_type and outbound_type != CONST_OUTBOUND_TYPE_LOAD_BALANCER:
            mc.network_profile.load_balancer_profile = None
        else:
            # In the internal function "_update_load_balancer_profile", it will check whether the provided parameters
            # have been assigned, and if there are any, the corresponding profile will be modified; otherwise, it will
            # remain unchanged.
            mc.network_profile.load_balancer_profile = _update_load_balancer_profile(
                managed_outbound_ip_count=self.context.get_load_balancer_managed_outbound_ip_count(),
                managed_outbound_ipv6_count=self.context.get_load_balancer_managed_outbound_ipv6_count(),
                outbound_ips=self.context.get_load_balancer_outbound_ips(),
                outbound_ip_prefixes=self.context.get_load_balancer_outbound_ip_prefixes(),
                outbound_ports=self.context.get_load_balancer_outbound_ports(),
                idle_timeout=self.context.get_load_balancer_idle_timeout(),
                backend_pool_type=self.context.get_load_balancer_backend_pool_type(),
                profile=mc.network_profile.load_balancer_profile,
                models=self.models.load_balancer_models)
        return mc

    def update_nat_gateway_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update nat gateway profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if not mc.network_profile:
            raise UnknownError(
                "Unexpectedly get an empty network profile in the process of updating nat gateway profile."
            )
        outbound_type = self.context.get_outbound_type()
        if outbound_type and outbound_type != CONST_OUTBOUND_TYPE_MANAGED_NAT_GATEWAY:
            mc.network_profile.nat_gateway_profile = None
        else:
            mc.network_profile.nat_gateway_profile = _update_nat_gateway_profile(
                managed_outbound_ip_count=self.context.get_nat_gateway_managed_outbound_ip_count(),
                idle_timeout=self.context.get_nat_gateway_idle_timeout(),
                profile=mc.network_profile.nat_gateway_profile,
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
        private_dns_zone = self.context.get_private_dns_zone()
        if api_server_authorized_ip_ranges is not None:
            # empty string is valid as it disables ip whitelisting
            profile_holder.authorized_ip_ranges = api_server_authorized_ip_ranges
        if disable_public_fqdn:
            profile_holder.enable_private_cluster_public_fqdn = False
        if enable_public_fqdn:
            profile_holder.enable_private_cluster_public_fqdn = True
        if private_dns_zone is not None:
            profile_holder.private_dns_zone = private_dns_zone
        if self.context.get_enable_apiserver_vnet_integration():
            profile_holder.additional_properties['enableVnetIntegration'] = True
            profile_holder.enable_additional_properties_sending()
        if self.context.get_apiserver_subnet_id():
            profile_holder.additional_properties['subnetId'] = self.context.get_apiserver_subnet_id()
            profile_holder.enable_additional_properties_sending()
        if self.context.get_enable_private_cluster():
            profile_holder.enable_private_cluster = True
            # send additional properties when enable private cluster since enableVnetIntegration is required
            profile_holder.enable_additional_properties_sending()
        if self.context.get_disable_private_cluster():
            profile_holder.enable_private_cluster = False
            # send additional properties when enable private cluster since enableVnetIntegration is required
            profile_holder.enable_additional_properties_sending()

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
        disable_windows_gmsa = self.context.get_disable_windows_gmsa()

        if any([enable_ahub, disable_ahub, windows_admin_password, enable_windows_gmsa, disable_windows_gmsa]) and not mc.windows_profile:
            # seems we know the error
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
        if disable_windows_gmsa:
            mc.windows_profile.gmsa_profile = self.models.WindowsGmsaProfile(
                enabled=False,
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

    def update_oidc_issuer_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update OIDC issuer profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)
        oidc_issuer_profile = self.context.get_oidc_issuer_profile()
        if oidc_issuer_profile is not None:
            mc.oidc_issuer_profile = oidc_issuer_profile

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

        node_os_upgrade_channel = self.context.get_node_os_upgrade_channel()
        if node_os_upgrade_channel is not None:
            if mc.auto_upgrade_profile is None:
                mc.auto_upgrade_profile = self.models.ManagedClusterAutoUpgradeProfile()
            mc.auto_upgrade_profile.node_os_upgrade_channel = node_os_upgrade_channel

        return mc

    def update_network_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update ip families settings for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        ip_families = self.context.get_ip_families()
        if ip_families:
            mc.network_profile.ip_families = ip_families

        self.update_network_plugin_settings(mc)

        loadbalancer_sku = self.context.get_load_balancer_sku()
        if loadbalancer_sku:
            mc.network_profile.load_balancer_sku = loadbalancer_sku

        return mc

    def update_network_plugin_settings(self, mc: ManagedCluster) -> ManagedCluster:
        """Update network plugin settings of network profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        network_plugin_mode = self.context.get_network_plugin_mode()
        if network_plugin_mode:
            mc.network_profile.network_plugin_mode = network_plugin_mode

        network_plugin = self.context.get_network_plugin()
        if network_plugin:
            mc.network_profile.network_plugin = network_plugin

        (
            pod_cidr,
            _,
            _,
            _,
            _
        ) = self.context.get_pod_cidr_and_service_cidr_and_dns_service_ip_and_docker_bridge_address_and_network_policy()

        network_dataplane = self.context.get_network_dataplane()
        if network_dataplane:
            mc.network_profile.network_dataplane = network_dataplane

        if pod_cidr:
            mc.network_profile.pod_cidr = pod_cidr

        network_policy = self.context.get_network_policy()
        if network_policy:
            mc.network_profile.network_policy = network_policy

        return mc

    def update_network_profile_advanced_networking(self, mc: ManagedCluster) -> ManagedCluster:
        """Update advanced networking settings of network profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)
        (acns_enabled, acns_observability, acns_security) = self.context.get_acns_enablement()
        acns_advanced_networkpolicies = self.context.get_acns_advanced_networkpolicies()
        if acns_enabled is not None:
            acns = self.models.AdvancedNetworking(
                enabled=acns_enabled,
            )
            if acns_observability is not None:
                acns.observability = self.models.AdvancedNetworkingObservability(
                    enabled=acns_observability,
                )
            if acns_security is not None:
                acns.security = self.models.AdvancedNetworkingSecurity(
                    enabled=acns_security,
                )
            if acns_advanced_networkpolicies is not None:
                if acns.security is None:
                    acns.security = self.models.AdvancedNetworkingSecurity(
                        advanced_network_policies=acns_advanced_networkpolicies
                    )
                else:
                    acns.security.advanced_network_policies = acns_advanced_networkpolicies
        if acns_enabled is not None:
            mc.network_profile.advanced_networking = acns
        return mc

    def update_http_proxy_config(self, mc: ManagedCluster) -> ManagedCluster:
        """Set up http proxy config for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc.http_proxy_config = self.context.get_http_proxy_config()
        return mc

    def update_identity(self, mc: ManagedCluster) -> ManagedCluster:
        """Update identity for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        current_identity_type = "spn"
        current_user_assigned_identity = ""
        if mc.identity is not None:
            current_identity_type = mc.identity.type.casefold()
            if mc.identity.user_assigned_identities is not None and len(mc.identity.user_assigned_identities) > 0:
                current_user_assigned_identity = list(mc.identity.user_assigned_identities.keys())[0]

        goal_identity_type = current_identity_type
        assign_identity = self.context.get_assign_identity()
        if self.context.get_enable_managed_identity():
            if not assign_identity:
                goal_identity_type = "systemassigned"
            else:
                goal_identity_type = "userassigned"

        is_update_identity = ((current_identity_type != goal_identity_type) or
                              (current_identity_type == goal_identity_type and
                              current_identity_type == "userassigned" and
                              assign_identity is not None and
                              current_user_assigned_identity != assign_identity))
        if is_update_identity:
            if current_identity_type == "spn":
                msg = (
                    "Your cluster is using service principal, and you are going to update "
                    "the cluster to use {} managed identity.\nAfter updating, your "
                    "cluster's control plane and addon pods will switch to use managed "
                    "identity, but kubelet will KEEP USING SERVICE PRINCIPAL "
                    "until you upgrade your agentpool.\n"
                    "Are you sure you want to perform this operation?"
                ).format(goal_identity_type)
            elif current_identity_type != goal_identity_type:
                msg = (
                    "Your cluster is already using {} managed identity, and you are going to "
                    "update the cluster to use {} managed identity.\n"
                    "Are you sure you want to perform this operation?"
                ).format(current_identity_type, goal_identity_type)
            else:
                msg = (
                    "Your cluster is already using userassigned managed identity, current control plane identity is {},"
                    "and you are going to update the cluster identity to {}.\n"
                    "Are you sure you want to perform this operation?"
                ).format(current_user_assigned_identity, assign_identity)
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

    def ensure_azure_keyvault_secrets_provider_addon_profile(
        self,
        azure_keyvault_secrets_provider_addon_profile: ManagedClusterAddonProfile,
    ) -> ManagedClusterAddonProfile:
        # determine the value of constants
        addon_consts = self.context.get_addon_consts()
        CONST_SECRET_ROTATION_ENABLED = addon_consts.get(
            "CONST_SECRET_ROTATION_ENABLED"
        )
        CONST_ROTATION_POLL_INTERVAL = addon_consts.get(
            "CONST_ROTATION_POLL_INTERVAL"
        )
        if (
            azure_keyvault_secrets_provider_addon_profile is None or
            not azure_keyvault_secrets_provider_addon_profile.enabled
        ):
            raise InvalidArgumentValueError(
                "Addon azure-keyvault-secrets-provider is not enabled. "
                "Please use command 'az aks enable-addons' to enable it."
            )
        if azure_keyvault_secrets_provider_addon_profile.config is None:
            # backfill to default
            azure_keyvault_secrets_provider_addon_profile.config = {
                CONST_SECRET_ROTATION_ENABLED: "false",
                CONST_ROTATION_POLL_INTERVAL: "2m",
            }
        return azure_keyvault_secrets_provider_addon_profile

    def update_azure_keyvault_secrets_provider_addon_profile(
        self,
        azure_keyvault_secrets_provider_addon_profile: ManagedClusterAddonProfile,
    ) -> ManagedClusterAddonProfile:
        """Update azure keyvault secrets provider addon profile.

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
            azure_keyvault_secrets_provider_addon_profile = (
                self.ensure_azure_keyvault_secrets_provider_addon_profile(
                    azure_keyvault_secrets_provider_addon_profile
                )
            )
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_SECRET_ROTATION_ENABLED
            ] = "true"

        if self.context.get_disable_secret_rotation():
            azure_keyvault_secrets_provider_addon_profile = (
                self.ensure_azure_keyvault_secrets_provider_addon_profile(
                    azure_keyvault_secrets_provider_addon_profile
                )
            )
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_SECRET_ROTATION_ENABLED
            ] = "false"

        if self.context.get_rotation_poll_interval() is not None:
            azure_keyvault_secrets_provider_addon_profile = (
                self.ensure_azure_keyvault_secrets_provider_addon_profile(
                    azure_keyvault_secrets_provider_addon_profile
                )
            )
            azure_keyvault_secrets_provider_addon_profile.config[
                CONST_ROTATION_POLL_INTERVAL
            ] = self.context.get_rotation_poll_interval()
        return azure_keyvault_secrets_provider_addon_profile

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

        # update azure keyvault secrets provider profile
        azure_keyvault_secrets_provider_addon_profile = (
            self.update_azure_keyvault_secrets_provider_addon_profile(
                azure_keyvault_secrets_provider_addon_profile
            )
        )
        if azure_keyvault_secrets_provider_addon_profile:
            # mc.addon_profiles should not be None if azure_keyvault_secrets_provider_addon_profile is not None
            mc.addon_profiles[
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
            ] = azure_keyvault_secrets_provider_addon_profile
        return mc

    def update_storage_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update storage profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc.storage_profile = self.context.get_storage_profile()

        return mc

    def update_defender(self, mc: ManagedCluster) -> ManagedCluster:
        """Update defender for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        defender = self.context.get_defender_config()
        if defender:
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()

            mc.security_profile.defender = defender

        return mc

    def update_workload_identity_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update workload identity profile for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        profile = self.context.get_workload_identity_profile()
        if profile:
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()
            mc.security_profile.workload_identity = profile

        return mc

    def update_k8s_support_plan(self, mc: ManagedCluster) -> ManagedCluster:
        """Update supportPlan for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        support_plan = self.context.get_k8s_support_plan()
        if support_plan == KubernetesSupportPlan.AKS_LONG_TERM_SUPPORT:
            if mc is None or mc.sku is None or mc.sku.tier.lower() != CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM.lower():
                raise AzCLIError("Long term support is only available for premium tier clusters.")

        mc.support_plan = support_plan
        return mc

    def update_azure_keyvault_kms(self, mc: ManagedCluster) -> ManagedCluster:
        """Update security profile azureKeyvaultKms for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_enable_azure_keyvault_kms():
            # get kms profile
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()
            azure_key_vault_kms_profile = mc.security_profile.azure_key_vault_kms
            if azure_key_vault_kms_profile is None:
                azure_key_vault_kms_profile = self.models.AzureKeyVaultKms()
                mc.security_profile.azure_key_vault_kms = azure_key_vault_kms_profile

            # set enabled
            azure_key_vault_kms_profile.enabled = True
            # set key id
            azure_key_vault_kms_profile.key_id = self.context.get_azure_keyvault_kms_key_id()
            # set network access, should never be None for now, can be safely assigned, temp fix for rp
            # the value is obtained from user input or backfilled from existing mc or to default value
            azure_key_vault_kms_profile.key_vault_network_access = (
                self.context.get_azure_keyvault_kms_key_vault_network_access()
            )
            # set key vault resource id
            if azure_key_vault_kms_profile.key_vault_network_access == CONST_AZURE_KEYVAULT_NETWORK_ACCESS_PRIVATE:
                azure_key_vault_kms_profile.key_vault_resource_id = (
                    self.context.get_azure_keyvault_kms_key_vault_resource_id()
                )
            else:
                azure_key_vault_kms_profile.key_vault_resource_id = ""

        if self.context.get_disable_azure_keyvault_kms():
            # get kms profile
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()
            azure_key_vault_kms_profile = mc.security_profile.azure_key_vault_kms
            if azure_key_vault_kms_profile is None:
                azure_key_vault_kms_profile = self.models.AzureKeyVaultKms()
                mc.security_profile.azure_key_vault_kms = azure_key_vault_kms_profile

            # set enabled to False
            azure_key_vault_kms_profile.enabled = False

        return mc

    def update_image_cleaner(self, mc: ManagedCluster) -> ManagedCluster:
        """Update security profile imageCleaner for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        enable_image_cleaner = self.context.get_enable_image_cleaner()
        disable_image_cleaner = self.context.get_disable_image_cleaner()
        interval_hours = self.context.get_image_cleaner_interval_hours()

        # no image cleaner related changes
        if not enable_image_cleaner and not disable_image_cleaner and interval_hours is None:
            return mc

        if mc.security_profile is None:
            mc.security_profile = self.models.ManagedClusterSecurityProfile()

        image_cleaner_profile = mc.security_profile.image_cleaner

        if image_cleaner_profile is None:
            image_cleaner_profile = self.models.ManagedClusterSecurityProfileImageCleaner()
            mc.security_profile.image_cleaner = image_cleaner_profile

            # init the image cleaner profile
            image_cleaner_profile.enabled = False
            image_cleaner_profile.interval_hours = 7 * 24

        if enable_image_cleaner:
            image_cleaner_profile.enabled = True

        if disable_image_cleaner:
            image_cleaner_profile.enabled = False

        if interval_hours is not None:
            image_cleaner_profile.interval_hours = interval_hours

        return mc

    # pylint: disable=too-many-branches
    def update_app_routing_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update app routing profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # get parameters from context
        enable_app_routing = self.context.get_enable_app_routing()
        enable_keyvault_secret_provider = self.context.get_enable_kv()
        dns_zone_resource_ids = self.context.get_dns_zone_resource_ids_from_input()
        nginx = self.context.get_nginx()

        # update ManagedCluster object with app routing settings
        mc.ingress_profile = (
            mc.ingress_profile or
            self.models.ManagedClusterIngressProfile()  # pylint: disable=no-member
        )
        mc.ingress_profile.web_app_routing = (
            mc.ingress_profile.web_app_routing or
            self.models.ManagedClusterIngressProfileWebAppRouting()  # pylint: disable=no-member
        )
        if enable_app_routing is not None:
            if mc.ingress_profile.web_app_routing.enabled == enable_app_routing:
                error_message = (
                    "App Routing is already enabled.\n"
                    if enable_app_routing
                    else "App Routing is already disabled.\n"
                )
                raise CLIError(error_message)
            mc.ingress_profile.web_app_routing.enabled = enable_app_routing

        # enable keyvault secret provider addon
        if enable_keyvault_secret_provider:
            self._enable_keyvault_secret_provider_addon(mc)

        # modify DNS zone resource IDs
        if dns_zone_resource_ids:
            self._update_dns_zone_resource_ids(mc, dns_zone_resource_ids)

        # modify default nic config
        if nginx:
            self._update_app_routing_nginx(mc, nginx)

        return mc

    def _update_app_routing_nginx(self, mc: ManagedCluster, nginx) -> None:
        """Helper function to set default nginx ingress controller config for app routing
        :return: None
        """
        # web app routing object has been created
        if mc.ingress_profile and mc.ingress_profile.web_app_routing and mc.ingress_profile.web_app_routing.enabled:
            if mc.ingress_profile.web_app_routing.nginx is None:
                mc.ingress_profile.web_app_routing.nginx = self.models.ManagedClusterIngressProfileNginx()
            mc.ingress_profile.web_app_routing.nginx.default_ingress_controller_type = nginx
        else:
            raise CLIError('App Routing must be enabled to modify the default nginx ingress controller.\n')

    def update_node_resource_group_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update node resource group profile for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        nrg_lockdown_restriction_level = self.context.get_nrg_lockdown_restriction_level()
        if nrg_lockdown_restriction_level is not None:
            if mc.node_resource_group_profile is None:
                mc.node_resource_group_profile = (
                    self.models.ManagedClusterNodeResourceGroupProfile()  # pylint: disable=no-member
                )
            mc.node_resource_group_profile.restriction_level = nrg_lockdown_restriction_level
        return mc

    def _enable_keyvault_secret_provider_addon(self, mc: ManagedCluster) -> None:
        """Helper function to enable keyvault secret provider addon for the ManagedCluster object.

        :return: None
        """
        addon_consts = self.context.get_addon_consts()
        CONST_SECRET_ROTATION_ENABLED = addon_consts.get(
            "CONST_SECRET_ROTATION_ENABLED"
        )
        CONST_ROTATION_POLL_INTERVAL = addon_consts.get(
            "CONST_ROTATION_POLL_INTERVAL"
        )
        CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME = addon_consts.get(
            "CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME"
        )

        mc.addon_profiles = mc.addon_profiles or {}
        if not mc.addon_profiles.get(CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME):
            mc.addon_profiles[
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
            ] = self.models.ManagedClusterAddonProfile(  # pylint: disable=no-member
                enabled=True,
                config={
                    CONST_SECRET_ROTATION_ENABLED: "false",
                    CONST_ROTATION_POLL_INTERVAL: "2m",
                },
            )
        elif not mc.addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME].enabled:
            mc.addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME].enabled = True
            mc.addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME].config = {
                CONST_SECRET_ROTATION_ENABLED: "false",
                CONST_ROTATION_POLL_INTERVAL: "2m",
            }

    # pylint: disable=too-many-nested-blocks
    def _update_dns_zone_resource_ids(self, mc: ManagedCluster, dns_zone_resource_ids) -> None:
        """Helper function to update dns zone resource ids in app routing addon.

        :return: None
        """
        add_dns_zone = self.context.get_add_dns_zone()
        delete_dns_zone = self.context.get_delete_dns_zone()
        update_dns_zone = self.context.get_update_dns_zone()
        attach_zones = self.context.get_attach_zones()

        if mc.ingress_profile and mc.ingress_profile.web_app_routing and mc.ingress_profile.web_app_routing.enabled:
            if add_dns_zone:
                mc.ingress_profile.web_app_routing.dns_zone_resource_ids = (
                    mc.ingress_profile.web_app_routing.dns_zone_resource_ids or []
                )
                for dns_zone_id in dns_zone_resource_ids:
                    if dns_zone_id not in mc.ingress_profile.web_app_routing.dns_zone_resource_ids:
                        mc.ingress_profile.web_app_routing.dns_zone_resource_ids.append(dns_zone_id)
                        if attach_zones:
                            try:
                                is_private_dns_zone = (
                                    parse_resource_id(dns_zone_id).get("type").lower() == "privatednszones"
                                )
                                role = CONST_PRIVATE_DNS_ZONE_CONTRIBUTOR_ROLE if is_private_dns_zone else \
                                    CONST_DNS_ZONE_CONTRIBUTOR_ROLE
                                if not add_role_assignment(
                                    self.cmd,
                                    role,
                                    mc.ingress_profile.web_app_routing.identity.object_id,
                                    False,
                                    scope=dns_zone_id
                                ):
                                    logger.warning(
                                        'Could not create a role assignment for App Routing. '
                                        'Are you an Owner on this subscription?')
                            except Exception as ex:
                                raise CLIError('Error in granting dns zone permissions to managed identity.\n') from ex
            elif delete_dns_zone:
                if mc.ingress_profile.web_app_routing.dns_zone_resource_ids:
                    dns_zone_resource_ids = [
                        x
                        for x in mc.ingress_profile.web_app_routing.dns_zone_resource_ids
                        if x not in dns_zone_resource_ids
                    ]
                    mc.ingress_profile.web_app_routing.dns_zone_resource_ids = dns_zone_resource_ids
                else:
                    raise CLIError('No DNS zone is used by App Routing.\n')
            elif update_dns_zone:
                mc.ingress_profile.web_app_routing.dns_zone_resource_ids = dns_zone_resource_ids
                if attach_zones:
                    try:
                        for dns_zone in dns_zone_resource_ids:
                            is_private_dns_zone = parse_resource_id(dns_zone).get("type").lower() == "privatednszones"
                            role = CONST_PRIVATE_DNS_ZONE_CONTRIBUTOR_ROLE if is_private_dns_zone else \
                                CONST_DNS_ZONE_CONTRIBUTOR_ROLE
                            if not add_role_assignment(
                                self.cmd,
                                role,
                                mc.ingress_profile.web_app_routing.identity.object_id,
                                False,
                                scope=dns_zone,
                            ):
                                logger.warning(
                                    'Could not create a role assignment for App Routing. '
                                    'Are you an Owner on this subscription?')
                    except Exception as ex:
                        raise CLIError('Error in granting dns zone permisions to managed identity.\n') from ex
        else:
            raise CLIError('App Routing must be enabled to modify DNS zone resource IDs.\n')

    def update_identity_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update identity profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        assign_kubelet_identity = self.context.get_assign_kubelet_identity()
        if assign_kubelet_identity:
            identity_profile = {
                'kubeletidentity': self.models.UserAssignedIdentity(
                    resource_id=assign_kubelet_identity,
                )
            }
            user_assigned_identity = self.context.get_assign_identity()
            if not user_assigned_identity:
                user_assigned_identity = self.context.get_user_assignd_identity_from_mc()
            cluster_identity_object_id = self.context.get_user_assigned_identity_object_id(user_assigned_identity)
            # ensure the cluster identity has "Managed Identity Operator" role at the scope of kubelet identity
            self.context.external_functions.ensure_cluster_identity_permission_on_kubelet_identity(
                self.cmd,
                cluster_identity_object_id,
                assign_kubelet_identity)
            mc.identity_profile = identity_profile
        return mc

    def update_workload_auto_scaler_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update workload auto-scaler profile for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_enable_keda():
            if mc.workload_auto_scaler_profile is None:
                mc.workload_auto_scaler_profile = self.models.ManagedClusterWorkloadAutoScalerProfile()
            mc.workload_auto_scaler_profile.keda = self.models.ManagedClusterWorkloadAutoScalerProfileKeda(enabled=True)

        if self.context.get_disable_keda():
            if mc.workload_auto_scaler_profile is None:
                mc.workload_auto_scaler_profile = self.models.ManagedClusterWorkloadAutoScalerProfile()
            mc.workload_auto_scaler_profile.keda = self.models.ManagedClusterWorkloadAutoScalerProfileKeda(
                enabled=False
            )

        if self.context.get_enable_vpa():
            if mc.workload_auto_scaler_profile is None:
                mc.workload_auto_scaler_profile = self.models.ManagedClusterWorkloadAutoScalerProfile()
            if mc.workload_auto_scaler_profile.vertical_pod_autoscaler is None:
                mc.workload_auto_scaler_profile.vertical_pod_autoscaler = self.models.ManagedClusterWorkloadAutoScalerProfileVerticalPodAutoscaler()

            # set enabled
            mc.workload_auto_scaler_profile.vertical_pod_autoscaler.enabled = True

        if self.context.get_disable_vpa():
            if mc.workload_auto_scaler_profile is None:
                mc.workload_auto_scaler_profile = self.models.ManagedClusterWorkloadAutoScalerProfile()
            if mc.workload_auto_scaler_profile.vertical_pod_autoscaler is None:
                mc.workload_auto_scaler_profile.vertical_pod_autoscaler = self.models.ManagedClusterWorkloadAutoScalerProfileVerticalPodAutoscaler()

            # set disabled
            mc.workload_auto_scaler_profile.vertical_pod_autoscaler.enabled = False

        return mc

    def update_custom_ca_trust_certificates(self, mc: ManagedCluster) -> ManagedCluster:
        """Update Custom CA Trust Certificates for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # Check if the parameter was explicitly provided
        if self.context.raw_param.get("custom_ca_trust_certificates") is not None:
            ca_certs = self.context.get_custom_ca_trust_certificates()
            if mc.security_profile is None:
                mc.security_profile = self.models.ManagedClusterSecurityProfile()  # pylint: disable=no-member

            # Set certificates (this allows setting to empty list to remove certificates)
            mc.security_profile.custom_ca_trust_certificates = ca_certs

        return mc

    def update_run_command(self, mc: ManagedCluster) -> ManagedCluster:
        """Update run command for the ManagedCluster object.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        enable_run_command = self.context.get_enable_run_command()
        disable_run_command = self.context.get_disable_run_command()
        if enable_run_command or disable_run_command:
            if mc.api_server_access_profile is None:
                mc.api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile(
                    disable_run_command=(
                        not enable_run_command
                        if enable_run_command or disable_run_command
                        else None
                    )
                )
            else:
                mc.api_server_access_profile.disable_run_command = (
                    not enable_run_command
                    if enable_run_command or disable_run_command
                    else None
                )

        return mc

    def update_azure_monitor_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Update azure monitor profile for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        # read the original value passed by the command
        ksm_metric_labels_allow_list = self.context.raw_param.get("ksm_metric_labels_allow_list")
        ksm_metric_annotations_allow_list = self.context.raw_param.get("ksm_metric_annotations_allow_list")

        if ksm_metric_labels_allow_list is None:
            ksm_metric_labels_allow_list = ""
        if ksm_metric_annotations_allow_list is None:
            ksm_metric_annotations_allow_list = ""

        if self.context.get_enable_azure_monitor_metrics():
            if mc.azure_monitor_profile is None:
                mc.azure_monitor_profile = self.models.ManagedClusterAzureMonitorProfile()
            mc.azure_monitor_profile.metrics = self.models.ManagedClusterAzureMonitorProfileMetrics(enabled=True)
            mc.azure_monitor_profile.metrics.kube_state_metrics = self.models.ManagedClusterAzureMonitorProfileKubeStateMetrics(  # pylint:disable=line-too-long
                metric_labels_allowlist=str(ksm_metric_labels_allow_list),
                metric_annotations_allow_list=str(ksm_metric_annotations_allow_list))

        if self.context.get_disable_azure_monitor_metrics():
            if mc.azure_monitor_profile is None:
                mc.azure_monitor_profile = self.models.ManagedClusterAzureMonitorProfile()
            mc.azure_monitor_profile.metrics = self.models.ManagedClusterAzureMonitorProfileMetrics(enabled=False)

        if (
            self.context.raw_param.get("enable_azure_monitor_metrics") or
            self.context.raw_param.get("disable_azure_monitor_metrics")
        ):
            self.context.external_functions.ensure_azure_monitor_profile_prerequisites(
                self.cmd,
                self.context.get_subscription_id(),
                self.context.get_resource_group_name(),
                self.context.get_name(),
                self.context.get_location(),
                self.__raw_parameters,
                self.context.get_disable_azure_monitor_metrics(),
                False)

        return mc

    # pylint: disable=too-many-statements,too-many-locals
    def update_azure_container_storage(self, mc: ManagedCluster) -> ManagedCluster:
        """Update azure container storage for the Managed Cluster object
        :return: ManagedCluster
        """
        self._ensure_mc(mc)

        # check if we are trying to enable container storage v1
        enable_azure_container_storage_param = self.context.raw_param.get("enable_azure_container_storage")
        disable_azure_container_storage_param = self.context.raw_param.get("disable_azure_container_storage")
        container_storage_version = self.context.raw_param.get("container_storage_version")

        if disable_azure_container_storage_param is not None and container_storage_version is not None:
            raise InvalidArgumentValueError(
                'The --container-storage-version parameter is not required when disabling Azure Container Storage.'
                ' Please remove this parameter and try again.'
            )

        if enable_azure_container_storage_param is not None or disable_azure_container_storage_param is not None:
            self.context.set_intermediate("container_storage_version", container_storage_version, overwrite_exists=True)

            enable_azure_container_storage_v1 = enable_azure_container_storage_param is not None and container_storage_version == CONST_ACSTOR_VERSION_V1

            # Check if we are trying to disable container storage v1
            from azure.cli.command_modules.acs.azurecontainerstorage._helpers import get_container_storage_extension_installed
            try:
                is_container_storage_v1_extension_installed, _ = get_container_storage_extension_installed(
                    self.cmd,
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
                )
            except Exception as ex:
                raise UnknownError(
                    f"An error occurred while checking the version of Azure Container Storage"
                    f" extension installed on the cluster: {str(ex)}"
                ) from ex

            disable_azure_container_storage_v1 = disable_azure_container_storage_param is not None and is_container_storage_v1_extension_installed
            # pylint: disable=too-many-nested-blocks
            if enable_azure_container_storage_v1 or disable_azure_container_storage_v1:

                # read the azure container storage values passed
                enable_pool_type = self.context.raw_param.get("enable_azure_container_storage")
                disable_pool_type = self.context.raw_param.get("disable_azure_container_storage")
                enable_azure_container_storage = enable_pool_type is not None
                disable_azure_container_storage = disable_pool_type is not None
                nodepool_list = self.context.raw_param.get("azure_container_storage_nodepools")
                ephemeral_disk_volume_type = self.context.raw_param.get("ephemeral_disk_volume_type")
                ephemeral_disk_nvme_perf_tier = self.context.raw_param.get("ephemeral_disk_nvme_perf_tier")
                if enable_azure_container_storage and disable_azure_container_storage:
                    raise MutuallyExclusiveArgumentError(
                        'Conflicting flags. Cannot set --enable-azure-container-storage '
                        'and --disable-azure-container-storage together.'
                    )

                if (ephemeral_disk_volume_type is not None or ephemeral_disk_nvme_perf_tier is not None) and \
                        not enable_azure_container_storage:
                    params_defined_arr = []
                    if ephemeral_disk_volume_type is not None:
                        params_defined_arr.append('--ephemeral-disk-volume-type')
                    if ephemeral_disk_nvme_perf_tier is not None:
                        params_defined_arr.append('--ephemeral-disk-nvme-perf-tier')

                    params_defined = 'and '.join(params_defined_arr)
                    raise RequiredArgumentMissingError(
                        f'Cannot set {params_defined} without the parameter --enable-azure-container-storage.'
                    )

                # Require the agent pool profiles for azure container storage
                # operations. Raise exception if not found.
                if not mc.agent_pool_profiles:
                    raise UnknownError(
                        "Encounter an unexpected error while getting agent pool profiles from the cluster "
                        "in the process of updating agentpool profile."
                    )
                storagepool_name = self.context.raw_param.get("storage_pool_name")
                pool_option = self.context.raw_param.get("storage_pool_option")
                pool_sku = self.context.raw_param.get("storage_pool_sku")
                pool_size = self.context.raw_param.get("storage_pool_size")
                agentpool_details = {}
                from azure.cli.command_modules.acs.azurecontainerstorage._helpers import get_extension_installed_and_cluster_configs_v1
                (
                    is_extension_installed,
                    is_azureDisk_enabled,
                    is_elasticSan_enabled,
                    is_ephemeralDisk_localssd_enabled,
                    is_ephemeralDisk_nvme_enabled,
                    current_core_value,
                    existing_ephemeral_disk_volume_type,
                    existing_perf_tier,
                ) = get_extension_installed_and_cluster_configs_v1(
                    self.cmd,
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    mc.agent_pool_profiles,
                )

                from azure.cli.command_modules.acs.azurecontainerstorage._helpers import generate_vm_sku_cache_for_region
                generate_vm_sku_cache_for_region(self.cmd.cli_ctx, self.context.get_location())

                if enable_azure_container_storage:
                    from azure.cli.command_modules.acs.azurecontainerstorage._helpers import get_container_storage_extension_installed
                    try:
                        is_container_storage_v2_extension_installed, version_v2 = get_container_storage_extension_installed(
                            self.cmd,
                            self.context.get_resource_group_name(),
                            self.context.get_name(),
                            CONST_ACSTOR_EXT_INSTALLATION_NAME,
                        )
                    except Exception as ex:
                        raise UnknownError(
                            f"An error occurred while checking if Azure Container Storage"
                            f"extension is installed on the cluster: {str(ex)}"
                        ) from ex

                    from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
                        CONST_ACSTOR_IO_ENGINE_LABEL_KEY,
                        CONST_ACSTOR_IO_ENGINE_LABEL_VAL
                    )
                    labelled_nodepool_arr = []
                    for agentpool in mc.agent_pool_profiles:
                        pool_details = {}
                        nodepool_name = agentpool.name
                        pool_details["vm_size"] = agentpool.vm_size
                        pool_details["count"] = agentpool.count
                        pool_details["os_type"] = agentpool.os_type
                        pool_details["mode"] = agentpool.mode
                        pool_details["node_taints"] = agentpool.node_taints
                        pool_details["zoned"] = agentpool.availability_zones is not None
                        if agentpool.node_labels is not None:
                            node_labels = agentpool.node_labels
                            if node_labels is not None and \
                                    node_labels.get(CONST_ACSTOR_IO_ENGINE_LABEL_KEY) is not None and \
                                    nodepool_name is not None:
                                labelled_nodepool_arr.append(nodepool_name)
                            pool_details["node_labels"] = node_labels
                        agentpool_details[nodepool_name] = pool_details

                    # Incase of a new installation, if the nodepool list is not defined
                    # then check for all the nodepools which are marked with acstor io-engine
                    # labels and include them for installation. If none of the nodepools are
                    # labelled, either pick nodepool1 as default, or if only
                    # one nodepool exists, choose the only nodepool by default.
                    if not is_extension_installed:
                        if nodepool_list is None:
                            nodepool_list = ""
                            if len(labelled_nodepool_arr) > 0:
                                nodepool_list = ','.join(labelled_nodepool_arr)
                            elif len(agentpool_details) == 1:
                                nodepool_list = ','.join(agentpool_details.keys())

                    from azure.cli.command_modules.acs.azurecontainerstorage._validators import (
                        validate_enable_azure_container_storage_v1_params
                    )
                    validate_enable_azure_container_storage_v1_params(
                        enable_pool_type,
                        storagepool_name,
                        pool_sku,
                        pool_option,
                        pool_size,
                        nodepool_list,
                        agentpool_details,
                        is_extension_installed,
                        is_container_storage_v2_extension_installed,
                        version_v2,
                        is_azureDisk_enabled,
                        is_elasticSan_enabled,
                        is_ephemeralDisk_localssd_enabled,
                        is_ephemeralDisk_nvme_enabled,
                        ephemeral_disk_volume_type,
                        ephemeral_disk_nvme_perf_tier,
                        existing_ephemeral_disk_volume_type,
                        existing_perf_tier,
                    )

                    if is_ephemeralDisk_nvme_enabled and ephemeral_disk_nvme_perf_tier is not None:
                        msg = (
                            "Changing ephemeralDisk NVMe performance tier may result in a temporary "
                            "interruption to the applications using Azure Container Storage. Do you "
                            "want to continue with this operation?"
                        )
                        if not (self.context.get_yes() or prompt_y_n(msg, default="n")):
                            raise DecoratorEarlyExitException()
                    # If the extension is already installed,
                    # we expect that the Azure Container Storage
                    # nodes are already labelled. Use those label
                    # to generate the nodepool_list.
                    if is_extension_installed:
                        nodepool_list = ','.join(labelled_nodepool_arr)
                    else:
                        # Set Azure Container Storage labels on the required nodepools.
                        nodepool_list_arr = nodepool_list.split(',')
                        for agentpool in mc.agent_pool_profiles:
                            labels = agentpool.node_labels
                            if agentpool.name in nodepool_list_arr:
                                if labels is None:
                                    labels = {}
                                labels[CONST_ACSTOR_IO_ENGINE_LABEL_KEY] = CONST_ACSTOR_IO_ENGINE_LABEL_VAL
                            else:
                                # Remove residual Azure Container Storage labels
                                # from any other nodepools where its not intended
                                if labels is not None:
                                    labels.pop(CONST_ACSTOR_IO_ENGINE_LABEL_KEY, None)
                            agentpool.node_labels = labels

                    # set intermediates
                    self.context.set_intermediate("azure_container_storage_nodepools", nodepool_list, overwrite_exists=True)
                    self.context.set_intermediate("enable_azure_container_storage", True, overwrite_exists=True)

                if disable_azure_container_storage:
                    from azure.cli.command_modules.acs.azurecontainerstorage._validators import (
                        validate_disable_azure_container_storage_params_v1
                    )
                    validate_disable_azure_container_storage_params_v1(
                        disable_pool_type,
                        storagepool_name,
                        pool_sku,
                        pool_option,
                        pool_size,
                        nodepool_list,
                        is_extension_installed,
                        is_azureDisk_enabled,
                        is_elasticSan_enabled,
                        is_ephemeralDisk_localssd_enabled,
                        is_ephemeralDisk_nvme_enabled,
                        ephemeral_disk_volume_type,
                        ephemeral_disk_nvme_perf_tier,
                    )
                    pre_disable_validate = False

                    msg = (
                        "Disabling Azure Container Storage will forcefully delete all the storage pools in the cluster and "
                        "affect the applications using these storage pools. Forceful deletion of storage pools can also "
                        "lead to leaking of storage resources which are being consumed. Do you want to validate whether "
                        "any of the storage pools are being used before disabling Azure Container Storage?"
                    )

                    from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
                        CONST_ACSTOR_ALL,
                    )
                    if disable_pool_type != CONST_ACSTOR_ALL:
                        msg = (
                            f"Disabling Azure Container Storage for storage pool type {disable_pool_type} "
                            "will forcefully delete all the storage pools of the same type and affect the "
                            "applications using these storage pools. Forceful deletion of storage pools can "
                            "also lead to leaking of storage resources which are being consumed. Do you want to "
                            f"validate whether any of the storage pools of type {disable_pool_type} are being used "
                            "before disabling Azure Container Storage?"
                        )
                    if self.context.get_yes() or prompt_y_n(msg, default="y"):
                        pre_disable_validate = True

                    # set intermediate
                    self.context.set_intermediate("disable_azure_container_storage", True, overwrite_exists=True)
                    self.context.set_intermediate("container_storage_version", CONST_ACSTOR_VERSION_V1, overwrite_exists=True)
                    self.context.set_intermediate(
                        "pre_disable_validate_azure_container_storage",
                        pre_disable_validate,
                        overwrite_exists=True
                    )

                # Set intermediates
                self.context.set_intermediate("is_extension_installed", is_extension_installed, overwrite_exists=True)
                self.context.set_intermediate("is_azureDisk_enabled", is_azureDisk_enabled, overwrite_exists=True)
                self.context.set_intermediate("is_elasticSan_enabled", is_elasticSan_enabled, overwrite_exists=True)
                self.context.set_intermediate("current_core_value", current_core_value, overwrite_exists=True)
                self.context.set_intermediate(
                    "current_ephemeral_nvme_perf_tier",
                    existing_perf_tier,
                    overwrite_exists=True
                )
                self.context.set_intermediate(
                    "existing_ephemeral_disk_volume_type",
                    existing_ephemeral_disk_volume_type,
                    overwrite_exists=True
                )
                self.context.set_intermediate(
                    "is_ephemeralDisk_nvme_enabled",
                    is_ephemeralDisk_nvme_enabled,
                    overwrite_exists=True
                )
                self.context.set_intermediate(
                    "is_ephemeralDisk_localssd_enabled",
                    is_ephemeralDisk_localssd_enabled,
                    overwrite_exists=True
                )
                self.context.set_intermediate("current_core_value", current_core_value, overwrite_exists=True)

            else:
                storage_pool_name = self.context.raw_param.get("storage_pool_name")
                pool_sku = self.context.raw_param.get("storage_pool_sku")
                pool_option = self.context.raw_param.get("storage_pool_option")
                pool_size = self.context.raw_param.get("storage_pool_size")

                if enable_azure_container_storage_param and disable_azure_container_storage_param:
                    raise MutuallyExclusiveArgumentError(
                        'Conflicting flags. Cannot set --enable-azure-container-storage '
                        'and --disable-azure-container-storage together.'
                    )

                from azure.cli.command_modules.acs.azurecontainerstorage._helpers import get_extension_installed_and_cluster_configs
                is_extension_installed, is_ephemeralDisk_enabled, is_elasticSan_enabled = get_extension_installed_and_cluster_configs(
                    self.cmd,
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                )

                from azure.cli.command_modules.acs.azurecontainerstorage._helpers import get_container_storage_extension_installed
                try:
                    is_containerstorage_v1_installed, v1_extension_version = get_container_storage_extension_installed(
                        self.cmd,
                        self.context.get_resource_group_name(),
                        self.context.get_name(),
                        CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
                    )
                except Exception as ex:
                    raise UnknownError(
                        f"An error occurred while checking if Azure Container Storage "
                        f"extension is installed on the cluster: {str(ex)}"
                    ) from ex

                if enable_azure_container_storage_param:
                    from azure.cli.command_modules.acs.azurecontainerstorage._validators import (
                        validate_enable_azure_container_storage_params,
                    )
                    validate_enable_azure_container_storage_params(
                        enable_azure_container_storage_param,
                        is_extension_installed,
                        is_ephemeralDisk_enabled,
                        is_elasticSan_enabled,
                        is_containerstorage_v1_installed,
                        v1_extension_version,
                        storage_pool_name,
                        pool_sku,
                        pool_option,
                        pool_size,
                    )

                if disable_azure_container_storage_param:
                    msg = (
                        "Please make sure there are no existing PVs and PVCs that are provisioned by Azure Container Storage "
                        "before disabling. If Azure Container Storage is disabled with remaining PVs and PVCs, "
                        "any data associated with those PVs and PVCs will not be erased and the nodes will be left in an unclean state. "
                        "The PVs and PVCs can only be cleaned up after re-enabling it by running 'az aks update --enable-azure-container-storage'. "
                        "Would you like to proceed with the disabling?"
                    )
                    from azure.cli.command_modules.acs.azurecontainerstorage._helpers import should_delete_extension
                    if not should_delete_extension(disable_azure_container_storage_param):
                        storage_option_display = storage_option_param_str = disable_azure_container_storage_param
                        if isinstance(disable_azure_container_storage_param, list):
                            storage_options = disable_azure_container_storage_param
                            storage_option_param_str = " ".join(storage_options)
                            if len(storage_options) > 2:
                                storage_options = [storage_options[:-1].join("', '"), storage_options[-1]]
                            storage_option_display = "' and '".join(storage_options)
                        msg = (
                            "Please make sure there are no existing PVs and PVCs that are provisioned by Azure Container Storage "
                            f"for '{storage_option_display}' before disabling. If storage options are disabled "
                            "with remaining PVs and PVCs, any data associated with those PVs and PVCs will not be erased "
                            "and the nodes will be left in an unclean state. The PVs and PVCs can only be cleaned up "
                            f"after re-enabling it by running 'az aks update --enable-azure-container-storage {storage_option_param_str}'. "
                            "Would you like to proceed with the disabling?"
                        )
                    if not self.context.get_yes() and not prompt_y_n(msg, default="n"):
                        raise DecoratorEarlyExitException()

                    from azure.cli.command_modules.acs.azurecontainerstorage._validators import (
                        validate_disable_azure_container_storage_params
                    )
                    validate_disable_azure_container_storage_params(
                        disable_azure_container_storage_param,
                        is_extension_installed,
                        is_ephemeralDisk_enabled,
                        is_elasticSan_enabled,
                        storage_pool_name,
                        pool_sku,
                        pool_option,
                        pool_size
                    )

                self.context.set_intermediate("enable_azure_container_storage", enable_azure_container_storage_param, overwrite_exists=True)
                self.context.set_intermediate("disable_azure_container_storage", disable_azure_container_storage_param, overwrite_exists=True)
                self.context.set_intermediate("is_extension_installed", is_extension_installed, overwrite_exists=True)

        return mc

    def update_ai_toolchain_operator(self, mc: ManagedCluster) -> ManagedCluster:
        """Updates the aiToolchainOperatorProfile field of the managed cluster
        :return: the ManagedCluster object
        """

        if self.context.get_ai_toolchain_operator(enable_validation=True):
            if mc.ai_toolchain_operator_profile is None:
                mc.ai_toolchain_operator_profile = self.models.ManagedClusterAIToolchainOperatorProfile()  # pylint: disable=no-member
            mc.ai_toolchain_operator_profile.enabled = True

        if self.context.get_disable_ai_toolchain_operator():
            if mc.ai_toolchain_operator_profile is None:
                mc.ai_toolchain_operator_profile = self.models.ManagedClusterAIToolchainOperatorProfile()  # pylint: disable=no-member
            mc.ai_toolchain_operator_profile.enabled = False

        return mc

    def update_cost_analysis(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        if self.context.get_enable_cost_analysis():
            if mc.metrics_profile is None:
                mc.metrics_profile = self.models.ManagedClusterMetricsProfile()
            if mc.metrics_profile.cost_analysis is None:
                mc.metrics_profile.cost_analysis = self.models.ManagedClusterCostAnalysis()

            # set enabled
            mc.metrics_profile.cost_analysis.enabled = True

        if self.context.get_disable_cost_analysis():
            if mc.metrics_profile is None:
                mc.metrics_profile = self.models.ManagedClusterMetricsProfile()
            if mc.metrics_profile.cost_analysis is None:
                mc.metrics_profile.cost_analysis = self.models.ManagedClusterCostAnalysis()

            # set disabled
            mc.metrics_profile.cost_analysis.enabled = False

        return mc

    def update_metrics_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Updates the metricsProfile field of the managed cluster
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc = self.update_cost_analysis(mc)

        return mc

    def update_bootstrap_profile(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        bootstrap_artifact_source = self.context.get_bootstrap_artifact_source()
        bootstrap_container_registry_resource_id = self.context.get_bootstrap_container_registry_resource_id()
        if hasattr(mc, "bootstrap_profile") and bootstrap_artifact_source is not None:
            if bootstrap_artifact_source != CONST_ARTIFACT_SOURCE_CACHE and bootstrap_container_registry_resource_id:
                raise MutuallyExclusiveArgumentError(
                    "Cannot specify --bootstrap-container-registry-resource-id when "
                    "--bootstrap-artifact-source is not Cache."
                )
            if mc.bootstrap_profile is None:
                mc.bootstrap_profile = self.models.ManagedClusterBootstrapProfile()  # pylint: disable=no-member
            mc.bootstrap_profile.artifact_source = bootstrap_artifact_source
            mc.bootstrap_profile.container_registry_id = bootstrap_container_registry_resource_id

        return mc

    def update_static_egress_gateway(self, mc: ManagedCluster) -> ManagedCluster:
        """Update static egress gateway addon for the ManagedCluster object.
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_enable_static_egress_gateway():
            if not mc.network_profile:
                raise UnknownError(
                    "Unexpectedly get an empty network profile in the process of updating static-egress-gateway config."
                )
            if mc.network_profile.static_egress_gateway_profile is None:
                mc.network_profile.static_egress_gateway_profile = (
                    self.models.ManagedClusterStaticEgressGatewayProfile()  # pylint: disable=no-member
                )
            mc.network_profile.static_egress_gateway_profile.enabled = True

        if self.context.get_disable_static_egress_gateway():
            if not mc.network_profile:
                raise UnknownError(
                    "Unexpectedly get an empty network profile in the process of updating static-egress-gateway config."
                )
            if mc.network_profile.static_egress_gateway_profile is None:
                mc.network_profile.static_egress_gateway_profile = (
                    self.models.ManagedClusterStaticEgressGatewayProfile()  # pylint: disable=no-member
                )
            mc.network_profile.static_egress_gateway_profile.enabled = False
        return mc

    def update_vmas_to_vms(self, mc: ManagedCluster) -> ManagedCluster:
        """Update the agent pool profile type from VMAS to VMS and LB sku to standard
        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        if self.context.get_migrate_vmas_to_vms():
            msg = (
                "\nWARNING: This operation will be disruptive to your workload while underway. "
                "Do you wish to continue?"
            )
            if not self.context.get_yes() and not prompt_y_n(msg, default="n"):
                raise DecoratorEarlyExitException()
            # Ensure we have valid vmas AP
            if len(mc.agent_pool_profiles) == 1 and mc.agent_pool_profiles[0].type == CONST_AVAILABILITY_SET:
                mc.agent_pool_profiles[0].type = CONST_VIRTUAL_MACHINES
            else:
                raise ArgumentUsageError('This is not a valid VMAS cluster with {} agent pool profiles and {} agent pool type, we cannot proceed with the migration.'.format(len(mc.agent_pool_profiles), mc.agent_pool_profiles[0].type))

            if mc.network_profile.load_balancer_sku == CONST_LOAD_BALANCER_SKU_BASIC:
                mc.network_profile.load_balancer_sku = CONST_LOAD_BALANCER_SKU_STANDARD

            # Set agent pool profile count and vm_size to None
            mc.agent_pool_profiles[0].count = None
            mc.agent_pool_profiles[0].vm_size = None

        return mc

    def update_node_provisioning_mode(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        mode = self.context.get_node_provisioning_mode()
        if mode is not None:
            if mc.node_provisioning_profile is None:
                mc.node_provisioning_profile = (
                    self.models.ManagedClusterNodeProvisioningProfile()  # pylint: disable=no-member
                )

            # set mode
            mc.node_provisioning_profile.mode = mode

        return mc

    def update_node_provisioning_default_pools(self, mc: ManagedCluster) -> ManagedCluster:
        self._ensure_mc(mc)

        default_pools = self.context.get_node_provisioning_default_pools()
        if default_pools is not None:
            if mc.node_provisioning_profile is None:
                mc.node_provisioning_profile = (
                    self.models.ManagedClusterNodeProvisioningProfile()  # pylint: disable=no-member
                )

            # set default_node_pools
            mc.node_provisioning_profile.default_node_pools = default_pools

        return mc

    def update_node_provisioning_profile(self, mc: ManagedCluster) -> ManagedCluster:
        """Updates the nodeProvisioningProfile field of the managed cluster

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        mc = self.update_node_provisioning_mode(mc)
        mc = self.update_node_provisioning_default_pools(mc)

        return mc

    def update_mc_profile_default(self) -> ManagedCluster:
        """The overall controller used to update the default ManagedCluster profile.

        The completely updated ManagedCluster object will later be passed as a parameter to the underlying SDK
        (mgmt-containerservice) to send the actual request.

        :return: the ManagedCluster object
        """
        # check raw parameters
        # promt y/n if no options are specified to ask user whether to perform a reconcile operation
        self.check_raw_parameters()
        # fetch the ManagedCluster object
        mc = self.fetch_mc()
        # update agentpool profile by the agentpool decorator
        mc = self.update_agentpool_profile(mc)
        # update auto scaler profile
        mc = self.update_auto_scaler_profile(mc)
        # update tags
        mc = self.update_tags(mc)
        # attach or detach acr (add or delete role assignment for acr)
        self.process_attach_detach_acr(mc)
        # update sku (uptime sla)
        mc = self.update_sku(mc)
        # update outbound type
        mc = self.update_outbound_type_in_network_profile(mc)
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
        # update network plugin settings
        mc = self.update_network_plugin_settings(mc)
        # update network profile settings
        mc = self.update_network_profile(mc)
        # update network profile with acns
        mc = self.update_network_profile_advanced_networking(mc)
        # update aad profile
        mc = self.update_aad_profile(mc)
        # update oidc issuer profile
        mc = self.update_oidc_issuer_profile(mc)
        # update auto upgrade profile
        mc = self.update_auto_upgrade_profile(mc)
        # update custom ca trust certificates
        mc = self.update_custom_ca_trust_certificates(mc)
        # update run command
        mc = self.update_run_command(mc)
        # update identity
        mc = self.update_identity(mc)
        # update addon profiles
        mc = self.update_addon_profiles(mc)
        # update defender
        mc = self.update_defender(mc)
        # update workload identity profile
        mc = self.update_workload_identity_profile(mc)
        # update stroage profile
        mc = self.update_storage_profile(mc)
        # update azure keyvalut kms
        mc = self.update_azure_keyvault_kms(mc)
        # update image cleaner
        mc = self.update_image_cleaner(mc)
        # update identity
        mc = self.update_identity_profile(mc)
        # set up http proxy config
        mc = self.update_http_proxy_config(mc)
        # update workload autoscaler profile
        mc = self.update_workload_auto_scaler_profile(mc)
        # update kubernetes support plan
        mc = self.update_k8s_support_plan(mc)
        # update azure monitor metrics profile
        mc = self.update_azure_monitor_profile(mc)
        # update azure container storage
        mc = self.update_azure_container_storage(mc)
        # update cluster upgrade settings
        mc = self.update_upgrade_settings(mc)
        # update metrics profile
        mc = self.update_metrics_profile(mc)
        # update node resource group profile
        mc = self.update_node_resource_group_profile(mc)
        # update AI toolchain operator
        mc = self.update_ai_toolchain_operator(mc)
        # update bootstrap profile
        mc = self.update_bootstrap_profile(mc)
        # update static egress gateway
        mc = self.update_static_egress_gateway(mc)
        # update kubernetes version and orchestrator version
        mc = self.update_kubernetes_version_and_orchestrator_version(mc)
        # update VMAS to VMS
        mc = self.update_vmas_to_vms(mc)
        # update node provisioning profile
        mc = self.update_node_provisioning_profile(mc)
        return mc

    def update_kubernetes_version_and_orchestrator_version(self, mc: ManagedCluster) -> ManagedCluster:
        """Update kubernetes version and orchestrator version for the ManagedCluster object.

        :param mc: The ManagedCluster object to be updated.
        :return: The updated ManagedCluster object.
        """
        self._ensure_mc(mc)

        # Check if auto_upgrade_channel is set to "none"
        auto_upgrade_channel = self.context.get_auto_upgrade_channel()
        if auto_upgrade_channel == CONST_NONE_UPGRADE_CHANNEL:
            warning_message = (
                "Since auto-upgrade-channel is set to none, cluster kubernetesVersion will be set to the value of "
                "currentKubernetesVersion, all agent pools orchestratorVersion will be set to the value of "
                "currentOrchestratorVersion respectively. Continue?"
            )
            if not self.context.get_yes() and not prompt_y_n(warning_message, default="n"):
                raise DecoratorEarlyExitException()

            # Set kubernetes version to match the current kubernetes version if it has a value
            if mc.current_kubernetes_version:
                mc.kubernetes_version = mc.current_kubernetes_version

            # Set orchestrator version for each agent pool to match the current orchestrator version if it has a value
            for agent_pool in mc.agent_pool_profiles:
                if agent_pool.current_orchestrator_version:
                    agent_pool.orchestrator_version = agent_pool.current_orchestrator_version

        return mc

    def check_is_postprocessing_required(self, mc: ManagedCluster) -> bool:
        """Helper function to check if postprocessing is required after sending a PUT request to create the cluster.

        :return: bool
        """
        from azure.cli.command_modules.acs._consts import CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
        # some addons require post cluster creation role assigment
        monitoring_addon_enabled = self.context.get_intermediate("monitoring_addon_enabled", default_value=False)
        ingress_appgw_addon_enabled = self.context.get_intermediate("ingress_appgw_addon_enabled", default_value=False)
        virtual_node_addon_enabled = self.context.get_intermediate("virtual_node_addon_enabled", default_value=False)
        enable_managed_identity = check_is_msi_cluster(mc)
        attach_acr = self.context.get_attach_acr()
        keyvault_id = self.context.get_keyvault_id()
        enable_azure_keyvault_secrets_provider_addon = self.context.get_enable_kv() or (
            mc.addon_profiles and mc.addon_profiles.get(CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME) and
            mc.addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME].enabled)
        enable_azure_container_storage = self.context.get_intermediate(
            "enable_azure_container_storage", default_value=False
        )
        disable_azure_container_storage = self.context.get_intermediate(
            "disable_azure_container_storage", default_value=False
        )
        # pylint: disable=too-many-boolean-expressions
        if (
            monitoring_addon_enabled or
            ingress_appgw_addon_enabled or
            virtual_node_addon_enabled or
            (enable_managed_identity and attach_acr) or
            (keyvault_id and enable_azure_keyvault_secrets_provider_addon) or
            (enable_azure_container_storage or disable_azure_container_storage)
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

    # pylint: disable=too-many-locals
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
                    from azure.mgmt.core.tools import resource_id

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
            elif (
                self.context.raw_param.get("enable_addons") is not None
            ):
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
                    enable_syslog=self.context.get_enable_syslog(),
                    data_collection_settings=self.context.get_data_collection_settings(),
                    is_private_cluster=self.context.get_enable_private_cluster(),
                    ampls_resource_id=self.context.get_ampls_resource_id(),
                    enable_high_log_scale_mode=self.context.get_enable_high_log_scale_mode(),
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
                    assignee_principal_type=self.context.get_assignee_principal_type()
                )

        enable_azure_container_storage = self.context.get_intermediate("enable_azure_container_storage")
        disable_azure_container_storage = self.context.get_intermediate("disable_azure_container_storage")
        container_storage_version = self.context.get_intermediate("container_storage_version")

        is_extension_installed = self.context.get_intermediate("is_extension_installed")
        is_azureDisk_enabled = self.context.get_intermediate("is_azureDisk_enabled")
        is_elasticSan_enabled = self.context.get_intermediate("is_elasticSan_enabled")
        is_ephemeralDisk_localssd_enabled = self.context.get_intermediate("is_ephemeralDisk_localssd_enabled")
        is_ephemeralDisk_nvme_enabled = self.context.get_intermediate("is_ephemeralDisk_nvme_enabled")
        current_core_value = self.context.get_intermediate("current_core_value")
        existing_ephemeral_disk_volume_type = self.context.get_intermediate("existing_ephemeral_disk_volume_type")
        existing_ephemeral_nvme_perf_tier = self.context.get_intermediate("current_ephemeral_nvme_perf_tier")
        pool_option = self.context.raw_param.get("storage_pool_option")

        # enable azure container storage
        if enable_azure_container_storage:
            if container_storage_version is not None and container_storage_version == CONST_ACSTOR_VERSION_V1:
                if cluster.identity_profile is None or cluster.identity_profile["kubeletidentity"] is None:
                    logger.warning(
                        "Unexpected error getting kubelet's identity for the cluster."
                        "Unable to perform azure container storage operation."
                    )
                    return

                pool_name = self.context.raw_param.get("storage_pool_name")
                pool_type = self.context.raw_param.get("enable_azure_container_storage")
                pool_sku = self.context.raw_param.get("storage_pool_sku")
                pool_size = self.context.raw_param.get("storage_pool_size")
                nodepool_list = self.context.get_intermediate("azure_container_storage_nodepools")
                ephemeral_disk_volume_type = self.context.raw_param.get("ephemeral_disk_volume_type")
                ephemeral_disk_nvme_perf_tier = self.context.raw_param.get("ephemeral_disk_nvme_perf_tier")
                kubelet_identity_object_id = cluster.identity_profile["kubeletidentity"].object_id
                acstor_nodepool_skus = []
                for agentpool_profile in cluster.agent_pool_profiles:
                    if agentpool_profile.name in nodepool_list:
                        acstor_nodepool_skus.append(agentpool_profile.vm_size)

                self.context.external_functions.perform_enable_azure_container_storage_v1(
                    self.cmd,
                    self.context.get_subscription_id(),
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    self.context.get_node_resource_group(),
                    kubelet_identity_object_id,
                    pool_name,
                    pool_type,
                    pool_size,
                    pool_sku,
                    pool_option,
                    acstor_nodepool_skus,
                    ephemeral_disk_volume_type,
                    ephemeral_disk_nvme_perf_tier,
                    False,
                    existing_ephemeral_disk_volume_type,
                    existing_ephemeral_nvme_perf_tier,
                    is_extension_installed,
                    is_azureDisk_enabled,
                    is_elasticSan_enabled,
                    is_ephemeralDisk_localssd_enabled,
                    is_ephemeralDisk_nvme_enabled,
                    current_core_value,
                )
            else:
                self.context.external_functions.perform_azure_container_storage_update(
                    self.cmd,
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    enable_azure_container_storage,
                    is_extension_installed,
                )

        # disable azure container storage
        if disable_azure_container_storage:
            if container_storage_version is not None:
                if container_storage_version == CONST_ACSTOR_VERSION_V1:
                    pool_type = self.context.raw_param.get("disable_azure_container_storage")
                    kubelet_identity_object_id = cluster.identity_profile["kubeletidentity"].object_id
                    pre_disable_validate = self.context.get_intermediate("pre_disable_validate_azure_container_storage")
                    self.context.external_functions.perform_disable_azure_container_storage_v1(
                        self.cmd,
                        self.context.get_subscription_id(),
                        self.context.get_resource_group_name(),
                        self.context.get_name(),
                        self.context.get_node_resource_group(),
                        kubelet_identity_object_id,
                        pre_disable_validate,
                        pool_type,
                        pool_option,
                        is_elasticSan_enabled,
                        is_azureDisk_enabled,
                        is_ephemeralDisk_localssd_enabled,
                        is_ephemeralDisk_nvme_enabled,
                        current_core_value,
                        existing_ephemeral_disk_volume_type,
                        existing_ephemeral_nvme_perf_tier,
                    )

            else:
                self.context.external_functions.perform_azure_container_storage_update(
                    self.cmd,
                    self.context.get_resource_group_name(),
                    self.context.get_name(),
                    None,
                    is_extension_installed,
                    disable_azure_container_storage,
                )

        # attach keyvault to app routing addon
        from azure.cli.command_modules.keyvault.custom import set_policy
        from azure.cli.command_modules.acs._client_factory import get_keyvault_client
        from azure.cli.command_modules.acs._consts import CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
        keyvault_id = self.context.get_keyvault_id()
        enable_azure_keyvault_secrets_provider_addon = (
            self.context.get_enable_kv() or
            (cluster.addon_profiles and
             cluster.addon_profiles.get(CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME) and
             cluster.addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME].enabled)
        )
        logger.warning("keyvaultid: %s, enable_kv: %s", keyvault_id, enable_azure_keyvault_secrets_provider_addon)
        if keyvault_id:
            if enable_azure_keyvault_secrets_provider_addon:
                if cluster.ingress_profile and \
                   cluster.ingress_profile.web_app_routing and \
                   cluster.ingress_profile.web_app_routing.enabled:
                    if not is_valid_resource_id(keyvault_id):
                        raise InvalidArgumentValueError("Please provide a valid keyvault ID")
                    self.cmd.command_kwargs['operation_group'] = 'vaults'
                    keyvault_params = parse_resource_id(keyvault_id)
                    keyvault_subscription = keyvault_params['subscription']
                    keyvault_name = keyvault_params['name']
                    keyvault_rg = keyvault_params['resource_group']
                    keyvault_client = get_keyvault_client(self.cmd.cli_ctx, subscription_id=keyvault_subscription)
                    keyvault = keyvault_client.get(resource_group_name=keyvault_rg, vault_name=keyvault_name)
                    managed_identity_object_id = cluster.ingress_profile.web_app_routing.identity.object_id
                    is_service_principal = False

                    try:
                        if keyvault.properties.enable_rbac_authorization:
                            if not self.context.external_functions.add_role_assignment(
                                self.cmd,
                                "Key Vault Secrets User",
                                managed_identity_object_id,
                                is_service_principal,
                                scope=keyvault_id,
                            ):
                                logger.warning(
                                    "Could not create a role assignment for App Routing. "
                                    "Are you an Owner on this subscription?"
                                )
                        else:
                            keyvault = set_policy(
                                self.cmd,
                                keyvault_client,
                                keyvault_rg,
                                keyvault_name,
                                object_id=managed_identity_object_id,
                                secret_permissions=["Get"],
                                certificate_permissions=["Get"],
                            )
                    except Exception as ex:
                        raise CLIError('Error in granting keyvault permissions to managed identity.\n') from ex
                else:
                    raise CLIError('App Routing must be enabled to attach keyvault.\n')
            else:
                raise CLIError('Keyvault secrets provider addon must be enabled to attach keyvault.\n')

    def put_mc(self, mc: ManagedCluster) -> ManagedCluster:
        active_cloud = get_active_cloud(self.cmd.cli_ctx)
        if active_cloud.profile != "latest":
            cluster = sdk_no_wait(
                self.context.get_no_wait(),
                self.client.begin_create_or_update,
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
            )
            return cluster

        if self.check_is_postprocessing_required(mc):
            # send request
            poller = self.client.begin_create_or_update(
                resource_group_name=self.context.get_resource_group_name(),
                resource_name=self.context.get_name(),
                parameters=mc,
                headers=self.context.get_aks_custom_headers(),
                if_match=self.context.get_if_match(),
                if_none_match=self.context.get_if_none_match(),
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
                if_match=self.context.get_if_match(),
                if_none_match=self.context.get_if_none_match(),
            )
        return cluster

    def update_mc(self, mc: ManagedCluster) -> ManagedCluster:
        """Send request to update the existing managed cluster.

        :return: the ManagedCluster object
        """
        self._ensure_mc(mc)

        return self.put_mc(mc)

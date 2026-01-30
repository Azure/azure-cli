# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, consider-using-f-string, logging-format-interpolation, inconsistent-return-statements, broad-except, bare-except, too-many-statements, too-many-locals, too-many-boolean-expressions, too-many-branches, too-many-nested-blocks, pointless-statement, expression-not-assigned, unbalanced-tuple-unpacking, unsupported-assignment-operation, too-many-public-methods, broad-exception-caught, expression-not-assigned, ungrouped-imports
from copy import deepcopy
from typing import Any, Dict
from knack.log import get_logger

from azure.cli.command_modules.appservice.utils import _normalize_location
from azure.cli.core.azclierror import RequiredArgumentMissingError, ValidationError
from azure.cli.core.commands import AzCliCommand
from knack.util import CLIError
from azure.mgmt.core.tools import is_valid_resource_id

from ._constants import CONTAINER_APPS_RP
from ._utils import (get_vnet_location,
                     validate_environment_location,
                     _ensure_location_allowed,
                     _generate_log_analytics_if_not_provided,
                     load_cert_file,
                     safe_set,
                     get_default_workload_profiles,
                     _azure_monitor_quickstart, safe_get)
from ._client_factory import handle_raw_exception, handle_non_404_status_code_exception
from .base_resource import BaseResource
from ._models import (
    ManagedEnvironment as ManagedEnvironmentModel,
    VnetConfiguration as VnetConfigurationModel,
    AppLogsConfiguration as AppLogsConfigurationModel,
    LogAnalyticsConfiguration as LogAnalyticsConfigurationModel,
    CustomDomainConfiguration as CustomDomainConfigurationModel)

logger = get_logger(__name__)


class ContainerAppEnvDecorator(BaseResource):

    def get_argument_logs_destination(self):
        return self.get_param("logs_destination")

    def get_argument_storage_account(self):
        return self.get_param("storage_account")

    def get_argument_logs_customer_id(self):
        return self.get_param("logs_customer_id")

    def set_argument_logs_customer_id(self, logs_customer_id):
        self.set_param("logs_customer_id", logs_customer_id)

    def get_argument_logs_key(self):
        return self.get_param("logs_key")

    def set_argument_logs_key(self, logs_key):
        self.set_param("logs_key", logs_key)

    def get_argument_location(self):
        return self.get_param("location")

    def set_argument_location(self, location):
        self.set_param("location", location)

    def get_argument_instrumentation_key(self):
        return self.get_param("instrumentation_key")

    def get_argument_dapr_connection_string(self):
        return self.get_param("dapr_connection_string")

    def get_argument_infrastructure_subnet_resource_id(self):
        return self.get_param("infrastructure_subnet_resource_id")

    def get_argument_platform_reserved_cidr(self):
        return self.get_param("platform_reserved_cidr")

    def get_argument_platform_reserved_dns_ip(self):
        return self.get_param("platform_reserved_dns_ip")

    def get_argument_internal_only(self):
        return self.get_param("internal_only")

    def get_argument_tags(self):
        return self.get_param("tags")

    def get_argument_disable_warnings(self):
        return self.get_param("disable_warnings")

    def get_argument_zone_redundant(self):
        return self.get_param("zone_redundant")

    def get_argument_hostname(self):
        return self.get_param("hostname")

    def get_argument_certificate_file(self):
        return self.get_param("certificate_file")

    def get_argument_certificate_password(self):
        return self.get_param("certificate_password")

    def get_argument_mtls_enabled(self):
        return self.get_param("mtls_enabled")

    def get_argument_p2p_encryption_enabled(self):
        return self.get_param("p2p_encryption_enabled")

    def get_argument_workload_profile_type(self):
        return self.get_param("workload_profile_type")

    def get_argument_workload_profile_name(self):
        return self.get_param("workload_profile_name")

    def get_argument_min_nodes(self):
        return self.get_param("min_nodes")

    def get_argument_max_nodes(self):
        return self.get_param("max_nodes")

    def set_up_peer_to_peer_encryption(self):
        is_p2p_encryption_enabled = self.get_argument_p2p_encryption_enabled()
        is_mtls_enabled = self.get_argument_mtls_enabled()

        if is_p2p_encryption_enabled is not None:
            safe_set(self.managed_env_def, "properties", "peerTrafficConfiguration", "encryption", "enabled", value=is_p2p_encryption_enabled)

        if is_mtls_enabled is not None:
            safe_set(self.managed_env_def, "properties", "peerAuthentication", "mtls", "enabled", value=is_mtls_enabled)


class ContainerAppEnvCreateDecorator(ContainerAppEnvDecorator):
    def __init__(self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str):
        super().__init__(cmd, client, raw_parameters, models)
        self.managed_env_def = deepcopy(ManagedEnvironmentModel)

    def get_argument_enable_workload_profiles(self):
        return self.get_param("enable_workload_profiles")

    def get_argument_infrastructure_resource_group(self):
        return self.get_param("infrastructure_resource_group")

    def validate_arguments(self):
        location = self.get_argument_location()
        if self.get_argument_zone_redundant():
            if not self.get_argument_infrastructure_subnet_resource_id():
                raise RequiredArgumentMissingError("Cannot use --zone-redundant/-z without "
                                                   "--infrastructure-subnet-resource-id/-s")
            if not is_valid_resource_id(self.get_argument_infrastructure_subnet_resource_id()):
                raise ValidationError("--infrastructure-subnet-resource-id must be a valid resource id")
            vnet_location = get_vnet_location(self.cmd, self.get_argument_infrastructure_subnet_resource_id())
            if location:
                if _normalize_location(self.cmd, location) != vnet_location:
                    raise ValidationError(
                        f"Location '{location}' does not match the subnet's location: '{vnet_location}'. "
                        "Please change either --location/-l or --infrastructure-subnet-resource-id/-s")
            else:
                location = vnet_location

        location = validate_environment_location(self.cmd, location)
        _ensure_location_allowed(self.cmd, location, CONTAINER_APPS_RP, "managedEnvironments")
        self.set_argument_location(location)

        # validate mtls and p2p traffic encryption
        if self.get_argument_p2p_encryption_enabled() is False and self.get_argument_mtls_enabled() is True:
            raise ValidationError("Cannot use '--enable-mtls' with '--enable-peer-to-peer-encryption False'")

        # Infrastructure Resource Group
        if self.get_argument_infrastructure_resource_group() is not None:
            if not self.get_argument_infrastructure_subnet_resource_id():
                raise RequiredArgumentMissingError("Cannot use --infrastructure-resource-group/-i without "
                                                   "--infrastructure-subnet-resource-id/-s")
            if not self.get_argument_enable_workload_profiles():
                raise RequiredArgumentMissingError("Cannot use --infrastructure-resource-group/-i without "
                                                   "--enable-workload-profiles/-w")

    def create(self):
        try:
            return self.client.create(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(),
                                      name=self.get_argument_name(), managed_environment_envelope=self.managed_env_def, no_wait=self.get_argument_no_wait())
        except Exception as e:
            handle_raw_exception(e)

    def post_process(self, r):
        _azure_monitor_quickstart(self.cmd, self.get_argument_name(), self.get_argument_resource_group_name(), self.get_argument_storage_account(), self.get_argument_logs_destination())

        # return ENV
        if "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() != "succeeded" and not self.get_argument_no_wait():
            not self.get_argument_disable_warnings() and logger.warning('Containerapp environment creation in progress. Please monitor the creation using `az containerapp env show -n {} -g {}`'.format(self.get_argument_name(), self.get_argument_resource_group_name()))

        if "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() == "succeeded":
            not self.get_argument_disable_warnings() and logger.warning("\nContainer Apps environment created. To deploy a container app, use: az containerapp create --help\n")

        return r

    def construct_payload(self):
        self.set_up_app_log_configuration()

        self.managed_env_def["location"] = self.get_argument_location()
        self.managed_env_def["tags"] = self.get_argument_tags()
        self.managed_env_def["properties"]["zoneRedundant"] = self.get_argument_zone_redundant()

        self.set_up_workload_profiles()

        # Custom domains
        if self.get_argument_hostname():
            custom_domain = deepcopy(CustomDomainConfigurationModel)
            blob, _ = load_cert_file(self.get_argument_certificate_file(), self.get_argument_certificate_password())
            custom_domain["dnsSuffix"] = self.get_argument_hostname()
            custom_domain["certificatePassword"] = self.get_argument_certificate_password()
            custom_domain["certificateValue"] = blob
            self.managed_env_def["properties"]["customDomainConfiguration"] = custom_domain

        if self.get_argument_instrumentation_key() is not None:
            self.managed_env_def["properties"]["daprAIInstrumentationKey"] = self.get_argument_instrumentation_key()

        if self.get_argument_dapr_connection_string() is not None:
            self.managed_env_def["properties"]["daprAIConnectionString"] = self.get_argument_dapr_connection_string()

        # Vnet
        self.set_up_vnet_configuration()

        self.set_up_peer_to_peer_encryption()

        self.set_up_infrastructure_resource_group()

    def set_up_infrastructure_resource_group(self):
        if self.get_argument_enable_workload_profiles() and self.get_argument_infrastructure_subnet_resource_id() is not None:
            self.managed_env_def["properties"]["InfrastructureResourceGroup"] = self.get_argument_infrastructure_resource_group()

    def set_up_workload_profiles(self):
        # If the environment exists, infer the environment type
        existing_environment = None
        try:
            existing_environment = self.client.show(cmd=self.cmd,
                                                    resource_group_name=self.get_argument_resource_group_name(),
                                                    name=self.get_argument_name())
        except Exception as e:
            handle_non_404_status_code_exception(e)
        if self.get_argument_enable_workload_profiles():
            if existing_environment and safe_get(existing_environment, "properties", "workloadProfiles") is None:
                # check if input params include -w/--enable-workload-profiles
                if self.cmd.cli_ctx.data.get('safe_params') and ('-w' in self.cmd.cli_ctx.data.get(
                        'safe_params') or '--enable-workload-profiles' in self.cmd.cli_ctx.data.get('safe_params')):
                    raise ValidationError(
                        f"Existing environment {self.get_argument_name()} cannot enable workload profiles. If you want to use Consumption and Dedicated environment, please create a new one.")
                return

            self.managed_env_def["properties"]["workloadProfiles"] = get_default_workload_profiles(self.cmd, self.get_argument_location())
        else:
            if existing_environment and safe_get(existing_environment, "properties", "workloadProfiles") is not None:
                raise ValidationError(
                    f"Existing environment {self.get_argument_name()} uses workload profiles. If you want to use Consumption-Only environment, please create a new one.")

    def set_up_app_log_configuration(self):
        if (self.get_argument_logs_customer_id() is None or self.get_argument_logs_key() is None) and self.get_argument_logs_destination() == "log-analytics":
            logs_customer_id, logs_key = _generate_log_analytics_if_not_provided(self.cmd, self.get_argument_logs_customer_id(), self.get_argument_logs_key(),
                                                                                 self.get_argument_location(), self.get_argument_resource_group_name())
            self.set_argument_logs_customer_id(logs_customer_id)
            self.set_argument_logs_key(logs_key)

        if self.get_argument_logs_destination() == "log-analytics":
            log_analytics_config_def = deepcopy(LogAnalyticsConfigurationModel)
            log_analytics_config_def["customerId"] = self.get_argument_logs_customer_id()
            log_analytics_config_def["sharedKey"] = self.get_argument_logs_key()
        else:
            log_analytics_config_def = None

        app_logs_config_def = deepcopy(AppLogsConfigurationModel)
        app_logs_config_def["destination"] = self.get_argument_logs_destination() if self.get_argument_logs_destination() != "none" else None
        app_logs_config_def["logAnalyticsConfiguration"] = log_analytics_config_def

        self.managed_env_def["properties"]["appLogsConfiguration"] = app_logs_config_def

    def set_up_vnet_configuration(self):
        if self.get_argument_infrastructure_subnet_resource_id() or self.get_argument_platform_reserved_cidr() or self.get_argument_platform_reserved_dns_ip():
            vnet_config_def = deepcopy(VnetConfigurationModel)

            if self.get_argument_infrastructure_subnet_resource_id() is not None:
                vnet_config_def["infrastructureSubnetId"] = self.get_argument_infrastructure_subnet_resource_id()

            if self.get_argument_platform_reserved_cidr() is not None:
                vnet_config_def["platformReservedCidr"] = self.get_argument_platform_reserved_cidr()

            if self.get_argument_platform_reserved_dns_ip() is not None:
                vnet_config_def["platformReservedDnsIP"] = self.get_argument_platform_reserved_dns_ip()

            self.managed_env_def["properties"]["vnetConfiguration"] = vnet_config_def

        if self.get_argument_internal_only():
            if not self.get_argument_infrastructure_subnet_resource_id():
                raise ValidationError(
                    'Infrastructure subnet resource ID needs to be supplied for internal only environments.')
            self.managed_env_def["properties"]["vnetConfiguration"]["internal"] = True


class ContainerAppEnvUpdateDecorator(ContainerAppEnvDecorator):
    def __init__(self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str):
        super().__init__(cmd, client, raw_parameters, models)
        self.managed_env_def = {}

    def validate_arguments(self):
        if self.get_argument_logs_destination() == "log-analytics" or self.get_argument_logs_customer_id() or self.get_argument_logs_key():
            if self.get_argument_logs_destination() != "log-analytics":
                raise ValidationError(
                    "When configuring Log Analytics workspace, --logs-destination should be \"log-analytics\"")
            if not self.get_argument_logs_customer_id() or not self.get_argument_logs_key():
                raise ValidationError(
                    "Must provide --logs-workspace-id and --logs-workspace-key if updating logs destination to type 'log-analytics'.")

        # validate mtls and p2p traffic encryption
        if self.get_argument_p2p_encryption_enabled() is False and self.get_argument_mtls_enabled() is True:
            raise ValidationError("Cannot use '--enable-mtls' with '--enable-peer-to-peer-encryption False'")

    def construct_payload(self):
        try:
            r = self.client.show(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name())
        except CLIError as e:
            handle_raw_exception(e)

        # General setup
        safe_set(self.managed_env_def, "location", value=r["location"])  # required for API
        if self.get_argument_tags():
            safe_set(self.managed_env_def, "tags", value=self.get_argument_tags())

        # Logs
        self.set_up_app_log_configuration()

        # Custom domains
        self.set_up_custom_domain_configuration()

        # workload Profiles
        self.set_up_workload_profiles(r)

        self.set_up_peer_to_peer_encryption()

        # dapr
        self.set_up_dapr()

    def set_up_app_log_configuration(self):
        logs_destination = self.get_argument_logs_destination()

        if logs_destination:
            if logs_destination == "none":
                safe_set(self.managed_env_def, "properties", "appLogsConfiguration", "destination", value=None)
                safe_set(self.managed_env_def, "properties", "appLogsConfiguration", "logAnalyticsConfiguration", value=None)
            else:
                safe_set(self.managed_env_def, "properties", "appLogsConfiguration", "destination", value=logs_destination)

        if logs_destination == "azure-monitor":
            safe_set(self.managed_env_def, "properties", "appLogsConfiguration", "logAnalyticsConfiguration", value=None)

        if self.get_argument_logs_customer_id() and self.get_argument_logs_key():
            safe_set(self.managed_env_def, "properties", "appLogsConfiguration", "logAnalyticsConfiguration", "customerId", value=self.get_argument_logs_customer_id())
            safe_set(self.managed_env_def, "properties", "appLogsConfiguration", "logAnalyticsConfiguration", "sharedKey", value=self.get_argument_logs_key())

    def set_up_custom_domain_configuration(self):
        if self.get_argument_hostname():
            safe_set(self.managed_env_def, "properties", "customDomainConfiguration", value={})
            cert_def = self.managed_env_def["properties"]["customDomainConfiguration"]
            if self.get_argument_certificate_file():
                blob, _ = load_cert_file(self.get_argument_certificate_file(), self.get_argument_certificate_password())
                safe_set(cert_def, "certificateValue", value=blob)
            safe_set(cert_def, "dnsSuffix", value=self.get_argument_hostname())
            if self.get_argument_certificate_password():
                safe_set(cert_def, "certificatePassword", value=self.get_argument_certificate_password())

    def set_up_workload_profiles(self, r):
        workload_profile_name = self.get_argument_workload_profile_name()
        workload_profile_type = self.get_argument_workload_profile_type()

        if workload_profile_name:
            if "workloadProfiles" not in r["properties"] or not r["properties"]["workloadProfiles"]:
                raise ValidationError(
                    "This environment does not allow for workload profiles. Can create a compatible environment with 'az containerapp env create --enable-workload-profiles'")

            if workload_profile_type:
                workload_profile_type = workload_profile_type.upper()
            workload_profiles = r["properties"]["workloadProfiles"]
            profile = [p for p in workload_profiles if p["name"].lower() == workload_profile_name.lower()]
            update = False  # flag for updating an existing profile
            if profile:
                profile = profile[0]
                update = True
            else:
                profile = {"name": workload_profile_name}

            if workload_profile_type:
                profile["workloadProfileType"] = workload_profile_type
            if self.get_argument_max_nodes():
                profile["maximumCount"] = self.get_argument_max_nodes()
            if self.get_argument_min_nodes():
                profile["minimumCount"] = self.get_argument_min_nodes()

            if not update:
                workload_profiles.append(profile)
            else:
                idx = [i for i, p in enumerate(workload_profiles) if p["name"].lower() == workload_profile_name.lower()][0]
                workload_profiles[idx] = profile

            safe_set(self.managed_env_def, "properties", "workloadProfiles", value=workload_profiles)

    def set_up_dapr(self):
        dapr_connection_string = self.get_argument_dapr_connection_string()
        if dapr_connection_string is not None:
            if dapr_connection_string == "none":
                safe_set(self.managed_env_def, "properties", "daprAIConnectionString", value=None)
            else:
                safe_set(self.managed_env_def, "properties", "daprAIConnectionString", value=dapr_connection_string)

    def update(self):
        try:
            return self.client.update(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(),
                                      name=self.get_argument_name(), managed_environment_envelope=self.managed_env_def, no_wait=self.get_argument_no_wait())
        except Exception as e:
            handle_raw_exception(e)

    def post_process(self, r):
        _azure_monitor_quickstart(self.cmd, self.get_argument_name(), self.get_argument_resource_group_name(), self.get_argument_storage_account(), self.get_argument_logs_destination())

        return r

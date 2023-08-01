# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import ValidationError, CLIError, ResourceNotFoundError
from ._client_factory import handle_raw_exception
from ._clients import ManagedEnvironmentClient, ContainerAppClient
from ._constants import (
    CONTAINER_APPS_RP
)
from ._utils import register_provider_if_needed, validate_container_app_name, AppType


class DevServiceUtils:
    @staticmethod
    def create_service(cmd, service_name, environment_name, resource_group_name, no_wait, disable_warnings, image,
                       service_type, container_name):
        from .custom import create_containerapp

        register_provider_if_needed(cmd, CONTAINER_APPS_RP)
        validate_container_app_name(service_name, AppType.ContainerApp.name)

        env_info = None

        try:
            env_info = ManagedEnvironmentClient.show(cmd=cmd, resource_group_name=resource_group_name,
                                                     name=environment_name)
        except Exception:
            pass

        if not env_info:
            raise ResourceNotFoundError("The environment '{}' in resource group '{}' was not found".format(
                environment_name, resource_group_name))

        return create_containerapp(cmd=cmd, name=service_name, resource_group_name=resource_group_name,
                                   managed_env=env_info['id'],
                                   image=image, service_type=service_type, container_name=container_name,
                                   no_wait=no_wait, disable_warnings=disable_warnings)

    @staticmethod
    def delete_service(cmd, service_name, resource_group_name, no_wait, service_type):
        register_provider_if_needed(cmd, CONTAINER_APPS_RP)

        containerapp_def = None

        try:
            containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name,
                                                       name=service_name)
        except Exception:
            pass

        if not containerapp_def:
            raise ResourceNotFoundError("The service '{}' does not exist".format(service_name))
        if containerapp_def["properties"]["configuration"]["service"] is None:
            raise ResourceNotFoundError("The service '{}' of type {} does not exist".format(service_name, service_type))
        if containerapp_def["properties"]["configuration"]["service"]["type"] != service_type:
            raise ResourceNotFoundError("The service '{}' of type {} does not exist".format(service_name, service_type))

        try:
            return ContainerAppClient.delete(cmd=cmd, name=service_name, resource_group_name=resource_group_name,
                                             no_wait=no_wait)
        except CLIError as e:
            handle_raw_exception(e)

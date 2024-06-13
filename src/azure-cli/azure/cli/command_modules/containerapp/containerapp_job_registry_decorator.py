# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=ungrouped-imports
# pylint: disable=unused-argument, unused-variable
# pylint: disable=broad-exception-caught
# pylint: disable=logging-format-interpolation
# pylint: disable=too-many-statements, too-many-locals, too-many-branches, too-many-public-methods, too-many-boolean-expressions, expression-not-assigned
from copy import deepcopy
from urllib.parse import urlparse

from typing import Dict, Any

from azure.cli.core.commands import AzCliCommand

from azure.cli.core.azclierror import (
    RequiredArgumentMissingError,
    ValidationError, ResourceNotFoundError, InvalidArgumentValueError)

from knack.log import get_logger

from ._constants import ACR_IMAGE_SUFFIX
from .base_resource import BaseResource
from ._client_factory import handle_raw_exception, handle_non_404_status_code_exception

from ._models import (
    RegistryCredentials as RegistryCredentialsModel)

from ._utils import (store_as_secret_and_return_secret_ref,
                     set_managed_identity,
                     safe_set,
                     safe_get,
                     _remove_registry_secret,
                     _get_acr_cred)

logger = get_logger(__name__)


class ContainerAppJobRegistryDecorator(BaseResource):
    def __init__(
            self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str
    ):
        super().__init__(cmd, client, raw_parameters, models)
        self.new_containerappjob = {}
        self.containerappjob_def = {}

    def get_argument_server(self):
        return self.get_param("server")

    def get_argument_username(self):
        return self.get_param("username")

    def set_argument_username(self, username):
        self.set_param("username", username)

    def get_argument_password(self):
        return self.get_param("password")

    def set_argument_password(self, password):
        self.set_param("password", password)

    def get_argument_identity(self):
        return self.get_param("identity")

    def get_argument_disable_warnings(self):
        return self.get_param("disable_warnings")

    def validate_arguments(self):
        # Check if containerapp job exists
        self.containerappjob_def = None
        try:
            self.containerappjob_def = self.client.show(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name())
        except Exception as e:
            handle_non_404_status_code_exception(e)

        if not self.containerappjob_def:
            raise ResourceNotFoundError("The containerapps job '{}' does not exist".format(self.get_argument_name()))

    def show(self):
        registries_def = safe_get(self.containerappjob_def, "properties", "configuration", "registries")
        if registries_def is None or len(registries_def) == 0:
            raise ValidationError("The containerapp job {} has no assigned registries.".format(self.get_argument_name()))

        for r in registries_def:
            if r['server'].lower() == self.get_argument_server().lower():
                return r
        raise InvalidArgumentValueError("The containerapp job {} does not have specified registry {} assigned.".format(self.get_argument_name(), self.get_argument_server()))

    def list(self):
        return safe_get(self.containerappjob_def, "properties", "configuration", "registries", default=[])

    def set_up_get_existing_secrets(self):
        if "secrets" not in self.containerappjob_def["properties"]["configuration"]:
            safe_set(self.containerappjob_def, "properties", "configuration", "secrets", value=[])
            safe_set(self.new_containerappjob, "properties", "configuration", "secrets", value=[])
        else:
            secrets = None
            try:
                secrets = self.client.list_secrets(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name())
            except Exception as e:  # pylint: disable=broad-except
                handle_raw_exception(e)
            safe_set(self.containerappjob_def, "properties", "configuration", "secrets", value=secrets["value"])
            safe_set(self.new_containerappjob, "properties", "configuration", "secrets", value=secrets["value"])

    def send_update(self):
        try:
            r = self.client.update(
                cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name(), containerapp_job_envelope=self.new_containerappjob,
                no_wait=self.get_argument_no_wait())
            return r
        except Exception as e:
            handle_raw_exception(e)


class ContainerAppJobRegistryRemoveDecorator(ContainerAppJobRegistryDecorator):
    def construct_payload(self):
        registries_def = safe_get(self.containerappjob_def, "properties", "configuration", "registries")
        safe_set(self.new_containerappjob, "properties", "configuration", "registries", value=registries_def)
        logger.warning(self.new_containerappjob["properties"]["configuration"]["registries"])
        if registries_def is None or len(registries_def) == 0:
            raise ValidationError(
                "The containerapp job {} has no assigned registries.".format(self.get_argument_name()))

        self.set_up_get_existing_secrets()

        was_removed = False
        for i, value in enumerate(registries_def):
            r = value
            if r['server'].lower() == self.get_argument_server().lower():
                registries_def.pop(i)
                if r.get('username'):
                    _remove_registry_secret(containerapp_def=self.new_containerappjob, server=self.get_argument_server(),
                                            username=r.get('username'))
                was_removed = True
                break

        if not was_removed:
            raise ValidationError(
                "The containerapp job {} does not have specified registry {} assigned.".format(self.get_argument_name(),
                                                                                               self.get_argument_server()))

    def remove(self):
        r = self.send_update()
        logger.warning("Registry successfully removed.")
        return safe_get(r, "properties", "configuration", "registries")


class ContainerAppJobRegistrySetDecorator(ContainerAppJobRegistryDecorator):
    def validate_arguments(self):
        if (self.get_argument_username() or self.get_argument_password()) and self.get_argument_identity():
            raise ValidationError("Use either identity or --username/--password.")

        super().validate_arguments()

    def construct_payload(self):

        self.set_up_get_existing_secrets()

        registries_def = safe_get(self.containerappjob_def, "properties", "configuration", "registries", default=[])
        safe_set(self.new_containerappjob, "properties", "configuration", "registries", value=registries_def)

        if (not self.get_argument_username() or not self.get_argument_password()) and not self.get_argument_identity():
            # If registry is Azure Container Registry, we can try inferring credentials
            if ACR_IMAGE_SUFFIX not in self.get_argument_server():
                raise RequiredArgumentMissingError(
                    'Registry username and password are required if you are not using Azure Container Registry.')
            not self.get_argument_disable_warnings() and logger.warning(
                'No credential was provided to access Azure Container Registry. Trying to look up...')
            parsed = urlparse(self.get_argument_server())
            registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]

            try:
                username, password, _ = _get_acr_cred(self.cmd.cli_ctx, registry_name)
                self.set_argument_username(username)
                self.set_argument_password(password)
            except Exception as ex:
                raise RequiredArgumentMissingError(
                    'Failed to retrieve credentials for container registry. Please provide the registry username and password') from ex

        # Check if updating existing registry
        updating_existing_registry = False
        for r in registries_def:
            if r['server'].lower() == self.get_argument_server().lower():
                not self.get_argument_disable_warnings() and logger.warning("Updating existing registry.")
                updating_existing_registry = True
                if self.get_argument_username():
                    r["username"] = self.get_argument_username()
                    r["identity"] = None
                if self.get_argument_password():
                    r["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                        self.new_containerappjob["properties"]["configuration"]["secrets"],
                        r["username"],
                        r["server"],
                        self.get_argument_password(),
                        update_existing_secret=True)
                    r["identity"] = None
                if self.get_argument_identity():
                    r["identity"] = self.get_argument_identity()
                    r["username"] = None
                    r["passwordSecretRef"] = None

        # If not updating existing registry, add as new registry
        if not updating_existing_registry:
            registry = deepcopy(RegistryCredentialsModel)
            registry["server"] = self.get_argument_server()
            if not self.get_argument_identity():
                registry["username"] = self.get_argument_username()
                registry["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                    self.new_containerappjob["properties"]["configuration"]["secrets"],
                    self.get_argument_username(),
                    self.get_argument_server(),
                    self.get_argument_password(),
                    update_existing_secret=True)
            else:
                registry["identity"] = self.get_argument_identity()

            registries_def.append(registry)

        if self.get_argument_identity():
            identity_def = safe_get(self.containerappjob_def, "identity", default={})
            safe_set(self.new_containerappjob, "identity", value=identity_def)

            system_assigned_identity = self.get_argument_identity().lower() == "system"
            user_assigned = None if system_assigned_identity else [self.get_argument_identity()]
            set_managed_identity(self.cmd, self.get_argument_resource_group_name(), self.new_containerappjob, system_assigned_identity, user_assigned)

    def set(self):
        r = self.send_update()
        return safe_get(r, "properties", "configuration", "registries")

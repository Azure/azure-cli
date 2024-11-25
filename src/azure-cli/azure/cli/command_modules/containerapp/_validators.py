# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, unused-argument

import re
from azure.cli.core.azclierror import (ValidationError, ResourceNotFoundError, InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError)
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from knack.log import get_logger

from ._clients import ContainerAppClient, ManagedEnvironmentClient
from ._ssh_utils import ping_container_app
from ._utils import safe_get, is_registry_msi_system
from ._constants import ACR_IMAGE_SUFFIX, LOG_TYPE_SYSTEM, MANAGED_ENVIRONMENT_RESOURCE_TYPE

logger = get_logger(__name__)


# called directly from custom method bc otherwise it disrupts the --environment auto RID functionality
def validate_create(registry_identity, registry_pass, registry_user, registry_server, no_wait):
    if registry_identity and (registry_pass or registry_user):
        raise MutuallyExclusiveArgumentError("Cannot provide both registry identity and username/password")
    if is_registry_msi_system(registry_identity) and no_wait:
        raise MutuallyExclusiveArgumentError("--no-wait is not supported with system registry identity")
    if registry_identity and not is_valid_resource_id(registry_identity) and not is_registry_msi_system(registry_identity):
        raise InvalidArgumentValueError("--registry-identity must be an identity resource ID or 'system'")
    if registry_identity and ACR_IMAGE_SUFFIX not in (registry_server or ""):
        raise InvalidArgumentValueError("--registry-identity: expected an ACR registry (*.azurecr.io) for --registry-server")


def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def validate_revision_suffix(value):
    if value is not None:
        # what does the following regex check?
        # 1. ^[a-z0-9] - starts with a letter or number
        # 2. (?!.*-{2}) - does not contain '--'
        # 3. ([-a-z0-9]*[a-z0-9])? - ends with a letter or number and can contain '-' in between
        matched = re.match(r"^[a-z0-9](?!.*-{2})([-a-z0-9]*[a-z0-9])?$", value)
        if not matched:
            raise ValidationError(f"Invalid Container App revision suffix '{value}'. A revision suffix must consist of lower case alphanumeric characters or '-', start with a letter or number, end with an alphanumeric character and cannot have '--'.")


def validate_memory(namespace):
    if namespace.memory is not None:
        valid = False

        if not namespace.memory.endswith("Gi"):
            namespace.memory = namespace.memory.rstrip()
            namespace.memory += "Gi"

        valid = _is_number(namespace.memory[:-2])

        if not valid:
            raise ValidationError("Usage error: --memory must be a number ending with \"Gi\"")


def validate_cpu(namespace):
    if namespace.cpu:
        cpu = namespace.cpu
        try:
            float(cpu)
        except ValueError as e:
            raise ValidationError("Usage error: --cpu must be a number eg. \"0.5\"") from e


def validate_managed_env_name_or_id(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import resource_id

    if namespace.managed_env:
        if not is_valid_resource_id(namespace.managed_env):
            namespace.managed_env = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.App',
                type='managedEnvironments',
                name=namespace.managed_env
            )


def validate_storage_name_or_id(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import resource_id

    if namespace.storage_account:
        if not is_valid_resource_id(namespace.storage_account):
            namespace.storage_account = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Storage',
                type='storageAccounts',
                name=namespace.storage_account
            )


def validate_registry_server(namespace):
    if "create" in namespace.command.lower():
        if namespace.registry_server:
            if not namespace.registry_user or not namespace.registry_pass:
                if ACR_IMAGE_SUFFIX not in namespace.registry_server:
                    raise ValidationError("Usage error: --registry-server, --registry-password and --registry-username are required together if not using Azure Container Registry")


def validate_registry_user(namespace):
    if "create" in namespace.command.lower():
        if namespace.registry_user:
            if not namespace.registry_server or (not namespace.registry_pass and ACR_IMAGE_SUFFIX not in namespace.registry_server):
                raise ValidationError("Usage error: --registry-server, --registry-password and --registry-username are required together if not using Azure Container Registry")


def validate_registry_pass(namespace):
    if "create" in namespace.command.lower():
        if namespace.registry_pass:
            if not namespace.registry_server or (not namespace.registry_user and ACR_IMAGE_SUFFIX not in namespace.registry_server):
                raise ValidationError("Usage error: --registry-server, --registry-password and --registry-username are required together if not using Azure Container Registry")


def validate_target_port(namespace):
    if "create" in namespace.command.lower():
        if namespace.target_port:
            if not namespace.ingress:
                raise ValidationError("Usage error: must specify --ingress with --target-port")


def validate_allow_insecure(namespace):
    if "create" in namespace.command.lower():
        if namespace.allow_insecure:
            if not namespace.ingress:
                raise ValidationError("Usage error: must specify --ingress with --allow-insecure")
            if namespace.transport == "tcp":
                raise ValidationError("Usage error: --allow-insecure is not supported for TCP ingress")


def _ping_containerapp_if_need(cmd, app) -> (bool, str):
    # if container app has no ingress or is internal, not need to ping
    if safe_get(app, "properties", "configuration", "ingress") is None or safe_get(app, "properties", "configuration", "ingress", "external") is False:
        return False, None

    parsed_env = parse_resource_id(safe_get(app, "properties", "environmentId"))
    env_name = parsed_env['name']
    env_rg = parsed_env['resource_group']
    if parsed_env["resource_type"].lower() == MANAGED_ENVIRONMENT_RESOURCE_TYPE.lower():
        env = ManagedEnvironmentClient.show(cmd, env_rg, env_name)
        # if environment is internal, not need to ping
        if safe_get(env, "properties", "vnetConfiguration", "internal") is True:
            return False, None

    try:
        # ping containerapp to activate its replica
        ping_container_app(app)  # needed to get an alive replica
    except Exception as ex:  # pylint: disable=broad-except
        warning_message = f"Error encountered while attempting to ping container app.\n" \
                          f"Error message: '{str(ex)}'\n" \
                          f"Please ensure there is an alive replica. "
        return True, warning_message

    return False, None


def _set_ssh_defaults(cmd, namespace):
    app = ContainerAppClient.show(cmd, namespace.resource_group_name, namespace.name)
    if not app:
        raise ResourceNotFoundError("Could not find a container app")
    replicas = []
    if not namespace.revision:
        namespace.revision = app.get("properties", {}).get("latestRevisionName")
        if not namespace.revision:
            raise ResourceNotFoundError("Could not find a revision")
    if not namespace.replica:
        failed_to_ping, warning_message = _ping_containerapp_if_need(cmd, app)
        replicas = ContainerAppClient.list_replicas(cmd=cmd,
                                                    resource_group_name=namespace.resource_group_name,
                                                    container_app_name=namespace.name,
                                                    revision_name=namespace.revision)
        if not replicas:
            if failed_to_ping:
                logger.warning(warning_message)
            raise ResourceNotFoundError("Could not find a replica for this app")
        namespace.replica = replicas[0]["name"]
    if not namespace.container:
        revision = ContainerAppClient.show_revision(cmd, resource_group_name=namespace.resource_group_name,
                                                    container_app_name=namespace.name,
                                                    name=namespace.revision)
        revision_containers = safe_get(revision, "properties", "template", "containers")
        if revision_containers:
            namespace.container = revision_containers[0]["name"]


def _validate_revision_exists(cmd, namespace):
    revision = ContainerAppClient.show_revision(cmd, resource_group_name=namespace.resource_group_name,
                                                container_app_name=namespace.name, name=namespace.revision)
    if not revision:
        raise ResourceNotFoundError("Could not find revision")


def _validate_replica_exists(cmd, namespace):
    replica = ContainerAppClient.get_replica(cmd=cmd,
                                             resource_group_name=namespace.resource_group_name,
                                             container_app_name=namespace.name,
                                             revision_name=namespace.revision,
                                             replica_name=namespace.replica)
    if not replica:
        raise ResourceNotFoundError("Could not find replica")


def _validate_container_exists(cmd, namespace):
    replica_containers = ContainerAppClient.get_replica(cmd=cmd,
                                                        resource_group_name=namespace.resource_group_name,
                                                        container_app_name=namespace.name,
                                                        revision_name=namespace.revision,
                                                        replica_name=namespace.replica)["properties"]["containers"]
    matches = [r for r in replica_containers if r["name"].lower() == namespace.container.lower()]
    if not matches:
        raise ResourceNotFoundError("Could not find container")


# also used to validate logstream
def validate_ssh(cmd, namespace):
    if not hasattr(namespace, "kind") or (namespace.kind and namespace.kind.lower() != LOG_TYPE_SYSTEM):
        _set_ssh_defaults(cmd, namespace)
        _validate_revision_exists(cmd, namespace)
        _validate_replica_exists(cmd, namespace)
        _validate_container_exists(cmd, namespace)


def validate_cors_max_age(cmd, namespace):
    if namespace.max_age:
        try:
            if namespace.max_age == "":
                return

            max_age = int(namespace.max_age)
            if max_age < 0:
                raise InvalidArgumentValueError("max-age must be a positive integer.")
        except ValueError:
            raise InvalidArgumentValueError("max-age must be an integer.")

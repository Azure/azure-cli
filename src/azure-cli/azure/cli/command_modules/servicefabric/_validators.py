# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrestazure.azure_exceptions import CloudError
from ._client_factory import servicefabric_client_factory

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def validate_create_service(namespace):
    if not namespace.stateless and not namespace.stateful:
        raise CLIError("One of these paremeters must be specified: --stateless or --stateful")
    if namespace.stateless and namespace.stateful:
        raise CLIError("Only one of these paremeters can be specified: --stateless or --stateful")
    if namespace.stateless:
        if namespace.target_replica_set_size or namespace.min_replica_set_size:
            raise CLIError("--target-replica-set-size and --min-replica-set-size should only be use with --stateful")
        if not namespace.instance_count:
            raise CLIError("--instance-count is required")
    if namespace.stateful:
        if namespace.instance_count:
            raise CLIError("Unexpected parameter --instance-count should not be use with --stateful")
        if not namespace.target_replica_set_size or not namespace.min_replica_set_size:
            raise CLIError("--target-replica-set-size and --min-replica-set-size are required")

    # pylint: disable=too-many-boolean-expressions
    if ((namespace.partition_scheme_singleton and
         (namespace.partition_scheme_uniformInt64 or namespace.partition_scheme_named)) or
            (namespace.partition_scheme_uniformInt64 and
             (namespace.partition_scheme_singleton or namespace.partition_scheme_named)) or
            (namespace.partition_scheme_named and
             (namespace.partition_scheme_uniformInt64 or namespace.partition_scheme_singleton))):
        raise CLIError("Only use one partition scheme parameter out of"
                       "--partition_scheme_singleton, --partition_scheme_uniformInt64 or --partition_scheme_named")

    if not namespace.service_name.startswith(namespace.application_name):
        raise CLIError("Invalid service name, the application name must be a prefix of the service name, "
                       "for example: '{}~{}'".format(namespace.application_name, namespace.service_name))


def validate_update_application(cmd, namespace):
    client = servicefabric_client_factory(cmd.cli_ctx)
    app = _safe_get_resource(client.applications.get,
                             (namespace.resource_group_name, namespace.cluster_name, namespace.application_name))
    if app is None:
        raise CLIError("Application '{}' Not Found.".format(namespace.application_name))
    if namespace.application_type_version is not None:
        if app.type_version == namespace.application_type_version:
            raise CLIError("The application '{}' is alrady running with type version '{}'."
                           .format(app.name, app.type_version))
        type_version = _safe_get_resource(client.application_type_versions.get,
                                          (namespace.resource_group_name,
                                           namespace.cluster_name,
                                           app.type_name,
                                           namespace.application_type_version))
        if type_version is None:
            raise CLIError("Application type version {}:{} not found. "
                           "Create the type version before runnig this command."
                           .format(app.type_name, namespace.application_type_version))

    if namespace.upgrade_replica_set_check_timeout:
        namespace.upgrade_replica_set_check_timeout = int(namespace.upgrade_replica_set_check_timeout)
    if namespace.health_check_stable_duration:
        namespace.health_check_stable_duration = int(namespace.health_check_stable_duration)
    if namespace.health_check_retry_timeout:
        namespace.health_check_retry_timeout = int(namespace.health_check_retry_timeout)
    if namespace.health_check_wait_duration:
        namespace.health_check_wait_duration = int(namespace.health_check_wait_duration)
    if namespace.upgrade_timeout:
        namespace.upgrade_timeout = int(namespace.upgrade_timeout)
    if namespace.upgrade_domain_timeout:
        namespace.upgrade_domain_timeout = int(namespace.upgrade_domain_timeout)
    if namespace.minimum_nodes:
        namespace.minimum_nodes = int(namespace.minimum_nodes)
    if namespace.maximum_nodes:
        namespace.maximum_nodes = int(namespace.maximum_nodes)


def validate_create_application(cmd, namespace):
    client = servicefabric_client_factory(cmd.cli_ctx)
    if namespace.package_url is None:
        type_version = _safe_get_resource(client.application_type_versions.get,
                                          (namespace.resource_group_name,
                                           namespace.cluster_name,
                                           namespace.application_type_name,
                                           namespace.version))
        if type_version is None:
            raise CLIError("Application type version {}:{} not found. "
                           "Create the type version before runnig this command or use --package-url to create it."
                           .format(namespace.application_type_name, namespace.version))

    if namespace.minimum_nodes:
        namespace.minimum_nodes = int(namespace.minimum_nodes)
    if namespace.maximum_nodes:
        namespace.maximum_nodes = int(namespace.maximum_nodes)


def _safe_get_resource(getResourceAction, params):
    try:
        return getResourceAction(*params)
    except CloudError as ex:
        if ex.error.error == 'ResourceNotFound':
            return None
        logger.warning("Unable to get resource, exception: %s", ex)
        raise

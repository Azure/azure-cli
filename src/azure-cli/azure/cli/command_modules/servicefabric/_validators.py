# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrestazure.azure_exceptions import CloudError
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.azclierror import ValidationError
from azure.cli.command_modules.servicefabric._sf_utils import _get_resource_group_by_name
from azure.mgmt.servicefabricmanagedclusters.models import (PartitionScheme, ServiceKind)
from ._client_factory import servicefabric_client_factory, servicefabric_managed_client_factory

logger = get_logger(__name__)


def validate_create_service(namespace):
    if namespace.state == 'stateless':
        if namespace.target_replica_set_size or namespace.min_replica_set_size:
            raise CLIError("--target-replica-set-size and --min-replica-set-size should only be use with "
                           "--state stateful")
        if not namespace.instance_count:
            raise CLIError("--instance-count is required")
    else:  # stateful
        if namespace.instance_count:
            raise CLIError("Unexpected parameter --instance-count should only be use with --state stateless")
        if not namespace.target_replica_set_size or not namespace.min_replica_set_size:
            raise CLIError("--target-replica-set-size and --min-replica-set-size are required")

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
                           "Create the type version before running this command."
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
        if namespace.minimum_nodes < 0:
            raise CLIError("minimum_nodes should be a non-negative integer.")
    if namespace.maximum_nodes:
        namespace.maximum_nodes = int(namespace.maximum_nodes)
        if namespace.maximum_nodes < 0:
            raise CLIError("maximum_nodes should be a non-negative integer.")


def validate_create_application(cmd, namespace):
    client = servicefabric_client_factory(cmd.cli_ctx)
    if namespace.package_url is None:
        type_version = _safe_get_resource(client.application_type_versions.get,
                                          (namespace.resource_group_name,
                                           namespace.cluster_name,
                                           namespace.application_type_name,
                                           namespace.application_type_version))
        if type_version is None:
            raise CLIError("Application type version {}:{} not found. "
                           "Create the type version before running this command or use --package-url to create it."
                           .format(namespace.application_type_name, namespace.application_type_version))

    if namespace.minimum_nodes:
        namespace.minimum_nodes = int(namespace.minimum_nodes)
        if namespace.minimum_nodes < 0:
            raise CLIError("minimum_nodes should be a non-negative integer.")
    if namespace.maximum_nodes:
        namespace.maximum_nodes = int(namespace.maximum_nodes)
        if namespace.maximum_nodes < 0:
            raise CLIError("maximum_nodes should be a non-negative integer.")


# Managed Clusters
def validate_create_managed_cluster(cmd, namespace):
    rg = _get_resource_group_by_name(cmd.cli_ctx, namespace.resource_group_name)
    if rg is None and namespace.location is None:
        raise CLIError("Resource group {} doesn't exists and location is not provided. "
                       "Either create the resource group before running this command or provide the location parameter."
                       .format(namespace.resource_group_name))

    if namespace.client_cert_issuer_thumbprint is not None:
        if namespace.client_cert_common_name is None:
            raise CLIError("--client-cert-issuer-thumbprint should be used with --client-cert-common-name.")


def validate_create_managed_service(namespace):
    if namespace.service_type is None:
        raise CLIError("--service-type is required")

    if namespace.state.lower() == ServiceKind.STATELESS.lower():
        if namespace.target_replica_set_size or namespace.min_replica_set_size:
            raise ValidationError("--target-replica-set-size and --min-replica-set-size should only be use with "
                                  "--state stateful")
        if not namespace.instance_count:
            raise ValidationError("--instance-count is required")
        namespace.instance_count = int(namespace.instance_count)
    elif namespace.state.lower() == ServiceKind.STATEFUL.lower():
        if namespace.instance_count:
            raise ValidationError("Unexpected parameter --instance-count should only be use with --state stateless")
        if not namespace.target_replica_set_size or not namespace.min_replica_set_size:
            raise ValidationError("--target-replica-set-size and --min-replica-set-size are required")
        namespace.target_replica_set_size = int(namespace.target_replica_set_size)
        namespace.min_replica_set_size = int(namespace.min_replica_set_size)
    else:
        raise ValidationError("Invalid --state '%s': service state is not valid." % namespace.state)

    if namespace.partition_scheme is None:
        raise ValidationError("--partition-scheme is required")

    if namespace.partition_scheme.lower() == PartitionScheme.NAMED.lower():
        if namespace.partition_names is None:
            raise ValidationError("--partition-names is required for partition scheme '%s'"
                                  % namespace.partition_scheme)
    elif namespace.partition_scheme.lower() == PartitionScheme.SINGLETON.lower():
        pass  # No parameters needed for singleton
    elif namespace.partition_scheme.lower() == PartitionScheme.UNIFORM_INT64_RANGE.lower():
        if namespace.partition_count is None or namespace.low_key is None or namespace.high_key is None:
            raise ValidationError(
                "--partition-count, --low-key and --high-key are required for partition scheme '%s'"
                % namespace.partition_scheme)
        namespace.partition_count = int(namespace.partition_count)
        namespace.low_key = int(namespace.low_key)
        namespace.high_key = int(namespace.high_key)
    else:
        raise ValidationError(
            "Invalid --partition_scheme '%s': service partition_scheme is not valid." % namespace.partition_scheme)


def validate_update_managed_service(cmd, namespace):
    client = servicefabric_managed_client_factory(cmd.cli_ctx)
    service = _safe_get_resource(client.services.get,
                                 (namespace.resource_group_name, namespace.cluster_name,
                                  namespace.application_name, namespace.service_name))
    if service.properties.service_kind.lower() == ServiceKind.STATELESS.lower():
        if namespace.target_replica_set_size or namespace.min_replica_set_size:
            raise ValidationError("--target-replica-set-size and --min-replica-set-size should only be use with "
                                  "--state stateful")
        if namespace.instance_count is not None:
            namespace.instance_count = int(namespace.instance_count)
    elif service.properties.service_kind.lower() == ServiceKind.STATEFUL.lower():
        if namespace.instance_count:
            raise ValidationError("Unexpected parameter --instance-count should only be use with --state stateless")
        if namespace.target_replica_set_size is not None:
            namespace.target_replica_set_size = int(namespace.target_replica_set_size)
        if namespace.min_replica_set_size is not None:
            namespace.min_replica_set_size = int(namespace.min_replica_set_size)
    else:
        raise ValidationError("Invalid --state '%s': service state is not valid." % service.properties.service_kind)


def validate_create_managed_service_load_metric(cmd, namespace):
    client = servicefabric_managed_client_factory(cmd.cli_ctx)
    service = _safe_get_resource(client.services.get,
                                 (namespace.resource_group_name, namespace.cluster_name,
                                  namespace.application_name, namespace.service_name))

    if service is None:
        raise ValidationError("Service '{}' Not Found.".format(namespace.service_name))
    if service.properties.service_kind.lower() == ServiceKind.STATELESS.lower():
        if namespace.metric_name is None or namespace.weight is None or namespace.default_load is None:
            raise ValidationError("--metric-name, --weight and --default-load are required")
        if namespace.primary_default_load is not None or namespace.secondary_default_load is not None:
            raise ValidationError(
                "--primary-default-load and --secondary-default-load can only be used for stateful services."
            )
        namespace.default_load = int(namespace.default_load)
    elif service.properties.service_kind.lower() == ServiceKind.STATEFUL.lower():
        if namespace.metric_name is None or namespace.weight is None or \
           namespace.primary_default_load is None or namespace.secondary_default_load is None:
            raise ValidationError("--metric-name, --weight, --primary-default-load and "
                                  "--secondary-default-load are required")
        if namespace.default_load is not None:
            raise ValidationError("--default-load can only be used for stateless services.")
        namespace.primary_default_load = int(namespace.primary_default_load)
        namespace.secondary_default_load = int(namespace.secondary_default_load)
    else:
        raise ValidationError("Invalid --state '%s': service state is not valid." % service.properties.service_kind)
    if any(namespace.metric_name == metric.name for metric in service.properties.service_load_metrics):
        raise ValidationError("Duplicate metric names are not allowed: %s." % namespace.metric_name)


def validate_update_managed_service_load_metric(cmd, namespace):
    client = servicefabric_managed_client_factory(cmd.cli_ctx)
    service = _safe_get_resource(client.services.get,
                                 (namespace.resource_group_name, namespace.cluster_name,
                                  namespace.application_name, namespace.service_name))

    if service is None:
        raise CLIError("Service '{}' Not Found.".format(namespace.service_name))
    if service.properties.service_kind.lower() == ServiceKind.STATELESS.lower():
        if namespace.primary_default_load is not None or namespace.secondary_default_load is not None:
            raise ValidationError(
                "--primary-default-load and --secondary-default-load can only be used for stateful services."
            )
        if namespace.default_load is not None:
            namespace.default_load = int(namespace.default_load)
    elif service.properties.service_kind.lower() == ServiceKind.STATEFUL.lower():
        if namespace.default_load is not None:
            raise ValidationError("--default-load can only be used for stateless services.")
        if namespace.primary_default_load is not None:
            namespace.primary_default_load = int(namespace.primary_default_load)
        if namespace.secondary_default_load is not None:
            namespace.secondary_default_load = int(namespace.secondary_default_load)
    else:
        raise ValidationError("Invalid --state '%s': service state is not valid." % service.properties.service_kind)


def validate_create_managed_service_correlation(cmd, namespace):
    client = servicefabric_managed_client_factory(cmd.cli_ctx)
    service = _safe_get_resource(client.services.get,
                                 (namespace.resource_group_name, namespace.cluster_name,
                                  namespace.application_name, namespace.service_name))

    if service is None:
        raise ValidationError("Service '{}' Not Found.".format(namespace.service_name))

    if service.properties.correlation_scheme:
        raise ValidationError("There can only be one service correlation per service.")


def validate_update_managed_service_correlation(cmd, namespace):
    client = servicefabric_managed_client_factory(cmd.cli_ctx)
    service = _safe_get_resource(client.services.get,
                                 (namespace.resource_group_name, namespace.cluster_name,
                                  namespace.application_name, namespace.service_name))

    if service is None:
        raise ValidationError("Service '{}' Not Found.".format(namespace.service_name))


def validate_update_managed_application(cmd, namespace):
    client = servicefabric_managed_client_factory(cmd.cli_ctx)
    app = _safe_get_resource(client.applications.get,
                             (namespace.resource_group_name, namespace.cluster_name, namespace.application_name))
    if app is None:
        raise CLIError("Application '{}' Not Found.".format(namespace.application_name))
    if namespace.application_type_version is not None:
        if app.version.endswith(namespace.application_type_version):
            raise ValidationError("The application '{}' is alrady running with type version '{}'."
                                  .format(app.name, app.version))
        app_type_name = app.version.split("/")[-3]
        type_version = _safe_get_resource(client.application_type_versions.get,
                                          (namespace.resource_group_name,
                                           namespace.cluster_name,
                                           app_type_name,
                                           namespace.application_type_version))
        if type_version is None:
            raise ValidationError("Application type version {}:{} not found. "
                                  "Create the type version before running this command."
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


def validate_create_managed_application(cmd, namespace):
    client = servicefabric_managed_client_factory(cmd.cli_ctx)
    if namespace.package_url is None:
        type_version = _safe_get_resource(client.application_type_versions.get,
                                          (namespace.resource_group_name,
                                           namespace.cluster_name,
                                           namespace.application_type_name,
                                           namespace.application_type_version))
        if type_version is None:
            raise ValidationError("Application type version {}:{} not found. "
                                  "Create the type version before running this "
                                  "command or use --package-url to create it."
                                  .format(namespace.application_type_name, namespace.application_type_version))


# Helpers
def _safe_get_resource(getResourceAction, params):
    try:
        return getResourceAction(*params)
    except CloudError as ex:
        if ex.error.error == 'ResourceNotFound':
            return None
        logger.warning("Unable to get resource, exception: %s", ex)
        raise

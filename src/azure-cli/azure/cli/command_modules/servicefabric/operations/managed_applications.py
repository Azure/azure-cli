# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-lines,too-many-branches,too-many-locals

import time

from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.commands import LongRunningOperation
from azure.mgmt.servicefabricmanagedclusters.models import (ApplicationTypeResource,
                                                            ApplicationTypeVersionResource,
                                                            ApplicationResource,
                                                            ApplicationUpgradePolicy,
                                                            ApplicationHealthPolicy,
                                                            NamedPartitionScheme,
                                                            PartitionScheme,
                                                            RollingUpgradeMonitoringPolicy,
                                                            ServiceCorrelation,
                                                            ServiceLoadMetric,
                                                            ServiceResource,
                                                            StatefulServiceProperties,
                                                            StatelessServiceProperties,
                                                            ServiceTypeHealthPolicy,
                                                            ServiceKind,
                                                            SingletonPartitionScheme,
                                                            UniformInt64RangePartitionScheme)
from azure.cli.command_modules.servicefabric._sf_utils import (add_to_collection,
                                                               _get_managed_cluster_location,
                                                               delete_from_collection,
                                                               find_in_collection,
                                                               update_in_collection)
from knack.log import get_logger

logger = get_logger(__name__)

# Constants
APP_VERSION_ARM_RESOURCE_ID_FORMAT = ("/subscriptions/{subscription}/resourceGroups/{rg}/providers/"
                                      "Microsoft.ServiceFabric/managedclusters/{cluster}/"
                                      "applicationTypes/{appType}/versions/{version}")
CONSIDER_WARNING_AS_ERROR_DEFAULT = False
MAX_PERCENT_UNHEALTHY_DEPLOYED_APPLICATIONS_DEFAULT = 0
FAILURE_ACTION_DEFAULT = "Manual"
HEALTH_CHECK_STABLE_DURATION_DEFAULT = time.strftime('%H:%M:%S', time.gmtime(120))
HEALTH_CHECK_RETRY_TIMEOUT_DEFAULT = time.strftime('%H:%M:%S', time.gmtime(600))
HEALTH_CHECK_WAIT_DURATION_DEFAULT = time.strftime('%H:%M:%S', time.gmtime(0))
_twelve_hours = 43200
UPGRADE_TIMEOUT_DEFAULT = time.strftime('%H:%M:%S', time.gmtime(_twelve_hours))
UPGRADE_DOMAIN_TIMEOUT = time.strftime('%H:%M:%S', time.gmtime(_twelve_hours))
SERVICE_TYPE_UNHEALTHY_SERVICES_MAX_PERCENT_DEFAULT = 0
SERVICE_TYPE_MAX_PERCENT_UNHEALTHY_REPLICAS_PER_PARTITION_DEFAULT = 0
SERVICE_TYPE_MAX_PERCENT_UNHEALTHY_PARTITIONS_PER_SERVICE_DEFAULT = 0


def create_app(cmd,
               client,
               resource_group_name,
               cluster_name,
               application_type_name,
               application_type_version,
               application_name,
               package_url=None,
               application_parameters=None,
               tags=None):
    location = _get_managed_cluster_location(cmd.cli_ctx, resource_group_name, cluster_name)
    if package_url is not None:
        create_app_type_version(cmd, client, resource_group_name, cluster_name, application_type_name, application_type_version, package_url)

    try:
        apps = client.applications.list(resource_group_name, cluster_name)
        for app in apps:
            if app.name.lower() == application_name.lower():
                logger.info("Application '%s' already exists", application_name)
                return app

        new_app_type_version = _format_app_version(cmd.cli_ctx, resource_group_name, cluster_name, application_type_name, application_type_version)
        appResource = ApplicationResource(version=new_app_type_version,
                                          parameters=application_parameters,
                                          location=location,
                                          tags=tags)
        appResource.name = application_name
        poller = client.applications.begin_create_or_update(resource_group_name, cluster_name, application_name, appResource)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_app(cmd,
               client,
               resource_group_name,
               cluster_name,
               application_name,
               application_type_version=None,
               application_parameters=None,
               force_restart=False,
               recreate_application=False,
               upgrade_replica_set_check_timeout=None,
               instance_close_delay_duration=None,
               failure_action=None,
               upgrade_mode=None,
               health_check_retry_timeout=None,
               health_check_wait_duration=None,
               health_check_stable_duration=None,
               upgrade_domain_timeout=None,
               upgrade_timeout=None,
               consider_warning_as_error=False,
               default_service_type_max_percent_unhealthy_partitions_per_service=None,
               default_service_type_max_percent_unhealthy_replicas_per_partition=None,
               default_service_type_max_percent_unhealthy_services=None,
               max_percent_unhealthy_deployed_applications=None,
               service_type_health_policy_map=None,
               tags=None):
    try:
        currentApp = client.applications.get(resource_group_name, cluster_name, application_name)
        appResource = currentApp
        # TODO: change to patch once is supported in the rp
        # appResourceUpdate: ApplicationResourceUpdate = ApplicationResourceUpdate()

        if application_type_version:
            appResource.version = _replace_app_version(appResource.version, application_type_version)
        if application_parameters:
            appResource.parameters.update(application_parameters)
        if tags:
            appResource.tags = tags

        appResource.upgrade_policy = _set_upgrade_policy(currentApp.upgrade_policy,
                                                         force_restart,
                                                         recreate_application,
                                                         upgrade_replica_set_check_timeout,
                                                         instance_close_delay_duration,
                                                         failure_action,
                                                         upgrade_mode,
                                                         health_check_retry_timeout,
                                                         health_check_wait_duration,
                                                         health_check_stable_duration,
                                                         upgrade_domain_timeout,
                                                         upgrade_timeout,
                                                         consider_warning_as_error,
                                                         default_service_type_max_percent_unhealthy_partitions_per_service,
                                                         default_service_type_max_percent_unhealthy_replicas_per_partition,
                                                         default_service_type_max_percent_unhealthy_services,
                                                         max_percent_unhealthy_deployed_applications,
                                                         service_type_health_policy_map)

        # TODO: change to patch once the fix is supported in the rp
        # client.applications.update(resource_group_name, cluster_name, application_name, appResourceUpdate)
        poller = client.applications.begin_create_or_update(resource_group_name, cluster_name, application_name, appResource)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def create_app_type(cmd, client, resource_group_name, cluster_name, application_type_name, tags=None):
    try:
        location = _get_managed_cluster_location(cmd.cli_ctx, resource_group_name, cluster_name)
        appTypes = client.application_types.list(resource_group_name, cluster_name)
        for appType in appTypes:
            if appType.name.lower() == application_type_name.lower():
                logger.info("Application type '%s' already exists", application_type_name)
                return appType

        appTypeResource = ApplicationTypeResource(location=location, tags=tags)
        logger.info("Creating application type '%s'", application_type_name)
        return client.application_types.create_or_update(
            resource_group_name,
            cluster_name,
            application_type_name,
            appTypeResource)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_app_type(client, resource_group_name, cluster_name, application_type_name, tags=None):
    try:
        currentAppType = client.application_types.get(resource_group_name, cluster_name, application_type_name)

        if tags:
            currentAppType.tags = tags
        logger.info("Updating application type '%s'", application_type_name)
        return client.application_types.create_or_update(
            resource_group_name,
            cluster_name,
            application_type_name,
            currentAppType)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def create_app_type_version(cmd,
                            client,
                            resource_group_name,
                            cluster_name,
                            application_type_name,
                            version,
                            package_url,
                            tags=None):
    location = _get_managed_cluster_location(cmd.cli_ctx, resource_group_name, cluster_name)
    create_app_type(cmd, client, resource_group_name, cluster_name, application_type_name)
    try:
        appTypeVerions = client.application_type_versions.list_by_application_types(resource_group_name, cluster_name, application_type_name)
        for appTypeVerion in appTypeVerions:
            if appTypeVerion.name.lower() == version.lower():
                logger.error("Application type version '%s' already exists", version)
                return appTypeVerion

        appTypeVersionResource = ApplicationTypeVersionResource(app_package_url=package_url, location=location, tags=tags)
        logger.info("Creating application type version %s:%s", application_type_name, version)
        poller = client.application_type_versions.begin_create_or_update(resource_group_name,
                                                                         cluster_name,
                                                                         application_type_name,
                                                                         version,
                                                                         appTypeVersionResource)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_app_type_version(client,
                            resource_group_name,
                            cluster_name,
                            application_type_name,
                            version,
                            package_url=None,
                            tags=None):
    try:
        currentAppTypeVersion = client.application_type_versions.get(
            resource_group_name,
            cluster_name,
            application_type_name,
            version)

        if package_url is not None:
            currentAppTypeVersion.app_package_url = package_url

        if tags is not None:
            currentAppTypeVersion.tags = tags

        logger.info("Updating application type version %s:%s", application_type_name, version)
        return client.application_type_versions.begin_create_or_update(resource_group_name,
                                                                       cluster_name,
                                                                       application_type_name,
                                                                       version,
                                                                       currentAppTypeVersion).result()
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def create_service(cmd,
                   client,
                   resource_group_name,
                   cluster_name,
                   application_name,
                   service_name,
                   service_type,
                   state,
                   default_move_cost=None,
                   placement_constraints=None,
                   service_package_activation_mode=None,
                   target_replica_set_size=None,
                   min_replica_set_size=None,
                   has_persisted_state=None,
                   service_placement_time_limit=None,
                   stand_by_replica_keep_duration=None,
                   quorum_loss_wait_duration=None,
                   replica_restart_wait_duration=None,
                   instance_count=None,
                   min_instance_count=None,
                   min_instance_percentage=None,
                   partition_scheme='singleton',
                   partition_count=None,
                   low_key=None,
                   high_key=None,
                   partition_names=None,
                   tags=None):
    try:
        location = _get_managed_cluster_location(cmd.cli_ctx, resource_group_name, cluster_name)
        services = client.services.list_by_applications(resource_group_name, cluster_name, application_name)
        for service in services:
            if service.name.lower() == service_name.lower():
                logger.error("Service '%s' already exists", service_name)
                return service

        serviceResource = ServiceResource(location=location, tags=tags)
        serviceResource.name = service_name

        if state.lower() == ServiceKind.STATELESS.lower():
            properties = StatelessServiceProperties(
                service_type_name=service_type,
                instance_count=instance_count,
                partition_description=_set_partition_description(partition_scheme, partition_names, partition_count, low_key, high_key)
            )
            serviceResource.properties = _set_stateless_service_properties(properties,
                                                                           min_instance_count,
                                                                           min_instance_percentage)

        elif state.lower() == ServiceKind.STATEFUL.lower():
            properties = StatefulServiceProperties(
                service_type_name=service_type,
                instance_count=instance_count,
                partition_description=_set_partition_description(partition_scheme, partition_names, partition_count, low_key, high_key),
                min_replica_set_size=min_replica_set_size,
                target_replica_set_size=target_replica_set_size
            )
            serviceResource.properties = _set_stateful_service_properties(properties,
                                                                          has_persisted_state,
                                                                          service_placement_time_limit,
                                                                          stand_by_replica_keep_duration,
                                                                          quorum_loss_wait_duration,
                                                                          replica_restart_wait_duration)
        else:
            raise InvalidArgumentValueError("Invalid --state '%s': service state is not valid." % state)

        serviceResource.properties.service_load_metrics = []
        serviceResource.properties.correlation_scheme = []

        if default_move_cost is not None:
            serviceResource.properties.default_move_cost = default_move_cost
        if placement_constraints is not None:
            serviceResource.properties.placement_constraints = placement_constraints
        if service_package_activation_mode is not None:
            serviceResource.properties.service_package_activation_mode = service_package_activation_mode

        poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, serviceResource)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_service(cmd,
                   client,
                   resource_group_name,
                   cluster_name,
                   application_name,
                   service_name,
                   default_move_cost=None,
                   placement_constraints=None,
                   target_replica_set_size=None,
                   min_replica_set_size=None,
                   service_placement_time_limit=None,
                   stand_by_replica_keep_duration=None,
                   quorum_loss_wait_duration=None,
                   replica_restart_wait_duration=None,
                   instance_count=None,
                   min_instance_count=None,
                   min_instance_percentage=None,
                   tags=None):
    try:
        currentService = client.services.get(resource_group_name, cluster_name, application_name, service_name)

        state = currentService.properties.service_kind
        logger.info("Updating service '%s'", service_name)

        if tags:
            currentService.tags = tags

        if state.lower() == ServiceKind.STATELESS.lower():
            if instance_count is not None:
                currentService.properties.instance_count = instance_count
            currentService.properties = _set_stateless_service_properties(currentService.properties,
                                                                          min_instance_count,
                                                                          min_instance_percentage)
        elif state.lower() == ServiceKind.STATEFUL.lower():
            if min_replica_set_size is not None:
                currentService.properties.min_replica_set_size = min_replica_set_size
            if target_replica_set_size is not None:
                currentService.properties.target_replica_set_size = target_replica_set_size
            currentService.properties = _set_stateful_service_properties(currentService.properties,
                                                                         None,
                                                                         service_placement_time_limit,
                                                                         stand_by_replica_keep_duration,
                                                                         quorum_loss_wait_duration,
                                                                         replica_restart_wait_duration)
        else:
            raise InvalidArgumentValueError("Invalid --state '%s': service state is not valid." % state)

        if default_move_cost is not None:
            currentService.properties.default_move_cost = default_move_cost
        if placement_constraints is not None:
            currentService.properties.placement_constraints = placement_constraints

        poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, currentService)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def create_service_load_metric(cmd,
                               client,
                               resource_group_name,
                               cluster_name,
                               application_name,
                               service_name,
                               metric_name,
                               weight=None,
                               primary_default_load=None,
                               secondary_default_load=None,
                               default_load=None):

    service = client.services.get(resource_group_name, cluster_name, application_name, service_name)
    new_metric = ServiceLoadMetric(
        name=metric_name,
        weight=weight,
        primary_default_load=primary_default_load,
        secondary_default_load=secondary_default_load,
        default_load=default_load
    )
    # add the new child to the parent collection
    add_to_collection(service.properties, 'service_load_metrics', new_metric, 'name')
    # update the parent object
    poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, service)
    return LongRunningOperation(cmd.cli_ctx)(poller)


def update_service_load_metric(cmd,
                               client,
                               resource_group_name,
                               cluster_name,
                               application_name,
                               service_name,
                               metric_name,
                               weight=None,
                               primary_default_load=None,
                               secondary_default_load=None,
                               default_load=None):

    service = client.services.get(resource_group_name, cluster_name, application_name, service_name)
    existing_metric = find_in_collection(service.properties, 'service_load_metrics', 'name', metric_name)
    if existing_metric is None:
        logger.error('Metric %s does not exist.', metric_name)
        return None

    updated_metric = ServiceLoadMetric(
        name=metric_name,
        weight=weight if weight is not None else existing_metric.weight,
        primary_default_load=primary_default_load if primary_default_load is not None else existing_metric.primary_default_load,
        secondary_default_load=secondary_default_load if secondary_default_load is not None else existing_metric.secondary_default_load,
        default_load=default_load if default_load is not None else existing_metric.default_load,
    )
    # add the new child to the parent collection
    update_in_collection(service.properties, 'service_load_metrics', updated_metric, 'name')
    # update the parent object
    poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, service)
    return LongRunningOperation(cmd.cli_ctx)(poller)


def delete_service_load_metric(cmd,
                               client,
                               resource_group_name,
                               cluster_name,
                               application_name,
                               service_name,
                               metric_name):

    service = client.services.get(resource_group_name, cluster_name, application_name, service_name)

    # add the new child to the parent collection
    delete_from_collection(service.properties, 'service_load_metrics', 'name', metric_name)
    # update the parent object
    poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, service)
    return LongRunningOperation(cmd.cli_ctx)(poller)


def create_service_correlation(cmd,
                               client,
                               resource_group_name,
                               cluster_name,
                               application_name,
                               service_name,
                               scheme,
                               correlated_service_name):

    service = client.services.get(resource_group_name, cluster_name, application_name, service_name)
    new_correlation = ServiceCorrelation(
        service_name=correlated_service_name,
        scheme=scheme
    )
    # add the new child to the parent collection
    add_to_collection(service.properties, 'correlation_scheme', new_correlation, 'service_name')
    # update the parent object
    poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, service)
    return LongRunningOperation(cmd.cli_ctx)(poller)


def update_service_correlation(cmd,
                               client,
                               resource_group_name,
                               cluster_name,
                               application_name,
                               service_name,
                               scheme,
                               correlated_service_name):

    service = client.services.get(resource_group_name, cluster_name, application_name, service_name)
    existing_correlation = find_in_collection(service.properties, 'correlation_scheme', 'service_name', correlated_service_name)
    if existing_correlation is None:
        logger.error('Correlation %s does not exist.', correlated_service_name)
        return None

    updated_correlation = ServiceCorrelation(
        service_name=correlated_service_name,
        scheme=scheme
    )
    # add the new child to the parent collection
    update_in_collection(service.properties, 'correlation_scheme', updated_correlation, 'service_name')
    # update the parent object
    poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, service)
    return LongRunningOperation(cmd.cli_ctx)(poller)


def delete_service_correlation(cmd,
                               client,
                               resource_group_name,
                               cluster_name,
                               application_name,
                               service_name,
                               correlated_service_name):

    service = client.services.get(resource_group_name, cluster_name, application_name, service_name)

    # add the new child to the parent collection
    delete_from_collection(service.properties, 'correlation_scheme', 'service_name', correlated_service_name)
    # update the parent object
    poller = client.services.begin_create_or_update(resource_group_name, cluster_name, application_name, service_name, service)
    return LongRunningOperation(cmd.cli_ctx)(poller)


# Managed application helpers
def _format_app_version(cli_ctx, rg_name, cluster_name, app_type, new_app_version):
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cli_ctx)
    return APP_VERSION_ARM_RESOURCE_ID_FORMAT.format(
        subscription=subscription_id,
        rg=rg_name,
        cluster=cluster_name,
        appType=app_type,
        version=new_app_version
    )


def _replace_app_version(old_app_version, new_app_version):
    split_version_id = old_app_version.rsplit(sep='/', maxsplit=1)
    split_version_id[-1] = new_app_version
    return "/".join(split_version_id)


def _set_service_type_health_policy(service_type_health_policy_map):
    def _policy_string_to_object(value_string):
        try:
            max_percent_unhealthy_partitions_per_service, max_percent_unhealthy_replicas_per_partition, max_percent_unhealthy_services = map(int, value_string.split(","))
        except:
            raise InvalidArgumentValueError("Invalid --service-type-health-policy-map '%s': service type health policy map is not valid." % service_type_health_policy_map)
        return ServiceTypeHealthPolicy(
            max_percent_unhealthy_partitions_per_service=max_percent_unhealthy_partitions_per_service,
            max_percent_unhealthy_replicas_per_partition=max_percent_unhealthy_replicas_per_partition,
            max_percent_unhealthy_services=max_percent_unhealthy_services
        )
    return {k: _policy_string_to_object(v) for k, v in service_type_health_policy_map.items()}


def _set_upgrade_policy(current_upgrade_policy,
                        force_restart,
                        recreate_application,
                        upgrade_replica_set_check_timeout,
                        instance_close_delay_duration,
                        failure_action,
                        upgrade_mode,
                        health_check_retry_timeout,
                        health_check_wait_duration,
                        health_check_stable_duration,
                        upgrade_domain_timeout,
                        upgrade_timeout,
                        consider_warning_as_error,
                        default_service_type_max_percent_unhealthy_partitions_per_service,
                        default_service_type_max_percent_unhealthy_replicas_per_partition,
                        default_service_type_max_percent_unhealthy_services,
                        max_percent_unhealthy_deployed_applications,
                        service_type_health_policy_map):
    if current_upgrade_policy is None:
        current_upgrade_policy = ApplicationUpgradePolicy()

    if force_restart is not None:
        current_upgrade_policy.force_restart = force_restart
    if recreate_application is not None:
        current_upgrade_policy.recreate_application = recreate_application
    if upgrade_mode:
        current_upgrade_policy.upgrade_mode = upgrade_mode
    if upgrade_replica_set_check_timeout is not None:
        current_upgrade_policy.upgrade_replica_set_check_timeout = upgrade_replica_set_check_timeout
    if instance_close_delay_duration is not None:
        current_upgrade_policy.instance_close_delay_duration = instance_close_delay_duration

    # RollingUpgradeMonitoringPolicy
    if current_upgrade_policy.rolling_upgrade_monitoring_policy is None:
        # initialize with defaults
        current_upgrade_policy.rolling_upgrade_monitoring_policy = RollingUpgradeMonitoringPolicy(failure_action=FAILURE_ACTION_DEFAULT,
                                                                                                  health_check_stable_duration=HEALTH_CHECK_STABLE_DURATION_DEFAULT,
                                                                                                  health_check_retry_timeout=HEALTH_CHECK_RETRY_TIMEOUT_DEFAULT,
                                                                                                  health_check_wait_duration=HEALTH_CHECK_WAIT_DURATION_DEFAULT,
                                                                                                  upgrade_timeout=UPGRADE_TIMEOUT_DEFAULT,
                                                                                                  upgrade_domain_timeout=UPGRADE_DOMAIN_TIMEOUT)

    if failure_action:
        current_upgrade_policy.rolling_upgrade_monitoring_policy.failure_action = failure_action
    if health_check_stable_duration is not None:
        current_upgrade_policy.rolling_upgrade_monitoring_policy.health_check_stable_duration = time.strftime('%H:%M:%S', time.gmtime(health_check_stable_duration))
    if health_check_retry_timeout is not None:
        current_upgrade_policy.rolling_upgrade_monitoring_policy.health_check_retry_timeout = time.strftime('%H:%M:%S', time.gmtime(health_check_retry_timeout))
    if health_check_wait_duration is not None:
        current_upgrade_policy.rolling_upgrade_monitoring_policy.health_check_wait_duration = time.strftime('%H:%M:%S', time.gmtime(health_check_wait_duration))
    if upgrade_timeout is not None:
        current_upgrade_policy.rolling_upgrade_monitoring_policy.upgrade_timeout = time.strftime('%H:%M:%S', time.gmtime(upgrade_timeout))
    if upgrade_domain_timeout is not None:
        current_upgrade_policy.rolling_upgrade_monitoring_policy.upgrade_domain_timeout = time.strftime('%H:%M:%S', time.gmtime(upgrade_domain_timeout))

    # ApplicationHealthPolicy
    if current_upgrade_policy.application_health_policy is None:
        current_upgrade_policy.application_health_policy = ApplicationHealthPolicy(
            consider_warning_as_error=CONSIDER_WARNING_AS_ERROR_DEFAULT,
            max_percent_unhealthy_deployed_applications=MAX_PERCENT_UNHEALTHY_DEPLOYED_APPLICATIONS_DEFAULT
        )

    if consider_warning_as_error:
        current_upgrade_policy.application_health_policy.consider_warning_as_error = True

    if current_upgrade_policy.application_health_policy.default_service_type_health_policy is None:
        current_upgrade_policy.application_health_policy.default_service_type_health_policy = ServiceTypeHealthPolicy(
            max_percent_unhealthy_partitions_per_service=SERVICE_TYPE_MAX_PERCENT_UNHEALTHY_PARTITIONS_PER_SERVICE_DEFAULT,
            max_percent_unhealthy_replicas_per_partition=SERVICE_TYPE_MAX_PERCENT_UNHEALTHY_REPLICAS_PER_PARTITION_DEFAULT,
            max_percent_unhealthy_services=SERVICE_TYPE_UNHEALTHY_SERVICES_MAX_PERCENT_DEFAULT)

    if default_service_type_max_percent_unhealthy_partitions_per_service is not None:
        current_upgrade_policy.application_health_policy.default_service_type_health_policy.max_percent_unhealthy_partitions_per_service \
            = default_service_type_max_percent_unhealthy_partitions_per_service
    if default_service_type_max_percent_unhealthy_replicas_per_partition is not None:
        current_upgrade_policy.application_health_policy.default_service_type_health_policy.max_percent_unhealthy_replicas_per_partition \
            = default_service_type_max_percent_unhealthy_replicas_per_partition
    if default_service_type_max_percent_unhealthy_services is not None:
        current_upgrade_policy.application_health_policy.default_service_type_health_policy.max_percent_unhealthy_partitions_per_service \
            = default_service_type_max_percent_unhealthy_services

    if max_percent_unhealthy_deployed_applications is not None:
        current_upgrade_policy.application_health_policy.max_percent_unhealthy_deployed_applications \
            = max_percent_unhealthy_deployed_applications

    if service_type_health_policy_map:
        current_upgrade_policy.application_health_policy.service_type_health_policy_map = _set_service_type_health_policy(service_type_health_policy_map)
    return current_upgrade_policy


def _set_partition_description(partition_scheme, partition_names, partition_count, low_key, high_key):
    partition_description = None
    if partition_scheme.lower() == PartitionScheme.SINGLETON.lower():
        partition_description = SingletonPartitionScheme()
    elif partition_scheme.lower() == PartitionScheme.NAMED.lower():
        partition_description = NamedPartitionScheme(
            names=partition_names
        )
    elif partition_scheme.lower() == PartitionScheme.UNIFORM_INT64_RANGE.lower():
        partition_description = UniformInt64RangePartitionScheme(
            count=partition_count,
            low_key=low_key,
            high_key=high_key
        )
    else:
        raise InvalidArgumentValueError("Invalid --partition-scheme '%s': service partition scheme is not valid." % partition_scheme)
    return partition_description


def _set_stateless_service_properties(properties, min_instance_count, min_instance_percentage):
    # Optional
    if min_instance_count is not None:
        properties.min_instance_count = min_instance_count
    if min_instance_percentage is not None:
        properties.min_instance_percentage = min_instance_percentage
    return properties


def _set_stateful_service_properties(properties,
                                     has_persisted_state,
                                     service_placement_time_limit,
                                     stand_by_replica_keep_duration,
                                     quorum_loss_wait_duration,
                                     replica_restart_wait_duration):
    # Optional
    if has_persisted_state is not None:
        properties.has_persisted_state = has_persisted_state
    if service_placement_time_limit is not None:
        properties.service_placement_time_limit = service_placement_time_limit
    if stand_by_replica_keep_duration is not None:
        properties.stand_by_replica_keep_duration = stand_by_replica_keep_duration
    if quorum_loss_wait_duration is not None:
        properties.quorum_loss_wait_duration = quorum_loss_wait_duration
    if replica_restart_wait_duration is not None:
        properties.replica_restart_wait_duration = replica_restart_wait_duration
    return properties

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-lines

import os
import time

from azure.cli.core.util import get_file_json
from azure.core.exceptions import HttpResponseError
from azure.mgmt.servicefabric.models import (ApplicationTypeResource,
                                             ApplicationTypeVersionResource,
                                             ApplicationResource,
                                             ApplicationUpgradePolicy,
                                             ArmRollingUpgradeMonitoringPolicy,
                                             ArmApplicationHealthPolicy,
                                             ArmServiceTypeHealthPolicy)
from azure.cli.command_modules.servicefabric._arm_deployment_utils import validate_and_deploy_arm_template

from knack.log import get_logger

logger = get_logger(__name__)


def create_app(client,
               resource_group_name,
               cluster_name,
               application_type_name,
               application_type_version,
               application_name,
               package_url=None,
               application_parameters=None,
               minimum_nodes=None,
               maximum_nodes=None):
    if package_url is not None:
        create_app_type_version(client, resource_group_name, cluster_name, application_type_name, application_type_version, package_url)

    try:
        apps = client.applications.list(resource_group_name, cluster_name)
        for app in apps.value:
            if app.name.lower() == application_name.lower():
                logger.info("Application '%s' already exists", application_name)
                return app

        appResource = ApplicationResource(type_name=application_type_name,
                                          type_version=application_type_version,
                                          minimum_nodes=minimum_nodes,
                                          maximum_nodes=maximum_nodes,
                                          parameters=application_parameters)
        appResource.name = application_name
        app = client.applications.begin_create_or_update(resource_group_name, cluster_name, application_name, appResource).result()
        return app
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_app(client,
               resource_group_name,
               cluster_name,
               application_name,
               application_type_version=None,
               application_parameters=None,
               minimum_nodes=None,
               maximum_nodes=None,
               force_restart=False,
               upgrade_replica_set_check_timeout=None,
               failure_action=None,
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
               service_type_health_policy_map=None):
    try:
        currentApp = client.applications.get(resource_group_name, cluster_name, application_name)
        appResource = currentApp
        # TODO: change to patch once the fix is deployed in the rp
        # appResourceUpdate: ApplicationResourceUpdate = ApplicationResourceUpdate()

        if application_type_version:
            appResource.type_version = application_type_version
        if application_parameters:
            appResource.parameters.update(application_parameters)
        if minimum_nodes is not None:
            appResource.minimum_nodes = minimum_nodes
        if maximum_nodes is not None:
            appResource.maximum_nodes = maximum_nodes

        appResource.upgrade_policy = _set_uprade_policy(currentApp.upgrade_policy,
                                                        force_restart,
                                                        upgrade_replica_set_check_timeout,
                                                        failure_action,
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

        # TODO: change to patch once the fix is deployed in the rp
        # client.applications.update(resource_group_name, cluster_name, application_name, appResourceUpdate)
        return client.applications.begin_create_or_update(resource_group_name, cluster_name, application_name, appResource).result()
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def create_app_type(client, resource_group_name, cluster_name, application_type_name):
    try:
        appTypes = client.application_types.list(resource_group_name, cluster_name)
        for appType in appTypes.value:
            if appType.name.lower() == application_type_name.lower():
                logger.info("Application type '%s' already exists", application_type_name)
                return appType

        appTypeResource = ApplicationTypeResource()
        logger.info("Creating application type '%s'", application_type_name)
        return client.application_types.create_or_update(resource_group_name, cluster_name, application_type_name, appTypeResource)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def create_app_type_version(client,
                            resource_group_name,
                            cluster_name,
                            application_type_name,
                            version,
                            package_url):
    create_app_type(client, resource_group_name, cluster_name, application_type_name)
    try:
        appTypeVerions = client.application_type_versions.list(resource_group_name, cluster_name, application_type_name)
        for appTypeVerion in appTypeVerions.value:
            if appTypeVerion.name.lower() == version.lower():
                logger.info("Application type version '%s' already exists", version)
                return appTypeVerion

        appTypeVersionResource = ApplicationTypeVersionResource(app_package_url=package_url)
        logger.info("Creating application type version %s:%s", application_type_name, version)
        return client.application_type_versions.begin_create_or_update(resource_group_name,
                                                                       cluster_name,
                                                                       application_type_name,
                                                                       version,
                                                                       appTypeVersionResource).result()
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
                   instance_count=None,
                   target_replica_set_size=None,
                   min_replica_set_size=None,
                   default_move_cost=None,
                   partition_scheme='singleton'):
    parameter_file, template_file = _get_template_file_and_parameters_file()
    template = get_file_json(template_file)
    parameters = get_file_json(parameter_file)['parameters']

    # set params
    _set_parameters(parameters, "clusterName", cluster_name)
    _set_parameters(parameters, "applicationName", application_name)
    _set_parameters(parameters, "serviceName", service_name)

    _set_service_parameters(template, parameters, "serviceTypeName", service_type, "string")

    if partition_scheme == 'singleton':
        _set_service_parameters(template, parameters, "partitionDescription", {"partitionScheme": "Singleton"}, "object")
    elif partition_scheme == 'uniformInt64':
        _set_service_parameters(template, parameters, "partitionDescription", {"partitionScheme": "UniformInt64Range"}, "object")
    elif partition_scheme == 'named':
        _set_service_parameters(template, parameters, "partitionDescription", {"partitionScheme": "Named"}, "object")

    if state == 'stateless':
        _set_service_parameters(template, parameters, "instanceCount", int(instance_count), "int")
    else:
        _set_service_parameters(template, parameters, "targetReplicaSetSize", int(target_replica_set_size), "int")
        _set_service_parameters(template, parameters, "minReplicaSetSize", int(min_replica_set_size), "int")

    if default_move_cost:
        _set_service_parameters(template, parameters, "defaultMoveCost", default_move_cost, "string")

    validate_and_deploy_arm_template(cmd, resource_group_name, template, parameters)

    return client.services.get(resource_group_name, cluster_name, application_name, service_name)


def _get_template_file_and_parameters_file():
    script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    template_parameter_folder = os.path.join('template', 'service')
    parameter_file = os.path.join(
        script_dir, template_parameter_folder, 'parameter.json')
    template_file = os.path.join(
        script_dir, template_parameter_folder, 'template.json')
    return parameter_file, template_file


def _set_service_parameters(template, parameters, name, value, param_type):
    tempalte_parameters = template['parameters']
    if name not in tempalte_parameters:
        tempalte_parameters[name] = {}
    tempalte_parameters[name]["type"] = param_type
    tempalte_resources_properties = template['resources'][0]['properties']
    tempalte_resources_properties[name] = "[parameters('{}')]".format(name)
    _set_parameters(parameters, name, value)


def _set_parameters(parameters, name, value):
    if name not in parameters:
        parameters[name] = {}
    parameters[name]["value"] = value


def _set_uprade_policy(current_upgrade_policy,
                       force_restart,
                       upgrade_replica_set_check_timeout,
                       failure_action,
                       health_check_retry_timeout,
                       health_check_wait_duration,
                       health_check_stable_duration,
                       upgrade_domain_timeout,
                       upgrade_timeout,
                       consider_warning_as_error,
                       default_service_type_max_percent_unhealthy_partitions_per_service,
                       default_service_type_max_percent_unhealthy_replicas_per_partition,
                       default_max_percent_service_type_unhealthy_services,
                       max_percent_unhealthy_deployed_applications,
                       service_type_health_policy_map):
    if current_upgrade_policy is None:
        current_upgrade_policy = ApplicationUpgradePolicy()

    if force_restart:
        current_upgrade_policy.force_restart = force_restart
    if upgrade_replica_set_check_timeout is not None:
        current_upgrade_policy.upgrade_replica_set_check_timeout = time.strftime('%H:%M:%S', time.gmtime(upgrade_replica_set_check_timeout))

    # RollingUpgradeMonitoringPolicy
    if current_upgrade_policy.rolling_upgrade_monitoring_policy is None:
        # initialize with defaults
        current_upgrade_policy.rolling_upgrade_monitoring_policy \
            = ArmRollingUpgradeMonitoringPolicy(failure_action='Manual',
                                                health_check_stable_duration=time.strftime('%H:%M:%S', time.gmtime(120)),
                                                health_check_retry_timeout=time.strftime('%H:%M:%S', time.gmtime(600)),
                                                health_check_wait_duration=time.strftime('%H:%M:%S', time.gmtime(0)),
                                                upgrade_timeout=time.strftime('%H:%M:%S', time.gmtime(86399)),
                                                upgrade_domain_timeout=time.strftime('%H:%M:%S', time.gmtime(86399)))

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
        current_upgrade_policy.application_health_policy = ArmApplicationHealthPolicy()

    if consider_warning_as_error:
        current_upgrade_policy.application_health_policy.consider_warning_as_error = True

    if current_upgrade_policy.application_health_policy.default_service_type_health_policy is None:
        current_upgrade_policy.application_health_policy.default_service_type_health_policy = ArmServiceTypeHealthPolicy(
            max_percent_unhealthy_partitions_per_service=default_service_type_max_percent_unhealthy_partitions_per_service,
            max_percent_unhealthy_replicas_per_partition=default_service_type_max_percent_unhealthy_replicas_per_partition,
            max_percent_unhealthy_services=default_max_percent_service_type_unhealthy_services)
    else:
        if default_service_type_max_percent_unhealthy_partitions_per_service:
            current_upgrade_policy.application_health_policy.default_service_type_health_policy .max_percent_unhealthy_partitions_per_service \
                = default_service_type_max_percent_unhealthy_partitions_per_service
        if default_service_type_max_percent_unhealthy_replicas_per_partition:
            current_upgrade_policy.application_health_policy.default_service_type_health_policy.max_percent_unhealthy_replicas_per_partition \
                = default_service_type_max_percent_unhealthy_replicas_per_partition
        if default_max_percent_service_type_unhealthy_services:
            current_upgrade_policy.application_health_policy.default_service_type_health_policy.max_percent_unhealthy_partitions_per_service \
                = default_max_percent_service_type_unhealthy_services

    if max_percent_unhealthy_deployed_applications:
        current_upgrade_policy.ApplicationHealthPolicy.max_percent_unhealthy_deployed_applications \
            = max_percent_unhealthy_deployed_applications

    if service_type_health_policy_map:
        current_upgrade_policy.application_health_policy.service_type_health_policy_map = service_type_health_policy_map
    return current_upgrade_policy

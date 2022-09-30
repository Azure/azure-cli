# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _resource_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def _resource_feature_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_FEATURES)


def _resource_policy_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_POLICY)


def _resource_lock_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_LOCKS)


def _resource_links_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_LINKS)


def _resource_deploymentscripts_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_DEPLOYMENTSCRIPTS)


def _authorization_management_client(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)


def _resource_managedapps_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.managedapplications import ApplicationClient
    return get_mgmt_service_client(cli_ctx, ApplicationClient)


def _resource_managementgroups_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.managementgroups import ManagementGroupsAPI
    return get_mgmt_service_client(cli_ctx, ManagementGroupsAPI, subscription_bound=False)


def _resource_templatespecs_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS)


def _resource_privatelinks_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_PRIVATELINKS)


def cf_resource_groups(cli_ctx, _):
    return _resource_client_factory(cli_ctx).resource_groups


def cf_resources(cli_ctx, _):
    return _resource_client_factory(cli_ctx).resources


def cf_providers(cli_ctx, _):
    return _resource_client_factory(cli_ctx).providers


def cf_tags(cli_ctx, _):
    return _resource_client_factory(cli_ctx).tags


def cf_deployments(cli_ctx, _):
    return _resource_client_factory(cli_ctx).deployments


def cf_deployment_operations(cli_ctx, _):
    return _resource_client_factory(cli_ctx).deployment_operations


def cf_features(cli_ctx, _):
    return _resource_feature_client_factory(cli_ctx).features


def cf_feature_registrations(cli_ctx, _):
    return _resource_feature_client_factory(cli_ctx).subscription_feature_registrations


def cf_policy_definitions(cli_ctx, _):
    return _resource_policy_client_factory(cli_ctx).policy_definitions


def cf_policy_set_definitions(cli_ctx, _):
    return _resource_policy_client_factory(cli_ctx).policy_set_definitions


def cf_policy_exemptions(cli_ctx, _):
    return _resource_policy_client_factory(cli_ctx).policy_exemptions


def cf_management_locks(cli_ctx, _):
    return _resource_lock_client_factory(cli_ctx).management_locks


def cf_resource_links(cli_ctx, _):
    return _resource_links_client_factory(cli_ctx).resource_links


def cf_resource_deploymentscripts(cli_ctx, _):
    return _resource_deploymentscripts_client_factory(cli_ctx).deployment_scripts


def cf_resource_managedapplications(cli_ctx, _):
    return _resource_managedapps_client_factory(cli_ctx).applications


def cf_resource_managedappdefinitions(cli_ctx, _):
    return _resource_managedapps_client_factory(cli_ctx).application_definitions


def cf_management_groups_mixin(cli_ctx, _):
    return _resource_managementgroups_client_factory(cli_ctx)


def cf_management_groups(cli_ctx, _):
    return _resource_managementgroups_client_factory(cli_ctx).management_groups


def cf_management_group_subscriptions(cli_ctx, _):
    return _resource_managementgroups_client_factory(cli_ctx).management_group_subscriptions


def cf_management_group_entities(cli_ctx, _):
    return _resource_managementgroups_client_factory(cli_ctx).entities


def cf_hierarchy_settings(cli_ctx, _):
    return _resource_managementgroups_client_factory(cli_ctx).hierarchy_settings


def cf_resource_templatespecs(cli_ctx, _):
    return _resource_templatespecs_client_factory(cli_ctx).template_specs


def cf_resource_privatelinkassociations(cli_ctx, _):
    return _resource_privatelinks_client_factory(cli_ctx).private_link_association


def cf_resource_resourcemanagementprivatelinks(cli_ctx, _):
    return _resource_privatelinks_client_factory(cli_ctx).resource_management_private_link

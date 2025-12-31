# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _compute_client_factory(cli_ctx, **kwargs):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE,
                                   subscription_id=kwargs.get('subscription_id'),
                                   aux_subscriptions=kwargs.get('aux_subscriptions'))


def cf_vm(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machines


def cf_vm_ext(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machine_extensions


def cf_vm_ext_image(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machine_extension_images


def cf_vm_image(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machine_images


def cf_vm_image_term(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.marketplaceordering import MarketplaceOrderingAgreements
    market_place_client = get_mgmt_service_client(cli_ctx, MarketplaceOrderingAgreements)
    return market_place_client.marketplace_agreements


def cf_usage(cli_ctx, _):
    return _compute_client_factory(cli_ctx).usage


def cf_vmss(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machine_scale_sets


def cf_vmss_vm(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machine_scale_set_vms


def cf_vm_sizes(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machine_sizes


def cf_disks(cli_ctx, _):
    return _compute_client_factory(cli_ctx).disks


def cf_snapshots(cli_ctx, _):
    return _compute_client_factory(cli_ctx).snapshots


def cf_disk_accesses(cli_ctx, _):
    return _compute_client_factory(cli_ctx).disk_accesses


def cf_images(cli_ctx, _):
    return _compute_client_factory(cli_ctx).images


def cf_rolling_upgrade_commands(cli_ctx, _):
    return _compute_client_factory(cli_ctx).virtual_machine_scale_set_rolling_upgrades


def cf_galleries(cli_ctx, _):
    return _compute_client_factory(cli_ctx).galleries


def cf_gallery_images(cli_ctx, _):
    return _compute_client_factory(cli_ctx).gallery_images


def cf_gallery_image_versions(cli_ctx, _):
    return _compute_client_factory(cli_ctx).gallery_image_versions


def cf_proximity_placement_groups(cli_ctx, _):
    return _compute_client_factory(cli_ctx).proximity_placement_groups


def cf_dedicated_hosts(cli_ctx, _):
    return _compute_client_factory(cli_ctx).dedicated_hosts


def cf_dedicated_host_groups(cli_ctx, _):
    return _compute_client_factory(cli_ctx).dedicated_host_groups


def _log_analytics_client_factory(cli_ctx, subscription_id, *_):
    from azure.mgmt.loganalytics import LogAnalyticsManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, LogAnalyticsManagementClient, subscription_id=subscription_id)


def cf_log_analytics(cli_ctx, subscription_id, *_):
    return _log_analytics_client_factory(cli_ctx, subscription_id)


def cf_log_analytics_data_sources(cli_ctx, subscription_id, *_):
    return _log_analytics_client_factory(cli_ctx, subscription_id).data_sources


def cf_log_analytics_data_plane(cli_ctx, _):
    """Initialize Log Analytics data client for use with CLI."""
    from azure.monitor.query import LogsQueryClient
    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, _ = profile.get_login_credentials()
    api_version = 'v1'
    return LogsQueryClient(cred, endpoint=cli_ctx.cloud.endpoints.log_analytics_resource_id + '/' + api_version,
                           audience=cli_ctx.cloud.endpoints.log_analytics_resource_id)


def cf_vm_cl(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.compute import ComputeManagementClient
    return get_mgmt_service_client(cli_ctx,
                                   ComputeManagementClient)


def cf_shared_galleries(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).shared_galleries


def cf_shared_gallery_image(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).shared_gallery_images


def cf_shared_gallery_image_version(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).shared_gallery_image_versions


def cf_community_gallery(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).community_galleries


def cf_community_gallery_image(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).community_gallery_images


def cf_community_gallery_image_version(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).community_gallery_image_versions


def cf_capacity_reservation_groups(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).capacity_reservation_groups


def cf_capacity_reservations(cli_ctx, *_):
    return cf_vm_cl(cli_ctx).capacity_reservations

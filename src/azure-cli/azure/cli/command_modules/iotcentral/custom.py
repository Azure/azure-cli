# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.mgmt.iotcentral.models import (AppSkuInfo,
                                          App)

from ._client_factory import resource_service_factory

logger = get_logger(__name__)


def iotcentral_app_create(
        cmd, client, app_name, resource_group_name, subdomain, sku="ST2",
        location=None, template=None, display_name=None
):
    cli_ctx = cmd.cli_ctx
    location = _ensure_location(cli_ctx, resource_group_name, location)
    display_name = _ensure_display_name(app_name, display_name)
    appSku = AppSkuInfo(name=sku)

    app = App(subdomain=subdomain,
              location=location,
              display_name=display_name,
              sku=appSku,
              template=template)

    createResult = client.apps.create_or_update(
        resource_group_name, app_name, app)
    return createResult


def iotcentral_app_get(client, app_name, resource_group_name=None):
    if resource_group_name is None:
        return _get_iotcentral_app_by_name(client, app_name)
    return client.apps.get(resource_group_name, app_name)


def iotcentral_app_delete(client, app_name, resource_group_name):
    return client.apps.delete(resource_group_name, app_name)


def iotcentral_app_list(client, resource_group_name=None):
    if resource_group_name is None:
        return client.apps.list_by_subscription()
    return client.apps.list_by_resource_group(resource_group_name)


def iotcentral_app_update(client, app_name, parameters, resource_group_name):
    etag = parameters.additional_properties['etag']
    return client.apps.update(resource_group_name, app_name, parameters, {'IF-MATCH': etag})


def _ensure_location(cli_ctx, resource_group_name, location):
    """Check to see if a location was provided. If not,
        fall back to the resource group location.
    :param object cli_ctx: CLI Context
    :param str resource_group_name: Resource group name
    :param str location: Location to create the resource
    """
    if location is None:
        resource_group_client = resource_service_factory(
            cli_ctx).resource_groups
        return resource_group_client.get(resource_group_name).location
    return location


def _ensure_display_name(app_name, display_name):
    if not display_name or display_name.isspace():
        return app_name
    return display_name


def _get_iotcentral_app_by_name(client, app_name):
    """Search the current subscription for an app with the given name.
    :param object client: IoTCentralClient
    :param str app_name: App name to search for
    """
    all_apps = iotcentral_app_list(client)
    if all_apps is None:
        raise CLIError(
            "No IoT Central application found in current subscription.")
    try:
        target_app = next(
            x for x in all_apps if app_name.lower() == x.name.lower())
    except StopIteration:
        raise CLIError(
            "No IoT Central application found with name {} in current subscription.".format(app_name))
    return target_app

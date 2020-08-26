# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._client_factory import web_client_factory


MSI_LOCAL_ID = '[system]'


def _generic_site_operation(cli_ctx, resource_group_name, name, operation_name, slot=None,
                            extra_parameter=None, client=None, api_version=None):
    # api_version was added to support targeting a specific API
    # Based on get_appconfig_service_client example
    client = client or web_client_factory(cli_ctx, api_version=api_version)
    operation = getattr(client.web_apps,
                        operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return (operation(resource_group_name, name)
                if extra_parameter is None else operation(resource_group_name,
                                                          name, extra_parameter))

    return (operation(resource_group_name, name, slot)
            if extra_parameter is None else operation(resource_group_name,
                                                      name, extra_parameter, slot))

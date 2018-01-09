# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._client_factory import web_client_factory


def _generic_site_operation(cli_ctx, resource_group_name, name, operation_name, slot=None,
                            extra_parameter=None, client=None):
    client = client or web_client_factory(cli_ctx)
    operation = getattr(client.web_apps,
                        operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return (operation(resource_group_name, name)
                if extra_parameter is None else operation(resource_group_name,
                                                          name, extra_parameter))

    return (operation(resource_group_name, name, slot)
            if extra_parameter is None else operation(resource_group_name,
                                                      name, extra_parameter, slot))

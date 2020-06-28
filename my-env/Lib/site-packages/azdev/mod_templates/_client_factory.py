# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def cf_{{ name }}(cli_ctx, *_):
{% if client_name %}
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from {{ sdk_path }} import {{ client_name }}
    return get_mgmt_service_client(cli_ctx, {{ client_name }})
{% else %}
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    # TODO: Replace CONTOSO with the appropriate label and uncomment
    # from azure.mgmt.CONTOSO import CONTOSOManagementClient
    # return get_mgmt_service_client(cli_ctx, CONTOSOManagementClient)
    return None
{% endif %}
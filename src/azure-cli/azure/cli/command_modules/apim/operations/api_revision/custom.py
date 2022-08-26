# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.util import sdk_no_wait
from azure.cli.command_modules.apim.operations.api.custom import create_api
from azure.mgmt.apimanagement.models import ApiCreateOrUpdateParameter


def list_api_revision(client, resource_group_name, service_name, api_id):
    """Lists all revisions of an API."""
    return client.list_by_service(resource_group_name, service_name, api_id)


def create_api_revision(cmd, resource_group_name, service_name, api_id, api_revision, api_revision_description=None, no_wait=False):
    """Creates a new API Revision. """
    from azure.cli.command_modules.apim._client_factory import cf_api
    api_client = cf_api(cmd.cli_ctx)

    cur_api = api_client.get(resource_group_name, service_name, api_id)
    resource = ApiCreateOrUpdateParameter(
        path=cur_api.path,
        display_name=cur_api.display_name,
        service_url=cur_api.service_url,
        authentication_settings=cur_api.authentication_settings,
        protocols=cur_api.protocols,
        subscription_key_parameter_names=cur_api.subscription_key_parameter_names,
        api_revision_description=api_revision_description,
        source_api_id="/apis/" + api_id
    )

    return sdk_no_wait(no_wait, api_client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       service_name=service_name,
                       api_id=api_id + ";rev=" + api_revision,
                       parameters=resource
            )

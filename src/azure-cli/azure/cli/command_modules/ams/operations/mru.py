# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=redefined-builtin

import json
import requests
from azure.cli.core.util import CLIError
from azure.cli.command_modules.ams._completers import get_mru_type_completion_list
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.azclierror import BadRequestError

_rut_dict = {0: 'S1',
             1: 'S2',
             2: 'S3'}


def get_mru(client, cmd, resource_group_name, account_name):
    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)
    if account_info.encryption:
        raise BadRequestError('The media reserved unit operation failed as the Media Services account was created'
                              ' with the 2020-05-01 version of the API or later. Accounts created this way no'
                              ' longer need to set media reserved units as the system will automatically'
                              ' scale up and down based on load.')
    mru = MediaV2Client(cmd.cli_ctx, resource_group_name, account_name).get_mru()
    return _map_mru(mru)


def set_mru(client, cmd, resource_group_name, account_name, count=None, type=None):
    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)
    if account_info.encryption:
        raise BadRequestError('The media reserved unit operation failed as the Media Services account was created'
                              ' with the 2020-05-01 version of the API or later. Accounts created this way no'
                              ' longer need to set media reserved units as the system will automatically'
                              ' scale up and down based on load.')
    client = MediaV2Client(cmd.cli_ctx, resource_group_name, account_name)
    mru = client.get_mru()

    count = count if count is not None else int(mru['CurrentReservedUnits'])

    if type is None:
        type = int(mru['ReservedUnitType'])
    else:
        try:
            type = int(list(_rut_dict.keys())[list(_rut_dict.values()).index(type)])
        except:
            raise CLIError(
                'Invalid --type argument. Allowed values: {}.'.format(", ".join(get_mru_type_completion_list())))

    client.set_mru(mru['AccountId'], count, type)
    return _map_mru(client.get_mru())


def _map_mru(mru):
    mapped_obj = {}
    mapped_obj['count'] = mru['CurrentReservedUnits']
    mapped_obj['type'] = _rut_dict[mru['ReservedUnitType']]
    return mapped_obj


class MediaV2Client():
    """ Media V2 Client """
    def __init__(self, cli_ctx, resource_group_name, account_name):
        from azure.cli.core._profile import Profile
        self.profile = Profile(cli_ctx=cli_ctx)
        self._old_rp_api_version = '2015-10-01'
        self.v2_media_api_resource = cli_ctx.cloud.endpoints.media_resource_id
        self.api_endpoint = self._get_v2_api_endpoint(cli_ctx, resource_group_name, account_name)
        self.access_token = self._get_v2_access_token()

    def _get_v2_api_endpoint(self, cli_ctx, resource_group_name, account_name):
        from msrestazure.tools import resource_id
        from azure.cli.command_modules.ams._sdk_utils import (get_media_namespace, get_media_type)

        access_token = self.profile.get_raw_token()[0][2].get('accessToken')

        media_old_rp_url = resource_id(subscription=get_subscription_id(cli_ctx),
                                       resource_group=resource_group_name,
                                       namespace=get_media_namespace(), type=get_media_type(),
                                       name=account_name) + '?api-version={}'.format(self._old_rp_api_version)

        media_service_res = requests.get(cli_ctx.cloud.endpoints.resource_manager.rstrip('/') + media_old_rp_url,
                                         headers={'Authorization': 'Bearer {}'.format(access_token)})
        if not media_service_res.ok:
            err_info = 'Request to 2015-10-01 Media API failed.'
            res_text = json.loads(media_service_res.text)
            if res_text is not None and res_text.get('error') is not None:
                err_info = res_text.get('error').get('message')
            raise CLIError(err_info)

        media_service = media_service_res.json()
        api_endpoints = media_service.get('properties').get('apiEndpoints')
        api_endpoint = next((x for x in api_endpoints if x.get('majorVersion') == '2'), api_endpoints[0])
        if not api_endpoint:
            raise CLIError('v2 Media API endpoint was not found.')
        return api_endpoint

    def _get_v2_access_token(self):
        # pylint: disable=protected-access
        access_token = self.profile.get_raw_token(resource=self.v2_media_api_resource)[0][2].get('accessToken')
        return access_token

    def set_mru(self, account_id, count, type):
        headers = {}
        headers['Authorization'] = 'Bearer {}'.format(self.access_token)
        headers['Content-Type'] = 'application/json;odata=verbose'
        headers['Accept'] = 'application/json;odata=verbose'

        url_request_template = "{}EncodingReservedUnitTypes(guid'{}')?api-version=2.19"
        response = requests.put(url_request_template.format(self.api_endpoint.get('endpoint'), account_id),
                                headers=headers,
                                data='{{"ReservedUnitType":{}, "CurrentReservedUnits":{}}}'.format(type, count))

        if not response.ok:
            err_info = 'No error information available'
            if json.loads(response.text) is not None and json.loads(response.text).get('error') is not None:
                err_info = json.loads(response.text).get('error').get('message').get('value')
            raise CLIError('Request to EncodingReservedUnitTypes v2 API endpoint failed. ' + err_info)

    def get_mru(self):
        headers = {}
        headers['Authorization'] = 'Bearer {}'.format(self.access_token)
        headers['Content-Type'] = 'application/json;odata=minimalmetadata'
        headers['Accept'] = 'application/json;odata=minimalmetadata'
        headers['Accept-Charset'] = 'UTF-8'

        url_request_template = '{}EncodingReservedUnitTypes?api-version=2.19'
        response = requests.get(url_request_template.format(self.api_endpoint.get('endpoint')),
                                headers=headers)
        if not response.ok:
            raise CLIError('Request to EncodingReservedUnitTypes v2 API endpoint failed.')
        return response.json().get('value')[0]

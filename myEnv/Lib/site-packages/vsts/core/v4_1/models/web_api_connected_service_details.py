# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .web_api_connected_service_ref import WebApiConnectedServiceRef


class WebApiConnectedServiceDetails(WebApiConnectedServiceRef):
    """WebApiConnectedServiceDetails.

    :param id:
    :type id: str
    :param url:
    :type url: str
    :param connected_service_meta_data: Meta data for service connection
    :type connected_service_meta_data: :class:`WebApiConnectedService <core.v4_1.models.WebApiConnectedService>`
    :param credentials_xml: Credential info
    :type credentials_xml: str
    :param end_point: Optional uri to connect directly to the service such as https://windows.azure.com
    :type end_point: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'connected_service_meta_data': {'key': 'connectedServiceMetaData', 'type': 'WebApiConnectedService'},
        'credentials_xml': {'key': 'credentialsXml', 'type': 'str'},
        'end_point': {'key': 'endPoint', 'type': 'str'}
    }

    def __init__(self, id=None, url=None, connected_service_meta_data=None, credentials_xml=None, end_point=None):
        super(WebApiConnectedServiceDetails, self).__init__(id=id, url=url)
        self.connected_service_meta_data = connected_service_meta_data
        self.credentials_xml = credentials_xml
        self.end_point = end_point

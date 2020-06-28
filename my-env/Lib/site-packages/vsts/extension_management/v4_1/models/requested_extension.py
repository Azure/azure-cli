# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RequestedExtension(Model):
    """RequestedExtension.

    :param extension_name: The unique name of the extension
    :type extension_name: str
    :param extension_requests: A list of each request for the extension
    :type extension_requests: list of :class:`ExtensionRequest <extension-management.v4_1.models.ExtensionRequest>`
    :param publisher_display_name: DisplayName of the publisher that owns the extension being published.
    :type publisher_display_name: str
    :param publisher_name: Represents the Publisher of the requested extension
    :type publisher_name: str
    :param request_count: The total number of requests for an extension
    :type request_count: int
    """

    _attribute_map = {
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'extension_requests': {'key': 'extensionRequests', 'type': '[ExtensionRequest]'},
        'publisher_display_name': {'key': 'publisherDisplayName', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'request_count': {'key': 'requestCount', 'type': 'int'}
    }

    def __init__(self, extension_name=None, extension_requests=None, publisher_display_name=None, publisher_name=None, request_count=None):
        super(RequestedExtension, self).__init__()
        self.extension_name = extension_name
        self.extension_requests = extension_requests
        self.publisher_display_name = publisher_display_name
        self.publisher_name = publisher_name
        self.request_count = request_count

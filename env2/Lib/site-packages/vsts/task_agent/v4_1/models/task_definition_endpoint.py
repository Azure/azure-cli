# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskDefinitionEndpoint(Model):
    """TaskDefinitionEndpoint.

    :param connection_id: An ID that identifies a service connection to be used for authenticating endpoint requests.
    :type connection_id: str
    :param key_selector: An Json based keyselector to filter response returned by fetching the endpoint <c>Url</c>.A Json based keyselector must be prefixed with "jsonpath:". KeySelector can be used to specify the filter to get the keys for the values specified with Selector. <example> The following keyselector defines an Json for extracting nodes named 'ServiceName'. <code> endpoint.KeySelector = "jsonpath://ServiceName"; </code></example>
    :type key_selector: str
    :param scope: The scope as understood by Connected Services. Essentialy, a project-id for now.
    :type scope: str
    :param selector: An XPath/Json based selector to filter response returned by fetching the endpoint <c>Url</c>. An XPath based selector must be prefixed with the string "xpath:". A Json based selector must be prefixed with "jsonpath:". <example> The following selector defines an XPath for extracting nodes named 'ServiceName'. <code> endpoint.Selector = "xpath://ServiceName"; </code></example>
    :type selector: str
    :param task_id: TaskId that this endpoint belongs to.
    :type task_id: str
    :param url: URL to GET.
    :type url: str
    """

    _attribute_map = {
        'connection_id': {'key': 'connectionId', 'type': 'str'},
        'key_selector': {'key': 'keySelector', 'type': 'str'},
        'scope': {'key': 'scope', 'type': 'str'},
        'selector': {'key': 'selector', 'type': 'str'},
        'task_id': {'key': 'taskId', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, connection_id=None, key_selector=None, scope=None, selector=None, task_id=None, url=None):
        super(TaskDefinitionEndpoint, self).__init__()
        self.connection_id = connection_id
        self.key_selector = key_selector
        self.scope = scope
        self.selector = selector
        self.task_id = task_id
        self.url = url

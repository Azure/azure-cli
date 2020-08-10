# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublishersQuery(Model):
    """PublishersQuery.

    :param publisher_ids: Optional list of publisher ids to restrict the results to
    :type publisher_ids: list of str
    :param publisher_inputs: Filter for publisher inputs
    :type publisher_inputs: dict
    :param results: Results from the query
    :type results: list of :class:`Publisher <service-hooks.v4_1.models.Publisher>`
    """

    _attribute_map = {
        'publisher_ids': {'key': 'publisherIds', 'type': '[str]'},
        'publisher_inputs': {'key': 'publisherInputs', 'type': '{str}'},
        'results': {'key': 'results', 'type': '[Publisher]'}
    }

    def __init__(self, publisher_ids=None, publisher_inputs=None, results=None):
        super(PublishersQuery, self).__init__()
        self.publisher_ids = publisher_ids
        self.publisher_inputs = publisher_inputs
        self.results = results

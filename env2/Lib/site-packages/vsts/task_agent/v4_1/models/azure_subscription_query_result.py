# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AzureSubscriptionQueryResult(Model):
    """AzureSubscriptionQueryResult.

    :param error_message:
    :type error_message: str
    :param value:
    :type value: list of :class:`AzureSubscription <task-agent.v4_1.models.AzureSubscription>`
    """

    _attribute_map = {
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'value': {'key': 'value', 'type': '[AzureSubscription]'}
    }

    def __init__(self, error_message=None, value=None):
        super(AzureSubscriptionQueryResult, self).__init__()
        self.error_message = error_message
        self.value = value

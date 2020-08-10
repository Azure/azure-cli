# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DtlEnvironmentDetails(Model):
    """DtlEnvironmentDetails.

    :param csm_content:
    :type csm_content: str
    :param csm_parameters:
    :type csm_parameters: str
    :param subscription_name:
    :type subscription_name: str
    """

    _attribute_map = {
        'csm_content': {'key': 'csmContent', 'type': 'str'},
        'csm_parameters': {'key': 'csmParameters', 'type': 'str'},
        'subscription_name': {'key': 'subscriptionName', 'type': 'str'}
    }

    def __init__(self, csm_content=None, csm_parameters=None, subscription_name=None):
        super(DtlEnvironmentDetails, self).__init__()
        self.csm_content = csm_content
        self.csm_parameters = csm_parameters
        self.subscription_name = subscription_name

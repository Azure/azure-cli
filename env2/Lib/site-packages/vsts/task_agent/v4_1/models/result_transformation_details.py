# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResultTransformationDetails(Model):
    """ResultTransformationDetails.

    :param result_template:
    :type result_template: str
    """

    _attribute_map = {
        'result_template': {'key': 'resultTemplate', 'type': 'str'}
    }

    def __init__(self, result_template=None):
        super(ResultTransformationDetails, self).__init__()
        self.result_template = result_template

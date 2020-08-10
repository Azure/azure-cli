# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeTemplate(Model):
    """WorkItemTypeTemplate.

    :param template:
    :type template: str
    """

    _attribute_map = {
        'template': {'key': 'template', 'type': 'str'}
    }

    def __init__(self, template=None):
        super(WorkItemTypeTemplate, self).__init__()
        self.template = template

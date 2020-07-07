# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeTemplateUpdateModel(Model):
    """WorkItemTypeTemplateUpdateModel.

    :param action_type: Describes the type of the action for the update request.
    :type action_type: object
    :param methodology: Methodology to which the template belongs, eg. Agile, Scrum, CMMI.
    :type methodology: str
    :param template: String representation of the work item type template.
    :type template: str
    :param template_type: The type of the template described in the request body.
    :type template_type: object
    """

    _attribute_map = {
        'action_type': {'key': 'actionType', 'type': 'object'},
        'methodology': {'key': 'methodology', 'type': 'str'},
        'template': {'key': 'template', 'type': 'str'},
        'template_type': {'key': 'templateType', 'type': 'object'}
    }

    def __init__(self, action_type=None, methodology=None, template=None, template_type=None):
        super(WorkItemTypeTemplateUpdateModel, self).__init__()
        self.action_type = action_type
        self.methodology = methodology
        self.template = template
        self.template_type = template_type

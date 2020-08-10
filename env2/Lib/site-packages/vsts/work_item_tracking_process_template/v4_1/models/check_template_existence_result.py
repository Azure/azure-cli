# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CheckTemplateExistenceResult(Model):
    """CheckTemplateExistenceResult.

    :param does_template_exist: Indicates whether a template exists.
    :type does_template_exist: bool
    :param existing_template_name: The name of the existing template.
    :type existing_template_name: str
    :param existing_template_type_id: The existing template type identifier.
    :type existing_template_type_id: str
    :param requested_template_name: The name of the requested template.
    :type requested_template_name: str
    """

    _attribute_map = {
        'does_template_exist': {'key': 'doesTemplateExist', 'type': 'bool'},
        'existing_template_name': {'key': 'existingTemplateName', 'type': 'str'},
        'existing_template_type_id': {'key': 'existingTemplateTypeId', 'type': 'str'},
        'requested_template_name': {'key': 'requestedTemplateName', 'type': 'str'}
    }

    def __init__(self, does_template_exist=None, existing_template_name=None, existing_template_type_id=None, requested_template_name=None):
        super(CheckTemplateExistenceResult, self).__init__()
        self.does_template_exist = does_template_exist
        self.existing_template_name = existing_template_name
        self.existing_template_type_id = existing_template_type_id
        self.requested_template_name = requested_template_name

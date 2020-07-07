# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_template_reference import WorkItemTemplateReference


class WorkItemTemplate(WorkItemTemplateReference):
    """WorkItemTemplate.

    :param url:
    :type url: str
    :param _links: Link references to related REST resources.
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_1.models.ReferenceLinks>`
    :param description: The description of the work item template.
    :type description: str
    :param id: The identifier of the work item template.
    :type id: str
    :param name: The name of the work item template.
    :type name: str
    :param work_item_type_name: The name of the work item type.
    :type work_item_type_name: str
    :param fields: Mapping of field and its templated value.
    :type fields: dict
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'work_item_type_name': {'key': 'workItemTypeName', 'type': 'str'},
        'fields': {'key': 'fields', 'type': '{str}'}
    }

    def __init__(self, url=None, _links=None, description=None, id=None, name=None, work_item_type_name=None, fields=None):
        super(WorkItemTemplate, self).__init__(url=url, _links=_links, description=description, id=id, name=name, work_item_type_name=work_item_type_name)
        self.fields = fields

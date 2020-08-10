# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_delete_reference import WorkItemDeleteReference


class WorkItemDelete(WorkItemDeleteReference):
    """WorkItemDelete.

    :param code:
    :type code: int
    :param deleted_by:
    :type deleted_by: str
    :param deleted_date:
    :type deleted_date: str
    :param id:
    :type id: int
    :param message:
    :type message: str
    :param name:
    :type name: str
    :param project:
    :type project: str
    :param type:
    :type type: str
    :param url:
    :type url: str
    :param resource:
    :type resource: :class:`WorkItem <work-item-tracking.v4_0.models.WorkItem>`
    """

    _attribute_map = {
        'code': {'key': 'code', 'type': 'int'},
        'deleted_by': {'key': 'deletedBy', 'type': 'str'},
        'deleted_date': {'key': 'deletedDate', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'message': {'key': 'message', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'project': {'key': 'project', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'resource': {'key': 'resource', 'type': 'WorkItem'}
    }

    def __init__(self, code=None, deleted_by=None, deleted_date=None, id=None, message=None, name=None, project=None, type=None, url=None, resource=None):
        super(WorkItemDelete, self).__init__(code=code, deleted_by=deleted_by, deleted_date=deleted_date, id=id, message=message, name=name, project=project, type=type, url=url)
        self.resource = resource

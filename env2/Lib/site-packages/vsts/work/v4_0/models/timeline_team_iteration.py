# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TimelineTeamIteration(Model):
    """TimelineTeamIteration.

    :param finish_date: The end date of the iteration
    :type finish_date: datetime
    :param name: The iteration name
    :type name: str
    :param partially_paged_work_items: All the partially paged workitems in this iteration.
    :type partially_paged_work_items: list of [object]
    :param path: The iteration path
    :type path: str
    :param start_date: The start date of the iteration
    :type start_date: datetime
    :param status: The status of this iteration
    :type status: :class:`TimelineIterationStatus <work.v4_0.models.TimelineIterationStatus>`
    :param work_items: The work items that have been paged in this iteration
    :type work_items: list of [object]
    """

    _attribute_map = {
        'finish_date': {'key': 'finishDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'partially_paged_work_items': {'key': 'partiallyPagedWorkItems', 'type': '[[object]]'},
        'path': {'key': 'path', 'type': 'str'},
        'start_date': {'key': 'startDate', 'type': 'iso-8601'},
        'status': {'key': 'status', 'type': 'TimelineIterationStatus'},
        'work_items': {'key': 'workItems', 'type': '[[object]]'}
    }

    def __init__(self, finish_date=None, name=None, partially_paged_work_items=None, path=None, start_date=None, status=None, work_items=None):
        super(TimelineTeamIteration, self).__init__()
        self.finish_date = finish_date
        self.name = name
        self.partially_paged_work_items = partially_paged_work_items
        self.path = path
        self.start_date = start_date
        self.status = status
        self.work_items = work_items

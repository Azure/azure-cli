# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseTask(Model):
    """ReleaseTask.

    :param agent_name:
    :type agent_name: str
    :param date_ended:
    :type date_ended: datetime
    :param date_started:
    :type date_started: datetime
    :param finish_time:
    :type finish_time: datetime
    :param id:
    :type id: int
    :param issues:
    :type issues: list of :class:`Issue <release.v4_0.models.Issue>`
    :param line_count:
    :type line_count: long
    :param log_url:
    :type log_url: str
    :param name:
    :type name: str
    :param percent_complete:
    :type percent_complete: int
    :param rank:
    :type rank: int
    :param start_time:
    :type start_time: datetime
    :param status:
    :type status: object
    :param task:
    :type task: :class:`WorkflowTaskReference <release.v4_0.models.WorkflowTaskReference>`
    :param timeline_record_id:
    :type timeline_record_id: str
    """

    _attribute_map = {
        'agent_name': {'key': 'agentName', 'type': 'str'},
        'date_ended': {'key': 'dateEnded', 'type': 'iso-8601'},
        'date_started': {'key': 'dateStarted', 'type': 'iso-8601'},
        'finish_time': {'key': 'finishTime', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'int'},
        'issues': {'key': 'issues', 'type': '[Issue]'},
        'line_count': {'key': 'lineCount', 'type': 'long'},
        'log_url': {'key': 'logUrl', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'percent_complete': {'key': 'percentComplete', 'type': 'int'},
        'rank': {'key': 'rank', 'type': 'int'},
        'start_time': {'key': 'startTime', 'type': 'iso-8601'},
        'status': {'key': 'status', 'type': 'object'},
        'task': {'key': 'task', 'type': 'WorkflowTaskReference'},
        'timeline_record_id': {'key': 'timelineRecordId', 'type': 'str'}
    }

    def __init__(self, agent_name=None, date_ended=None, date_started=None, finish_time=None, id=None, issues=None, line_count=None, log_url=None, name=None, percent_complete=None, rank=None, start_time=None, status=None, task=None, timeline_record_id=None):
        super(ReleaseTask, self).__init__()
        self.agent_name = agent_name
        self.date_ended = date_ended
        self.date_started = date_started
        self.finish_time = finish_time
        self.id = id
        self.issues = issues
        self.line_count = line_count
        self.log_url = log_url
        self.name = name
        self.percent_complete = percent_complete
        self.rank = rank
        self.start_time = start_time
        self.status = status
        self.task = task
        self.timeline_record_id = timeline_record_id

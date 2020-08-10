# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AutoTriggerIssue(Model):
    """AutoTriggerIssue.

    :param issue:
    :type issue: :class:`Issue <release.v4_0.models.Issue>`
    :param issue_source:
    :type issue_source: object
    :param project:
    :type project: :class:`ProjectReference <release.v4_0.models.ProjectReference>`
    :param release_definition_reference:
    :type release_definition_reference: :class:`ReleaseDefinitionShallowReference <release.v4_0.models.ReleaseDefinitionShallowReference>`
    :param release_trigger_type:
    :type release_trigger_type: object
    """

    _attribute_map = {
        'issue': {'key': 'issue', 'type': 'Issue'},
        'issue_source': {'key': 'issueSource', 'type': 'object'},
        'project': {'key': 'project', 'type': 'ProjectReference'},
        'release_definition_reference': {'key': 'releaseDefinitionReference', 'type': 'ReleaseDefinitionShallowReference'},
        'release_trigger_type': {'key': 'releaseTriggerType', 'type': 'object'}
    }

    def __init__(self, issue=None, issue_source=None, project=None, release_definition_reference=None, release_trigger_type=None):
        super(AutoTriggerIssue, self).__init__()
        self.issue = issue
        self.issue_source = issue_source
        self.project = project
        self.release_definition_reference = release_definition_reference
        self.release_trigger_type = release_trigger_type

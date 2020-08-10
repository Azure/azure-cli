# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReportingWorkItemRevisionsFilter(Model):
    """ReportingWorkItemRevisionsFilter.

    :param fields: A list of fields to return in work item revisions. Omit this parameter to get all reportable fields.
    :type fields: list of str
    :param include_deleted: Include deleted work item in the result.
    :type include_deleted: bool
    :param include_identity_ref: Return an identity reference instead of a string value for identity fields.
    :type include_identity_ref: bool
    :param include_latest_only: Include only the latest version of a work item, skipping over all previous revisions of the work item.
    :type include_latest_only: bool
    :param include_tag_ref: Include tag reference instead of string value for System.Tags field
    :type include_tag_ref: bool
    :param types: A list of types to filter the results to specific work item types. Omit this parameter to get work item revisions of all work item types.
    :type types: list of str
    """

    _attribute_map = {
        'fields': {'key': 'fields', 'type': '[str]'},
        'include_deleted': {'key': 'includeDeleted', 'type': 'bool'},
        'include_identity_ref': {'key': 'includeIdentityRef', 'type': 'bool'},
        'include_latest_only': {'key': 'includeLatestOnly', 'type': 'bool'},
        'include_tag_ref': {'key': 'includeTagRef', 'type': 'bool'},
        'types': {'key': 'types', 'type': '[str]'}
    }

    def __init__(self, fields=None, include_deleted=None, include_identity_ref=None, include_latest_only=None, include_tag_ref=None, types=None):
        super(ReportingWorkItemRevisionsFilter, self).__init__()
        self.fields = fields
        self.include_deleted = include_deleted
        self.include_identity_ref = include_identity_ref
        self.include_latest_only = include_latest_only
        self.include_tag_ref = include_tag_ref
        self.types = types

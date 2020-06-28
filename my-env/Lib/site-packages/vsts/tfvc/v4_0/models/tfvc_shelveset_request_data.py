# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcShelvesetRequestData(Model):
    """TfvcShelvesetRequestData.

    :param include_details: Whether to include policyOverride and notes Only applies when requesting a single deep shelveset
    :type include_details: bool
    :param include_links: Whether to include the _links field on the shallow references. Does not apply when requesting a single deep shelveset object. Links will always be included in the deep shelveset.
    :type include_links: bool
    :param include_work_items: Whether to include workItems
    :type include_work_items: bool
    :param max_change_count: Max number of changes to include
    :type max_change_count: int
    :param max_comment_length: Max length of comment
    :type max_comment_length: int
    :param name: Shelveset's name
    :type name: str
    :param owner: Owner's ID. Could be a name or a guid.
    :type owner: str
    """

    _attribute_map = {
        'include_details': {'key': 'includeDetails', 'type': 'bool'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'include_work_items': {'key': 'includeWorkItems', 'type': 'bool'},
        'max_change_count': {'key': 'maxChangeCount', 'type': 'int'},
        'max_comment_length': {'key': 'maxCommentLength', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'str'}
    }

    def __init__(self, include_details=None, include_links=None, include_work_items=None, max_change_count=None, max_comment_length=None, name=None, owner=None):
        super(TfvcShelvesetRequestData, self).__init__()
        self.include_details = include_details
        self.include_links = include_links
        self.include_work_items = include_work_items
        self.max_change_count = max_change_count
        self.max_comment_length = max_comment_length
        self.name = name
        self.owner = owner

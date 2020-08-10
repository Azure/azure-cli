# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitQueryCommitsCriteria(Model):
    """GitQueryCommitsCriteria.

    :param skip: Number of entries to skip
    :type skip: int
    :param top: Maximum number of entries to retrieve
    :type top: int
    :param author: Alias or display name of the author
    :type author: str
    :param compare_version: Only applicable when ItemVersion specified. If provided, start walking history starting at this commit.
    :type compare_version: :class:`GitVersionDescriptor <git.v4_1.models.GitVersionDescriptor>`
    :param exclude_deletes: If true, don't include delete history entries
    :type exclude_deletes: bool
    :param from_commit_id: If provided, a lower bound for filtering commits alphabetically
    :type from_commit_id: str
    :param from_date: If provided, only include history entries created after this date (string)
    :type from_date: str
    :param history_mode: What Git history mode should be used. This only applies to the search criteria when Ids = null.
    :type history_mode: object
    :param ids: If provided, specifies the exact commit ids of the commits to fetch. May not be combined with other parameters.
    :type ids: list of str
    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    :param include_work_items: Whether to include linked work items
    :type include_work_items: bool
    :param item_path: Path of item to search under
    :type item_path: str
    :param item_version: If provided, identifies the commit or branch to search
    :type item_version: :class:`GitVersionDescriptor <git.v4_1.models.GitVersionDescriptor>`
    :param to_commit_id: If provided, an upper bound for filtering commits alphabetically
    :type to_commit_id: str
    :param to_date: If provided, only include history entries created before this date (string)
    :type to_date: str
    :param user: Alias or display name of the committer
    :type user: str
    """

    _attribute_map = {
        'skip': {'key': '$skip', 'type': 'int'},
        'top': {'key': '$top', 'type': 'int'},
        'author': {'key': 'author', 'type': 'str'},
        'compare_version': {'key': 'compareVersion', 'type': 'GitVersionDescriptor'},
        'exclude_deletes': {'key': 'excludeDeletes', 'type': 'bool'},
        'from_commit_id': {'key': 'fromCommitId', 'type': 'str'},
        'from_date': {'key': 'fromDate', 'type': 'str'},
        'history_mode': {'key': 'historyMode', 'type': 'object'},
        'ids': {'key': 'ids', 'type': '[str]'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'include_work_items': {'key': 'includeWorkItems', 'type': 'bool'},
        'item_path': {'key': 'itemPath', 'type': 'str'},
        'item_version': {'key': 'itemVersion', 'type': 'GitVersionDescriptor'},
        'to_commit_id': {'key': 'toCommitId', 'type': 'str'},
        'to_date': {'key': 'toDate', 'type': 'str'},
        'user': {'key': 'user', 'type': 'str'}
    }

    def __init__(self, skip=None, top=None, author=None, compare_version=None, exclude_deletes=None, from_commit_id=None, from_date=None, history_mode=None, ids=None, include_links=None, include_work_items=None, item_path=None, item_version=None, to_commit_id=None, to_date=None, user=None):
        super(GitQueryCommitsCriteria, self).__init__()
        self.skip = skip
        self.top = top
        self.author = author
        self.compare_version = compare_version
        self.exclude_deletes = exclude_deletes
        self.from_commit_id = from_commit_id
        self.from_date = from_date
        self.history_mode = history_mode
        self.ids = ids
        self.include_links = include_links
        self.include_work_items = include_work_items
        self.item_path = item_path
        self.item_version = item_version
        self.to_commit_id = to_commit_id
        self.to_date = to_date
        self.user = user

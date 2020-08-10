# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcChangesetSearchCriteria(Model):
    """TfvcChangesetSearchCriteria.

    :param author: Alias or display name of user who made the changes
    :type author: str
    :param follow_renames: Whether or not to follow renames for the given item being queried
    :type follow_renames: bool
    :param from_date: If provided, only include changesets created after this date (string) Think of a better name for this.
    :type from_date: str
    :param from_id: If provided, only include changesets after this changesetID
    :type from_id: int
    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    :param item_path: Path of item to search under
    :type item_path: str
    :param to_date: If provided, only include changesets created before this date (string) Think of a better name for this.
    :type to_date: str
    :param to_id: If provided, a version descriptor for the latest change list to include
    :type to_id: int
    """

    _attribute_map = {
        'author': {'key': 'author', 'type': 'str'},
        'follow_renames': {'key': 'followRenames', 'type': 'bool'},
        'from_date': {'key': 'fromDate', 'type': 'str'},
        'from_id': {'key': 'fromId', 'type': 'int'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'item_path': {'key': 'itemPath', 'type': 'str'},
        'to_date': {'key': 'toDate', 'type': 'str'},
        'to_id': {'key': 'toId', 'type': 'int'}
    }

    def __init__(self, author=None, follow_renames=None, from_date=None, from_id=None, include_links=None, item_path=None, to_date=None, to_id=None):
        super(TfvcChangesetSearchCriteria, self).__init__()
        self.author = author
        self.follow_renames = follow_renames
        self.from_date = from_date
        self.from_id = from_id
        self.include_links = include_links
        self.item_path = item_path
        self.to_date = to_date
        self.to_id = to_id

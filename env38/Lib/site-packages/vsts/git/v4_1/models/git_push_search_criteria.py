# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPushSearchCriteria(Model):
    """GitPushSearchCriteria.

    :param from_date:
    :type from_date: datetime
    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    :param include_ref_updates:
    :type include_ref_updates: bool
    :param pusher_id:
    :type pusher_id: str
    :param ref_name:
    :type ref_name: str
    :param to_date:
    :type to_date: datetime
    """

    _attribute_map = {
        'from_date': {'key': 'fromDate', 'type': 'iso-8601'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'include_ref_updates': {'key': 'includeRefUpdates', 'type': 'bool'},
        'pusher_id': {'key': 'pusherId', 'type': 'str'},
        'ref_name': {'key': 'refName', 'type': 'str'},
        'to_date': {'key': 'toDate', 'type': 'iso-8601'}
    }

    def __init__(self, from_date=None, include_links=None, include_ref_updates=None, pusher_id=None, ref_name=None, to_date=None):
        super(GitPushSearchCriteria, self).__init__()
        self.from_date = from_date
        self.include_links = include_links
        self.include_ref_updates = include_ref_updates
        self.pusher_id = pusher_id
        self.ref_name = ref_name
        self.to_date = to_date

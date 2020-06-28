# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPushRef(Model):
    """GitPushRef.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param date:
    :type date: datetime
    :param push_correlation_id:
    :type push_correlation_id: str
    :param pushed_by:
    :type pushed_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param push_id:
    :type push_id: int
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'date': {'key': 'date', 'type': 'iso-8601'},
        'push_correlation_id': {'key': 'pushCorrelationId', 'type': 'str'},
        'pushed_by': {'key': 'pushedBy', 'type': 'IdentityRef'},
        'push_id': {'key': 'pushId', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, date=None, push_correlation_id=None, pushed_by=None, push_id=None, url=None):
        super(GitPushRef, self).__init__()
        self._links = _links
        self.date = date
        self.push_correlation_id = push_correlation_id
        self.pushed_by = pushed_by
        self.push_id = push_id
        self.url = url

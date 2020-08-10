# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestSession(Model):
    """TestSession.

    :param area: Area path of the test session
    :type area: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param comment: Comments in the test session
    :type comment: str
    :param end_date: Duration of the session
    :type end_date: datetime
    :param id: Id of the test session
    :type id: int
    :param last_updated_by: Last Updated By  Reference
    :type last_updated_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param last_updated_date: Last updated date
    :type last_updated_date: datetime
    :param owner: Owner of the test session
    :type owner: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param project: Project to which the test session belongs
    :type project: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param property_bag: Generic store for test session data
    :type property_bag: :class:`PropertyBag <test.v4_0.models.PropertyBag>`
    :param revision: Revision of the test session
    :type revision: int
    :param source: Source of the test session
    :type source: object
    :param start_date: Start date
    :type start_date: datetime
    :param state: State of the test session
    :type state: object
    :param title: Title of the test session
    :type title: str
    :param url: Url of Test Session Resource
    :type url: str
    """

    _attribute_map = {
        'area': {'key': 'area', 'type': 'ShallowReference'},
        'comment': {'key': 'comment', 'type': 'str'},
        'end_date': {'key': 'endDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'int'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'IdentityRef'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'property_bag': {'key': 'propertyBag', 'type': 'PropertyBag'},
        'revision': {'key': 'revision', 'type': 'int'},
        'source': {'key': 'source', 'type': 'object'},
        'start_date': {'key': 'startDate', 'type': 'iso-8601'},
        'state': {'key': 'state', 'type': 'object'},
        'title': {'key': 'title', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, area=None, comment=None, end_date=None, id=None, last_updated_by=None, last_updated_date=None, owner=None, project=None, property_bag=None, revision=None, source=None, start_date=None, state=None, title=None, url=None):
        super(TestSession, self).__init__()
        self.area = area
        self.comment = comment
        self.end_date = end_date
        self.id = id
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.owner = owner
        self.project = project
        self.property_bag = property_bag
        self.revision = revision
        self.source = source
        self.start_date = start_date
        self.state = state
        self.title = title
        self.url = url

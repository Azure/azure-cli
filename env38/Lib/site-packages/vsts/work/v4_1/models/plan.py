# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Plan(Model):
    """Plan.

    :param created_by_identity: Identity that created this plan. Defaults to null for records before upgrading to ScaledAgileViewComponent4.
    :type created_by_identity: :class:`IdentityRef <work.v4_1.models.IdentityRef>`
    :param created_date: Date when the plan was created
    :type created_date: datetime
    :param description: Description of the plan
    :type description: str
    :param id: Id of the plan
    :type id: str
    :param modified_by_identity: Identity that last modified this plan. Defaults to null for records before upgrading to ScaledAgileViewComponent4.
    :type modified_by_identity: :class:`IdentityRef <work.v4_1.models.IdentityRef>`
    :param modified_date: Date when the plan was last modified. Default to CreatedDate when the plan is first created.
    :type modified_date: datetime
    :param name: Name of the plan
    :type name: str
    :param properties: The PlanPropertyCollection instance associated with the plan. These are dependent on the type of the plan. For example, DeliveryTimelineView, it would be of type DeliveryViewPropertyCollection.
    :type properties: object
    :param revision: Revision of the plan. Used to safeguard users from overwriting each other's changes.
    :type revision: int
    :param type: Type of the plan
    :type type: object
    :param url: The resource url to locate the plan via rest api
    :type url: str
    :param user_permissions: Bit flag indicating set of permissions a user has to the plan.
    :type user_permissions: object
    """

    _attribute_map = {
        'created_by_identity': {'key': 'createdByIdentity', 'type': 'IdentityRef'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'modified_by_identity': {'key': 'modifiedByIdentity', 'type': 'IdentityRef'},
        'modified_date': {'key': 'modifiedDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': 'object'},
        'revision': {'key': 'revision', 'type': 'int'},
        'type': {'key': 'type', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'},
        'user_permissions': {'key': 'userPermissions', 'type': 'object'}
    }

    def __init__(self, created_by_identity=None, created_date=None, description=None, id=None, modified_by_identity=None, modified_date=None, name=None, properties=None, revision=None, type=None, url=None, user_permissions=None):
        super(Plan, self).__init__()
        self.created_by_identity = created_by_identity
        self.created_date = created_date
        self.description = description
        self.id = id
        self.modified_by_identity = modified_by_identity
        self.modified_date = modified_date
        self.name = name
        self.properties = properties
        self.revision = revision
        self.type = type
        self.url = url
        self.user_permissions = user_permissions

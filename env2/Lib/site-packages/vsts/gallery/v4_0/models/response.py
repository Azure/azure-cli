# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .qn_aItem import QnAItem


class Response(QnAItem):
    """Response.

    :param created_date: Time when the review was first created
    :type created_date: datetime
    :param id: Unique identifier of a QnA item
    :type id: long
    :param status: Get status of item
    :type status: object
    :param text: Text description of the QnA item
    :type text: str
    :param updated_date: Time when the review was edited/updated
    :type updated_date: datetime
    :param user: User details for the item.
    :type user: :class:`UserIdentityRef <gallery.v4_0.models.UserIdentityRef>`
    """

    _attribute_map = {
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'long'},
        'status': {'key': 'status', 'type': 'object'},
        'text': {'key': 'text', 'type': 'str'},
        'updated_date': {'key': 'updatedDate', 'type': 'iso-8601'},
        'user': {'key': 'user', 'type': 'UserIdentityRef'},
    }

    def __init__(self, created_date=None, id=None, status=None, text=None, updated_date=None, user=None):
        super(Response, self).__init__(created_date=created_date, id=id, status=status, text=text, updated_date=updated_date, user=user)

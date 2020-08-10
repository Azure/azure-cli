# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Review(Model):
    """Review.

    :param admin_reply: Admin Reply, if any, for this review
    :type admin_reply: :class:`ReviewReply <gallery.v4_0.models.ReviewReply>`
    :param id: Unique identifier of a review item
    :type id: long
    :param is_deleted: Flag for soft deletion
    :type is_deleted: bool
    :param is_ignored:
    :type is_ignored: bool
    :param product_version: Version of the product for which review was submitted
    :type product_version: str
    :param rating: Rating procided by the user
    :type rating: str
    :param reply: Reply, if any, for this review
    :type reply: :class:`ReviewReply <gallery.v4_0.models.ReviewReply>`
    :param text: Text description of the review
    :type text: str
    :param title: Title of the review
    :type title: str
    :param updated_date: Time when the review was edited/updated
    :type updated_date: datetime
    :param user_display_name: Name of the user
    :type user_display_name: str
    :param user_id: Id of the user who submitted the review
    :type user_id: str
    """

    _attribute_map = {
        'admin_reply': {'key': 'adminReply', 'type': 'ReviewReply'},
        'id': {'key': 'id', 'type': 'long'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'is_ignored': {'key': 'isIgnored', 'type': 'bool'},
        'product_version': {'key': 'productVersion', 'type': 'str'},
        'rating': {'key': 'rating', 'type': 'str'},
        'reply': {'key': 'reply', 'type': 'ReviewReply'},
        'text': {'key': 'text', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'},
        'updated_date': {'key': 'updatedDate', 'type': 'iso-8601'},
        'user_display_name': {'key': 'userDisplayName', 'type': 'str'},
        'user_id': {'key': 'userId', 'type': 'str'}
    }

    def __init__(self, admin_reply=None, id=None, is_deleted=None, is_ignored=None, product_version=None, rating=None, reply=None, text=None, title=None, updated_date=None, user_display_name=None, user_id=None):
        super(Review, self).__init__()
        self.admin_reply = admin_reply
        self.id = id
        self.is_deleted = is_deleted
        self.is_ignored = is_ignored
        self.product_version = product_version
        self.rating = rating
        self.reply = reply
        self.text = text
        self.title = title
        self.updated_date = updated_date
        self.user_display_name = user_display_name
        self.user_id = user_id

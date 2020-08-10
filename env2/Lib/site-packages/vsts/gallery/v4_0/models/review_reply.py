# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReviewReply(Model):
    """ReviewReply.

    :param id: Id of the reply
    :type id: long
    :param is_deleted: Flag for soft deletion
    :type is_deleted: bool
    :param product_version: Version of the product when the reply was submitted or updated
    :type product_version: str
    :param reply_text: Content of the reply
    :type reply_text: str
    :param review_id: Id of the review, to which this reply belongs
    :type review_id: long
    :param title: Title of the reply
    :type title: str
    :param updated_date: Date the reply was submitted or updated
    :type updated_date: datetime
    :param user_id: Id of the user who left the reply
    :type user_id: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'long'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'product_version': {'key': 'productVersion', 'type': 'str'},
        'reply_text': {'key': 'replyText', 'type': 'str'},
        'review_id': {'key': 'reviewId', 'type': 'long'},
        'title': {'key': 'title', 'type': 'str'},
        'updated_date': {'key': 'updatedDate', 'type': 'iso-8601'},
        'user_id': {'key': 'userId', 'type': 'str'}
    }

    def __init__(self, id=None, is_deleted=None, product_version=None, reply_text=None, review_id=None, title=None, updated_date=None, user_id=None):
        super(ReviewReply, self).__init__()
        self.id = id
        self.is_deleted = is_deleted
        self.product_version = product_version
        self.reply_text = reply_text
        self.review_id = review_id
        self.title = title
        self.updated_date = updated_date
        self.user_id = user_id

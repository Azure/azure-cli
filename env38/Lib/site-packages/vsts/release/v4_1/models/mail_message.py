# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MailMessage(Model):
    """MailMessage.

    :param body:
    :type body: str
    :param cC:
    :type cC: :class:`EmailRecipients <release.v4_1.models.EmailRecipients>`
    :param in_reply_to:
    :type in_reply_to: str
    :param message_id:
    :type message_id: str
    :param reply_by:
    :type reply_by: datetime
    :param reply_to:
    :type reply_to: :class:`EmailRecipients <release.v4_1.models.EmailRecipients>`
    :param sections:
    :type sections: list of MailSectionType
    :param sender_type:
    :type sender_type: object
    :param subject:
    :type subject: str
    :param to:
    :type to: :class:`EmailRecipients <release.v4_1.models.EmailRecipients>`
    """

    _attribute_map = {
        'body': {'key': 'body', 'type': 'str'},
        'cC': {'key': 'cC', 'type': 'EmailRecipients'},
        'in_reply_to': {'key': 'inReplyTo', 'type': 'str'},
        'message_id': {'key': 'messageId', 'type': 'str'},
        'reply_by': {'key': 'replyBy', 'type': 'iso-8601'},
        'reply_to': {'key': 'replyTo', 'type': 'EmailRecipients'},
        'sections': {'key': 'sections', 'type': '[object]'},
        'sender_type': {'key': 'senderType', 'type': 'object'},
        'subject': {'key': 'subject', 'type': 'str'},
        'to': {'key': 'to', 'type': 'EmailRecipients'}
    }

    def __init__(self, body=None, cC=None, in_reply_to=None, message_id=None, reply_by=None, reply_to=None, sections=None, sender_type=None, subject=None, to=None):
        super(MailMessage, self).__init__()
        self.body = body
        self.cC = cC
        self.in_reply_to = in_reply_to
        self.message_id = message_id
        self.reply_by = reply_by
        self.reply_to = reply_to
        self.sections = sections
        self.sender_type = sender_type
        self.subject = subject
        self.to = to

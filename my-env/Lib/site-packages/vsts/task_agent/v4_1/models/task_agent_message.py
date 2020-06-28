# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentMessage(Model):
    """TaskAgentMessage.

    :param body: Gets or sets the body of the message. If the <c>IV</c> property is provided the body will need to be decrypted using the <c>TaskAgentSession.EncryptionKey</c> value in addition to the <c>IV</c>.
    :type body: str
    :param iV: Gets or sets the intialization vector used to encrypt this message.
    :type iV: str
    :param message_id: Gets or sets the message identifier.
    :type message_id: long
    :param message_type: Gets or sets the message type, describing the data contract found in <c>TaskAgentMessage.Body</c>.
    :type message_type: str
    """

    _attribute_map = {
        'body': {'key': 'body', 'type': 'str'},
        'iV': {'key': 'iV', 'type': 'str'},
        'message_id': {'key': 'messageId', 'type': 'long'},
        'message_type': {'key': 'messageType', 'type': 'str'}
    }

    def __init__(self, body=None, iV=None, message_id=None, message_type=None):
        super(TaskAgentMessage, self).__init__()
        self.body = body
        self.iV = iV
        self.message_id = message_id
        self.message_type = message_type

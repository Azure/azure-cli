# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentSession(Model):
    """TaskAgentSession.

    :param agent: Gets or sets the agent which is the target of the session.
    :type agent: :class:`TaskAgentReference <task-agent.v4_1.models.TaskAgentReference>`
    :param encryption_key: Gets the key used to encrypt message traffic for this session.
    :type encryption_key: :class:`TaskAgentSessionKey <task-agent.v4_1.models.TaskAgentSessionKey>`
    :param owner_name: Gets or sets the owner name of this session. Generally this will be the machine of origination.
    :type owner_name: str
    :param session_id: Gets the unique identifier for this session.
    :type session_id: str
    :param system_capabilities:
    :type system_capabilities: dict
    """

    _attribute_map = {
        'agent': {'key': 'agent', 'type': 'TaskAgentReference'},
        'encryption_key': {'key': 'encryptionKey', 'type': 'TaskAgentSessionKey'},
        'owner_name': {'key': 'ownerName', 'type': 'str'},
        'session_id': {'key': 'sessionId', 'type': 'str'},
        'system_capabilities': {'key': 'systemCapabilities', 'type': '{str}'}
    }

    def __init__(self, agent=None, encryption_key=None, owner_name=None, session_id=None, system_capabilities=None):
        super(TaskAgentSession, self).__init__()
        self.agent = agent
        self.encryption_key = encryption_key
        self.owner_name = owner_name
        self.session_id = session_id
        self.system_capabilities = system_capabilities

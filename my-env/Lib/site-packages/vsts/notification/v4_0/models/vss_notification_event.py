# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class VssNotificationEvent(Model):
    """VssNotificationEvent.

    :param actors: Optional: A list of actors which are additional identities with corresponding roles that are relevant to the event.
    :type actors: list of :class:`EventActor <microsoft.-visual-studio.-services.-web-api.v4_0.models.EventActor>`
    :param artifact_uris: Optional: A list of artifacts referenced or impacted by this event.
    :type artifact_uris: list of str
    :param data: Required: The event payload.  If Data is a string, it must be in Json or XML format.  Otherwise it must have a serialization format attribute.
    :type data: object
    :param event_type: Required: The name of the event.  This event must be registered in the context it is being fired.
    :type event_type: str
    :param scopes: Optional: A list of scopes which are are relevant to the event.
    :type scopes: list of :class:`EventScope <microsoft.-visual-studio.-services.-web-api.v4_0.models.EventScope>`
    """

    _attribute_map = {
        'actors': {'key': 'actors', 'type': '[EventActor]'},
        'artifact_uris': {'key': 'artifactUris', 'type': '[str]'},
        'data': {'key': 'data', 'type': 'object'},
        'event_type': {'key': 'eventType', 'type': 'str'},
        'scopes': {'key': 'scopes', 'type': '[EventScope]'}
    }

    def __init__(self, actors=None, artifact_uris=None, data=None, event_type=None, scopes=None):
        super(VssNotificationEvent, self).__init__()
        self.actors = actors
        self.artifact_uris = artifact_uris
        self.data = data
        self.event_type = event_type
        self.scopes = scopes

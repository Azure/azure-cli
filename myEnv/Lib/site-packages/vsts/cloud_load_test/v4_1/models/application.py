# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Application(Model):
    """Application.

    :param application_id:
    :type application_id: str
    :param description:
    :type description: str
    :param name:
    :type name: str
    :param path:
    :type path: str
    :param path_seperator:
    :type path_seperator: str
    :param type:
    :type type: str
    :param version:
    :type version: str
    """

    _attribute_map = {
        'application_id': {'key': 'applicationId', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'},
        'path_seperator': {'key': 'pathSeperator', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, application_id=None, description=None, name=None, path=None, path_seperator=None, type=None, version=None):
        super(Application, self).__init__()
        self.application_id = application_id
        self.description = description
        self.name = name
        self.path = path
        self.path_seperator = path_seperator
        self.type = type
        self.version = version

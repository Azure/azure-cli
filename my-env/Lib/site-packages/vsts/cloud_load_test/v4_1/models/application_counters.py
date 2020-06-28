# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ApplicationCounters(Model):
    """ApplicationCounters.

    :param application_id:
    :type application_id: str
    :param description:
    :type description: str
    :param id:
    :type id: str
    :param is_default:
    :type is_default: bool
    :param name:
    :type name: str
    :param path:
    :type path: str
    """

    _attribute_map = {
        'application_id': {'key': 'applicationId', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_default': {'key': 'isDefault', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, application_id=None, description=None, id=None, is_default=None, name=None, path=None):
        super(ApplicationCounters, self).__init__()
        self.application_id = application_id
        self.description = description
        self.id = id
        self.is_default = is_default
        self.name = name
        self.path = path

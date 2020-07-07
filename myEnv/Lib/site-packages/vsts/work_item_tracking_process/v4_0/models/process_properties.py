# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProcessProperties(Model):
    """ProcessProperties.

    :param class_:
    :type class_: object
    :param is_default:
    :type is_default: bool
    :param is_enabled:
    :type is_enabled: bool
    :param parent_process_type_id:
    :type parent_process_type_id: str
    :param version:
    :type version: str
    """

    _attribute_map = {
        'class_': {'key': 'class', 'type': 'object'},
        'is_default': {'key': 'isDefault', 'type': 'bool'},
        'is_enabled': {'key': 'isEnabled', 'type': 'bool'},
        'parent_process_type_id': {'key': 'parentProcessTypeId', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, class_=None, is_default=None, is_enabled=None, parent_process_type_id=None, version=None):
        super(ProcessProperties, self).__init__()
        self.class_ = class_
        self.is_default = is_default
        self.is_enabled = is_enabled
        self.parent_process_type_id = parent_process_type_id
        self.version = version

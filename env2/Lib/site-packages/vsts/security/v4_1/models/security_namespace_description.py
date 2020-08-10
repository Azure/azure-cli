# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SecurityNamespaceDescription(Model):
    """SecurityNamespaceDescription.

    :param actions: The list of actions that this Security Namespace is responsible for securing.
    :type actions: list of :class:`ActionDefinition <security.v4_1.models.ActionDefinition>`
    :param dataspace_category: This is the dataspace category that describes where the security information for this SecurityNamespace should be stored.
    :type dataspace_category: str
    :param display_name: This localized name for this namespace.
    :type display_name: str
    :param element_length: If the security tokens this namespace will be operating on need to be split on certain character lengths to determine its elements, that length should be specified here. If not, this value will be -1.
    :type element_length: int
    :param extension_type: This is the type of the extension that should be loaded from the plugins directory for extending this security namespace.
    :type extension_type: str
    :param is_remotable: If true, the security namespace is remotable, allowing another service to proxy the namespace.
    :type is_remotable: bool
    :param name: This non-localized for this namespace.
    :type name: str
    :param namespace_id: The unique identifier for this namespace.
    :type namespace_id: str
    :param read_permission: The permission bits needed by a user in order to read security data on the Security Namespace.
    :type read_permission: int
    :param separator_value: If the security tokens this namespace will be operating on need to be split on certain characters to determine its elements that character should be specified here. If not, this value will be the null character.
    :type separator_value: str
    :param structure_value: Used to send information about the structure of the security namespace over the web service.
    :type structure_value: int
    :param system_bit_mask: The bits reserved by system store
    :type system_bit_mask: int
    :param use_token_translator: If true, the security service will expect an ISecurityDataspaceTokenTranslator plugin to exist for this namespace
    :type use_token_translator: bool
    :param write_permission: The permission bits needed by a user in order to modify security data on the Security Namespace.
    :type write_permission: int
    """

    _attribute_map = {
        'actions': {'key': 'actions', 'type': '[ActionDefinition]'},
        'dataspace_category': {'key': 'dataspaceCategory', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'element_length': {'key': 'elementLength', 'type': 'int'},
        'extension_type': {'key': 'extensionType', 'type': 'str'},
        'is_remotable': {'key': 'isRemotable', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'namespace_id': {'key': 'namespaceId', 'type': 'str'},
        'read_permission': {'key': 'readPermission', 'type': 'int'},
        'separator_value': {'key': 'separatorValue', 'type': 'str'},
        'structure_value': {'key': 'structureValue', 'type': 'int'},
        'system_bit_mask': {'key': 'systemBitMask', 'type': 'int'},
        'use_token_translator': {'key': 'useTokenTranslator', 'type': 'bool'},
        'write_permission': {'key': 'writePermission', 'type': 'int'}
    }

    def __init__(self, actions=None, dataspace_category=None, display_name=None, element_length=None, extension_type=None, is_remotable=None, name=None, namespace_id=None, read_permission=None, separator_value=None, structure_value=None, system_bit_mask=None, use_token_translator=None, write_permission=None):
        super(SecurityNamespaceDescription, self).__init__()
        self.actions = actions
        self.dataspace_category = dataspace_category
        self.display_name = display_name
        self.element_length = element_length
        self.extension_type = extension_type
        self.is_remotable = is_remotable
        self.name = name
        self.namespace_id = namespace_id
        self.read_permission = read_permission
        self.separator_value = separator_value
        self.structure_value = structure_value
        self.system_bit_mask = system_bit_mask
        self.use_token_translator = use_token_translator
        self.write_permission = write_permission

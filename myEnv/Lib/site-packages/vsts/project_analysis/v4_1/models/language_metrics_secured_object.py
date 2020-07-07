# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LanguageMetricsSecuredObject(Model):
    """LanguageMetricsSecuredObject.

    :param namespace_id:
    :type namespace_id: str
    :param project_id:
    :type project_id: str
    :param required_permissions:
    :type required_permissions: int
    """

    _attribute_map = {
        'namespace_id': {'key': 'namespaceId', 'type': 'str'},
        'project_id': {'key': 'projectId', 'type': 'str'},
        'required_permissions': {'key': 'requiredPermissions', 'type': 'int'}
    }

    def __init__(self, namespace_id=None, project_id=None, required_permissions=None):
        super(LanguageMetricsSecuredObject, self).__init__()
        self.namespace_id = namespace_id
        self.project_id = project_id
        self.required_permissions = required_permissions

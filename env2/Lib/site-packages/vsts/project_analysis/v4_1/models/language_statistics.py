# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .language_metrics_secured_object import LanguageMetricsSecuredObject


class LanguageStatistics(LanguageMetricsSecuredObject):
    """LanguageStatistics.

    :param namespace_id:
    :type namespace_id: str
    :param project_id:
    :type project_id: str
    :param required_permissions:
    :type required_permissions: int
    :param bytes:
    :type bytes: long
    :param files:
    :type files: int
    :param files_percentage:
    :type files_percentage: float
    :param language_percentage:
    :type language_percentage: float
    :param name:
    :type name: str
    """

    _attribute_map = {
        'namespace_id': {'key': 'namespaceId', 'type': 'str'},
        'project_id': {'key': 'projectId', 'type': 'str'},
        'required_permissions': {'key': 'requiredPermissions', 'type': 'int'},
        'bytes': {'key': 'bytes', 'type': 'long'},
        'files': {'key': 'files', 'type': 'int'},
        'files_percentage': {'key': 'filesPercentage', 'type': 'float'},
        'language_percentage': {'key': 'languagePercentage', 'type': 'float'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, namespace_id=None, project_id=None, required_permissions=None, bytes=None, files=None, files_percentage=None, language_percentage=None, name=None):
        super(LanguageStatistics, self).__init__(namespace_id=namespace_id, project_id=project_id, required_permissions=required_permissions)
        self.bytes = bytes
        self.files = files
        self.files_percentage = files_percentage
        self.language_percentage = language_percentage
        self.name = name

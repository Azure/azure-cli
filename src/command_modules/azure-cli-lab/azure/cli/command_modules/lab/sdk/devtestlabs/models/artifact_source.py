# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class ArtifactSource(Model):
    """Properties of an artifact source.

    :param display_name: The artifact source's display name.
    :type display_name: str
    :param uri: The artifact source's URI.
    :type uri: str
    :param source_type: The artifact source's type. Possible values include:
     'VsoGit', 'GitHub'
    :type source_type: str or :class:`SourceControlType
     <azure.mgmt.devtestlabs.models.SourceControlType>`
    :param folder_path: The folder containing artifacts.
    :type folder_path: str
    :param arm_template_folder_path: The folder containing Azure Resource
     Manager templates.
    :type arm_template_folder_path: str
    :param branch_ref: The artifact source's branch reference.
    :type branch_ref: str
    :param security_token: The security token to authenticate to the artifact
     source.
    :type security_token: str
    :param status: Indicates if the artifact source is enabled (values:
     Enabled, Disabled). Possible values include: 'Enabled', 'Disabled'
    :type status: str or :class:`EnableStatus
     <azure.mgmt.devtestlabs.models.EnableStatus>`
    :param created_date: The artifact source's creation date.
    :type created_date: datetime
    :param provisioning_state: The provisioning status of the resource.
    :type provisioning_state: str
    :param unique_identifier: The unique immutable identifier of a resource
     (Guid).
    :type unique_identifier: str
    :param id: The identifier of the resource.
    :type id: str
    :param name: The name of the resource.
    :type name: str
    :param type: The type of the resource.
    :type type: str
    :param location: The location of the resource.
    :type location: str
    :param tags: The tags of the resource.
    :type tags: dict
    """

    _attribute_map = {
        'display_name': {'key': 'properties.displayName', 'type': 'str'},
        'uri': {'key': 'properties.uri', 'type': 'str'},
        'source_type': {'key': 'properties.sourceType', 'type': 'str'},
        'folder_path': {'key': 'properties.folderPath', 'type': 'str'},
        'arm_template_folder_path': {'key': 'properties.armTemplateFolderPath', 'type': 'str'},
        'branch_ref': {'key': 'properties.branchRef', 'type': 'str'},
        'security_token': {'key': 'properties.securityToken', 'type': 'str'},
        'status': {'key': 'properties.status', 'type': 'str'},
        'created_date': {'key': 'properties.createdDate', 'type': 'iso-8601'},
        'provisioning_state': {'key': 'properties.provisioningState', 'type': 'str'},
        'unique_identifier': {'key': 'properties.uniqueIdentifier', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, display_name=None, uri=None, source_type=None, folder_path=None, arm_template_folder_path=None, branch_ref=None, security_token=None, status=None, created_date=None, provisioning_state=None, unique_identifier=None, id=None, name=None, type=None, location=None, tags=None):
        self.display_name = display_name
        self.uri = uri
        self.source_type = source_type
        self.folder_path = folder_path
        self.arm_template_folder_path = arm_template_folder_path
        self.branch_ref = branch_ref
        self.security_token = security_token
        self.status = status
        self.created_date = created_date
        self.provisioning_state = provisioning_state
        self.unique_identifier = unique_identifier
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags

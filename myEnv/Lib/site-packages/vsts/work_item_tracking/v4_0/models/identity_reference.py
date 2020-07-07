# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .identity_ref import IdentityRef


class IdentityReference(IdentityRef):
    """IdentityReference.

    :param directory_alias:
    :type directory_alias: str
    :param display_name:
    :type display_name: str
    :param image_url:
    :type image_url: str
    :param inactive:
    :type inactive: bool
    :param is_aad_identity:
    :type is_aad_identity: bool
    :param is_container:
    :type is_container: bool
    :param profile_url:
    :type profile_url: str
    :param unique_name:
    :type unique_name: str
    :param url:
    :type url: str
    :param id:
    :type id: str
    :param name: Legacy back-compat property. This has been the WIT specific value from Constants. Will be hidden (but exists) on the client unless they are targeting the newest version
    :type name: str
    """

    _attribute_map = {
        'directory_alias': {'key': 'directoryAlias', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'image_url': {'key': 'imageUrl', 'type': 'str'},
        'inactive': {'key': 'inactive', 'type': 'bool'},
        'is_aad_identity': {'key': 'isAadIdentity', 'type': 'bool'},
        'is_container': {'key': 'isContainer', 'type': 'bool'},
        'profile_url': {'key': 'profileUrl', 'type': 'str'},
        'unique_name': {'key': 'uniqueName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, directory_alias=None, display_name=None, image_url=None, inactive=None, is_aad_identity=None, is_container=None, profile_url=None, unique_name=None, url=None, id=None, name=None):
        super(IdentityReference, self).__init__(directory_alias=directory_alias, display_name=display_name, image_url=image_url, inactive=inactive, is_aad_identity=is_aad_identity, is_container=is_container, profile_url=profile_url, unique_name=unique_name, url=url)
        self.id = id
        self.name = name

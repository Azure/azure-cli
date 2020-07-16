# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.paging import Paged


class VaultPaged(Paged):
    """
    A paging container for iterating over a list of :class:`Vault <azure.mgmt.keyvault.v2020_04_01.models.Vault>` object
    """

    _attribute_map = {
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'current_page': {'key': 'value', 'type': '[Vault]'}
    }

    def __init__(self, *args, **kwargs):

        super(VaultPaged, self).__init__(*args, **kwargs)
class DeletedVaultPaged(Paged):
    """
    A paging container for iterating over a list of :class:`DeletedVault <azure.mgmt.keyvault.v2020_04_01.models.DeletedVault>` object
    """

    _attribute_map = {
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'current_page': {'key': 'value', 'type': '[DeletedVault]'}
    }

    def __init__(self, *args, **kwargs):

        super(DeletedVaultPaged, self).__init__(*args, **kwargs)
class ResourcePaged(Paged):
    """
    A paging container for iterating over a list of :class:`Resource <azure.mgmt.keyvault.v2020_04_01.models.Resource>` object
    """

    _attribute_map = {
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'current_page': {'key': 'value', 'type': '[Resource]'}
    }

    def __init__(self, *args, **kwargs):

        super(ResourcePaged, self).__init__(*args, **kwargs)
class OperationPaged(Paged):
    """
    A paging container for iterating over a list of :class:`Operation <azure.mgmt.keyvault.v2020_04_01.models.Operation>` object
    """

    _attribute_map = {
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'current_page': {'key': 'value', 'type': '[Operation]'}
    }

    def __init__(self, *args, **kwargs):

        super(OperationPaged, self).__init__(*args, **kwargs)
class SecretPaged(Paged):
    """
    A paging container for iterating over a list of :class:`Secret <azure.mgmt.keyvault.v2020_04_01.models.Secret>` object
    """

    _attribute_map = {
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'current_page': {'key': 'value', 'type': '[Secret]'}
    }

    def __init__(self, *args, **kwargs):

        super(SecretPaged, self).__init__(*args, **kwargs)
class ManagedHsmPaged(Paged):
    """
    A paging container for iterating over a list of :class:`ManagedHsm <azure.mgmt.keyvault.v2020_04_01.models.ManagedHsm>` object
    """

    _attribute_map = {
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'current_page': {'key': 'value', 'type': '[ManagedHsm]'}
    }

    def __init__(self, *args, **kwargs):

        super(ManagedHsmPaged, self).__init__(*args, **kwargs)

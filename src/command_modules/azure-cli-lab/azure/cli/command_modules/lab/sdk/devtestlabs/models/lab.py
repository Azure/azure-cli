# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class Lab(Model):
    """A lab.

    :param default_storage_account: The lab's default storage account.
    :type default_storage_account: str
    :param default_premium_storage_account: The lab's default premium storage
     account.
    :type default_premium_storage_account: str
    :param artifacts_storage_account: The lab's artifact storage account.
    :type artifacts_storage_account: str
    :param premium_data_disk_storage_account: The lab's premium data disk
     storage account.
    :type premium_data_disk_storage_account: str
    :param vault_name: The lab's Key vault.
    :type vault_name: str
    :param lab_storage_type: Type of storage used by the lab. It can be either
     Premium or Standard. Default is Premium. Possible values include:
     'Standard', 'Premium'
    :type lab_storage_type: str or :class:`StorageType
     <azure.mgmt.devtestlabs.models.StorageType>`
    :param created_date: The creation date of the lab.
    :type created_date: datetime
    :param storage_details: The storage properties.
    :type storage_details: :class:`LabStorageProperties
     <azure.mgmt.devtestlabs.models.LabStorageProperties>`
    :param premium_data_disks: The setting to enable usage of premium data
     disks.
     When its value is 'Enabled', creation of standard or premium data disks is
     allowed.
     When its value is 'Disabled', only creation of standard data disks is
     allowed. Possible values include: 'Disabled', 'Enabled'
    :type premium_data_disks: str or :class:`PremiumDataDisk
     <azure.mgmt.devtestlabs.models.PremiumDataDisk>`
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
        'default_storage_account': {'key': 'properties.defaultStorageAccount', 'type': 'str'},
        'default_premium_storage_account': {'key': 'properties.defaultPremiumStorageAccount', 'type': 'str'},
        'artifacts_storage_account': {'key': 'properties.artifactsStorageAccount', 'type': 'str'},
        'premium_data_disk_storage_account': {'key': 'properties.premiumDataDiskStorageAccount', 'type': 'str'},
        'vault_name': {'key': 'properties.vaultName', 'type': 'str'},
        'lab_storage_type': {'key': 'properties.labStorageType', 'type': 'str'},
        'created_date': {'key': 'properties.createdDate', 'type': 'iso-8601'},
        'storage_details': {'key': 'properties.storageDetails', 'type': 'LabStorageProperties'},
        'premium_data_disks': {'key': 'properties.premiumDataDisks', 'type': 'str'},
        'provisioning_state': {'key': 'properties.provisioningState', 'type': 'str'},
        'unique_identifier': {'key': 'properties.uniqueIdentifier', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, default_storage_account=None, default_premium_storage_account=None, artifacts_storage_account=None, premium_data_disk_storage_account=None, vault_name=None, lab_storage_type=None, created_date=None, storage_details=None, premium_data_disks=None, provisioning_state=None, unique_identifier=None, id=None, name=None, type=None, location=None, tags=None):
        self.default_storage_account = default_storage_account
        self.default_premium_storage_account = default_premium_storage_account
        self.artifacts_storage_account = artifacts_storage_account
        self.premium_data_disk_storage_account = premium_data_disk_storage_account
        self.vault_name = vault_name
        self.lab_storage_type = lab_storage_type
        self.created_date = created_date
        self.storage_details = storage_details
        self.premium_data_disks = premium_data_disks
        self.provisioning_state = provisioning_state
        self.unique_identifier = unique_identifier
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags

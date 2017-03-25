# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class LabStorageProperties(Model):
    """LabStorageProperties.

    :param default_storage_account: The default storage account properties.
    :type default_storage_account: :class:`StorageProperties
     <azure.mgmt.devtestlabs.models.StorageProperties>`
    :param default_premium_storage_account: The default premium storage
     account properties.
    :type default_premium_storage_account: :class:`StorageProperties
     <azure.mgmt.devtestlabs.models.StorageProperties>`
    :param artifacts_storage_account: The artifacts storage account
     properties.
    :type artifacts_storage_account: :class:`StorageProperties
     <azure.mgmt.devtestlabs.models.StorageProperties>`
    :param premium_data_disk_storage_account: The premium data disk storage
     account properties.
    :type premium_data_disk_storage_account: :class:`StorageProperties
     <azure.mgmt.devtestlabs.models.StorageProperties>`
    """

    _attribute_map = {
        'default_storage_account': {'key': 'defaultStorageAccount', 'type': 'StorageProperties'},
        'default_premium_storage_account': {'key': 'defaultPremiumStorageAccount', 'type': 'StorageProperties'},
        'artifacts_storage_account': {'key': 'artifactsStorageAccount', 'type': 'StorageProperties'},
        'premium_data_disk_storage_account': {'key': 'premiumDataDiskStorageAccount', 'type': 'StorageProperties'},
    }

    def __init__(self, default_storage_account=None, default_premium_storage_account=None, artifacts_storage_account=None, premium_data_disk_storage_account=None):
        self.default_storage_account = default_storage_account
        self.default_premium_storage_account = default_premium_storage_account
        self.artifacts_storage_account = artifacts_storage_account
        self.premium_data_disk_storage_account = premium_data_disk_storage_account

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-arguments

from azure.cli.core.profiles import get_api_version, get_versioned_models
from azure.cli.core.profiles.shared import ResourceType

from azure.cli.command_modules.storage._factory import storage_client_factory


if get_api_version(ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS) in ['2016-12-01']:

    def create_storage_account(resource_group_name, account_name, sku, location,
                               kind=get_versioned_models(ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS, 'Kind').storage.value, tags=None, custom_domain=None,
                               encryption=None, access_tier=None):
        StorageAccountCreateParameters, Kind, Sku, CustomDomain, AccessTier = get_versioned_models(ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS, 'StorageAccountCreateParameters', 'Kind', 'Sku', 'CustomDomain', 'AccessTier')
        scf = storage_client_factory()
        params = StorageAccountCreateParameters(
            sku=Sku(sku),
            kind=Kind(kind),
            location=location,
            tags=tags,
            custom_domain=CustomDomain(custom_domain, None) if custom_domain else None,
            encryption=encryption,
            access_tier=AccessTier(access_tier) if access_tier else None)
        return scf.storage_accounts.create(resource_group_name, account_name, params)

    def update_storage_account(instance, sku=None, tags=None, custom_domain=None,
                               use_subdomain=None, encryption=None, access_tier=None):
        StorageAccountUpdateParameters, Sku, CustomDomain, AccessTier = get_versioned_models(ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS, 'StorageAccountUpdateParameters', 'Sku', 'CustomDomain', 'AccessTier')
        domain = instance.custom_domain
        if custom_domain is not None:
            domain = CustomDomain(custom_domain)
            if use_subdomain is not None:
                domain.name = use_subdomain == 'true'

        params = StorageAccountUpdateParameters(
            sku=Sku(sku) if sku is not None else instance.sku,
            tags=tags if tags is not None else instance.tags,
            custom_domain=domain,
            encryption=encryption if encryption is not None else instance.encryption,
            access_tier=AccessTier(access_tier) if access_tier is not None else instance.access_tier
        )
        return params

elif get_api_version(ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS) in ['2015-06-15']:

    def create_storage_account(resource_group_name, account_name, location, account_type, tags=None):
        StorageAccountCreateParameters, AccountType = get_versioned_models(ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS, 'StorageAccountCreateParameters', 'AccountType')
        scf = storage_client_factory()
        params = StorageAccountCreateParameters(location, AccountType(account_type), tags)
        return scf.storage_accounts.create(resource_group_name, account_name, params)

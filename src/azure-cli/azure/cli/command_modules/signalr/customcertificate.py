# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long


from azure.mgmt.signalr.models import (
    CustomCertificate
)

from azure.mgmt.signalr._signal_rmanagement_client import (
    SignalRCustomCertificatesOperations
)


def custom_certificate_create(client: SignalRCustomCertificatesOperations, resource_group_name, signalr_name, name, keyvault_base_uri, keyvault_secret_name, keyvault_secret_version=None):
    custom_certificate = CustomCertificate(key_vault_base_uri=keyvault_base_uri, key_vault_secret_name=keyvault_secret_name, keyvault_secret_version=keyvault_secret_version)

    return client.begin_create_or_update(resource_group_name, signalr_name, name, custom_certificate)


def custom_certificate_delete(client: SignalRCustomCertificatesOperations, resource_group_name, signalr_name, name):
    return client.delete(resource_group_name, signalr_name, name)


def custom_certificate_show(client: SignalRCustomCertificatesOperations, resource_group_name, signalr_name, name):
    return client.get(resource_group_name, signalr_name, name)


def custom_certificate_list(client: SignalRCustomCertificatesOperations, resource_group_name, signalr_name):
    return client.list(resource_group_name, signalr_name)


def get_custom_certificate(client: SignalRCustomCertificatesOperations, resource_group_name, signalr_name, name):
    return client.get(resource_group_name, signalr_name, name)


def set_custom_certificate(client: SignalRCustomCertificatesOperations, resource_group_name, signalr_name, name, parameters):
    return client.begin_create_or_update(resource_group_name, signalr_name, name, parameters)


def update(instance: CustomCertificate, keyvault_base_uri=None, keyvault_secret_name=None, keyvault_secret_version=None):
    if keyvault_base_uri is not None:
        instance.key_vault_base_uri = keyvault_base_uri
    if keyvault_secret_name is not None:
        instance.key_vault_secret_name = keyvault_secret_name
    if keyvault_secret_version is not None:
        instance.key_vault_secret_version = keyvault_secret_version
    return instance

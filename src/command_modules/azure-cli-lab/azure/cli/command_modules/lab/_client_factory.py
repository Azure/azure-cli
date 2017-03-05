# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def get_devtestlabs_management_client(_):
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(DevTestLabsClient)


def get_devtestlabs_virtual_machine_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).virtual_machine


def get_devtestlabs_lab_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).lab


def get_devtestlabs_custom_image_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).custom_image


def get_devtestlabs_gallery_image_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).gallery_image


def get_devtestlabs_artifact_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).artifact


def get_devtestlabs_virtual_network_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).virtual_network

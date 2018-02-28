# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def accessrights_converter(accessrights):
    from azure.mgmt.servicebus.models.service_bus_management_client_enums import AccessRights
    accessrights_new = []
    if 'Send' in accessrights:
        accessrights_new.append(AccessRights.send)
    if 'Manage' in accessrights:
        accessrights_new.append(AccessRights.manage)
    if 'Listen' in accessrights:
        accessrights_new.append(AccessRights.listen)

    return accessrights_new

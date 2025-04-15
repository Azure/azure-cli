# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.mgmt.signalr.models import (
    ManagedIdentity,
    SignalRResource)

SYSTEM_ASSIGNED_IDENTITY_ALIAS = '[system]'


def signalr_msi_assign(client, resource_group_name, signalr_name, identity):
    msiType, user_identity = _analyze_identity(identity)

    identity = ManagedIdentity(type=msiType, user_assigned_identities={user_identity: {}} if user_identity else None)
    parameter = SignalRResource(location=None, identity=identity)
    return client.begin_update(resource_group_name, signalr_name, parameter)


def signalr_msi_remove(client, resource_group_name, signalr_name):
    identity = ManagedIdentity(type="None")
    parameter = SignalRResource(location=None, identity=identity)
    return client.begin_update(resource_group_name, signalr_name, parameter)


def signalr_msi_show(client, resource_group_name, signalr_name):
    res = client.get(resource_group_name, signalr_name)
    return res.identity


def _analyze_identity(identity):
    if identity == SYSTEM_ASSIGNED_IDENTITY_ALIAS:
        return "SystemAssigned", None
    return "UserAssigned", identity

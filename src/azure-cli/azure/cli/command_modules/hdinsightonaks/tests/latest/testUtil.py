# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

# Set your auth info.
# auth info for cluster version 1.1
def authorization_info_version11():
    msiClientId = '00000000-0000-0000-0000-000000000000'  # Managed Service Identity ClientId
    msiObjectId = '00000000-0000-0000-0000-000000000000'  # Managed Service Identity ObjectId

    authorizationUserId = '00000000-0000-0000-0000-000000000000'
    identityProfileMsiResourceId = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/PSGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/psmsi'

    return '--assigned-identity-object-id {} --assigned-identity-client-id {} --authorization-user-id {} --assigned-identity-id {}' \
        .format(msiObjectId, msiClientId, authorizationUserId, identityProfileMsiResourceId)

# auth info for cluster version 1.2


def authorization_info_version12():
   
    return '--identity-list \'[{"client-id":"00000000-0000-0000-0000-000000000000","object-id":"00000000-0000-0000-0000-000000000000","resource-id":"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/hilocli-test/providers/Microsoft.ManagedIdentity/userAssignedIdentities/tfmsi11","type":"cluster"}]\' --authorization-user-id "77e9262b-339d-4ac4-a044-8884fdf73071"'

# Config flink cluster cpu and memory.


def flink_config_str():
    return ' --job-manager-cpu 1 --job-manager-memory 2000 --task-manager-cpu 6 --task-manager-memory 49016 '

# Config cluster autoscale config.


def autoScale_config_str():
    return "--enable-autoscale --autoscale-profile-type ScheduleBased --decommission-time -1 --schedule-default-count 5 --schedule-time-zone 'UTC' --schedule-schedules \"[{count:10,days:[Monday,Sunday],end-time:'9:00',start-time:'8:00'}]\""


def logAnalyticProfileWorkspaceId():

    return "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/hilocli-test/providers/microsoft.operationalinsights/workspaces/hiloworkspace"
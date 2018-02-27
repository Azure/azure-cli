# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.managementpartner.models import PartnerResponse


def print_managementpartner(partnerresponse):
    partner = {}
    partner["objectId"] = partnerresponse.object_id
    partner["partnerId"] = partnerresponse.partner_id
    partner["tenantId"] = partnerresponse.tenant_id
    partner["state"] = partnerresponse.state
    return partner

def xstr(s):
    if s is None:
        return ""
    return str(s)

def create_managementpartner(client, partner_id):
    return print_managementpartner(client.create(partner_id))


def get_managementpartner(client, partner_id=None):
    return print_managementpartner(client.get(xstr(partner_id)))


def update_managementpartner(client, partner_id):
    return print_managementpartner(client.update(partner_id))

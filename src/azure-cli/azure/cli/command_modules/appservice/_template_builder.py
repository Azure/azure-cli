# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def build_dns_zone(domain_name, dependencies=None):
    dependencies = dependencies or []
    dns_zone_resource = {
        "type": "Microsoft.Network/dnszones",
        "name": domain_name,
        "apiVersion": "2018-05-01",
        "location": "global",
        "dependsOn": dependencies,
        "properties": {
            "zoneType": "Public"
        }
    }
    return dns_zone_resource


def build_domain(domain_name, local_ip_address, current_time, address1, address2, city,
                 country, postal_code, state, email, fax, job_title, name_first,
                 name_last, name_middle, organization, phone, dns_zone_id, privacy,
                 auto_renew, agreement_keys, tags, dependencies=None):
    dependencies = dependencies or []

    contact_info = {
        'AddressMailing': {
            'Address1': address1,
            'Address2': address2,
            'City': city,
            'Country': country,
            'PostalCode': postal_code,
            'State': state
        },
        'Email': email,
        'Fax': fax,
        'JobTitle': job_title,
        'NameFirst': name_first,
        'NameLast': name_last,
        'NameMiddle': name_middle,
        'Organization': organization,
        'Phone': phone
    }

    domain_resource = {
        "type": "Microsoft.DomainRegistration/domains",
        "name": domain_name,
        "apiVersion": "2018-02-01",
        "location": "global",
        "dependsOn": dependencies,
        "tags": tags,
        "properties": {
            "consent": {
                "agreementKeys": agreement_keys,
                "agreedBy": local_ip_address,
                "agreedAt": current_time
            },
            "ContactAdmin": contact_info,
            "ContactBilling": contact_info,
            "ContactRegistrant": contact_info,
            "ContactTech": contact_info,
            "privacy": privacy,
            "autoRenew": auto_renew,
            "dnsType": "AzureDns",
            "targetDnsType": "AzureDns",
            "dnsZoneId": dns_zone_id
        },
        "resources": []
    }
    return domain_resource

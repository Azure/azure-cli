# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation, DeploymentOutputLongRunningOperation
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait, random_string
from knack.util import CLIError
from knack.log import get_logger

from ._client_factory import web_client_factory, dns_client_factory

logger = get_logger(__name__)

def create_domain(cmd, resource_group_name, hostname, contact_info, privacy=True, auto_renew=True,
                  accept_hostname_purchase_terms=False, tags=None, dryrun=False):
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.appservice._template_builder import (build_dns_zone, build_domain)
    from datetime import datetime
    import socket
    import json

    tags = tags or {}

    if not accept_hostname_purchase_terms and not dryrun:
        raise CLIError("To purchase and create your custom domain '{}', you must view the terms and conditions using the command `az appservice domain show-terms`,"
                       " and accept these terms and conditions using the --accept-hostname-purchase-terms flag".format(hostname))

    contact_info = json.loads(contact_info)
    contact_info = verify_contact_info_and_format(contact_info)

    current_time = str(datetime.utcnow()).replace('+00:00', 'Z')
    local_ip_address=''
    try:
        local_ip_address = socket.gethostbyname(socket.gethostname())
    except:
        raise CLIError("Unable to get IP address")

    web_client = web_client_factory(cmd.cli_ctx)
    hostname_availability = web_client.domains.check_availability(name=hostname)

    if dryrun:
        logger.warning("Custom domain will be purchased with the below configuration. Re-run command "
                    "without the --dryrun flag to purchase & create the custom domain")
        dry_run_params = contact_info.copy()
        dry_run_params.update({
            "hostname": hostname,
            "resource_group_name": resource_group_name,
            "privacy": bool(privacy),
            "auto_renew": bool(auto_renew),
            "accept_hostname_purchase_terms": bool(accept_hostname_purchase_terms),
            "hostname_available": bool(hostname_availability.available),
            "price": "$11.99 USD" if hostname_availability.available else "N/A"
        })
        dry_run_str = r""" {
                    "hostname" : "%(hostname)s",
                    "resource_group" : "%(resource_group_name)s",
                    "contact_info": {
                            "address1": "%(address1)s",
                            "address2": "%(address2)s",
                            "city": "%(city)s",
                            "country": "%(country)s",
                            "postal_code": "%(postal_code)s",
                            "state": "%(state)s",
                            "email": "%(email)s",
                            "fax": "%(fax)s",
                            "job_title": "%(job_title)s",
                            "name_first": "%(name_first)s",
                            "name_last": "%(name_last)s",
                            "name_middle": "%(name_middle)s",
                            "organization": "%(organization)s",
                            "phone": "%(phone)s"
                        },
                    "privacy": "%(privacy)s",
                    "auto_renew": "%(auto_renew)s",
                    "accepted_hostname_purchase_terms": "%(accept_hostname_purchase_terms)s",
                    "hostname_available": "%(hostname_available)s",
                    "price": "%(price)s"
                    }
                    """ % dry_run_params
        return json.loads(dry_run_str)

    if not hostname_availability.available:
        raise CLIError("Custom domain name '{}' is not available. Please try again with a new hostname.".format(hostname))

    dns_zone_id = "[resourceId('Microsoft.Network/dnszones', '{}')]".format(hostname)

    master_template = ArmTemplateBuilder()
    dns_zone_resource = build_dns_zone(hostname)
    domain_resource = build_domain(domain_name=hostname,
                                  local_ip_address=local_ip_address,
                                  current_time=current_time,
                                  address1=contact_info['address1'],
                                  address2=contact_info['address2'],
                                  city=contact_info['city'],
                                  country=contact_info['country'],
                                  postal_code=contact_info['postal_code'],
                                  state=contact_info['state'],
                                  email=contact_info['email'],
                                  fax=contact_info['fax'],
                                  job_title=contact_info['job_title'],
                                  name_first=contact_info['name_first'],
                                  name_last=contact_info['name_last'],
                                  name_middle=contact_info['name_middle'],
                                  organization=contact_info['organization'],
                                  phone=contact_info['phone'],
                                  dns_zone_id=dns_zone_id,
                                  privacy=privacy,
                                  auto_renew=auto_renew,
                                  tags=tags,
                                  dependencies=[dns_zone_id])

    master_template.add_resource(dns_zone_resource)
    master_template.add_resource(domain_resource)

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'domain_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')    

    if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
        Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
        deployment = Deployment(properties=properties)

        deployment_result = DeploymentOutputLongRunningOperation(cmd.cli_ctx)(
            sdk_no_wait(False, client.create_or_update, resource_group_name, deployment_name, deployment))
    else:
        deployment_result = DeploymentOutputLongRunningOperation(cmd.cli_ctx)(
            sdk_no_wait(False, client.create_or_update, resource_group_name, deployment_name, properties))
    
    return deployment_result


def show_domain_purchase_terms(cmd, resource_group_name, hostname):
    web_client = web_client_factory(cmd.cli_ctx)
    hostname_availability = web_client.domains.check_availability(name=hostname)

    legal_terms_string = ("By purchasing and creating an appservice domain using the `az appservice domain create` command with the --accept-hostname-purchase-terms flag, I (a) acknowledge that domain registration is provided by GoDaddy.com, LLC ('Go Daddy'), who is my registrar of record, "
        "(b) agree to the legal terms provided below, (c) agree to share my contact information and IP address with Go Daddy, "
        "(d) authorize Microsoft to charge or bill my current payment method for the price of the domain ($11.99) including applicable taxes "
        "on a one-time basis or, if auto-renewal is selected, an annual basis until I discontinue auto-renewal, and (e) agree "
        "that Microsoft may share my contact information and these transaction details with GoDaddy. Microsoft does not provide rights for non-Microsoft "
        "products or services.")

    additional_terms_string = ("No domain name registration will be deemed effective unless and until the relevant registry accepts your application and activates your domain "
        "name registration. If you have selected automatic renewal, Go Daddy will automatically renew your domain name registration(s) on an annual basis. "
        "You may cancel automatic renewal at any time. If you have not selected automatic renewal, you may renew an expired domain name registration at "
        "Microsoft’s then-current rate for domain names up to 18 days after the expiration date. After such 18-day period, and until the 42nd day after "
        "the expiration date (the “Redemption Period”), renewal will be subject to an additional 80.00 USD fee. If you fail to renew your domain name "
        "registration prior to expiration of the Redemption Period, the domain name may be reassigned by Go Daddy to auction or backorder holders, or "
        "dropped to the registry. If your domain name is dropped to the registry, it may still remain in redeemable status for 30 days, during which time "
        "you may request renewal of your domain name. You may cancel your domain name registration within 5 days after the registration date for a full "
        "refund. No cancellations will be accepted and no refunds will be granted more than 5 days after the registration date.")

    terms = {
        "hostname": hostname,
        "hostname_available": hostname_availability.available,
        "hostname_purchase_price": "$11.99 USD" if hostname_availability.available else "N/A",
        "legal_terms": legal_terms_string,
        "GoDaddy_domain_registration_and_customer_service_agreement": "https://www.godaddy.com/legal/agreements/domain-name-registration-agreement",
        "ICANN_rights_and_responsibilities_policy": "https://www.icann.org/resources/pages/responsibilities-2014-03-14-en",
        "legal_terms_additional": additional_terms_string,
        "domain_registration_agreement": "https://www.secureserver.net/legal-agreement?id=reg_sa&pageid=reg_sa&pl_id=510456j",
        "domains_by_proxy_agreement": "https://www.secureserver.net/legal-agreement?id=domain_nameproxy&pageid=domain_nameproxy&pl_id=510456"
    }
    return terms


def verify_contact_info_and_format(contact_info):
    return_contact_info = {}
    required_keys = ['name_first', 'name_last', 'email', 'phone', 'address1', 'country', 'state', 'city', 'postal_code']
    for required_key in required_keys:
        if not (required_key in contact_info and 'value' in contact_info[required_key] and contact_info[required_key]['value']):
            raise CLIError("Missing value in contact info: {}".format(required_key))

    import re

    # GoDaddy regex
    _phone_regex = r"^\+([0-9]){1,3}\.([0-9]\ ?){5,14}$"
    _person_name_regex = r"^[a-zA-Z0-9\-.,\(\)\\\@&' ]*$"
    _email_regex = r"^(?:[\w\!\#\$\%\&\'\*\+\-\/\=\?\^\`\{\|\}\~]+\.)*[\w\!\#\$\%\&\'\*\+\-\/\=\?\^\`\{\|\}\~]+@(?:(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-](?!\.)){0,61}[a-zA-Z0-9]?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9\-](?!$)){0,61}[a-zA-Z0-9]?)|(?:\[(?:(?:[01]?\d{1,2}|2[0-4]\d|25[0-5])\.){3}(?:[01]?\d{1,2}|2[0-4]\d|25[0-5])\]))$"
    _city_regex = r"^[a-zA-Z0-9\-.,' ]+$"
    _address_regex = r"^[a-zA-Z0-9\-.,'#*@/& ]+$"
    _postal_code_regex = r"^[a-zA-Z0-9 .\\-]+$"

    # Validate required values
    if not re.match(_phone_regex, contact_info['phone']['value']):
        raise CLIError('Invalid value: phone number must match pattern +areacode.phonenumber, for example "+1.0000000000"')
    return_contact_info['phone'] = contact_info['phone']['value']

    if not re.match(_person_name_regex, contact_info['name_first']['value']):
        raise CLIError('Invalid value: first name')
    if len(contact_info['name_first']['value']) > 30:
        raise CLIError('Invalid value: first name must have a length of at most 30')
    return_contact_info['name_first'] = contact_info['name_first']['value']

    if not re.match(_person_name_regex, contact_info['name_last']['value']):
        raise CLIError('Invalid value: last name')
    if len(contact_info['name_last']['value']) > 30:
        raise CLIError('Invalid value: last name must have a length of at most 30')
    return_contact_info['name_last'] = contact_info['name_last']['value']

    if not re.match(_email_regex, contact_info['email']['value']):
        raise CLIError('Invalid value: email')
    return_contact_info['email'] = contact_info['email']['value']

    if not re.match(_address_regex, contact_info['address1']['value']):
        raise CLIError('Invalid value: address1')
    if len(contact_info['address1']['value']) > 41:
        raise CLIError('Invalid value: address1 must have a length of at most 41')
    return_contact_info['address1'] = contact_info['address1']['value']

    allowed_countries = ["AC", "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ", "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BM", "BN", "BO", "BQ", "BR", "BS", "BT", "BV", "BW", "BY", "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN", "CO", "CR", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO", "DZ", "EC", "EE", "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM", "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IS", "IT", "JE", "JM", "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN", "KR", "KV", "KW", "KY", "KZ", "LA", "LB", "LC", "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MG", "MH", "MK", "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ", "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW", "SA", "SB", "SC", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "ST", "SV", "SX", "SZ", "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TP", "TR", "TT", "TV", "TW", "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI", "VN", "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW"]
    if contact_info['country']['value'] not in allowed_countries:
        raise CLIError('Invalid value: country is not one of the following values: {}'.format(allowed_countries))
    return_contact_info['country'] = contact_info['country']['value']

    if not (2 <= len(contact_info['state']['value']) <= 30):
        raise CLIError('Invalid value: state must have a length between 2 and 30')
    return_contact_info['state'] = contact_info['state']['value']

    if not re.match(_city_regex, contact_info['city']['value']):
        raise CLIError('Invalid value: city')
    if len(contact_info['city']['value']) > 30:
        raise CLIError('Invalid value: city must have a length of at most 30')
    return_contact_info['city'] = contact_info['city']['value']

    if not re.match(_postal_code_regex, contact_info['postal_code']['value']):
        raise CLIError('Invalid value: postal code')
    if not (2 <= len(contact_info['postal_code']['value']) <= 10):
        raise CLIError('Invalid value: postal code must have a length between 2 and 10')
    return_contact_info['postal_code'] = contact_info['postal_code']['value']

    # Validate optional params
    if 'fax' in contact_info and 'value' in contact_info['fax'] and contact_info['fax']['value']:
        if not re.match(_phone_regex, contact_info['fax']['value']):
            raise CLIError('Invalid value: fax number must match pattern +areacode.phonenumber, for example "+1.0000000000"')
        return_contact_info['fax'] = contact_info['fax']['value']
    else:
        return_contact_info['fax'] = ''

    if 'job_title' in contact_info and 'value' in contact_info['job_title'] and contact_info['job_title']['value']:
        if len(contact_info['job_title']['value']) > 41:
            raise CLIError('Invalid value: job title must have a length of at most 41')
        return_contact_info['job_title'] = contact_info['job_title']['value']
    else:
        return_contact_info['job_title'] = ''

    if 'name_middle' in contact_info and 'value' in contact_info['name_middle'] and contact_info['name_middle']['value']:
        if not re.match(_person_name_regex, contact_info['name_middle']['value']):
            raise CLIError('Invalid value: middle name')
        if len(contact_info['name_middle']['value']) > 30:
            raise CLIError('Invalid value: middle name must have a length of at most 30')
        return_contact_info['name_middle'] = contact_info['name_middle']['value']
    else:
        return_contact_info['name_middle'] = ''

    if 'organization' in contact_info and 'value' in contact_info['organization'] and contact_info['organization']['value']:
        if len(contact_info['organization']['value']) > 41:
            raise CLIError('Invalid value: organization must have a length of at most 41')
        return_contact_info['organization'] = contact_info['organization']['value']
    else:
        return_contact_info['organization'] = ''

    if 'address2' in contact_info and 'value' in contact_info['address2'] and contact_info['address2']['value']:
        if not re.match(_address_regex, contact_info['address2']['value']):
            raise CLIError('Invalid value: address2')
        if len(contact_info['address2']['value']) > 41:
            raise CLIError('Invalid value: address2 must have a length of at most 41')
        return_contact_info['address2'] = contact_info['address2']['value']
    else:
        return_contact_info['address2'] = ''

    return return_contact_info


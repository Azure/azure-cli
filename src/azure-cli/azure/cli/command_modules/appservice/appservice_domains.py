# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.commands import DeploymentOutputLongRunningOperation
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait, random_string
from azure.mgmt.web.models import NameIdentifier
from knack.util import CLIError
from knack.log import get_logger

from ._client_factory import web_client_factory

logger = get_logger(__name__)


def create_domain(cmd, resource_group_name, hostname, contact_info, privacy=True, auto_renew=True,  # pylint: disable=too-many-locals
                  accept_terms=False, tags=None, dryrun=False, no_wait=False):
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.appservice._template_builder import (build_dns_zone, build_domain)
    from datetime import datetime
    import socket
    import json

    tags = tags or {}

    if not accept_terms and not dryrun:
        raise CLIError("To purchase and create your custom domain '{}', you must view the terms and conditions "
                       "using the command `az appservice domain show-terms`, and accept these terms and "
                       "conditions using the --accept-terms flag".format(hostname))

    try:
        contact_info = json.loads(contact_info)
    except Exception:
        raise CLIError('Unable to load contact info. Please verify the path to your contact info file, '
                       'and that the format matches the sample found at the following link: '
                       'https://github.com/AzureAppServiceCLI/appservice_domains_templates'
                       '/blob/master/contact_info.json')
    contact_info = verify_contact_info_and_format(contact_info)

    current_time = str(datetime.utcnow()).replace('+00:00', 'Z')
    local_ip_address = ''
    try:
        local_ip_address = socket.gethostbyname(socket.gethostname())
    except:
        raise CLIError("Unable to get IP address")

    # TODO remove api_version when Microsoft.DomainRegistration supports a later version
    web_client = web_client_factory(cmd.cli_ctx, api_version="2021-01-15")
    hostname_availability = web_client.domains.check_availability(NameIdentifier(name=hostname))

    if not hostname_availability.available:
        raise ValidationError("Custom domain name '{}' is not available. Please try again "
                              "with a new hostname.".format(hostname))

    tld = '.'.join(hostname.split('.')[1:])
    TopLevelDomainAgreementOption = cmd.get_models('TopLevelDomainAgreementOption')
    domain_agreement_option = TopLevelDomainAgreementOption(include_privacy=bool(privacy), for_transfer=False)
    agreements = web_client.top_level_domains.list_agreements(name=tld, agreement_option=domain_agreement_option)
    agreement_keys = [agreement.agreement_key for agreement in agreements]

    if dryrun:
        logger.warning("Custom domain will be purchased with the below configuration. Re-run command "
                       "without the --dryrun flag to purchase & create the custom domain")
        dry_run_params = contact_info.copy()
        dry_run_params.update({
            "hostname": hostname,
            "resource_group_name": resource_group_name,
            "privacy": bool(privacy),
            "auto_renew": bool(auto_renew),
            "agreement_keys": agreement_keys,
            "accept_terms": bool(accept_terms),
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
                    "accepted_hostname_purchase_terms": "%(accept_terms)s",
                    "agreement_keys": "%(agreement_keys)s",
                    "hostname_available": "%(hostname_available)s",
                    "price": "%(price)s"
                    }
                    """ % dry_run_params
        return json.loads(dry_run_str)

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
                                   agreement_keys=agreement_keys,
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
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)
    deployment_result = DeploymentOutputLongRunningOperation(cmd.cli_ctx)(
        sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment))

    return deployment_result


def show_domain_purchase_terms(cmd, hostname):
    from azure.mgmt.web.models import TopLevelDomainAgreementOption
    domain_identifier = NameIdentifier(name=hostname)
    web_client = web_client_factory(cmd.cli_ctx)
    hostname_availability = web_client.domains.check_availability(domain_identifier)
    if not hostname_availability.available:  # api returns false
        raise CLIError(" hostname: '{}' in not available. Please enter a valid hostname.".format(hostname))

    tld = '.'.join(hostname.split('.')[1:])
    domain_agreement_option = TopLevelDomainAgreementOption(include_privacy=True, for_transfer=True)
    agreements = web_client.top_level_domains.list_agreements(name=tld, agreement_option=domain_agreement_option)

    terms = {
        "hostname": hostname,
        "hostname_available": hostname_availability.available,
        "hostname_purchase_price": "$11.99 USD" if hostname_availability.available else None,
        "legal_terms":
            "https://storedomainslegalterms.blob.core.windows.net/domain-purchase-legal-terms/legal_terms.txt",
        "GoDaddy_domain_registration_and_customer_service_agreement":
            "https://www.godaddy.com/legal/agreements/domain-name-registration-agreement",
        "ICANN_rights_and_responsibilities_policy":
            "https://www.icann.org/resources/pages/responsibilities-2014-03-14-en"
    }

    for agreement in agreements:
        terms['_'.join(agreement.title.lower().split(' '))] = agreement.url

    return terms


def verify_contact_info_and_format(contact_info):
    # pylint: disable=too-many-statements, too-many-branches
    return_contact_info = {}
    required_keys = ['name_first', 'name_last', 'email', 'phone', 'address1', 'country', 'state', 'city', 'postal_code']
    for required_key in required_keys:
        if not (required_key in contact_info and 'value' in contact_info[required_key] and contact_info[required_key]['value']):  # pylint: disable=line-too-long
            raise CLIError("Missing value in contact info: {}".format(required_key))

    import re

    # GoDaddy regex
    _phone_regex = r"^\+([0-9]){1,3}\.([0-9]\ ?){5,14}$"
    _person_name_regex = r"^[a-zA-Z0-9\-.,\(\)\\\@&' ]*$"
    _email_regex = (
        r"^(?:[\w\!\#\$\%\&\'\*\+\-\/\=\?\^\`\{\|\}\~]+\.)*[\w\!\#\$\%\&\'\*\+\-\/\=\?\^\`\{\|\}\~]+@(?:(?:(?:"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9\-](?!\.)){0,61}[a-zA-Z0-9]?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9\-](?!$)){0,61}[a-zA-Z0-9]"
        r"?)|(?:\[(?:(?:[01]?\d{1,2}|2[0-4]\d|25[0-5])\.){3}(?:[01]?\d{1,2}|2[0-4]\d|25[0-5])\]))$"
    )
    _city_regex = r"^[a-zA-Z0-9\-.,' ]+$"
    _address_regex = r"^[a-zA-Z0-9\-.,'#*@/& ]+$"
    _postal_code_regex = r"^[a-zA-Z0-9 .\\-]+$"

    # Validate required values
    if not re.match(_phone_regex, contact_info['phone']['value']):
        raise CLIError('Invalid value: phone number must match pattern +areacode.phonenumber, '
                       'for example "+1.0000000000"')
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

    allowed_countries = [
        "AC", "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
        "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BM", "BN", "BO", "BQ", "BR", "BS", "BT", "BV",
        "BW", "BY", "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN", "CO", "CR", "CV",
        "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO", "DZ", "EC", "EE", "EG", "EH", "ER", "ES", "ET",
        "FI", "FJ", "FK", "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL", "GM", "GN",
        "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM", "HN", "HR", "HT", "HU", "ID", "IE", "IL",
        "IM", "IN", "IO", "IQ", "IS", "IT", "JE", "JM", "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN", "KR",
        "KV", "KW", "KY", "KZ", "LA", "LB", "LC", "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY", "MA", "MC",
        "MD", "ME", "MG", "MH", "MK", "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW",
        "MX", "MY", "MZ", "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ", "OM", "PA",
        "PE", "PF", "PG", "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS",
        "RU", "RW", "SA", "SB", "SC", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "ST",
        "SV", "SX", "SZ", "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TP", "TR", "TT",
        "TV", "TW", "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI", "VN", "VU", "WF",
        "WS", "YE", "YT", "ZA", "ZM", "ZW"
    ]
    if contact_info['country']['value'] not in allowed_countries:
        raise CLIError('Invalid value: country is not one of the following values: {}'.format(allowed_countries))
    return_contact_info['country'] = contact_info['country']['value']

    if not 2 <= len(contact_info['state']['value']) <= 30:
        raise CLIError('Invalid value: state must have a length between 2 and 30')
    return_contact_info['state'] = contact_info['state']['value']

    if not re.match(_city_regex, contact_info['city']['value']):
        raise CLIError('Invalid value: city')
    if len(contact_info['city']['value']) > 30:
        raise CLIError('Invalid value: city must have a length of at most 30')
    return_contact_info['city'] = contact_info['city']['value']

    if not re.match(_postal_code_regex, contact_info['postal_code']['value']):
        raise CLIError('Invalid value: postal code')
    if not 2 <= len(contact_info['postal_code']['value']) <= 10:
        raise CLIError('Invalid value: postal code must have a length between 2 and 10')
    return_contact_info['postal_code'] = contact_info['postal_code']['value']

    # Validate optional params
    if 'fax' in contact_info and 'value' in contact_info['fax'] and contact_info['fax']['value']:
        if not re.match(_phone_regex, contact_info['fax']['value']):
            raise CLIError('Invalid value: fax number must match pattern +areacode.phonenumber, '
                           'for example "+1.0000000000"')
        return_contact_info['fax'] = contact_info['fax']['value']
    else:
        return_contact_info['fax'] = ''

    if 'job_title' in contact_info and 'value' in contact_info['job_title'] and contact_info['job_title']['value']:
        if len(contact_info['job_title']['value']) > 41:
            raise CLIError('Invalid value: job title must have a length of at most 41')
        return_contact_info['job_title'] = contact_info['job_title']['value']
    else:
        return_contact_info['job_title'] = ''

    if ('name_middle' in contact_info and 'value' in contact_info['name_middle'] and contact_info['name_middle']['value']):  # pylint: disable=line-too-long
        if not re.match(_person_name_regex, contact_info['name_middle']['value']):
            raise CLIError('Invalid value: middle name')
        if len(contact_info['name_middle']['value']) > 30:
            raise CLIError('Invalid value: middle name must have a length of at most 30')
        return_contact_info['name_middle'] = contact_info['name_middle']['value']
    else:
        return_contact_info['name_middle'] = ''

    if ('organization' in contact_info and 'value' in contact_info['organization'] and contact_info['organization']['value']):  # pylint: disable=line-too-long
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

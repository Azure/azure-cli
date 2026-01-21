# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines
from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType, ignore_type

from azure.cli.core.commands.parameters import (get_location_type, get_resource_name_completion_list,
                                                tags_type, zone_type, zones_type,
                                                file_type, get_three_state_flag, get_enum_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.template_create import get_folded_parameter_help_string
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction, ALL
from azure.cli.command_modules.network._validators import (
    dns_zone_name_type,
    validate_address_pool_name_or_id, validate_metadata,
    validate_dns_record_type, validate_private_ip_address,
    get_servers_validator, get_public_ip_validator, get_nsg_validator,
    get_vnet_validator, validate_ip_tags, validate_ddos_name_or_id,
    auto_scale_config_validator,
    validate_service_endpoint_policy,
    validate_custom_error_pages,
    validate_custom_headers, validate_status_code_ranges, validate_subnet_ranges,
    WafConfigExclusionAction,
    validate_nat_gateway,
    validate_waf_policy,
    validate_user_assigned_identity,
    process_private_link_resource_id_argument, process_private_endpoint_connection_id_argument)
from azure.cli.command_modules.network._completers import (
    subnet_completion_list, get_lb_subresource_completion_list, get_ag_subresource_completion_list,
    tm_endpoint_completion_list)
from azure.cli.command_modules.network._actions import (
    TrustedClientCertificateCreate,
    SslProfilesCreate, AddMappingRequest, WAFRulesCreate)
from azure.cli.core.util import shell_safe_json_parse


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def load_arguments(self, _):
    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    nic_type = CLIArgumentType(options_list='--nic-name', metavar='NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
    nsg_name_type = CLIArgumentType(options_list='--nsg-name', metavar='NAME', help='Name of the network security group.')
    virtual_network_name_type = CLIArgumentType(options_list='--vnet-name', metavar='NAME', help='The virtual network (VNet) name.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'),
                                                local_context_attribute=LocalContextAttribute(name='vnet_name', actions=[LocalContextAction.GET]))
    subnet_name_type = CLIArgumentType(options_list='--subnet-name', metavar='NAME', help='The subnet name.',
                                       local_context_attribute=LocalContextAttribute(name='subnet_name', actions=[LocalContextAction.GET]))
    load_balancer_name_type = CLIArgumentType(options_list='--lb-name', metavar='NAME', help='The load balancer name.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), id_part='name')
    private_ip_address_type = CLIArgumentType(help='Static private IP address to use.', validator=validate_private_ip_address)
    cookie_based_affinity_type = CLIArgumentType(arg_type=get_three_state_flag(positive_label='Enabled', negative_label='Disabled', return_label=True))
    http_protocol_type = CLIArgumentType(get_enum_type(["Http", "Https", "Tcp", "Tls"]))
    ag_servers_type = CLIArgumentType(nargs='+', help='Space-separated list of IP addresses or DNS names corresponding to backend servers.', validator=get_servers_validator())
    app_gateway_name_type = CLIArgumentType(help='Name of the application gateway.', options_list='--gateway-name', completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'), id_part='name')
    zone_compatible_type = CLIArgumentType(
        options_list=['--zone', '-z'],
        nargs='+',
        help='Space-separated list of availability zones into which to provision the resource.',
    )
    edge_zone = CLIArgumentType(help='The name of edge zone.')
    auto_scale_config = CLIArgumentType(
        nargs='*',
        options_list='--auto-scale-config',
        validator=auto_scale_config_validator
    )

    # region NetworkRoot
    with self.argument_context('network') as c:
        c.argument('subnet_name', subnet_name_type)
        c.argument('virtual_network_name', virtual_network_name_type, id_part='name')
        c.argument('tags', tags_type)
        c.argument('network_security_group_name', nsg_name_type, id_part='name')
        c.argument('private_ip_address', private_ip_address_type)
        c.argument('private_ip_address_version', arg_type=get_enum_type(["IPv4", "IPv6"]))
        c.argument('enable_tcp_reset', arg_type=get_three_state_flag(), help='Receive bidirectional TCP reset on TCP flow idle timeout or unexpected connection termination. Only used when protocol is set to TCP.')
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('cache_result', arg_type=get_enum_type(['in', 'out', 'inout']), options_list='--cache', help='Cache the JSON object instead of sending off immediately.')
    # endregion

    # region ApplicationGateways
    with self.argument_context('network application-gateway') as c:
        c.argument('application_gateway_name', app_gateway_name_type, options_list=['--name', '-n'])
        skus = ["Standard_Small", "Standard_Medium", "WAF_Medium", "WAF_Large", "Standard_v2", "WAF_v2"]
        c.argument('sku', arg_group='Gateway', help='The name of the SKU.', arg_type=get_enum_type(skus), default="Standard_Medium")
        c.argument('min_capacity', help='Lower bound on the number of application gateway instances.', type=int)
        c.argument('max_capacity', help='Upper bound on the number of application gateway instances.', type=int)
        c.ignore('virtual_network_type', 'private_ip_address_allocation')
        c.argument('zones', zones_type)
        c.argument('custom_error_pages', nargs='+', help='Space-separated list of custom error pages in `STATUS_CODE=URL` format.', validator=validate_custom_error_pages)
        c.argument('firewall_policy', options_list='--waf-policy', help='Name or ID of a web application firewall (WAF) policy.', validator=validate_waf_policy)
        c.argument('priority', type=int, help='Priority of the request routing rule. Supported SKU tiers are Standard_v2, WAF_v2.')

    with self.argument_context('network application-gateway', arg_group='Identity') as c:
        c.argument('user_assigned_identity', options_list='--identity', help="Name or ID of the ManagedIdentity Resource", validator=validate_user_assigned_identity)

    with self.argument_context('network application-gateway', arg_group='Network') as c:
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('private_ip_address')
        c.argument('public_ip_address_allocation', help='The kind of IP allocation to use when creating a new public IP.', default="Dynamic")
        c.argument('subnet_address_prefix', help='The CIDR prefix to use when creating a new subnet.')
        c.argument('vnet_address_prefix', help='The CIDR prefix to use when creating a new VNet.')

    with self.argument_context('network application-gateway', arg_group='Gateway') as c:
        c.argument('servers', ag_servers_type)
        c.argument('capacity', help='The number of instances to use with the application gateway.', type=int)
        c.argument('http_settings_cookie_based_affinity', cookie_based_affinity_type, help='Enable or disable HTTP settings cookie-based affinity.')
        c.argument('http_settings_protocol', http_protocol_type, help='The HTTP settings protocol.')
        c.argument('enable_http2', arg_type=get_three_state_flag(positive_label='Enabled', negative_label='Disabled'), options_list=['--http2'], help='Use HTTP2 for the application gateway.')
        c.ignore('public_ip_address_type', 'frontend_type', 'subnet_type')
        c.argument('ssl_profile_id', help='SSL profile resource of the application gateway.', is_preview=True)
        c.argument('enable_fips', arg_type=get_three_state_flag(), help='Whether FIPS is enabled on the application gateway resource.')

    with self.argument_context('network application-gateway', arg_group='Private Link Configuration') as c:
        c.argument('enable_private_link',
                   action='store_true',
                   help='Enable Private Link feature for this application gateway. '
                        'If both public IP and private IP are enbaled, taking effect only in public frontend IP',
                   default=False)
        c.argument('private_link_ip_address', help='The static private IP address of a subnet for Private Link. If omitting, a dynamic one will be created')
        c.argument('private_link_subnet_prefix', help='The CIDR prefix to use when creating a new subnet')
        c.argument('private_link_subnet', help='The name of the subnet within the same vnet of an application gateway')
        c.argument('private_link_primary', arg_type=get_three_state_flag(), help='Whether the IP configuration is primary or not')

    with self.argument_context('network application-gateway', arg_group='Mutual Authentication Support') as c:
        c.argument('trusted_client_cert', nargs='+', action=TrustedClientCertificateCreate, is_preview=True)

    with self.argument_context('network application-gateway', arg_group='SSL Profile') as c:
        c.argument('ssl_profile', nargs='+', action=SslProfilesCreate, is_preview=True)

    with self.argument_context('network application-gateway create') as c:
        c.argument('validate', help='Generate and validate the ARM template without creating any resources.', action='store_true')
        c.argument('routing_rule_type', arg_group='Gateway', help='The request routing rule type.', arg_type=get_enum_type(["Basic", "PathBasedRouting"]))
        public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True, default_none=True)
        c.argument('public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), arg_group='Network')
        subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True)
        c.argument('subnet', help=subnet_help, completer=subnet_completion_list, arg_group='Network')

    with self.argument_context('network application-gateway create', arg_group='Gateway') as c:
        c.argument('cert_data', options_list='--cert-file', type=file_type, completer=FilesCompleter(), help='The path to the PFX certificate file.')
        c.argument('frontend_port', help='The front end port number.')
        c.argument('cert_password', help='The certificate password')
        c.argument('http_settings_port', help='The HTTP settings port.')
        c.argument('servers', ag_servers_type)
        c.argument('key_vault_secret_id', help="Secret Id of (base-64 encoded unencrypted pfx) 'Secret' or 'Certificate' object stored in Azure KeyVault. You need enable soft delete for keyvault to use this feature.")
        c.argument('ssl_cert_name', options_list='--ssl-certificate-name', help="The certificate name. Default will be `<application-gateway-name>SslCert`.")

    with self.argument_context('network application-gateway update', arg_group=None) as c:
        c.argument('sku', default=None)
        c.argument('enable_http2')
        c.argument('capacity', help='The number of instances to use with the application gateway.', type=int)

    with self.argument_context('network application-gateway create') as c:
        c.argument('connection_draining_timeout', type=int, help='The time in seconds after a backend server is removed during which on open connection remains active. Range: 0 (disabled) to 3600', arg_group='Gateway')

    with self.argument_context('network application-gateway ssl-policy') as c:
        c.argument('clear', action='store_true', help='Clear SSL policy.')
        c.argument('disabled_ssl_protocols', nargs='+', help='Space-separated list of protocols to disable.', arg_type=get_enum_type(["TLSv1_0", "TLSv1_1", "TLSv1_2", "TLSv1_3"]))

    with self.argument_context('network application-gateway url-path-map rule create') as c:
        c.argument('item_name', options_list=['--name', '-n'], help='The name of the url-path-map rule.', completer=None)

    with self.argument_context('network application-gateway waf-config') as c:
        c.argument('disabled_rule_groups', nargs='+')
        c.argument('disabled_rules', nargs='+')
        c.argument('enabled', help='Specify whether the application firewall is enabled.', arg_type=get_enum_type(['true', 'false']))
        c.argument('firewall_mode', help='Web application firewall mode.', arg_type=get_enum_type(['detection', 'prevention'], default='detection'))

    with self.argument_context('network application-gateway waf-config') as c:
        c.argument('file_upload_limit', help='File upload size limit in MB.', type=int)
        c.argument('max_request_body_size', help='Max request body size in KB.', type=int)
        c.argument('request_body_check', arg_type=get_three_state_flag(), help='Allow WAF to check the request body.')
        c.argument('exclusions', nargs='+', options_list='--exclusion', action=WafConfigExclusionAction)

    for item in ['ssl-policy', 'waf-config']:
        with self.argument_context('network application-gateway {}'.format(item)) as c:
            c.argument('application_gateway_name', app_gateway_name_type)

    with self.argument_context('network application-gateway waf-config list-rule-sets') as c:
        c.argument('_type', options_list=['--type'])

    with self.argument_context('network application-gateway ssl-policy predefined') as c:
        c.argument('predefined_policy_name', name_arg_type)

    with self.argument_context('network application-gateway ssl-policy') as c:
        c.argument('policy_name', name_arg_type, help='Name of SSL policy.')
        c.argument('policy_type', help='Type of SSL Policy.', choices=['Custom', 'Predefined', 'CustomV2'])
        c.argument('cipher_suites', nargs='*', help='SSL cipher suites to be enabled in the specified order to application gateway.')
        c.argument('min_protocol_version', help='Minimum version of SSL protocol to be supported on application gateway.')
        c.argument('disabled_ssl_protocols', nargs='+', help='Space-separated list of protocols to disable.')

    with self.argument_context('network application-gateway url-path-map') as c:
        c.argument('default_redirect_config', help='The name or ID of the default redirect configuration.')
        c.argument('redirect_config', help='The name or ID of the redirect configuration to use with the created rule.', arg_group='First Rule')

    with self.argument_context('network application-gateway rule') as c:
        c.argument('redirect_config', help='The name or ID of the redirect configuration to use with the created rule.')

    with self.argument_context('network application-gateway identity') as c:
        c.argument('application_gateway_name', app_gateway_name_type)

    with self.argument_context('network application-gateway show-backend-health') as c:
        c.argument('expand', help='Expands BackendAddressPool and BackendHttpSettings referenced in backend health.')

    with self.argument_context('network application-gateway show-backend-health', is_preview=True, arg_group="Probe Operation") as c:
        c.argument('protocol', http_protocol_type, help='The HTTP settings protocol.')
        c.argument('host', help='The name of the host to send the probe.')
        c.argument('path', help='The relative path of the probe. Valid paths start from "/"')
        c.argument('timeout', type=int, help='The probe timeout in seconds.')
        c.argument('host_name_from_http_settings', help='Use host header from HTTP settings.',
                   arg_type=get_three_state_flag())
        c.argument('match_body', help='Body that must be contained in the health response.')
        c.argument('match_status_codes', nargs='+',
                   help='Space-separated list of allowed ranges of healthy status codes for the health response.')
        c.argument('address_pool', help='The name or ID of the backend address pool.', completer=get_ag_subresource_completion_list('backend_address_pools'))
        c.argument('http_settings', help='The name or ID of the HTTP settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

    # endregion

    # region WebApplicationFirewallPolicy
    OwaspCrsExclusionEntryMatchVariable = [
        "RequestHeaderNames", "RequestCookieNames", "RequestArgNames", "RequestHeaderKeys", "RequestHeaderValues",
        "RequestCookieKeys", "RequestCookieValues", "RequestArgKeys", "RequestArgValues"
    ]
    OwaspCrsExclusionEntrySelectorMatchOperator = ["Equals", "Contains", "StartsWith", "EndsWith", "EqualsAny"]

    with self.argument_context('network application-gateway waf-policy') as c:
        c.argument('policy_name', name_arg_type, id_part='name', help='The name of the application gateway WAF policy.')
        c.argument('rule_set_type', options_list='--type',
                   arg_type=get_enum_type(['Microsoft_BotManagerRuleSet', 'Microsoft_DefaultRuleSet', 'OWASP', 'Microsoft_HTTPDDoSRuleSet']),
                   help='The type of the web application firewall rule set.')
        c.argument('rule_set_version',
                   options_list='--version',
                   help='The version of the web application firewall rule set type. '
                        '0.1, 1.0, and 1.1 are used for Microsoft_BotManagerRuleSet.')

    with self.argument_context('network application-gateway waf-policy policy-setting') as c:
        c.argument('policy_name', options_list='--policy-name', id_part=None,
                   help='The name of the web application firewall policy.')
        c.argument('request_body_check',
                   arg_type=get_three_state_flag(),
                   help='Specified to require WAF to check request Body.')
        c.argument('max_request_body_size_in_kb',
                   type=int,
                   help='Maximum request body size in Kb for WAF.')
        c.argument('file_upload_limit_in_mb',
                   type=int,
                   help='Maximum file upload size in Mb for WAF."')

    with self.argument_context('network application-gateway waf-policy custom-rule list') as c:
        c.argument('policy_name', options_list='--policy-name', id_part=None)

    with self.argument_context('network application-gateway waf-policy custom-rule match-condition list') as c:
        c.argument('policy_name', options_list='--policy-name', id_part=None)

    with self.argument_context('network application-gateway waf-policy managed-rule') as c:
        c.argument('policy_name', options_list='--policy-name', id_part=None,
                   help='The name of the web application firewall policy.')

    with self.argument_context('network application-gateway waf-policy managed-rule rule-set') as c:
        c.argument('rule_group_name',
                   options_list='--group-name',
                   help='The name of the web application firewall rule set group.')
        c.argument('rules', options_list=['--rule'], nargs='+', action=WAFRulesCreate,
                   help='List of rules that will be disabled. If provided, --group-name must be provided too')

    with self.argument_context('network application-gateway waf-policy managed-rule exclusion') as c:
        c.argument('match_variable',
                   arg_type=get_enum_type(OwaspCrsExclusionEntryMatchVariable),
                   help='The variable to be excluded.')
        c.argument('selector_match_operator',
                   arg_type=get_enum_type(OwaspCrsExclusionEntrySelectorMatchOperator),
                   options_list=['--selector-match-operator', '--match-operator'],
                   help='When matchVariable is a collection, operate on the selector to '
                        'specify which elements in the collection this exclusion applies to.')
        c.argument('selector',
                   help='When matchVariable is a collection, operator used to '
                        'specify which elements in the collection this exclusion applies to.')

    with self.argument_context('network application-gateway waf-policy managed-rule exclusion rule-set') as c:
        c.argument('rule_group_name',
                   options_list='--group-name',
                   help='The managed rule group for exclusion.')
        c.argument('rule_ids', nargs='+', help='List of rules that will be disabled. If provided, --group-name must be provided too.')
    # endregion

    # region DDoS Protection Plans
    with self.argument_context('network ddos-protection') as c:
        for dest in ['ddos_plan_name', 'ddos_protection_plan_name']:
            c.argument(dest, name_arg_type, help='Name of the DDoS protection plan.', id_part='name')
        c.argument('vnets', nargs='*', help='Space-separated list of VNets (name or IDs) to associate with the plan.', validator=get_vnet_validator('vnets'))
    # endregion

    # region DNS
    with self.argument_context('network dns') as c:
        c.argument('record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
        c.argument('relative_record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
        c.argument('zone_name', options_list=['--zone-name', '-z'], help='The name of the zone.', type=dns_zone_name_type)
        c.argument('metadata', nargs='+', help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_metadata)

    with self.argument_context('network dns zone') as c:
        c.argument('zone_name', name_arg_type)
        c.ignore('location')

    with self.argument_context('network dns zone import') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to import')

    with self.argument_context('network dns zone export') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to save')

    with self.argument_context('network dns zone update') as c:
        c.ignore('if_none_match')

    with self.argument_context('network dns zone create') as c:
        c.argument('parent_zone_name', options_list=['--parent-name', '-p'], help='Specify if parent zone exists for this zone and delegation for the child zone in the parent is to be added.')

    with self.argument_context('network dns record-set') as c:
        c.argument('target_resource', help='ID of an Azure resource from which the DNS resource value is taken.')
        for item in ['record_type', 'record_set_type']:
            c.argument(item, ignore_type, validator=validate_dns_record_type)

    for item in ['', 'a', 'aaaa', 'caa', 'cname', 'ds', 'mx', 'naptr', 'ns', 'ptr', 'srv', 'tlsa', 'txt']:
        with self.argument_context('network dns record-set {} create'.format(item)) as c:
            c.argument('ttl', type=int, help='Record set TTL (time-to-live)')
            c.argument('if_none_match', help='Create the record set only if it does not already exist.', action='store_true')

    for item in ['a', 'aaaa', 'caa', 'cname', 'ds', 'mx', 'naptr', 'ns', 'ptr', 'srv', 'tlsa', 'txt']:
        with self.argument_context('network dns record-set {} add-record'.format(item)) as c:
            c.argument('ttl', type=int, help='Record set TTL (time-to-live)')
            c.argument('record_set_name',
                       options_list=['--record-set-name', '-n'],
                       help='The name of the record set relative to the zone. '
                            'Creates a new record set if one does not exist.')
            c.argument('if_none_match', help='Create the record set only if it does not already exist.',
                       action='store_true')

        with self.argument_context('network dns record-set {} remove-record'.format(item)) as c:
            c.argument('record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone.')
            c.argument('keep_empty_record_set', action='store_true', help='Keep the empty record set if the last record is removed.')

    with self.argument_context('network dns record-set cname set-record') as c:
        c.argument('record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')
        c.argument('ttl', type=int, help='Record set TTL (time-to-live)')
        c.argument('if_none_match', help='Create the record set only if it does not already exist.',
                   action='store_true')

    with self.argument_context('network dns record-set soa') as c:
        c.argument('relative_record_set_name', ignore_type, default='@')
        c.argument('if_none_match', help='Create the record set only if it does not already exist.',
                   action='store_true')

    with self.argument_context('network dns record-set a') as c:
        c.argument('ipv4_address', options_list=['--ipv4-address', '-a'], help='IPv4 address in string notation.')

    with self.argument_context('network dns record-set aaaa') as c:
        c.argument('ipv6_address', options_list=['--ipv6-address', '-a'], help='IPv6 address in string notation.')

    with self.argument_context('network dns record-set caa') as c:
        c.argument('value', help='Value of the CAA record.')
        c.argument('flags', help='Integer flags for the record.', type=int)
        c.argument('tag', help='Record tag')

    with self.argument_context('network dns record-set cname') as c:
        c.argument('cname', options_list=['--cname', '-c'], help='Value of the cname record-set. It should be Canonical name.')

    with self.argument_context('network dns record-set ds') as c:
        c.argument('key_tag', help='The key tag value is used to determine which DNSKEY Resource Record is used for signature verification.', type=int)
        c.argument('algorithm', help='The security algorithm type represents the standard security algorithm number of the DNSKEY Resource Record. See: https://www.iana.org/assignments/dns-sec-alg-numbers/dns-sec-alg-numbers.xhtml', type=int)
        c.argument('digest_type', help='The digest algorithm type represents the standard digest algorithm number used to construct the digest. See: https://www.iana.org/assignments/ds-rr-types/ds-rr-types.xhtml', type=int)
        c.argument('digest', help='The digest value is a cryptographic hash value of the referenced DNSKEY Resource Record.')

    with self.argument_context('network dns record-set mx') as c:
        c.argument('exchange', options_list=['--exchange', '-e'], help='Exchange metric.')
        c.argument('preference', options_list=['--preference', '-p'], help='Preference metric.')

    with self.argument_context('network dns record-set naptr') as c:
        c.argument('order', help='The order in which the NAPTR records MUST be processed in order to accurately represent the ordered list of rules. The ordering is from lowest to highest. Valid values: 0-65535.', type=int)
        c.argument('preference', help='The preference specifies the order in which NAPTR records with equal "order" values should be processed, low numbers being processed before high numbers. Valid values: 0-65535.', type=int)
        c.argument('flags', help='The flags specific to DDDS applications. Values currently defined in RFC 3404 are uppercase and lowercase letters "A", "P", "S", and "U", and the empty string, "". Enclose Flags in quotation marks.')
        c.argument('services', help='The services specific to DDDS applications. Enclose Services in quotation marks.')
        c.argument('regexp', help='The regular expression that the DDDS application uses to convert an input value into an output value. For example: an IP phone system might use a regular expression to convert a phone number that is entered by a user into a SIP URI. Enclose the regular expression in quotation marks. Specify either a value for "regexp" or a value for "replacement".')
        c.argument('replacement', help='The replacement is a fully qualified domain name (FQDN) of the next domain name that you want the DDDS application to submit a DNS query for. The DDDS application replaces the input value with the value specified for replacement. Specify either a value for "regexp" or a value for "replacement". If you specify a value for "regexp", specify a dot (.) for "replacement".')

    with self.argument_context('network dns record-set ns') as c:
        c.argument('dname', options_list=['--nsdname', '-d'], help='Name server domain name.')

    with self.argument_context('network dns record-set ns add-record') as c:
        c.argument('subscription_id', options_list=['--subscriptionid', '-s'], help='Subscription id to add name server record')
        c.ignore('_subscription')

    with self.argument_context('network dns record-set ptr') as c:
        c.argument('dname', options_list=['--ptrdname', '-d'], help='PTR target domain name.')

    with self.argument_context('network dns record-set soa') as c:
        c.argument('host', options_list=['--host', '-t'], help='Host name.')
        c.argument('email', options_list=['--email', '-e'], help='Email address.')
        c.argument('expire_time', options_list=['--expire-time', '-x'], type=int, help='Expire time (seconds).')
        c.argument('minimum_ttl', options_list=['--minimum-ttl', '-m'], type=int, help='Minimum TTL (time-to-live, seconds).')
        c.argument('refresh_time', options_list=['--refresh-time', '-f'], type=int, help='Refresh value (seconds).')
        c.argument('retry_time', options_list=['--retry-time', '-r'], type=int, help='Retry time (seconds).')
        c.argument('serial_number', options_list=['--serial-number', '-s'], type=int, help='Serial number.')

    with self.argument_context('network dns record-set srv') as c:
        c.argument('priority', type=int, options_list=['--priority', '-p'], help='Priority metric.')
        c.argument('weight', type=int, options_list=['--weight', '-w'], help='Weight metric.')
        c.argument('port', type=int, options_list=['--port', '-r'], help='Service port.')
        c.argument('target', options_list=['--target', '-t'], help='Target domain name.')

    with self.argument_context('network dns record-set tlsa') as c:
        c.argument('certificate_usage', help='The usage specifies the provided association that will be used to match the certificate presented in the TLS handshake.', type=int)
        c.argument('selector', help='The selector specifies which part of the TLS certificate presented by the server will be matched against the association data.', type=int)
        c.argument('matching_type', help='The matching type specifies how the certificate association is presented.', type=int)
        c.argument('certificate_data', help='This specifies the certificate association data to be matched.')

    with self.argument_context('network dns record-set txt') as c:
        c.argument('value', options_list=['--value', '-v'], nargs='+', help='Space-separated list of text values which will be concatenated together.')

    # endregion

    # region ExpressRoutes
    er_port_name_type = CLIArgumentType(options_list='--port-name', metavar='NAME', help='ExpressRoute port name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/expressRoutePorts'))
    with self.argument_context('network express-route port generate-loa') as c:
        c.argument('express_route_port_name', er_port_name_type, options_list=['--name', '-n'])
        c.argument('customer_name', help='The customer name')
        c.argument('file_path',
                   options_list=['--file', '-f'],
                   help="Directory or the file path of the letter to be saved to. If the file name extension is not .pdf, Azure CLI will help to append. "
                        "Be careful, the existing file might get overwritten")
    # endregion

    # region PrivateLinkService
    service_name = CLIArgumentType(options_list='--service-name', id_part='name', help='Name of the private link service.', completer=get_resource_name_completion_list('Microsoft.Network/privateLinkServices'))
    with self.argument_context('network private-link-service ip-configs') as c:
        c.argument('service_name', service_name)
        c.argument('ip_config_name', help='Name of the ip configuration.', options_list=['--name', '-n'])
        c.argument('virtual_network_name', id_part=None)
    # endregion

    # region LoadBalancers
    with self.argument_context('network lb') as c:
        c.argument('load_balancer_name', load_balancer_name_type, options_list=['--name', '-n'])
        c.argument('frontend_port', help='Port number')
        c.argument('frontend_port_range_start', help='Port number')
        c.argument('frontend_port_range_end', help='Port number')
        c.argument('backend_port', help='Port number')
        c.argument('frontend_ip_name', help='The name of the frontend IP configuration.', completer=get_lb_subresource_completion_list('frontend_ip_configurations'))
        c.argument('floating_ip', help='Enable floating IP.', arg_type=get_three_state_flag())
        c.argument('idle_timeout', help='Idle timeout in minutes.', type=int)
        c.argument('protocol', help='Network transport protocol.', arg_type=get_enum_type(["Udp", "Tcp", "All"]))
        c.argument('private_ip_address_version', help='The private IP address version to use.', default="IPv4")
        for item in ['backend_pool_name', 'backend_address_pool_name']:
            c.argument(item, options_list='--backend-pool-name', help='The name of the backend address pool.', completer=get_lb_subresource_completion_list('backend_address_pools'))
        c.argument('request', help='Query inbound NAT rule port mapping request.', action=AddMappingRequest, nargs='*')

    with self.argument_context('network lb create') as c:
        c.argument('frontend_ip_zone', zones_type, options_list=['--frontend-ip-zone'], help='used to create internal facing Load balancer')
        c.argument('validate', help='Generate and validate the ARM template without creating any resources.', action='store_true')
        c.argument('sku', help='Load balancer SKU', arg_type=get_enum_type(['Basic', 'Gateway', 'Standard'], default='Standard'))
        c.argument('edge_zone', edge_zone)

    with self.argument_context('network lb create', arg_group='Public IP') as c:
        public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True)
        c.argument('public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
        c.argument('public_ip_address_allocation', help='IP allocation method.', arg_type=get_enum_type(['Static', 'Dynamic']))
        c.argument('public_ip_dns_name', help='Globally unique DNS name for a new public IP.')
        c.argument('public_ip_zone', zone_type, options_list=['--public-ip-zone'], help='used to created a new public ip for the load balancer, a.k.a public facing Load balancer')
        c.ignore('public_ip_address_type')

    with self.argument_context('network lb create', arg_group='Subnet') as c:
        subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True, allow_none=True, default_none=True)
        c.argument('subnet', help=subnet_help, completer=subnet_completion_list)
        c.argument('subnet_address_prefix', help='The CIDR address prefix to use when creating a new subnet.')
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('vnet_address_prefix', help='The CIDR address prefix to use when creating a new VNet.')
        c.ignore('vnet_type', 'subnet_type')
    # endregion

    # region cross-region load balancer
    with self.argument_context('network cross-region-lb') as c:
        c.argument('load_balancer_name', load_balancer_name_type, options_list=['--name', '-n'])
        c.argument('frontend_port', help='Port number')
        c.argument('frontend_port_range_start', help='Port number')
        c.argument('frontend_port_range_end', help='Port number')
        c.argument('backend_port', help='Port number')
        c.argument('frontend_ip_name', help='The name of the frontend IP configuration.',
                   completer=get_lb_subresource_completion_list('frontend_ip_configurations'))
        c.argument('floating_ip', help='Enable floating IP.', arg_type=get_three_state_flag())
        c.argument('idle_timeout', help='Idle timeout in minutes.', type=int)
        c.argument('protocol', help='Network transport protocol.', arg_type=get_enum_type(["Udp", "Tcp", "All"]))
        for item in ['backend_pool_name', 'backend_address_pool_name']:
            c.argument(item, options_list='--backend-pool-name', help='The name of the backend address pool.',
                       completer=get_lb_subresource_completion_list('backend_address_pools'))

    with self.argument_context('network cross-region-lb create') as c:
        c.argument('frontend_ip_zone', zone_type, options_list=['--frontend-ip-zone'],
                   help='used to create internal facing Load balancer')
        c.argument('validate', help='Generate and validate the ARM template without creating any resources.',
                   action='store_true')

    with self.argument_context('network cross-region-lb create', arg_group='Public IP') as c:
        public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True)
        c.argument('public_ip_address', help=public_ip_help,
                   completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
        c.argument('public_ip_address_allocation', options_list=['--public-ip-address-allocation', '--address-allocation'], help='IP allocation method.',
                   arg_type=get_enum_type(["Static", "Dynamic"]))
        c.argument('public_ip_dns_name', help='Globally unique DNS name for a new public IP.')
        c.argument('public_ip_zone', zone_type, options_list=['--public-ip-zone'],
                   help='used to created a new public ip for the load balancer, a.k.a public facing Load balancer')
        c.ignore('public_ip_address_type')
    # endregion

    # region NetworkInterfaces (NIC)
    with self.argument_context('network nic ip-config address-pool') as c:
        c.argument('load_balancer_name', options_list='--lb-name', help='The name of the load balancer containing the address pool (Omit if supplying an address pool ID).', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))
        c.argument('application_gateway_name', app_gateway_name_type, help='The name of an application gateway containing the address pool (Omit if supplying an address pool ID).', id_part=None)
        c.argument('backend_address_pool', options_list='--address-pool', help='The name or ID of an existing backend address pool.', validator=validate_address_pool_name_or_id)
        c.argument('ip_config_name', options_list=['--ip-config-name', '-n'], metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part=None)
        c.argument('network_interface_name', nic_type, id_part=None)
    # endregion

    # region NetworkSecurityGroups
    with self.argument_context('network nsg') as c:
        c.argument('network_security_group_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'), id_part='name')

    with self.argument_context('network nsg create') as c:
        c.argument('name', name_arg_type)

    with self.argument_context('network nsg rule') as c:
        c.argument('security_rule_name', name_arg_type, id_part='child_name_1', help='Name of the network security group rule')
        c.argument('network_security_group_name', options_list='--nsg-name', metavar='NSGNAME', help='Name of the network security group', id_part='name')
        c.argument('include_default', help='Include default security rules in the output.')

    with self.argument_context('network nsg rule create') as c:
        c.argument('network_security_group_name', options_list='--nsg-name', metavar='NSGNAME', help='Name of the network security group', id_part=None)
    # endregion

    # region NetworkWatchers
    with self.argument_context('network watcher') as c:
        c.argument('network_watcher_name', name_arg_type, help='Name of the Network Watcher.')
        c.argument('location', validator=None)
        c.ignore('watcher_rg')
        c.ignore('watcher_name')

    with self.argument_context('network watcher connection-monitor') as c:
        c.argument('network_watcher_name', arg_type=ignore_type, options_list=['--__NETWORK_WATCHER_NAME'])
        c.argument('connection_monitor_name', name_arg_type, help='Connection monitor name.')

    # connection monitor V2 parameter set
    with self.argument_context('network watcher connection-monitor', arg_group='V2') as c:
        c.argument('notes', help='Optional notes to be associated with the connection monitor')

    with self.argument_context('network watcher connection-monitor test-group') as c:
        c.argument('connection_monitor_name',
                   options_list=['--connection-monitor'],
                   help='Connection monitor name.')
        c.argument('name',
                   arg_type=name_arg_type,
                   help='The name of the connection monitor test group')

    with self.argument_context('network watcher connection-monitor output') as c:
        c.argument('connection_monitor_name',
                   options_list=['--connection-monitor'],
                   help='Connection monitor name.')

    with self.argument_context('network watcher configure') as c:
        c.argument('locations', get_location_type(self.cli_ctx), options_list=['--locations', '-l'], nargs='+')
        c.argument('enabled', arg_type=get_three_state_flag())

    with self.argument_context('network watcher create') as c:
        c.argument('location', validator=get_default_location_from_resource_group)

    with self.argument_context('network watcher flow-log') as c:
        c.argument('location', get_location_type(self.cli_ctx),
                   help='Location to identify the exclusive Network Watcher under a region. '
                        'Only one Network Watcher can be existed per subscription and region.')
        c.argument('flow_log_name', name_arg_type, help='The name of the flow logger')
        c.argument('nsg', help='Name or ID of the network security group.')
        c.argument('enabled', arg_type=get_three_state_flag(), help='Enable logging', default='true')
        c.argument('retention', type=int, help='Number of days to retain logs')
        c.argument('storage_account', help='Name or ID of the storage account in which to save the flow logs. '
                                           'Must be in the same region of flow log.')

    # temporary solution for compatible with old show command's parameter
    # after old show command's parameter is deprecated and removed,
    # this argument group "network watcher flow-log show" should be removed
    with self.argument_context('network watcher flow-log show') as c:
        c.argument('nsg',
                   deprecate_info=c.deprecate(redirect='--location and --name combination', hide=False),
                   help='Name or ID of the network security group.')

    with self.argument_context('network watcher flow-log', arg_group='Traffic Analytics') as c:
        c.argument('traffic_analytics_interval', type=int, options_list='--interval', help='Interval in minutes at which to conduct flow analytics. Temporarily allowed values are 10 and 60.')
        c.argument('traffic_analytics_workspace',
                   options_list='--workspace',
                   help='Name or ID of a Log Analytics workspace. Must be in the same region of flow log')
        c.argument('traffic_analytics_enabled', options_list='--traffic-analytics', arg_type=get_three_state_flag(), help='Enable traffic analytics. Defaults to true if `--workspace` is provided.')

    with self.argument_context('network watcher troubleshooting') as c:
        c.argument('resource', help='Name or ID of the resource to troubleshoot.')
        c.argument('resource_type', help='The resource type', options_list=['--resource-type', '-t'], id_part='resource_type', arg_type=get_enum_type(['vnetGateway', 'vpnConnection']))
    # endregion

    # region PublicIPAddresses
    with self.argument_context('network public-ip') as c:
        c.argument('public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), id_part='name', help='The name of the public IP address.')
        c.argument('name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), help='The name of the public IP address.')
        c.argument('reverse_fqdn', help='Reverse FQDN (fully qualified domain name).')
        c.argument('dns_name', help='Globally unique DNS entry.')
        c.argument('dns_name_scope', help='The domain name label scope. If a domain name label and a domain name label scope are specified, an A DNS record is created for the public IP in the Microsoft Azure DNS system with a hashed value includes in FQDN.', arg_type=get_enum_type(["NoReuse", "ResourceGroupReuse", "SubscriptionReuse", "TenantReuse"]))
        c.argument('idle_timeout', type=int, help='Idle timeout in minutes.')
        c.argument('zone', zone_type)
        c.argument('zone', zone_compatible_type)
        c.argument('ip_tags', nargs='+', help="Space-separated list of IP tags in 'TYPE=VAL' format.", validator=validate_ip_tags)
        c.argument('ip_address', help='The IP address associated with the public IP address resource.')

    with self.argument_context('network public-ip create') as c:
        c.argument('name', completer=None)
        c.argument('sku', help='Name of a public IP address SKU', arg_type=get_enum_type(["Basic", "Standard", "StandardV2"]), default="Standard")
        c.argument('tier', help='Tier of a public IP address SKU and Global tier is only supported for standard SKU public IP addresses', arg_type=get_enum_type(["Regional", "Global"]))
        c.ignore('dns_name_type')
        c.argument('edge_zone', edge_zone)

    with self.argument_context('network public-ip create') as c:
        c.argument('allocation_method', help='IP address allocation method', arg_type=get_enum_type(['Static', 'Dynamic']))
        c.argument('version', help='IP address type.', arg_type=get_enum_type(["IPv4", "IPv6"]))
        c.argument('protection_mode', options_list=['--ddos-protection-mode', '--protection-mode'],
                   help='The DDoS protection mode of the public IP', arg_type=get_enum_type(['Enabled', 'Disabled', 'VirtualNetworkInherited']))
        c.argument('ddos_protection_plan', help='Name or ID of a DDoS protection plan associated with the public IP. Can only be set if `--protection-mode` is Enabled.')

    for scope in ['public-ip', 'lb frontend-ip', 'cross-region-lb frontend-ip']:
        with self.argument_context('network {}'.format(scope)) as c:
            c.argument('public_ip_prefix', help='Name or ID of a public IP prefix.')
    # endregion

    # region TrafficManagers
    with self.argument_context('network traffic-manager profile') as c:
        c.argument('traffic_manager_profile_name', name_arg_type, id_part='name', help='Traffic manager profile name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
        c.argument('profile_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
        c.argument('profile_status', options_list=['--status'], help='Status of the Traffic Manager profile.', arg_type=get_enum_type(['Enabled', 'Disabled']))
        c.argument('routing_method', help='Routing method.', arg_type=get_enum_type(['Performance', 'Weighted', 'Priority', 'Geographic', 'Multivalue', 'Subnet']))
        c.argument('unique_dns_name', help="Relative DNS name for the traffic manager profile. Resulting FQDN will be `<unique-dns-name>.trafficmanager.net` and must be globally unique.")
        c.argument('max_return', help="Maximum number of endpoints to be returned for MultiValue routing type.", type=int)
        c.argument('ttl', help='DNS config time-to-live in seconds.', type=int)

    with self.argument_context('network traffic-manager profile', arg_group='Monitor Configuration') as c:
        c.argument('monitor_path', help='Path to monitor. Use ""(\'""\' in PowerShell) for none.', options_list=['--path', c.deprecate(target='--monitor-path', redirect='--path', hide=True)])
        c.argument('monitor_port', help='Port to monitor.', type=int, options_list=['--port', c.deprecate(target='--monitor-port', redirect='--port', hide=True)])
        c.argument('monitor_protocol', help='Monitor protocol.', arg_type=get_enum_type(['HTTP', 'HTTPS', 'TCP']), options_list=['--protocol', c.deprecate(target='--monitor-protocol', redirect='--protocol', hide=True)])
        c.argument('timeout', help='The time in seconds allowed for endpoints to respond to a health check.', type=int)
        c.argument('interval', help='The interval in seconds at which health checks are conducted.', type=int)
        c.argument('max_failures', help='The number of consecutive failed health checks tolerated before an endpoint is considered degraded.', type=int)
        c.argument('monitor_custom_headers', options_list='--custom-headers', help='Space-separated list of NAME=VALUE pairs.', nargs='+', validator=validate_custom_headers)
        c.argument('status_code_ranges', help='Space-separated list of status codes in MIN-MAX or VAL format.', nargs='+', validator=validate_status_code_ranges)

    with self.argument_context('network traffic-manager endpoint') as c:
        c.argument('endpoint_name', name_arg_type, id_part='child_name_1', help='Endpoint name.', completer=tm_endpoint_completion_list)
        c.argument('endpoint_type', options_list=['--type', '-t'], help='Endpoint type.', id_part='child_name_1', arg_type=get_enum_type(['azureEndpoints', 'externalEndpoints', 'nestedEndpoints']))
        c.argument('profile_name', help='Name of parent profile.', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'), id_part='name')
        c.argument('endpoint_location', help="Location of the external or nested endpoints when using the 'Performance' routing method.")
        c.argument('endpoint_monitor_status', help='The monitoring status of the endpoint.')
        c.argument('endpoint_status', arg_type=get_enum_type(['Enabled', 'Disabled']), help="The status of the endpoint. If enabled the endpoint is probed for endpoint health and included in the traffic routing method.")
        c.argument('min_child_endpoints', type=int, help="The minimum number of endpoints that must be available in the child profile for the parent profile to be considered available. Only applicable to an endpoint of type 'NestedEndpoints'.")
        c.argument('min_child_ipv4', type=int, help="The minimum number of IPv4 (DNS record type A) endpoints that must be available in the child profile in order for the parent profile to be considered available. Only applicable to endpoint of type 'NestedEndpoints'.")
        c.argument('min_child_ipv6', type=int, help="The minimum number of IPv6 (DNS record type AAAA) endpoints that must be available in the child profile in order for the parent profile to be considered available. Only applicable to endpoint of type 'NestedEndpoints'.")
        c.argument('priority', help="Priority of the endpoint when using the 'Priority' traffic routing method. Values range from 1 to 1000, with lower values representing higher priority.", type=int)
        c.argument('target', help='Fully-qualified DNS name of the endpoint.')
        c.argument('target_resource_id', help="The Azure Resource URI of the endpoint. Not applicable for endpoints of type 'ExternalEndpoints'.")
        c.argument('weight', help="Weight of the endpoint when using the 'Weighted' traffic routing method. Values range from 1 to 1000.", type=int)
        c.argument('geo_mapping', help="Space-separated list of country/region codes mapped to this endpoint when using the 'Geographic' routing method.", nargs='+')
        c.argument('subnets', nargs='+', help='Space-separated list of subnet CIDR prefixes (10.0.0.0/24) or subnet ranges (10.0.0.0-11.0.0.0).', validator=validate_subnet_ranges)
        c.argument('monitor_custom_headers', nargs='+', options_list='--custom-headers', help='Space-separated list of custom headers in KEY=VALUE format.', validator=validate_custom_headers)
        c.argument('always_serve', arg_type=get_enum_type(['Enabled', 'Disabled']), help='If Always Serve is enabled, probing for endpoint health will be disabled and endpoints will be included in the traffic routing method.')
    # endregion

    # region VirtualNetworks
    encryption_policy_types = ['dropUnencrypted', 'allowUnencrypted']
    with self.argument_context('network vnet') as c:
        c.argument('virtual_network_name', virtual_network_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('vnet_prefixes', nargs='+', help='Space-separated list of IP address prefixes for the VNet.', options_list='--address-prefixes', metavar='PREFIX')
        c.argument('dns_servers', nargs='+', help='Space-separated list of DNS server IP addresses.', metavar='IP')
        c.argument('ddos_protection', arg_type=get_three_state_flag(), help='Control whether DDoS protection is enabled.')
        c.argument('ddos_protection_plan', help='Name or ID of a DDoS protection plan to associate with the VNet.', validator=validate_ddos_name_or_id)
        c.argument('vm_protection', arg_type=get_three_state_flag(), help='Enable VM protection for all subnets in the VNet.')
        c.argument('flowtimeout', type=int, help='The FlowTimeout value (in minutes) for the Virtual Network', is_preview=True)
        c.argument('bgp_community', help='The BGP community associated with the virtual network.')
        c.argument('enable_encryption', arg_type=get_three_state_flag(), help='Enable encryption on the virtual network.', is_preview=True)
        c.argument('encryption_enforcement_policy', options_list=['--encryption-enforcement-policy', '--encryption-policy'], arg_type=get_enum_type(encryption_policy_types), help='To control if the Virtual Machine without encryption is allowed in encrypted Virtual Network or not.', is_preview=True)

    with self.argument_context('network vnet check-ip-address') as c:
        c.argument('ip_address', required=True)

    with self.argument_context('network vnet create') as c:
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('vnet_name', virtual_network_name_type, options_list=['--name', '-n'], completer=None,
                   local_context_attribute=LocalContextAttribute(name='vnet_name', actions=[LocalContextAction.SET], scopes=[ALL]))
        c.argument('edge_zone', edge_zone)

    with self.argument_context('network vnet create', arg_group='Subnet') as c:
        c.argument('subnet_name', help='Name of a new subnet to create within the VNet.',
                   local_context_attribute=LocalContextAttribute(name='subnet_name', actions=[LocalContextAction.SET], scopes=[ALL]))
        c.argument('subnet_prefix', help='IP address prefix for the new subnet. If omitted, automatically reserves a /24 (or as large as available) block within the VNet address space.', metavar='PREFIX')
        c.argument('subnet_prefix', options_list='--subnet-prefixes', nargs='+', help='Space-separated list of address prefixes in CIDR format for the new subnet. If omitted, automatically reserves a /24 (or as large as available) block within the VNet address space.', metavar='PREFIXES')
        c.argument('network_security_group', options_list=['--network-security-group', '--nsg'], validator=get_nsg_validator(), help='Name or ID of a network security group (NSG).')

    with self.argument_context('network vnet update') as c:
        c.argument('address_prefixes', nargs='+')

    with self.argument_context('network vnet delete') as c:
        c.argument('virtual_network_name', local_context_attribute=None)

    with self.argument_context('network vnet peering') as c:
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('virtual_network_peering_name', options_list=['--name', '-n'], help='The name of the VNet peering.', id_part='child_name_1')
        c.argument('remote_virtual_network', options_list=['--remote-vnet'], help='Resource ID or name of the remote VNet.')

    with self.argument_context('network vnet peering create') as c:
        c.argument('allow_virtual_network_access', options_list='--allow-vnet-access', action='store_true', help='Allows access from the local VNet to the remote VNet.')
        c.argument('allow_gateway_transit', action='store_true', help='Allows gateway link to be used in the remote VNet.')
        c.argument('allow_forwarded_traffic', action='store_true', help='Allows forwarded traffic from the local VNet to the remote VNet.')
        c.argument('use_remote_gateways', action='store_true', help='Allows VNet to use the remote VNet\'s gateway. Remote VNet gateway must have --allow-gateway-transit enabled for remote peering. Only 1 peering can have this flag enabled. Cannot be set if the VNet already has a gateway.')

    with self.argument_context('network vnet subnet') as c:
        c.argument('subnet_name', arg_type=subnet_name_type, options_list=['--name', '-n'], id_part='child_name_1')
        c.argument('nat_gateway', validator=validate_nat_gateway, help='Name or ID of a NAT gateway to attach.')
        c.argument('address_prefix', metavar='PREFIX', help='Address prefix in CIDR format.')
        c.argument('address_prefix', metavar='PREFIXES', options_list='--address-prefixes', nargs='+', help='Space-separated list of address prefixes in CIDR format.')
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('network_security_group', options_list=['--network-security-group', '--nsg'], validator=get_nsg_validator(), help='Name or ID of a network security group (NSG).')
        c.argument('route_table', help='Name or ID of a route table to associate with the subnet.')
        c.argument('service_endpoints', nargs='+')
        c.argument('service_endpoint_policy', nargs='+', help='Space-separated list of names or IDs of service endpoint policies to apply.', validator=validate_service_endpoint_policy)
        c.argument('disable_private_endpoint_network_policies', arg_type=get_three_state_flag(), help='Disable private endpoint network policies on the subnet, the policy is disabled by default.')
        c.argument('disable_private_link_service_network_policies', arg_type=get_three_state_flag(), help='Disable private link service network policies on the subnet.')

    with self.argument_context('network vnet subnet create') as c:
        c.argument('subnet_name', arg_type=subnet_name_type, options_list=['--name', '-n'], id_part='child_name_1',
                   local_context_attribute=LocalContextAttribute(name='subnet_name', actions=[LocalContextAction.SET], scopes=[ALL]))

    with self.argument_context('network vnet subnet update') as c:
        c.argument('network_security_group', validator=get_nsg_validator(), help='Name or ID of a network security group (NSG). Use empty string ""(\'""\' in PowerShell) to detach it.')
        c.argument('route_table', help='Name or ID of a route table to associate with the subnet. Use empty string ""(\'""\' in PowerShell) to detach it. You can also append "--remove routeTable" in "az network vnet subnet update" to detach it.')

    for scope in ['network vnet subnet list', 'network vnet peering list']:
        with self.argument_context(scope) as c:
            c.argument('virtual_network_name', id_part=None)

    with self.argument_context('network vnet subnet delete') as c:
        c.argument('subnet_name', local_context_attribute=None)

    # endregion

    # region VirtualNetworkGateways
    with self.argument_context('network vnet-gateway') as c:
        c.argument('virtual_network_gateway_name', options_list=['--name', '-n'], help='Name of the VNet gateway.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'), id_part='name')
        c.argument('gateway_name', help='Virtual network gateway name')

    with self.argument_context('network vnet-gateway vpn-client') as c:
        c.argument('processor_architecture', help='Processor architecture of the target system.', arg_type=get_enum_type(['Amd64', 'X86']))
        c.argument('authentication_method', help='Method used to authenticate with the generated client.', arg_type=get_enum_type(['EAPMSCHAPv2', 'EAPTLS']))
        c.argument('radius_server_auth_certificate', help='Public certificate data for the Radius server auth certificate in Base-64 format. Required only if external Radius auth has been configured with EAPTLS auth.')
        c.argument('client_root_certificates', nargs='+', help='Space-separated list of client root certificate public certificate data in Base-64 format. Optional for external Radius-based auth with EAPTLS')
        c.argument('use_legacy', help='Generate VPN client package using legacy implementation.', arg_type=get_three_state_flag())
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.argument_context('network vpn-connection') as c:
        c.argument('virtual_network_gateway_connection_name', options_list=['--name', '-n'], metavar='NAME', id_part='name', help='Connection name.')
        c.argument('shared_key', help='Shared IPSec key.')
        c.argument('connection_name', help='Connection name.')
        c.argument('routing_weight', type=int, help='Connection routing weight')
        c.argument('use_policy_based_traffic_selectors', help='Enable policy-based traffic selectors.', arg_type=get_three_state_flag())
        c.argument('express_route_gateway_bypass', arg_type=get_three_state_flag(), help='Bypass ExpressRoute gateway for data forwarding.')
        c.argument('ingress_nat_rule', nargs='+', help='List of ingress NatRules.', is_preview=True)
        c.argument('egress_nat_rule', nargs='+', help='List of egress NatRules.', is_preview=True)

    with self.argument_context('network vpn-connection list') as c:
        c.argument('virtual_network_gateway_name', options_list=['--vnet-gateway'], help='Name of the VNet gateway.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'))

    with self.argument_context('network vpn-connection create') as c:
        c.argument('connection_name', options_list=['--name', '-n'], metavar='NAME', help='Connection name.')
        c.ignore('connection_type')
        for item in ['vnet_gateway2', 'local_gateway2', 'express_route_circuit2']:
            c.argument(item, arg_group='Destination')

        c.argument('auth_type', options_list=['--authentication-type', '--auth-type'], help='Authentication type for the VPN connection.', arg_type=get_enum_type(['Certificate', 'PSK']))
        c.argument('cert_auth', options_list=['--certificate-authentication', '--cert-auth'],
                   help='Certificate-based authentication configuration. Provide as JSON string or file path with @ prefix, Expected keys (outboundAuthCertificate, inboundAuthCertificateChain, inboundAuthCertificateSubjectName).',
                   type=shell_safe_json_parse)

    with self.argument_context('network routeserver') as c:
        c.argument('virtual_hub_name', options_list=['--name', '-n'], id_part='name',
                   help='Name of the route server.')
        c.argument('hosted_subnet', help='ID of a subnet where route server would be deployed')
        c.argument('allow_branch_to_branch_traffic', options_list=['--allow-b2b-traffic'],
                   arg_type=get_three_state_flag(), help='Whether to allow branch to branch traffic.')
        c.argument('public_ip_address', validator=get_public_ip_validator(),
                   help='Name or ID of the public IP address.',
                   completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
        c.argument("hub_routing_preference", help="Routing preference of the route server.", arg_type=get_enum_type(["ASPath", "ExpressRoute", "VpnGateway"]))

    with self.argument_context('network routeserver create') as c:
        c.argument('virtual_hub_name', id_part=None)
        c.argument('auto_scale_config', auto_scale_config)
    # endregion

    # region Remove --ids from listsaz
    for scope in ['express-route auth', 'express-route peering']:
        with self.argument_context('network {} list'.format(scope)) as c:
            c.argument('circuit_name', id_part=None)

    with self.argument_context('network nsg rule list') as c:
        c.argument('network_security_group_name', id_part=None)

    with self.argument_context('network route-filter rule list') as c:
        c.argument('route_filter_name', id_part=None)

    with self.argument_context('network route-table route list') as c:
        c.argument('route_table_name', id_part=None)

    with self.argument_context('network traffic-manager endpoint list') as c:
        c.argument('profile_name', id_part=None)
    # endregion

    # region PrivateLinkResource and PrivateEndpointConnection
    from azure.cli.command_modules.network.private_link_resource_and_endpoint_connections.custom import TYPE_CLIENT_MAPPING, register_providers
    register_providers()
    for scope in ['private-link-resource', 'private-endpoint-connection']:
        with self.argument_context('network {} list'.format(scope)) as c:
            c.argument('name', required=False, help='Name of the resource. If provided, --type and --resource-group must be provided too', options_list=['--name', '-n'])
            c.argument('resource_provider', required=False, help='Type of the resource. If provided, --name and --resource-group must be provided too', options_list='--type', arg_type=get_enum_type(TYPE_CLIENT_MAPPING.keys()))
            c.argument('resource_group_name', required=False, help='Name of resource group. If provided, --name and --type must be provided too')
            c.extra('id', help='ID of the resource', validator=process_private_link_resource_id_argument)
    for scope in ['show', 'approve', 'reject', 'delete']:
        with self.argument_context('network private-endpoint-connection {}'.format(scope)) as c:
            c.extra('connection_id', options_list=['--id'], help='ID of the private endpoint connection', validator=process_private_endpoint_connection_id_argument)
            c.argument('approval_description', options_list=['--description', '-d'], help='Comments for the approval.')
            c.argument('rejection_description', options_list=['--description', '-d'],
                       help='Comments for the rejection.')
            c.argument('name', required=False, help='Name of the private endpoint connection',
                       options_list=['--name', '-n'])
            c.argument('resource_provider', required=False, help='Type of the resource.', options_list='--type',
                       arg_type=get_enum_type(TYPE_CLIENT_MAPPING.keys()))
            c.argument('resource_group_name', required=False)
            c.argument('resource_name', required=False, help='Name of the resource')
    # endregion

    # region DdosCustomPolicy
    with self.argument_context('network ddos-custom-policy create') as c:
        c.argument('ddos_custom_policy_name', options_list=['--ddos-custom-policy-name', '--name', '-n'], help='The name of the DDoS custom policy.')
        c.argument('location', arg_group='Parameters', help='Resource location.')
        c.argument('tags', arg_group='Parameters', help='Resource tags.')
        c.argument('detection_rule_name', arg_group='Detection Rules', help='The name of the DDoS detection rule.')
        c.argument('detection_mode', arg_group='Detection Rules', help='The detection mode for the DDoS detection rule.')
        c.argument('traffic_type', arg_group='Detection Rules', help='The traffic type (one of Tcp, Udp, TcpSyn) that the detection rule will be applied upon.')
        c.argument('packets_per_second', arg_group='Detection Rules', help='The customized packets per second threshold.')
    # endregion

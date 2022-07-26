# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from knack.arguments import CLIArgumentType
from knack.log import get_logger

from azure.cli.core.commands.parameters import (
    tags_type,
    get_enum_type,
    get_three_state_flag,
    resource_group_name_type,
    get_resource_name_completion_list,
    get_location_type)
from azure.cli.core.util import (shell_safe_json_parse, CLIError)

from azure.cli.core.commands.validators import validate_tag
from azure.cli.core.decorators import Completer

from azure.cli.command_modules.cognitiveservices._client_factory import cf_resource_skus

from azure.mgmt.cognitiveservices.models import KeyName, DeploymentScaleType, HostingModel

logger = get_logger(__name__)
name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')


def extract_key_values_pairs(api_properties):
    api_properties_dict = {}
    for item in api_properties:
        api_properties_dict.update(validate_tag(item))
    return api_properties_dict


def validate_api_properties(ns):
    """ Extracts JSON format or 'a=b c=d' format as api properties """
    api_properties = ns.api_properties

    if api_properties is None:
        return

    if len(api_properties) > 1:
        ns.api_properties = extract_key_values_pairs(api_properties)
    else:
        string = api_properties[0]
        try:
            ns.api_properties = shell_safe_json_parse(string)
            return
        except CLIError:
            result = extract_key_values_pairs([string])
            if _is_suspected_json(string):
                logger.warning('Api properties looks like a JSON format but not valid, interpreted as key=value pairs:'
                               ' %s', str(result))
            ns.api_properties = result
            return


def _is_suspected_json(string):
    """ If the string looks like a JSON """
    if string.startswith('{') or string.startswith('\'{') or string.startswith('\"{'):
        return True
    if string.startswith('[') or string.startswith('\'[') or string.startswith('\"['):
        return True
    if re.match(r"^['\"\s]*{.+}|\[.+\]['\"\s]*$", string):
        return True

    return False


api_properties_type = CLIArgumentType(
    validator=validate_api_properties,
    help="Api properties in JSON format or a=b c=d format. Some cognitive services (i.e. QnA Maker) "
         "require extra api properties to create the account.",
    nargs='*'
)


def _sku_filter(cmd, namespace):
    """
    Get a list of ResourceSku and filter by existing conditions: 'kind', 'location' and 'sku_name'
    """
    kind = getattr(namespace, 'kind', None)
    location = getattr(namespace, 'location', None)
    sku_name = getattr(namespace, 'sku_name', None)

    def _filter_sku(_sku):
        if sku_name is not None:
            if _sku.name != sku_name:
                return False
        if kind is not None:
            if _sku.kind != kind:
                return False
        if location is not None:
            if location.lower() not in [x.lower() for x in _sku.locations]:
                return False
        return True

    return [x for x in cf_resource_skus(cmd.cli_ctx).list() if _filter_sku(x)]


def _validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    subnet = namespace.subnet
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        return
    if subnet and not subnet_is_id and vnet:
        namespace.subnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)


@Completer
def sku_name_completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    names = {x.name for x in _sku_filter(cmd, namespace)}
    return sorted(list(names))


@Completer
def kind_completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    kinds = {x.kind for x in _sku_filter(cmd, namespace)}
    return sorted(list(kinds))


@Completer
def location_completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    names = {location for x in _sku_filter(cmd, namespace) for location in x.locations}
    return [x.lower() for x in sorted(list(names))]


def load_arguments(self, _):
    with self.argument_context('cognitiveservices') as c:
        c.argument('account_name', arg_type=name_arg_type, help='cognitive service account name',
                   completer=get_resource_name_completion_list('Microsoft.CognitiveServices/accounts'))
        c.argument('location', arg_type=get_location_type(self.cli_ctx),
                   completer=location_completer)
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('sku_name', options_list=['--sku'], help='Name of the Sku of cognitive services account',
                   completer=sku_name_completer)
        c.argument('kind', help='the API name of cognitive services account',
                   completer=kind_completer)
        c.argument('tags', tags_type)
        c.argument('key_name', required=True, help='Key name to generate', arg_type=get_enum_type(KeyName))
        c.argument('api_properties', api_properties_type)
        c.argument('custom_domain', help='User domain assigned to the account. Name is the CNAME source.')
        c.argument('storage', help='The storage accounts for this resource, in JSON array format.')
        c.argument('encryption', help='The encryption properties for this resource, in JSON format.')

    with self.argument_context('cognitiveservices account create') as c:
        c.argument('assign_identity', help='Generate and assign an Azure Active Directory Identity for this account.')
        c.argument('yes', action='store_true', help='Do not prompt for terms confirmation')

    with self.argument_context('cognitiveservices account network-rule') as c:
        c.argument('ip_address', help='IPv4 address or CIDR range.')
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.', validator=_validate_subnet)

    with self.argument_context('cognitiveservices account deployment') as c:
        c.argument('deployment_name', help='Cognitive Services account deployment name')

    with self.argument_context('cognitiveservices account deployment', arg_group='DeploymentModel') as c:
        c.argument('model_name', help='Cognitive Services account deployment model name.')
        c.argument('model_format', help='Cognitive Services account deployment model format.')
        c.argument('model_version', help='Cognitive Services account deployment model version.')

    with self.argument_context('cognitiveservices account deployment', arg_group='DeploymentScaleSettings') as c:
        c.argument(
            'scale_settings_scale_type', get_enum_type(DeploymentScaleType),
            options_list=['--scale-type', '--scale-settings-scale-type'],
            help='Cognitive Services account deployment scale settings scale type.')
        c.argument(
            'scale_settings_capacity', options_list=['--scale-capacity', '--scale-settings-capacity'],
            help='Cognitive Services account deployment scale settings capacity.')

    with self.argument_context('cognitiveservices account commitment-plan') as c:
        c.argument('commitment_plan_name', help='Cognitive Services account commitment plan name')
        c.argument('plan_type', help='Cognitive Services account commitment plan type')
        c.argument('hosting_model', get_enum_type(HostingModel), help='Cognitive Services account hosting model')
        c.argument(
            'auto_renew', arg_type=get_three_state_flag(),
            help='A boolean indicating whether to apply auto renew.')

    with self.argument_context('cognitiveservices account commitment-plan', arg_group='Current CommitmentPeriod') as c:
        c.argument('current_count', help='Cognitive Services account commitment plan current commitment period count.')
        c.argument('current_tier', help='Cognitive Services account commitment plan current commitment period tier.')

    with self.argument_context('cognitiveservices account commitment-plan', arg_group='Next CommitmentPeriod') as c:
        c.argument('next_count', help='Cognitive Services account commitment plan next commitment period count.')
        c.argument('next_tier', help='Cognitive Services account commitment plan next commitment period tier.')

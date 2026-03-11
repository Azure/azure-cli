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
    get_location_type,
)
from azure.cli.core.util import shell_safe_json_parse, CLIError

from azure.cli.core.commands.validators import validate_tag
from azure.cli.core.decorators import Completer

from azure.cli.command_modules.cognitiveservices._client_factory import cf_resource_skus

from azure.mgmt.cognitiveservices.models import (
    KeyName,
    DeploymentScaleType,
    HostingModel,
)

logger = get_logger(__name__)
name_arg_type = CLIArgumentType(options_list=["--name", "-n"], metavar="NAME")


def _environment_variables_type(value: str) -> dict:
    """
    Parse environment variable in key=value format.

    Args:
        value: String in format 'KEY=value'

    Returns:
        dict: Dictionary with 'key' and 'value' keys

    Raises:
        ValueError: If format is invalid

    Examples:
        >>> _environment_variables_type('FOO=bar')
        {'key': 'FOO', 'value': 'bar'}
        >>> _environment_variables_type('CONNECTION_STRING=Server=localhost;Database=mydb')
        {'key': 'CONNECTION_STRING', 'value': 'Server=localhost;Database=mydb'}
    """
    if '=' not in value:
        raise ValueError(
            f"Environment variable must be in 'key=value' format. Got: '{value}'"
        )

    # Split on first equals sign only (value might contain '=')
    key, _, val = value.partition('=')

    if not key:
        raise ValueError(
            f"Environment variable key cannot be empty. Got: '{value}'"
        )

    return {'key': key, 'value': val}


def extract_key_values_pairs(api_properties):
    api_properties_dict = {}
    for item in api_properties:
        api_properties_dict.update(validate_tag(item))
    return api_properties_dict


def validate_api_properties(ns):
    """Extracts JSON format or 'a=b c=d' format as api properties"""
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
                logger.warning(
                    "Api properties looks like a JSON format but not valid, interpreted as key=value pairs:"
                    " %s",
                    str(result),
                )
            ns.api_properties = result
            return


def _is_suspected_json(string):
    """If the string looks like a JSON"""
    if string.startswith("{") or string.startswith("'{") or string.startswith('"{'):
        return True
    if string.startswith("[") or string.startswith("'[") or string.startswith('"['):
        return True
    if re.match(r"^['\"\s]*{.+}|\[.+\]['\"\s]*$", string):
        return True

    return False


api_properties_type = CLIArgumentType(
    validator=validate_api_properties,
    help="Api properties in JSON format or a=b c=d format. Some cognitive services (i.e. QnA Maker) "
    "require extra api properties to create the account.",
    nargs="*",
)


def _sku_filter(cmd, namespace):
    """
    Get a list of ResourceSku and filter by existing conditions: 'kind', 'location' and 'sku_name'
    """
    kind = getattr(namespace, "kind", None)
    location = getattr(namespace, "location", None)
    sku_name = getattr(namespace, "sku_name", None)

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
    from azure.mgmt.core.tools import resource_id, is_valid_resource_id
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
            namespace="Microsoft.Network",
            type="virtualNetworks",
            name=vnet,
            child_type_1="subnets",
            child_name_1=subnet,
        )


def _validate_user_assigned_identity(cmd, namespace):
    from azure.mgmt.core.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    if namespace.user_assigned_identity:
        identity = namespace.user_assigned_identity
        if not is_valid_resource_id(identity):
            namespace.user_assigned_identity = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.ManagedIdentity',
                type='userAssignedIdentities',
                name=identity)


@Completer
def sku_name_completer(
    cmd, prefix, namespace, **kwargs
):  # pylint: disable=unused-argument
    names = {x.name for x in _sku_filter(cmd, namespace)}
    # TODO: For deployment
    return sorted(list(names))


@Completer
def kind_completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    kinds = {x.kind for x in _sku_filter(cmd, namespace)}
    return sorted(list(kinds))


@Completer
def location_completer(
    cmd, prefix, namespace, **kwargs
):  # pylint: disable=unused-argument
    names = {location for x in _sku_filter(cmd, namespace) for location in x.locations}
    return [x.lower() for x in sorted(list(names))]


def load_arguments(self, _):
    with self.argument_context("cognitiveservices") as c:
        c.argument(
            "account_name",
            arg_type=name_arg_type,
            help="cognitive service account name",
            completer=get_resource_name_completion_list(
                "Microsoft.CognitiveServices/accounts"
            ),
        )
        c.argument(
            "location",
            arg_type=get_location_type(self.cli_ctx),
            completer=location_completer,
        )
        c.argument("resource_group_name", arg_type=resource_group_name_type)
        c.argument(
            "sku_name",
            options_list=["--sku", "--sku-name"],
            help="Name of the Sku of Cognitive Services account/deployment",
            completer=sku_name_completer,
        )
        c.argument(
            "sku_capacity",
            options_list=["--capacity", "--sku-capacity"],
            help="Capacity value of the Sku of Cognitive Services account/deployment.",
        )
        c.argument(
            "kind",
            help="the API name of cognitive services account",
            completer=kind_completer,
        )
        c.argument("tags", tags_type)
        c.argument(
            "key_name",
            required=True,
            help="Key name to generate",
            arg_type=get_enum_type(KeyName),
        )
        c.argument("api_properties", api_properties_type)
        c.argument(
            "custom_domain",
            help="User domain assigned to the account. Name is the CNAME source.",
        )
        c.argument(
            "storage",
            help="The storage accounts for this resource, in JSON array format.",
        )
        c.argument(
            "encryption",
            help="The encryption properties for this resource, in JSON format.",
        )

    with self.argument_context(
        "cognitiveservices account", arg_group="AI Services"
    ) as c:
        c.argument(
            "allow_project_management",
            options_list=["--manage-projects", "--allow-project-management"],
            arg_type=get_three_state_flag(),
            help="AIServices kind only. Enables project management.  Default true.",
        )

    with self.argument_context("cognitiveservices account create") as c:
        c.argument(
            "assign_identity",
            help="Generate and assign an Azure Active Directory Identity for this account.",
        )
        c.argument(
            "yes", action="store_true", help="Do not prompt for terms confirmation"
        )

    with self.argument_context(
        "cognitiveservices account update", arg_group="AI Services"
    ) as c:
        c.argument(
            "kind",
            arg_type=get_enum_type(data=["AIServices", "OpenAI"]),
            help="The target API name to transform the existing account into.",
        )

    with self.argument_context("cognitiveservices account network-rule") as c:
        c.argument("ip_address", help="IPv4 address or CIDR range.")
        c.argument(
            "subnet",
            help="Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.",
        )
        c.argument(
            "vnet_name", help="Name of a virtual network.", validator=_validate_subnet
        )

    with self.argument_context("cognitiveservices account deployment") as c:
        c.argument("deployment_name", help="Cognitive Services account deployment name")

    with self.argument_context(
        "cognitiveservices account deployment", arg_group="DeploymentModel"
    ) as c:
        c.argument(
            "model_name", help="Cognitive Services account deployment model name."
        )
        c.argument(
            "model_format", help="Cognitive Services account deployment model format."
        )
        c.argument(
            "model_version", help="Cognitive Services account deployment model version."
        )
        c.argument(
            "model_source", help="Cognitive Services account deployment model source."
        )

    with self.argument_context(
        "cognitiveservices account deployment", arg_group="DeploymentScaleSettings"
    ) as c:
        c.argument(
            "scale_settings_scale_type",
            get_enum_type(DeploymentScaleType),
            options_list=["--scale-type", "--scale-settings-scale-type"],
            help="Cognitive Services account deployment scale settings scale type.",
        )
        c.argument(
            "scale_settings_capacity",
            options_list=["--scale-capacity", "--scale-settings-capacity"],
            help="Cognitive Services account deployment scale settings capacity.",
        )

    with self.argument_context("cognitiveservices account commitment-plan") as c:
        c.argument(
            "commitment_plan_name",
            help="Cognitive Services account commitment plan name",
        )
        c.argument("plan_type", help="Cognitive Services account commitment plan type")
        c.argument(
            "hosting_model",
            get_enum_type(HostingModel),
            help="Cognitive Services account hosting model",
        )
        c.argument(
            "auto_renew",
            arg_type=get_three_state_flag(),
            help="A boolean indicating whether to apply auto renew.",
        )

    with self.argument_context(
        "cognitiveservices account commitment-plan",
        arg_group="Current CommitmentPeriod",
    ) as c:
        c.argument(
            "current_count",
            help="Cognitive Services account commitment plan current commitment period count.",
        )
        c.argument(
            "current_tier",
            help="Cognitive Services account commitment plan current commitment period tier.",
        )

    with self.argument_context(
        "cognitiveservices account commitment-plan", arg_group="Next CommitmentPeriod"
    ) as c:
        c.argument(
            "next_count",
            help="Cognitive Services account commitment plan next commitment period count.",
        )
        c.argument(
            "next_tier",
            help="Cognitive Services account commitment plan next commitment period tier.",
        )

    with self.argument_context("cognitiveservices agent") as c:
        c.argument(
            "account_name",
            options_list=["--account-name", "-a"],
            help="cognitive service account name."
        )
        c.argument(
            "project_name",
            options_list=["--project-name", "-p"],
            help="AI project name"
        )
        c.argument(
            "agent_name",
            options_list=["--name", "-n"],
            help="Cognitive Services hosted agent name",
        )
        c.argument("agent_version", help="Cognitive Services hosted agent version")

    with self.argument_context("cognitiveservices agent status") as c:
        c.argument(
            "agent_version",
            help="Cognitive Services hosted agent version",
            required=True,
        )

    with self.argument_context('cognitiveservices agent create') as c:
        c.argument(
            'agent_name',
            options_list=['--name', '-n'],
            help='Name of the agent to create',
            required=True
        )
        c.argument(
            'image',
            help=(
                'Container image URI including tag '
                '(e.g., myregistry.azurecr.io/myagent:v1 or myagent:v1 if using --registry). '
                'The image tag becomes the agent version. Mutually exclusive with --source.'
            )
        )
        c.argument(
            'source',
            help=(
                'Path to source directory containing Dockerfile. '
                'When provided, the image will be built and pushed automatically. '
                'Mutually exclusive with --image.'
            )
        )
        c.argument(
            'dockerfile',
            help=(
                'Name of the Dockerfile in the source directory. '
                'Default: "Dockerfile". Only used with --source.'
            )
        )
        c.argument(
            'build_remote',
            options_list=['--build-remote'],
            action='store_true',
            help=(
                'Force remote build using Azure Container Registry Task. '
                'By default, builds locally if Docker is available, '
                'otherwise builds remotely. Only used with --source.'
            )
        )
        c.argument(
            'registry',
            help=(
                'Azure Container Registry name (e.g., myregistry). '
                'If provided, the full ACR URI will be constructed. '
                'Required when using --source.'
            )
        )
        c.argument(
            'cpu',
            help='CPU cores allocation (e.g., "1", "2", "0.5"). Default: "1"',
            default='1'
        )
        c.argument(
            'memory',
            help='Memory allocation with units (e.g., "2Gi", "4Gi", "512Mi"). Default: "2Gi"',
            default='2Gi'
        )
        c.argument(
            'environment_variables',
            options_list=['--environment-variables', '--env'],
            nargs='+',
            type=_environment_variables_type,
            help="Space-separated environment variables in 'key=value' format (e.g., FOO=bar LOG_LEVEL=debug)"
        )
        c.argument(
            'protocol',
            help='Agent communication protocol. Default: "responses"',
            arg_type=get_enum_type(['responses', 'streaming']),
            default='responses'
        )
        c.argument(
            'protocol_version',
            help='Protocol version. Default: "v1"',
            default='v1'
        )
        c.argument(
            'description',
            help='Human-readable description of the agent'
        )
        c.argument(
            'min_replicas',
            type=int,
            help='Minimum number of replicas for horizontal scaling. Default: 0'
        )
        c.argument(
            'max_replicas',
            type=int,
            help='Maximum number of replicas for horizontal scaling. Default: 3'
        )
        c.argument(
            'skip_acr_check',
            action='store_true',
            help=(
                'Skip validation that project managed identity has access to '
                'container registry. Use when access is configured via user-assigned '
                'identity, service principal, network-level permissions, or other methods '
                'the check cannot detect.'
            )
        )
        c.argument(
            'no_wait',
            action='store_true',
            help='Do not wait for the long-running operation to finish'
        )
        c.argument(
            'no_start',
            action='store_true',
            help=(
                'Skip automatic deployment after agent version creation. '
                'Use this to create the agent version without starting the deployment. '
                'Cannot be used with --min-replicas or --max-replicas.'
            )
        )
        c.argument(
            'timeout',
            type=int,
            help=(
                'Maximum time in seconds to wait for deployment to be ready. '
                'Default: 600 seconds (10 minutes). '
                'Increase for large container images or slow network conditions.'
            ),
            default=600
        )
        c.argument(
            'show_logs',
            options_list=['--show-logs'],
            action='store_true',
            help=(
                'Stream container console logs during deployment. '
                'Shows real-time output from the agent container as it starts up. '
                'Useful for debugging startup issues.'
            )
        )

    with self.argument_context("cognitiveservices agent update") as c:
        c.argument(
            "min_replicas",
            type=int,
            options_list=["--min-replicas"],
            help="Minimum number of replicas for horizontal scaling",
        )
        c.argument(
            "max_replicas",
            type=int,
            options_list=["--max-replicas"],
            help="Maximum number of replicas for horizontal scaling",
        )
        c.argument("description", help="Description of the agent")

    with self.argument_context("cognitiveservices agent delete") as c:
        c.argument(
            "agent_version",
            help="Cognitive Services hosted agent version. If not provided, deletes all versions.",
            required=False,
        )

    with self.argument_context("cognitiveservices agent start") as c:
        c.argument(
            'show_logs',
            options_list=['--show-logs'],
            action='store_true',
            help=(
                'Stream container console logs during startup. '
                'Shows real-time output from the agent container as it starts. '
                'Useful for debugging startup issues.'
            )
        )
        c.argument(
            'timeout',
            type=int,
            help=(
                'Maximum time in seconds to wait for deployment to be ready. '
                'Default: 600 seconds (10 minutes).'
            ),
            default=600
        )

    with self.argument_context("cognitiveservices agent logs") as c:
        c.argument(
            "account_name",
            options_list=["--account-name", "-a"],
            help="Cognitive service account name."
        )
        c.argument(
            "project_name",
            options_list=["--project-name", "-p"],
            help="AI project name"
        )
        c.argument(
            "agent_name",
            options_list=["--name", "-n"],
            help="Cognitive Services hosted agent name",
        )
        c.argument("agent_version", help="Cognitive Services hosted agent version")

    with self.argument_context("cognitiveservices agent logs show") as c:
        c.argument(
            'kind',
            options_list=['--type', '-t'],
            help="Type of logs to stream. 'console' for stdout/stderr, 'system' for container events.",
            arg_type=get_enum_type(['console', 'system']),
            default='console'
        )
        c.argument(
            'tail',
            type=int,
            help='Number of trailing log lines to fetch (1-300). Default: 50',
            default=50
        )
        c.argument(
            'follow',
            options_list=['--follow', '-f'],
            action='store_true',
            help='Stream logs in real-time. Without this flag, fetches recent logs and exits.'
        )

    with self.argument_context('cognitiveservices') as c:
        c.argument('account_name', arg_type=name_arg_type, help='cognitive service account name',
                   completer=get_resource_name_completion_list('Microsoft.CognitiveServices/accounts'))
        c.argument('location', arg_type=get_location_type(self.cli_ctx),
                   completer=location_completer)
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('sku_name', options_list=['--sku', '--sku-name'],
                   help='Name of the Sku of Cognitive Services account/deployment',
                   completer=sku_name_completer)
        c.argument('sku_capacity', options_list=['--capacity', '--sku-capacity'],
                   help='Capacity value of the Sku of Cognitive Services account/deployment.')
        c.argument('kind', help='the API name of cognitive services account',
                   completer=kind_completer)
        c.argument('tags', tags_type)
        c.argument('key_name', required=True, help='Key name to generate', arg_type=get_enum_type(KeyName))
        c.argument('api_properties', api_properties_type)
        c.argument('custom_domain', help='User domain assigned to the account. Name is the CNAME source.')
        c.argument('storage', help='The storage accounts for this resource, in JSON array format.')
        c.argument('encryption', help='The encryption properties for this resource, in JSON format.')

    with self.argument_context('cognitiveservices account', arg_group="AI Services") as c:
        c.argument('allow_project_management',
                   options_list=['--manage-projects', '--allow-project-management'],
                   arg_type=get_three_state_flag(),
                   help='AIServices kind only. Enables project management.  Default true.')

    with self.argument_context('cognitiveservices account create') as c:
        c.argument('assign_identity', help='Generate and assign an Azure Active Directory Identity for this account.')
        c.argument('yes', action='store_true', help='Do not prompt for terms confirmation')

    with self.argument_context('cognitiveservices account update', arg_group="AI Services") as c:
        c.argument('kind',
                   arg_type=get_enum_type(data=['AIServices', 'OpenAI']),
                   help='The target API name to transform the existing account into.')

    with self.argument_context('cognitiveservices account network-rule') as c:
        c.argument('ip_address', help='IPv4 address or CIDR range.')
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.', validator=_validate_subnet)

    with self.argument_context('cognitiveservices account deployment') as c:
        c.argument('deployment_name', help='Cognitive Services account deployment name')
        c.argument('spillover_deployment_name',
                   options_list=['--spillover-deployment-name', '--spillover-name'],
                   help='The name of the standard deployment to use as a spillover when at capacity.')

    with self.argument_context('cognitiveservices account deployment', arg_group='DeploymentModel') as c:
        c.argument('model_name', help='Cognitive Services account deployment model name.')
        c.argument('model_format', help='Cognitive Services account deployment model format.')
        c.argument('model_version', help='Cognitive Services account deployment model version.')
        c.argument('model_source', help='Cognitive Services account deployment model source.')

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

    with self.argument_context('cognitiveservices account project') as c:
        c.argument('project_name', help='Cognitive Services account project name')
        c.argument('location', arg_type=get_location_type(self.cli_ctx),
                   completer=location_completer)
        c.argument('description', help='Description of the project.')
        c.argument('display_name', help='Display name of the project.')

    with self.argument_context('cognitiveservices account project', arg_group='Project Identity') as c:
        c.argument("assign_identity",
                   options_list=['--include-system-identity', '--assign-identity'],
                   help=('Use with --user-assigned-identity to generate and assign a '
                         'system managed Azure Active Directory Identity for this project.'))
        c.argument('user_assigned_identity',
                   help=('User assigned identity resource ID to use for the project. '
                         'If not specified, a system assigned identity will be used.'),
                   validator=_validate_user_assigned_identity)

    with self.argument_context('cognitiveservices account project create') as c:
        c.argument('description', help='Description of the project.')
        c.argument('display_name', help='Display name of the project.')

    with self.argument_context('cognitiveservices account project connection') as c:
        c.argument('connection_name', help='Cognitive Services account connection name')
        c.argument('file', help='Path to the connection file in JSON or YAML format.')

    with self.argument_context('cognitiveservices account connection') as c:
        c.argument('connection_name', help='Cognitive Services account connection name')
        c.argument('file', help='Path to the connection file in JSON or YAML format.')

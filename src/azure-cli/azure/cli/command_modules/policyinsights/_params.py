# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import (
    resource_group_name_type, get_enum_type)

from azure.cli.command_modules.resource._completers import (
    get_providers_completion_list, get_resource_types_completion_list)

from ._validators import (validate_resource, validate_expand)
from azure.cli.command_modules.resource._validators import validate_metadata

from ._completers import (
    get_policy_set_completion_list, get_policy_completion_list, get_policy_assignment_completion_list,
    get_policy_remediation_completion_list, get_policy_metadata_completion_list)

from ._actions import AttestationEvidenceAddAction


def load_arguments(self, _):
    for scope in ['state', 'event', 'remediation']:
        with self.argument_context('policy {}'.format(scope)) as c:
            c.argument(
                'management_group_name',
                options_list=['--management-group', '-m'],
                arg_group='Scope',
                help='Name of management group.')
            c.argument(
                'resource',
                validator=validate_resource,
                arg_group='Resource ID',
                help='Resource ID or resource name. If a name is given, please provide the resource group and other relevant resource id arguments.')  # pylint: disable=line-too-long

    for scope in ['state', 'event', 'remediation', 'attestation']:
        with self.argument_context('policy {}'.format(scope)) as c:
            c.argument(
                'resource_group_name',
                arg_type=resource_group_name_type,
                arg_group='Scope')
            c.argument(
                'namespace',
                completer=get_providers_completion_list,
                arg_group='Resource ID',
                help='Provider namespace (Ex: Microsoft.Provider).')
            c.argument(
                'resource_type_parent',
                options_list=['--parent'],
                arg_group='Resource ID',
                help='The parent path (Ex: resourceTypeA/nameA/resourceTypeB/nameB).')
            c.argument(
                'resource_type',
                completer=get_resource_types_completion_list,
                arg_group='Resource ID',
                help='Resource type (Ex: resourceTypeC).')

    for scope in ['state', 'event']:
        with self.argument_context('policy {}'.format(scope)) as c:
            c.argument(
                'policy_set_definition_name',
                options_list=['--policy-set-definition', '-s'],
                completer=get_policy_set_completion_list,
                arg_group='Scope',
                help='Name of policy set definition.')
            c.argument(
                'policy_definition_name',
                options_list=['--policy-definition', '-d'],
                completer=get_policy_completion_list,
                arg_group='Scope',
                help='Name of policy definition.')
            c.argument(
                'policy_assignment_name',
                options_list=['--policy-assignment', '-a'],
                completer=get_policy_assignment_completion_list,
                arg_group='Scope',
                help='Name of policy assignment.')
            c.argument(
                'from_value',
                options_list=['--from'],
                arg_group='Query Option',
                help='ISO 8601 formatted timestamp specifying the start time of the interval to query.')
            c.argument(
                'to_value',
                options_list=['--to'],
                arg_group='Query Option',
                help='ISO 8601 formatted timestamp specifying the end time of the interval to query.')
            c.argument(
                'top_value',
                options_list=['--top'],
                type=int,
                arg_group='Query Option',
                help='Maximum number of records to return.')
            c.argument(
                'order_by_clause',
                options_list=['--order-by'],
                arg_group='Query Option',
                help='Ordering expression using OData notation.')
            c.argument(
                'select_clause',
                options_list=['--select'],
                arg_group='Query Option',
                help='Select expression using OData notation.')
            c.argument(
                'filter_clause',
                options_list=['--filter'],
                arg_group='Query Option',
                help='Filter expression using OData notation.')
            c.argument(
                'apply_clause',
                options_list=['--apply'],
                arg_group='Query Option',
                help='Apply expression for aggregations using OData notation.')

    with self.argument_context('policy state') as c:
        c.argument(
            'all_results',
            options_list=['--all'],
            action='store_true',
            help='Within the specified time interval, get all policy states instead of the latest only.')
        c.argument(
            'expand_clause',
            validator=validate_expand,
            options_list=['--expand'],
            arg_group='Query Option',
            help='Expand expression using OData notation.')

    with self.argument_context('policy state summarize') as c:
        c.ignore('all_results', 'order_by_clause',
                 'select_clause', 'apply_clause', 'expand_clause')

    with self.argument_context('policy remediation') as c:
        c.argument('remediation_name', options_list=['--name', '-n'],
                   completer=get_policy_remediation_completion_list, help='Name of the remediation.')

    with self.argument_context('policy remediation create') as c:
        c.argument(
            'location_filters',
            options_list='--location-filters',
            nargs='+',
            help='Space separated list of resource locations that should be remediated (Ex: centralus westeurope).')  # pylint: disable=line-too-long
        c.argument(
            'policy_assignment',
            options_list=['--policy-assignment', '-a'],
            completer=get_policy_assignment_completion_list,
            help='Name or resource ID of the policy assignment.')
        c.argument(
            'definition_reference_id',
            options_list=['--definition-reference-id'],
            help='Policy definition reference ID inside the policy set definition. Only required when the policy assignment is assigning a policy set definition.')  # pylint: disable=line-too-long
        c.argument(
            'resource_discovery_mode',
            arg_type=get_enum_type(
                ['ExistingNonCompliant', 'ReEvaluateCompliance']),
            help='The way resources to remediate are discovered. Defaults to ExistingNonCompliant if not specified.')

    with self.argument_context('policy metadata show') as c:
        c.argument(
            'resource_name',
            options_list=['--name', '-n'],
            completer=get_policy_metadata_completion_list,
            help='The name of the metadata resource.')

    with self.argument_context('policy metadata list') as c:
        c.argument(
            'top_value',
            options_list=['--top'],
            type=int,
            help='Maximum number of records to return.')

    with self.argument_context('policy attestation') as c:
        c.argument(
            'attestation_name',
            options_list=["--attestation-name", "-n", "--name"],
            help="The name of the attestation."
        )
        c.argument(
            'resource',
            validator=validate_resource,
            options_list=['--resource', '--resource-id'],
            arg_group='Resource ID',
            help='Resource ID or resource name. If a name is given, please provide the resource group and other relevant resource id arguments.')  # pylint: disable=line-too-long

    for operation in ["create", "update"]:
        with self.argument_context('policy attestation {}'.format(operation)) as c:
            c.argument(
                'policy_assignment_id',
                options_list=['--policy-assignment-id',
                              '--policy-assignment', '-a'],
                arg_group="Properties",
                completer=get_policy_assignment_completion_list,
                help="The resource ID of the policy assignment that the attestation is setting the state for."
            )
            c.argument(
                'comments',
                options_list=["--comments"],
                arg_group="Properties",
                help="Comments describing why this attestation was created."
            )
            c.argument(
                'assessment_date',
                options_list=["--assessment-date"],
                arg_group="Properties",
                help="The time the evidence was assessed."
            )
            c.argument(
                'compliance_state',
                options_list=["--compliance-state"],
                arg_type=get_enum_type(
                    ["Compliant", "NonCompliant", "Unknown"]),
                arg_group="Properties",
                help="The compliance state that should be set on the resource."
            )
            c.argument(
                'evidence',
                options_list=["--evidence"],
                arg_group="Properties",
                action=AttestationEvidenceAddAction,
                nargs='*',
                help="The evidence supporting the compliance state set in this attestation."
            )
            c.argument(
                'expires_on',
                options_list=["--expires-on"],
                arg_group="Properties",
                help="The time the compliance state should expire."
            )
            c.argument(
                'owner',
                options_list=["--owner"],
                arg_group="Properties",
                help="The person responsible for setting the state of the resource. This value is typically an Azure Active Directory object ID."  # pylint: disable=line-too-long
            )
            c.argument(
                'definition_reference_id',
                options_list=["--definition-reference-id"],
                arg_group="Properties",
                help="The policy definition reference ID from a policy set definition that the attestation is setting the state for. "  # pylint: disable=line-too-long
                "If the policy assignment assigns a policy set definition the attestation can choose a definition within the set definition with this property or omit this and set the state for the entire set definition."  # pylint: disable=line-too-long
            )
            c.argument(
                'metadata',
                options_list='--metadata',
                arg_group='Properties',
                help='Additional metadata in space-separated key=value pairs for an attestation. This overwrites any existing metadata for the attestation.',  # pylint: disable=line-too-long
                nargs='*',
                validator=validate_metadata
            )

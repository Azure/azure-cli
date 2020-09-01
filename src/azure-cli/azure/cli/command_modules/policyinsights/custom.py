# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrestazure.tools import is_valid_resource_id, resource_id

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import sdk_no_wait

from knack.util import CLIError


def list_policy_events(
        cmd,
        client,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None,
        policy_set_definition_name=None,
        policy_definition_name=None,
        policy_assignment_name=None,
        from_value=None,
        to_value=None,
        order_by_clause=None,
        select_clause=None,
        top_value=None,
        filter_clause=None,
        apply_clause=None):

    from azure.mgmt.policyinsights.models import QueryOptions

    query_options = QueryOptions(
        top=top_value,
        order_by=order_by_clause,
        select=select_clause,
        from_property=from_value,
        to=to_value,
        filter=filter_clause,
        apply=apply_clause)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    if policy_assignment_name:
        if resource_group_name:
            events = client.list_query_results_for_resource_group_level_policy_assignment(
                subscription_id,
                resource_group_name,
                policy_assignment_name,
                query_options)
        else:
            events = client.list_query_results_for_subscription_level_policy_assignment(
                subscription_id,
                policy_assignment_name,
                query_options)
    elif policy_definition_name:
        events = client.list_query_results_for_policy_definition(
            subscription_id,
            policy_definition_name,
            query_options)
    elif policy_set_definition_name:
        events = client.list_query_results_for_policy_set_definition(
            subscription_id,
            policy_set_definition_name,
            query_options)
    elif resource:
        if not is_valid_resource_id(resource):
            if resource_type_parent:
                resource_type_parent = _remove_leading_and_trailing_slash(resource_type_parent)
                resource_type = "{}/{}".format(resource_type_parent, resource_type)
            resource = resource_id(
                subscription=subscription_id,
                resource_group=resource_group_name,
                namespace=namespace,
                type=resource_type,
                name=resource)
        events = client.list_query_results_for_resource(
            resource,
            query_options)
    elif resource_group_name:
        events = client.list_query_results_for_resource_group(
            subscription_id,
            resource_group_name,
            query_options)
    elif management_group_name:
        events = client.list_query_results_for_management_group(
            management_group_name,
            query_options)
    else:
        events = client.list_query_results_for_subscription(
            subscription_id,
            query_options)

    return events.value


def list_policy_states(
        cmd,
        client,
        all_results=False,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None,
        policy_set_definition_name=None,
        policy_definition_name=None,
        policy_assignment_name=None,
        from_value=None,
        to_value=None,
        order_by_clause=None,
        select_clause=None,
        top_value=None,
        filter_clause=None,
        apply_clause=None,
        expand_clause=None):

    from azure.mgmt.policyinsights.models import QueryOptions

    query_options = QueryOptions(
        top=top_value,
        order_by=order_by_clause,
        select=select_clause,
        from_property=from_value,
        to=to_value,
        filter=filter_clause,
        apply=apply_clause,
        expand=expand_clause)

    policy_states_resource = 'latest'
    if all_results is True:
        policy_states_resource = 'default'

    subscription_id = get_subscription_id(cmd.cli_ctx)

    if policy_assignment_name:
        if resource_group_name:
            states = client.list_query_results_for_resource_group_level_policy_assignment(
                policy_states_resource,
                subscription_id,
                resource_group_name,
                policy_assignment_name,
                query_options)
        else:
            states = client.list_query_results_for_subscription_level_policy_assignment(
                policy_states_resource,
                subscription_id,
                policy_assignment_name,
                query_options)
    elif policy_definition_name:
        states = client.list_query_results_for_policy_definition(
            policy_states_resource,
            subscription_id,
            policy_definition_name,
            query_options)
    elif policy_set_definition_name:
        states = client.list_query_results_for_policy_set_definition(
            policy_states_resource,
            subscription_id,
            policy_set_definition_name,
            query_options)
    elif resource:
        if not is_valid_resource_id(resource):
            if resource_type_parent:
                resource_type_parent = _remove_leading_and_trailing_slash(resource_type_parent)
                resource_type = "{}/{}".format(resource_type_parent, resource_type)
            resource = resource_id(
                subscription=subscription_id,
                resource_group=resource_group_name,
                namespace=namespace,
                type=resource_type,
                name=resource)
        states = client.list_query_results_for_resource(
            policy_states_resource,
            resource,
            query_options)
    elif resource_group_name:
        states = client.list_query_results_for_resource_group(
            policy_states_resource,
            subscription_id,
            resource_group_name,
            query_options)
    elif management_group_name:
        states = client.list_query_results_for_management_group(
            policy_states_resource,
            management_group_name,
            query_options)
    else:
        states = client.list_query_results_for_subscription(
            policy_states_resource,
            subscription_id,
            query_options)

    return states.value


def summarize_policy_states(
        cmd,
        client,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None,
        policy_set_definition_name=None,
        policy_definition_name=None,
        policy_assignment_name=None,
        from_value=None,
        to_value=None,
        top_value=None,
        filter_clause=None):

    from azure.mgmt.policyinsights.models import QueryOptions

    query_options = QueryOptions(
        top=top_value,
        from_property=from_value,
        to=to_value,
        filter=filter_clause)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    if policy_assignment_name:
        if resource_group_name:
            summary = client.summarize_for_resource_group_level_policy_assignment(
                subscription_id,
                resource_group_name,
                policy_assignment_name,
                query_options)
        else:
            summary = client.summarize_for_subscription_level_policy_assignment(
                subscription_id,
                policy_assignment_name,
                query_options)
    elif policy_definition_name:
        summary = client.summarize_for_policy_definition(
            subscription_id,
            policy_definition_name,
            query_options)
    elif policy_set_definition_name:
        summary = client.summarize_for_policy_set_definition(
            subscription_id,
            policy_set_definition_name,
            query_options)
    elif resource:
        resource = _build_resource_id(
            subscription_id,
            resource,
            resource_group_name,
            namespace,
            resource_type_parent,
            resource_type)
        summary = client.summarize_for_resource(
            resource,
            query_options)
    elif resource_group_name:
        summary = client.summarize_for_resource_group(
            subscription_id,
            resource_group_name,
            query_options)
    elif management_group_name:
        summary = client.summarize_for_management_group(
            management_group_name,
            query_options)
    else:
        summary = client.summarize_for_subscription(
            subscription_id,
            query_options)

    return summary.value[0]


def trigger_policy_scan(
        cmd,
        client,
        resource_group_name=None,
        no_wait=False):

    subscription_id = get_subscription_id(cmd.cli_ctx)
    if resource_group_name:
        return sdk_no_wait(no_wait, client.trigger_resource_group_evaluation,
                           subscription_id, resource_group_name)

    return sdk_no_wait(no_wait, client.trigger_subscription_evaluation,
                       subscription_id)


def get_policy_remediation(
        cmd,
        client,
        remediation_name,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None):

    return _execute_remediation_operation(
        cmd,
        client,
        "get_at_resource",
        management_group_name,
        resource_group_name,
        resource,
        namespace,
        resource_type_parent,
        resource_type,
        remediation_name)


def list_policy_remediations(
        cmd,
        client,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None):

    return _execute_remediation_operation(
        cmd,
        client,
        "list_for_resource",
        management_group_name,
        resource_group_name,
        resource,
        namespace,
        resource_type_parent,
        resource_type)


def delete_policy_remediation(
        cmd,
        client,
        remediation_name,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None):

    return _execute_remediation_operation(
        cmd,
        client,
        "delete_at_resource",
        management_group_name,
        resource_group_name,
        resource,
        namespace,
        resource_type_parent,
        resource_type,
        remediation_name)


def cancel_policy_remediation(
        cmd,
        client,
        remediation_name,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None):

    return _execute_remediation_operation(
        cmd,
        client,
        "cancel_at_resource",
        management_group_name,
        resource_group_name,
        resource,
        namespace,
        resource_type_parent,
        resource_type,
        remediation_name)


def list_policy_remediation_deployments(
        cmd,
        client,
        remediation_name,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None):

    return _execute_remediation_operation(
        cmd,
        client,
        "list_deployments_at_resource",
        management_group_name,
        resource_group_name,
        resource,
        namespace,
        resource_type_parent,
        resource_type,
        remediation_name)


def create_policy_remediation(
        cmd,
        client,
        remediation_name,
        policy_assignment,
        definition_reference_id=None,
        location_filters=None,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None,
        resource_discovery_mode=None):

    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_remediation_scope(
        management_group_name,
        subscription_id,
        resource_group_name,
        resource,
        resource_type_parent,
        resource_type,
        namespace)

    from azure.mgmt.policyinsights.models import Remediation
    remediation = Remediation(policy_definition_reference_id=definition_reference_id)

    # Get the full resource ID of the referenced policy assignment
    if (not is_valid_resource_id(policy_assignment) and
            not policy_assignment.lower().startswith("/providers/microsoft.management/managementgroups/")):
        from ._client_factory import cf_policy
        policy_assignment_client = cf_policy(cmd.cli_ctx).policy_assignments
        policy_assignments = policy_assignment_client.list()
        policy_assignment_ids = [p.id for p in policy_assignments if p.name.lower() == policy_assignment.lower()]
        if not policy_assignment_ids:
            raise CLIError("No policy assignment with the name '{}' found.".format(policy_assignment))
        if len(policy_assignment_ids) > 1:
            raise CLIError("Multiple policy assignment with the name '{}' found. "
                           "Specify the policy assignment ID.".format(policy_assignment))
        policy_assignment = policy_assignment_ids[0]
    remediation.policy_assignment_id = policy_assignment

    # Ensure locations in the location filters are using their short name
    if location_filters:
        locations_list = []
        for location_arg in location_filters:
            locations_list.append(location_arg.replace(' ', ''))
        from azure.mgmt.policyinsights.models import RemediationFilters
        remediation.filters = RemediationFilters(locations=locations_list)

    if resource_discovery_mode:
        remediation.resource_discovery_mode = resource_discovery_mode

    return client.create_or_update_at_resource(
        resource_id=_remove_leading_and_trailing_slash(scope),
        remediation_name=remediation_name,
        parameters=remediation)


def show_policy_metadata(cmd, client, resource_name):   # pylint: disable=unused-argument
    return client.get_resource(resource_name=resource_name)


def list_policy_metadata(cmd, client, top_value=None):   # pylint: disable=unused-argument
    if top_value is not None:
        from azure.mgmt.policyinsights.models import QueryOptions
        page_iter = client.list(QueryOptions(top=top_value))
        results = []

        while len(results) < top_value:
            try:
                results.extend(list(page_iter.advance_page()))
            except StopIteration:
                break

        return results[:top_value]

    return list(client.list())


def _execute_remediation_operation(
        cmd,
        client,
        operation_name,
        management_group_name=None,
        resource_group_name=None,
        resource=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None,
        remediation_name=None):

    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_remediation_scope(
        management_group_name,
        subscription_id,
        resource_group_name,
        resource,
        resource_type_parent,
        resource_type,
        namespace)

    operation = getattr(client, operation_name)
    if remediation_name is None:
        return operation(resource_id=_remove_leading_and_trailing_slash(scope))
    return operation(resource_id=_remove_leading_and_trailing_slash(scope), remediation_name=remediation_name)


def _build_resource_id(
        subscription_id,
        resource,
        resource_group_name=None,
        namespace=None,
        resource_type_parent=None,
        resource_type=None):

    if not is_valid_resource_id(resource):
        if resource_type_parent:
            resource_type_parent = _remove_leading_and_trailing_slash(resource_type_parent)
            resource_type = "{}/{}".format(resource_type_parent, resource_type)

        resource = resource_id(
            subscription=subscription_id,
            resource_group=resource_group_name,
            namespace=namespace,
            type=resource_type,
            name=resource)

    return resource


def _build_remediation_scope(
        management_group=None,
        subscription=None,
        resource_group_name=None,
        resource=None,
        resource_type_parent=None,
        resource_type=None,
        namespace=None):

    if management_group:
        return "/providers/Microsoft.Management/managementGroups/{}".format(management_group)
    if resource:
        return _build_resource_id(subscription, resource, resource_group_name,
                                  namespace, resource_type_parent, resource_type)
    return resource_id(subscription=subscription, resource_group=resource_group_name)


def _remove_leading_and_trailing_slash(s):
    if s:
        if s.startswith('/'):
            s = s[1:]
        if s.endswith('/'):
            s = s[:-1]

    return s

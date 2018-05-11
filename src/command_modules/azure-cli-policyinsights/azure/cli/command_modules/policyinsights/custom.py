# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.client_factory import get_subscription_id

def list_policy_events(
        cmd,
        client,
        management_group_name=None,
        subscription_id=None,
        resource_group_name=None,
        resource_id=None,
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

    default_subscription_id = subscription_id
    if default_subscription_id is None:
        default_subscription_id = get_subscription_id(cmd.cli_ctx)

    if policy_assignment_name is not None:
        if resource_group_name is not None:
            events = client.list_query_results_for_resource_group_level_policy_assignment(default_subscription_id, resource_group_name, policy_assignment_name, query_options)
        else:
            events = client.list_query_results_for_subscription_level_policy_assignment(default_subscription_id, policy_assignment_name, query_options)
    elif policy_definition_name is not None:
        events = client.list_query_results_for_policy_definition(default_subscription_id, policy_definition_name, query_options)
    elif policy_set_definition_name is not None:
        events = client.list_query_results_for_policy_set_definition(default_subscription_id, policy_set_definition_name, query_options)
    elif resource_id is not None:
        events = client.list_query_results_for_resource(resource_id, query_options)
    elif resource_group_name is not None:
        events = client.list_query_results_for_resource_group(default_subscription_id, resource_group_name, query_options)
    elif management_group_name is not None:
        events = client.list_query_results_for_management_group(management_group_name, query_options)
    else:
        events = client.list_query_results_for_subscription(default_subscription_id, query_options)

    return events

def list_policy_states(
        cmd,
        client,
        all_results=False,
        management_group_name=None,
        subscription_id=None,
        resource_group_name=None,
        resource_id=None,
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

    policy_states_resource = 'latest'
    if all_results is True:
        policy_states_resource = 'default'

    default_subscription_id = subscription_id
    if default_subscription_id is None:
        default_subscription_id = get_subscription_id(cmd.cli_ctx)

    if policy_assignment_name is not None:
        if resource_group_name is not None:
            states = client.list_query_results_for_resource_group_level_policy_assignment(policy_states_resource, default_subscription_id, resource_group_name, policy_assignment_name, query_options)
        else:
            states = client.list_query_results_for_subscription_level_policy_assignment(policy_states_resource, default_subscription_id, policy_assignment_name, query_options)
    elif policy_definition_name is not None:
        states = client.list_query_results_for_policy_definition(policy_states_resource, default_subscription_id, policy_definition_name, query_options)
    elif policy_set_definition_name is not None:
        states = client.list_query_results_for_policy_set_definition(policy_states_resource, default_subscription_id, policy_set_definition_name, query_options)
    elif resource_id is not None:
        states = client.list_query_results_for_resource(policy_states_resource, resource_id, query_options)
    elif resource_group_name is not None:
        states = client.list_query_results_for_resource_group(policy_states_resource, default_subscription_id, resource_group_name, query_options)
    elif management_group_name is not None:
        states = client.list_query_results_for_management_group(policy_states_resource, management_group_name, query_options)
    else:
        states = client.list_query_results_for_subscription(policy_states_resource, default_subscription_id, query_options)

    return states

def summarize_policy_states(
        cmd,
        client,
        management_group_name=None,
        subscription_id=None,
        resource_group_name=None,
        resource_id=None,
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

    default_subscription_id = subscription_id
    if default_subscription_id is None:
        default_subscription_id = get_subscription_id(cmd.cli_ctx)

    if policy_assignment_name is not None:
        if resource_group_name is not None:
            summary = client.summarize_for_resource_group_level_policy_assignment(default_subscription_id, resource_group_name, policy_assignment_name, query_options)
        else:
            summary = client.summarize_for_subscription_level_policy_assignment(default_subscription_id, policy_assignment_name, query_options)
    elif policy_definition_name is not None:
        summary = client.summarize_for_policy_definition(default_subscription_id, policy_definition_name, query_options)
    elif policy_set_definition_name is not None:
        summary = client.summarize_for_policy_set_definition(default_subscription_id, policy_set_definition_name, query_options)
    elif resource_id is not None:
        summary = client.summarize_for_resource(resource_id, query_options)
    elif resource_group_name is not None:
        summary = client.summarize_for_resource_group(default_subscription_id, resource_group_name, query_options)
    elif management_group_name is not None:
        summary = client.summarize_for_management_group(management_group_name, query_options)
    else:
        summary = client.summarize_for_subscription(default_subscription_id, query_options)

    return summary

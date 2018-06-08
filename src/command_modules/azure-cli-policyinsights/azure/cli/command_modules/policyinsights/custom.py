# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrestazure.tools import is_valid_resource_id, resource_id
from azure.cli.core.commands.client_factory import get_subscription_id


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


def _remove_leading_and_trailing_slash(s):
    if s:
        if s.startswith('/'):
            s = s[1:]
        if s.endswith('/'):
            s = s[:-1]

    return s

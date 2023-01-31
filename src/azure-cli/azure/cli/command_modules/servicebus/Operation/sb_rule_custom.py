# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def sb_rule_create(cmd, resource_group_name, namespace_name, topic_name, subscription_name, rule_name,
                   action_sql_expression=None, action_compatibility_level=None, correlation_id=None,
                   action_requires_preprocessing=None, reply_to=None, label=None, session_id=None,
                   filter_sql_expression=None, filter_requires_preprocessing=None, reply_to_session_id=None,
                   message_id=None, to=None, content_type=None, requires_preprocessing=None,
                   filter_type=None, tags=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.topic.subscription.rule import Create
    command_arg_dict = {}
    command_arg_dict.update({
        'resource_group': resource_group_name,
        'namespace_name': namespace_name,
        'topic_name': topic_name,
        'subscription_name': subscription_name,
        'rule_name': rule_name,
        'action_sql_expression': action_sql_expression,
        'action_compatibility_level': action_compatibility_level,
        'action_requires_preprocessing': action_requires_preprocessing,
        'filter_type': filter_type
    })

    if filter_type == 'SqlFilter' or filter_type is None:
        command_arg_dict.update({
            'filter_sql_expression': filter_sql_expression,
            'filter_requires_preprocessing': filter_requires_preprocessing
        })

    if filter_type == 'CorrelationFilter':
        command_arg_dict.update({
            'correlation_id': correlation_id,
            'to': to,
            'message_id': message_id,
            'reply_to': reply_to,
            'properties': tags,
            'session_id': session_id,
            'reply_to_session_id': reply_to_session_id,
            'content_type': content_type,
            'requires_preprocessing': requires_preprocessing,
            'label': label
        })
    return Create(cli_ctx=cmd.cli_ctx)(command_args=command_arg_dict)





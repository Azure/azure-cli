# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_app_group_policy_object(col):
    policy_object = {}
    policy_object.update({
        "name": col["name"],
        "type": "ThrottlingPolicy",
    })

    if "rateLimitThreshold" in col and "metricId" in col:
        policy_object.update({
            "throttling_policy": {
                "rate_limit_threshold": col["rateLimitThreshold"],
                "metric_id": col["metricId"]
            }
        })

    return policy_object


def cli_appgroup_create(cmd, resource_group_name, namespace_name, application_group_name, client_app_group_identifier,
                        throttling_policy_config=None, is_enabled=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.application_group import Create
    command_args_dict = {}

    command_args_dict.update({
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "application_group_name": application_group_name,
        "is_enabled": is_enabled,
        "client_app_group_identifier": client_app_group_identifier,
        "policies": throttling_policy_config
    })

    return Create(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def cli_add_appgroup_policy(cmd, resource_group_name, namespace_name, application_group_name, throttling_policy_config):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.application_group import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.application_group import Show

    application_group = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "application_group_name": application_group_name
    })
    policy_object = []
    for obj in application_group["policies"]:
        policy = create_app_group_policy_object(obj)
        policy_object.append(policy)
    for obj in throttling_policy_config:
        if obj not in policy_object:
            policy_object.append(obj)
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "application_group_name": application_group_name,
        "policies": policy_object
    })


def cli_remove_appgroup_policy(cmd, resource_group_name, namespace_name, application_group_name, policy):
    from azure.cli.core.azclierror import ResourceNotFoundError
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.application_group import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.application_group import Show
    application_group = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "application_group_name": application_group_name
    })
    policy_object = []
    for i in policy:
        semaphor = 0
        for j in application_group["policies"]:
            if i["name"] == j["name"]:
                application_group["policies"].remove(j)
                semaphor = 1
        if semaphor == 0:
            raise ResourceNotFoundError('The following policy was not found: Name: ' + i["name"])
    for col in application_group["policies"]:
        policy_object.append(create_app_group_policy_object(col))
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "application_group_name": application_group_name,
        "policies": policy_object
    })

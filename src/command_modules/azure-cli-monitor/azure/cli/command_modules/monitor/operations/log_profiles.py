# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_log_profile_operations(client, name, location, locations, categories, days, enabled, tags=None,
                                  storage_account_id=None, service_bus_rule_id=None):
    from azure.mgmt.monitor.models.log_profile_resource import LogProfileResource
    from azure.mgmt.monitor.models import RetentionPolicy
    parameters = LogProfileResource(location=location, locations=locations, categories=categories,
                                    retention_policy=RetentionPolicy(days=days, enabled=enabled),
                                    storage_account_id=storage_account_id, service_bus_rule_id=service_bus_rule_id,
                                    tags=tags)
    return client.create_or_update(log_profile_name=name, parameters=parameters)

from azure.cli.commands._command_creation import (get_mgmt_service_client,
                                                  get_subscription_service_client)
from azure.mgmt.compute import ComputeManagementClient, ComputeManagementClientConfiguration

def _compute_client_factory(**_):
    return get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

def _subscription_client_factory(**_):
    from azure.mgmt.resource.subscriptions import (SubscriptionClient,
                                                   SubscriptionClientConfiguration)
    return get_subscription_service_client(SubscriptionClient, SubscriptionClientConfiguration)

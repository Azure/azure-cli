from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient, ComputeManagementClientConfiguration

def _compute_client_factory(**_):
    return get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

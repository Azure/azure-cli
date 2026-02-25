from azure.cli.core.util import sdk_no_wait
from ._flexible_server_util import get_tenant_id


# Create Microsoft Entra admin
def _create_admin(client, resource_group_name, server_name, principal_name, sid, principal_type=None, no_wait=False):
    parameters = {
        'properties': {
            'principalName': principal_name,
            'tenantId': get_tenant_id(),
            'principalType': principal_type
        }
    }

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, server_name, sid, parameters)
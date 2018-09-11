
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

def _resolve_api_version(cli_ctx, provider_namespace, resource_type, parent_path):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    provider = client.providers.get(provider_namespace)

    # If available, we will use parent resource's api-version
    resource_type_str = (parent_path.split('/')[0] if parent_path else resource_type)

    rt = [t for t in provider.resource_types  # pylint: disable=no-member
          if t.resource_type.lower() == resource_type_str.lower()]
    if not rt:
        raise CLIError('Resource type {} not found.'.format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    else:
        raise CLIError(
            'API version is required and could not be resolved for resource {}'
            .format(resource_type))


def check_existence(cli_ctx, value, resource_group, provider_namespace, resource_type,
                    parent_name=None, parent_type=None):
    # check for name or ID and set the type flags
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import parse_resource_id
    from azure.cli.core.profiles import ResourceType
    resource_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).resources

    id_parts = parse_resource_id(value)

    rg = id_parts.get('resource_group', resource_group)
    ns = id_parts.get('namespace', provider_namespace)

    if parent_name and parent_type:
        parent_path = '{}/{}'.format(parent_type, parent_name)
        resource_name = id_parts.get('child_name_1', value)
        resource_type = id_parts.get('child_type_1', resource_type)
    else:
        parent_path = ''
        resource_name = id_parts['name']
        resource_type = id_parts.get('type', resource_type)
    api_version = _resolve_api_version(cli_ctx, provider_namespace, resource_type, parent_path)

    try:
        resource_client.get(rg, ns, parent_path, resource_type, resource_name, api_version)
        return True
    except CloudError:
        return False
from ..commands import command, description
from ._command_creation import get_mgmt_service_client

@command('resource group list')
@description('List resource groups')
# TODO: waiting on Python Azure SDK bug fixes
# @option('--tag-name -g <tagName>', L('the resource group's tag name'))
# @option('--tag-value -g <tagValue>', L('the resource group's tag value'))
# @option('--top -g <number>', L('Top N resource groups to retrieve'))
def list_groups(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources import ResourceManagementClient, \
                                              ResourceManagementClientConfiguration
    from azure.mgmt.resource.resources.models import ResourceGroup, ResourceGroupFilter

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    # TODO: waiting on Python Azure SDK bug fixes
    #group_filter = ResourceGroupFilter(args.get('tag-name'), args.get('tag-value'))
    #groups = rmc.resource_groups.list(filter=None, top=args.get('top'))
    groups = rmc.resource_groups.list()
    return list(groups)

from ._command_creation import get_mgmt_service_client
from ..commands import CommandTable
from .._locale import L

command_table = CommandTable()

def get_command_table():
    return command_table

@command_table.option('--tag-name -tn', help=L("the resource group's tag name"))
@command_table.option('--tag-value -tv', help=L("the resource group's tag value"))
@command_table.option('--top -t', help=L('Top N resource groups to retrieve'))
@command_table.command('resource group list', description=L('List resource groups'))
def list_groups(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources import ResourceManagementClient, \
                                              ResourceManagementClientConfiguration
    from azure.mgmt.resource.resources.models import ResourceGroup, ResourceGroupFilter

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    filters = []
    if args.get('tag-name'):
        filters.append("tagname eq '{}'".format(args.get('tag-name')))
    if args.get('tag-value'):
        filters.append("tagvalue eq '{}'".format(args.get('tag-value')))

    filter_text = ' and '.join(filters) if len(filters) > 0 else None

    # TODO: top param doesn't work in SDK [bug #115521665]
    groups = rmc.resource_groups.list(filter=filter_text, top=args.get('top'))
    return list(groups)

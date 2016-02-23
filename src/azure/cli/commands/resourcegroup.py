from .._util import TableOutput
from ..commands import command, description, option
from .._profile import Profile

@command('resource group list')
@description('List resource groups')
# TODO: waiting on Python Azure SDK bug fixes
#@option('--tag-name -g <tagName>', _("the resource group's tag name"))
#@option('--tag-value -g <tagValue>', _("the resource group's tag value"))
#@option('--top -g <number>', _("Top N resource groups to retrieve"))
def list_groups(args, unexpected):
    from azure.mgmt.resource.resources import ResourceManagementClient, ResourceManagementClientConfiguration
    from azure.mgmt.resource.resources.models import ResourceGroup, ResourceGroupFilter

    rmc = ResourceManagementClient(ResourceManagementClientConfiguration(*Profile().get_credentials()))

    # TODO: waiting on Python Azure SDK bug fixes
    #group_filter = ResourceGroupFilter(args.get('tag-name'), args.get('tag-value'))
    #groups = rmc.resource_groups.list(filter=None, top=args.get('top'))
    groups = rmc.resource_groups.list()

    with TableOutput() as to:
        for grp in groups:
            assert isinstance(grp, ResourceGroup)
            to.cell('Name', grp.name)
            to.cell('Type', grp.properties)
            to.cell('Location', grp.location)
            to.cell('Tags', grp.tags)
            to.end_row()
        if not to.any_rows:
            print('No resource groups defined')


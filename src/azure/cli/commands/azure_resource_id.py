import re

from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.mgmt.resource.resources import ResourceManagementClient

regex = re.compile('/subscriptions/(?P<subscription>[^/]*)/resourceGroups/(?P<resourceGroup>[^/]*)'
                   '/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)'
                   '(/(?P<childType>[^/]*)/(?P<childName>[^/]*))?')

class AzureResourceId(object): #pylint: disable=too-many-instance-attributes,too-few-public-methods
    def __init__(self, name_or_id, resource_group=None, full_type=None, #pylint: disable=too-many-arguments
                 subscription_id=None, child_type=None, child_name=None):
        self.name = name_or_id
        self.resource_group = resource_group
        self.namespace = full_type.split('/')[0] if full_type else None
        self.type = full_type.split('/')[1] if full_type else None
        self.full_type = full_type
        self.child_type = child_type
        self.child_name = child_name
        self.subscription_id = subscription_id

        id_parts = regex.match(name_or_id)
        if id_parts:
            self.name = id_parts.group('name')
            self.resource_group = id_parts.group('resourceGroup')
            self.namespace = id_parts.group('namespace')
            self.type = id_parts.group('type')
            self.child_type = id_parts.group('childType')
            self.child_name = id_parts.group('childName')
            self.subscription_id = id_parts.group('subscription')
        elif not resource_group or not full_type or not subscription_id:
            raise ValueError('Provide either an ID for name_or_id or provide a name and values for '
                             'resource_group, full_type and subscription_id')

    def __str__(self):
        child_id = '/{type}/{name}'.format(type=self.child_type, name=self.child_name) \
            if self.child_name else ''
        return '/subscriptions/{subscription}/resourceGroups/{resource_group}/' \
            'providers/{namespace}/{type}/{name}{child_resource}' \
            .format(subscription=self.subscription_id, resource_group=self.resource_group,
                    namespace=self.namespace, type=self.type, name=self.name,
                    child_resource=child_id)

def resource_exists(r_id):
    odata_filter = "resourceGroup eq '{0}' and name eq '{1}'" \
        " and resourceType eq '{2}'".format(r_id.resource_group, r_id.name, r_id.full_type)
    client = get_mgmt_service_client(ResourceManagementClient).resources
    existing = len(list(client.list(filter=odata_filter))) == 1
    return existing

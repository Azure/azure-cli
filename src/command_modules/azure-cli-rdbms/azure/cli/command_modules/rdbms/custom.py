# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.arm import \
    (resource_id, is_valid_resource_id, parse_resource_id)


# need to replace source sever name with source server id, so customer server restore function
# The parameter list should be the same as that in factory to use the ParametersContext
# auguments and validators
def _server_restore(
        client,
        resource_group_name,
        server_name,
        parameters,
        **kwargs):
    """
    Create a new server by restoring from a server backup.
    """
    source_server = kwargs['source_server_id']

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            from azure.cli.core.commands.client_factory import get_subscription_id
            from azure.mgmt.rdbms.mysql.operations.servers_operations import ServersOperations
            provider = 'Microsoft.DBForMySQL' if isinstance(client, ServersOperations) else 'Microsoft.DBforPostgreSQL'
            source_server = resource_id(subscription=get_subscription_id(),
                                        resource_group=resource_group_name,
                                        namespace=provider,
                                        type='servers',
                                        name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))

    parameters.properties.source_server_id = source_server

    # Here is a workaround that we don't support cross-region restore currently,
    # so the location must be set as the same as source server (not the resource group)
    id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        parameters.location = source_server_object.location
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))

    return client.create_or_update(resource_group_name, server_name, parameters)


def _server_update_custom_func(instance,
                               capacity=None,
                               administrator_login_password=None,
                               ssl_enforcement=None,
                               tags=None):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path.replace('server', 'server_update_parameters'))
    ServerUpdateParameters = getattr(module, 'ServerUpdateParameters')

    if capacity is not None:
        instance.sku.capacity = capacity
    else:
        instance.sku = None

    params = ServerUpdateParameters(sku=instance.sku,
                                    storage_mb=None,
                                    administrator_login_password=administrator_login_password,
                                    version=None,
                                    ssl_enforcement=ssl_enforcement,
                                    tags=tags)

    return params


# define custom func for firewall rule update, because flatten make generic update not work
def _firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name,
                                 parameters):
    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        firewall_rule_name=firewall_rule_name,
        start_ip_address=parameters.start_ip_address,
        end_ip_address=parameters.end_ip_address)


def _firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


#        Custom funcs for server logs        #

def _download_log_files(
        client,
        resource_group_name,
        server_name,
        file_name):
    """
     Download log file(s) of a given server to current directory.

    :param resource_group_name: The name of the resource group that
    contains the resource. You can obtain this value from the Azure
    Resource Manager API or the portal.
    :type resource_group_name: str
    :param server_name: Name of the server.
    :type server_name: str
    :param file_name: Space separated list of log filenames on the server to download.
    :type filename_contains: str
    """
    from six.moves.urllib.request import urlretrieve  # pylint: disable=import-error

    # list all files
    files = client.list_by_server(resource_group_name, server_name)

    for f in files:
        if f.name in file_name:
            urlretrieve(f.url, f.name)


def _list_log_files_with_filter(client, resource_group_name, server_name, filename_contains=None,
                                file_last_written=None, max_file_size=None):
    """List all the log files of a given server.

    :param resource_group_name: The name of the resource group that
    contains the resource. You can obtain this value from the Azure
    Resource Manager API or the portal.
    :type resource_group_name: str
    :param server_name: The name of the server.
    :type server_name: str
    :param filename_contains: The pattern that file name should match.
    :type filename_contains: str
    :param file_last_written: Interger in hours to indicate file last modify time,
    default value is 72.
    :type file_last_written: int
    :param max_file_size: The file size limitation to filter files.
    :type max_file_size: int
    """
    import re
    from datetime import datetime, timedelta
    from dateutil.tz import tzutc

    # list all files
    all_files = client.list_by_server(resource_group_name, server_name)
    files = []

    if file_last_written is None:
        file_last_written = 72
    time_line = datetime.utcnow().replace(tzinfo=tzutc()) - timedelta(hours=file_last_written)

    for f in all_files:
        if f.last_modified_time < time_line:
            continue
        if filename_contains is not None and re.search(filename_contains, f.name) is None:
            continue
        if max_file_size is not None and f.size_in_kb > max_file_size:
            continue

        del f.created_time
        files.append(f)

    return files


#        Custom funcs for list servers        #
def _server_list_custom_func(
        client,
        resource_group_name=None):
    """
    List servers by resource group name or subscription
    """

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()

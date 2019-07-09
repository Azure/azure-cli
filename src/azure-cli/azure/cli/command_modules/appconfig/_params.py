# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (get_enum_type,
                                                get_location_type,
                                                tags_type,
                                                resource_group_name_type)
from azure.cli.core.commands.validators import \
    get_default_location_from_resource_group

from ._validators import (validate_appservice_name_or_id,
                          validate_connection_string, validate_datetime,
                          validate_export, validate_import,
                          validate_import_depth, validate_query_fields,
                          validate_separator)


def load_arguments(self, _):

    # PARAMETER REGISTRATION
    fields_arg_type = CLIArgumentType(
        nargs='+',
        help='Customize output fields.',
        validator=validate_query_fields,
        arg_type=get_enum_type(['key', 'value', 'label', 'content_type', 'etag', 'locked', 'last_modified'])
    )
    datatime_filter_arg_type = CLIArgumentType(
        validator=validate_datetime,
        help='Format: "YYYY-MM-DDThh:mm:ssZ". If no time zone specified, use UTC by default.'
    )
    top_arg_type = CLIArgumentType(
        options_list=['--top', '-t'],
        type=int,
        help='Maximum number of items to return. Default to 100.'
    )

    with self.argument_context('appconfig') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('name', options_list=['--name', '-n'], id_part='name', help='Name of the App Configuration. You can configure the default name using `az configure --defaults app_configuration_store=<name>`', configured_default='app_configuration_store')
        c.argument('connection_string', validator=validate_connection_string, configured_default='appconfig_connection_string',
                   help="Connections of access key and endpoint of App Configuration. Can be found using 'az appconfig credential list'. Users can preset it using `az configure --defaults appconfig_connection_string=<connection_string>` or environment variable with the name AZURE_APPCONFIG_CONNECTION_STRING.")
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.')
        c.argument('datetime', arg_type=datatime_filter_arg_type)
        c.argument('top', arg_type=top_arg_type)
        c.argument('all_', options_list=['--all'], action='store_true', help="List all items.")
        c.argument('fields', arg_type=fields_arg_type)

    with self.argument_context('appconfig create') as c:
        c.argument('location', options_list=['--location', '-l'], arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)

    with self.argument_context('appconfig update') as c:
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('appconfig credential regenerate') as c:
        c.argument('id_', options_list=['--id'], help='Id of the key to be regenerated. Can be found using az appconfig credential list command.')

    with self.argument_context('appconfig credential list') as c:
        c.argument('name', id_part=None)

    with self.argument_context('appconfig kv import') as c:
        c.argument('label', help="Imported KVs will be assigned with this label. If no label specified, will assign null label.")
        c.argument('prefix', help="This prefix will be appended to the front of imported keys.")
        c.argument('source', options_list=['--source', '-s'], choices=['file', 'appconfig', 'appservice'], validator=validate_import, help="The source of importing.")
        c.argument('yes', help="Do not prompt for preview.")

    with self.argument_context('appconfig kv import', arg_group='File') as c:
        c.argument('path', help='Local configuration file path. Required for file arguments.')
        c.argument('format_', options_list=['--format'], choices=['json', 'yaml', 'properties'], help='Imported file format. Required for file arguments.')
        c.argument('depth', validator=validate_import_depth, help="Depth for flatterning the json or yaml file to key-value paris. Flattern to the deepest level by default.")
        c.argument('separator', arg_type=get_enum_type(['.', ',', ';', '-', '_', '__', '/']), help="Delimiter for flatterning the json or yaml file to key-value pairs. Required for importing hierarchical structure. Not applicable for property files.")

    with self.argument_context('appconfig kv import', arg_group='AppConfig') as c:
        c.argument('src_name', help='The name of the source App Configuration.')
        c.argument('src_connection_string', validator=validate_connection_string, help="Connections of access key and endpoint of the source store. ")
        c.argument('src_key', help='If no key specified, import all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix. Similarly, *abc and *abc* are also supported.')
        c.argument('src_label', help="Only keys with this label in source AppConfig will be imported. If no label specified, import keys with null label by default.")

    with self.argument_context('appconfig kv import', arg_group='AppService') as c:
        c.argument('appservice_account', validator=validate_appservice_name_or_id, help='ARM ID for AppService OR the name of the AppService, assuming the it is in the same subscription and resource group as the App Configuration. Required for AppService arguments')

    with self.argument_context('appconfig kv export') as c:
        c.argument('label', help="Only keys with this label will be exported. If no label specified, export keys with null label by default.")
        c.argument('prefix', help="Prefix to be trimed from keys.")
        c.argument('key', help='If no key specified, return all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix. Similarly, *abc and *abc* are also supported.')
        c.argument('destination', options_list=['--destination', '-d'], choices=['file', 'appconfig', 'appservice'], validator=validate_export, help="The destination of exporting.")
        c.argument('yes', help="Do not prompt for preview.")

    with self.argument_context('appconfig kv export', arg_group='File') as c:
        c.argument('path', help='Local configuration file path. Required for file arguments.')
        c.argument('format_', options_list=['--format'], choices=['json', 'yaml', 'properties'], help='File format exporting to. Required for file arguments.')
        c.argument('depth', validator=validate_import_depth, help="Depth for flatterning the json or yaml file to key-value paris. Flattern to the deepest level by default.")
        c.argument('separator', validator=validate_separator, help="Delimiter for flatterning the json or yaml file to key-value pairs. Required for importing hierarchical structure. Not applicable for property files. Supported values: '.', ',', ';', '-', '_', '__', '/', ':', '' ")

    with self.argument_context('appconfig kv export', arg_group='AppConfig') as c:
        c.argument('dest_name', help='The name of the destination App Configuration.')
        c.argument('dest_connection_string', validator=validate_connection_string, help="Connections of access key and endpoint of the destination store. ")
        c.argument('dest_label', help="Exported KVs will be labeled with this destination label.")

    with self.argument_context('appconfig kv export', arg_group='AppService') as c:
        c.argument('appservice_account', validator=validate_appservice_name_or_id, help='ARM ID for AppService OR the name of the AppService, assuming the it is in the same subscription and resource group as the App Configuration. Required for AppService arguments')

    with self.argument_context('appconfig kv set') as c:
        c.argument('key', help='Key to be set.')
        c.argument('label', help="If no label specified, set the key with null label by default")
        c.argument('tags', arg_type=tags_type)
        c.argument('content_type', help='Content type of the keyvalue to be set.')
        c.argument('value', help='Value of the keyvalue to be set.')

    with self.argument_context('appconfig kv delete') as c:
        c.argument('key', help='Support star sign as filters, for instance * means all key and abc* means keys with abc as prefix. Similarly, *abc and *abc* are also supported.')
        c.argument('label', help="If no label specified, delete entry with null label. Support star sign as filters, for instance * means all label and abc* means labels with abc as prefix. Similarly, *abc and *abc* are also supported.")

    with self.argument_context('appconfig kv show') as c:
        c.argument('key', help='Key to be showed.')
        c.argument('label', help="If no label specified, show entry with null label. Does NOT support filters like other commands")

    with self.argument_context('appconfig kv list') as c:
        c.argument('name', id_part=None)
        c.argument('key', help='If no key specified, return all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix. Similarly, *abc and *abc* are also supported.')
        c.argument('label', help="If no label specified, list all labels. Support star sign as filters, for instance abc* means labels with abc as prefix. Similarly, *abc and *abc* are also supported.")

    with self.argument_context('appconfig kv lock') as c:
        c.argument('key', help='Key to be locked.')
        c.argument('label', help="If no label specified, lock entry with null label. Does NOT support filters like other commands")

    with self.argument_context('appconfig kv unlock') as c:
        c.argument('key', help='Key to be unlocked.')
        c.argument('label', help="If no label specified, unlock entry with null label. Does NOT support filters like other commands")

    with self.argument_context('appconfig revision list') as c:
        c.argument('name', id_part=None)
        c.argument('key', help='If no key specified, return all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix. Similarly, *abc and *abc* are also supported.')
        c.argument('label', help="If no label specified, list all labels. Support star sign as filters, for instance abc* means labels with abc as prefix. Similarly, *abc and *abc* are also supported.")

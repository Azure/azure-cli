# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_three_state_flag
)

from ._validators import (
    validate_params,
    validate_kafka_params
)
from ._resource_config import (
    RESOURCE,
    SOURCE_RESOURCES_PARAMS,
    TARGET_RESOURCES_PARAMS,
    AUTH_TYPE_PARAMS,
    SUPPORTED_AUTH_TYPE,
    SUPPORTED_CLIENT_TYPE,
)
from ._addon_factory import AddonFactory


def load_arguments(self, _):  # pylint: disable=too-many-statements

    def add_source_resource_block(context, source, enable_id=True, validate_source_id=False):
        source_args = SOURCE_RESOURCES_PARAMS.get(source)
        for resource, args in SOURCE_RESOURCES_PARAMS.items():
            if resource != source:
                for arg in args:
                    if arg not in source_args:
                        context.ignore(arg)

        required_args = []
        for arg, content in SOURCE_RESOURCES_PARAMS.get(source).items():
            context.argument(arg, options_list=content.get('options'), type=str,
                             help='{}. Required if \'--source-id\' is not specified.'.format(content.get('help')))
            required_args.append(content.get('options')[0])

        validator_kwargs = {'validator': validate_params} if validate_source_id else {}
        if not enable_id:
            context.argument('source_id', options_list=['--source-id'], type=str,
                             help="The resource id of a {source}. Required if {required_args} "
                             "are not specified.".format(source=source.value, required_args=str(required_args)),
                             **validator_kwargs)
        else:
            required_args.append('--connection')
            context.argument('indentifier', options_list=['--id'], type=str,
                             help="The resource id of the connection. {required_args} are required "
                                  "if '--id' is not specified.".format(required_args=str(required_args)))
            context.ignore('source_id')

    def add_auth_block(context, source, target):
        support_auth_types = SUPPORTED_AUTH_TYPE.get(source, {}).get(target, [])
        for auth_type in AUTH_TYPE_PARAMS:
            if auth_type in support_auth_types:
                for arg, params in AUTH_TYPE_PARAMS.get(auth_type).items():
                    context.argument(arg, options_list=params.get('options'), action=params.get('action'), nargs='*',
                                     help=params.get('help'), arg_group='AuthType')
            else:
                for arg in AUTH_TYPE_PARAMS.get(auth_type):
                    context.ignore(arg)

    def add_target_resource_block(context, target):
        target_args = TARGET_RESOURCES_PARAMS.get(target)
        for resource, args in TARGET_RESOURCES_PARAMS.items():
            if resource != target:
                for arg in args:
                    if arg not in target_args:
                        context.ignore(arg)

        required_args = []
        for arg, content in TARGET_RESOURCES_PARAMS.get(target).items():
            context.argument(arg, options_list=content.get('options'), type=str,
                             help='{}. Required if \'--target-id\' is not specified.'.format(content.get('help')))
            required_args.append(content.get('options')[0])

        context.argument('target_id', type=str,
                         help='The resource id of target service. Required if {required_args} '
                              'are not specified.'.format(required_args=str(required_args)))

    def add_connection_name_argument(context, source):
        context.argument('connection_name', options_list=['--connection'], type=str,
                         help='Name of the {} connection.'.format(source.value), validator=validate_params)

    def add_client_type_argument(context, source, target):
        client_types = SUPPORTED_CLIENT_TYPE.get(source).get(target, [])
        client_types = [item.value for item in client_types]
        context.argument('client_type', options_list=['--client-type'], arg_type=get_enum_type(client_types),
                         help='The client type used on the {}'.format(source.value))

    def add_target_type_argument(context, source):
        TARGET_TYPES = [elem.value for elem in SUPPORTED_AUTH_TYPE.get(source).keys()]
        context.argument('target_resource_type', options_list=['--target-type', '-t'],
                         arg_type=get_enum_type(TARGET_TYPES), help='The target resource type')

    def add_new_addon_argument(context, source, target):
        if AddonFactory.get(target, None):
            context.argument('new_addon', options_list=['--new'], arg_type=get_three_state_flag(), default=False,
                             help='Indicates whether to create a new {} when '
                                  'creating the {} connection'.format(target.value, source.value))
        else:
            context.ignore('new_addon')

    def add_secret_store_argument(context):
        context.argument('key_vault_id', options_list=['--kv-id'], help='The id of key vault to store secret value')

    def add_confluent_kafka_argument(context):
        context.argument('bootstrap_server', options_list=['--bootstrap-server'], help='Kafka bootstrap server url')
        context.argument('kafka_key', options_list=['--kafka-key'], help='Kafka API-Key (key)')
        context.argument('kafka_secret', options_list=['--kafka-secret'], help='Kafka API-Key (secret)')
        context.argument('schema_registry', options_list=['--schema-registry'], help='Schema registry url')
        context.argument('schema_key', options_list=['--schema-key'], help='Schema registry API-Key (key)')
        context.argument('schema_secret', options_list=['--schema-secret'], help='Schema registry API-Key (secret)')
        context.argument('connection_name', options_list=['--connection'],
                         help='Name of the connection', validator=validate_kafka_params)

    for source in SOURCE_RESOURCES_PARAMS:

        with self.argument_context('{} connection list'.format(source.value)) as c:
            add_source_resource_block(c, source, enable_id=False, validate_source_id=True)

        with self.argument_context('{} connection show'.format(source.value)) as c:
            add_source_resource_block(c, source)
            add_connection_name_argument(c, source)

        with self.argument_context('{} connection delete'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)

        with self.argument_context('{} connection list-configuration'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)
        with self.argument_context('{} connection validate'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)

        with self.argument_context('{} connection list-support-types'.format(source.value)) as c:
            add_target_type_argument(c, source)

        with self.argument_context('{} connection wait'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)

        for target in TARGET_RESOURCES_PARAMS:
            with self.argument_context('{} connection create {}'.format(source.value, target.value)) as c:
                add_client_type_argument(c, source, target)
                add_connection_name_argument(c, source)
                add_source_resource_block(c, source, enable_id=False)
                add_target_resource_block(c, target)
                add_auth_block(c, source, target)
                add_new_addon_argument(c, source, target)
                add_secret_store_argument(c)
            with self.argument_context('{} connection update {}'.format(source.value, target.value)) as c:
                add_client_type_argument(c, source, target)
                add_connection_name_argument(c, source)
                add_source_resource_block(c, source)
                add_auth_block(c, source, target)
                add_secret_store_argument(c)

        # special target resource: independent implementation
        target = RESOURCE.ConfluentKafka
        with self.argument_context('{} connection create {}'.format(source.value, target.value)) as c:
            add_client_type_argument(c, source, target)
            add_source_resource_block(c, source, enable_id=False)
            add_confluent_kafka_argument(c)
            add_secret_store_argument(c)
        with self.argument_context('{} connection update {}'.format(source.value, target.value)) as c:
            add_client_type_argument(c, source, target)
            add_source_resource_block(c, source, enable_id=False)
            add_confluent_kafka_argument(c)
            add_secret_store_argument(c)

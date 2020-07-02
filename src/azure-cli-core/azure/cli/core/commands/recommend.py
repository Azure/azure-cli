
import argparse
from collections import OrderedDict
import copy
import json
import re
from six import string_types

from azure.cli.core import AzCommandsLoader, EXCLUDED_PARAMS
from azure.cli.core.commands import LongRunningOperation, _is_poller, cached_get, cached_put
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import IterateValue
from azure.cli.core.util import (
    shell_safe_json_parse, augment_no_wait_handler_args, get_command_type_kwarg, find_child_item)
from azure.cli.core.profiles import ResourceType, get_sdk

from knack.arguments import CLICommandArgument, ignore_type
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.log import get_logger
from knack.util import todict, CLIError
from knack import events

logger = get_logger(__name__)


def register_global_query_recommend(cli_ctx):
    def add_query_recommend_parameter(_, **kwargs):
        arg_group = kwargs.get('arg_group')
        arg_group.add_argument('--query-recommend', dest='_query_recommend',
            help="Recommend JMESPath string for you", action='store_true')

    def handle_recommend_parameter(cli, **kwargs):
        args = kwargs['args']
        query_recommend = args._query_recommend
        if query_recommend:
            logger.warning("Analyze output")

            def analyze_output(cli_ctx, **kwargs):
                kwargs['event_data']['result'] = parse_output(kwargs['event_data']['result'])
                cli_ctx.unregister_event(events.EVENT_INVOKER_FILTER_RESULT, analyze_output)

            cli_ctx.register_event(events.EVENT_INVOKER_FILTER_RESULT, analyze_output)
            cli_ctx.invocation.data['query_active'] = True

    cli_ctx.register_event(
        events.EVENT_PARSER_GLOBAL_CREATE, add_query_recommend_parameter)
    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_PARSE_ARGS, handle_recommend_parameter)


def parse_dict(data):
    all_keys = list(data.keys())
    help_str = 'You can use --query \"{}\" to query {} value. Available values are:{}'.format(
        all_keys[0], all_keys[0], all_keys
    )
    return help_str


def parse_list(data):
    help_str = []
    for item in data:
        help_str.append(parse_dict(item))
    return '\n'.join(help_str)


def parse_output(data):
    help_str = "Output format is not supported"
    if isinstance(data, dict):
        help_str = parse_dict(data)
    elif isinstance(data, list):
        help_str = parse_list(data)
    else:
        logger.warning("Ootput format is not supported")
    return help_str

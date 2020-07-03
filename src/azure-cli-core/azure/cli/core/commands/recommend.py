
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
    '''Register --query-recommend argument, and register handler
    '''
    def add_query_recommend_parameter(_, **kwargs):
        arg_group = kwargs.get('arg_group')
        arg_group.add_argument('--query-recommend', dest='_query_recommend',
            help="Recommend JMESPath string for you", action='store_true')

    def handle_recommend_parameter(cli, **kwargs):
        args = kwargs['args']
        query_recommend = args._query_recommend
        if query_recommend:
            def analyze_output(cli_ctx, **kwargs):
                tree_builder = TreeBuilder()
                tree_builder.build(kwargs['event_data']['result'])
                kwargs['event_data']['result'] = tree_builder.generate_recommend()
                cli_ctx.unregister_event(events.EVENT_INVOKER_FILTER_RESULT, analyze_output)

            cli_ctx.register_event(events.EVENT_INVOKER_FILTER_RESULT, analyze_output)
            cli_ctx.invocation.data['query_active'] = True

    cli_ctx.register_event(
        events.EVENT_PARSER_GLOBAL_CREATE, add_query_recommend_parameter)
    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_PARSE_ARGS, handle_recommend_parameter)


class TreeNode:
    def __init__(self, name):
        self._name = name
        self._parent = None
        self._keys = None
        self._child = None
        self._from_list = False

    def get_select_string(self, select_item=None):
        if self._parent:
            pass
        else:
            if select_item is None:
                return str(self._keys[0])
            else:
                raise Exception("Unfinished function!")


class TreeBuilder:
    def __init__(self):
        self._root = TreeNode('root')
        self._all_nodes = {}

    def build(self, data):
        '''Build a query tree with a given json file
        :param str data: json format data
        '''
        if isinstance(data, list):
            if len(data) > 0:
                self._root = self._parse_dict('root', data[0], from_list=True)
        elif isinstance(data, dict):
            self._root = self._parse_dict('root', data)

    def generate_recommend(self):
        for node in self._all_nodes.values():
            print(node.get_select_string())

    def _parse_dict(self, name, data, from_list=False):
        node = TreeNode(name)
        node._keys = list(data.keys())
        self._all_nodes[name] = node


def parse_dict(data):
    all_keys = list(data.keys())
    help_str = 'You can use --query "{}" to query {} value. Available values are:{}'.format(
        all_keys[0], all_keys[0], all_keys
    )
    return help_str


def parse_output(data):
    '''Parse entry. Generate recommendation from json
    :param str data: Command output in json format
    '''
    help_str = "Output format is not supported"
    if isinstance(data, dict):
        help_str = parse_dict(data)
    elif isinstance(data, list):
        help_str = parse_list(data)
    else:
        logger.warning("Output format is not supported")
    return help_str


def handle_escape_char(raw_str):
    def escape_char(raw_str, ch):
        return raw_str.replace(ch, '\\{}'.format(ch))
    # handle quotes
    ret = escape_char(raw_str, '"')
    # handle brackets
    ret = escape_char(ret, '[')
    ret = escape_char(ret, ']')
    return ret

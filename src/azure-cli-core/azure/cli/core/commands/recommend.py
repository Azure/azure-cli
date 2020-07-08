
import argparse
from collections import OrderedDict
import copy
import json
import re
import random
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
        self._data = None
        self._keys = None
        self._child = []  # list of child node
        self._from_list = False
        self._list_length = None  # valid only when from_list is true

    def _get_trace(self):
        traces = []
        if self._parent:  # only calculate non-root node
            traces.extend(self._parent._get_trace())
            traces.append(self._name)
        return traces

    def _get_trace_str(self, number=None, filter_rules=None):
        '''The correct JMESPath to get to current node'''
        trace_str = ""
        if self._parent:
            trace_str += self._parent._get_trace_str()
            trace_str += "." + self._name
        if self._from_list:
            if number:
                trace_str += "[:{}]".format(number)
            elif filter_rules:
                trace_str += "[?{}]".format(self.filter_with_condiction())
            else:
                trace_str += "[]"
        return trace_str

    def get_select_string(self, select_item=None):
        ret = []
        help_str = "{}.".format(self._get_trace_str())

        if select_item is None:
            for key in self._keys:
                ret.append(help_str + key)
        else:
            raise Exception("Unfinished function!")
        return ret

    def select_specific_number_string(self, number=5):
        ret = []
        if not self._from_list:
            return ret
        number = min(self._list_length, number)
        number = random.choice(range(1, number + 1))
        help_str = self._get_trace_str(number)
        ret.append(help_str)
        return ret

    def filter_with_condiction(self):
        help_str = ""
        if not self._from_list:
            return help_str
        for key in self._keys:
            if not (isinstance(self._data[key], list) or
                    isinstance(self._data[key], dict)):
                help_str = "{}=='{}'".format(key, self._data[key])
                break
        return help_str

    def get_function_recommend(self):
        ret = []
        if not self._from_list:
            return None
        # currently contains and length
        query_str = "length({})".format(self._get_trace_str())
        ret.append(query_str)
        return ret


class TreeBuilder:
    '''Parse entry. Generate parse tree from json. And
    then give recommendation
    '''
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
                self._root._list_length = len(data)
        elif isinstance(data, dict):
            self._root = self._parse_dict('root', data)

    def generate_recommend(self):
        def printlist(my_list):
            if isinstance(my_list, list):
                for item in my_list:
                    print(item)
            else:
                print(my_list)

        for node in self._all_nodes.values():
            print("Select some field:")
            printlist(node.get_select_string())
            print("Others:")
            if node._from_list:
                printlist(node.select_specific_number_string())
                printlist(node._get_trace_str(filter_rules=node.filter_with_condiction))
                printlist(node.get_function_recommend())

    def _parse_dict(self, name, data, from_list=False):
        node = TreeNode(name)
        node._keys = list(data.keys())
        node._data = data
        node._from_list = from_list
        for key in data.keys():
            child_node = None
            if isinstance(data[key], list):
                if len(data[key]) > 0:
                    child_node = self._parse_dict(key, data[key][0], from_list=True)
                    child_node._list_length = len(data[key])
            elif isinstance(data[key], dict) and not len(data[key]) == 0:
                child_node = self._parse_dict(key, data[key])
            if child_node:
                node._child.append(child_node)
                child_node._parent = node

        self._all_nodes[name] = node
        return node


def handle_escape_char(raw_str):
    def escape_char(raw_str, ch):
        return raw_str.replace(ch, '\\{}'.format(ch))
    # handle quotes
    ret = escape_char(raw_str, '"')
    # handle brackets
    ret = escape_char(ret, '[')
    ret = escape_char(ret, ']')
    return ret

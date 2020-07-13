
import argparse
from collections import OrderedDict
import copy
import json
import re
import random
from six import string_types
import jellyfish

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
                               help="Recommend JMESPath string for you", nargs="*")

    def handle_recommend_parameter(cli, **kwargs):
        args = kwargs['args']
        if args._query_recommend is not None:
            def analyze_output(cli_ctx, **kwargs):
                tree_builder = TreeBuilder()
                tree_builder.build(kwargs['event_data']['result'])
                kwargs['event_data']['result'] = tree_builder.generate_recommend(
                    args._query_recommend)
                cli_ctx.unregister_event(
                    events.EVENT_INVOKER_FILTER_RESULT, analyze_output)

            cli_ctx.register_event(
                events.EVENT_INVOKER_FILTER_RESULT, analyze_output)
            cli_ctx.invocation.data['query_active'] = True

    cli_ctx.register_event(
        events.EVENT_PARSER_GLOBAL_CREATE, add_query_recommend_parameter)
    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_PARSE_ARGS, handle_recommend_parameter)


class Recommendation:
    def __init__(self, query_str, help_str="", group_name="default"):
        self._query_str = query_str
        self._help_str = help_str
        self._group = group_name

    def __str__(self):
        return "{}\t{}".format(self._query_str, self._help_str)


class TreeNode:
    def __init__(self, name):
        self._name = name
        self._parent = None
        self._data = None
        self._keys = None
        self._child = []  # list of child node
        self._from_list = False
        self._list_length = None  # valid only when from_list is true
        self._similarity_threshold = 0.75

    def _get_trace(self):
        traces = []
        if self._parent:  # only calculate non-root node
            traces.extend(self._parent._get_trace())
            traces.append(self._name)
        return traces

    def _get_match_items(self, select_items, similarity_threshold=0, keys=None):
        '''Fuzzy match select items with self._keys
        '''
        if keys is None:
            keys = self._keys
        if len(select_items) == 0:
            return keys
        simi_dict = {}
        for item in select_items:
            for key in keys:
                similarity = jellyfish.jaro_winkler_similarity(item, key)
                simi_dict[key] = max(simi_dict.get(key, 0), similarity)
        sorted_list = sorted(simi_dict, key=simi_dict.get)
        sorted_list = list(filter(
            lambda k: simi_dict[k] > similarity_threshold, sorted_list))
        return sorted_list[::-1]

    def _get_trace_str(self, number=None, filter_rules=False, select_items=None):
        '''The correct JMESPath to get to current node'''
        trace_str = ""
        if self._parent:
            trace_str += self._parent._get_trace_str()
            trace_str += "." + self._name
        if self._from_list:
            if number:
                trace_str += "[:{}]".format(number)
            elif filter_rules:
                # do nothing
                pass
            else:
                trace_str += "[]"
        return trace_str

    def get_select_string(self, select_items):
        ret = []
        trace_str = ""
        if self._parent:
            trace_str = "{}.".format(self._get_trace_str())

        select_list = set()
        if len(select_items) == 0:
            for key in self._keys:
                select_list.add(key)
        else:
            select_list.update(self._get_match_items(
                select_items, self._similarity_threshold))
        for item in select_list:
            ret.append(Recommendation(trace_str + item,
                                      help_str="Get all {} from output".format(
                                          item),
                                      group_name="select"))
        return ret

    def select_specific_number_string(self, number=5):
        ret = []
        if not self._from_list:
            return ret
        number = min(self._list_length, number)
        number = random.choice(range(1, number + 1))
        query_str = self._get_trace_str(number)
        ret.append(Recommendation(
            query_str, help_str="Get first {} elements".format(number), group_name="limit_number"))
        return ret

    def get_condition_recommend(self, select_items):
        ret = []
        if not self._from_list:
            return ret

        trace_str = self._get_trace_str(filter_rules=True)
        viable_keys = []
        for key in self._keys:
            if not (isinstance(self._data[key], list) or
                    isinstance(self._data[key], dict)):
                viable_keys.append(key)
        match_items = self._get_match_items(select_items, keys=viable_keys)
        if match_items is not None:
            query_str = "{}=='{}'".format(
                match_items[0], self._data[match_items[0]])
            ret.append(Recommendation("{}[?{}]".format(trace_str, query_str),
                                      help_str="Display results only when {} equals to {}".format(
                                          match_items[0], self._data[match_items[0]]),
                                      group_name="condition"))
            for item in match_items[1:2]:
                query_str += "|| {}=='{}'".format(item, self._data[item])
                ret.append(Recommendation("{}[?{}]".format(trace_str, query_str),
                                          help_str="Display results only when satisfy one of the condition",
                                          group_name="condition"))
        return ret

    def get_function_recommend(self):
        ret = []
        if not self._from_list:
            return None
        # currently contains and length
        query_str = "length({})".format(self._get_trace_str())
        ret.append(Recommendation(
            query_str, help_str="Get the number of the results", group_name="function"))
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

    def generate_recommend(self, keywords_list):
        def printlist(my_list, group):
            if isinstance(my_list, list):
                for item in my_list:
                    if item._group == group:
                        print(item)
            else:
                print(my_list)

        recommendations = []
        for node in self._all_nodes.values():
            recommendations.extend(node.get_select_string(keywords_list))
            if node._from_list:
                recommendations.extend(node.select_specific_number_string())
                recommendations.extend(
                    node.get_condition_recommend(keywords_list))
                recommendations.extend(node.get_function_recommend())
        recommendations.sort(key=lambda x: x._group)
        groups = ["default", "select", "condition", "function", "limit_number"]
        for group in groups:
            print("Group {}:".format(group))
            printlist(recommendations, group)
            print("")

    def _parse_dict(self, name, data, from_list=False):
        node = TreeNode(name)
        node._keys = list(data.keys())
        node._data = data
        node._from_list = from_list
        for key in data.keys():
            child_node = None
            if isinstance(data[key], list):
                if len(data[key]) > 0 and isinstance(data[key][0], dict):
                    child_node = self._parse_dict(
                        key, data[key][0], from_list=True)
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

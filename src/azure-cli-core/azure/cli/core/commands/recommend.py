
import argparse
from collections import OrderedDict
import copy
import json
import re
import random
from six import string_types

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
            cli_ctx.invocation.data['output'] = 'table'

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
    def __init__(self, query_str, help_str="", group_name="default", max_length=40):
        self._query_str = query_str
        self._help_str = help_str
        self._group = group_name
        self._max_length = max_length

    def _asdict(self):
        query_str = self._query_str
        if len(query_str) > self._max_length:
            query_str = query_str[:self._max_length] + '...'
        help_str = self._help_str
        if len(help_str) > 2 * self._max_length:
            help_str = help_str[: 2 * self._max_length] + '...'
        return {"query string": query_str, "help": help_str}

    def __str__(self):
        return "{}\t{}".format(self._query_str, self._help_str)


class TreeNode:
    def __init__(self, name):
        self._name = name
        self._parent = None
        self._data = None
        self._keys = None
        self._list_keys = set()  # child node which is list
        self._child = []  # list of child node
        self._from_list = False
        self._list_length = 5  # valid only when from_list is true

    def _get_data(self, key):
        '''Return all key values with given key'''
        values = []
        if isinstance(self._data, list):
            for item in self._data:
                if item.get(key, None) is not None:
                    if isinstance(item[key], list):
                        values.extend(item[key])
                        self._list_keys.add(key)
                    else:
                        values.append(item[key])
        else:
            values.append(self._data[key])
        return values

    def get_one_value(self, key):
        '''Return only one value'''
        values = self._get_data(key)
        if len(values) > 0:
            return values[0]
        else:
            return None

    def is_list(self, key):
        '''Determine whether the key refer to a list'''
        return key in self._list_keys

    def _get_trace(self):
        '''Return the trace from root node to current node'''
        traces = []
        if self._parent:  # only calculate non-root node
            traces.extend(self._parent._get_trace())
            traces.append(self._name)
        return traces

    def _get_match_items(self, select_items, keys=None):
        '''
        Fuzzy match select items with self._keys

        :param select_items: User input which they are intrested in
        :param keys: if None, select from all keys in dict
        '''
        exclude_keys = ['id', 'subscriptions']
        if keys is None:
            keys = self._keys
        match_list = []
        for key in keys:
            if key in exclude_keys:
                continue
            if select_items:
                for item in select_items:
                    if item in key:
                        match_list.append(item)
            else:
                match_list.append(key)
        return match_list

    def _get_trace_str(self, number=None, filter_rules=False):
        '''The correct JMESPath to get to current node'''
        trace_str = ""
        if self._parent:
            trace_str += self._parent._get_trace_str()
            prefix = "" if trace_str == "" else "."
            trace_str += prefix + self._name
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
        if self._parent or self._from_list:
            trace_str = "{}.".format(self._get_trace_str())

        select_list = self._get_match_items(select_items)
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
            if not (isinstance(self.get_one_value(key), list) or
                    isinstance(self.get_one_value(key), dict)):
                viable_keys.append(key)
        match_items = self._get_match_items(select_items, keys=viable_keys)
        if match_items is not None and len(match_items) > 0:
            item_key = match_items[0]
            item_value = self.get_one_value(item_key)
            query_str = "{}=='{}'".format(
                match_items[0], self.get_one_value(match_items[0]))
            ret.append(Recommendation("{}[?{}]".format(trace_str, query_str),
                                      help_str="Display results only when {} equals to {}".format(
                                          match_items[0], self.get_one_value(match_items[0])),
                                      group_name="condition"))
            for item in match_items[1:2]:
                query_str += " || {}=='{}'".format(item,
                                                   self.get_one_value(item))
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
                self._root = self._do_parse('root', data, from_list=True)
                self._root._list_length = len(data)
        elif isinstance(data, dict):
            self._root = self._do_parse('root', [data])

    def generate_recommend(self, keywords_list):
        recommendations = []
        for node in self._all_nodes.values():
            recommendations.extend(node.get_select_string(keywords_list))
            if node._from_list:
                recommendations.extend(node.select_specific_number_string())
                recommendations.extend(
                    node.get_condition_recommend(keywords_list))
                recommendations.extend(node.get_function_recommend())
        recommendations.sort(key=lambda x: x._group)
        return todict(recommendations)

    def _get_from_list(self, data):
        '''Try to get not None item from input list

        :param list data:
            input list

        :return:
            An item from in this list. Return None if all items are None
        '''
        ret = None
        for item in data:
            if hasattr(item, '__len__'):
                if len(item) > 0:
                    ret = item
                    break
            elif item is not None:
                ret = item
                break
        return ret

    def _do_parse(self, name, data, from_list=False):
        '''do parse for a single node

        :param str name:
            name of the node
        :param list data:
            all data in the json with same depth and same name
        :param boolean from_list:
            a list node or a dict node
        '''
        node = TreeNode(name)
        node._keys = list(data[0].keys())
        node._data = data
        node._from_list = from_list
        for key in data[0].keys():
            child_node = None
            child_node_data = node._get_data(key)
            child_item = self._get_from_list(child_node_data)
            if child_item is None:
                node._keys.remove(key)  # remove key which has only null value
                continue
            if node.is_list(key):
                if isinstance(child_item, dict):
                    child_node = self._do_parse(
                        key, child_node_data, from_list=True)
            elif isinstance(child_item, dict):
                child_node = self._do_parse(key, child_node_data)
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

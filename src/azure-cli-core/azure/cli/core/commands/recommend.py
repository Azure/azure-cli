import random

from knack.log import get_logger
from knack.util import todict
from knack import events
from azure.cli.core.commands.events import EVENT_INVOKER_PRE_LOAD_ARGUMENTS

logger = get_logger(__name__)


def register_global_query_recommend_argument(cli_ctx):
    '''Register --query-recommend argument, and register handler
    '''
    # origin method to register a global argument
    # def add_query_recommend_parameter(_, **kwargs):
    #     arg_group = kwargs.get('arg_group')
    #     arg_group.add_argument('--query-recommend', dest='_query_recommend',
    #                            help="Recommend JMESPath string for you", nargs="*")

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

    def register_query_recommend(cli, **kwargs):
        from knack.experimental import ExperimentalItem
        commands_loader = kwargs.get('commands_loader')
        cmd_tbl = commands_loader.command_table
        experimental_info = ExperimentalItem(cli.local_context.cli_ctx,
                                             object_type='parameter', target='_query_recommend')
        default_kwargs = {
            'help': 'Recommend JMESPath string for you. You can copy one of the query '
                    'and paste it after --query parameter within double quotation marks'
                    'to see the results. You can add one or more positional keywords so'
                    'that we can give suggestions based on these key words.',
            'arg_group': 'Global',
            'is_experimental': True,
            'nargs': '*',
            'experimental_info': experimental_info
        }
        for _, cmd in cmd_tbl.items():
            cmd.add_argument('_query_recommend', *
                             ['--query-recommend'], **default_kwargs)

    cli_ctx.register_event(
        EVENT_INVOKER_PRE_LOAD_ARGUMENTS, register_query_recommend
    )
    # cli_ctx.register_event(
    #     events.EVENT_PARSER_GLOBAL_CREATE, add_query_recommend_parameter)
    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_PARSE_ARGS, handle_recommend_parameter)


class Recommendation:
    def __init__(self, query_str, help_str="", group_name="default", max_length=80):
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
            help_str = help_str[: 1 * self._max_length] + '...'
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

    def update_node_data(self, data, from_list):
        self._keys = list(data[0].keys())
        self._data = data
        self._from_list = from_list
        for item in self._data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, list):
                        self._list_keys.add(key)

    def get_values(self, key):
        '''Get all values with given key'''
        values = []
        if isinstance(self._data, list):
            for item in self._data:
                if item.get(key, None) is not None:
                    if isinstance(item[key], list):
                        values.extend(item[key])
                    else:
                        values.append(item[key])
        else:
            values.append(self._data[key])
        return values

    def from_list(self):
        return self._from_list

    def get_one_value(self, key):
        '''Return only one value, return None only if all values are None'''
        values = self.get_values(key)
        for item in values:
            if item is not None:
                return item
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
        suggest_keys = ['name', 'resourceGroup', 'location']
        # we use suggest keys if keys are not provided
        if keys is None:
            keys = [x for x in suggest_keys if x in self._keys]
            if not keys:
                keys.extend(self._keys)
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

    def _get_trace_str(self, no_brackets=False):
        '''The correct JMESPath to get to current node'''
        trace_str = ""
        if self._parent:
            trace_str += self._parent._get_trace_str()
            prefix = "" if trace_str == "" else "."
            trace_str += prefix + self._name
        if self._from_list and not no_brackets:
            trace_str += "[]"
        return trace_str

    def get_select_string(self, select_items):
        ret = []
        trace_str = ""
        if self._parent or self._from_list:
            trace_str = "{}.".format(self._get_trace_str())

        select_list = self._get_match_items(select_items)
        for item in select_list[:2]:  # limit the number of output
            ret.append(Recommendation(trace_str + item,
                                      help_str="Get all {} from output".format(
                                          item),
                                      group_name="select"))
        return ret

    def select_specific_number_string(self, keywords_list, number=5):
        ret = []
        if not self._from_list:
            return ret
        number = min(self._list_length, number)
        number = random.choice(range(1, number + 1))
        match_items = self._get_match_items(keywords_list)
        trace_str = self._get_trace_str(no_brackets=True)
        query_str = '{}[:{}]'.format(trace_str, number)
        if match_items:
            query_str = '{}.{}'.format(query_str, match_items[0])
        ret.append(Recommendation(
            query_str, help_str="Get first {} elements".format(number), group_name="limit_number"))
        return ret

    def get_condition_recommend(self, select_items):
        ret = []
        if not self._from_list:
            return ret

        trace_str = self._get_trace_str(no_brackets=True)
        viable_keys = []
        for key in self._keys:
            if not (isinstance(self.get_one_value(key), list) or
                    isinstance(self.get_one_value(key), dict)):
                viable_keys.append(key)
        match_items = self._get_match_items(select_items, keys=viable_keys)
        if match_items:
            item_key = match_items[0]
            item_value = self.get_one_value(item_key)
            if 'name' in self._keys:
                field_suffix = '.name'
                field_help = 'name of'
            elif len(match_items) >= 2:
                field_suffix = '.{}'.format(match_items[1])
                field_help = '{} of'.format(match_items[1])
            else:
                field_suffix = ''
                field_help = ''
            query_str = "{}=='{}'".format(item_key, item_value)
            ret.append(Recommendation("{}[?{}]{}".format(trace_str, query_str, field_suffix),
                                      help_str="Display {} resources only when {} equals to {}".format(
                                          field_help, item_key, item_value),
                                      group_name="condition"))
            ret.append(Recommendation("{0}[?contains(@.{1},'something')==`true`].{1}".format(trace_str, item_key),
                                      help_str="Display all {} field that contains given string".format(
                                          item_key),
                                      group_name="condition"))
            for item in match_items[1:2]:
                query_str += " || {}=='{}'".format(item,
                                                   self.get_one_value(item))
                ret.append(Recommendation("{}[?{}]{}".format(trace_str, query_str, field_suffix),
                                          help_str="Display {} resources only when satisfy one of the condition".format(
                                              field_help),
                                          group_name="condition"))
        return ret

    def get_function_recommend(self, select_items):
        ret = []
        if not self._from_list:
            return None
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
            if data:
                self._root = self._do_parse('root', data, from_list=True)
                self._root._list_length = len(data)
        elif isinstance(data, dict):
            self._root = self._do_parse('root', [data])

    def generate_recommend(self, keywords_list):
        recommendations = []
        # only perform select on root node
        recommendations.extend(self._root.get_select_string(keywords_list))
        if self._root.from_list():
            recommendations.extend(
                self._root.select_specific_number_string(keywords_list))
            recommendations.extend(
                self._root.get_condition_recommend(keywords_list))
            recommendations.extend(
                self._root.get_function_recommend(keywords_list))
        recommendations.sort(key=lambda x: x._group)
        return todict(recommendations)

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
        node.update_node_data(data, from_list)
        for key in data[0].keys():
            child_node = None
            child_node_data = node.get_values(key)
            child_item = node.get_one_value(key)
            if child_item is None:
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

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import todict
from knack import events
from knack.util import CLIError
from azure.cli.core.commands.events import EVENT_INVOKER_PRE_LOAD_ARGUMENTS

logger = get_logger(__name__)


def register_global_query_examples_argument(cli_ctx):
    """Register --query-examples argument, and register handler."""

    def handle_example_parameter(cli, **kwargs):  # pylint: disable=unused-argument
        args = kwargs['args']
        # `query_examples` has been registered and `--query-examples` appers in the command args
        if hasattr(args, '_query_examples') and args._query_examples is not None:  # pylint: disable=protected-access
            if cli_ctx.invocation.data['query_active']:
                raise CLIError('You should not use --query and --query-examples together.')
            # change the default output format to table
            if cli_ctx.invocation.data['output'] == 'json':
                cli_ctx.invocation.data['output'] = 'table'

            def analyze_output(cli_ctx, **kwargs):
                tree_builder = QueryTreeBuilder(cli.config)
                tree_builder.build(kwargs['event_data']['result'])
                # replace the result with query examples
                kwargs['event_data']['result'] = tree_builder.generate_examples(
                    args._query_examples, cli_ctx.invocation.data['output'])  # pylint: disable=protected-access
                cli_ctx.unregister_event(
                    events.EVENT_INVOKER_FILTER_RESULT, analyze_output)

            cli_ctx.register_event(
                events.EVENT_INVOKER_FILTER_RESULT, analyze_output)
            cli_ctx.invocation.data['query_active'] = True

    def register_query_examples(cli, **kwargs):
        from knack.experimental import ExperimentalItem
        experimental_info = ExperimentalItem(cli.local_context.cli_ctx,
                                             object_type='parameter', target='_query_examples')
        default_kwargs = {
            'help': 'Recommend JMESPath string for you. You can copy one of the query '
                    'and paste it after --query parameter within double quotation marks '
                    'to see the results. You can add one or more positional keywords so '
                    'that we can give suggestions based on these key words.',
            'arg_group': 'Global',
            'is_experimental': True,
            'nargs': '*',
            'experimental_info': experimental_info
        }

        allow_list = cli.config.get('query', 'allow_list', "list,show").split(',')
        allow_list = [s.strip() for s in allow_list if s.strip()]  # remove empty string
        # when allow_list="", do nothing
        if not allow_list:
            return

        commands_loader = kwargs.get('commands_loader')
        cmd_tbl = commands_loader.command_table
        for cmd_name, cmd in cmd_tbl.items():
            if any(cmd_name.endswith(suffix) for suffix in allow_list):
                cmd.add_argument('_query_examples', *
                                 ['--query-examples'], **default_kwargs)

    cli_ctx.register_event(
        EVENT_INVOKER_PRE_LOAD_ARGUMENTS, register_query_examples
    )
    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_PARSE_ARGS, handle_example_parameter)


class QueryExample:
    def __init__(self, query_str, help_str="", max_length=None):
        self._query_str = query_str
        self._help_str = help_str
        self._examples_len = max_length
        self._help_len = max_length
        self.escape_char()

    def set_max_length(self, examples_len, help_len):
        self._examples_len = examples_len
        self._help_len = help_len

    def escape_char(self):
        """Escape special characters in JMESPath"""
        # escape backtick
        self._query_str = self._query_str.replace('`', '\\`')

    def _asdict(self):
        query_str = self._query_str
        if self._examples_len and len(query_str) > self._examples_len:
            query_str = query_str[:self._examples_len] + '...'
        help_str = self._help_str
        if self._help_len and len(help_str) > self._help_len:
            help_str = help_str[:self._help_len] + '...'
        return {"query string": query_str, "help": help_str}

    def __str__(self):
        return "{}\t{}".format(self._query_str, self._help_str)


class QueryTreeNode:
    def __init__(self, name, parent, is_array):
        self.is_dummy = False
        self._name = name
        self._parent = parent
        self._is_array = is_array  # inside an JSON array
        self._data = None
        self._child = []  # list of child node

    def add_child(self, child_node):
        if child_node:
            self._child.append(child_node)

    def update_node_data(self, data):
        self._data = data

    def _get_one_data(self):
        """Try to get not None data."""
        if not self._data:
            return None
        for value in self._data:
            if value:
                return value
        return None

    def get_help_str(self, help_type):
        """Return help string based on help_type."""
        help_table = {
            'contains': 'Show the {} field that contains given string.'.format(self._name),
            'filter': 'Show the resources that satisfy the condition.',
            'select': 'Show the value of {} field.'.format(self._name),
        }
        return help_table.get(help_type, '')

    def get_trace_to_array(self, inner_trace):
        """
        Get trace to the nearest array. Return None if no array found. This function return two values,
        inner trace and outer trace. The inner trace is the trace inside the brackets and the outer
        trace is the trace outside the brackets.
        """
        if self._is_array:
            if self._parent:
                if self._parent.is_dummy and not self._parent._is_array:  # pylint: disable=protected-access
                    outer_trace = self._name
                else:
                    outer_trace = '{}.{}'.format(self._parent.get_trace_to_root(), self._name)
            else:
                outer_trace = self._name
            return outer_trace, inner_trace

        # under a dict
        if self._parent:
            if inner_trace:
                current_trace = self._name + '.' + inner_trace
            else:
                current_trace = self._name
            return self._parent.get_trace_to_array(current_trace)

        # no array found until root node
        return None, None

    def get_trace_to_root(self):
        """Return the trace string(aka, select string in JMESPath) to the root node."""
        if self._parent:
            if self._parent.is_dummy and not self._parent._is_array:  # pylint: disable=protected-access
                trace_str = self._name
            else:
                trace_str = '{}.{}'.format(self._parent.get_trace_to_root(), self._name)
        else:
            trace_str = self._name
        if self._is_array:
            trace_str += '[]'
        return trace_str

    def get_filter_str(self):
        """Return the kind of JMESPath that filters the results with some conditions."""
        outer_trace, inner_trace = self.get_trace_to_array('')
        if outer_trace is None or inner_trace is None:
            return None
        value = self._get_one_data()
        if not value:
            return None
        filter_str = "{}[?{}=='{}']".format(outer_trace, inner_trace, value)
        return filter_str

    def get_contains_str(self):
        """Return the JMESPath that filter the results with a contains function."""
        outer_trace, inner_trace = self.get_trace_to_array('')
        if outer_trace is None or inner_trace is None:
            return None
        value = self._get_one_data()
        if not value:
            return None
        contains_str = "{0}[?contains(@.{1}, 'something')==`true`].{1}".format(outer_trace, inner_trace)
        return contains_str

    def get_examples(self):
        """The entry function for recommend examples for current node."""
        ans = []
        select_string = self.get_trace_to_root()
        ans.append(QueryExample(select_string, self.get_help_str('select')))
        filter_str = self.get_filter_str()
        if filter_str:
            ans.append(QueryExample(filter_str, self.get_help_str('filter')))
        contains_str = self.get_contains_str()
        if contains_str:
            ans.append(QueryExample(contains_str, self.get_help_str('contains')))
        return ans


class QueryTreeBuilder:
    """Parse entry. Generate parse tree from json. And then give examples."""

    def __init__(self, config):
        self._root = None  # dummy root node
        self._all_nodes = {}
        self._config = {}
        self.update_config(config)

    def build(self, data):
        """Build a query tree with a given json file."""
        self._root = self._parse('', [data], None)
        if self._root:
            self._root.is_dummy = True

    def generate_examples(self, keywords_list, output_format):
        """Generate JMESPath query string examples based on keyword_list."""
        examples = []
        match_list = self._get_matched_nodes(keywords_list)
        for node_name in match_list:
            if node_name:  # skip root node
                for node in self._all_nodes.get(node_name):
                    examples.extend(node.get_examples())
        if self._config['max_examples'] >= 0:
            examples = examples[:self._config['max_examples']]
        if output_format == 'table':
            for item in examples:
                item.set_max_length(self._config['examples_len'], self._config['help_len'])
        return todict(examples)

    def update_config(self, config):
        self._config['examples_len'] = int(config.get('query', 'examples_len', '80'))
        self._config['help_len'] = int(config.get('query', 'help_len', '80'))
        self._config['max_examples'] = int(config.get('query', 'max_examples', '10'))

    def _get_matched_nodes(self, keywords_list):
        """
        Return a list of keys that match the user provided keywords.
        Return all available keys if no keyword is provided.
        """
        def name_match(pattern, line):
            return pattern.lower() in line.lower()

        match_list = []
        # return all available key if no keyword is provided
        if not keywords_list:
            return self._all_nodes.keys()

        for pattern in keywords_list:
            for node_name in self._all_nodes:
                if node_name not in match_list and name_match(pattern, node_name):
                    match_list.append(node_name)
        return match_list

    def _parse(self, name, data, parent, is_array=False):
        """do parse for a single node

        :param str name:
            Name of the node.
        :param list data:
            All data in the json with the same depth and the same name.
            This field must be a list.
        :param TreeNode parent:
            The parent node of current node. None if this is the root node.
        :param bool is_array:
            True if the value of this JSON node is an array.
        """
        if not data:
            return None
        if all(isinstance(d, list) for d in data):
            node = self._parse_list(name, data, parent)
        elif all(isinstance(d, dict) for d in data):
            node = self._parse_dict(name, data, parent, is_array)
        elif any(isinstance(d, (dict, list)) for d in data):
            node = None  # inhomogeneous type
        else:
            node = self._parse_leaf(name, data, parent, is_array)
        return node

    def _parse_list(self, name, data, parent):
        flatten_data = []
        # flatten list of list to list of data
        for d in data:
            flatten_data.extend(d)
        if not flatten_data:
            return None
        node = self._parse(name, flatten_data, parent, is_array=True)
        return node

    def _parse_leaf(self, name, data, parent, is_array):
        node = QueryTreeNode(name, parent, is_array)
        node.update_node_data(data)
        self._record_node(name, node)
        return node

    def _parse_dict(self, name, data, parent, is_array):
        node = QueryTreeNode(name, parent, is_array)
        all_keys = self._get_all_keys(data)
        for key in all_keys:
            values = self._get_not_none_values(data, key)
            if not values:  # all values are None
                continue
            child_node = self._parse(key, values, node, is_array=False)
            node.add_child(child_node)
        self._record_node(name, node)
        return node

    def _get_all_keys(self, data):  # pylint: disable=no-self-use
        """Get all keys in a list of dict"""
        return set().union(*(d.keys() for d in data))

    def _get_not_none_values(self, data, key):  # pylint: disable=no-self-use
        """Get all not None values in a list of dict"""
        return [d.get(key) for d in data if d.get(key, None) is not None]

    def _record_node(self, name, node):
        """Add name and node to `self._all_nodes`"""
        if not node:
            return
        if name in self._all_nodes:
            self._all_nodes[name].append(node)
        else:
            self._all_nodes[name] = [node]

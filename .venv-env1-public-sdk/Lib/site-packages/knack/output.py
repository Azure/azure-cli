# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import json
import traceback
from collections import OrderedDict
from io import StringIO

from .events import EVENT_INVOKER_POST_PARSE_ARGS, EVENT_PARSER_GLOBAL_CREATE
from .log import get_logger
from .util import CLIError, CommandResultItem, CtxTypeError

logger = get_logger(__name__)


def _decode_str(output):
    if not isinstance(output, str):
        output = str(output)
    return output


class _ComplexEncoder(json.JSONEncoder):

    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, (bytes, bytearray)):
            return o.decode()
        return json.JSONEncoder.default(self, o)


def format_json(obj):
    result = obj.result
    # OrderedDict.__dict__ is always '{}', to persist the data, convert to dict first.
    input_dict = dict(result) if hasattr(result, '__dict__') else result
    return json.dumps(input_dict, ensure_ascii=False, indent=2, sort_keys=True, cls=_ComplexEncoder,
                      separators=(',', ': ')) + '\n'


def format_json_color(obj):
    from pygments import highlight, lexers, formatters
    return highlight(format_json(obj), lexers.JsonLexer(), formatters.TerminalFormatter())  # pylint: disable=no-member


def format_yaml(obj):
    import yaml
    try:
        return yaml.safe_dump(obj.result, default_flow_style=False, allow_unicode=True)
    except yaml.representer.RepresenterError:
        # yaml.safe_dump fails when obj.result is an OrderedDict. knack's --query implementation converts the result to an OrderedDict. https://github.com/microsoft/knack/blob/af674bfea793ff42ae31a381a21478bae4b71d7f/knack/query.py#L46. # pylint: disable=line-too-long
        return yaml.safe_dump(json.loads(json.dumps(obj.result)), default_flow_style=False, allow_unicode=True)


def format_yaml_color(obj):
    from pygments import highlight, lexers, formatters
    return highlight(format_yaml(obj), lexers.YamlLexer(), formatters.TerminalFormatter())  # pylint: disable=no-member


def format_none(_):
    return ""


def format_table(obj):
    result = obj.result
    try:
        if obj.table_transformer and not obj.is_query_active:
            if isinstance(obj.table_transformer, str):
                from jmespath import compile as compile_jmes, Options
                result = compile_jmes(obj.table_transformer).search(result, Options(OrderedDict))
            else:
                result = obj.table_transformer(result)
        result_list = result if isinstance(result, list) else [result]
        should_sort_keys = not obj.is_query_active and not obj.table_transformer
        to = _TableOutput(should_sort_keys)
        return to.dump(result_list)
    except Exception as ex:
        logger.debug(traceback.format_exc())
        raise CLIError("Table output unavailable. "
                       "Use the --query option to specify an appropriate query. "
                       "Use --debug for more info.") from ex


def format_tsv(obj):
    result = obj.result
    result_list = result if isinstance(result, list) else [result]
    return _TsvOutput.dump(result_list)


class OutputProducer(object):

    ARG_DEST = '_output_format'

    _FORMAT_DICT = {
        'json': format_json,
        'jsonc': format_json_color,
        'yaml': format_yaml,
        'yamlc': format_yaml_color,
        'table': format_table,
        'tsv': format_tsv,
        'none': format_none,
    }

    @staticmethod
    def on_global_arguments(cli_ctx, **kwargs):
        arg_group = kwargs.get('arg_group')
        arg_group.add_argument('--output', '-o', dest=OutputProducer.ARG_DEST,
                               choices=list(OutputProducer._FORMAT_DICT),
                               default=cli_ctx.config.get('core', 'output', fallback='json'),
                               help='Output format',
                               type=str.lower)

    @staticmethod
    def handle_output_argument(cli_ctx, **kwargs):
        args = kwargs.get('args')
        # Set the output type for this invocation
        cli_ctx.invocation.data['output'] = getattr(args, OutputProducer.ARG_DEST)

    def __init__(self, cli_ctx=None):
        """ Manages the production of output from the result of a command invocation

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.cli_ctx.register_event(EVENT_PARSER_GLOBAL_CREATE, OutputProducer.on_global_arguments)
        self.cli_ctx.register_event(EVENT_INVOKER_POST_PARSE_ARGS, OutputProducer.handle_output_argument)

    def out(self, obj, formatter=None, out_file=None):
        """ Produces the output using the command result.
            The method does not return a result as the output is written straight to the output file.

        :param obj: The command result
        :type obj: knack.util.CommandResultItem
        :param formatter: The formatter we should use for the command result
        :type formatter: function
        :param out_file: The file to write output to
        :type out_file: file-like object
        """
        if not isinstance(obj, CommandResultItem):
            raise TypeError('Expected {} got {}'.format(CommandResultItem.__name__, type(obj)))

        output = formatter(obj)
        try:
            print(output, file=out_file, end='')
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                pass
            else:
                raise
        except UnicodeEncodeError:
            logger.warning("Unable to encode the output with %s encoding. Unsupported characters are discarded.",
                           out_file.encoding)
            print(output.encode('ascii', 'ignore').decode('utf-8', 'ignore'),
                  file=out_file, end='')

    def get_formatter(self, format_type):
        # remove color if stdout is not a tty
        if not self.cli_ctx.enable_color and format_type == 'jsonc':
            return OutputProducer._FORMAT_DICT['json']
        if not self.cli_ctx.enable_color and format_type == 'yamlc':
            return OutputProducer._FORMAT_DICT['yaml']
        return OutputProducer._FORMAT_DICT[format_type]


class _TableOutput(object):  # pylint: disable=too-few-public-methods

    SKIP_KEYS = ['id', 'type', 'etag']

    def __init__(self, should_sort_keys=False):
        self.should_sort_keys = should_sort_keys

    @staticmethod
    def _capitalize_first_char(x):
        return x[0].upper() + x[1:] if x else x

    def _auto_table_item(self, item):
        new_entry = OrderedDict()
        try:
            keys = sorted(item) if self.should_sort_keys and isinstance(item, dict) else item.keys()
            for k in keys:
                if k in _TableOutput.SKIP_KEYS:
                    continue
                if item[k] is not None and not isinstance(item[k], (list, dict, set)):
                    new_entry[_TableOutput._capitalize_first_char(k)] = item[k]
        except AttributeError:
            # handles odd cases where a string/bool/etc. is returned
            if isinstance(item, list):
                for col, val in enumerate(item):
                    new_entry['Column{}'.format(col + 1)] = val
            else:
                new_entry['Result'] = item
        return new_entry

    def _auto_table(self, result):
        if isinstance(result, list):
            new_result = []
            for item in result:
                new_result.append(self._auto_table_item(item))
            return new_result
        return self._auto_table_item(result)

    def dump(self, data):
        from tabulate import tabulate
        table_data = self._auto_table(data)
        table_str = tabulate(table_data, headers="keys", tablefmt="simple",
                             disable_numparse=True) if table_data else ''
        if table_str == '\n':
            raise ValueError('Unable to extract fields for table.')
        return table_str + '\n'


class _TsvOutput(object):  # pylint: disable=too-few-public-methods

    @staticmethod
    def _dump_obj(data, stream):
        if isinstance(data, list):
            stream.write(str(len(data)))
        elif isinstance(data, dict):
            # We need to print something to avoid mismatching
            # number of columns if the value is None for some instances
            # and a dictionary value in other...
            stream.write('')
        else:
            to_write = data if isinstance(data, str) else str(data)
            stream.write(to_write)

    @staticmethod
    def _dump_row(data, stream):
        separator = ''
        if isinstance(data, (dict, list)):
            if isinstance(data, OrderedDict):
                values = data.values()
            elif isinstance(data, dict):
                values = [value for _, value in sorted(data.items())]
            else:
                values = data

            # Iterate through the items either sorted by key value (if dict) or in the order
            # they were added (in the cases of an ordered dict) in order to make the output
            # stable
            for value in values:
                stream.write(separator)
                _TsvOutput._dump_obj(value, stream)
                separator = '\t'
        elif isinstance(data, list):
            for value in data:
                stream.write(separator)
                _TsvOutput._dump_obj(value, stream)
                separator = '\t'
        elif isinstance(data, bool):
            _TsvOutput._dump_obj(str(data).lower(), stream)
        else:
            _TsvOutput._dump_obj(data, stream)
        stream.write('\n')

    @staticmethod
    def dump(data):
        io = StringIO()
        for item in data:
            _TsvOutput._dump_row(item, io)

        result = io.getvalue()
        io.close()
        return result

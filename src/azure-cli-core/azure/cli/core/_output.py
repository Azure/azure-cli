# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function, unicode_literals

import errno
import sys
import traceback
from collections import OrderedDict, namedtuple
from six import StringIO, string_types

from azure.cli.core import get_az_logger, CLIError

logger = get_az_logger(__name__)

CommandResultItem = namedtuple('CommandResultItem', ['result', 'table_transformer', 'is_query_active'])


def format_json(result, *_):
    import json

    class ComplexEncoder(json.JSONEncoder):
        def default(self, o):  # pylint: disable=method-hidden
            if isinstance(o, bytes) and not isinstance(o, str):
                return o.decode()
            return json.JSONEncoder.default(self, o)

    # OrderedDict.__dict__ is always '{}', to persist the data, convert to dict first.
    input_dict = dict(result) if hasattr(result, '__dict__') else result
    return json.dumps(input_dict, indent=2, sort_keys=True, cls=ComplexEncoder, separators=(',', ': ')) + '\n'


def format_json_color(result, *args):
    from pygments import highlight, lexers, formatters
    return highlight(format_json(result, *args),
                     lexers.JsonLexer(), formatters.TerminalFormatter())  # pylint: disable=no-member


def format_table(result, table_transformer, is_query_active):
    from tabulate import tabulate
    try:
        def _transform_result_for_table(data):
            if table_transformer and not is_query_active:
                if isinstance(table_transformer, str):
                    from jmespath import compile as compile_jmes, Options
                    return compile_jmes(table_transformer).search(data, Options(OrderedDict))
                return table_transformer(data)
            return data

        def _capitalize_first_char(x):
            return x[0].upper() + x[1:] if x else x

        def _get_row(item):
            should_sort_keys = not is_query_active and not table_transformer
            row = OrderedDict()
            try:
                keys = sorted(item) if should_sort_keys and isinstance(item, dict) else item.keys()
                for k in keys:
                    if k in ('id', 'type', 'etag'):
                        continue
                    if item[k] and not isinstance(item[k], (list, dict, set)):
                        row[_capitalize_first_char(k)] = item[k]
            except AttributeError:
                # handles odd cases where a string/bool/etc. is returned
                if isinstance(item, list):
                    for col, val in enumerate(item):
                        row['Column{}'.format(col + 1)] = val
                else:
                    row['Result'] = item
            return row

        result = _transform_result_for_table(result)
        result = result if isinstance(result, list) else [result]
        table_data = [_get_row(each) for each in result]
        table_str = tabulate(table_data, headers="keys", tablefmt="simple") if table_data else ''
        if table_str == '\n':
            raise ValueError('Unable to extract fields for table.')
        return table_str + '\n'
    except:
        logger.debug(traceback.format_exc())
        raise CLIError("Table output unavailable. Use the --query option to specify an appropriate query. Use --debug "
                       "for more info.")


def format_tsv(result, *_):
    import contextlib

    result_list = result if isinstance(result, list) else [result]

    def _get_column(data, stream):
        if isinstance(data, list):
            stream.write(str(len(data)))
        elif isinstance(data, dict):
            # We need to print something to avoid mismatching number of columns if the value is None for some instances
            # and a dictionary value in other...
            stream.write('')
        else:
            to_write = data if isinstance(data, string_types) else str(data)
            stream.write(to_write)

    def _get_row(data, stream):
        separator = ''
        if isinstance(data, (dict, list)):
            if isinstance(data, OrderedDict):
                values = data.values()
            elif isinstance(data, dict):
                values = [value for _, value in sorted(data.items())]
            else:
                values = data

            # Iterate through the items either sorted by key value (if dict) or in the order they were added (in the
            # cases of an ordered dict) in order to make the output stable
            for value in values:
                stream.write(separator)
                _get_column(value, stream)
                separator = '\t'
        elif isinstance(data, list):
            for value in data:
                stream.write(separator)
                _get_column(value, stream)
                separator = '\t'
        elif isinstance(data, bool):
            _get_column(str(data).lower(), stream)
        else:
            _get_column(data, stream)
        stream.write('\n')

    @contextlib.contextmanager
    def _get_string_io():
        buffer = StringIO()
        yield buffer
        buffer.close()

    with _get_string_io() as buf:
        for item in result_list:
            _get_row(item, buf)

        return buf.getvalue()


def get_output_producer(formatter, output_stream=sys.stdout):
    """
    Returns a function which transform a command result with specified formatter and print to the given stream.

    :param formatter: The formatter transforms the command result data.
    :type formatter: callable
    :param output_stream: The stream where the result is printed.
    :type output_stream: a file-like object (stream)
    :return: The output function.
    """

    def _output_producer(command_result):
        """
        The output function transforms the data with given formatter and sent to specified stream.

        :param command_result: The command result of which its data is to be print.
        :type command_result: CommandResultItem
        """
        import colorama
        import platform

        stream = colorama.AnsiToWin32(output_stream).stream if platform.system() == 'Windows' else output_stream
        output = formatter(*command_result)
        try:
            print(output, file=stream, end='')
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                pass
            else:
                raise
        except UnicodeEncodeError:
            print(output.encode('ascii', 'ignore').decode('utf-8', 'ignore'), file=stream, end='')

    return _output_producer


def get_formatter(format_type):
    if format_type == 'json':
        formatter = format_json
    elif format_type == 'jsonc':
        formatter = format_json_color
    elif format_type == 'table':
        formatter = format_table
    elif format_type == 'tsv':
        formatter = format_tsv
    else:
        raise ValueError('Unknown formatter type: {}.'.format(format_type))

    return formatter

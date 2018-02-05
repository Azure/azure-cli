# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function, unicode_literals

import errno
import sys
import platform
from six import StringIO
import colorama

from knack.output import format_json, format_json_color, format_table, format_tsv


def format_text(obj):
    result = obj.result
    result_list = result if isinstance(result, list) else [result]
    to = TextOutput()
    try:
        for item in result_list:
            for item_key in sorted(item):
                to.add(item_key, item[item_key])
        return to.dump()
    except TypeError:
        return ''


class OutputProducer(object):  # pylint: disable=too-few-public-methods

    format_dict = {
        'json': format_json,
        'jsonc': format_json_color,
        'table': format_table,
        'text': format_text,
        'tsv': format_tsv,
    }

    def __init__(self, formatter, file=sys.stdout):  # pylint: disable=redefined-builtin
        self.formatter = formatter
        self.file = file

    def out(self, obj):
        if platform.system() == 'Windows':
            self.file = colorama.AnsiToWin32(self.file).stream
        output = self.formatter(obj)
        try:
            print(output, file=self.file, end='')
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                pass
            else:
                raise
        except UnicodeEncodeError:
            print(output.encode('ascii', 'ignore').decode('utf-8', 'ignore'),
                  file=self.file, end='')

    @staticmethod
    def get_formatter(format_type):
        return OutputProducer.format_dict.get(format_type)


class TextOutput(object):

    def __init__(self):
        self.identifiers = {}

    def add(self, identifier, value):
        if identifier in self.identifiers:
            self.identifiers[identifier].append(value)
        else:
            self.identifiers[identifier] = [value]

    def dump(self):
        io = StringIO()
        for identifier in sorted(self.identifiers):
            io.write(identifier.upper())
            io.write('\t')
            for col in self.identifiers[identifier]:
                if isinstance(col, (list, dict)):
                    # TODO: Need to handle complex objects
                    io.write("null")
                else:
                    io.write(str(col))
                io.write('\t')
            io.write('\n')
        result = io.getvalue()
        io.close()
        return result

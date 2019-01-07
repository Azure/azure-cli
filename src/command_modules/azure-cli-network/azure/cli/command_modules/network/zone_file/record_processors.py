# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# The MIT License (MIT)

# Copyright (c) 2016 Blockstack

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# pylint: skip-file

from __future__ import print_function

import copy


def process_soa(io, data, name, print_name=False):
    """
    Replace {SOA} in template with a set of serialized SOA records
    """
    indent = ' ' * len('{} {} IN SOA '.format(name, data['ttl']))
    print('{} {} IN SOA {} {} ('.format(name, data['ttl'], data['mname'], data['rname']), file=io)
    for item in ['serial', 'refresh', 'retry', 'expire', 'minimum']:
        print('{}{} ; {}'.format(indent, data[item], item), file=io)
    print('{})'.format(indent), file=io)


def _quote_field(data, field):
    """
    Quote a field in a list of DNS records.
    Return the new data records.
    """
    if data is None:
        return None

    # embedded quotes require escaping - but only if not escaped already
    # note that semi-colons do not need escaping here since we are putting it
    # inside of a quoted string
    fieldBuf = ""
    escape = False
    for c in data[field]:
        if c == '"':
            fieldBuf += '\\"'
            escape = False
        elif c == '\\':
            if escape:
                fieldBuf += '\\\\'
                escape = False
            else:
                escape = True
        else:
            if escape:
                fieldBuf += '\\'
            fieldBuf += c
            escape = False

    data[field] = '"%s"' % fieldBuf

    return data


def process_rr(io, data, record_type, record_keys, name, print_name):
    """ Print out single line record entries """
    if data is None:
        return

    if isinstance(record_keys, str):
        record_keys = [record_keys]
    elif not isinstance(record_keys, list):
        raise ValueError('record_keys must be a string or list of strings')

    name_display = name if print_name else ' ' * len(name)
    print('{} {} IN {} '.format(name_display, data['ttl'], record_type), end='', file=io)

    for i, key in enumerate(record_keys):
        print(data[key], end='\n' if i == len(record_keys) - 1 else ' ', file=io)


def process_ns(io, data, name, print_name=False):
    process_rr(io, data, 'NS', 'host', name, print_name)


def process_a(io, data, name, print_name=False):
    return process_rr(io, data, 'A', 'ip', name, print_name)


def process_aaaa(io, data, name, print_name=False):
    return process_rr(io, data, 'AAAA', 'ip', name, print_name)


def process_caa(io, data, name, print_name=False):
    process_rr(io, _quote_field(data, 'value'), 'CAA', ['flags', 'tag', 'value'], name, print_name)


def process_cname(io, data, name, print_name=False):
    return process_rr(io, data, 'CNAME', 'alias', name, print_name)


def process_mx(io, data, name, print_name=False):
    return process_rr(io, data, 'MX', ['preference', 'host'], name, print_name)


def process_ptr(io, data, name, print_name=False):
    return process_rr(io, data, 'PTR', 'host', name, print_name)


def process_txt(io, data, name, print_name=False):
    return process_rr(io, _quote_field(data, 'txt'), 'TXT', 'txt', name, print_name)


def process_srv(io, data, name, print_name=False):
    return process_rr(io, data, 'SRV', ['priority', 'weight', 'port', 'target'], name, print_name)

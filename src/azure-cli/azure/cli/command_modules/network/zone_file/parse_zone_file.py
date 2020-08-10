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

"""
Known limitations:
    * only the IN class is supported
    * PTR records must have a non-empty name
    * currently only supports the following:
    '$ORIGIN', '$TTL', 'SOA', 'NS', 'A', 'AAAA', 'CNAME', 'MX', 'PTR',
    'TXT', 'SRV', 'SPF', 'URI', 'CAA'
"""

import copy
import datetime
import time
import argparse
from collections import OrderedDict
import re

from knack.log import get_logger
from knack.util import CLIError


logger = get_logger(__name__)

semicolon_regex = re.compile(r'(?:"[^"]*")*[^\\](;.*)')
date_regex_dict = {
    'w': {'regex': re.compile(r'(\d*w)'), 'scale': 86400 * 7},
    'd': {'regex': re.compile(r'(\d*d)'), 'scale': 86400},
    'h': {'regex': re.compile(r'(\d*h)'), 'scale': 3600},
    'm': {'regex': re.compile(r'(\d*m)'), 'scale': 60},
    's': {'regex': re.compile(r'(\d*s)'), 'scale': 1}
}

_REGEX = {
    'ttl': r'(?P<delim>\$ttl)\s+(?P<val>\d+\w*)',
    'origin': r'(?P<delim>\$origin)\s+(?P<val>[\w\.-]+)',
    'soa': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>soa)\s+(?P<host>[\w\.-]+)\s+(?P<email>[\w\.-]+)\s+(?P<serial>\d*)\s+(?P<refresh>\w*)\s+(?P<retry>\w*)\s+(?P<expire>\w*)\s+(?P<minimum>\w*)?',
    'a': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>a)\s+(?P<ip>[\d\.]+)',
    'ns': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>ns)\s+(?P<host>[\w\.-]+)',
    'aaaa': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>aaaa)\s+(?P<ip>[\w:]+)',
    'caa': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>caa)\s+(?P<flags>\d+)\s+(?P<tag>\w+)\s+(?P<val>.+)',
    'cname': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>cname)\s+(?P<alias>[\w\.-]+)',
    'mx': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>mx)\s+(?P<preference>\d+)\s+(?P<host>[\w\.-]+)',
    'txt': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>txt)\s+(?P<txt>.+)',
    'ptr': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>ptr)\s+(?P<host>[\w\.-]+)',
    'srv': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>srv)\s+(?P<priority>\d+)\s+(?P<weight>\d+)\s+(?P<port>\d+)\s+(?P<target>[\w\.]+)',
    'spf': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>spf)\s+(?P<txt>.+)',
    'uri': r'(?P<name>[@\*\w\.-]*)\s+(?:(?P<ttl>\d+\w*)\s+)?(?:(?P<class>in)\s+)?(?P<delim>uri)\s+(?P<priority>\d+)\s+(?P<weight>\d+)\s+(?P<target>[\w\.]+)'
}

_COMPILED_REGEX = {k: re.compile(v, re.IGNORECASE) for k, v in _REGEX.items()}


class IncorrectParserException(Exception):
    pass


def _tokenize_line(line, quote_strings=False, infer_name=True):
    """
    Tokenize a line:
    * split tokens on whitespace
    * treat quoted strings as a single token
    """
    ret = []
    escape = False
    quote = False
    tokbuf = ""
    firstchar = True
    ll = list(line)
    while len(ll) > 0:
        c = ll.pop(0)
        if c.isspace():
            if firstchar:
                # used by the _add_record_names method
                tokbuf += '$NAME' if infer_name else ' '

            if not quote and not escape:
                # end of token
                if len(tokbuf) > 0:
                    ret.append(tokbuf)
                tokbuf = ''

            elif escape:
                # escaped space (can be inside or outside of quote)
                tokbuf += '\\' + c
                escape = False

            elif quote:
                # in quotes
                tokbuf += c

            else:
                tokbuf = ''
        elif c == '\\':
            if escape:
                # escape of an escape is valid part of the line sequence
                tokbuf += '\\\\'
                escape = False
            else:
                escape = True
        elif c == '"':
            if not escape:
                if quote:
                    # end of quote
                    if quote_strings:
                        tokbuf += '"'
                    ret.append(tokbuf)
                    tokbuf = ''
                    quote = False
                else:
                    # beginning of quote
                    if quote_strings:
                        tokbuf += '"'
                    quote = True
            else:
                # append the escaped quote
                tokbuf += '\\"'
                escape = False
        else:
            # normal character
            if escape:
                # append escape character
                tokbuf += '\\'

            tokbuf += c
            escape = False
        firstchar = False

    if len(tokbuf.strip(' \r\n\t')):
        ret.append(tokbuf)

    if len(ret) == 1 and ret[0] == '$NAME':
        return []
    else:
        return ret


def _find_comment_index(line):
    """
    Finds the index of a ; denoting a comment.
    Ignores escaped semicolons and semicolons inside quotes
    """
    escape = False
    quote = False
    for i, char in enumerate(line):
        if char == '\\':
            escape = True
            continue
        elif char == '"':
            if escape:
                escape = False
                continue
            else:
                quote = not quote
        elif char == ';':
            if quote:
                escape = False
                continue
            elif escape:
                escape = False
                continue
            else:
                # comment denoting semicolon found
                return i
        else:
            escape = False
            continue
    # no unquoted, unescaped ; found
    return -1


def _serialize(tokens):
    """
    Serialize tokens:
    * quote whitespace-containing tokens
    """
    ret = []
    for tok in tokens:
        if " " in tok:
            tok = '"%s"' % tok

        ret.append(tok)

    return " ".join(ret)


def _remove_comments(text):
    """
    Remove comments from a zonefile
    """
    ret = []
    lines = text.split("\n")
    for line in lines:
        if not line:
            continue

        index = _find_comment_index(line)
        if index != -1:
            line = line[:index]
        if line:
            ret.append(line)

    return "\n".join(ret)


def _flatten(text):
    """
    Flatten the text:
    * make sure each record is on one line.
    * remove parenthesis
    * remove Windows line endings
    """
    lines = text.split('\n')
    SENTINEL = '%%%'

    # tokens: sequence of non-whitespace separated by '' where a newline was
    tokens = []
    for line in (x for x in lines if len(x) > 0):
        line = line.replace('\t', ' ')
        tokens += _tokenize_line(line, quote_strings=True, infer_name=False)
        tokens.append(SENTINEL)

    # find (...) and turn it into a single line ("capture" it)
    capturing = False
    captured = []

    flattened = []
    while len(tokens) > 0:
        tok = tokens.pop(0)

        if tok == '$NAME':
            tok = ' '

        if not capturing and tok == SENTINEL:
            # normal end-of-line
            if len(captured) > 0:
                flattened.append(" ".join(captured))
                captured = []
            continue

        if tok.startswith("("):
            # begin grouping
            tok = tok.lstrip("(")
            capturing = True

        if capturing and tok.endswith(")"):
            # end grouping.  next end-of-line will turn this sequence into a flat line
            tok = tok.rstrip(")")
            capturing = False

        if tok != SENTINEL:
            captured.append(tok)

    return "\n".join(flattened)


def _add_record_names(text):
    """
    Go through each line of the text and ensure that
    a name is defined.  Use previous record name if there is none.
    """
    global SUPPORTED_RECORDS

    lines = text.split("\n")
    ret = []
    previous_record_name = None

    for line in lines:
        tokens = _tokenize_line(line)
        if not tokens:
            continue

        record_name = tokens[0]
        if record_name == '$NAME':
            tokens = [previous_record_name] + tokens[1:]
        elif not record_name.startswith('$'):
            previous_record_name = record_name

        ret.append(_serialize(tokens))

    return "\n".join(ret)


def _convert_to_seconds(value):
    """ Converts TTL strings into seconds """
    try:
        return int(value)
    except ValueError:
        # parse the BIND format
        # (w)eek, (d)ay, (h)our, (m)inute, (s)econd
        seconds = 0
        ttl_string = value.lower()
        for component in ['w', 'd', 'h', 'm', 's']:
            regex = date_regex_dict[component]['regex']
            match = regex.search(ttl_string)
            if match:
                match_string = match.group(0)
                ttl_string = ttl_string.replace(match_string, '')
                match_value = int(match_string.strip(component))
                seconds += match_value * date_regex_dict[component]['scale']
            if not ttl_string:
                return seconds
        # convert the last piece without any units, which must be seconds
        try:
            seconds += int(ttl_string)
            return seconds
        except ValueError:
            raise CLIError("Unable to convert value '{}' to seconds.".format(value))


def _expand_with_origin(record, properties, origin):
    if not isinstance(properties, list):
        properties = [properties]

    for property in properties:
        if not record[property].endswith('.'):
            record[property] = '{}.{}'.format(record[property], origin)


def _post_process_ttl(zone):
    for name in zone:
        for record_type in zone[name]:
            records = zone[name][record_type]
            if isinstance(records, list):
                ttl = min([x['ttl'] for x in records])
                for record in records:
                    if record['ttl'] != ttl:
                        logger.warning('Using lowest TTL {} for the record set. Ignoring value {}'
                                       .format(ttl, record['ttl']))
                    record['ttl'] = ttl


def _post_process_txt_record(record):

    def line_split(line):
        return re.findall(r'"(?:\\.|[^"\\])*"|(?:\\.|[^"\s\\])+', line)

    record_split = line_split(record['txt'])

    # strip quotes
    for i, val in enumerate(record_split):
        if val.startswith('"') and val.endswith('"'):
            record_split[i] = val[1:-1]

    long_text = ''.join(record_split)
    original_len = len(long_text)
    record['txt'] = []
    while len(long_text) > 255:
        record['txt'].append(long_text[:255])
        long_text = long_text[255:]
    record['txt'].append(long_text)
    final_str = ''.join(record['txt'])
    final_len = len(final_str)
    assert (original_len == final_len)


def _post_process_caa_record(record):
    # strip quotes
    if record['val'].startswith('"') and record['val'].endswith('"'):
        record['val'] = record['val'][1:-1]


def _post_check_names(zone):

    # get the origin name that has the SOA record
    # ensure the origin is in each record set
    origin = None
    for name in zone:
        for record_type in zone[name]:
            if record_type == 'soa':
                origin = name
                break
        if origin:
            break
    bad_names = [x for x in zone if origin not in x]
    if bad_names:
        raise CLIError("Record names '{}' are not part of the domain.".format(bad_names))


def parse_zone_file(text, zone_name, ignore_invalid=False):
    """
    Parse a zonefile into a dict
    """

    text = _remove_comments(text)
    text = _flatten(text)
    text = _add_record_names(text)

    zone_obj = OrderedDict()
    record_lines = text.split("\n")
    current_origin = zone_name.rstrip('.') + '.'
    current_ttl = 3600
    soa_processed = False

    for record_line in record_lines:
        parse_match = False
        record = None
        for record_type, regex in _COMPILED_REGEX.items():
            match = regex.match(record_line)
            if not match:
                continue

            parse_match = True
            record = match.groupdict()

        if not parse_match and not ignore_invalid:
            raise CLIError('Unable to parse: {}'.format(record_line))

        record_type = record['delim'].lower()
        if record_type == '$origin':
            origin_value = record['val']
            if not origin_value.endswith('.'):
                logger.warning("$ORIGIN '{}' should have terminating dot.".format(origin_value))
            current_origin = origin_value.rstrip('.') + '.'
        elif record_type == '$ttl':
            current_ttl = _convert_to_seconds(record['val'])
        else:
            record_name = record['name']
            if '@' in record_name:
                record_name = record_name.replace('@', current_origin)
            elif not record_name.endswith('.'):
                record_name = '{}.{}'.format(record_name, current_origin)
            print(current_origin, record_name)

            # special record-specific fix-ups
            if record_type == 'ptr':
                record['fullname'] = record_name + '.' + current_origin
            elif record_type == 'soa':
                for key in ['refresh', 'retry', 'expire', 'minimum']:
                    record[key] = _convert_to_seconds(record[key])
                _expand_with_origin(record, 'email', current_origin)
            elif record_type == 'cname':
                _expand_with_origin(record, 'alias', current_origin)
            elif record_type == 'mx':
                _expand_with_origin(record, 'host', current_origin)
            elif record_type == 'ns':
                _expand_with_origin(record, 'host', current_origin)
            elif record_type == 'srv':
                _expand_with_origin(record, 'target', current_origin)
            elif record_type == 'spf':
                record_type = 'txt'
            record['ttl'] = _convert_to_seconds(record['ttl'] or current_ttl)

            # handle quotes for CAA and TXT
            if record_type == 'caa':
                _post_process_caa_record(record)
            elif record_type == 'txt':
                # handle TXT concatenation and splitting separately
                _post_process_txt_record(record)

            if record_name not in zone_obj:
                zone_obj[record_name] = OrderedDict()

            if record_type == 'soa':
                if soa_processed:
                    raise CLIError('Zone file can contain only one SOA record.')
                if record_name != current_origin:
                    raise CLIError("Zone SOA record must be at the apex '@'.")
                zone_obj[record_name][record_type] = record
                soa_processed = True
                continue

            if not soa_processed:
                raise CLIError('First record in zone file must be SOA.')

            if record_type == 'cname':
                if record_type in zone_obj[record_name]:
                    logger.warning("CNAME record already exists for '{}'. Ignoring '{}'."
                                   .format(record_name, record['alias']))
                    continue
                zone_obj[record_name][record_type] = record
                continue

            # any other record can have multiple entries
            if record_type not in zone_obj[record_name]:
                zone_obj[record_name][record_type] = []
            zone_obj[record_name][record_type].append(record)

    _post_process_ttl(zone_obj)
    _post_check_names(zone_obj)
    return zone_obj

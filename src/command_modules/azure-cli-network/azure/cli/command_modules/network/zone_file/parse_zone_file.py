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
    'TXT', 'SRV', 'SPF', 'URI'
"""

import copy
import datetime
import time
import argparse
from collections import OrderedDict
import re

import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError

from azure.cli.command_modules.network.zone_file.configs import SUPPORTED_RECORDS
from azure.cli.command_modules.network.zone_file.exceptions import InvalidLineException

logger = azlogging.get_az_logger(__name__)
semicolon_regex = re.compile(r'(?:"[^"]*")*[^\\](;.*)')
date_regex_dict = {
    'w': {'regex': re.compile(r'(\d*w)'), 'scale': 86400 * 7},
    'd': {'regex': re.compile(r'(\d*d)'), 'scale': 86400},
    'h': {'regex': re.compile(r'(\d*h)'), 'scale': 3600},
    'm': {'regex': re.compile(r'(\d*m)'), 'scale': 60},
    's': {'regex': re.compile(r'(\d*s)'), 'scale': 1}
}


class ZonefileLineParser(argparse.ArgumentParser):
    def error(self, message):
        """
        Silent error message
        """
        raise InvalidLineException(message)


class IncorrectParserException(Exception):
    pass


def _make_record_parser(parsers, rec_type, arg_defs):
    """
    Make a parser for a given type of DNS record
    """
    parser = ZonefileLineParser(rec_type)
    parser.add_argument('name', type=str)

    for arg in arg_defs:
        nargs = arg[2] if len(arg) > 2 else 1
        parser.add_argument(arg[0], type=arg[1], nargs=nargs)

    parsers.append(parser)


def _make_parser():
    """
    Make an array of parsers that can process different DNS record types
    """
    parsers = []

    # parse $ORIGIN
    origin = ZonefileLineParser('$ORIGIN')
    origin.add_argument('DELIM', type=str)
    origin.add_argument('value', type=str)
    parsers.append(origin)

    # parse $TTL
    ttl = ZonefileLineParser('$TTL')
    ttl.add_argument('DELIM', type=str)
    ttl.add_argument('value', type=str)
    parsers.append(ttl)

    # parse each RR
    _make_record_parser(parsers, 'SOA', [
        ('ttl', str), ('DELIM', str),
        ('host', str), ('email', str), ('serial', int), ('refresh', str),
        ('retry', str), ('expire', str), ('minimum', str)
    ])
    _make_record_parser(parsers, 'SOA', [
        ('DELIM', str), ('host', str), ('email', str), ('serial', int), ('refresh', str),
        ('retry', str), ('expire', str), ('minimum', str)
    ])
    _make_record_parser(parsers, 'SOA', [
        ('DELIM', str), ('host', str), ('email', str), ('serial', int), ('refresh', str),
        ('retry', str), ('expire', str)
    ])
    _make_record_parser(parsers, 'NS', [('ttl', str, '?'), ('DELIM', str), ('host', str)])
    _make_record_parser(parsers, 'A', [('ttl', str, '?'), ('DELIM', str), ('ip', str)])
    _make_record_parser(parsers, 'AAAA', [('ttl', str, '?'), ('DELIM', str), ('ip', str)])
    _make_record_parser(parsers, 'CNAME', [('ttl', str, '?'), ('DELIM', str), ('alias', str)])
    _make_record_parser(parsers, 'MX', [('ttl', str, '?'), ('DELIM', str), ('preference', str), ('host', str)])
    _make_record_parser(parsers, 'TXT', [('ttl', str), ('DELIM', str), ('txt', str, '+')])
    _make_record_parser(parsers, 'TXT', [('DELIM', str), ('txt', str, '+')])
    _make_record_parser(parsers, 'PTR', [('ttl', str, '?'), ('DELIM', str), ('host', str)])
    _make_record_parser(parsers, 'SRV', [('ttl', str, '?'), ('DELIM', str), ('priority', int), ('weight', int), ('port', int), ('target', str)])
    _make_record_parser(parsers, 'SPF', [('ttl', str, '?'), ('DELIM', str), ('txt', str)])
    _make_record_parser(parsers, 'URI', [('ttl', str, '?'), ('DELIM', str), ('priority', int), ('weight', int), ('target', str)])

    return parsers


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
            elif quote:
                # in quotes
                tokbuf += c
            elif escape:
                # escaped space
                tokbuf += c
                escape = False
            else:
                tokbuf = ''
        elif c == '\\':
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
    * escape semicolons
    """
    ret = []
    for tok in tokens:
        if " " in tok:
            tok = '"%s"' % tok

        if ";" in tok:
            tok = tok.replace(";", "\;")

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
    for l in (x for x in lines if len(x) > 0):
        l = l.replace('\t', ' ')
        tokens += _tokenize_line(l, quote_strings=True, infer_name=False)
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


def _remove_class(text):
    """
    Remove the CLASS from each DNS record, if present.
    The only class that gets used today (for all intents
    and purposes) is 'IN'.
    """
    # see RFC 1035 for list of classes
    lines = text.split("\n")
    ret = []
    for line in lines:
        original_tokens = _tokenize_line(line)
        tokens = []
        for token in original_tokens:
            if token.upper() != 'IN':
                tokens.append(token)
        ret.append(_serialize(tokens))
    return "\n".join(ret)


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


def _parse_record(parser, record_token):
    global SUPPORTED_RECORDS

    # match parser to record type
    record_type = None
    for i in range(3):
        try:
            if record_token[i] in SUPPORTED_RECORDS:
                record_type = record_token[i]
                break
        except KeyError:
            break

    if not record_type:
        from azure.cli.core.util import CLIError
        raise CLIError('Unable to determine record type: {}'.format(' '.join(record_token)))

    # move the record type to the front of the token list so it will conform to argparse
    if record_type != parser.prog:
        raise IncorrectParserException

    try:
        rr, unmatched = parser.parse_known_args(record_token)
        assert len(unmatched) == 0, "Unmatched fields: %s" % unmatched
    except (SystemExit, AssertionError, InvalidLineException):
        # invalid argument
        raise InvalidLineException(' '.join(record_token))

    record = rr.__dict__
    record['type'] = record_type

    # remove emtpy fields
    for field in list(record.keys()):
        if record[field] is None:
            del record[field]

    for key in record:
        try:
            if len(record[key]) == 1:
                record[key] = record[key][0]
        except TypeError:
            continue

    return record


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


def _pre_process_txt_records(text):
    """ This looks only for the cases of multiple text records not surrounded by quotes.
    This must be done after flattening but before any tokenization occurs, as this strips out
    the quotes. """
    lines = text.split('\n')
    for line in lines:
        pass
    return text


def _post_process_txt_record(record, current_ttl):
    if not isinstance(record['txt'], list):
        record['txt'] = [record['txt']]
    record['ttl'] = _convert_to_seconds(record['ttl']) if 'ttl' in record else current_ttl
    long_text = ''.join(x for x in record['txt']) if isinstance(record['txt'], list) else record['txt']
    long_text = long_text.replace('\\', '')
    original_len = len(long_text)
    record['txt'] = []
    while len(long_text) > 255:
        record['txt'].append(long_text[:255])
        long_text = long_text[255:]
    record['txt'].append(long_text)
    final_str = ''.join(record['txt'])
    final_len = len(final_str)
    assert (original_len == final_len)


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
    parsers = _make_parser()

    text = _remove_comments(text)
    text = _flatten(text)
    text = _remove_class(text)
    text = _pre_process_txt_records(text)
    text = _add_record_names(text)

    zone_obj = OrderedDict()
    record_lines = text.split("\n")
    current_origin = zone_name.rstrip('.') + '.'
    current_ttl = 3600
    soa_processed = False

    for record_line in record_lines:
        parse_match = False
        record = None
        for parser in parsers:
            record_tokens = _tokenize_line(record_line)
            try:
                record = _parse_record(parser, record_tokens)
                if record['DELIM'].lower() != record['type'].lower():
                    raise IncorrectParserException
                parse_match = True
                break
            except (InvalidLineException, IncorrectParserException):
                continue
        if not parse_match and not ignore_invalid:
            raise CLIError('Unable to parse: {}'.format(record_line))

        record_type = record['type'].lower()
        if record_type.lower() == '$origin':
            origin_value = record['value']
            if not origin_value.endswith('.'):
                logger.warning("$ORIGIN '{}' should have terminating dot.".format(origin_value))
            current_origin = origin_value.rstrip('.') + '.'
        elif record_type.lower() == '$ttl':
            current_ttl = _convert_to_seconds(record['value'])
        else:
            record_name = record['name']
            if record_name == '@':
                record_name = current_origin
            elif not record_name.endswith('.'):
                record_name = '{}.{}'.format(record_name, current_origin)

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

            if record_type == 'txt':
                # handle TXT concatenation and splitting separately
                _post_process_txt_record(record, current_ttl)
            else:
                record['ttl'] = _convert_to_seconds(record['ttl']) if 'ttl' in record else current_ttl

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

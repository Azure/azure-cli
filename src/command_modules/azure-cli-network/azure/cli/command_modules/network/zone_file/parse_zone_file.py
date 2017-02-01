#!/usr/bin/python 
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#The MIT License (MIT)

#Copyright (c) 2016 Blockstack

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
#pylint: skip-file

"""
Known limitations:
    * only one $ORIGIN and one $TTL are supported
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
from collections import defaultdict

from .configs import SUPPORTED_RECORDS
from .exceptions import InvalidLineException


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
    origin.add_argument('$ORIGIN', type=str)
    parsers.append(origin)

    # parse $TTL
    ttl = ZonefileLineParser('$TTL')
    ttl.add_argument('$TTL', type=int)
    parsers.append(ttl)

    # parse each RR
    _make_record_parser(parsers, 'SOA', [
        ('ttl', int, '?'),
        ('mname', str), ('rname', str), ('serial', int), ('refresh', int),
        ('retry', int), ('expire', int), ('minimum', int)
    ])
    _make_record_parser(parsers, 'NS', [('ttl', int, '?'), ('host', str)])
    _make_record_parser(parsers, 'A', [('ttl', int, '?'), ('ip', str)])
    _make_record_parser(parsers, 'AAAA', [('ttl', int, '?'), ('ip', str)])
    _make_record_parser(parsers, 'CNAME', [('ttl', int, '?'), ('alias', str)])
    _make_record_parser(parsers, 'MX', [('ttl', int, '?'), ('preference', str), ('host', str)])
    _make_record_parser(parsers, 'TXT', [('ttl', int), ('txt', str, '+')])
    _make_record_parser(parsers, 'TXT', [('txt', str, '+')])
    _make_record_parser(parsers, 'PTR', [('ttl', int, '?'), ('host', str)])
    _make_record_parser(parsers, 'SRV', [('ttl', int, '?'), ('priority', int), ('weight', int), ('port', int), ('target', str)])
    _make_record_parser(parsers, 'SPF', [('ttl', int, '?'), ('data', str)])
    _make_record_parser(parsers, 'URI', [('ttl', int, '?'), ('priority', int), ('weight', int), ('target', str)])

    return parsers


def _tokenize_line(line):
    """
    Tokenize a line:
    * split tokens on whitespace
    * treat quoted strings as a single token
    * drop comments
    * handle escaped spaces and comment delimiters
    """
    ret = []
    escape = False
    quote = False
    tokbuf = ""
    ll = list(line)
    while len(ll) > 0:
        c = ll.pop(0)
        if c.isspace():
            if not quote and not escape:
                # end of token
                if len(tokbuf) > 0:
                    ret.append(tokbuf)

                tokbuf = ""
            elif quote:
                # in quotes
                tokbuf += c
            elif escape:
                # escaped space
                tokbuf += c
                escape = False
            else:
                tokbuf = ""

            continue

        if c == '\\':
            escape = True
            continue
        elif c == '"':
            if not escape:
                if quote:
                    # end of quote
                    ret.append(tokbuf)
                    tokbuf = ""
                    quote = False
                    continue
                else:
                    # beginning of quote
                    quote = True
                    continue
        elif c == ';':
            if not escape:
                # comment 
                ret.append(tokbuf)
                tokbuf = ""
                break
            
        # normal character
        tokbuf += c
        escape = False

    if len(tokbuf.strip(" ").strip("\n")) > 0:
        ret.append(tokbuf)

    return ret


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
        if len(line) == 0:
            continue 

        line = _serialize(_tokenize_line(line))
        ret.append(line)

    return "\n".join(ret)


def _flatten(text):
    """
    Flatten the text:
    * make sure each record is on one line.
    * remove parenthesis 
    """
    lines = text.split("\n")

    # tokens: sequence of non-whitespace separated by '' where a newline was
    tokens = []
    for l in lines:
        if len(l) == 0:
            continue 

        l = l.replace("\t", " ")
        tokens += list(filter(lambda x: len(x) > 0, l.split(" "))) + ['']

    # find (...) and turn it into a single line ("capture" it)
    capturing = False
    captured = []

    flattened = []
    while len(tokens) > 0:
        tok = tokens.pop(0)
        if not capturing and len(tok) == 0:
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
        tokens = _tokenize_line(line)
        tokens_upper = [t.upper() for t in tokens]

        if "IN" in tokens_upper:
            tokens.remove("IN")
        elif "CS" in tokens_upper:
            tokens.remove("CS")
        elif "CH" in tokens_upper:
            tokens.remove("CH")
        elif "HS" in tokens_upper:
            tokens.remove("HS")

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
        
        if not tokens[0].startswith("$"):
            is_int = False
            try:
                int(tokens[0])
                is_int = True
            except ValueError:
                pass
            has_name = not is_int and tokens[0] not in SUPPORTED_RECORDS

            if has_name:
                previous_record_name = tokens[0]
            else:
                # add back the name
                tokens = [previous_record_name] + tokens

        ret.append(_serialize(tokens))

    return "\n".join(ret)


def _parse_line(parser, record_token, parsed_records):
    """
    Given the parser, capitalized list of a line's tokens, and the current set of records 
    parsed so far, parse it into a dictionary.

    Return the new set of parsed records.
    Raise an exception on error.
    """

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
        from azure.cli.core._util import CLIError
        raise CLIError('Unable to determine record type: {}'.format(' '.join(record_token)))
            
    # move the record type to the front of the token list so it will conform to argparse
    if record_type != parser.prog:
        raise IncorrectParserException
    record_token.remove(record_type)

    try:
        rr, unmatched = parser.parse_known_args(record_token)
        assert len(unmatched) == 0, "Unmatched fields: %s" % unmatched
    except (SystemExit, AssertionError, InvalidLineException) as ex:
        # invalid argument 
        raise InvalidLineException(' '.join(record_token))

    record_dict = rr.__dict__
    record_dict['type'] = record_type

    # remove emtpy fields
    for field in list(record_dict.keys()):
        if record_dict[field] is None:
            del record_dict[field]

    current_origin = record_dict.get('$origin', parsed_records.get('$origin', ''))

    # special record-specific fix-ups
    if record_type == 'PTR':
        record_dict['fullname'] = record_dict['name'] + '.' + current_origin


    for key in record_dict:
        try:
            if len(record_dict[key]) == 1:
                record_dict[key] = record_dict[key][0]
        except TypeError:
            continue
      
    if len(record_dict) > 0:
        if record_type.startswith("$"):
            # put the value directly
            parsed_records[record_type.lower()] = record_dict[record_type]
        else:
            parsed_records['records'].append(record_dict)

    return parsed_records


# LOCAL COPY
def _parse_lines(text, ignore_invalid=False):
    """
    Parse a zonefile into a dict.
    @text must be flattened--each record must be on one line.
    Also, all comments must be removed.
    """
    json_zone_file = defaultdict(list)
    record_lines = text.split("\n")
    parsers = _make_parser()

    for record_line in record_lines:
        parse_match = False
        for parser in parsers:
            record_token = _tokenize_line(record_line)
            try:
                json_zone_file = _parse_line(parser, record_token, json_zone_file)
                parse_match = True
                break
            except (InvalidLineException, IncorrectParserException):
                continue
        if not parse_match and not ignore_invalid:
            raise CLIError('Unable to parse: {}'.format(record_line))

    return json_zone_file


def parse_zone_file(text, ignore_invalid=False):
    """
    Parse a zonefile into a dict
    """
    text = _remove_comments(text)
    text = _flatten(text)
    text = _remove_class(text)
    text = _add_record_names(text)
    json_zone_file = _parse_lines(text, ignore_invalid=ignore_invalid)

    return json_zone_file

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import os
import textwrap
import shutil

import six
from whoosh.highlight import UppercaseFormatter, ContextFragmenter
from whoosh.qparser import MultifieldParser
from whoosh import index
from whoosh.fields import TEXT, Schema

from azure.cli.command_modules.find._gather_commands import build_command_table
import azure.cli.core.azlogging as azlogging
from azure.cli.core._environment import get_config_dir

logger = azlogging.get_az_logger(__name__)

INDEX_PATH = os.path.join(get_config_dir(), 'search_index')

schema = Schema(
    cmd_name=TEXT(stored=True),
    short_summary=TEXT(stored=True),
    long_summary=TEXT(stored=True),
    examples=TEXT(stored=True))


def _cli_index_corpus():
    return build_command_table()


def _index_help():
    ix = index.open_dir(INDEX_PATH)
    writer = ix.writer()
    for cmd, document in list(_cli_index_corpus().items()):
        writer.add_document(
            cmd_name=six.u(cmd),
            short_summary=six.u(document.get('short-summary', '')),
            long_summary=six.u(document.get('long-summary', '')),
            examples=six.u(document.get('examples', ''))
        )
    writer.commit()


def _remove_index():
    if os.path.exists(INDEX_PATH):
        shutil.rmtree(INDEX_PATH)


def _create_index():
    _remove_index()
    os.mkdir(INDEX_PATH)
    index.create_in(INDEX_PATH, schema)
    _index_help()


def _ensure_index():
    if not os.path.exists(INDEX_PATH):
        _create_index()


def _get_index():
    _ensure_index()
    return index.open_dir(INDEX_PATH)


def _print_hit(hit):
    def print_para(field):
        if field not in hit:
            print(hit)
        print(textwrap.fill(
            hit[field],
            initial_indent='    ',
            subsequent_indent='    '))

    print('`az {0}`'.format(hit['cmd_name']))
    print_para('short_summary')
    if hit['long_summary']:
        print_para('long_summary')
    print('')


def find(criteria, reindex=False):
    """
    Search for Azure CLI commands
    :param str criteria: Query text to search for.
    :param bool reindex: Clear the current index and reindex the command modules.
    :return:
    :rtype: None
    """
    if reindex:
        _create_index()

    ix = _get_index()
    qp = MultifieldParser(
        ['cmd_name', 'short_summary', 'long_summary', 'examples'],
        schema=schema
    )

    if 'OR' in criteria or 'AND' in criteria:
        # looks more advanced, let's trust them to make a great query
        q = qp.parse(" ".join(criteria))
    else:
        # let's help out with some OR's to provide a less restrictive search
        q = qp.parse(" OR ".join(criteria))

    with ix.searcher() as searcher:
        results = searcher.search(q)
        results.fragmenter = ContextFragmenter(maxchars=300, surround=200)
        results.formatter = UppercaseFormatter()
        for hit in results:
            _print_hit(hit)

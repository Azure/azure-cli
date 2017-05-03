# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import os
import textwrap
import shutil

import re
import six

from azure.cli.command_modules.find._gather_commands import build_command_table
import azure.cli.core.azlogging as azlogging
from azure.cli.core._environment import get_config_dir

logger = azlogging.get_az_logger(__name__)

INDEX_DIR_PREFIX = 'search_index'
INDEX_VERSION = 'v1'
INDEX_PATH = os.path.join(get_config_dir(), '{}_{}'.format(INDEX_DIR_PREFIX, INDEX_VERSION))


def _get_schema():
    from whoosh.fields import TEXT, Schema
    from whoosh.analysis import StemmingAnalyzer
    stem_ana = StemmingAnalyzer()
    return Schema(
        cmd_name=TEXT(stored=True, analyzer=stem_ana, field_boost=1.3),
        short_summary=TEXT(stored=True, analyzer=stem_ana),
        long_summary=TEXT(stored=True, analyzer=stem_ana),
        examples=TEXT(stored=True, analyzer=stem_ana))


def _cli_index_corpus():
    return build_command_table()


def _index_help():
    from whoosh import index
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


def _purge():
    for f in os.listdir(get_config_dir()):
        if re.search("^{}_*".format(INDEX_DIR_PREFIX), f):
            shutil.rmtree(os.path.join(get_config_dir(), f))


def _create_index():
    from whoosh import index
    _purge()
    os.mkdir(INDEX_PATH)
    index.create_in(INDEX_PATH, _get_schema())
    _index_help()


def _ensure_index():
    if not os.path.exists(INDEX_PATH):
        _create_index()


def _get_index():
    from whoosh import index
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
    from whoosh.qparser import MultifieldParser
    if reindex:
        _create_index()

    try:
        ix = _get_index()
    except ValueError:
        # got a pickle error because the index was written by a different python version
        # recreate the index and proceed
        _create_index()
        ix = _get_index()

    qp = MultifieldParser(
        ['cmd_name', 'short_summary', 'long_summary', 'examples'],
        schema=_get_schema()
    )

    if 'OR' in criteria or 'AND' in criteria:
        # looks more advanced, let's trust them to make a great query
        q = qp.parse(" ".join(criteria))
    else:
        # let's help out with some OR's to provide a less restrictive search
        expanded_query = " OR ".join(criteria) + " OR '{}'".format(criteria)
        q = qp.parse(expanded_query)

    with ix.searcher() as searcher:
        from whoosh.highlight import UppercaseFormatter, ContextFragmenter
        results = searcher.search(q)
        results.fragmenter = ContextFragmenter(maxchars=300, surround=200)
        results.formatter = UppercaseFormatter()
        for hit in results:
            _print_hit(hit)

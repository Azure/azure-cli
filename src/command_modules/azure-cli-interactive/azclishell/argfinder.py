# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from argcomplete import CompletionFinder
from argcomplete.compat import USING_PYTHON2, ensure_bytes


class ArgsFinder(CompletionFinder):
    """ gets the parsed args """
    def __init__(self, parser, outstream=None):
        super(ArgsFinder, self).__init__(parser)
        self.outstream = outstream

    def get_parsed_args(self, comp_words):
        """ gets the parsed args from a patched parser """
        active_parsers = self._patch_argument_parser()

        parsed_args = argparse.Namespace()

        self.completing = True
        if USING_PYTHON2:
            # Python 2 argparse only properly works with byte strings.
            comp_words = [ensure_bytes(word) for word in comp_words]

        try:
            active_parsers[0].parse_known_args(comp_words, namespace=parsed_args)
        except BaseException:
            pass

        self.completing = False
        return parsed_args

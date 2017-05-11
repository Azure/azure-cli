# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import unittest
import six
import sys

from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion

from azclishell.__main__ import AZCOMPLETER
# from azure.cli.testsdk import JMESPathCheck as JMESPathCheckV2
# from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
# from azure.cli.testsdk.vcr_test_base import (ResourceGroupVCRTestBase,
#                                              JMESPathCheck, NoneCheck)


class DynamicShellCompletionsTest(unittest.TestCase):


    def test_mute_parse(self):
        """ tests dynamic completions """
        completer = AZCOMPLETER

        doc_before = Document(u'vm show -g ')
        doc = Document(u'vm show -g ')

        stream = six.StringIO()
        sys.stderr = stream
        completer.argsfinder.set_outstream(stream)
        gen = completer.get_completions(doc, None)
        # args = completer.argsfinder.get_parsed_args(['this', 'is', 'world'])
        print(stream.getvalue())
        self.assertTrue(stream.getvalue() == '')

        # self.assertEqual(six.next(gen), Completion(''))
        # self.assertEqual(six.next(gen), Completion(self.group2))

        # doc = Document(u'vm show -g group2 -n ')
        # gen = completer.get_completions(doc, None)
        # with self.assertRaises(StopIteration):
        #     six.next(gen)

        # doc = Document(u'vm show -g group1 -n ')
        # gen = completer.get_completions(doc, None)

        # self.assertEqual(six.next(gen), Completion(self.vm1))


if __name__ == '__main__':
    unittest.main()

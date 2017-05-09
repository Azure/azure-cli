# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import six

from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion

from azclishell.__main__ import AZCOMPLETER
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.vcr_test_base import ResourceGroupVCRTestBase


class DynamicShellCompletionsTest(ResourceGroupVCRTestBase):

    def init(self):
        self.completer = AZCOMPLETER

    def init_parse(self):
        self.group1 = 'group1'
        self.group2 = 'group2'
        self.cmd('group create --location westus --name {} --tags use=az-test'.format(
            self.group1
        ))
        self.cmd('group create --location westus --name {} --tags use=az-test'.format(
            self.group2
        ))
        self.vm1 = 'vm1'
        self.cmd('vm create -n {} -g {} --image UbuntuLTS'.format(
            self.vm1, self.group1
        ))

    def test_list_dynamic_completions(self):
        """ tests dynamic completions """
        self.init()
        self.init_parse()

        doc = Document(u'vm show -g group')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion(self.group1))
        self.assertEqual(six.next(gen), Completion(self.group2))

        doc = Document(u'vm show -g group2 -n ')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

        doc = Document(u'vm show -g group1 -n ')
        gen = self.completer.get_completions(doc, None)

        self.assertEqual(six.next(gen), Completion(self.vm1))

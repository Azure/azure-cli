# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
import mock
import unittest

from azure.cli.core.parser import IncorrectUsageError
from azure_devtools.scenario_tests.const import MOCKED_SUBSCRIPTION_ID
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, create_random_name, live_only, record_only
from azure.cli.core.util import get_file_json
from knack.util import CLIError


class LocalContextScenarioTest(ScenarioTest):

    def test_resource_group_with_local_context(self):
        self.kwargs.update({
            'group': 'test_local_context_group',
            'location': 'eastasia'
        })
        self.cmd('local-context on')
        self.cmd('group create -n {group} -l {location}', checks=[self.check('name', self.kwargs['group'])])
        self.cmd('group show', checks=[
            self.check('name', self.kwargs['group']),
            self.check('location', self.kwargs['location'])
        ])
        self.cmd('local-context off --yes')

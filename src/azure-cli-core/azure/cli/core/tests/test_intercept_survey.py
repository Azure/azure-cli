# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from unittest import mock

from azure.cli.core import intercept_survey


class TestInterceptSurvey(unittest.TestCase):
    def test_should_prompt_with_existing_utc_note(self):
        """Preserve scheduling for existing UTC notes stored without an offset.

        Past dates allow a prompt; future dates suppress it. This regression
        test also passes before the migration. Replacing utcnow() alone would
        compare a naive saved date with aware now(UTC) and raise TypeError,
        so the reader must attach UTC to the parsed date.
        Only the decision is checked, not prompt rendering or note creation.
        """
        cli = mock.Mock()
        cli.config.getboolean.return_value = True
        for timestamp, expected in [('2000-01-01T00:00:00', True), ('2999-01-01T00:00:00', False)]:
            with self.subTest(timestamp=timestamp):
                note = json.dumps({'next_prompt_time': timestamp})
                with mock.patch.object(intercept_survey.sys.stderr, 'isatty', return_value=True), \
                        mock.patch.object(intercept_survey.sys, 'argv', ['az', 'group', 'list']), \
                        mock.patch.object(intercept_survey.os.path, 'isfile', return_value=True), \
                        mock.patch('azure.cli.core.intercept_survey.open', mock.mock_open(read_data=note)):
                    self.assertEqual(intercept_survey.should_prompt(cli), expected)

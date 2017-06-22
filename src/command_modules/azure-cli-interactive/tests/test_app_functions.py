# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azclishell.app import space_examples, space_toolbar, validate_contains_query
PART_SCREEN_EXAMPLE = .3


class ShellFunctionsTest(unittest.TestCase):
    """ tests whether dump commands works """
    def __init__(self, *args, **kwargs):
        super(ShellFunctionsTest, self).__init__(*args, **kwargs)

    def test_space_toolbar(self):
        """ tests the toolbar spacing """

        pass

    def test_space_examples(self):
        """ tests the examples spacing """
        pass

    def test_validate_contains_query(self):
        """ tests whether the validation function knows if there is a query """
        pass


if __name__ == '__main__':
    unittest.main()

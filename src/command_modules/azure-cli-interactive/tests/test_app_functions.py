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

    def test_space_examples(self):
        """ tests the examples spacing """
        up_down_text = ' CTRL+Y (^) CTRL+N (v)'
        loe1 = [[]]
        row1 = 0
        section1 = 1
        self.assertEqual(space_examples(loe1, row1, section1), up_down_text)

        loe1 = [['start', 'end']]
        row1 = 0
        section1 = 1
        self.assertEqual(space_examples(loe1, row1, section1), '[1] startend' + up_down_text)

        loe1 = [['start', 'end\n']]
        row1 = 1
        section1 = 1
        self.assertEqual(space_examples(loe1, row1, section1), '[1] startend\n' + up_down_text)

        loe1 = [['start', 'end\n'], ['second', ' friend\n']]
        row1 = 4
        section1 = 1
        self.assertEqual(
            space_examples(loe1, row1, section1), '[1] startend\n\n' + '1/2' + up_down_text)

        loe1 = [['start', 'end\n'], ['second', ' friend\n']]
        row1 = 4
        section1 = 2
        self.assertEqual(
            space_examples(loe1, row1, section1),
            '[2] second friend\n\n' + '\n2/2' + up_down_text)

    def test_space_toolbar(self):
        """ tests the toolbar spacing """
        setting1 = []
        empty_space1 = ''

        settings, empty_space = space_toolbar(setting1, empty_space1)
        self.assertEqual(settings, '')
        self.assertEqual(empty_space, '')

        setting1 = ['friendship', ]
        empty_space1 = ' ' * 15

        settings, empty_space = space_toolbar(setting1, empty_space1)
        self.assertEqual(settings, 'friendship')
        self.assertTrue(len(empty_space) == 4)

        setting1 = ['friendship', 'and MORE']
        empty_space1 = ' ' * 20

        settings, empty_space = space_toolbar(setting1, empty_space1)
        self.assertEqual(settings, 'friendship  and MORE')
        self.assertEqual(empty_space, '')

    def test_validate_contains_query(self):
        """ tests whether the validation function knows if there is a query """
        args1 = []
        symbol1 = '?'
        self.assertFalse(validate_contains_query(args1, symbol1))

        args1 = ['vm', 'create', '-g=?[].group']
        self.assertTrue(validate_contains_query(args1, symbol1))

        args1 = ['hello', 'alexander', '--groups=?[?group == cj]']
        self.assertTrue(validate_contains_query(args1, symbol1))

        args1 = ['happiness', 'is', '-g', '?everything']
        self.assertTrue(validate_contains_query(args1, symbol1))

        args1 = ['happiness', 'is', '--query', '[?friends == me]']
        self.assertFalse(validate_contains_query(args1, symbol1))

        args1 = ['?hello']
        self.assertTrue(validate_contains_query(args1, symbol1))


if __name__ == '__main__':
    unittest.main()

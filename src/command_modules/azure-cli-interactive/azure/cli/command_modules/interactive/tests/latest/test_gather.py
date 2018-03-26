# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.command_modules.interactive.azclishell.gather_commands import add_new_lines as nl


class GatherTest(unittest.TestCase):
    def test_add_new_lines(self):
        phrase1 = "Hello World"
        phrase2 = "HEllO"
        self.assertEqual("Hello \nWorld\n", nl(phrase1, 5, 1))
        self.assertEqual("Hello World\n", nl(phrase1, 7, 4))
        self.assertEqual("HE\nll\nO\n", nl(phrase2, 2, 0))
        self.assertEqual("HEllO\n", nl(phrase2, 20, 0))
        self.assertEqual("\n", nl("", 20, 0))

        phrase4 = "To be, or not to be--that is the question:\
            Whether 'tis nobler in the mind to suffer\
            The slings and arrows of outrageous fortune\
            Or to take arms against a sea of troubles\
            And by opposing end them. To die, to sleep--\
            No more--and by a sleep to say we end\
            The heartache, and the thousand natural shocks\
            That flesh is heir to. 'Tis a consummation\
            Devoutly to be wished. To die, to sleep--\
            To sleep--perchance to dream: ay, there's the rub,\
            For in that sleep of death what dreams may come\
            When we have shuffled off this mortal coil,\
            Must give us pause"
        long_phrase = nl(phrase4, 20, 4)
        self.assertTrue(len(long_phrase) > len(phrase4))
        for word in long_phrase.split('\n'):
            self.assertTrue(len(word) <= 25)
            if word != long_phrase.split('\n')[-2] and word != long_phrase.split('\n')[-1]:
                self.assertTrue(len(word) >= 20)

        phrase3 = "This is his face, his face: his face is gone."
        self.assertEqual(
            "This \nis hi\ns fac\ne, hi\ns fac\ne: hi\ns fac\ne is \ngone.\n",
            nl(phrase3, 3, 2)
        )
        self.assertEqual(
            "This is \nhis fac\ne, his \nface: h\nis face \nis gone\n.\n",
            nl(phrase3, 5, 2)
        )
        self.assertEqual(
            "This \nis hi\ns fa\nce, \nhis \nface\n: hi\ns fa\nce i\ns go\nne.\n",
            nl(phrase3, 4, 0)
        )
        self.assertEqual(
            "This \nis \nhis \nface, \nhis \nface: \nhis \nface \nis \ngone.\n",
            nl(phrase3, 1, tolerance=6)
        )


if __name__ == '__main__':
    unittest.main()

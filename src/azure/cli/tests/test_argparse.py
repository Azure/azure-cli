try:
    # on Python2, we like to use the module "StringIO" rather "io" so to 
    # avoid "print" errors like: TypeError: string argument expected, got 'str'
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

import unittest

from azure.cli._argparse import ArgumentParser, IncorrectUsageError
from azure.cli._logging import logger
import logging
import azure.cli._util as util

class Test_argparse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def test_nouns(self):
        p = ArgumentParser('test')
        res = [False, False, False]
        def set_n1(a, b): res[0] = True
        def set_n2(a, b): res[1] = True
        def set_n3(a, b): res[2] = True
        p.add_command(set_n1, 'n1')
        p.add_command(set_n2, 'n1 n2')
        p.add_command(set_n3, 'n1 n2 n3')

        p.execute('n1 n2 n3'.split())
        self.assertSequenceEqual(res, (False, False, True))
        p.execute('n1'.split())
        self.assertSequenceEqual(res, (True, False, True))
        res[0] = False
        p.execute('n1 n2'.split())
        self.assertSequenceEqual(res, (False, True, True))

    def test_args(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b), 'n1', args=[('--arg -a', '', False), ('-b <v>', '', False)])

        cmd_result = p.execute('n1 -a x'.split())
        res, other = cmd_result.result
        self.assertTrue(res.arg)
        self.assertSequenceEqual(res.positional, ['x'])

        # Should recognize args with alternate prefix
        cmd_result = p.execute('n1 /a'.split())
        res, other = cmd_result.result
        self.assertTrue(res.arg)
        cmd_result = p.execute('n1 /arg'.split())
        res, other = cmd_result.result
        self.assertTrue(res.arg)

        # Should not recognize "------a"
        cmd_result = p.execute('n1 ------a'.split())
        res, other = cmd_result.result
        self.assertNotIn('arg', res)
        # First two '--' match, so '----a' is added to dict
        self.assertIn('----a', other)

        cmd_result = p.execute('n1 -a:x'.split())
        res = cmd_result.result
        self.assertIsNone(res)

        cmd_result = p.execute('n1 -b -a x'.split())
        res, other = cmd_result.result
        self.assertEqual(res.b, '-a')
        self.assertSequenceEqual(res.positional, ['x'])
        self.assertRaises(IncorrectUsageError, lambda: res.arg)

        cmd_result = p.execute('n1 -b:-a x'.split())
        res, other = cmd_result.result
        self.assertEqual(res.b, '-a')
        self.assertSequenceEqual(res.positional, ['x'])
        self.assertRaises(IncorrectUsageError, lambda: res.arg)

    def test_unexpected_args(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b), 'n1', args=[('-a', '', False)])

        cmd_result = p.execute('n1 -b=2'.split())
        res, other = cmd_result.result
        self.assertFalse(res)
        self.assertEqual('2', other.b)

        cmd_result = p.execute('n1 -b.c.d=2'.split())
        res, other = cmd_result.result
        self.assertFalse(res)
        self.assertEqual('2', other.b.c.d)

        cmd_result = p.execute('n1 -b.c.d 2 -b.c.e:3'.split())
        res, other = cmd_result.result
        self.assertFalse(res)
        self.assertEqual('2', other.b.c.d)
        self.assertEqual('3', other.b.c.e)

    def test_required_args(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b), 'n1', args=[('--arg -a', '', True), ('-b <v>', '', False)])

        cmd_result = p.execute('n1 -a x'.split())
        res, other = cmd_result.result
        self.assertTrue(res.arg)
        self.assertSequenceEqual(res.positional, ['x'])

        self.assertIsNone(p.execute('n1 -b x'.split()).result)

    def test_args_completion(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b), 'n1', args=[('--arg -a', '', True), ('-b <v>', '', False)])
        io = StringIO()

        p.execute('n1 - --complete'.split(), 
                               show_usage=False,
                               show_completions=True,
                               out=io)
        candidates = util.normalize_newlines(io.getvalue())
        self.assertEqual(candidates, '--arg\n-a\n-b\n')

        io = StringIO()
        p.execute('n1 --a --complete'.split(), 
                               show_usage=False,
                               out=io)
        candidates = util.normalize_newlines(io.getvalue())
        self.assertEqual(candidates, '--arg\n')

        io = StringIO()
        p.execute('n --a --complete'.split(), 
                               show_usage=False,
                               show_completions=True,
                               out=io)
        candidates = util.normalize_newlines(io.getvalue())
        self.assertEqual(candidates, 'n1\n')

    def test_specify_output_format(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b), 'n1', args=[('--arg -a', '', True), ('-b <v>', '', False)])

        cmd_result = p.execute('n1 -a x'.split())
        self.assertEqual(cmd_result.output_format, None)

        cmd_result = p.execute('n1 -a x --output json'.split())
        self.assertEqual(cmd_result.output_format, 'json')

        cmd_result = p.execute('n1 -a x --output table'.split())
        self.assertEqual(cmd_result.output_format, 'table')

        cmd_result = p.execute('n1 -a x --output text'.split())
        self.assertEqual(cmd_result.output_format, 'text')

        # Invalid format
        cmd_result = p.execute('n1 -a x --output unknown'.split())
        self.assertEqual(cmd_result.output_format, None)

        # Invalid format
        cmd_result = p.execute('n1 -a x --output'.split())
        self.assertEqual(cmd_result.output_format, None)

if __name__ == '__main__':
    unittest.main()

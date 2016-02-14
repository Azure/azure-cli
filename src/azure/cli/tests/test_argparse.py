import azure.cli.main
import unittest

from azure.cli._argparse import ArgumentParser, _iter_args, IncorrectUsageError

class Test_argparse(unittest.TestCase):
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
        p.add_command(lambda a, b: (a, b), 'n1', args=[('--arg -a', ''), ('-b <v>', '')])

        res, other = p.execute('n1 -a x'.split())
        self.assertTrue(res.arg)
        self.assertSequenceEqual(res.positional, ['x'])

        res, other = p.execute('n1 -a:x'.split())
        self.assertTrue(res.arg)
        self.assertSequenceEqual(res.positional, ['x'])

        res, other = p.execute('n1 -b -a x'.split())
        self.assertEquals(res.b, '-a')
        self.assertSequenceEqual(res.positional, ['x'])
        self.assertRaises(IncorrectUsageError, lambda: res.arg)

        res, other = p.execute('n1 -b:-a x'.split())
        self.assertEquals(res.b, '-a')
        self.assertSequenceEqual(res.positional, ['x'])
        self.assertRaises(IncorrectUsageError, lambda: res.arg)

    def test_unexpected_args(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b), 'n1', args=[('-a', '')])

        res, other = p.execute('n1 -b=2'.split())
        self.assertFalse(res)
        self.assertEquals('2', other.b)

        res, other = p.execute('n1 -b.c.d=2'.split())
        self.assertFalse(res)
        self.assertEquals('2', other.b.c.d)

        res, other = p.execute('n1 -b.c.d 2 -b.c.e:3'.split())
        self.assertFalse(res)
        self.assertEquals('2', other.b.c.d)
        self.assertEquals('3', other.b.c.e)

if __name__ == '__main__':
    unittest.main()

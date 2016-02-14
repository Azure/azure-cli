import azure.cli.main
import unittest

from azure.cli._argparse import ArgumentParser, _iter_args, IncorrectUsageError

class Test_argparse(unittest.TestCase):
    def test_nouns(self):
        p = ArgumentParser('test')
        res = [False, False, False]
        def set_n1(a): res[0] = True
        def set_n2(a): res[1] = True
        def set_n3(a): res[2] = True
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
        res = []
        p.add_command(res.append, 'n1', args=[('-a', ''), ('-b <v>', '')])

        p.execute('n1 -a x'.split())
        self.assertTrue(res[-1].a)
        self.assertSequenceEqual(res[-1].positional, ['x'])

        p.execute('n1 -a:x'.split())
        self.assertTrue(res[-1].a)
        self.assertSequenceEqual(res[-1].positional, ['x'])

        p.execute('n1 -b -a x'.split())
        self.assertEquals(res[-1].b, '-a')
        self.assertSequenceEqual(res[-1].positional, ['x'])
        self.assertRaises(IncorrectUsageError, lambda: res[-1].a)

        p.execute('n1 -b:-a x'.split())
        self.assertEquals(res[-1].b, '-a')
        self.assertSequenceEqual(res[-1].positional, ['x'])
        self.assertRaises(IncorrectUsageError, lambda: res[-1].a)


if __name__ == '__main__':
    unittest.main()

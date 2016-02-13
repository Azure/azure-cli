from azure.cli._argparse import ArgumentParser, _iter_args, _split_argspec, IncorrectUsageError
import unittest

class Test_argparse(unittest.TestCase):
    def test_split_argspec(self):
        n, a, k = _split_argspec('noun <positional-value> --arg --name <value>'.split())
        self.assertSequenceEqual(n, ['noun'])
        self.assertSequenceEqual(a, ['positional-value'])
        self.assertDictEqual(k, {'arg': True, 'name': 'value'})

        n, a, k = _split_argspec('noun --name <value> <positional-value> --arg'.split())
        self.assertSequenceEqual(n, ['noun'])
        self.assertSequenceEqual(a, ['positional-value'])
        self.assertDictEqual(k, {'arg': True, 'name': 'value'})

    def test_nouns(self):
        p = ArgumentParser('test')
        res = [False, False, False]
        def set_n1(a): res[0] = True
        def set_n2(a): res[1] = True
        def set_n3(a): res[2] = True
        p.add_command('n1'.split(), set_n1)
        p.add_command('n1 n2'.split(), set_n2)
        p.add_command('n1 n2 n3'.split(), set_n3)

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
        p.add_command('n1 -a -b <v>'.split(), res.append)

        p.execute('n1 -a x'.split())
        self.assertTrue(res[-1].a)
        self.assertSequenceEqual(res[-1].positional, ['x'])

        p.execute('n1 -b -a x'.split())
        self.assertEquals(res[-1].b, '-a')
        self.assertSequenceEqual(res[-1].positional, ['x'])
        self.assertRaises(IncorrectUsageError, lambda: res[-1].a)

if __name__ == '__main__':
    unittest.main()

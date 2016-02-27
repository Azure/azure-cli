from .test_argparse import Test_argparse

from unittest import TestSuite
 
test_cases = [Test_argparse]

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for testclass in test_cases:
        tests = loader.loadTestsFromTestCase(testclass)
        suite.addTests(tests)
    return suite

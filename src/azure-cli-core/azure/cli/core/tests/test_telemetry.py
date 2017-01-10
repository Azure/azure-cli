# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Requires python nosetests


class TestExeption(Exception):
    pass


def test_suppress_one_exception():
    def _impl(exception_to_raise, exception_to_expect, fallback_return, expected_case):
        from azure.cli.core.telemetry import _suppress_one_exception

        @_suppress_one_exception(expected_exception=exception_to_expect,
                                 fallback_return=fallback_return)
        def _error_fn():
            if not exception_to_raise:
                return 'positive result'
            else:
                raise exception_to_raise()

        if not exception_to_raise:
            assert expected_case == 'case 1'
            try:
                assert _error_fn() == 'positive result'
            except:  # pylint: disable=bare-except
                assert False
        elif issubclass(exception_to_raise, exception_to_expect):
            assert expected_case == 'case 2'
            try:
                assert _error_fn() == fallback_return
            except:  # pylint: disable=bare-except
                assert False
        else:
            assert expected_case == 'case 3'
            try:
                _error_fn()
                assert False
            except Exception as ex:  # pylint: disable=broad-except
                assert isinstance(ex, exception_to_raise)
                assert not isinstance(ex, exception_to_expect)

    yield _impl, None, Exception, None, 'case 1'
    yield _impl, Exception, Exception, 'fallback', 'case 2'
    yield _impl, ValueError, ImportError, None, 'case 3'
    yield _impl, Exception, ImportError, None, 'case 3'
    yield _impl, ImportError, Exception, 'fallback', 'case 2'


def test_suppress_all_exceptions():
    def _impl(exception_to_raise, fallback_return):
        from azure.cli.core.telemetry import _suppress_all_exceptions

        @_suppress_all_exceptions(fallback_return=fallback_return)
        def _error_fn():
            if not exception_to_raise:
                return 'positive result'
            else:
                raise exception_to_raise()

        if not exception_to_raise:
            try:
                assert _error_fn() == 'positive result'
            except:  # pylint: disable=bare-except
                assert False
        else:
            try:
                assert _error_fn() == fallback_return
            except:  # pylint: disable=bare-except
                assert False

    yield _impl, Exception, 'fallback'
    yield _impl, Exception, None
    yield _impl, ImportError, 'fallback_for_import_error'
    yield _impl, None, None

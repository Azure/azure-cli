# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Requires python nosetests


class TestExeption(Exception):
    pass


def test_suppress_all_exceptions():
    def _impl(exception_to_raise, fallback_return):
        from azure.cli.core.decorators import suppress_all_exceptions

        @suppress_all_exceptions(fallback_return=fallback_return)
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

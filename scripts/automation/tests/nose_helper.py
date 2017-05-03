# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

# pylint: disable=too-many-arguments
def get_nose_runner(report_folder, parallel=True, process_timeout=600, process_restart=True,
                    xunit_report=False, exclude_integration=True):
    """Create a nose execution method"""

    def _run_nose(test_folders):
        import nose
        import os.path
        from six import StringIO
        import sys

        tempout = StringIO()
        original_stderr = sys.stderr
        sys.stderr = tempout

        if not report_folder \
                or not os.path.exists(report_folder) \
                or not os.path.isdir(report_folder):
            raise ValueError('Report folder {} does not exist'.format(report_folder))

        arguments = [__file__, '-v', '--nologcapture']
        if parallel:
            arguments += ['--processes=-1', '--process-timeout={}'.format(process_timeout)]
            if process_restart:
                arguments += ['--process-restartworker']

        if xunit_report:
            test_report = os.path.join(report_folder, 'nosetests-report.xml')
            arguments += ['--with-xunit', '--xunit-file', test_report]
        else:
            test_report = ''

        if exclude_integration:
            arguments += ['--ignore-files=integration*']

        debug_file = os.path.join(report_folder, 'test-debug.log')
        arguments += ['--debug-log={}'.format(debug_file)]
        arguments += ['--nologcapture']
        arguments.extend(test_folders)
        result = nose.run(argv=arguments)

        sys.stderr = original_stderr
        output = tempout.getvalue()
        tempout.close()

        print(output, file=sys.stderr)

        failed_tests = []
        for line in output.splitlines():
            if line.endswith('... ERROR') or line.endswith('... FAIL'):
                failed_tests.append(line)

        return result, test_report, failed_tests

    return _run_nose

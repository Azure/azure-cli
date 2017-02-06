# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime


# pylint: disable=too-many-arguments
def get_nose_runner(report_folder, parallel=True, process_timeout=600, process_restart=True,
                    xunit_report=False, exclude_integration=True, code_coverage=False):
    """Create a nose execution method"""

    def _run_nose(name, working_dir):
        import nose
        import os.path

        if not report_folder \
                or not os.path.exists(report_folder) \
                or not os.path.isdir(report_folder):
            raise ValueError('Report folder {} does not exist'.format(report_folder))

        arguments = ['-w', working_dir, '-v']
        if parallel:
            arguments += ['--processes=-1', '--process-timeout={}'.format(process_timeout)]
            if process_restart:
                arguments += ['--process-restartworker']

        if xunit_report:
            log_file = os.path.join(report_folder, name + '-report.xml')
            arguments += ['--with-xunit', '--xunit-file', log_file]
        else:
            log_file = ''

        if exclude_integration:
            arguments += ['--ignore-files=integration*']

        if code_coverage:
            # coverage_config = os.path.join(os.path.dirname(__file__), '.coveragerc')
            # coverage_folder = os.path.join(report_folder, 'code_coverage')
            # make_dirs(coverage_folder)
            # if not os.path.exists(coverage_folder) or not os.path.isdir(coverage_folder):
            #     raise Exception('Failed to create folder {} for code coverage result'
            #                     .format(coverage_folder))

            arguments += ['--with-coverage']

        debug_file = os.path.join(report_folder, name + '-debug.log')
        arguments += ['--debug-log={}'.format(debug_file)]

        print('\n')
        print('<<< Run {} >>>'.format(name))
        start = datetime.now()
        result = nose.run(argv=arguments)
        end = datetime.now()

        return result, start, end, log_file

    return _run_nose

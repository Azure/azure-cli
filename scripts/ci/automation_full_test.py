#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azdev.utilities import get_path_table
import json
import logging
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

# sys.argv is passed by
# .azure-pipelines/templates/automation_test.yml in section `Running full test`
# scripts/regression_test/regression_test.yml in section "Rerun tests"
instance_cnt = int(sys.argv[1]) if len(sys.argv) >= 2 else 1
instance_idx = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
profile = sys.argv[3] if len(sys.argv) >= 4 else 'latest'
serial_modules = sys.argv[4].split() if len(sys.argv) >= 5 else []
fix_failure_tests = sys.argv[5].lower() == 'true' if len(sys.argv) >= 6 else False
target = sys.argv[6].lower() if len(sys.argv) >= 7 else 'cli'
working_directory = os.getenv('BUILD_SOURCESDIRECTORY') if target == 'cli' else f"{os.getenv('BUILD_SOURCESDIRECTORY')}/azure-cli-extensions"
azdev_test_result_dir = os.path.expanduser("~/.azdev/env_config/mnt/vss/_work/1/s/env")
python_version = os.environ.get('PYTHON_VERSION', None)
job_name = os.environ.get('JOB_NAME', None)
pull_request_number = os.environ.get('PULL_REQUEST_NUMBER', None)
enable_pipeline_result = bool(job_name and python_version)
unique_job_name = ' '.join([job_name, python_version, profile, str(instance_idx)]) if enable_pipeline_result else None
enable_traceback = True if (os.environ.get('ENABLE_TRACEBACK') is not None and os.environ.get('ENABLE_TRACEBACK').lower() == 'true') else False
cli_jobs = {
            'acr': 45,
            'acs': 62,
            'advisor': 18,
            'ams': 136,
            'apim': 30,
            'appconfig': 41,
            'appservice': 150,  # series
            # 'appservice': 157,  # parallel
            'aro': 33,
            'backup': 76,
            'batch': 21,
            'batchai': 24,
            'billing': 21,
            'botservice': 25,  # series
            # 'botservice': 28,  # parallel
            'cdn': 36,
            'cloud': 18,  # series
            # 'cloud': 22,  # parallel
            'cognitiveservices': 24,
            'config': 21,
            'configure': 17,
            'consumption': 21,
            'container': 19,
            'cosmosdb': 45,
            'databoxedge': 25,
            'dla': 19,
            'dls': 22,
            'dms': 22,
            'eventgrid': 24,
            'eventhubs': 24,
            'extension': 0,
            'feedback': 31,
            'find': 22,
            'hdinsight': 34,
            'identity': 18,
            'interactive': 18,
            'iot': 57,
            'keyvault': 39,
            'kusto': 23,
            'lab': 19,
            'managedservices': 18,
            'maps': 19,
            'marketplaceordering': 18,
            'monitor': 66,
            'natgateway': 22,
            'netappfiles': 48,
            'network': 364,  # series
            # 'network': 182,  # parallel
            'policyinsights': 20,
            'privatedns': 29,
            'profile': 20,
            'rdbms': 89,
            'redis': 31,
            'relay': 22,
            'resource': 101,
            'role': 38,
            'search': 34,
            'security': 23,
            'servicebus': 24,
            'serviceconnector': 56,
            'servicefabric': 49,
            'signalr': 20,
            'sql': 117,
            'sqlvm': 31,
            'storage': 108,
            'synapse': 45,
            'util': 18,
            'vm': 313,
            'azure-cli': 16,
            'azure-cli-core': 26,
            'azure-cli-telemetry': 18,
            'azure-cli-testsdk': 20,
        }

extension_jobs = {
    'account': 23,
    'acrtransfer': 20,
    'ad': 21,
    'aem': 50,
    'ai-examples': 30,
    'aks-preview': 118,
    'alertsmanagement': 20,
    'alias': 21,
    'amg': 26,
    'application-insights': 30,
    'appservice-kube': 21,
    'attestation': 21,
    'authV2': 24,
    'automation': 24,
    'azure-firewall': 121,
    'blockchain': 20,
    'blueprint': 21,
    'change-analysis': 20,
    'cli-translator': 22,
    'cloudservice': 20,
    'communication': 32,
    'confidentialledger': 21,
    'confluent': 21,
    'connectedk8s': 24,
    'connectedmachine': 26,
    'connectedvmware': 26,
    'connection-monitor-preview': 28,
    'containerapp': 228,
    'cosmosdb-preview': 58,
    'costmanagement': 25,
    'custom-providers': 27,
    'databox': 22,
    'databricks': 25,
    'datadog': 22,
    'datafactory': 27,
    'datamigration': 25,
    'dataprotection': 30,
    'datashare': 23,
    'db-up': 25,
    'desktopvirtualization': 23,
    'dev-spaces': 20,
    'diskpool': 23,
    'dms-preview': 23,
    'dnc': 21,
    'dns-resolver': 30,
    'edgeorder': 24,
    'elastic-san': 26,
    'elastic': 24,
    'eventgrid': 21,
    'express-route-cross-connection': 22,
    'fleet': 24,
    'fluid-relay': 23,
    'footprint': 22,
    'front-door': 36,
    'functionapp': 21,
    'guestconfig': 20,
    'hack': 28,
    'hardware-security-modules': 30,
    'healthbot': 23,
    'healthcareapis': 30,
    'hpc-cache': 24,
    'image-copy': 21,
    'image-gallery': 24,
    'import-export': 22,
    'init': 22,
    'interactive': 23,
    'internet-analyzer': 27,
    'ip-group': 24,
    'k8s-configuration': 26,
    'k8s-extension': 22,
    'kusto': 25,
    'log-analytics-solution': 22,
    'log-analytics': 23,
    'logic': 23,
    'logz': 23,
    'maintenance': 23,
    'managementpartner': 25,
    'mesh': 31,
    'mixed-reality': 32,
    'monitor-control-service': 25,
    'netappfiles-preview': 54,
    'network-manager': 37,
    'next': 25,
    'nginx': 25,
    'notification-hub': 23,
    'offazure': 25,
    'orbital': 26,
    'peering': 19,
    'portal': 21,
    'powerbidedicated': 22,
    'providerhub': 23,
    'purview': 24,
    'quantum': 38,
    'quota': 25,
    'rdbms-connect': 42,
    'redisenterprise': 26,
    'reservation': 34,
    'resource-graph': 23,
    'resource-mover': 28,
    'scenario-guide': 22,
    'scheduled-query': 24,
    'scvmm': 27,
    'securityinsight': 51,
    'serial-console': 24,
    'spring-cloud': 341,
    'spring': 345,
    'ssh': 24,
    'stack-hci': 25,
    'storage-blob-preview': 59,
    'storage-preview': 42,
    'storagesync': 25,
    'stream-analytics': 49,
    'subscription': 22,
    'support': 41,
    'swiftlet': 22,
    'timeseriesinsights': 24,
    'traffic-collector': 26,
    'virtual-network-tap': 20,
    'virtual-wan': 70,
    'vm-repair': 22,
    'vmware': 38,
    'webapp': 22,
    'webpubsub': 23,
}


def run_command(cmd, check_return_code=False):
    error_flag = False
    logger.info(cmd)
    try:
        out = subprocess.run(cmd, check=True)
        if check_return_code and out.returncode:
            raise RuntimeError(f"{cmd} failed")
    except subprocess.CalledProcessError:
        error_flag = True
    return error_flag


def install_extension(extension_module):
    try:
        cmd = ['azdev', 'extension', 'add', extension_module]
        error_flag = run_command(cmd, check_return_code=True)
    except Exception:
        error_flag = True

    return error_flag


def remove_extension(extension_module):
    try:
        cmd = ['azdev', 'extension', 'remove', extension_module]
        error_flag = run_command(cmd, check_return_code=True)
    except Exception:
        error_flag = True

    return error_flag


def rerun_setup(cli_repo_path, extension_repo_path):
    try:
        if extension_repo_path:
            cmd = ['azdev', 'setup', '-c', cli_repo_path, '-r', extension_repo_path, '--debug']
        else:
            cmd = ['azdev', 'setup', '-c', cli_repo_path, '--debug']
        error_flag = run_command(cmd, check_return_code=True)
    except Exception:
        error_flag = True

    return error_flag


def git_restore(file_path):
    if not file_path:
        return
    logger.info(f"git restore *{file_path}")
    out = subprocess.Popen(["git", "restore", "*" + file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, err = out.communicate()
    if stdout:
        logger.info(stdout)
    if err:
        logger.warning(err)


def git_push(message, modules=[]):
    out = subprocess.Popen(["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = out.communicate()
    if "nothing to commit, working tree clean" in str(stdout):
        return
    try:
        if modules:
            build_id = os.getenv("BUILD_BUILDID")
            module_name = '_'.join(modules)
            branch_name = f"regression_test_{build_id}_{module_name}"
            run_command(["git", "checkout", "-b", branch_name])
            run_command(["git", "push", "--set-upstream", "azclibot", branch_name], check_return_code=True)
        run_command(["git", "add", "src/*"], check_return_code=True)
        run_command(["git", "commit", "-m", message], check_return_code=True)
    except RuntimeError as ex:
        raise ex
    retry = 3
    while retry >= 0:
        try:
            run_command(["git", "fetch"], check_return_code=True)
            run_command(["git", "pull", "--rebase"], check_return_code=True)
            run_command(["git", "push"], check_return_code=True)

            logger.info("git push all recording files")
            break
        except RuntimeError as ex:
            if retry == 0:
                raise ex
            retry -= 1
            time.sleep(10)


def get_failed_tests(test_result_fp):
    tree = ET.parse(test_result_fp)
    root = tree.getroot()
    failed_tests = {}
    for testsuite in root:
        for testcase in testsuite:
            # Collect failed tests
            failures = testcase.findall('failure')
            if failures:
                logger.info(f"failed testcase attributes: {testcase.attrib}")
                test_case = testcase.attrib['name']
                test_case_class = testcase.attrib['classname'] + '.' + test_case
                recording_folder = os.path.join(os.path.dirname(testcase.attrib['file']), 'recordings')
                failed_tests[test_case_class] = os.path.join(recording_folder, test_case + '.yaml')
    return failed_tests


def process_test(cmd, azdev_test_result_fp, live_rerun=False, modules=[]):
    error_flag = run_command(cmd)
    if not error_flag or not live_rerun:
        return error_flag
    if not os.path.exists(azdev_test_result_fp):
        logger.warning(f"{cmd} failed directly. The related module can't work!")
        if modules:
            test_results_error_modules_fp = os.path.join(azdev_test_result_dir, f'test_results_error_modules_{instance_idx}.txt')
            with open(test_results_error_modules_fp, 'a') as fp:
                fp.write(','.join(modules)+"\n")
        return error_flag
    # drop the original `--pytest-args` and add new arguments
    cmd = cmd[:-2] + ['--lf', '--live', '--pytest-args', '-o junit_family=xunit1']
    error_flag = run_command(cmd)
    # restore original recording yaml file for failed test in live run
    if error_flag:
        failed_tests = get_failed_tests(azdev_test_result_fp)
        for (test, file) in failed_tests.items():
            git_restore(file)
            test_results_failure_tests_fp = os.path.join(azdev_test_result_dir, f'test_results_failure_tests_{instance_idx}.txt')
            with open(test_results_failure_tests_fp, 'a') as fp:
                fp.write(test + "\n")

    # save live run recording changes to git
    commit_message = f"Rerun tests from instance {instance_idx}. See {os.path.basename(azdev_test_result_fp)} for details"
    git_push(commit_message, modules=modules)
    return False


def build_pipeline_result():
    if profile == '2018-03-01-hybrid':
        selected_modules = ['keyvault', 'network', 'resource', 'storage', 'vm']
    elif profile == '2019-03-01-hybrid':
        selected_modules = ['databoxedge', 'iot', 'resource', 'storage', 'vm']
    elif profile == '2020-09-01-hybrid':
        selected_modules = ['acr', 'acs', 'databoxedge', 'iot', 'keyvault', 'storage', 'vm']
    else:
        selected_modules = get_path_table()['mod']
        excluded_modules = ['extension', 'interactive']
        for m in excluded_modules:
            selected_modules.pop(m)
        selected_modules = list(selected_modules.keys())
    # add azure-cli-core, azure-cli-telemetry to selected_modules
    selected_modules += ['core', 'telemetry']
    pipeline_result = {
        # "Automation Full Test Python310 Profile Latest instance1"
        unique_job_name: {
            "Name": job_name,
            "Details": [
                {
                    "TestName": "AzureCLI-FullTest",
                    "Details": [
                        {
                            "Profile": profile,
                            "Details": [
                                {
                                    "PythonVersion": python_version,
                                    "Details": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    if pull_request_number != '$(System.PullRequest.PullRequestNumber)':
        pipeline_result['pull_request_number'] = pull_request_number

    for k in selected_modules:
        pipeline_result[unique_job_name]['Details'][0]['Details'][0]['Details'][0]['Details'].append({
            "Module": k,
            "Status": "Running",
            "Content": ""
        })
    return pipeline_result


def get_pipeline_result(test_result_fp, pipeline_result):
    tree = ET.parse(test_result_fp)
    root = tree.getroot()
    for testsuite in root:
        for testcase in testsuite:
            # ['azure', 'cli', 'command_modules', 'network', 'tests', 'latest', 'test_network_commands', 'NetworkNicScenarioTest']
            # ['src', 'azure-cli', 'azure', 'cli', 'command_modules', 'network', 'tests', 'hybrid_2018_03_01', 'test_dns_commands', 'DnsZoneImportTest']
            # ['src', 'azure-cli-core', 'azure', 'cli', 'core', 'tests', 'test_aaz_arg', 'TestAAZArg']
            # ['src', 'azure-cli-telemetry', 'azure', 'cli', 'telemetry', 'tests', 'test_records_collection', 'TestRecordsCollection']
            class_name = testcase.attrib['classname'].split('.')
            # classname="azure.cli.command_modules.network.tests"
            if class_name[2] == 'command_modules':
                module = class_name[3]
            # classname="azure.cli.core.tests"
            # classname="azure.cli.telemetry.tests"
            elif class_name[2] in ['core', 'telemetry']:
                module = class_name[2]
            # classname="src.azure-cli.azure.cli.command_modules.network.tests"
            elif class_name[4] == 'command_modules':
                module = class_name[5]
            # classname="src.azure-cli-core.azure.cli.core.tests"
            # classname="src.azure-cli-telemetry.azure.cli.telemetry.tests"
            elif class_name[1] in ['azure-cli-core', 'azure-cli-telemetry']:
                module = class_name[4]
            else:
                logger.error(f'unexpected class name: {class_name}')
                module = 'unknown'
            failures = testcase.findall('failure')
            if failures:
                # logger.info(f"failed testcase attributes: {testcase.attrib}")
                state = "Failed"
                test_case = testcase.attrib['name']
                line = testcase.attrib['file'] + ':' + testcase.attrib['line']
                # only get first failure
                for failure in failures:
                    message = failure.attrib['message'].replace('\n', '<br>').replace(' ', '&nbsp;')
                    break
                for i in pipeline_result[unique_job_name]['Details'][0]['Details'][0]['Details'][0]['Details']:
                    if i['Module'] == module:
                        i['Status'] = 'Failed'
                        # GitHub has a comment length limit of 65535, we must ensure that the length is less than 65535.
                        # The azure cli bot will also add extra html characters.
                        # So the number of characters cannot be accurately calculated.
                        # Using indent=4 is just a rough estimate.
                        if len(json.dumps(pipeline_result, indent=4)) + len(message) > 65535:
                            message = 'The error message is too long, please check the pipeline log for details.'
                        i['Content'] = build_markdown_content(state, test_case, message, line, i['Content'])
                        break
            else:
                for i in pipeline_result[unique_job_name]['Details'][0]['Details'][0]['Details'][0]['Details']:
                    if i['Module'] == module:
                        i['Status'] = 'Succeeded' if i['Status'] != 'Failed' else 'Failed'
                        break

    return pipeline_result


def build_markdown_content(state, test_case, message, line, content):
    if content == "":
        content = f'|Type|Test Case|Error Message|Line|\n|---|---|---|---|\n'
    content += f'|{state}|{test_case}|{message}|{line}|\n'
    return content


def save_pipeline_result(pipeline_result):
    # save pipeline result to file
    # /mnt/vss/.azdev/env_config/mnt/vss/_work/1/s/env/pipeline_result_3.8_latest_1.json
    filename = os.path.join(azdev_test_result_dir, f'pipeline_result_{python_version}_{profile}_{instance_idx}.json')
    with open(filename, 'w') as f:
        json.dump(pipeline_result, f, indent=4)
    logger.info(f"save pipeline result to file: {filename}")


class AutomaticScheduling(object):

    def __init__(self):
        """
        self.jobs: Record the test time of each module
        self.modules: All modules and core, ignore extensions
        self.serial_modules: All modules which need to execute in serial mode
        self.works: Record which modules each worker needs to test
        self.instance_cnt:
        The total number of concurrent automation full test pipeline instance with specify python version
        Because we share the vm pool with azure-sdk team, so we can't set the number of concurrency arbitrarily
        Best practice is to keep the number of concurrent tasks below 50
        If you set a larger number of concurrency, it will cause many instances to be in the waiting state
        And the network module has the largest number of test cases and can only be tested serially for now, so setting instance_cnt = 8 is sufficient
        Total concurrent number: AutomationTest20200901 * 3 + AutomationTest20190301 * 3 + AutomationTest20180301 * 3 + AutomationFullTest * 8 * 3 (python_version) = 33
        self.instance_idx:
        The index of concurrent automation full test pipeline instance with specify python version
        For example:
        instance_cnt = 8, instance_idx = 3: means we have 8 instances totally, and now we are scheduling modules on third instance
        instance_cnt = 1, instance_idx = 1: means we only have 1 instance, so we don't need to schedule modules
        """
        self.jobs = []
        self.modules = {}
        self.serial_modules = serial_modules
        self.works = []
        self.instance_cnt = instance_cnt
        self.instance_idx = instance_idx
        for i in range(self.instance_cnt):
            worker = {}
            self.works.append(worker)
        self.profile = profile

    def get_all_modules(self):
        result = get_path_table()
        # only get modules and core, ignore extensions
        result_mod = result['mod']
        result_core = result['core']

        # make sure the dictionary is in order, otherwise job assignments will be random.
        from collections import OrderedDict
        self.modules = OrderedDict(sorted((result_mod | result_core).items()))
        logger.info(json.dumps(self.modules, indent=2))

    def get_extension_modules(self):
        out = subprocess.Popen(['azdev', 'extension', 'list', '-o', 'tsv'], stdout=subprocess.PIPE)
        stdout = out.communicate()[0]
        if not stdout:
            raise RuntimeError("No extension detected")
        extensions = stdout.decode('UTF-8').split('\n')
        self.modules = {extension.split('\t')[1]: extension.split('\t')[2].strip('\r')
                        for extension in extensions if len(extension.split('\t')) > 2}
        logger.info(self.modules)

    def append_new_modules(self, jobs):
        # If add a new module, use average test time
        avg_cost = int(sum(jobs.values()) / len(jobs.values()))
        for module in self.modules:
            if module not in jobs.keys():
                jobs[module] = avg_cost
        # sort jobs by time cost (desc)
        self.jobs = sorted(jobs.items(), key=lambda item: -item[1])

    def get_worker(self):
        """
        Use greedy algorithm distribute jobs to each worker
        For each job, we assign it to the worker with the fewest jobs currently
        :return worker number
        """
        for idx, worker in enumerate(self.works):
            tmp_time = sum(worker.values()) if sum(worker.values()) else 0
            if idx == 0:
                worker_time = tmp_time
                worker_num = idx
            if tmp_time < worker_time:
                worker_time = tmp_time
                worker_num = idx
        return worker_num

    def get_instance_modules(self):
        # get modules which need to execute in the pipeline instance with specific index
        for k, v in self.jobs:
            idx = self.get_worker()
            self.works[idx][k] = v
        # instance_idx: 1~n, python list index: 0~n-1
        self.instance_idx -= 1
        logger.info(json.dumps(self.works, indent=2))
        return self.works[self.instance_idx]

    def run_instance_modules(self, instance_modules):
        # divide the modules that the current instance needs to execute into parallel or serial execution
        serial_error_flag = parallel_error_flag = False
        serial_tests = []
        parallel_tests = []
        for k, v in instance_modules.items():
            if k in self.serial_modules:
                serial_tests.append(k)
            else:
                parallel_tests.append(k)
        # Put the cloud module at the end of the serial execution
        # Since it will cause the test_get_docker_credentials test to fail
        # TODO: Find the root cause of the failure and modify the test code.
        if 'cloud' in serial_tests:
            serial_tests.remove('cloud')
            serial_tests.append('cloud')
        pipeline_result = build_pipeline_result() if enable_pipeline_result else None
        pytest_args = '-o junit_family=xunit1 --durations=10'
        if not enable_traceback:
            pytest_args += ' --tb=no'
        if parallel_tests:
            azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{python_version}_{profile}_{instance_idx}.parallel.xml")
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose'] + parallel_tests + \
                  ['--profile', f'{profile}', '--xml-path', azdev_test_result_fp, '--pytest-args', pytest_args]
            parallel_error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests)
            pipeline_result = get_pipeline_result(azdev_test_result_fp, pipeline_result) if enable_pipeline_result else None
        if serial_tests:
            azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{python_version}_{profile}_{instance_idx}.serial.xml")
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose', '--series'] + serial_tests + \
                  ['--profile', f'{profile}', '--xml-path', azdev_test_result_fp, '--pytest-args', pytest_args]
            serial_error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests)
            pipeline_result = get_pipeline_result(azdev_test_result_fp, pipeline_result) if enable_pipeline_result else None
        save_pipeline_result(pipeline_result) if enable_pipeline_result else None
        return serial_error_flag or parallel_error_flag

    def run_extension_instance_modules(self, instance_modules):
        global_error_flag = False
        for module, path in instance_modules.items():
            run_command(["git", "checkout", f"regression_test_{os.getenv('BUILD_BUILDID')}"], check_return_code=True)
            error_flag = install_extension(module)
            logger.info(f"Finish installing extension {module}, error_flag: {error_flag}")
            if not error_flag:
                azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{module}.xml")
                cmd = ['azdev', 'test', module, '--discover', '--no-exitfirst', '--verbose',
                       '--xml-path', azdev_test_result_fp, '--pytest-args', '"--durations=10"']
                error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests, modules=[module])
                logger.info(f"Finish testing extension {module}, error_flag: {error_flag}")
            remove_extension(module)
            logger.info(f"Finish removing extension {module}, error_flag: {error_flag}")
            if error_flag:
                rerun_setup(cli_repo_path=os.getenv('BUILD_SOURCESDIRECTORY'), extension_repo_path=working_directory)
            global_error_flag = global_error_flag or error_flag
        return global_error_flag


def main():
    logger.info("Start automation full test ...\n")
    autoscheduling = AutomaticScheduling()
    autoscheduling.get_all_modules()
    autoscheduling.append_new_modules(cli_jobs)
    instance_modules = autoscheduling.get_instance_modules()
    sys.exit(1) if autoscheduling.run_instance_modules(instance_modules) else sys.exit(0)


def extension_main():
    logger.info("Start extension automation full test ...\n")
    autoscheduling = AutomaticScheduling()
    autoscheduling.get_extension_modules()
    autoscheduling.append_new_modules(extension_jobs)
    instance_modules = autoscheduling.get_instance_modules()
    sys.exit(1) if autoscheduling.run_extension_instance_modules(instance_modules) else sys.exit(0)


if __name__ == '__main__':
    if target == 'cli':
        main()
    else:
        extension_main()

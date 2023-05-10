#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import os
import subprocess

from azdev.utilities.path import get_cli_repo_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

pull_request_number = os.environ.get('PULL_REQUEST_NUMBER', None)
base_meta_path = '/mnt/vss/_work/1/base_meta'
diff_meta_path = '/mnt/vss/_work/1/diff_meta'
output_path = '/mnt/vss/_work/1/output_meta'


def get_base_meta_files():
    cmd = ['azdev', 'command-change', 'meta-export', 'CLI', '--meta-output-path', base_meta_path]
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    print(out.stdout)


def get_diff_meta_files():
    # refs/remotes/pull/24765/merge
    target_branch = f'refs/remotes/pull/{pull_request_number}/merge'
    cmd = ['azdev', 'command-change', 'meta-export', '--src', 'dev', '--tgt', target_branch, '--repo', get_cli_repo_path(), '--meta-output-path', diff_meta_path]
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    print(out.stdout)


def meta_diff():
    cmd = ['git', 'checkout',  'dev']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    print(out.stdout)
    # list file in diff_meta_path
    # for each file, run follow command
    # cmd = ['azdev', 'command-change', 'meta-diff', '--base-meta-file', 'az_monitor_meta_before.json', '--diff-meta-file', 'az_monitor_meta_after.json', '--output-file', 'xxx', '--output-type', 'xxx']
    for file in os.listdir(diff_meta_path):
        if file.endswith('.json'):
            cmd = ['azdev', 'command-change', 'meta-diff', '--base-meta-file', os.path.join(base_meta_path, file), '--diff-meta-file', os.path.join(diff_meta_path, file), '--output-file', output_path]
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            print(out.stdout)
    cmd = ['ls', '-al', output_path]
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    print(out.stdout)


def build_pipeline_result():
    pass


def get_pipeline_result():
    pass


def build_markdown_content(state, test_case, message, line, content):
    if content == "":
        content = f'|Type|Test Case|Error Message|Line|\n|---|---|---|---|\n'
    content += f'|{state}|{test_case}|{message}|{line}|\n'
    return content


def save_pipeline_result(pipeline_result):
    # # save pipeline result to file
    # # /mnt/vss/.azdev/env_config/mnt/vss/_work/1/s/env/pipeline_result_3.8_latest_1.json
    # filename = os.path.join(azdev_test_result_dir, f'pipeline_result_{python_version}_{profile}_{instance_idx}.json')
    # with open(filename, 'w') as f:
    #     json.dump(pipeline_result, f, indent=4)
    # logger.info(f"save pipeline result to file: {filename}")
    pass


def main():
    logger.info("Start breaking change check ...\n")
    get_base_meta_files()
    get_diff_meta_files()
    meta_diff()


if __name__ == '__main__':
    main()
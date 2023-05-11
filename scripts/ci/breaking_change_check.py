#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
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
job_name = os.environ.get('JOB_NAME', None)
src_branch = 'azure-cli-2.48.1'
target_branch = 'dev'
# src_branch = os.environ.get('SRC_BRANCH', None)
# refs/remotes/pull/24765/merge
# target_branch = f'refs/remotes/pull/{pull_request_number}/merge'
base_meta_path = '/mnt/vss/_work/1/base_meta'
diff_meta_path = '/mnt/vss/_work/1/diff_meta'
output_path = '/mnt/vss/_work/1/output_meta'


def get_diff_meta_files():
    cmd = ['git', 'fetch', '--all', '--tags', '--prune']
    print(cmd)
    subprocess.run(cmd)
    cmd = ['git', 'checkout', src_branch]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['git', 'checkout', target_branch]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['azdev', 'setup', '--cli', get_cli_repo_path()]
    print(cmd)
    subprocess.run(cmd)
    # refs/remotes/pull/24765/merge
    cmd = ['azdev', 'command-change', 'meta-export', '--src', 'azure-cli-2.48.1', '--tgt', target_branch, '--repo', get_cli_repo_path(), '--meta-output-path', diff_meta_path]
    print(cmd)
    subprocess.run(cmd)


# def get_diff_meta_files():
#     cmd = ['git', 'checkout', src_branch]
#     print(cmd)
#     subprocess.run(cmd)
#     cmd = ['git', 'checkout', target_branch]
#     print(cmd)
#     subprocess.run(cmd)
#     cmd = ['azdev', 'command-change', 'meta-export', '--src', 'dev', '--tgt', target_branch, '--repo', get_cli_repo_path(), '--meta-output-path', diff_meta_path]
#     print(cmd)
#     subprocess.run(cmd)


def get_base_meta_files():
    cmd = ['git', 'checkout', src_branch]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['azdev', 'setup', '--cli', get_cli_repo_path()]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['azdev', 'command-change', 'meta-export', 'CLI', '--meta-output-path', base_meta_path]
    print(cmd)
    subprocess.run(cmd)


def meta_diff():
    if os.path.exists(diff_meta_path):
        for file in os.listdir(diff_meta_path):
            if file.endswith('.json'):
                cmd = ['azdev', 'command-change', 'meta-diff', '--base-meta-file', os.path.join(base_meta_path, file), '--diff-meta-file', os.path.join(diff_meta_path, file), '--output-file', os.path.join(output_path, file)]
                print(cmd)
                subprocess.run(cmd)
        cmd = ['ls', '-al', output_path]
        print(cmd)
        subprocess.run(cmd)


def get_pipeline_result():
    pipeline_result = {
        "breaking_change_check": {
            "Name": job_name,
            "Details": []
        }
    }
    if pull_request_number != '$(System.PullRequest.PullRequestNumber)':
        pipeline_result['pull_request_number'] = pull_request_number
    if os.path.exists(output_path):
        for file in os.listdir(output_path):
            with open(os.path.join(output_path, file), 'r') as f:
                items = json.load(f)
                if items:
                    module = os.path.basename(file).split('.')[0].split('_')[1]
                    breaking_change = {
                        "Module": module,
                        "Status": "",
                        "Content": ""
                    }
                    status = 'Warning'
                    for item in items:
                        if item['is_break'] == 'Yes':
                            status = 'Fail'
                        breaking_change['Content'] = build_markdown_content(item['cmd_name'], item['is_break'], item['rule_message'], item['suggest_message'], breaking_change['Content'])
                    breaking_change['Status'] = status
                    pipeline_result['breaking_change_check']['Details'].append(breaking_change)
    print(json.dumps(pipeline_result, indent=2))
    return pipeline_result


def build_markdown_content(cmd_name, is_break, rule_message, suggest_message, content):
    if content == "":
        content = f'|is_break|cmd_name|rule_message|suggest_message|\n|---|---|---|---|\n'
    content += f'|{is_break}|{cmd_name}|{rule_message}|{suggest_message}|\n'
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
    if pull_request_number != '$(System.PullRequest.PullRequestNumber)':
        logger.info("Start breaking change check ...\n")
        get_diff_meta_files()
        get_base_meta_files()
        meta_diff()
        get_pipeline_result()


if __name__ == '__main__':
    main()
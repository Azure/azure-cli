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
azdev_test_result_dir = os.path.expanduser("~/.azdev/env_config/mnt/vss/_work/1/s/env")
src_branch = os.environ.get('PR_TARGET_BRANCH', None)
target_branch = 'merged_pr'
base_meta_path = '~/_work/1/base_meta'
diff_meta_path = '~/_work/1/diff_meta'
output_path = '~/_work/1/output_meta'


def get_diff_meta_files():
    cmd = ['git', 'checkout', '-b', target_branch]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['git', 'checkout', src_branch]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['git', 'checkout', target_branch]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['git', 'rev-parse', 'HEAD']
    print(cmd)
    subprocess.run(cmd)
    cmd = ['azdev', 'command-change', 'meta-export', '--src', src_branch, '--tgt', target_branch, '--repo', get_cli_repo_path(), '--meta-output-path', diff_meta_path]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['ls', '-al', diff_meta_path]
    print(cmd)
    subprocess.run(cmd)


def get_base_meta_files():
    cmd = ['git', 'checkout', src_branch]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['git', 'rev-parse', 'HEAD']
    print(cmd)
    subprocess.run(cmd)
    cmd = ['azdev', 'setup', '--cli', get_cli_repo_path()]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['azdev', 'command-change', 'meta-export', 'CLI', '--meta-output-path', base_meta_path]
    print(cmd)
    subprocess.run(cmd)
    cmd = ['ls', '-al', base_meta_path]
    print(cmd)
    subprocess.run(cmd)


def meta_diff(only_break=False):
    if os.path.exists(diff_meta_path):
        for file in os.listdir(diff_meta_path):
            if file.endswith('.json'):
                cmd = ['azdev', 'command-change', 'meta-diff', '--base-meta-file', os.path.join(base_meta_path, file), '--diff-meta-file', os.path.join(diff_meta_path, file), '--output-file', os.path.join(output_path, file)]
                if only_break:
                    cmd.append('--only-break')
                print(cmd)
                subprocess.run(cmd)
        cmd = ['ls', '-al', output_path]
        print(cmd)
        subprocess.run(cmd)


def get_pipeline_result(only_break=False):
    pipeline_result = {
        "breaking_change_test": {
            "Details": [
                {
                    "TestName": "AzureCLI-BreakingChangeTest",
                    "Details": []
                }
            ]
        }
    }
    if pull_request_number != '$(System.PullRequest.PullRequestNumber)':
        pipeline_result['pull_request_number'] = pull_request_number
    if os.path.exists(output_path):
        for file in os.listdir(output_path):
            # skip empty file
            if not os.path.getsize(os.path.join(output_path, file)):
                continue
            with open(os.path.join(output_path, file), 'r') as f:
                items = json.load(f)
                module = os.path.basename(file).split('.')[0].split('_')[1]
                breaking_change = {
                    "Module": module,
                    "Status": "",
                    "Content": ""
                }
                status = 'Warning'
                sorted_items = sorted(items, key=sort_by_content)
                for item in sorted_items:
                    if item['is_break']:
                        status = 'Failed'
                    breaking_change['Content'] = build_markdown_content(item, breaking_change['Content'])
                breaking_change['Status'] = status
                pipeline_result['breaking_change_test']['Details'][0]['Details'].append(breaking_change)
    if not pipeline_result['breaking_change_test']['Details'][0]['Details']:
        pipeline_result['breaking_change_test']['Details'][0]['Details'].append({
            "Module": "Non Breaking Changes",
            "Status": "Succeeded",
            "Content": ""
        })

    result_length = len(json.dumps(pipeline_result, indent=4))
    if result_length > 65535:
        if only_break:
            logger.error("Breaking change report exceeds 65535 characters even with only_break=True.")
            return pipeline_result

        logger.info("Regenerating breaking change report with only_break=True to control length within 65535.")
        meta_diff(only_break=True)
        pipeline_result = get_pipeline_result(only_break=True)
        return pipeline_result

    return pipeline_result


def sort_by_content(item):
    # Sort item by is_break, cmd_name and rule_message,
    is_break = 0 if item['is_break'] else 1
    cmd_name = item['cmd_name'] if 'cmd_name' in item else item['subgroup_name']
    return is_break, cmd_name, item['rule_message']


def build_markdown_content(item, content):
    if content == "":
        content = f'|rule|cmd_name|rule_message|suggest_message|\n|---|---|---|---|\n'
    rule_link = f'[{item["rule_id"]} - {item["rule_name"]}]({item["rule_link_url"]})'
    rule = f'❌ {rule_link} ' if item['is_break'] else f'⚠️ {rule_link}'
    cmd_name = item['cmd_name'] if 'cmd_name' in item else item['subgroup_name']
    rule_message = item['rule_message']
    suggest_message = item['suggest_message']
    content += f'|{rule}|{cmd_name}|{rule_message}|{suggest_message}|\n'
    return content


def save_pipeline_result(pipeline_result):
    # save pipeline result to file
    # /mnt/vss/.azdev/env_config/mnt/vss/_work/1/s/env/breaking_change_test.json
    filename = os.path.join(azdev_test_result_dir, f'breaking_change_test.json')
    with open(filename, 'w') as f:
        json.dump(pipeline_result, f, indent=4)
    logger.info(f"save pipeline result to file: {filename}")


def main():
    if pull_request_number != '$(System.PullRequest.PullRequestNumber)':
        logger.info("Start breaking change test ...\n")
        get_diff_meta_files()
        get_base_meta_files()
        meta_diff()
        pipeline_result = get_pipeline_result()
        save_pipeline_result(pipeline_result)


if __name__ == '__main__':
    main()

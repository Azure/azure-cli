#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import fileinput
import json
import re
import requests


base_url = 'https://api.github.com/repos/azure/azure-cli'
release_head_url = '{}/git/ref/heads/release'.format(base_url)
dev_commits_url = '{}/commits?sha=dev'.format(base_url)
commit_pr_url = '{}/commits/commit_id/pulls'.format(base_url)

history_line_breaker = '==============='
days_before = 45
history_notes = {}


def generate_history_notes():
    release_head_sha = get_release_head()
    dev_commits = get_commits()
    for commit in dev_commits:
        if commit['sha'] == release_head_sha:
            break
        prs = get_prs_for_commit(commit['sha'])
        # parse PR if one commit is mapped to one PR
        if len(prs) == 1:
            process_pr(prs[0])
        else:
            process_commit(commit)

    cli_history = ''
    core_history = ''
    for component in sorted(history_notes, key=str.casefold):
        if component == 'Core':
            core_history += construct_core_history(component)
        else:
            cli_history += construct_cli_history(component)
    if core_history == '':
        core_history = '* Minor fixes'

    print("azure-cli history notes:")
    print(cli_history)
    print("azure-cli-core history notes:")
    print(core_history)

    cli_history = cli_history[:-2]  # remove last two \n
    with fileinput.FileInput('src/azure-cli/HISTORY.rst', inplace=True) as file:
        modify_history_file(file, cli_history)

    with fileinput.FileInput('src/azure-cli-core/HISTORY.rst', inplace=True) as file:
        modify_history_file(file, core_history)


def modify_history_file(file: fileinput.FileInput, new_history: str):
    write = True
    for line in file:
        if line == '{}\n'.format(history_line_breaker):
            print(line.replace(history_line_breaker, '{}\n\n{}'.format(history_line_breaker, new_history)))
            write = False
        else:
            # remove any history notes written above previous release version
            # make the generation of history notes idempotent
            if re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', line):
                write = True
            if write:
                print(line, end='')

def construct_cli_history(component: str):
    history = '**{}**\n\n'.format(component)
    for note in history_notes[component]:
        history += '* {}\n'.format(note)
    history += '\n'
    return history


def construct_core_history(component: str):
    history = ''
    for note in history_notes[component]:
        history += '* {}\n'.format(note)
    history += '\n'
    return history


def get_release_head() -> str:
    response = requests.get(release_head_url)
    if response.status_code != 200:
        raise Exception("Request to {} failed with {}".format(release_head_url, response.status_code))

    release_head_obj = json.loads(response.content.decode('utf-8'))
    release_head_sha = release_head_obj['object']['sha']
    return release_head_sha


def get_commits():
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days_before)
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    dev_since_url = '{}&since={}'.format(dev_commits_url, start_date_str)
    response = requests.get(dev_since_url)
    if response.status_code != 200:
        raise Exception("Request to {} failed with {}".format(dev_since_url, response.status_code))
    dev_commits = json.loads(response.content.decode('utf-8'))
    return dev_commits


def get_prs_for_commit(commit: str):
    headers = {'Accept': 'application/vnd.github.groot-preview+json'}
    url = commit_pr_url.replace('commit_id', commit)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception("Request to {} failed with {}".format(url, response.status_code))
    prs = json.loads(response.content.decode('utf-8'))
    return prs


def process_pr(pr):
    lines = [pr['title']]
    body = pr['body']
    search_result = re.search(r'\*\*History Notes:\*\*(.*)---', body, flags=re.DOTALL)
    if search_result is None:
        search_result = re.search(r'\*\*History Notes:\*\*(.*)', body, flags=re.DOTALL)
        if search_result is None:
            return
    body = search_result.group(1)
    lines.extend(body.splitlines())
    process_lines(lines)


def process_commit(commit):
    lines = commit['commit']['message'].splitlines()
    process_lines(lines)


def process_lines(lines: [str]):
    # do not put note of hotfix here since it's for last release
    if re.search('hotfix', lines[0], re.IGNORECASE):
        return
    note_in_desc = False
    for desc in lines[1:]:
        component, note = parse_message(desc)
        if component is not None:
            note_in_desc = True
            history_notes.setdefault(component, []).append(note)
    # if description has no history notes, parse PR title/commit message
    # otherwise should skip PR title/commit message
    if not note_in_desc:
        component, note = parse_message(lines[0])
        if component is not None:
            history_notes.setdefault(component, []).append(note)


def parse_message(message: str) ->(str, str):
    # do not include template
    if message.startswith('[Component Name'):
        return None, None
    m = re.search(r'^\[(.+)\](.+)$', message)
    if m is not None:
        component = m.group(1)
        note = m.group(2).strip()
        #remove appended PR number in commit message
        note = re.sub(r' \(#[0-9]+\)$', '', note)
        note = re.sub('BREAKING CHANGE:', '[BREAKING CHANGE]', note, flags=re.IGNORECASE)
        if note.endswith('.'):
            note = note[:-1]
        return component, note
    return None, None


if __name__ == "__main__":
    generate_history_notes()

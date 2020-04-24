#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
#
# This script is used to generate history notes for the commits on dev branch since last release.
# The history notes are generated based on the title/description of the Pull Requests for the commits.
# Make sure you have added the remote repository as upstream and fetched the latest code, i.e. you
# have done:
# git remote add upstream git@github.com:Azure/azure-cli.git
# git fetch upstream

import fileinput
import json
import os
import re
import subprocess
import requests
from requests.auth import HTTPBasicAuth

base_url = 'https://api.github.com/repos/azure/azure-cli'
commit_pr_url = '{}/commits/commit_id/pulls'.format(base_url)

history_line_breaker = '==============='
history_notes = {}


def generate_history_notes():
    dev_commits = get_commits()
    print("Get PRs for {} commits.".format(len(dev_commits)))
    for commit in dev_commits:
        prs = get_prs_for_commit(commit['sha'])
        # parse PR if one commit is mapped to one PR
        if len(prs) == 1:
            process_pr(prs[0])
        else:
            process_commit(commit)

    cli_history = ''
    core_history = ''
    for component in sorted(history_notes, key=str.casefold):
        if component.casefold() == 'core':
            core_history += construct_core_history(component)
        else:
            cli_history += construct_cli_history(component)
    if core_history == '':
        core_history = '* Minor fixes\n'
    else:
        core_history = core_history[:-1]  # remove last \n

    print("azure-cli history notes:")
    print(cli_history)
    print("azure-cli-core history notes:")
    print(core_history)

    cli_history = cli_history[:-1]  # remove last \n
    with fileinput.FileInput('src/azure-cli/HISTORY.rst',
                             inplace=True) as file:
        modify_history_file(file, cli_history)

    with fileinput.FileInput('src/azure-cli-core/HISTORY.rst',
                             inplace=True) as file:
        modify_history_file(file, core_history)


def modify_history_file(file: fileinput.FileInput, new_history: str):
    write = True
    for line in file:
        if line == '{}\n'.format(history_line_breaker):
            print(line.replace(
                history_line_breaker,
                '{}\n\n{}'.format(history_line_breaker, new_history)),
                  end='')
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


def get_commits():
    last_release = 'azure-cli-{}'.format(os.getenv('PRE_VERSION')) if os.getenv('PRE_VERSION') else 'upstream/release'
    out = subprocess.Popen([
        'git', 'log', '{}..upstream/dev'.format(last_release),
        '--pretty=format:"%H %s"'
    ],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    stdout, _ = out.communicate()
    dev_commits = []
    for line in stdout.decode('utf-8').splitlines():
        words = line.strip('"').split(None, 1)
        sha = words[0]
        subject = words[1]
        dev_commits.append({'sha': sha, 'subject': subject})
    dev_commits.reverse()
    return dev_commits


def get_prs_for_commit(commit: str):
    headers = {'Accept': 'application/vnd.github.groot-preview+json'}
    url = commit_pr_url.replace('commit_id', commit)
    response = requests.get(url, headers=headers, auth=HTTPBasicAuth('anything', os.environ.get('PAT_TOKEN')))
    if response.status_code != 200:
        raise Exception("Request to {} failed with {}".format(
            url, response.status_code))
    prs = json.loads(response.content.decode('utf-8'))
    return prs


def process_pr(pr):
    lines = [pr['title']]
    body = pr['body']
    search_result = re.search(r'\*\*History Notes:\*\*(.*)---',
                              body,
                              flags=re.DOTALL)
    if search_result is None:
        search_result = re.search(r'\*\*History Notes:\*\*(.*)',
                                  body,
                                  flags=re.DOTALL)
        if search_result is not None:
            body = search_result.group(1)
    else:
        body = search_result.group(1)
    lines.extend(body.splitlines())
    process_lines(lines, pr['number'])


def process_commit(commit):
    lines = commit['subject'].splitlines()
    process_lines(lines)


def process_lines(lines: [str], pr_num: str = None):
    # do not put note of hotfix here since it's for last release
    if re.search('hotfix', lines[0], re.IGNORECASE):
        return
    note_in_desc = False
    for desc in lines[1:]:
        component, note = parse_message(desc, pr_num)
        if component is not None:
            note_in_desc = True
            history_notes.setdefault(component, []).append(note)
    # if description has no history notes, parse PR title/commit message
    # otherwise should skip PR title/commit message
    if not note_in_desc:
        component, note = parse_message(lines[0], pr_num)
        if component is not None:
            history_notes.setdefault(component, []).append(note)


def parse_message(message: str, pr_num: str = None) -> (str, str):
    # do not include template
    if message.startswith('[Component Name'):
        return None, None
    m = re.search(r'^\[(.+?)\](.+)$', message)
    if m is not None:
        component = m.group(1)
        note = m.group(2).strip()
        if not pr_number_appended(note) and pr_num:
            note = '{} (#{})'.format(note, pr_num)
        note = re.sub('BREAKING CHANGE:',
                      '[BREAKING CHANGE]',
                      note,
                      flags=re.IGNORECASE)
        note = re.sub(r"^'(az .*?)':", r"`\1`:", note)
        note = re.sub(r"^(az .*?):", r"`\1`:", note)
        if not note.startswith('az') and not ':' in note:
            note = note[0].capitalize() + note[1:]
        if note.endswith('.'):
            note = note[:-1]
        return component, note
    return None, None


def pr_number_appended(line):
    m = re.search(r' \(#[0-9]+\)$', line)
    return m is not None


if __name__ == "__main__":
    generate_history_notes()

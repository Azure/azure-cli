# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import os
import hmac
import tempfile
import shutil
import requests
from hashlib import sha1
from flask import Flask, jsonify, request, Response
from subprocess import check_call, CalledProcessError
from uritemplate import URITemplate, expand

VERSION = '0.1.0'

# GitHub API constants
GITHUB_UA_PREFIX = 'GitHub-Hookshot/'
GITHUB_EVENT_NAME_PING = 'ping'
GITHUB_EVENT_NAME_PR = 'pull_request'
GITHUB_ALLOWED_EVENTS = [GITHUB_EVENT_NAME_PING, GITHUB_EVENT_NAME_PR]

# Environment variables
ENV_REPO_NAME = os.environ.get('REPO_NAME')
ENV_GITHUB_SECRET_TOKEN = os.environ.get('GITHUB_SECRET_TOKEN')
ENV_GITHUB_API_USER = os.environ.get('GITHUB_USER')
ENV_GITHUB_API_USER_TOKEN = os.environ.get('GITHUB_USER_TOKEN')
ENV_ALLOWED_USERS = os.environ.get('ALLOWED_USERS')
ENV_PYPI_REPO = os.environ.get('PYPI_REPO')
# although not used directly here, twine env vars are needed for releasing
ENV_PYPI_USERNAME = os.environ.get('TWINE_USERNAME')
ENV_PYPI_PASSWORD = os.environ.get('TWINE_PASSWORD')

assert (ENV_REPO_NAME and ENV_GITHUB_SECRET_TOKEN and ENV_ALLOWED_USERS and ENV_PYPI_REPO and ENV_PYPI_USERNAME and ENV_PYPI_PASSWORD and ENV_GITHUB_API_USER and ENV_GITHUB_API_USER_TOKEN),\
        "Not all required environment variables have been set. "\
        "Set ENV_REPO_NAME, GITHUB_SECRET_TOKEN, GITHUB_USER, GITHUB_USER_TOKEN, ALLOWED_USERS, PYPI_REPO, TWINE_USERNAME, TWINE_PASSWORD"

GITHUB_API_AUTH = (ENV_GITHUB_API_USER, ENV_GITHUB_API_USER_TOKEN)
GITHUB_API_HEADERS = {'Accept': 'application/vnd.github.v3+json', 'user-agent': 'azure-cli-bot/{}'.format(VERSION)}

RELEASE_LABEL = 'Release'
SOURCE_ARCHIVE_NAME = 'source.tar.gz'

OPENED_RELEASE_PR_COMMENT = """
Reviewers, please verify the following for this PR:

- [ ] The PR title has format `Release <component-name> <version>`.
- [ ] `setup.py` has been modified with the same version as in the PR title.
- [ ] `HISTORY.rst` has been modified with appropriate release notes.
- [ ] If releasing azure-cli or azure-cli-core, `__version__` defined in `__init__.py` should also be modified to match.
"""

GITHUB_RELEASE_BODY_TMPL = """
The module has been published to PyPI.

View HISTORY.rst of the module for a changelog.

{}
"""

def _verify_parse_request(req):
    headers = req.headers
    raw_payload = req.data
    payload = req.get_json()
    # Verify User Agent
    ua = headers.get('User-Agent')
    assert ua.startswith(GITHUB_UA_PREFIX), "Invalid User-Agent '{}'".format(ua)
    # Verify Signature
    gh_sig = headers.get('X-Hub-Signature')
    computed_sig = 'sha1=' + hmac.new(bytearray(ENV_GITHUB_SECRET_TOKEN, 'utf-8'), msg=raw_payload, digestmod=sha1).hexdigest()
    assert hmac.compare_digest(gh_sig, computed_sig), "Signatures didn't match"
    # Verify GitHub event
    gh_event = headers.get('X-GitHub-Event')
    assert gh_event in GITHUB_ALLOWED_EVENTS, "Webhook does not support event '{}'".format(gh_event)
    # Verify the repository
    event_repo = payload['repository']['full_name']
    assert event_repo == ENV_REPO_NAME, "Not listening for events from repo '{}'".format(event_repo)
    # Verify the sender (user who performed/triggered the event)
    event_sender = payload['sender']['login']
    assert event_sender in ENV_ALLOWED_USERS.split(), "Not listening for events from sender '{}'".format(event_sender)
    return {'event': gh_event, 'payload': payload}

def _handle_ping_event(_):
    return jsonify(ok=True)

def _parse_pr_title(title):
    assert title
    part1, component_name, version = title.split()
    assert part1.lower() == 'release'
    assert component_name.lower().startswith('azure-cli')
    return component_name, version

def create_release(component_name, release_assets_dir):
    working_dir = tempfile.mkdtemp()
    check_call(['git', 'clone', 'https://github.com/{}'.format(ENV_REPO_NAME), working_dir])
    check_call(['pip', 'install', '-e', 'scripts'], cwd=working_dir)
    check_call(['python', '-m', 'scripts.automation.release.run', '-c', component_name,
                '-r', ENV_PYPI_REPO, '--dest', release_assets_dir], cwd=working_dir)
    shutil.rmtree(working_dir, ignore_errors=True)

def apply_release_label(issue_url):
    payload = [RELEASE_LABEL]
    r = requests.post('{}/labels'.format(issue_url), json=payload, auth=GITHUB_API_AUTH, headers=GITHUB_API_HEADERS)
    return True if r.status_code in [200, 201] else False

def comment_on_pr(comments_url, comment_body):
    payload = {'body': comment_body}
    r = requests.post(comments_url, json=payload, auth=GITHUB_API_AUTH, headers=GITHUB_API_HEADERS)
    return True if r.status_code == 201 else False

def upload_asset(upload_uri_tmpl, filepath, label):
    filename = os.path.basename(filepath)
    upload_url = URITemplate(upload_uri_tmpl).expand(name=filename, label=label)
    headers = GITHUB_API_HEADERS
    headers['Content-Type'] = 'application/octet-stream'
    with open(filepath, 'rb') as payload:
        requests.post(upload_url, data=payload, auth=GITHUB_API_AUTH, headers=headers)

def upload_assets_for_github_release(upload_uri_tmpl, component_name, component_version, release_assets_dir):
    for filename in os.listdir(release_assets_dir):
        fullpath = os.path.join(release_assets_dir, filename)
        if filename == SOURCE_ARCHIVE_NAME:
            upload_asset(upload_uri_tmpl, fullpath, '{} {} source code (.tar.gz)'.format(component_name, component_version))
        elif filename.endswith('.tar.gz'):
            upload_asset(upload_uri_tmpl, fullpath, '{} {} Source Distribution (.tar.gz)'.format(component_name, component_version))
        elif filename.endswith('.whl'):
            upload_asset(upload_uri_tmpl, fullpath, '{} {} Python Wheel (.whl)'.format(component_name, component_version))

def create_github_release(component_name, component_version, released_pypi_url, release_assets_dir):
    tag_name = '{}-{}'.format(component_name, component_version)
    release_name = "{} {}".format(component_name, component_version)
    payload = {'tag_name': tag_name, "target_commitish": "master", "name": release_name, "body": GITHUB_RELEASE_BODY_TMPL.format(released_pypi_url), "prerelease": True}
    r = requests.post('https://api.github.com/repos/{}/releases'.format(ENV_REPO_NAME), json=payload, auth=GITHUB_API_AUTH, headers=GITHUB_API_HEADERS)
    if r.status_code == 201:
        upload_url = r.json()['upload_url']
        upload_assets_for_github_release(upload_url, component_name, component_version, release_assets_dir)
        return True
    return False

def _handle_pr_event(payload):
    pr_action = payload['action']
    pr = payload['pull_request']
    pr_merged = pr_action == 'closed' and pr['merged']
    try:
        component_name, component_version = _parse_pr_title(pr['title'])
        issue_url = pr['_links']['issue']['href']
        comment_url = pr['_links']['comments']['href']
        if pr_action == 'opened':
            apply_release_label(issue_url)
            comment_created = comment_on_pr(comment_url, OPENED_RELEASE_PR_COMMENT)
            if comment_created:
                return jsonify(msg="Commented on PR with release PR checklist.")
            else:
                return jsonify(msg="Attempted to comment on PR but API request did not succeed.")
        elif not pr_merged:
            return jsonify(msg="Ignoring event. PR not merged.")
        else:
            # Merged PR
            try:
                release_assets_dir = tempfile.mkdtemp()
                create_release(component_name, release_assets_dir)
                released_pypi_url = '{}/{}/{}'.format(ENV_PYPI_REPO, component_name, component_version)
                msg = "Release of '{}' with version '{}' successful. View at {}.".format(component_name, component_version, released_pypi_url)
                comment_on_pr(comment_url, msg)
                success = create_github_release(component_name, component_version, released_pypi_url, release_assets_dir)
                if success:
                    comment_on_pr(comment_url, 'GitHub release created. https://github.com/{}/releases.'.format(ENV_REPO_NAME))
                else:
                    comment_on_pr(comment_url, 'GitHub release creation unsuccessful. Please create a release at https://github.com/{}/releases.'.format(ENV_REPO_NAME))
                return jsonify(msg=msg)
            except CalledProcessError as e:
                err_msg = "Release of '{}' with version '{}' unsuccessful. Admins, please release manually.".format(component_name, component_version)
                comment_on_pr(comment_url, err_msg)
                print(err_msg)
                print(e)
                return jsonify(msg="Release of '{}' with version '{}' failed. View server logs for more info.".format(component_name, component_version)), 500
    except (AssertionError, ValueError):
        return jsonify(msg="Ignoring merged PR as not a Release PR. Expecting title to have format 'Release <component-name> <version>'")
    return jsonify(error='Unable to handle PR event.'), 500

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify(version=VERSION, message='API is running!')

@app.route('/github-webhook', methods=['POST'])
def handle_github_webhook():
    try:
        parsed_req = _verify_parse_request(request)
        event = parsed_req['event']
        payload = parsed_req['payload']
        if event == GITHUB_EVENT_NAME_PING:
            return _handle_ping_event(payload)
        elif event == GITHUB_EVENT_NAME_PR:
            return _handle_pr_event(payload)
        else:
            return jsonify(error="Event '{}' not supported.".format(event)), 400
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    return jsonify(error='Unable to handle request.'), 500

if __name__ == "__main__":
    app.run()

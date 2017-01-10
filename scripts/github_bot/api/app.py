# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import os
import hmac
import tempfile
import shutil
from hashlib import sha1
from flask import Flask, jsonify, request, Response
from subprocess import check_call, CalledProcessError

VERSION = '0.1.0'
REPO_NAME = 'azure/azure-cli'

# GitHub API constants
GITHUB_UA_PREFIX = 'GitHub-Hookshot/'
GITHUB_EVENT_NAME_PING = 'ping'
GITHUB_EVENT_NAME_PR = 'pull_request'
GITHUB_ALLOWED_EVENTS = [GITHUB_EVENT_NAME_PING, GITHUB_EVENT_NAME_PR]

# Environment variables
ENV_GITHUB_SECRET_TOKEN = os.environ.get('GITHUB_SECRET_TOKEN')
ENV_ALLOWED_USERS = os.environ.get('ALLOWED_USERS')
ENV_PYPI_REPO = os.environ.get('PYPI_REPO')
# although not used directly here, twine env vars are needed for releasing
ENV_PYPI_USERNAME = os.environ.get('TWINE_USERNAME')
ENV_PYPI_PASSWORD = os.environ.get('TWINE_PASSWORD')

assert (ENV_GITHUB_SECRET_TOKEN and ENV_ALLOWED_USERS and ENV_PYPI_REPO and ENV_PYPI_USERNAME and ENV_PYPI_PASSWORD),\
        "Not all required environment variables have been set. "\
        "Set GITHUB_SECRET_TOKEN, ALLOWED_USERS, PYPI_REPO, TWINE_USERNAME, TWINE_PASSWORD"

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
    assert event_repo == REPO_NAME, "Not listening for events from repo '{}'".format(event_repo)
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

def create_release(component_name):
    working_dir = tempfile.mkdtemp()
    check_call(['git', 'clone', 'https://github.com/{}'.format(REPO_NAME), working_dir])
    check_call(['python', '-m', 'scripts.automation.release.run', '-c', component_name,
                '-r', ENV_PYPI_REPO], cwd=working_dir)
    shutil.rmtree(working_dir, ignore_errors=True)

def _handle_pr_event(payload):
    pr_action = payload['action']
    pr = payload['pull_request']
    pr_merged = pr_action == 'closed' and pr['merged']
    if not pr_merged:
        return jsonify(msg="Ignoring event. PR not merged.")
    try:
        component_name, component_version = _parse_pr_title(pr['title'])
        try:
            create_release(component_name)
            released_pypi_url = '{}/{}'.format(ENV_PYPI_REPO, component_name)
            return jsonify(msg="Release of '{}' with version '{}' successful. View at {}".format(component_name, component_version, released_pypi_url))
        except CalledProcessError as e:
            print("Release of '{}' with version '{}' failed:".format(component_name, component_version))
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

#!/usr/bin/env python3

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import shlex
import shutil
from datetime import datetime
from subprocess import check_output, CalledProcessError, STDOUT
from typing import Optional
from importlib import import_module

import requests


class InternalCommunicationAuth(requests.auth.AuthBase):  # pylint: disable=too-few-public-methods
    def __call__(self, req):
        req.headers['Authorization'] = os.environ['A01_INTERNAL_COMKEY']
        return req


session = requests.Session()  # pylint: disable=invalid-name
session.auth = InternalCommunicationAuth()


class Droid(object):
    def __init__(self):
        try:
            self.run_id = os.environ['A01_DROID_RUN_ID']
        except KeyError:
            print('The environment variable A01_DROID_RUN_ID is missing.', file=sys.stderr, flush=True)
            sys.exit(1)

        try:
            self.store_host = os.environ['A01_STORE_NAME']
        except KeyError:
            print('The environment variable A01_STORE_NAME is missing. Fallback to a01store.', file=sys.stderr,
                  flush=True)
            self.store_host = 'a01store'

        self.run_live = os.environ.get('A01_RUN_LIVE', 'False') == 'True'
        self.username = os.environ.get('A01_SP_USERNAME', None)
        self.password = os.environ.get('A01_SP_PASSWORD', None)
        self.tenant = os.environ.get('A01_SP_TENANT', None)

    def login_azure_cli(self) -> None:
        if not self.run_live:
            return

        if self.username and self.password and self.tenant:
            try:
                login = check_output(shlex.split('az login --service-principal -u {} -p {} -t {}'
                                                 .format(self.username, self.password, self.tenant)))
                print(login.decode('utf-8'), flush=True)
            except CalledProcessError as error:
                print('Failed to sign in with the service principal.', file=sys.stderr, flush=True)
                print(str(error), file=sys.stderr, flush=True)
                sys.exit(1)
        else:
            print('Missing service principal settings for live test', file=sys.stderr, flush=True)
            sys.exit(1)

    def start(self):
        print('Store host: {}'.format(self.store_host), flush=True)
        print('    Run ID: {}'.format(self.run_id), flush=True)

        # Exit condition: when the /run/<run_id>/checkout endpoint returns 204, the sys.exit(0) will be called therefore
        # exits the entire program.
        while True:
            task = self.checkout_task()
            self.run_task(task)

    def checkout_task(self) -> str:
        task = self.request_task()
        print('Pick up task {}.'.format(task['id']), flush=True)

        # update the running agent first
        result_details = task.get('result_detail', dict())
        result_details['agent'] = '{}@{}'.format(
            os.environ.get('ENV_POD_NAME', 'N/A'),
            os.environ.get('ENV_NODE_NAME', 'N/A'))
        result_details['live'] = self.run_live
        self.update_task(task['id'], {'result_details': result_details})

        return task['id']

    def run_task(self, task_id: str) -> None:
        # run the task
        task = self.retrieve_task(task_id)

        begin = datetime.now()
        try:
            test_path = task['settings']['path']
            env_vars = {'AZURE_TEST_RUN_LIVE': 'True'} if self.run_live else None
            output = check_output(shlex.split(f'python -m unittest {test_path}'), stderr=STDOUT, env=env_vars)
            output = output.decode('utf-8')
            result = 'Passed'
        except CalledProcessError as error:
            output = error.output.decode('utf-8')
            result = 'Failed'
        elapsed = datetime.now() - begin

        print(f'Task {result}', flush=True)

        storage_mount = '/mnt/storage'
        if not os.path.isdir(storage_mount):
            print(f'Storage volume is not mount for logging. Print the task output to the stdout instead.',
                  file=sys.stderr, flush=True)
            print(output, file=sys.stdout, flush=True)
        else:
            os.makedirs(os.path.join(storage_mount, self.run_id), exist_ok=True)
            with open(os.path.join(storage_mount, self.run_id, f'task_{task_id}.log'), 'w') as log_file_handle:
                log_file_handle.write(output)

            # find the recording file and save it
            recording_file = self._find_recording_file(test_path)
            if recording_file:
                shutil.copyfile(recording_file,
                                os.path.join(storage_mount, self.run_id, f'recording_{task_id}.yaml'))

        result_details = task.get('result_detail', dict())
        result_details['duration'] = int(elapsed.total_seconds() * 1000)
        patch = {
            'result': result,
            'result_details': result_details,
            'status': 'completed',
        }
        self.update_task(task['id'], patch)

    def request_task(self) -> dict:
        try:
            resp = session.post('http://{}/run/{}/checkout'.format(self.store_host, self.run_id))
            resp.raise_for_status()

            if resp.status_code == 204:
                print("No more task. This Droid's work should be completed.")
                sys.exit(0)

            return resp.json()
        except requests.HTTPError as error:
            print(f'Fail to checkout task from the store. {error}')
            sys.exit(1)
        except ValueError as error:
            print(f'Fail to parse the task as JSON. {error}')
            sys.exit(1)

    def update_task(self, task_id: str, patch: dict) -> None:
        try:
            session.patch('http://{}/task/{}'.format(self.store_host, task_id), json=patch).raise_for_status()
        except requests.HTTPError as error:
            print(f'Fail to update the task\'s details. {error}')
            sys.exit(1)

    def retrieve_task(self, task_id: str) -> dict:
        try:
            resp = session.get('http://{}/task/{}'.format(self.store_host, task_id))
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as error:
            print(f'Fail to update the task\'s details. {error}')
            sys.exit(1)
        except ValueError as error:
            print(f'Fail to parse the task as JSON. {error}')
            sys.exit(1)

    @staticmethod
    def _find_recording_file(test_path: str) -> Optional[str]:
        module_path, _, test_method = test_path.rsplit('.', 2)
        test_folder = os.path.dirname(import_module(module_path).__file__)
        recording_file = os.path.join(test_folder, 'recordings', test_method + '.yaml')
        return recording_file if os.path.exists(recording_file) else None


def main():
    droid = Droid()
    droid.login_azure_cli()
    droid.start()


if __name__ == '__main__':
    main()

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import logging
import os
import time
from azure.cli.core.util import CLIError

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

logger = logging.getLogger(__name__)


def _add_selfsigned_cert_to_keyvault(test, kwargs):
    kwargs.update({'policy_path': os.path.join(TEST_DIR, 'policy.json')})
    test.cmd('keyvault certificate create --vault-name {kv_name} -n {cert_name} -p @"{policy_path}"')

    while True:
        cert = test.cmd('keyvault certificate show --vault-name {kv_name} -n {cert_name}').get_output_in_json()
        if cert:
            break
    assert cert['sid'] is not None
    return cert


def _create_keyvault(test, kwargs):
    test.cmd('keyvault create --resource-group {rg} -n {kv_name} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true')


def _create_cluster_with_separate_kv(test, kwargs):
    _create_keyvault(test, kwargs)
    cert = _add_selfsigned_cert_to_keyvault(test, kwargs)
    cert_secret_id = cert['sid']
    kwargs.update({'cert_secret_id': cert_secret_id})

    test.cmd('az sf cluster create -g {rg} -c {cluster_name} -l {loc} --secret-identifier {cert_secret_id} --vm-password "{vm_password}" --cluster-size 3')
    timeout = time.time() + 900
    while True:
        cluster = test.cmd('az sf cluster show -g {rg} -c {cluster_name}').get_output_in_json()
        if cluster['provisioningState']:
            if cluster['provisioningState'] == 'Succeeded':
                return
            if cluster['provisioningState'] == 'Failed':
                raise CLIError("Cluster deployment was not succesful")

        if time.time() > timeout:
            raise CLIError("Cluster deployment timed out")
        if test.in_recording or test.is_live:
            time.sleep(60)


def _create_cluster(test, kwargs):
    test.cmd('az sf cluster create -g {rg} -c {cluster_name} -l {loc} --certificate-output-folder MyCertificates --certificate-subject-name {cluster_name} --vm-password "{vm_password}" --cluster-size 3')
    timeout = time.time() + 900
    while True:
        cluster = test.cmd('az sf cluster show -g {rg} -c {cluster_name}').get_output_in_json()
        if cluster['provisioningState']:
            if cluster['provisioningState'] == 'Succeeded':
                return
            if cluster['provisioningState'] == 'Failed':
                raise CLIError("Cluster deployment was not succesful")

        if time.time() > timeout:
            raise CLIError("Cluster deployment timed out")
        if test.in_recording or test.is_live:
            time.sleep(60)


def _wait_for_cluster_state_ready(test, kwargs):
    timeout = time.time() + 900
    while True:
        cluster = test.cmd('az sf cluster show -g {rg} -c {cluster_name}').get_output_in_json()

        if cluster['clusterState']:
            if cluster['clusterState'] == 'Ready':
                return

        if time.time() > timeout:
            state = "unknown"
            if cluster['clusterState']:
                state = cluster['clusterState']
            raise CLIError("Cluster deployment timed out. cluster state is not 'Ready'. State: {}".format(state))
        if test.in_recording or test.is_live:
            time.sleep(60)

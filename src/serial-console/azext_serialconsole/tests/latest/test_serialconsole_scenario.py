# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
import time
import requests
import websocket
import pytest
from azext_serialconsole.custom import check_resource
from azure.cli.testsdk.base import ScenarioTest
from azure.cli.testsdk import (
    LiveScenarioTest, StorageAccountPreparer, ResourceGroupPreparer)
from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError
from azure.cli.core.azclierror import ForbiddenError, ResourceNotFoundError
from azure.cli.core.azclierror import AzureConnectionError
from azure.cli.core.azclierror import ForbiddenError
from azure.core.exceptions import ResourceNotFoundError as ComputeClientResourceNotFoundError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class CheckResourceTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    def test_check_resource_VMSS(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })

        with self.assertRaises(ComputeClientResourceNotFoundError):
            check_resource(self.cli_ctx, resource_group, name, None)
        with self.assertRaises(ComputeClientResourceNotFoundError):
            check_resource(self.cli_ctx, resource_group, name, "0")

        self.cmd('az vmss create -g {rg} -n {name} --image {urn} --instance-count 2 -l {loc} --orchestration-mode uniform')

        with self.assertRaises(ResourceNotFoundError):
            check_resource(self.cli_ctx, resource_group, name, None)

        iid = self.cmd('vmss list-instances --resource-group {rg} --name {name} --query "[].instanceId"').get_output_in_json()[0]
        self.kwargs.update({'id': iid})
        self.cmd('az vmss update --name {name} --resource-group {rg} --set virtualMachineProfile.diagnosticsProfile="{{\\"bootDiagnostics\\": {{\\"Enabled\\" : \\"True\\",\\"StorageUri\\" : null}}}}"')
        self.cmd('az vmss update-instances -g {rg} -n {name} --instance-ids {id}')

        check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss deallocate -g {rg} -n {name} --instance-ids {id}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss start -g {rg} -n {name} --instance-ids {id}')
        self.cmd('az vmss stop -g {rg} -n {name} --instance-ids {id}')

        check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss start -g {rg} -n {name} --instance-ids {id}')
        self.cmd('az vmss update --name {name} --resource-group {rg} --set virtualMachineProfile.diagnosticsProfile="{{\\"bootDiagnostics\\": {{\\"Enabled\\" : \\"True\\",\\"StorageUri\\":\\"https://{sa}.blob.core.windows.net/\\"}}}}"')
        self.cmd('az vmss update-instances -g {rg} -n {name} --instance-ids {id}')

        check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az serial-console disable')

        with self.assertRaises(ForbiddenError):
            check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az serial-console enable')

        check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss deallocate -g {rg} -n {name} --instance-ids {id}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss start -g {rg} -n {name} --instance-ids {id}')
        self.cmd('az vmss stop -g {rg} -n {name} --instance-ids {id}')

        check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss start -g {rg} -n {name} --instance-ids {id}')
        self.cmd('az vmss update --name {name} --resource-group {rg} --set virtualMachineProfile.diagnosticsProfile="{{\\"bootDiagnostics\\": {{\\"Enabled\\" : \\"False\\",\\"StorageUri\\" : null}}}}"')

        check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss update-instances -g {rg} -n {name} --instance-ids {id}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss deallocate -g {rg} -n {name} --instance-ids {id}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss start -g {rg} -n {name} --instance-ids {id}')
        self.cmd('az vmss update --name {name} --resource-group {rg} --set virtualMachineProfile.diagnosticsProfile="{{\\"bootDiagnostics\\": {{\\"Enabled\\" : \\"True\\",\\"StorageUri\\" : null}}}}"')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, iid)

        self.cmd('az vmss update-instances -g {rg} -n {name} --instance-ids {id}')

        check_resource(self.cli_ctx, resource_group, name, iid)

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    @AllowLargeResponse()
    def test_check_resource_VM(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })

        with self.assertRaises(ComputeClientResourceNotFoundError):
            check_resource(self.cli_ctx, resource_group, name, None)
        with self.assertRaises(ComputeClientResourceNotFoundError):
            check_resource(self.cli_ctx, resource_group, name, "0")

        self.cmd('az vm create -g {rg} -n {name} --image {urn} -l {loc} --generate-ssh-keys')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm boot-diagnostics enable -g {rg} -n {name}')

        check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm deallocate -g {rg} -n {name}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm start -g {rg} -n {name}')
        self.cmd('az vm stop -g {rg} -n {name}')

        check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm boot-diagnostics disable -g {rg} -n {name}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm start -g {rg} -n {name}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm boot-diagnostics enable -g {rg} -n {name} --storage {sa}')

        check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az serial-console disable')

        with self.assertRaises(ForbiddenError):
            check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az serial-console enable')

        check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm stop -g {rg} -n {name}')

        check_resource(self.cli_ctx, resource_group, name, None)

        self.cmd('az vm deallocate -g {rg} -n {name}')

        with self.assertRaises(AzureConnectionError):
            check_resource(self.cli_ctx, resource_group, name, None)


class SerialConsoleEnableDisableTest(ScenarioTest):

    def test_enable_disable(self):
        self.cmd('az serial-console disable', checks=[
            self.check('properties.disabled', 'True')
        ])
        self.cmd('az serial-console enable', checks=[
            self.check('properties.disabled', 'False')
        ])


class SerialconsoleAdminCommandsTest(LiveScenarioTest):

    def check_result(self, resource_group_name, vm_vmss_name, vmss_instanceid=None, message="", hasManagedStorageAccount=False):
        print("Checking serial console output for message: ", message)
        ARM_ENDPOINT = "https://management.azure.com"
        RP_PROVIDER = "Microsoft.SerialConsole"
        subscription_id = self.get_subscription_id()
        vm_path = f"virtualMachineScaleSets/{vm_vmss_name}/virtualMachines/{vmss_instanceid}" \
            if vmss_instanceid else f"virtualMachines/{vm_vmss_name}"
        connection_url = (f"{ARM_ENDPOINT}/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}"
                          f"/providers/Microsoft.Compute/{vm_path}"
                          f"/providers/{RP_PROVIDER}/serialPorts/0"
                          f"/connect?api-version=2024-07-01")

        from azure.cli.core._profile import Profile
        token_info, _, _ = Profile().get_raw_token()
        access_token = token_info[1]
        application_json_format = "application/json"
        headers = {'authorization': "Bearer " + access_token,
                   'accept': application_json_format,
                   'content-type': application_json_format}

        postRetryCounter = 1

        while True:
            result = requests.post(connection_url, headers=headers)
            json_results = json.loads(result.text)

            if result.status_code == 200 and "connectionString" in json_results:
                break
            else:
                print("Failed to get connection string from serial console connect endpoint.")
                print("Status code: ", result.status_code)
                print("Response text: ", result.text)

            if postRetryCounter > 3:
                self.fail("Failed to get connection string from serial console connect endpoint after retrying multiple times... Failing test. See status and response of retries in logs.")
            else:
                postRetryCounter += 1
                time.sleep(10)

        websocket_url = json_results["connectionString"]

        ws = websocket.WebSocket()
        ws.connect(websocket_url + "?authorization=" + access_token, timeout=30)
        print("WebSocket connected for verifying message.")
        print("Sleeping 60 seconds to allow 'Connecting...' message to appear.")
        time.sleep(60)
        
        if not hasManagedStorageAccount:
            print("Sending access token to start custom storage account setup...")
            ws.send(access_token)
            print("Finished sending access token")
        
        buffer = ""
        iter = 0
        print("Starting to read from WebSocket to find message...")
        while True:
            iter += 1
            print(f"Current timestamp: {time.strftime('%X')}, current iteration: {iter}/5")
            
            while True:
                try:
                    buffer += ws.recv()
                except (websocket.WebSocketTimeoutException, websocket.WebSocketConnectionClosedException):
                    break
                        
            if message in buffer:
                print("Found message in buffer! Finished verification.")
                break
            
            print(f"Message not found yet in buffer, current buffer: {buffer}")
            
            if iter >= 10:
                print("Max retries reached, exiting read loop.")
                break
            else:
                print("Sleeping 10 seconds before retrying...")
                time.sleep(10) 
        
        ws.close()
        assert message in buffer

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    def test_send_sysrq_VMSS(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })
        result = self.createVMSS()
        print("Sending SysRq...")
        stopwatch_start = time.time()
        self.cmd(
            'serial-console send sysrq -g {rg} -n {name} --instance-id {id} --input h')
        stopwatch_end = time.time()
        print(f"SysRq sent in {stopwatch_end - stopwatch_start} seconds.")
        self.check_result(resource_group, name,
                          vmss_instanceid=result[1], message="sysrq: HELP")

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    def test_send_nmi_VMSS(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })
        result = self.createVMSS()
        print("Sending NMI...")
        stopwatch_start = time.time()
        self.cmd(
            'serial-console send nmi -g {rg} -n {name} --instance-id {id}')
        stopwatch_end = time.time()
        print(f"NMI sent in {stopwatch_end - stopwatch_start} seconds.")
        self.check_result(resource_group, name,
                          vmss_instanceid=result[1], message="NMI received")

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    def test_send_reset_VMSS(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })
        result = self.createVMSS()
        print("Sending Reset...")
        stopwatch_start = time.time()
        self.cmd('serial-console send reset -g {rg} -n {name} --instance-id {id}')
        stopwatch_end = time.time()
        print(f"Reset sent in {stopwatch_end - stopwatch_start} seconds.")
        self.check_result(resource_group, name,
                          vmss_instanceid=result[1], message="Record successful boot")

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    def test_send_nmi_VM(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })
        self.createVM()
        print("Sending NMI...")
        stopwatch_start = time.time()
        self.cmd('serial-console send nmi -g {rg} -n {name}')
        stopwatch_end = time.time()
        print(f"NMI sent in {stopwatch_end - stopwatch_start} seconds.")
        self.check_result(resource_group, name, message="NMI received")

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    def test_send_sysrq_VM(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })
        self.createVM()
        print("Sending Sysrq...")
        stopwatch_start = time.time()
        self.cmd('serial-console send sysrq -g {rg} -n {name} --input h')
        stopwatch_end = time.time()
        print(f"Sysrq sent in {stopwatch_end - stopwatch_start} seconds.")
        self.check_result(resource_group, name, message="sysrq: HELP")

    @ResourceGroupPreparer(name_prefix='cli_test_serialconsole', location='westus2')
    @StorageAccountPreparer(name_prefix='cli', location="westus2")
    def test_send_reset_VM(self, resource_group, storage_account):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'name': name,
            'urn': 'Ubuntu2204',
            'loc': 'westus2'
        })
        self.createVM()
        print("Sending Reset...")
        stopwatch_start = time.time()
        self.cmd('serial-console send reset -g {rg} -n {name}')
        stopwatch_end = time.time()
        print(f"Reset sent in {stopwatch_end - stopwatch_start} seconds.")
        self.check_result(resource_group, name, message="Record successful boot")
        
    def createVMSS(self):
        self.cmd(
            'az vmss create -g {rg} -n {name} --image {urn} --instance-count 2 -l {loc} --orchestration-mode uniform')
        self.cmd(
            'az vmss update --name {name} --resource-group {rg} --set virtualMachineProfile.diagnosticsProfile="{{\\"bootDiagnostics\\": {{\\"Enabled\\" : \\"True\\",\\"StorageUri\\":\\"https://{sa}.blob.core.windows.net/\\"}}}}"')
        result = self.cmd(
            'vmss list-instances --resource-group {rg} --name {name} --query "[].instanceId"').get_output_in_json()
        self.kwargs.update({'id': result[1]})
        self.cmd(
            'az vmss update-instances -g {rg} -n {name} --instance-ids {id}')
        time.sleep(60)
        for i in range(5):
            try:
                self.cmd('vmss get-instance-view --resource-group {rg} --name {name} --instance-id {id}', checks=[
                    self.check('statuses[0].code',
                               'ProvisioningState/succeeded'),
                    self.check('statuses[1].code', 'PowerState/running'),
                ])
                break
            except JMESPathCheckAssertionError:
                time.sleep(30)
        return result

    def createVM(self):
        self.cmd(
            'az vm create -g {rg} -n {name} --image {urn} --boot-diagnostics-storage {sa} -l {loc} --generate-ssh-keys')
        time.sleep(60)
        for i in range(5):
            try:
                self.cmd('vm get-instance-view --resource-group {rg} --name {name}', checks=[
                    self.check(
                        'instanceView.statuses[0].code', 'ProvisioningState/succeeded'),
                    self.check(
                        'instanceView.statuses[1].code', 'PowerState/running'),
                ])
                break
            except JMESPathCheckAssertionError:
                time.sleep(30)

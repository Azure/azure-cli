# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import unittest

from azure.cli.testsdk.scenario_tests import AllowLargeResponse, live_only
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)
from msrestazure.tools import parse_resource_id

from azext_containerapp.tests.latest.common import (write_test_file, clean_up_test_file)
from .common import TEST_LOCATION
from .utils import create_containerapp_env

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class ContainerappIdentityTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_identity_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)
        user_identity_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp identity assign --system-assigned -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name))

        self.cmd('containerapp identity assign --user-assigned {} -g {} -n {}'.format(user_identity_name, resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
        ])

        self.cmd('containerapp identity show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
        ])

        self.cmd('containerapp identity remove --user-assigned {} -g {} -n {}'.format(user_identity_name, resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('containerapp identity show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('containerapp identity remove --system-assigned -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'None'),
        ])

        self.cmd('containerapp identity show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'None'),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="canadacentral")
    def test_containerapp_identity_system(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)
        logs_workspace_name = self.create_random_name(prefix='containerapp-env', length=24)

        logs_workspace_id = self.cmd('monitor log-analytics workspace create -g {} -n {} -l eastus'.format(resource_group, logs_workspace_name)).get_output_in_json()["customerId"]
        logs_workspace_key = self.cmd('monitor log-analytics workspace get-shared-keys -g {} -n {}'.format(resource_group, logs_workspace_name)).get_output_in_json()["primarySharedKey"]

        self.cmd('containerapp env create -g {} -n {} --logs-workspace-id {} --logs-workspace-key {}'.format(resource_group, env_name, logs_workspace_id, logs_workspace_key))

        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env_name)).get_output_in_json()

        self.cmd('containerapp create -g {} -n {} --environment {} --system-assigned'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp identity show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('containerapp identity remove --system-assigned -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'None'),
        ])

        self.cmd('containerapp identity assign --system-assigned -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('containerapp identity remove --system-assigned -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'None'),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_identity_user(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)
        user_identity_name1 = self.create_random_name(prefix='containerapp-user1', length=24)
        user_identity_name2 = self.create_random_name(prefix='containerapp-user2', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, ca_name, env_name))

        self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name1))

        self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name2))

        self.cmd('containerapp identity assign --system-assigned -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('containerapp identity assign --user-assigned {} {} -g {} -n {}'.format(user_identity_name1, user_identity_name2, resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
        ])

        self.cmd('containerapp identity show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
        ])

        self.cmd('containerapp identity remove --user-assigned {} -g {} -n {}'.format(user_identity_name1, resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
        ])

        self.cmd('containerapp identity remove --user-assigned {} -g {} -n {}'.format(user_identity_name2, resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('containerapp identity show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
        ])

        self.cmd('containerapp identity remove --system-assigned -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'None'),
        ])

        self.cmd('containerapp identity show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('type', 'None'),
        ])

class ContainerappIngressTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_ingress_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 80'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('external', True),
            JMESPathCheck('targetPort', 80),
        ])

        self.cmd('containerapp ingress disable -g {} -n {}'.format(resource_group, ca_name, env_name))

        containerapp_def = self.cmd('containerapp show -g {} -n {}'.format(resource_group, ca_name)).get_output_in_json()

        self.assertEqual("fqdn" in containerapp_def["properties"]["configuration"], False)

        self.cmd('containerapp ingress enable -g {} -n {} --type internal --target-port 81 --allow-insecure --transport http2'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('external', False),
            JMESPathCheck('targetPort', 81),
            JMESPathCheck('allowInsecure', True),
            JMESPathCheck('transport', "Http2"),
        ])

        self.cmd('containerapp ingress update -g {} -n {} --type external --allow-insecure=False'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('external', True),
            JMESPathCheck('targetPort', 81),
            JMESPathCheck('allowInsecure', False),
            JMESPathCheck('transport', "Http2"),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_ingress_traffic_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 80 --revisions-mode multiple'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('external', True),
            JMESPathCheck('targetPort', 80),
        ])

        self.cmd('containerapp ingress traffic set -g {} -n {} --revision-weight latest=100'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].latestRevision', True),
            JMESPathCheck('[0].weight', 100),
        ])

        self.cmd('containerapp update -g {} -n {} --cpu 1.0 --memory 2Gi'.format(resource_group, ca_name))

        revisions_list = self.cmd('containerapp revision list -g {} -n {}'.format(resource_group, ca_name)).get_output_in_json()

        self.cmd('containerapp ingress traffic set -g {} -n {} --revision-weight latest=50 {}=50'.format(resource_group, ca_name, revisions_list[0]["name"]), checks=[
            JMESPathCheck('[0].latestRevision', True),
            JMESPathCheck('[0].weight', 50),
            JMESPathCheck('[1].revisionName', revisions_list[0]["name"]),
            JMESPathCheck('[1].weight', 50),
        ])

        self.cmd('containerapp ingress traffic show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].latestRevision', True),
            JMESPathCheck('[0].weight', 50),
            JMESPathCheck('[1].revisionName', revisions_list[0]["name"]),
            JMESPathCheck('[1].weight', 50),
        ])

        revisions_list = self.cmd('containerapp revision list -g {} -n {}'.format(resource_group, ca_name)).get_output_in_json()

        for revision in revisions_list:
            self.assertEqual(revision["properties"]["trafficWeight"], 50)

    @AllowLargeResponse(8192)
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_custom_domains_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        app = self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 80'.format(resource_group, ca_name, env_name)).get_output_in_json()

        self.cmd('containerapp hostname list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 0),
        ])

        # list hostnames with a wrong location
        self.cmd('containerapp hostname list -g {} -n {} -l "{}"'.format(resource_group, ca_name, "eastus2"), checks={
            JMESPathCheck('length(@)', 0),
        }, expect_failure=True)

        # create an App service domain and update its txt records
        contacts = os.path.join(TEST_DIR, 'domain-contact.json')
        zone_name = "{}.com".format(ca_name)
        subdomain_1 = "devtest"
        subdomain_2 = "clitest"
        txt_name_1 = "asuid.{}".format(subdomain_1)
        txt_name_2 = "asuid.{}".format(subdomain_2)
        hostname_1 = "{}.{}".format(subdomain_1, zone_name)
        hostname_2 = "{}.{}".format(subdomain_2, zone_name)
        verification_id = app["properties"]["customDomainVerificationId"]
        self.cmd("appservice domain create -g {} --hostname {} --contact-info=@'{}' --accept-terms".format(resource_group, zone_name, contacts)).get_output_in_json()
        self.cmd('network dns record-set txt add-record -g {} -z {} -n {} -v {}'.format(resource_group, zone_name, txt_name_1, verification_id)).get_output_in_json()
        self.cmd('network dns record-set txt add-record -g {} -z {} -n {} -v {}'.format(resource_group, zone_name, txt_name_2, verification_id)).get_output_in_json()

        # upload cert, add hostname & binding
        pfx_file = os.path.join(TEST_DIR, 'cert.pfx')
        pfx_password = 'test12'
        cert_id = self.cmd('containerapp ssl upload -n {} -g {} --environment {} --hostname {} --certificate-file "{}" --password {}'.format(ca_name, resource_group, env_name, hostname_1, pfx_file, pfx_password), checks=[
            JMESPathCheck('[0].name', hostname_1),
        ]).get_output_in_json()[0]["certificateId"]

        self.cmd('containerapp hostname list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', hostname_1),
            JMESPathCheck('[0].bindingType', "SniEnabled"),
            JMESPathCheck('[0].certificateId', cert_id),
        ])

        # get cert thumbprint
        cert_thumbprint = self.cmd('containerapp env certificate list -n {} -g {} -c {}'.format(env_name, resource_group, cert_id), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].id', cert_id),
        ]).get_output_in_json()[0]["properties"]["thumbprint"]

        # add binding by cert thumbprint
        self.cmd('containerapp hostname bind -g {} -n {} --hostname {} --thumbprint {}'.format(resource_group, ca_name, hostname_2, cert_thumbprint), expect_failure=True)

        self.cmd('containerapp hostname bind -g {} -n {} --hostname {} --thumbprint {} -e {}'.format(resource_group, ca_name, hostname_2, cert_thumbprint, env_name), checks=[
            JMESPathCheck('length(@)', 2),
        ])

        self.cmd('containerapp hostname list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].bindingType', "SniEnabled"),
            JMESPathCheck('[0].certificateId', cert_id),
            JMESPathCheck('[1].bindingType', "SniEnabled"),
            JMESPathCheck('[1].certificateId', cert_id),
        ])

        # delete hostname with a wrong location
        self.cmd('containerapp hostname delete -g {} -n {} --hostname {} -l "{}" --yes'.format(resource_group, ca_name, hostname_1, "eastus2"), expect_failure=True)

        self.cmd('containerapp hostname delete -g {} -n {} --hostname {} -l "{}" --yes'.format(resource_group, ca_name, hostname_1, app["location"]), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', hostname_2),
            JMESPathCheck('[0].bindingType', "SniEnabled"),
            JMESPathCheck('[0].certificateId', cert_id),
        ]).get_output_in_json()

        self.cmd('containerapp hostname list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', hostname_2),
            JMESPathCheck('[0].bindingType', "SniEnabled"),
            JMESPathCheck('[0].certificateId', cert_id),
        ])

        self.cmd('containerapp hostname delete -g {} -n {} --hostname {} --yes'.format(resource_group, ca_name, hostname_2), checks=[
            JMESPathCheck('length(@)', 0),
        ]).get_output_in_json()

        # add binding by cert id
        self.cmd('containerapp hostname bind -g {} -n {} --hostname {} --certificate {}'.format(resource_group, ca_name, hostname_2, cert_id), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].bindingType', "SniEnabled"),
            JMESPathCheck('[0].certificateId', cert_id),
            JMESPathCheck('[0].name', hostname_2),
        ]).get_output_in_json()

        self.cmd('containerapp hostname delete -g {} -n {} --hostname {} --yes'.format(resource_group, ca_name, hostname_2), checks=[
            JMESPathCheck('length(@)', 0),
        ]).get_output_in_json()

        # add binding by cert name, with and without environment
        cert_name = parse_resource_id(cert_id)["resource_name"]

        self.cmd('containerapp hostname bind -g {} -n {} --hostname {} --certificate {}'.format(resource_group, ca_name, hostname_1, cert_name), expect_failure=True)

        self.cmd('containerapp hostname bind -g {} -n {} --hostname {} --certificate {} -e {}'.format(resource_group, ca_name, hostname_1, cert_name, env_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].bindingType', "SniEnabled"),
            JMESPathCheck('[0].certificateId', cert_id),
            JMESPathCheck('[0].name', hostname_1),
        ]).get_output_in_json()

        self.cmd('containerapp hostname delete -g {} -n {} --hostname {} --yes'.format(resource_group, ca_name, hostname_1), checks=[
            JMESPathCheck('length(@)', 0),
        ]).get_output_in_json()

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live) and vnet command error in cli pipeline
    def test_containerapp_tcp_ingress(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='env', length=24)
        logs = self.create_random_name(prefix='logs', length=24)
        vnet = self.create_random_name(prefix='name', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        self.cmd(f"az network vnet create --address-prefixes '14.0.0.0/23' -g {resource_group} -n {vnet}")
        sub_id = self.cmd(f"az network vnet subnet create --address-prefixes '14.0.0.0/23' -n sub -g {resource_group} --vnet-name {vnet}").get_output_in_json()["id"]

        logs_id = self.cmd(f"monitor log-analytics workspace create -g {resource_group} -n {logs} -l eastus").get_output_in_json()["customerId"]
        logs_key = self.cmd(f'monitor log-analytics workspace get-shared-keys -g {resource_group} -n {logs}').get_output_in_json()["primarySharedKey"]

        self.cmd(f'containerapp env create -g {resource_group} -n {env_name} --logs-workspace-id {logs_id} --logs-workspace-key {logs_key} --internal-only -s {sub_id}')

        containerapp_env = self.cmd(f'containerapp env show -g {resource_group} -n {env_name}').get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd(f'containerapp env show -g {resource_group} -n {env_name}').get_output_in_json()

        self.cmd(f'containerapp env show -n {env_name} -g {resource_group}', checks=[
            JMESPathCheck('name', env_name),
            JMESPathCheck('properties.vnetConfiguration.internal', True),
        ])

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --transport tcp --target-port 80 --exposed-port 3000'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('external', True),
            JMESPathCheck('targetPort', 80),
            JMESPathCheck('exposedPort', 3000),
            JMESPathCheck('transport', "Tcp"),
        ])

        self.cmd('containerapp ingress enable -g {} -n {} --type internal --target-port 81 --allow-insecure --transport http2'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('external', False),
            JMESPathCheck('targetPort', 81),
            JMESPathCheck('allowInsecure', True),
            JMESPathCheck('transport', "Http2"),
        ])

        self.cmd('containerapp ingress enable -g {} -n {} --type internal --target-port 81 --transport tcp --exposed-port 3020'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('external', False),
            JMESPathCheck('targetPort', 81),
            JMESPathCheck('transport', "Tcp"),
            JMESPathCheck('exposedPort', 3020),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_ip_restrictions(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        # self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, ca_name, env_name))
        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 80'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress access-restriction set -g {} -n {} --rule-name name --ip-address 192.168.1.1/32 --description "Description here." --action Allow'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Allow"),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Allow"),
        ])

        self.cmd('containerapp ingress access-restriction set -g {} -n {} --rule-name name2 --ip-address 192.168.1.1/8 --description "Description here 2." --action Allow'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Allow"),
            JMESPathCheck('[1].name', "name2"),
            JMESPathCheck('[1].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[1].description', "Description here 2."),
            JMESPathCheck('[1].action', "Allow"),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Allow"),
            JMESPathCheck('[1].name', "name2"),
            JMESPathCheck('[1].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[1].description', "Description here 2."),
            JMESPathCheck('[1].action', "Allow"),
        ])

        self.cmd('containerapp ingress access-restriction remove -g {} -n {} --rule-name name'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name2"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[0].description', "Description here 2."),
            JMESPathCheck('[0].action', "Allow"),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name2"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[0].description', "Description here 2."),
            JMESPathCheck('[0].action', "Allow"),
        ])

        self.cmd('containerapp ingress access-restriction remove -g {} -n {} --rule-name name2'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 0),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 0),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_ip_restrictions_deny(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        # self.cmd('containerapp create -g {} -n {} --environment {}'.format(resource_group, ca_name, env_name))
        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 80'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress access-restriction set -g {} -n {} --rule-name name --ip-address 192.168.1.1/32 --description "Description here." --action Deny'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Deny"),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Deny"),
        ])

        self.cmd('containerapp ingress access-restriction set -g {} -n {} --rule-name name2 --ip-address 192.168.1.1/8 --description "Description here 2." --action Deny'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Deny"),
            JMESPathCheck('[1].name', "name2"),
            JMESPathCheck('[1].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[1].description', "Description here 2."),
            JMESPathCheck('[1].action', "Deny"),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/32"),
            JMESPathCheck('[0].description', "Description here."),
            JMESPathCheck('[0].action', "Deny"),
            JMESPathCheck('[1].name', "name2"),
            JMESPathCheck('[1].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[1].description', "Description here 2."),
            JMESPathCheck('[1].action', "Deny"),
        ])

        self.cmd('containerapp ingress access-restriction remove -g {} -n {} --rule-name name'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name2"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[0].description', "Description here 2."),
            JMESPathCheck('[0].action', "Deny"),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('[0].name', "name2"),
            JMESPathCheck('[0].ipAddressRange', "192.168.1.1/8"),
            JMESPathCheck('[0].description', "Description here 2."),
            JMESPathCheck('[0].action', "Deny"),
        ])

        self.cmd('containerapp ingress access-restriction remove -g {} -n {} --rule-name name2'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 0),
        ])

        self.cmd('containerapp ingress access-restriction list -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(@)', 0),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_cors_policy(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 80'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress cors enable -g {} -n {} --allowed-origins "http://www.contoso.com" "https://www.contoso.com" --allowed-methods "GET" "POST" --allowed-headers "header1" "header2" --expose-headers "header3" "header4" --allow-credentials true --max-age 100'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(allowedOrigins)', 2),
            JMESPathCheck('allowedOrigins[0]', "http://www.contoso.com"),
            JMESPathCheck('allowedOrigins[1]', "https://www.contoso.com"),
            JMESPathCheck('length(allowedMethods)', 2),
            JMESPathCheck('allowedMethods[0]', "GET"),
            JMESPathCheck('allowedMethods[1]', "POST"),
            JMESPathCheck('length(allowedHeaders)', 2),
            JMESPathCheck('allowedHeaders[0]', "header1"),
            JMESPathCheck('allowedHeaders[1]', "header2"),
            JMESPathCheck('length(exposeHeaders)', 2),
            JMESPathCheck('exposeHeaders[0]', "header3"),
            JMESPathCheck('exposeHeaders[1]', "header4"),
            JMESPathCheck('allowCredentials', True),
            JMESPathCheck('maxAge', 100),
        ])

        self.cmd('containerapp ingress cors update -g {} -n {} --allowed-origins "*" --allowed-methods "GET" --allowed-headers "header1" --expose-headers --allow-credentials false --max-age 0'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(allowedOrigins)', 1),
            JMESPathCheck('allowedOrigins[0]', "*"),
            JMESPathCheck('length(allowedMethods)', 1),
            JMESPathCheck('allowedMethods[0]', "GET"),
            JMESPathCheck('length(allowedHeaders)', 1),
            JMESPathCheck('allowedHeaders[0]', "header1"),
            JMESPathCheck('exposeHeaders', None),
            JMESPathCheck('allowCredentials', False),
            JMESPathCheck('maxAge', 0),
        ])

        self.cmd('containerapp ingress cors show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('length(allowedOrigins)', 1),
            JMESPathCheck('allowedOrigins[0]', "*"),
            JMESPathCheck('length(allowedMethods)', 1),
            JMESPathCheck('allowedMethods[0]', "GET"),
            JMESPathCheck('length(allowedHeaders)', 1),
            JMESPathCheck('allowedHeaders[0]', "header1"),
            JMESPathCheck('exposeHeaders', None),
            JMESPathCheck('allowCredentials', False),
            JMESPathCheck('maxAge', 0),
        ])

        self.cmd('containerapp ingress cors disable -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('corsPolicy', None),
        ])


class ContainerappDaprTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_dapr_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {} --dapr-app-id containerapp --dapr-app-port 800 --dapr-app-protocol grpc --dhmrs 4 --dhrbs 50 --dapr-log-level debug --enable-dapr'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('properties.configuration.dapr.appId', "containerapp"),
            JMESPathCheck('properties.configuration.dapr.appPort', 800),
            JMESPathCheck('properties.configuration.dapr.appProtocol', "grpc"),
            JMESPathCheck('properties.configuration.dapr.enabled', True),
            JMESPathCheck('properties.configuration.dapr.httpReadBufferSize', 50),
            JMESPathCheck('properties.configuration.dapr.httpMaxRequestSize', 4),
            JMESPathCheck('properties.configuration.dapr.logLevel', "debug"),
            JMESPathCheck('properties.configuration.dapr.enableApiLogging', False),
        ])

        self.cmd('containerapp dapr enable -g {} -n {} --dapr-app-id containerapp1 --dapr-app-port 80 --dapr-app-protocol http --dal --dhmrs 6 --dhrbs 60 --dapr-log-level warn'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('appId', "containerapp1"),
            JMESPathCheck('appPort', 80),
            JMESPathCheck('appProtocol', "http"),
            JMESPathCheck('enabled', True),
            JMESPathCheck('httpReadBufferSize', 60),
            JMESPathCheck('httpMaxRequestSize', 6),
            JMESPathCheck('logLevel', "warn"),
            JMESPathCheck('enableApiLogging', True),
        ])

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('properties.configuration.dapr.appId', "containerapp1"),
            JMESPathCheck('properties.configuration.dapr.appPort', 80),
            JMESPathCheck('properties.configuration.dapr.appProtocol', "http"),
            JMESPathCheck('properties.configuration.dapr.enabled', True),
            JMESPathCheck('properties.configuration.dapr.httpReadBufferSize', 60),
            JMESPathCheck('properties.configuration.dapr.httpMaxRequestSize', 6),
            JMESPathCheck('properties.configuration.dapr.logLevel', "warn"),
            JMESPathCheck('properties.configuration.dapr.enableApiLogging', True),
        ])

        self.cmd('containerapp dapr disable -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('appId', "containerapp1"),
            JMESPathCheck('appPort', 80),
            JMESPathCheck('appProtocol', "http"),
            JMESPathCheck('enabled', False),
            JMESPathCheck('httpReadBufferSize', 60),
            JMESPathCheck('httpMaxRequestSize', 6),
            JMESPathCheck('logLevel', "warn"),
            JMESPathCheck('enableApiLogging', True),
        ])

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, ca_name), checks=[
            JMESPathCheck('properties.configuration.dapr.appId', "containerapp1"),
            JMESPathCheck('properties.configuration.dapr.appPort', 80),
            JMESPathCheck('properties.configuration.dapr.appProtocol', "http"),
            JMESPathCheck('properties.configuration.dapr.enabled', False),
            JMESPathCheck('properties.configuration.dapr.httpReadBufferSize', 60),
            JMESPathCheck('properties.configuration.dapr.httpMaxRequestSize', 6),
            JMESPathCheck('properties.configuration.dapr.logLevel', "warn"),
            JMESPathCheck('properties.configuration.dapr.enableApiLogging', True),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_up_dapr_e2e(self, resource_group):
        """ Ensure that dapr can be enabled if the app has been created using containerapp up """
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        image = 'mcr.microsoft.com/azuredocs/aks-helloworld:v1'
        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd(
            'containerapp up -g {} -n {} --environment {} --image {}'.format(
                resource_group, ca_name, env_name, image))

        self.cmd(
            'containerapp dapr enable -g {} -n {} --dapr-app-id containerapp1 --dapr-app-port 80 '
            '--dapr-app-protocol http --dal --dhmrs 6 --dhrbs 60 --dapr-log-level warn'.format(
                resource_group, ca_name, env_name), checks=[
                JMESPathCheck('appId', "containerapp1"),
                JMESPathCheck('enabled', True)
            ])


class ContainerappServiceBindingTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus2")
    def test_containerapp_dev_service_binding_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)
        image = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
        redis_ca_name = 'redis'
        postgres_ca_name = 'postgres'
        kafka_ca_name = 'kafka'
        mariadb_ca_name = 'mariadb'

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp service redis create -g {} -n {} --environment {}'.format(
            resource_group, redis_ca_name, env_name))

        self.cmd('containerapp service postgres create -g {} -n {} --environment {}'.format(
            resource_group, postgres_ca_name, env_name))
        
        self.cmd('containerapp service kafka create -g {} -n {} --environment {}'.format(
            resource_group, kafka_ca_name, env_name))

        self.cmd('containerapp service mariadb create -g {} -n {} --environment {}'.format(
            resource_group, mariadb_ca_name, env_name))

        self.cmd('containerapp create -g {} -n {} --environment {} --image {} --bind postgres:postgres_binding redis'.format(
            resource_group, ca_name, env_name, image), checks=[
            JMESPathCheck('properties.template.serviceBinds[0].name', "postgres_binding"),
            JMESPathCheck('properties.template.serviceBinds[1].name', "redis")
        ])

        self.cmd('containerapp update -g {} -n {} --unbind postgres_binding'.format(
            resource_group, ca_name, image), checks=[
            JMESPathCheck('properties.template.serviceBinds[0].name', "redis"),
        ])

        self.cmd('containerapp update -g {} -n {} --bind postgres:postgres_binding kafka mariadb'.format(
            resource_group, ca_name, image), checks=[
            JMESPathCheck('properties.template.serviceBinds[0].name', "redis"),
            JMESPathCheck('properties.template.serviceBinds[1].name', "postgres_binding"),
            JMESPathCheck('properties.template.serviceBinds[2].name', "kafka"),
            JMESPathCheck('properties.template.serviceBinds[3].name', "mariadb")
        ])

        self.cmd('containerapp service postgres delete -g {} -n {} --yes'.format(
            resource_group, postgres_ca_name, env_name))

        self.cmd('containerapp service redis delete -g {} -n {} --yes'.format(
            resource_group, redis_ca_name, env_name))

        self.cmd('containerapp service kafka delete -g {} -n {} --yes'.format(
            resource_group, kafka_ca_name, env_name))

        self.cmd('containerapp service mariadb delete -g {} -n {} --yes'.format(
            resource_group, mariadb_ca_name, env_name))

        self.cmd('containerapp service list -g {} --environment {}'.format(resource_group, env_name), checks=[
            JMESPathCheck('length(@)', 0),
        ])


class ContainerappEnvStorageTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @live_only()  # Passes locally but fails in CI
    @ResourceGroupPreparer(location="eastus")
    def test_containerapp_env_storage(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        storage_name = self.create_random_name(prefix='storage', length=24)
        shares_name = self.create_random_name(prefix='share', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('storage account create -g {} -n {} --kind StorageV2 --sku Standard_LRS --enable-large-file-share'.format(resource_group, storage_name))
        self.cmd('storage share-rm create -g {} -n {} --storage-account {} --access-tier "TransactionOptimized" --quota 1024'.format(resource_group, shares_name, storage_name))

        storage_keys = self.cmd('az storage account keys list -g {} -n {}'.format(resource_group, storage_name)).get_output_in_json()[0]

        self.cmd('containerapp env storage set -g {} -n {} --storage-name {} --azure-file-account-name {} --azure-file-account-key {} --access-mode ReadOnly --azure-file-share-name {}'.format(resource_group, env_name, storage_name, storage_name, storage_keys["value"], shares_name), checks=[
            JMESPathCheck('name', storage_name),
        ])

        self.cmd('containerapp env storage show -g {} -n {} --storage-name {}'.format(resource_group, env_name, storage_name), checks=[
            JMESPathCheck('name', storage_name),
        ])

        self.cmd('containerapp env storage list -g {} -n {}'.format(resource_group, env_name), checks=[
            JMESPathCheck('[0].name', storage_name),
        ])

        self.cmd('containerapp env storage remove -g {} -n {} --storage-name {} --yes'.format(resource_group, env_name, storage_name))

        self.cmd('containerapp env storage list -g {} -n {}'.format(resource_group, env_name), checks=[
            JMESPathCheck('length(@)', 0),
        ])


class ContainerappRevisionTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_revision_label_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_name = self.create_random_name(prefix='containerapp-env', length=24)
        ca_name = self.create_random_name(prefix='containerapp', length=24)

        create_containerapp_env(self, env_name, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp ingress show -g {} -n {}'.format(resource_group, ca_name, env_name), checks=[
            JMESPathCheck('external', True),
            JMESPathCheck('targetPort', 80),
        ])

        self.cmd('containerapp create -g {} -n {} --environment {} --ingress external --target-port 80 --image nginx'.format(resource_group, ca_name, env_name))

        self.cmd('containerapp revision set-mode -g {} -n {} --mode multiple'.format(resource_group, ca_name, env_name))

        revision_names = self.cmd(f"containerapp revision list -g {resource_group} -n {ca_name} --all --query '[].name'").get_output_in_json()

        self.assertEqual(len(revision_names), 2)

        labels = []
        for revision in revision_names:
            label = self.create_random_name(prefix='label', length=12)
            labels.append(label)
            self.cmd(f"containerapp revision label add -g {resource_group} -n {ca_name} --revision {revision} --label {label}")

        traffic_weight = self.cmd(f"containerapp ingress traffic show -g {resource_group} -n {ca_name} --query '[].name'").get_output_in_json()

        for traffic in traffic_weight:
            if "label" in traffic:
                self.assertEqual(traffic["label"] in labels, True)

        self.cmd(f"containerapp ingress traffic set -g {resource_group} -n {ca_name} --revision-weight latest=50 --label-weight {labels[0]}=25 {labels[1]}=25")

        traffic_weight = self.cmd(f"containerapp ingress traffic show -g {resource_group} -n {ca_name} --query '[].name'").get_output_in_json()

        for traffic in traffic_weight:
            if "label" in traffic:
                self.assertEqual(traffic["weight"], 25)
            else:
                self.assertEqual(traffic["weight"], 50)

        traffic_weight = self.cmd(f"containerapp revision label swap -g {resource_group} -n {ca_name} --source {labels[0]} --target {labels[1]}").get_output_in_json()

        for revision in revision_names:
            traffic = [w for w in traffic_weight if "revisionName" in w and w["revisionName"] == revision][0]
            self.assertEqual(traffic["label"], labels[(revision_names.index(revision) + 1) % 2])

        self.cmd(f"containerapp revision label remove -g {resource_group} -n {ca_name} --label {labels[0]}", checks=[
            JMESPathCheck('length(@)', 3),
        ])

        self.cmd(f"containerapp revision label remove -g {resource_group} -n {ca_name} --label {labels[1]}", checks=[
            JMESPathCheck('length(@)', 3),
        ])

        traffic_weight = self.cmd(f"containerapp ingress traffic show -g {resource_group} -n {ca_name}").get_output_in_json()

        self.assertEqual(len([w for w in traffic_weight if "label" in w]), 0)


class ContainerappAnonymousRegistryTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_anonymous_registry(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)
        image = "mcr.microsoft.com/k8se/quickstart:latest"

        create_containerapp_env(self, env, resource_group)

        self.cmd(f'containerapp create -g {resource_group} -n {app} --image {image} --ingress external --target-port 80 --environment {env}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[JMESPathCheck("properties.provisioningState", "Succeeded")])


class ContainerappRegistryIdentityTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_registry_identity_user(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)
        identity = self.create_random_name(prefix='id', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        image_source = "mcr.microsoft.com/k8se/quickstart:latest"
        image_name = f"{acr}.azurecr.io/k8se/quickstart:latest"

        create_containerapp_env(self, env, resource_group)

        identity_rid = self.cmd(f'identity create -g {resource_group} -n {identity}').get_output_in_json()["id"]

        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        self.cmd(f'acr import -n {acr} --source {image_source}')

        self.cmd(f'containerapp create -g {resource_group} -n {app} --registry-identity {identity_rid} --image {image_name} --ingress external --target-port 80 --environment {env} --registry-server {acr}.azurecr.io')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[JMESPathCheck("properties.provisioningState", "Succeeded")])

        app2 = self.create_random_name(prefix='aca', length=24)
        self.cmd(f'containerapp create -g {resource_group} -n {app2} --registry-identity {identity_rid} --image {image_name} --ingress external --target-port 80 --environment {env} --registry-server {acr}.azurecr.io --revision-suffix test1')

        self.cmd(f'containerapp show -g {resource_group} -n {app2}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.template.revisionSuffix", "test1"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_registry_identity_system(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        image_source = "mcr.microsoft.com/k8se/quickstart:latest"
        image_name = f"{acr}.azurecr.io/k8se/quickstart:latest"

        create_containerapp_env(self, env, resource_group)

        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        self.cmd(f'acr import -n {acr} --source {image_source}')

        self.cmd(f'containerapp create -g {resource_group} -n {app} --registry-identity "system" --image {image_name} --ingress external --target-port 80 --environment {env} --registry-server {acr}.azurecr.io')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[JMESPathCheck("properties.provisioningState", "Succeeded")])

        app2 = self.create_random_name(prefix='aca', length=24)
        self.cmd(f'containerapp create -g {resource_group} -n {app2} --registry-identity "system" --image {image_name} --ingress external --target-port 80 --environment {env} --registry-server {acr}.azurecr.io --revision-suffix test1')

        self.cmd(f'containerapp show -g {resource_group} -n {app2}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.template.revisionSuffix", "test1"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_private_registry_port(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        image_source = "mcr.microsoft.com/k8se/quickstart:latest"
        image_name = f"{acr}.azurecr.io:443/k8se/quickstart:latest"

        create_containerapp_env(self, env, resource_group)

        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        self.cmd(f'acr import -n {acr} --source {image_source}')
        password = self.cmd(f'acr credential show -n {acr} --query passwords[0].value').get_output_in_json()

        self.cmd(f'containerapp create -g {resource_group} -n {app}  --image {image_name} --ingress external --target-port 80 --environment {env} --registry-server {acr}.azurecr.io:443 --registry-username {acr} --registry-password {password}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.registries[0].server", f"{acr}.azurecr.io:443"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
            JMESPathCheck("properties.configuration.secrets[0].name", f"{acr}azurecrio-443-{acr}")
        ])

        app2 = self.create_random_name(prefix='aca', length=24)
        image_name = f"{acr}.azurecr.io/k8se/quickstart:latest"
        self.cmd(
            f'containerapp create -g {resource_group} -n {app2}  --image {image_name} --ingress external --target-port 80 --environment {env} --registry-server {acr}.azurecr.io --registry-username {acr} --registry-password {password}')

        self.cmd(f'containerapp show -g {resource_group} -n {app2}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.registries[0].server", f"{acr}.azurecr.io"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
            JMESPathCheck("properties.configuration.secrets[0].name", f"{acr}azurecrio-{acr}")
        ])


class ContainerappScaleTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_scale_create(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)

        create_containerapp_env(self, env, resource_group)

        self.cmd(f'containerapp create -g {resource_group} -n {app} --image nginx --ingress external --target-port 80 --environment {env} --scale-rule-name http-scale-rule --scale-rule-http-concurrency 50 --scale-rule-auth trigger=secretref --scale-rule-metadata key=value')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.template.scale.rules[0].name", "http-scale-rule"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.concurrentRequests", "50"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.key", "value"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].triggerParameter", "trigger"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].secretRef", "secretref"),
        ])

        self.cmd(f'containerapp create -g {resource_group} -n {app}2 --image nginx --environment {env} --scale-rule-name my-datadog-rule --scale-rule-type datadog --scale-rule-metadata "queryValue=7" "age=120" "metricUnavailableValue=0" --scale-rule-auth "apiKey=api-key" "appKey=app-key"')

        self.cmd(f'containerapp show -g {resource_group} -n {app}2', checks=[
            JMESPathCheck("properties.template.scale.rules[0].name", "my-datadog-rule"),
            JMESPathCheck("properties.template.scale.rules[0].custom.type", "datadog"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.queryValue", "7"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.age", "120"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.metricUnavailableValue", "0"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].triggerParameter", "apiKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].secretRef", "api-key"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].triggerParameter", "appKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].secretRef", "app-key"),

        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_scale_update(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)

        create_containerapp_env(self, env, resource_group)

        self.cmd(f'containerapp create -g {resource_group} -n {app} --image nginx --ingress external --target-port 80 --environment {env} --scale-rule-name http-scale-rule --scale-rule-http-concurrency 50 --scale-rule-auth trigger=secretref --scale-rule-metadata key=value')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.template.scale.rules[0].name", "http-scale-rule"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.concurrentRequests", "50"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.key", "value"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].triggerParameter", "trigger"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].secretRef", "secretref"),
        ])

        self.cmd(f'containerapp update -g {resource_group} -n {app} --image nginx --scale-rule-name my-datadog-rule --scale-rule-type datadog --scale-rule-metadata "queryValue=7" "age=120" "metricUnavailableValue=0"  --scale-rule-auth "apiKey=api-key" "appKey=app-key"')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.template.scale.rules[0].name", "my-datadog-rule"),
            JMESPathCheck("properties.template.scale.rules[0].custom.type", "datadog"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.queryValue", "7"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.age", "120"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.metricUnavailableValue", "0"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].triggerParameter", "apiKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].secretRef", "api-key"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].triggerParameter", "appKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].secretRef", "app-key"),

        ])

        self.cmd(f'containerapp update -g {resource_group} -n {app} --cpu 0.5 --no-wait')
        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.template.containers[0].resources.cpu", "0.5"),
            JMESPathCheck("properties.template.scale.rules[0].name", "my-datadog-rule"),
            JMESPathCheck("properties.template.scale.rules[0].custom.type", "datadog"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.queryValue", "7"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.age", "120"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.metricUnavailableValue", "0"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].triggerParameter", "apiKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].secretRef", "api-key"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].triggerParameter", "appKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].secretRef", "app-key"),
        ])


    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_scale_revision_copy(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)

        create_containerapp_env(self, env, resource_group)

        self.cmd(f'containerapp create -g {resource_group} -n {app} --image nginx --ingress external --target-port 80 --environment {env} --scale-rule-name http-scale-rule --scale-rule-http-concurrency 50 --scale-rule-auth trigger=secretref --scale-rule-metadata key=value')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.template.scale.rules[0].name", "http-scale-rule"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.concurrentRequests", "50"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.key", "value"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].triggerParameter", "trigger"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].secretRef", "secretref"),
        ])

        self.cmd(f'containerapp revision copy -g {resource_group} -n {app} --image nginx --scale-rule-name my-datadog-rule --scale-rule-type datadog --scale-rule-metadata "queryValue=7" "age=120" "metricUnavailableValue=0"  --scale-rule-auth "apiKey=api-key" "appKey=app-key"')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.template.scale.rules[0].name", "my-datadog-rule"),
            JMESPathCheck("properties.template.scale.rules[0].custom.type", "datadog"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.queryValue", "7"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.age", "120"),
            JMESPathCheck("properties.template.scale.rules[0].custom.metadata.metricUnavailableValue", "0"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].triggerParameter", "apiKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[0].secretRef", "api-key"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].triggerParameter", "appKey"),
            JMESPathCheck("properties.template.scale.rules[0].custom.auth[1].secretRef", "app-key"),

        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_create_with_yaml(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='yaml', length=24)

        create_containerapp_env(self, env, resource_group)
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        user_identity_name = self.create_random_name(prefix='containerapp-user', length=24)
        user_identity = self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name)).get_output_in_json()
        user_identity_id = user_identity['id']

        # test managedEnvironmentId
        containerapp_yaml_text = f"""
            location: {TEST_LOCATION}
            type: Microsoft.App/containerApps
            tags:
                tagname: value
            properties:
              managedEnvironmentId: {containerapp_env["id"]}
              configuration:
                activeRevisionsMode: Multiple
                ingress:
                  external: true
                  allowInsecure: false
                  targetPort: 80
                  traffic:
                    - latestRevision: true
                      weight: 100
                  transport: Auto
                  ipSecurityRestrictions:
                    - name: name
                      ipAddressRange: "1.1.1.1/10"
                      action: "Allow"
              template:
                revisionSuffix: myrevision
                terminationGracePeriodSeconds: 90
                containers:
                  - image: nginx
                    name: nginx
                    env:
                      - name: HTTP_PORT
                        value: 80
                    command:
                      - npm
                      - start
                    resources:
                      cpu: 0.5
                      memory: 1Gi
                scale:
                  minReplicas: 1
                  maxReplicas: 3
                  rules:
                  - http:
                      auth:
                      - secretRef: secretref
                        triggerParameter: trigger
                      metadata:
                        concurrentRequests: '50'
                        key: value
                    name: http-scale-rule
            identity:
              type: UserAssigned
              userAssignedIdentities:
                {user_identity_id}: {{}}
            """
        containerapp_file_name = f"{self._testMethodName}_containerapp.yml"

        write_test_file(containerapp_file_name, containerapp_yaml_text)
        self.cmd(f'containerapp create -n {app} -g {resource_group} --environment {env} --yaml {containerapp_file_name}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.ingress.external", True),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].name", "name"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].ipAddressRange", "1.1.1.1/10"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].action", "Allow"),
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision"),
            JMESPathCheck("properties.template.terminationGracePeriodSeconds", 90),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3),
            JMESPathCheck("properties.template.scale.rules[0].name", "http-scale-rule"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.concurrentRequests", "50"),
            JMESPathCheck("properties.template.scale.rules[0].http.metadata.key", "value"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].triggerParameter", "trigger"),
            JMESPathCheck("properties.template.scale.rules[0].http.auth[0].secretRef", "secretref"),
        ])

        # test environmentId
        containerapp_yaml_text = f"""
                    location: {TEST_LOCATION}
                    type: Microsoft.App/containerApps
                    tags:
                        tagname: value
                    properties:
                      environmentId: {containerapp_env["id"]}
                      configuration:
                        activeRevisionsMode: Multiple
                        ingress:
                          external: true
                          allowInsecure: false
                          targetPort: 80
                          traffic:
                            - latestRevision: true
                              weight: 100
                          transport: Auto
                      template:
                        revisionSuffix: myrevision2
                        containers:
                          - image: nginx
                            name: nginx
                            env:
                              - name: HTTP_PORT
                                value: 80
                            command:
                              - npm
                              - start
                            resources:
                              cpu: 0.5
                              memory: 1Gi
                        scale:
                          minReplicas: 1
                          maxReplicas: 3
                          rules: []
                    """
        write_test_file(containerapp_file_name, containerapp_yaml_text)

        self.cmd(f'containerapp update -n {app} -g {resource_group} --yaml {containerapp_file_name}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.ingress.external", True),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].name", "name"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].ipAddressRange", "1.1.1.1/10"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].action", "Allow"),
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision2"),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3),
            JMESPathCheck("properties.template.scale.rules", None)
        ])

        # test update without environmentId
        containerapp_yaml_text = f"""
                            properties:
                              template:
                                revisionSuffix: myrevision3
                            """
        write_test_file(containerapp_file_name, containerapp_yaml_text)

        self.cmd(f'containerapp update -n {app} -g {resource_group} --yaml {containerapp_file_name}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision3")
        ])
        clean_up_test_file(containerapp_file_name)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    @live_only()  # encounters 'CannotOverwriteExistingCassetteException' only when run from recording (passes when run live)
    def test_containerapp_create_with_vnet_yaml(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        vnet = self.create_random_name(prefix='name', length=24)

        self.cmd(f"network vnet create --address-prefixes '14.0.0.0/23' -g {resource_group} -n {vnet}")
        sub_id = self.cmd(f"network vnet subnet create --address-prefixes '14.0.0.0/23' -n sub -g {resource_group} --vnet-name {vnet}").get_output_in_json()["id"]

        self.cmd(f'containerapp env create -g {resource_group} -n {env} --internal-only -s {sub_id}')
        containerapp_env = self.cmd(f'containerapp env show -g {resource_group} -n {env}').get_output_in_json()

        while containerapp_env["properties"]["provisioningState"].lower() == "waiting":
            time.sleep(5)
            containerapp_env = self.cmd(f'containerapp env show -g {resource_group} -n {env}').get_output_in_json()

        app = self.create_random_name(prefix='yaml', length=24)

        user_identity_name = self.create_random_name(prefix='containerapp-user', length=24)
        user_identity = self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name)).get_output_in_json()
        user_identity_id = user_identity['id']

        # test create containerapp transport: Tcp, with exposedPort
        containerapp_yaml_text = f"""
        location: {TEST_LOCATION}
        type: Microsoft.App/containerApps
        tags:
            tagname: value
        properties:
          managedEnvironmentId: {containerapp_env["id"]}
          configuration:
            activeRevisionsMode: Multiple
            ingress:
              external: true
              exposedPort: 3000
              allowInsecure: false
              targetPort: 80
              traffic:
                - latestRevision: true
                  weight: 100
              transport: Tcp
          template:
            revisionSuffix: myrevision
            containers:
              - image: nginx
                name: nginx
                env:
                  - name: HTTP_PORT
                    value: 80
                command:
                  - npm
                  - start
                resources:
                  cpu: 0.5
                  memory: 1Gi
            scale:
              minReplicas: 1
              maxReplicas: 3
        identity:
          type: UserAssigned
          userAssignedIdentities:
            {user_identity_id}: {{}}
        """
        containerapp_file_name = f"{self._testMethodName}_containerapp.yml"

        write_test_file(containerapp_file_name, containerapp_yaml_text)
        self.cmd(f'containerapp create -n {app} -g {resource_group} --environment {env} --yaml {containerapp_file_name}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.ingress.external", True),
            JMESPathCheck("properties.configuration.ingress.exposedPort", 3000),
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision"),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3)
        ])

        # test update containerapp transport: Tcp, with exposedPort
        containerapp_yaml_text = f"""
                location: {TEST_LOCATION}
                type: Microsoft.App/containerApps
                tags:
                    tagname: value
                properties:
                  environmentId: {containerapp_env["id"]}
                  configuration:
                    activeRevisionsMode: Multiple
                    ingress:
                      external: true
                      exposedPort: 9551
                      allowInsecure: false
                      targetPort: 80
                      traffic:
                        - latestRevision: true
                          weight: 100
                      transport: Tcp
                  template:
                    revisionSuffix: myrevision
                    containers:
                      - image: nginx
                        name: nginx
                        env:
                          - name: HTTP_PORT
                            value: 80
                        command:
                          - npm
                          - start
                        resources:
                          cpu: 0.5
                          memory: 1Gi
                    scale:
                      minReplicas: 1
                      maxReplicas: 3
                """
        write_test_file(containerapp_file_name, containerapp_yaml_text)

        self.cmd(f'containerapp update -n {app} -g {resource_group} --yaml {containerapp_file_name}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.ingress.external", True),
            JMESPathCheck("properties.configuration.ingress.exposedPort", 9551),
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision"),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3)
        ])

        # test create containerapp transport: http, with CORS policy
        containerapp_yaml_text = f"""
                        location: {TEST_LOCATION}
                        type: Microsoft.App/containerApps
                        tags:
                            tagname: value
                        properties:
                          environmentId: {containerapp_env["id"]}
                          configuration:
                            activeRevisionsMode: Multiple
                            ingress:
                              external: true
                              allowInsecure: false
                              clientCertificateMode: Require
                              corsPolicy:
                                allowedOrigins: [a, b]
                                allowedMethods: [c, d]
                                allowedHeaders: [e, f]
                                exposeHeaders: [g, h]
                                maxAge: 7200
                                allowCredentials: true
                              targetPort: 80
                              ipSecurityRestrictions:
                                - name: name
                                  ipAddressRange: "1.1.1.1/10"
                                  action: "Allow"
                              traffic:
                                - latestRevision: true
                                  weight: 100
                              transport: http
                          template:
                            revisionSuffix: myrevision
                            containers:
                              - image: nginx
                                name: nginx
                                env:
                                  - name: HTTP_PORT
                                    value: 80
                                command:
                                  - npm
                                  - start
                                resources:
                                  cpu: 0.5
                                  memory: 1Gi
                            scale:
                              minReplicas: 1
                              maxReplicas: 3
                        """
        write_test_file(containerapp_file_name, containerapp_yaml_text)
        app2 = self.create_random_name(prefix='yaml', length=24)
        self.cmd(f'containerapp create -n {app2} -g {resource_group} --environment {env} --yaml {containerapp_file_name}')

        self.cmd(f'containerapp show -g {resource_group} -n {app2}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.ingress.external", True),
            JMESPathCheck("properties.configuration.ingress.clientCertificateMode", "Require"),
            JMESPathCheck("properties.configuration.ingress.corsPolicy.allowCredentials", True),
            JMESPathCheck("properties.configuration.ingress.corsPolicy.maxAge", 7200),
            JMESPathCheck("properties.configuration.ingress.corsPolicy.allowedHeaders[0]", "e"),
            JMESPathCheck("properties.configuration.ingress.corsPolicy.allowedMethods[0]", "c"),
            JMESPathCheck("properties.configuration.ingress.corsPolicy.allowedOrigins[0]", "a"),
            JMESPathCheck("properties.configuration.ingress.corsPolicy.exposeHeaders[0]", "g"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].name", "name"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].ipAddressRange", "1.1.1.1/10"),
            JMESPathCheck("properties.configuration.ingress.ipSecurityRestrictions[0].action", "Allow"),
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.template.revisionSuffix", "myrevision"),
            JMESPathCheck("properties.template.containers[0].name", "nginx"),
            JMESPathCheck("properties.template.scale.minReplicas", 1),
            JMESPathCheck("properties.template.scale.maxReplicas", 3)
        ])
        clean_up_test_file(containerapp_file_name)


class ContainerappOtherPropertyTests(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northeurope")
    def test_containerapp_termination_grace_period_seconds(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)
        image = "mcr.microsoft.com/k8se/quickstart:latest"
        terminationGracePeriodSeconds = 90
        create_containerapp_env(self, env, resource_group)

        self.cmd(f'containerapp create -g {resource_group} -n {app} --image {image} --ingress external --target-port 80 --environment {env} --termination-grace-period {terminationGracePeriodSeconds}')

        self.cmd(f'containerapp show -g {resource_group} -n {app}', checks=[JMESPathCheck("properties.template.terminationGracePeriodSeconds", terminationGracePeriodSeconds)])

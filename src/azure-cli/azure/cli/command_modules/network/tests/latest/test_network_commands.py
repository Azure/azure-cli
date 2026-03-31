import os
import unittest
import tempfile

from azure.cli.testsdk.constants import AUX_SUBSCRIPTION
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.core.exceptions import HttpResponseError
from .recording_processors import StorageAccountSASReplacer

from azure.cli.testsdk import (
    ScenarioTest, LiveScenarioTest, LocalContextScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, live_only,
    KeyVaultPreparer, record_only)

from knack.util import CLIError

from azure.mgmt.core.tools import resource_id

from .credential_replacer import ExpressRoutePortLOAContentReplacer

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
CERTS_DIR = os.path.join(TEST_DIR, 'certs')

class NetworkVnetGatewayFailoverAPIsTest(ScenarioTest):

    @live_only()
    def test_start_site_failover_test(self): # live_only as the express route is extremely expensive, contact service team for an available ER
        resource_group = "shubhati_failover"  
        vnet_gateway_name = "shubhati_failoverGw"
        peering_location = "London2"

        self.kwargs.update({
            'rg': resource_group,
            'vnet_gw': vnet_gateway_name,
            'peering_loc': peering_location
        })

        # Run the command
        result = self.cmd(
            'network vnet-gateway start-site-failover-test '
            '-g {rg} --virtual-network-gateway-name {vnet_gw} --peering-location {peering_loc}'
        ).get_output_in_json()

        # Validate that result is a string (per _schema_on_200 = AAZStrType())
        self.assertIsInstance(result, dict)

    @live_only()
    def test_stop_site_failover_test(self): # live_only as the express route is extremely expensive, contact service team for an available ER
        import time

        time.sleep(2 * 60)  # 120 seconds To wait for sometime before stopping the test failover
        resource_group = "shubhati_failover"
        vnet_gateway_name = "shubhati_failoverGw"
        peering_location = "London2"
        was_simulation_successful = True

        # Construct failover test connection details
        failover_details = [
            {
                "failover-connection-name": "failoverGR",
                "failover-location": "Amsterdam",
                "is-verified": True
            }
        ]

        # Convert details list to CLI argument format
        details_arg = "[" + ",".join(
            "{{failover-connection-name:{},failover-location:{},is-verified:{}}}".format(
                d["failover-connection-name"],
                d["failover-location"],
                str(d["is-verified"]).lower()
            ) for d in failover_details
        ) + "]"

        self.kwargs.update({
            'rg': resource_group,
            'vnet_gw': vnet_gateway_name,
            'peering_loc': peering_location,
            'was_successful': was_simulation_successful,
            'details_arg': details_arg
        })

        # Run the command
        result = self.cmd(
            'network vnet-gateway stop-site-failover-test '
            '-g {rg} --virtual-network-gateway-name {vnet_gw} '
            '--peering-location {peering_loc} '
            '--was-simulation-successful {was_successful} '
            '--details \'{details_arg}\''
        ).get_output_in_json()

        # Validate
        self.assertTrue(isinstance(result, (str, dict)))

class NetworkVnetGatewayRoutesAndResiliencyInfoScenarioTest(ScenarioTest):

    @live_only()
    @ResourceGroupPreparer(name_prefix='test_vnet_gw_routes_resiliency_info', location='eastus2euap')
    @AllowLargeResponse(size_kb=9999)
    def test_network_vnet_gateway_get_routes_and_resiliency_information(self, resource_group):
        from time import sleep

        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'rg': resource_group,
            'gw': self.create_random_name('ergw', 20),
            'vnet': 'vnet1',
            'subnet': 'GatewaySubnet',
            'pip': 'pip1',
            'subscription': subscription_id
        })

        # Create Virtual Network with GatewaySubnet
        self.cmd('network vnet create -g {rg} -n {vnet} --address-prefix 10.0.0.0/16 '
                 '--subnet-name {subnet} --subnet-prefix 10.0.0.0/24', checks=[
            self.check('newVNet.name', '{vnet}')
        ])

        # Create Public IP
        self.cmd('network public-ip create -g {rg} -n {pip} --sku Standard', checks=[
            self.check('publicIp.name', '{pip}')
        ])

        # Create ExpressRoute Virtual Network Gateway
        self.cmd('network vnet-gateway create -g {rg} -n {gw} --vnet {vnet} '
                 '--public-ip-addresses {pip} --gateway-type ExpressRoute '
                 '--sku ErGw1AZ --no-wait')

        # Wait until the ExpressRoute gateway is provisioned
        self.cmd('network vnet-gateway wait -g {rg} -n {gw} --created')

        # Retry loop to verify provisioning state
        provisioning_state = self.cmd('network vnet-gateway show -g {rg} -n {gw}').get_output_in_json()['provisioningState']
        retry_count = 0
        while provisioning_state != 'Succeeded':
            if retry_count == 20:
                raise Exception(f"ExpressRoute Gateway provisioning failed. Last known state: {provisioning_state}")
            retry_count += 1
            sleep(60)
            provisioning_state = self.cmd('network vnet-gateway show -g {rg} -n {gw}').get_output_in_json()['provisioningState']

        # ---------------------------
        # Get Routes Information
        # ---------------------------
        self.cmd('network vnet-gateway get-routes-information -g {rg} --name {gw} --attempt-refresh true', checks=[
            self.check('type(@)', 'object'),
            self.check('length(lastComputedTime)', 24),  # Format: '8/22/2025 5:57:28 PM UTC' = 24 characters
            self.check('length(nextEligibleComputeTime)', 24),
            self.check('length(routeSetVersion)', 36),  # UUIDs are always 36 characters
            self.check('type(routeSets)', 'array'),
            self.check('type(circuitsMetadataMap)', 'object')
        ])

        # ---------------------------
        # Get Resiliency Information
        # ---------------------------
        self.cmd('network vnet-gateway get-resiliency-information -g {rg} --name {gw} --attempt-refresh true', checks=[
            self.check('type(@)', 'object'),
            self.check('length(overallScore)', 2),
            self.check('length(scoreChange)', 3),
            self.check('length(minScoreFromRecommendations)', 2),
            self.check('length(maxScoreFromRecommendations)', 3),
            self.check('length(lastComputedTime)', 24),
            self.check('length(nextEligibleComputeTime)', 24),
            self.check('type(components)', 'array')
        ])

class NetworkERGatewayFailoverSimulationScenarioTest(ScenarioTest):
    @live_only()
    def test_start_site_failover_test(self): # live_only as the express route is extremely expensive, contact service team for an available ER
        resource_group = "tamil-vwan-test"  
        er_gateway_name = "afcf242ff531409897c9a28b4c69096a-centraluseuap-er-gw"
        peering_location = "Washington DC"

        self.kwargs.update({
            'rg': resource_group,
            'er_gw': er_gateway_name,
            'peering_loc': peering_location
        })

        # Run the command
        result = self.cmd(
            'network express-route-gateway start-site-failover-test '
            '--resource-group {rg} --name {er_gw} --peering-location {peering_loc}'
        ).get_output_in_json()

        # Validate that result is a string (per _schema_on_200 = AAZStrType())
        self.assertIsInstance(result, dict)

    @live_only()
    def test_stop_site_failover_test(self): # live_only as the express route is extremely expensive, contact service team for an available ER
        import time

        time.sleep(2 * 60)  # 120 seconds To wait for sometime before stopping the test failover
        resource_group = "tamil-vwan-test"  
        er_gateway_name = "afcf242ff531409897c9a28b4c69096a-centraluseuap-er-gw"
        peering_location = "Washington DC"
        was_simulation_successful = True

        # Construct failover test connection details
        failover_details = [
            {
                "failover-connection-name": "ExRConnection-centraluseuap-1750696126887",
                "failover-location": "Washington DC",
                "is-verified": True
            }
        ]

        # Convert details list to CLI argument format
        details_arg = "[" + ",".join(
            "{{failover-connection-name:{},failover-location:{},is-verified:{}}}".format(
                d["failover-connection-name"],
                d["failover-location"],
                str(d["is-verified"]).lower()
            ) for d in failover_details
        ) + "]"

        self.kwargs.update({
            'rg': resource_group,
            'er_gw': er_gateway_name,
            'peering_loc': peering_location,
            'was_successful': was_simulation_successful,
            'details_arg': details_arg
        })

        # Run the command
        result = self.cmd(
            'network express-route-gateway stop-site-failover-test '
            '--resource-group {rg} --name {er_gw} '
            '--peering-location {peering_loc} '
            '--was-simulation-successful {was_successful} '
            '--details \'{details_arg}\''
        ).get_output_in_json()

        # Validate
        self.assertTrue(isinstance(result, (str, dict)))

class NetworkExpressRouteGatewayRoutesResiliencyScenarioTest(ScenarioTest):

    @live_only()  # live_only as express route gateways require expensive resources
    @ResourceGroupPreparer(name_prefix='test_express_route_gateway_routes', location='eastus')
    @AllowLargeResponse(size_kb=9999)
    def test_network_express_route_gateway_routes_and_resiliency(self, resource_group):
        """
        Test Express Route Gateway routes and resiliency information operations:
        - Get routes information
        - Get resiliency information
        """
        from time import sleep

        self.kwargs.update({
            'rg': resource_group,
            'ergw': 'test-ergw-routes',
            'vwan': 'test-vwan-routes',
            'vhub': 'test-vhub-routes',
            'attempt_refresh': True,
        })

        # Create Virtual WAN
        self.cmd('network vwan create -n {vwan} -g {rg} --type Standard', checks=[
            self.check('name', '{vwan}')
        ])

        # Create Virtual Hub
        self.cmd('network vhub create -g {rg} -n {vhub} --vwan {vwan} --address-prefix 10.6.0.0/16 --sku Standard', checks=[
            self.check('name', '{vhub}')
        ])

        # Wait for hub to be provisioned
        routing_state = self.cmd('network vhub show -g {rg} -n {vhub}').get_output_in_json()['routingState']
        retry_count = 0
        while routing_state != 'Provisioned':
            if retry_count == 20:
                raise Exception(f"Virtual Hub provisioning failed. Last known state: {routing_state}")
            retry_count += 1
            sleep(60)
            routing_state = self.cmd('network vhub show -g {rg} -n {vhub}').get_output_in_json()['routingState']

        # Create Express Route Gateway
        self.cmd('network express-route gateway create -g {rg} -n {ergw} --virtual-hub {vhub} --min-val 2', checks=[
            self.check('name', '{ergw}'),
            self.check('provisioningState', 'Succeeded')
        ])

        # Test 1: Get Routes Information
        routes_result = self.cmd(
            'network express-route-gateway get-routes-information '
            '-g {rg} --name {ergw} --attempt-refresh {attempt_refresh}'
        ).get_output_in_json()

        # Validate routes information response structure
        self.assertIsInstance(routes_result, dict)
        self.assertIn('routeSetVersion', routes_result)
        self.assertIn('lastComputedTime', routes_result)
        self.assertIn('nextEligibleComputeTime', routes_result)
        if 'routeSets' in routes_result:
            self.assertIsInstance(routes_result['routeSets'], list)
        if 'circuitsMetadataMap' in routes_result:
            self.assertIsInstance(routes_result['circuitsMetadataMap'], dict)

        # Test 2: Get Resiliency Information
        resiliency_result = self.cmd(
            'network express-route-gateway get-resiliency-information '
            '-g {rg} --name {ergw} --attempt-refresh {attempt_refresh}'
        ).get_output_in_json()

        # Validate resiliency information response structure
        self.assertIsInstance(resiliency_result, dict)
        self.assertIn('overallScore', resiliency_result)
        self.assertIn('lastComputedTime', resiliency_result)
        self.assertIn('nextEligibleComputeTime', resiliency_result)
        if 'components' in resiliency_result:
            self.assertIsInstance(resiliency_result['components'], list)
            if len(resiliency_result['components']) > 0:
                component = resiliency_result['components'][0]
                self.assertIn('name', component)
                self.assertIn('currentScore', component)
                if 'recommendations' in component:
                    self.assertIsInstance(component['recommendations'], list)

if __name__ == '__main__':
    unittest.main()
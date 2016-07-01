# NIC Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change is merged

**Automated Test**

 - delete the following:
	- test_network_app_gateway_with_defaults.yaml
	- test_network_app_gateway_with_internal_load_balancer.yaml
	- test_network_app_gateway_with_public_ip.yaml
	- test_network_app_gateway_with_subnet.yaml
 - Run the tests twice (first records, second verifies stability)

OR

Execute the follow scenarios manually:

**Create with minimum parameters (new vnet/subnet with dynamic private IP) **

  - create new application gateway
  - verify frontend IP configuration set to new subnet

**Create with Existing vnet/subnet**

  - create new vnet and subnet
  - create new application gateway with existing vnet/subnet
  - verify frontend IP configuration set to existing subnet

**Create with Static ILB Endpoint**

  - create new application gateway specifying a private IP address
  - verify frontend IP configuration is a static private IP

**Create with Public IP**

  - create new application gateway with a new public IP
  - verify frontend IP configuration set to public IP
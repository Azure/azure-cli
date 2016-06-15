# NIC Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change is merged

**automated create**

 - delete test_network_nic.yaml
 - Run test twice (first records, second verifies stability)
	- create with only required params
	- create with optional params
	- create with an existing NSG
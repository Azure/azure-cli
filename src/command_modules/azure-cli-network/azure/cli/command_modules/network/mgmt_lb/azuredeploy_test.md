# Load Balancer Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change is merged

**automated create**

 - delete test_network_load_balancer.yaml
 - Run test twice (first records, second verifies stability)
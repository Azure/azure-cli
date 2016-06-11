# NSG Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change is merged

**automated create**

 - delete test_network_nsg.yaml
 - re-run tests twice (first records, second verifies stability)
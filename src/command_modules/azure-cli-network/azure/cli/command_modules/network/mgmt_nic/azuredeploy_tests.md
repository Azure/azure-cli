# NIC Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change is merged

**Automated Test**

 - delete test_network_nic.yaml
 - Run test twice (first records, second verifies stability)

OR

Execute the follow scenarios manually:

**Create with minimum parameters**

  - create new vnet
  - create new nic with newly created vnet and its associated subnet

**Create with optional parameters**

  - create new vnet
  - create new nic with newly created vnet specifying optional parameters:
    "--ip-forwarding" (verify enabled)
	"--private-ip-address" (verify address and allocation method 'static')
	"--public-ip-address-name" (verify public ip address name)
	"--lb-nat-rule-ids" (verify rules)
	"--lb-backend-address-pool-ids" (verify address pools)

**Create with NSG**

  - create new vnet
  - create new nsg
  - create new nic with the newly created vnet and nsg
  - verify nsg

**Create with NSG and Public IP**

  - create new vnet
  - create new nsg
  - create new public ip address
  - create new nic with newly created vnet, nsg and public ip
  - verify nsg and public ip
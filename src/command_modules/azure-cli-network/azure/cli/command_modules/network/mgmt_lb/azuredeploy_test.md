# Load Balancer Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change is merged

**automated create**

 - delete test_network_load_balancer.yaml
 - Run test twice (first records, second verifies stability)
 
OR

Execute the follow scenarios manually:

**Create with minimum parameters**

  - create new lb with the minimum required parameters
  - verify new dynamic public IP created

**Create internet facing LB with new static public IP**

  - create new lb with static public IP allocation
  - verify new static public IP created

**Create internal LB with existing subnet ID**

  - create new vnet
  - create new lb with the newly created vnet and subnet, specifying a private IP address
  - verify private IP address allocation method is static
  - verify lb is associated with the subnet and not a public IP

**Create internet facing LB with existing public IP**

  - create new public IP
  - create new lb using the public IP
  - verify lb is associated with the newly created public IP

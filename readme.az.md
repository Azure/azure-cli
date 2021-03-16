

## Azure CLI

These settings apply only when `--az` is specified on the command line.

``` yaml $(az)
az:
  extensions: network
  namespace: azure.mgmt.network
  package-name: azure-mgmt-network
  disable-checks: true
  randomize-names: true
  test-unique-resource: true
az-output-folder: $(azure-cli-folder)/src/azure-cli/azure/cli/command_modules/network
python-sdk-output-folder: "$(azure-cli-folder)/src/azure-cli/azure/cli/command_modules/network/vendored_sdks/network"
compatible-level: track2
```

### -----start of auto generated cli-directive----- ###
``` yaml $(az)
directive:

  - where:
      group: network express-route-circuit-connection
    set:
      group: network express-route-peering-connection
  - where:
      group: network express-route-peering-connection
    set:
      group: network express-route peering-connection
  - where:
      group: network express-route peering-connection
    set:
      group: network express-route peering connection

  - where:
      group: network express-route-circuit
    set:
      group: network express-route

cli:
  cli-directive:
    - where:
        group: '*'
        op: '*'
      hidden: true
    - where:
        group: 'ExpressRouteCircuitConnections'
        op: List
        apiVersion: '2018-11-01'
      hidden: false
    - where:
        group: 'ExpressRouteCircuits'
        op: ListRoutesTableSummary
        apiVersion: '2017-06-01'
      hidden: false
    - where:
        group: 'ExpressRouteCircuits'
        op: GetPeeringStats
        apiVersion: '2017-03-01'
      hidden: false
```
### -----end of auto generated cli-directive----- ###

# Azure CLI Serial Console Extension #
This is a extension for Serial Console Connections

### How to use ###
Install this extension using the CLI command below
```
az extension add --name serial-console
```

### Included Features ###
#### Connect to the text-based Serial Console of a VM or VMSS Instance ####
To exit serial console type Ctrl + ] and then q. To send an NMI/SysRq/Reset type Ctrl + ] and then n/s/r respectively.
```
az serial-console connect -n MyVM -g MyResourceGroup
```
#### Enable the serial console service for an entire subscription ####
```
az serial-console enable
```
#### Disable the serial console service for an entire subscription ####
```
az serial-console disable
```
#### Send a Non-Maskable Interrupt (NMI) to a VM or VMSS Instance ####
```
az serial-console send nmi -n MyVM -g MyResourceGroup
```
#### Send SysRq sequence to a VM or VMSS Instance ####
```
az serial-console send sysrq -n MyVM -g MyResourceGroup --input c
```
#### Perform a "hard" restart of the VM or VMSS Instance ####
```
az serial-console send reset -n MyVM -g MyResourceGroup
```
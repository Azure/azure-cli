import yaml
helps = {'test_group1 test_group2': """
            type: group
            short-summary: this module does xyz one-line or so
            long-summary: |
                this module.... kjsdflkj... klsfkj paragraph1
                this module.... kjsdflkj... klsfkj paragraph2
            examples:
                - name: foo example
                  text: example details
            """,
         'vm create': """
            type: command
            short-summary: Create an Azure Virtual Machine
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-quick-create-cli/ for an end-to-end tutorial
            parameters: 
                - name: --image
                  type: string
                  required: false
                  short-summary: OS image
                  long-summary: |
                    Common OS types: CentOS, CoreOS, Debian, openSUSE, RHEL, SLES, UbuntuLTS,
                    Win2012R2Datacenter, Win2012Datacenter, Win2008R2SP1
                    Example URN: canonical:Ubuntu_Snappy_Core:15.04:2016.0318.1949
                    Example URI: http://<storageAccount>.blob.core.windows.net/vhds/osdiskimage.vhd
                  populator-commands: 
                    - az vm image list
                    - az vm image show
            examples:
                - name: Create a simple Windows Server VM with private IP address
                  text: >
                    az vm create --image Win2012R2Datacenter --admin-username myadmin --admin-password Admin_001 
                    -l "West US" -g myvms --name myvm001
                - name: Create a Linux VM with SSH key authentication, add a public DNS entry and add to an existing Virtual Network and Availability Set.
                  text: >
                    az vm create --image canonical:Ubuntu_Snappy_Core:15.04:2016.0318.1949
                    --admin-username myadmin --admin-password Admin_001 --authentication-type sshkey
                    --virtual-network-type existing --virtual-network-name myvnet --subnet-name default
                    --availability-set-type existing --availability-set-id myavailset
                    --public-ip-address-type new --dns-name-for-public-ip myGloballyUniqueVmDnsName
                    -l "West US" -g myvms --name myvm18o --ssh-key-value "<ssh-rsa-key>"
            """
        }

def _load_help_file(delimiters):
    if delimiters in helps:
        return yaml.load(helps[delimiters])
    else:
        return None

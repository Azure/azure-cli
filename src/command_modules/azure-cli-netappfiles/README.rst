Microsoft Azure CLI 'Azure NetApp Files (ANF)' Command Module
=============================================================

This package is for the Azure NetApp Files (ANF) module.
i.e. 'az netappfiles'


It contains commands that can be used to create and manage volumes. The typical sequence would be to first create an account

az netappfiles account create --resource-group rg -n account_name


Then allocate a storage pool in which volumes can be created

az netappfiles pool create --resource-group rg -a account_name -n pool_name -l location --size 4398046511104 --service-level "Premium"


Volumes are created within the pool resource

az netappfiles volume create --resource-group rg -a account_name -p pool_name -n volume_name -l location --service-level "Premium" --usage-threshold 107374182400 --creation-token "unique-token" --subnet-id "/subscriptions/mysubsid/resourceGroups/myrg/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/default"


Snapshots of volumes can also be created

az netappfiles snapshot create --resource-group rg -a account_name --p pool_name -v vname -n snapshot_name -l location --file-system-id volume-uuid


These resources can be updated, deleted and listed. See the help to find out more

az netappfiles --help

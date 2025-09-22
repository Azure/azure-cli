# Create a VM directly instead of using an ARM template
az vm create --resource-group myrg --name MyVM_01 --image UbuntuLTS --size Standard_D2s_v3 --admin-username azureuser --generate-ssh-keys

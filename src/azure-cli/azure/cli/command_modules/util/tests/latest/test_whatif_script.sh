az vm create --resource-group myrg --name MyVM_01 --image UbuntuLTS --size Standard_D2s_v3 --admin-username azureuser --generate-ssh-keys

az functionapp update --name myfunctionapp --resource-group myrg --set tags.Environment=Test
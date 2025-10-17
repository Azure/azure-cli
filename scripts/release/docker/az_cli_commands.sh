# Basic Information
echo "=== Basic Information ==="
az account show
az --version
az extension list

# Template Specs
echo "=== Template Specs ==="
az ts list

# Accounts and Subscriptions
echo "=== Accounts and Subscriptions ==="
az account list
az account subscription list

# Resource Groups
echo "=== Resource Groups ==="
az group list

# Virtual Machines
echo "=== Virtual Machines ==="
az vm list
az vm image list --output json
# az vm size list --location eastus
az vmss list
az disk list
az snapshot list
az image list
az sig list
az vm availability-set list

# Networking
echo "=== Networking ==="
az network vnet list
az network subnet list --vnet-name MyVNet --resource-group MyResourceGroup 2>/dev/null || echo 'Requires specific vnet and resource group'
az network nsg list
az network nic list
az network public-ip list
az network lb list
az network application-gateway list
az network dns zone list
az network vpn-gateway list
az network express-route list
az network route-table list
az network firewall list
az network private-endpoint list
az network private-link-service list
az network nat gateway list
az network traffic-manager profile list

# Storage
echo "=== Storage ==="
az storage account list

# Databases
echo "=== Databases ==="
az sql server list
az sql mi list
az mysql server list
az postgres server list
az postgres flexible-server list
az mysql flexible-server list
az mariadb server list
az cosmosdb list
az cosmosdb postgres cluster list --resource-group azure-cli-test-rg

# Containers
echo "=== Containers ==="
az aks list
az acr list
az container list
az containerapp list
az containerapp env list
az aro list

# App Services
echo "=== App Services ==="
az webapp list
az appservice plan list
az functionapp list

# App Configuration
echo "=== App Configuration ==="
az appconfig list

# Security and Identity
echo "=== Security and Identity ==="
az ad sp list --show-mine
az ad user list
az ad group list
az keyvault list
az policy assignment list
az policy definition list
az policy exemption list
az policy set-definition list
az role assignment list
az role definition list
az identity list
az security pricing list
az security contact list

# Managed Services
echo "=== Managed Services ==="
az managedservices assignment list
az managedservices definition list

# Monitoring
echo "=== Monitoring ==="
az monitor activity-log list --start-time 2025-09-01 --end-time 2025-09-10 2>/dev/null || echo 'Requires time range specification'
az monitor log-analytics workspace list

# Backup
echo "=== Backup ==="
az backup vault list

# Cognitive Services
echo "=== Cognitive Services ==="
az cognitiveservices account list

# IoT
echo "=== IoT ==="
az iot hub list
az iot dps list
az iot central app list

# Data Box Edge
echo "=== Data Box Edge ==="
az databoxedge device list

# Events
echo "=== Events ==="
az eventgrid topic list
az eventgrid domain list
az eventhubs namespace list

# Service Bus
echo "=== Service Bus ==="
az servicebus namespace list

# Relay
echo "=== Relay ==="
az relay namespace list

# Batch
echo "=== Batch ==="
az batch account list

# CDN and Front Door
echo "=== CDN and Front Door ==="
az cdn profile list
az afd profile list

# API Management
echo "=== API Management ==="
az apim list

# Logic Apps
echo "=== Logic Apps ==="
az logic workflow list

# Search
echo "=== Search ==="
az search service list --resource-group azure-cli-test-rg

# HDInsight and Analytics
echo "=== HDInsight and Analytics ==="
az hdinsight list
az synapse workspace list

# Signal R
echo "=== Signal R ==="
az signalr list

# Locations and Availability
echo "=== Locations and Availability ==="
az account list-locations
az provider list

# Resources
echo "=== Resources ==="
az resource list --output json

# Tags
echo "=== Tags ==="
az tag list

# NetApp Files
echo "=== NetApp Files ==="
az netappfiles account list

# # Compute Fleet
# echo "=== Compute Fleet ==="
# az compute-fleet list

# Budget and Cost
echo "=== Budget and Cost ==="
az consumption budget list 2>/dev/null || echo 'Budget command may require specific permissions'
az consumption usage list 2>/dev/null || echo 'Usage command may require specific permissions'
az billing account list
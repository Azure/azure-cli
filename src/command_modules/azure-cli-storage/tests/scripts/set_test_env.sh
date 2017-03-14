# Make sure you using this script in this form so that environment variables are properly added.
# $ source set_test_env.sh <storage account name> <resource group>

if [ -z $1 ] || [ -z $2 ]; then
    echo "Missing parameters"
    echo "Usage: source <script name> <storage account name> <resource group>"
else
    export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string -n $1 -g $2 --query 'connectionString' | tr -d '"')

    echo "existing blob containers ..."
    az storage container list -o table

    echo
    echo "existing file share ..."
    az storage share list -o table
fi

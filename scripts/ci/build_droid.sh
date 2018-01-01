# Build the docker image for A01 automation system

set -e

dp0=`cd $(dirname $0); pwd`

# Build the whl files first
. $dp0/build.sh

# Move dockerfile
cp $dp0/a01/Dockerfile.py36 artifacts/

image_name=azurecli-test:python3.6-$version
docker build -t $image_name -f artifacts/Dockerfile.py36 artifacts

if [ $A01_ACR ]; then
    az acr login -n $A01_ACR
    docker tag $image_name $A01_ACR.azurecr.io/$image_name
    docker push $A01_ACR.azurecr.io/$image_name
fi


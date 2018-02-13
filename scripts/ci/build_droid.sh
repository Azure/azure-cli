# Build the docker image for A01 automation system

set -e

dp0=`cd $(dirname $0); pwd`

#############################################
# Define colored output func
function title {
    LGREEN='\033[1;32m'
    CLEAR='\033[0m'

    echo -e ${LGREEN}$1${CLEAR}
}

#############################################
# Clean up artifacts
title 'Remove artifacts folder'
if [ -d artifacts ]; then rm -r artifacts; fi

#############################################
# Build the whl files first
$dp0/build.sh

#############################################
# Move dockerfile
cp $dp0/a01/Dockerfile.py36 artifacts/

#############################################
# Move other scripts for docker
cp -R $dp0/a01/* artifacts/

#############################################
# for travis repo slug, remove the suffix to reveal the owner
# - the offical repo will generate image: azurecli-test-Azure
# - the fork repo will generate image: azurecli-test-johnongithub
# for local private build uses local user name.
# - eg. azurecli-test-private-john
title 'Determine docker image name'
image_owner=${TRAVIS_REPO_SLUG%/azure-cli} 
image_owner=${image_owner:="private-${USER}"}
image_owner=`echo $image_owner | tr '[:upper:]' '[:lower:]'`
version=`cat artifacts/version`
image_name=azureclidev.azurecr.io/azurecli-test-$image_owner:python3.6-$version
echo 'Image name: $image_name'

title 'Login docker registry'
if [ $AZURECLIDEV_ACR_SP_USERNAME ] && [ $AZURECLIDEV_ACR_SP_PASSWORD ]; then
    docker login azureclidev.azurecr.io -u $AZURECLIDEV_ACR_SP_USERNAME -p $AZURECLIDEV_ACR_SP_PASSWORD
fi

title 'Build docker image'
docker build -t $image_name -f artifacts/Dockerfile.py36 artifacts

title 'Push docker image'
if [ "$1" == "push" ] || [ "$TRAVIS" == "true" ]; then
    docker push $image_name
else
    echo "Skip"
fi

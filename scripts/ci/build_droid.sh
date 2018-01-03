# Build the docker image for A01 automation system

set -e

dp0=`cd $(dirname $0); pwd`

# Clean up artifacts
if [ -d artifacts ]; then rm -r artifacts; fi

# Build the whl files first
. $dp0/build.sh

# Move dockerfile
cp $dp0/a01/Dockerfile.py36 artifacts/

# for travis repo slug, remove the suffix to reveal the owner
# - the offical repo will generate image: azurecli-test-Azure
# - the fork repo will generate image: azurecli-test-johnongithub
# for local private build uses local user name.
# - eg. azurecli-test-private-john
image_owner=${TRAVIS_REPO_SLUG%/azure-cli} 
image_owner=${image_owner:="private-${USER}"}

image_name=azurecli-test-$image_owner:python3.6-$version

docker build -t $image_name -f artifacts/Dockerfile.py36 artifacts

if [ $AZURE_CLI_BUILD_CR ]; then
    if [ -z $TRAVIS ]; then $dp0/login_cr.sh; fi
    docker tag $image_name $AZURE_CLI_BUILD_CR/$image_name
    docker push $AZURE_CLI_BUILD_CR/$image_name
fi


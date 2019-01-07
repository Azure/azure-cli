# Build wheel and set the $share_folder to the artifacts folder

if [[ $TRAVIS_REPO_SLUG == "Azure/azure-cli" ]]; then
    . $(cd $(dirname $0); pwd)/build.sh
else
    sh ./scripts/ci/build.sh
fi
share_folder=$(cd $(dirname $0); cd ../../artifacts; pwd)
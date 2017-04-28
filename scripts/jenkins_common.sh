# define the common functions for jenkins scripts

if [ -z $BUILD_NUMBER ]; then
    echo "Environment variable BUILD_NUMBER is missing."
    exit 1
fi

version=$(printf '%.8d' $BUILD_NUMBER)

if [ -z $BRANCH_NAME ]; then
    BRANCH_NAME='Infrastructure'
fi

build_share="/var/build_share/$BRANCH_NAME/$version"

echo "== Common build variables =="
echo "Version number: $version"
echo "Branch name: $BRANCH_NAME"
echo "Build share: $build_share"


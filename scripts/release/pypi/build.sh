#!/usr/bin/env bash

# This is the script builds the final wheel packages for shipping. The major difference between this script and the
# scripts/ci/build.sh is that this script doesn't build testsdk and test packages. It doesn't update version string,
# either. Therefore this script is shorter and cleaner.

set -ev

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set}"
: "${BUILD_SOURCESDIRECTORY:=`cd $(dirname $0); cd ../../../; pwd`}"

cd $BUILD_SOURCESDIRECTORY

branch=$1
echo "Branch $branch"

echo "Search pyproject.toml files from `pwd`."
python --version

# Provision the PEP 517 frontend and backend for --no-isolation builds,
# keeping setuptools at or above the security floor.
pip install -U pip "setuptools>=78.1.1" wheel build
pip list

script_dir=`cd $(dirname $BASH_SOURCE[0]); pwd`

if [[ ! $branch =~ ^release ]]; then
    . $script_dir/../../ci/version.sh post`date -u '+%Y%m%d%H%M%S'`
fi

python -c 'import tomllib' 2>/dev/null || python -m pip install --disable-pip-version-check -q 'tomli>=2.0.1'
python "$script_dir/../../ci/check_package_versions.py"

for pyproject_file in $(find src -name 'pyproject.toml' | grep -v azure-cli-testsdk); do
    pushd `dirname $pyproject_file`
    python -m build --wheel --no-isolation --outdir $BUILD_STAGINGDIRECTORY
    python -m build --sdist --no-isolation --outdir $BUILD_STAGINGDIRECTORY
    popd
done

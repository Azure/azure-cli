#/bin/bash

set -ev

CLI_VERSION=`cat $SYSTEM_ARTIFACTSDIRECTORY/metadata/version`

echo == Remove pre-installed azure-cli ==
brew uninstall azure-cli

echo == Install azure-cli.rb formula ==
# TODO(packaging): remove once the macOS CI agent image's Homebrew provides formula_opt_prefix.
# The upstream homebrew-core formula calls `formula_opt_prefix("openssl@3")`, a newer
# Homebrew DSL helper not available on the older Homebrew on the macOS CI agent image
# (NoMethodError). Rewrite it to the backward-compatible `Formula["openssl@3"].opt_prefix`
# form for the local test install only; the generated/submitted formula stays upstream-faithful.
sed -E -i '' 's/formula_opt_prefix\(?[[:space:]]*"([^"]+)"[[:space:]]*\)?/Formula["\1"].opt_prefix/g' $SYSTEM_ARTIFACTSDIRECTORY/homebrew/azure-cli.rb
brew install --build-from-source $SYSTEM_ARTIFACTSDIRECTORY/homebrew/azure-cli.rb

AZ_BASE=/usr/local/Cellar/azure-cli/$CLI_VERSION/libexec
export PATH=$AZ_BASE/bin:$PATH
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
echo $PATH
pip install wheel
./scripts/ci/build.sh
pip install pytest --prefix $AZ_BASE
pip install pytest-xdist --prefix $AZ_BASE
pip install pytest-forked --prefix $AZ_BASE

find ./artifacts/build -name "azure_cli_testsdk*" | xargs pip install --prefix $AZ_BASE --upgrade --ignore-installed
find ./artifacts/build -name "azure_cli_fulltest*" | xargs pip install --prefix $AZ_BASE --upgrade --ignore-installed --no-deps

# workaround for this bug (https://github.com/microsoft/azure-devops-python-api/issues/354)
mkdir -p ~/.vsts/python-sdk/cache

PYTHON_VERSION=`ls $AZ_BASE/lib/ | head -n 1`
python ./scripts/release/homebrew/test_homebrew_package.py $AZ_BASE $PYTHON_VERSION
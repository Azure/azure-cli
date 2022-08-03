#!/usr/bin/env bash

# Build wheel packages containing both CLI product and tests. The script doesn't rely on a pre-existing virtual
# environment.

set -ev

##############################################
# clean up and dir search
mkdir -p ./artifacts

# Current folder (/azure-cli) is mounted from host which has different owner than docker container's
# current user 0(root).
# https://github.blog/2022-04-12-git-security-vulnerability-announced/
git config --global --add safe.directory $(pwd)
echo `git rev-parse --verify HEAD` > ./artifacts/build.sha

mkdir -p ./artifacts/build
mkdir -p ./artifacts/source
mkdir -p ./artifacts/testsrc

output_dir=$(cd artifacts/build && pwd)
sdist_dir=$(cd artifacts/source && pwd)
testsrc_dir=$(cd artifacts/testsrc && pwd)
script_dir=`cd $(dirname $BASH_SOURCE[0]); pwd`

target_profile=${AZURE_CLI_TEST_TARGET_PROFILE:-latest}
if [ "$target_profile" != "latest" ]; then
    # example: hybrid-2019-03-01. Python module name can't begin with a digit.
    target_profile=hybrid_${target_profile//-/_}
fi
echo Pick up profile: $target_profile

##############################################
# Define colored output func
function title {
    LGREEN='\033[1;32m'
    CLEAR='\033[0m'

    echo -e ${LGREEN}$1${CLEAR}
}

##############################################
# Update version strings
title 'Determine version'
. $script_dir/version.sh $1
# echo -n $version > ./artifacts/version

##############################################
# build product packages
title 'Build Azure CLI and its command modules'
for setup_file in $(find src -name 'setup.py'); do
    pushd $(dirname ${setup_file}) >/dev/null
    echo "Building module at $(pwd) ..."
    python setup.py -q bdist_wheel -d $output_dir
    python setup.py -q sdist -d $sdist_dir
    popd >/dev/null
done

##############################################
# copy private packages
if [ -z ./privates ]; then
    cp ./privates/*.whl $output_dir
fi

##############################################
# build test packages
title 'Build Azure CLI tests package'

for test_src in $(find src/azure-cli/azure/cli/command_modules -name tests -type d); do
    rel_path=${test_src##src/azure-cli/}

    mkdir -p $testsrc_dir/$rel_path
    cp -R $test_src/* $testsrc_dir/$rel_path
done

if [ "$target_profile" == "latest" ]; then
    # don't pack core tests for profiles other than latest
    for test_src in $(find src -name tests | grep -v command_modules); do
        rel_path=${test_src##src/}
        rel_path=(${rel_path/\// })
        rel_path=${rel_path[1]}

        mkdir -p $testsrc_dir/$rel_path
        cp -R $test_src/* $testsrc_dir/$rel_path
    done
fi

cat >$testsrc_dir/setup.py <<EOL
#!/usr/bin/env python

from setuptools import setup

VERSION = "1.0.0.$version"

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'azure-cli',
    'azure-cli-testsdk'
]

setup(
    name='azure-cli-fulltest',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools Full Tests',
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    packages=[
EOL

if [ "$target_profile" == "latest" ]; then
    echo "        'azure.cli.core.tests'," >>$testsrc_dir/setup.py
fi

for name in `ls src/azure-cli/azure/cli/command_modules`; do
    test_folder=src/azure-cli/azure/cli/command_modules/$name/tests
    if [ -d $test_folder ]; then
        echo "        'azure.cli.command_modules.$name.tests'," >>$testsrc_dir/setup.py
        if [ -d $test_folder/$target_profile ]; then
            echo "        'azure.cli.command_modules.$name.tests.$target_profile'," >>$testsrc_dir/setup.py
        fi
    fi
done


cat >>$testsrc_dir/setup.py <<EOL
    ],
    package_data={'': ['*.bat',
                       '*.byok',
                       '*.cer',
                       '*.gql',  # graphql used by apim
                       '*.js',
                       '*.json',
                       '*.kql',
                       '*.md',
                       '*.pem',
                       '*.pfx',
                       '*.sql',
                       '*.txt',
                       '*.txt',
                       '*.xml',
                       '*.yml',
                       '*.zip',
                       '**/*.bat',
                       '**/*.byok',
                       '**/*.cer',
                       '**/*.gql',
                       '**/*.ipynb',
                       '**/*.jar',
                       '**/*.js',
                       '**/*.json',
                       '**/*.kql',
                       '**/*.md',
                       '**/*.pem',
                       '**/*.pfx',
                       '**/*.sql',
                       '**/*.txt',
                       '**/*.txt',
                       '**/*.xml',
                       'data/*',
                       'recordings/*.yaml']},
    install_requires=DEPENDENCIES
)
EOL

cat >>$testsrc_dir/setup.cfg <<EOL
[bdist_wheel]
universal=1
EOL

cat >>$testsrc_dir/README.txt <<EOL
Azure CLI Test Cases
EOL

pushd $testsrc_dir >/dev/null
python setup.py -q bdist_wheel -d $output_dir
python setup.py -q sdist -d $sdist_dir
popd >/dev/null

##############################################
# clear afterwards
rm -rf $testsrc_dir
git checkout src

##############################################
# summary
title 'Results'
echo $(ls $sdist_dir | wc -l) packages created.

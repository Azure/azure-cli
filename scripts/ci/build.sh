#!/usr/bin/env bash

# Build wheel packages containing both CLI product and tests. The script doesn't rely on a pre-existing virtual
# environment.

set -e

##############################################
# clean up
mkdir -p ./artifacts
echo `git rev-parse --verify HEAD` > ./artifacts/build.sha

mkdir -p ./artifacts/build
mkdir -p ./artifacts/source
mkdir -p ./artifacts/app
mkdir -p ./artifacts/testsrc

output_dir=$(cd artifacts/build && pwd)
sdist_dir=$(cd artifacts/source && pwd)
testsrc_dir=$(cd artifacts/testsrc && pwd)
app_dir=$(cd artifacts/app && pwd)

##############################################
# Copy app scripts for batch run - To be retired in the future
cp $(cd $(dirname $0); pwd)/app/* $app_dir

##############################################
# Update version strings
if $TRAVIS; then
    $(cd $(dirname $0); pwd)/version.sh $1
fi

##############################################
# build product packages
echo 'Build Azure CLI and its command modules'
for setup_file in $(find src -name 'setup.py'); do
    pushd $(dirname $setup_file)
    echo ""
    echo "Building module at $(pwd) ..."
    python setup.py -q bdist_wheel -d $output_dir
    python setup.py -q sdist -d $sdist_dir
    popd
done

##############################################
# build test packages
echo 'Build Azure CLI tests package'

echo "Copy test source code into $build_src ..."
for test_src in $(find src/command_modules -name tests -type d); do
    rel_path=${test_src##src/command_modules/}
    rel_path=(${rel_path/\// })
    rel_path=${rel_path[1]}

    mkdir -p $testsrc_dir/$rel_path
    cp -R $test_src/* $testsrc_dir/$rel_path
done

for test_src in $(find src -name tests | grep -v command_modules); do
    rel_path=${test_src##src/}
    rel_path=(${rel_path/\// })
    rel_path=${rel_path[1]}

    mkdir -p $testsrc_dir/$rel_path
    cp -R $test_src/* $testsrc_dir/$rel_path
done

cat >$testsrc_dir/setup.py <<EOL
#!/usr/bin/env python

from setuptools import setup

VERSION = "1.0.0.dev$TRAVIS_BUILD_NUMBER"

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
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
        'azure.cli.core.tests',
EOL

for name in $(ls src/command_modules | grep azure-cli-); do
    if [ "$name" == "azure-cli-acr" ]; then continue; fi
    if [ "$name" == "azure-cli-acs" ]; then continue; fi
    if [ "$name" == "azure-cli-advisor" ]; then continue; fi
    if [ "$name" == "azure-cli-appservice" ]; then continue; fi
    if [ "$name" == "azure-cli-backup" ]; then continue; fi
    if [ "$name" == "azure-cli-batch" ]; then continue; fi
    if [ "$name" == "azure-cli-batchai" ]; then continue; fi
    # if [ "$name" == "azure-cli-billing" ]; then continue; fi
    # if [ "$name" == "azure-cli-cdn" ]; then continue; fi
    # if [ "$name" == "azure-cli-cloud" ]; then continue; fi
    if [ "$name" == "azure-cli-cognitiveservices" ]; then continue; fi
    # if [ "$name" == "azure-cli-configure" ]; then continue; fi
    if [ "$name" == "azure-cli-consumption" ]; then continue; fi
    if [ "$name" == "azure-cli-container" ]; then continue; fi
    if [ "$name" == "azure-cli-cosmosdb" ]; then continue; fi
    if [ "$name" == "azure-cli-dla" ]; then continue; fi
    if [ "$name" == "azure-cli-dls" ]; then continue; fi
    if [ "$name" == "azure-cli-eventgrid" ]; then continue; fi
    # if [ "$name" == "azure-cli-extension" ]; then continue; fi
    # if [ "$name" == "azure-cli-feedback" ]; then continue; fi
    # if [ "$name" == "azure-cli-find" ]; then continue; fi
    # if [ "$name" == "azure-cli-interactive" ]; then continue; fi
    if [ "$name" == "azure-cli-iot" ]; then continue; fi
    if [ "$name" == "azure-cli-keyvault" ]; then continue; fi
    if [ "$name" == "azure-cli-lab" ]; then continue; fi
    if [ "$name" == "azure-cli-monitor" ]; then continue; fi
    # if [ "$name" == "azure-cli-network" ]; then continue; fi
    if [ "$name" == "azure-cli-profile" ]; then continue; fi
    if [ "$name" == "azure-cli-rdbms" ]; then continue; fi
    # if [ "$name" == "azure-cli-redis" ]; then continue; fi
    if [ "$name" == "azure-cli-reservations" ]; then continue; fi
    # if [ "$name" == "azure-cli-resource" ]; then continue; fi
    # if [ "$name" == "azure-cli-role" ]; then continue; fi
    if [ "$name" == "azure-cli-servicefabric" ]; then continue; fi
    if [ "$name" == "azure-cli-sql" ]; then continue; fi
    if [ "$name" == "azure-cli-storage" ]; then continue; fi
    if [ "$name" == "azure-cli-vm" ] ; then continue; fi
    module_name=${name##azure-cli-}
    if [ -d src/command_modules/$name/azure/cli/command_modules/$module_name/tests ]; then
        echo "        'azure.cli.command_modules.$module_name.tests'," >>$testsrc_dir/setup.py
    fi
done


cat >>$testsrc_dir/setup.py <<EOL
    ],
    package_data={'': ['recordings/**/*.yaml', 
                       'data/*.zip',
                       'data/*.whl',
                       '*.pem', 
                       '*.pfx',
                       '*.txt',
                       '*.json',
                       '*.byok',
                       '*.js',
                       '*.md',
                       '*.bat',
                       '*.txt',
                       '*.cer', 
                       '**/*.cer',
                       '**/*.pem', 
                       '**/*.pfx',
                       '**/*.txt',
                       '**/*.json',
                       '**/*.byok',
                       '**/*.js',
                       '**/*.md',
                       '**/*.bat',
                       '**/*.txt']},
    install_requires=DEPENDENCIES
)
EOL

pushd $testsrc_dir
python setup.py -q bdist_wheel -d $output_dir 
python setup.py -q sdist -d $sdist_dir
popd

##############################################
# clear afterwards
rm -rf $testsrc_dir  
git checkout src

##############################################
# summary 
echo 'Build result:'
ls -R ./artifacts

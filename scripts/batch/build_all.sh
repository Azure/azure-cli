#!/usr/bin/env bash

# build a wheel package containing all the CLI tests

pip install --user virtualenv
python -m virtualenv env
. env/bin/activate

python ./scripts/dev_setup.py


# clean up
rm -rf ./artifacts

mkdir -p ./artifacts/build
mkdir -p ./artifacts/app
mkdir -p ./artifacts/testsrc

output_dir=$(cd artifacts/build && pwd)
testsrc_dir=$(cd artifacts/testsrc && pwd)
app_dir=$(cd artifacts/app && pwd)

##############################################
# Copy app scripts for batch run

cp $(cd $(dirname $0); pwd)/app/* $app_dir


##############################################
# List tests to the test file

content=`nosetests azure.cli -v --collect-only 2>&1`

echo $content > $app_dir/raw.txt
manifest="$app_dir/all_tests.txt"
if [ -e $manifest ]; then rm $manifest; fi

while IFS='' read -r line || [[ -n "$line" ]]; do
    if [ -n "$line" ] && [ "OK" != "$line" ] && [ "${line:0:3}" != "Ran" ] && [ "${line:0:3}" != "---" ]; then
        parts=($line)
        test_method=${parts[0]}
        test_class=${parts[1]}
        test_class=${test_class##(}
        test_class=${test_class%%)}

        echo "$test_class $test_method" >> $manifest
    fi
done <<< "$content"


##############################################
# build product packages

echo 'Build Azure CLI and its command modules'
for setup_file in $(find src -name 'setup.py'); do
    pushd $(dirname $setup_file)
    echo ""
    echo "Building module at $(pwd) ..."
    python setup.py bdist_wheel -d $output_dir sdist -d $output_dir
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

VERSION = "1.0.0"

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
    module_name=${name##azure-cli-}
    echo "src/command_modules/azure-cli-$name/azure/cli/command_modules/$name/tests"
    if [ -d src/command_modules/$name/azure/cli/command_modules/$module_name/tests ]; then
        echo "        'azure.cli.command_modules.$module_name.tests'," >>$testsrc_dir/setup.py
    fi
done


cat >>$testsrc_dir/setup.py <<EOL
    ],
    package_data={'': ['recordings/**/*.yaml', 
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
python setup.py bdist_wheel -d $output_dir sdist -d $output_dir
popd

rm -rf $testsrc_dir  # clear afterwards

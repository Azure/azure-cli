#!/usr/bin/env bash

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

[ -d privates ] && pip install privates/*.whl
pip install pylint
pip install $ALL_MODULES

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'

proc_number=`python -c 'import multiprocessing; print(multiprocessing.cpu_count())'`

echo "Run pylint with $proc_number proc."

# Uncommented after all conversion is done
# pylint azure.cli --rcfile=./pylintrc -j $proc_number

proc_number=`python -c 'import multiprocessing; print(multiprocessing.cpu_count())'`
exit_code=0

run_style() {
    pylint $1 --rcfile=./pylintrc -j $proc_number
    let exit_code=$exit_code+$?
}


set +e

run_style azure.cli.core
run_style azure.cli.command_modules.acr
run_style azure.cli.command_modules.acs
#run_style azure.cli.command_modules.advisor
#run_style azure.cli.command_modules.appservice
#run_style azure.cli.command_modules.backup
run_style azure.cli.command_modules.batch
#run_style azure.cli.command_modules.batchai
run_style azure.cli.command_modules.billing
run_style azure.cli.command_modules.cdn
run_style azure.cli.command_modules.cloud
run_style azure.cli.command_modules.cognitiveservices
run_style azure.cli.command_modules.configure
#run_style azure.cli.command_modules.consumption
run_style azure.cli.command_modules.container
#run_style azure.cli.command_modules.cosmosdb
#run_style azure.cli.command_modules.dla
#run_style azure.cli.command_modules.dls
run_style azure.cli.command_modules.eventgrid
run_style azure.cli.command_modules.extension
run_style azure.cli.command_modules.feedback
run_style azure.cli.command_modules.find
run_style azure.cli.command_modules.interactive
#run_style azure.cli.command_modules.iot
run_style azure.cli.command_modules.keyvault
#run_style azure.cli.command_modules.lab
#run_style azure.cli.command_modules.monitor
run_style azure.cli.command_modules.network
#run_style azure.cli.command_modules.nspkg
#run_style azure.cli.command_modules.profile
#run_style azure.cli.command_modules.rdbms
run_style azure.cli.command_modules.redis
run_style azure.cli.command_modules.reservations
run_style azure.cli.command_modules.resource
run_style azure.cli.command_modules.role
run_style azure.cli.command_modules.servicefabric
#run_style azure.cli.command_modules.sql
#run_style azure.cli.command_modules.storage
#run_style azure.cli.command_modules.testsdk
#run_style azure.cli.command_modules.vm

exit $exit_code

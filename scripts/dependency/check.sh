#!/bin/bash

set -ev

cd `cd $(dirname $0); cd ../..; pwd`

git status >/dev/null 2>&1 || (echo "This command is expected to run in a git environment." >&2; exit 1)

VENV_DIR=`mktemp -d /tmp/azurecli.dep.check.XXXXXX`
echo "Created temporary folder $VENV_DIR" >&2

REQU_NAME="`dirname $0`/requirements.`uname`.external.txt"
echo "Baseline requirements file $REQU_NAME"

python3 -m venv $VENV_DIR

. $VENV_DIR/bin/activate
pip install -U pip

echo "Virtual environemtn established at $VENV_DIR." >&2
echo "   Python path `which python3`" >&2
echo "   `python3 --version`" >&2

echo "Install Telemetry" >&2
pip install -e src/azure-cli-telemetry -q --log pip.log

echo "Install CORE" >&2
pip install -e src/azure-cli-core -q --log pip.log

echo "Install Namespace Package" >&2
pip install -e src/azure-cli-nspkg -q --log pip.log

for setups in `find src/command_modules -name setup.py | sort`; do
    dir_path=`dirname $setups`
    echo "Install $dir_path" >&2
    pip install -e $dir_path -q --log pip.log
done

echo "Install CLI Main Package" >&2
pip install -e src/azure-cli -q --log pip.log

pip check

pip freeze | sed '/-e/d' > $REQU_NAME


if ! git diff --exit-code $REQU_NAME; then

    cat << EOM >&2


The check failed because a change to the external dependencies has been detected. You can find the
exact difference in the git-diff command output (which is above this message.)

The failure is caused by:

1) Your commit alters one or multiple 'setup.py'; or

2) One or multiple dependencies have released newer version.

To resolve the failures:

1) To confirm that the change to the external dependency is expected, edit the $REQU_NAME file
    to reflect the change. The file can be also edited automatically by run script $0.

2) To avoid the change to the external dependency, edit the impacted setup.py to cap the external
    dependencies.

EOM

    echo $ERROR_MESSAGE
fi

rm -rf $VENV_DIR
exit 0

#!/usr/bin/env bash

# This script should be run in a centos7 docker.
set -exv

export USERNAME=azureuser

if [ `rpm --eval "%{dist}"` == '.el7' ] ; then
    centos7=true
else
    centos7=false
fi

if [ $centos7 == true ] ; then
    yum install -y dnf
    dnf install -y centos-release-scl
fi

dnf --nogpgcheck install /mnt/rpm/$RPM_NAME -y

dnf install git gcc $PYTHON_PACKAGE-devel findutils -y

if [ $centos7 == true ] ; then
    ln -s -f $PYTHON_CMD /usr/bin/python
    ln -s -f $PIP_CMD /usr/bin/pip
else
    ln -s -f /usr/bin/$PYTHON_CMD /usr/bin/python
    ln -s -f /usr/bin/$PIP_CMD /usr/bin/pip
fi
time az self-test
time az --version

cd /azure-cli/
pip install wheel
./scripts/ci/build.sh

# From Fedora36, when using `pip install --prefix` with root privileges, the package is installed into `{prefix}/local/lib`.
# In order to keep the original installation path, I have to set RPM_BUILD_ROOT
# Ref https://docs.fedoraproject.org/en-US/fedora/latest/release-notes/developers/Development_Python/#_pipsetup_py_installation_with_prefix
export RPM_BUILD_ROOT=/

pip install pytest --prefix /usr/lib64/az
pip install pytest-xdist --prefix /usr/lib64/az
pip install pytest-forked --prefix /usr/lib64/az

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs pip install --prefix /usr/lib64/az --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs pip install --prefix /usr/lib64/az --upgrade --ignore-installed --no-deps

python /azure-cli/scripts/release/rpm/test_rpm_package.py

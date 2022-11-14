# Red Hat Universal Base Image 8: https://catalog.redhat.com/software/containers/ubi8/ubi/5c359854d70cc534b3a3784e
# Red Hat Universal Base Image 9: https://catalog.redhat.com/software/containers/ubi9/ubi/615bcf606feffc5384e8452e

ARG image=registry.access.redhat.com/ubi8/ubi:8.4

FROM ${image} AS build-env
ARG cli_version=dev
ARG python_package=python39
ARG python_cmd=python3.9

RUN yum update -y
RUN yum install -y wget rpm-build gcc libffi-devel ${python_package}-devel openssl-devel make bash diffutils patch dos2unix perl

# dos2unix is not avaialble in ubi7
RUN if [ "${image}" == "registry.access.redhat.com/ubi7/ubi:7.9" ]; then wget "http://mirror.centos.org/centos/7/os/x86_64/Packages/dos2unix-6.0.3-7.el7.x86_64.rpm" && rpm -i dos2unix-6.0.3-7.el7.x86_64.rpm ; fi

WORKDIR /azure-cli

COPY . .

# RHEL 8's 'python3' is Python 3.6. RHEL 9's 'python3' is Python 3.9.
# We have to explicitly specify 'python39' to install Python 3.9.
RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=$python_package PYTHON_CMD=$python_cmd \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/x86_64/azure-cli-${cli_version}-1.*.x86_64.rpm /azure-cli-dev.rpm

FROM ${image} AS execution-env

RUN yum update -y
RUN yum install -y python39

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

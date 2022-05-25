ARG tag=2.0
ARG image=mcr.microsoft.com/cbl-mariner/base/core

FROM ${image}:${tag} AS build-env
ARG cli_version=dev

RUN tdnf update -y
RUN tdnf install -y binutils file rpm-build gcc libffi-devel python3-devel openssl-devel make diffutils patch dos2unix python3-virtualenv perl

WORKDIR /azure-cli

COPY . .

# Mariner only has 'python3' package. It has no version-specific packages, like 'python39'.
# - On Mariner 1.0, 'python3' is Python 3.7
# - On Mariner 2.0, 'python3' is Python 3.9
RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=python3 PYTHON_CMD=python3 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /usr/src/mariner/RPMS/x86_64/azure-cli-${cli_version}-1.x86_64.rpm /azure-cli-dev.rpm

FROM ${image}:${tag} AS execution-env

RUN tdnf update -y
RUN tdnf install -y python3 python3-virtualenv rpm

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

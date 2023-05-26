ARG image=fedora:35

FROM ${image} AS build-env
ARG cli_version=dev
ARG python_package=python3

RUN dnf update -y
RUN dnf install -y wget rpm-build gcc libffi-devel ${python_package}-devel openssl-devel make bash coreutils diffutils patch dos2unix perl

WORKDIR /azure-cli

COPY . .

RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=$python_package PYTHON_CMD=python3 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/*/azure-cli-${cli_version}-1.*.rpm /azure-cli-dev.rpm && \
    mkdir /out && cp /root/rpmbuild/RPMS/*/azure-cli-${cli_version}-1.*.rpm /out/

FROM ${image} AS execution-env

COPY --from=build-env /azure-cli-dev.rpm ./
RUN dnf install -y ./azure-cli-dev.rpm && \
    az --version

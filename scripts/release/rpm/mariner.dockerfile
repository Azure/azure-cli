ARG image=mcr.microsoft.com/cbl-mariner/base/core:2.0

FROM ${image} AS build-env
ARG cli_version=dev

RUN tdnf update -y

# kernel-headers, glibc-devel, binutils are needed to install psutil python package on ARM64
# ca-certificates: Mariner by default only adds a very minimal set of root certs to trust certain Microsoft
# resources (primarily packages.microsoft.com). ca-certificates contains the official Microsoft curated set of
# trusted root certificates. It has replaced the set of Mozilla Trusted Root Certificates.
RUN tdnf install -y binutils file rpm-build gcc libffi-devel python3-devel openssl-devel make diffutils patch \
    dos2unix perl sed kernel-headers glibc-devel binutils ca-certificates

WORKDIR /azure-cli

COPY . .

# Mariner 2.0 only has 'python3' package, which is currently (2022-12-09) Python 3.9.
# It has no version-specific packages like 'python39'.
RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=python3 PYTHON_CMD=python3 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /usr/src/*/RPMS/*/azure-cli-${cli_version}-1.*.rpm /azure-cli-dev.rpm && \
    mkdir /out && cp /usr/src/*/RPMS/*/azure-cli-${cli_version}-1.*.rpm /out/

FROM ${image} AS execution-env

RUN tdnf update -y

COPY --from=build-env /azure-cli-dev.rpm ./
RUN tdnf install -y ./azure-cli-dev.rpm && \
    az --version

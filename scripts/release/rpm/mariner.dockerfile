ARG tag=2.0
ARG acr=cblmariner2preview

FROM ${acr}.azurecr.io/base/core:${tag} AS build-env
ARG cli_version=dev

RUN tdnf update -y
RUN tdnf install -y binutils file rpm-build gcc libffi-devel python3-devel openssl-devel make diffutils patch dos2unix python3-virtualenv perl

WORKDIR /azure-cli

COPY . .

RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /usr/src/mariner/RPMS/x86_64/azure-cli-${cli_version}-1.x86_64.rpm /azure-cli-dev.rpm

FROM ${acr}.azurecr.io/base/core:${tag} AS execution-env

RUN tdnf update -y
RUN tdnf install -y python3 python3-virtualenv

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

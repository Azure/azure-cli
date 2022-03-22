ARG tag=35

FROM fedora:${tag} AS build-env
ARG cli_version=dev

RUN dnf update -y
RUN dnf install -y wget rpm-build gcc libffi-devel python3-devel python3-virtualenv openssl-devel make bash coreutils diffutils patch dos2unix perl

WORKDIR /azure-cli

COPY . .

RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/x86_64/azure-cli-${cli_version}-1.*.x86_64.rpm /azure-cli-dev.rpm

FROM fedora:${tag} AS execution-env

RUN dnf install -y python3 python3-virtualenv

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

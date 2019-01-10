ARG base_image=centos:centos7

FROM $base_image AS build-env
ARG cli_version=dev

RUN yum install -y wget rpm-build gcc libffi-devel python-devel openssl-devel make bash coreutils diffutils patch dos2unix

WORKDIR /azure-cli

COPY . .

RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/x86_64/azure-cli-${cli_version}-1.el7.x86_64.rpm /azure-cli-dev.rpm

FROM $base_image AS execution-env

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

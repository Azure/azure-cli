ARG tag=centos7

FROM centos:${tag} AS build-env
ARG cli_version=dev

RUN yum update -y
RUN yum install -y wget rpm-build gcc libffi-devel python3-devel openssl-devel make bash coreutils diffutils patch dos2unix python3-virtualenv

WORKDIR /azure-cli

COPY . .

# CentOS 7 only has 'python3' package, which is Python 3.6.
RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=python3 PYTHON_CMD=python3 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/x86_64/azure-cli-${cli_version}-1.*.x86_64.rpm /azure-cli-dev.rpm

FROM centos:${tag} AS execution-env

RUN yum update -y
RUN yum install -y python3 python3-virtualenv

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

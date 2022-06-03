# Red Hat Universal Base Image 8: https://catalog.redhat.com/software/containers/ubi8/ubi/5c359854d70cc534b3a3784e

ARG tag=8.4

FROM registry.access.redhat.com/ubi8/ubi:${tag} AS build-env
ARG cli_version=dev

RUN yum update -y
RUN yum install -y wget rpm-build gcc libffi-devel python39-devel openssl-devel make bash diffutils patch dos2unix perl

WORKDIR /azure-cli

COPY . .

# RHEL's 'python3' is Python 3.6. We have to explicitly specify 'python39' to install Python 3.9.
RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=python39 PYTHON_CMD=python3.9 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/x86_64/azure-cli-${cli_version}-1.*.x86_64.rpm /azure-cli-dev.rpm

FROM registry.access.redhat.com/ubi8/ubi:${tag} AS execution-env

RUN yum update -y
RUN yum install -y python39

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

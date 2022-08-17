# Red Hat Universal Base Image 9: https://catalog.redhat.com/software/containers/ubi9/ubi/615bcf606feffc5384e8452e

ARG tag=9.0.0-1604

FROM registry.access.redhat.com/ubi9/ubi:${tag} AS build-env
ARG cli_version=dev

RUN yum update -y
RUN yum install -y wget rpm-build gcc libffi-devel python3-devel openssl-devel make bash diffutils patch dos2unix perl

WORKDIR /azure-cli

COPY . .

# RHEL 9's 'python3' is Python 3.9.
# https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html-single/9.0_release_notes/index#enhancement_dynamic-programming-languages-web-and-database-servers
RUN dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=python3 PYTHON_CMD=python3 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/x86_64/azure-cli-${cli_version}-1.*.x86_64.rpm /azure-cli-dev.rpm

FROM registry.access.redhat.com/ubi9/ubi:${tag} AS execution-env

COPY --from=build-env /azure-cli-dev.rpm ./
RUN rpm -i ./azure-cli-dev.rpm && \
    az --version

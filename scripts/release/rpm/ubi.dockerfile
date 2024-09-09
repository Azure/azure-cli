# Red Hat Universal Base Image 8: https://catalog.redhat.com/software/containers/ubi8/ubi/5c359854d70cc534b3a3784e
# Red Hat Universal Base Image 9: https://catalog.redhat.com/software/containers/ubi9/ubi/615bcf606feffc5384e8452e

ARG image=registry.access.redhat.com/ubi8/ubi:8.4

FROM ${image} AS build-env
ARG cli_version=dev
ARG python_package=python39

RUN yum update -y
RUN yum install -y wget rpm-build gcc libffi-devel ${python_package}-devel openssl-devel make bash diffutils patch dos2unix perl

WORKDIR /azure-cli

COPY . .

# RHEL 8's 'python3' is Python 3.6. RHEL 9's 'python3' is Python 3.9.
# We have to explicitly specify 'python39' to install Python 3.9.
RUN --mount=type=secret,id=PIP_INDEX_URL export PIP_INDEX_URL=$(cat /run/secrets/PIP_INDEX_URL) && \
    dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=$python_package PYTHON_CMD=python3.9 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    cp /root/rpmbuild/RPMS/*/azure-cli-${cli_version}-1.*.rpm /azure-cli-dev.rpm && \
    mkdir /out && cp /root/rpmbuild/RPMS/*/azure-cli-${cli_version}-1.*.rpm /out/

FROM ${image} AS execution-env

RUN yum update -y

COPY --from=build-env /azure-cli-dev.rpm ./
RUN yum install -y ./azure-cli-dev.rpm && \
    az --version

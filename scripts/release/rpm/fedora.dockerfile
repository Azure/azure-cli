ARG image=fedora:35

FROM ${image} AS build-env
ARG cli_version=dev
ARG python_package=python3

# Install build dependencies in a single dnf transaction so the resolver
# picks a mutually consistent set of packages. A separate `dnf update -y`
# step is intentionally avoided: if the configured repositories are
# temporarily out of sync (e.g. a newer glibc-devel is published before
# the matching glibc, or vice versa), updating first can pin a package
# to a version whose tightly-coupled companion is not yet available,
# breaking the subsequent install. The base image already ships with
# updates, and any newer transitive dependencies will be pulled in here.
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

ARG base_image=ubuntu:xenial
FROM ${base_image} AS build-env

# Update APT packages
RUN apt-get update
RUN apt-get install -y libssl-dev libffi-dev python3-dev python3-venv debhelper zlib1g-dev wget

COPY . .

ARG cli_version=0.0.0-dev
ARG cli_version_revision=1

RUN mkdir -p ./debian && \
    CLI_VERSION=${cli_version} CLI_VERSION_REVISION=${cli_version_revision} ./scripts/release/debian/prepare.sh ./debian ./az.completion ./ && \
    dpkg-buildpackage -us -uc && \
    cp /azure-cli_${cli_version}-${cli_version_revision}_all.deb /azure-cli_all.deb

FROM $base_image AS execution-env

COPY --from=build-env /azure-cli_all.deb /azure-cli_all.deb

RUN dpkg -i /azure-cli_all.deb && \
    rm /azure-cli_all.deb
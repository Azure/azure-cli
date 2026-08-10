# Default is Azure Linux 4.0 (Beta), but this dockerfile is shared with Azure Linux 3.0
# builds too -- the CI pipeline always overrides this with --build-arg image=<AZL3 or AZL4>.
ARG image=mcr.microsoft.com/azurelinux-beta/base/core:4.0

FROM ${image} AS build-env
ARG cli_version=dev

RUN tdnf update -y

# kernel-headers, glibc-devel, binutils are needed to install psutil python package on ARM64
# ca-certificates: Azure Linux by default only adds a very minimal set of root certs to trust certain Microsoft
# resources (primarily packages.microsoft.com). ca-certificates contains the official Microsoft curated set of
# trusted root certificates. It has replaced the set of Mozilla Trusted Root Certificates.
RUN tdnf install -y binutils file rpm-build gcc libffi-devel python3-devel openssl-devel make diffutils patch \
    dos2unix perl sed kernel-headers glibc-devel binutils ca-certificates

WORKDIR /azure-cli

COPY . .

# This dockerfile is shared by both Azure Linux 3.0 and Azure Linux 4.0 (Beta) builds
# (the ${image} build-arg selects which base image is used). The two base images use
# different rpmbuild topdir defaults, so the built RPM ends up in different locations:
#   AZL3: /usr/src/azl/RPMS/x86_64/azure-cli-2.63.0-1.azl3.x86_64.rpm
#   AZL4: /root/rpmbuild/RPMS/x86_64/azure-cli-2.63.0-1.azl4.x86_64.rpm
# Use `find` so the same RUN step works for either base image without needing to know
# which topdir it used.
RUN --mount=type=secret,id=PIP_INDEX_URL export PIP_INDEX_URL=$(cat /run/secrets/PIP_INDEX_URL) && \
    dos2unix ./scripts/release/rpm/azure-cli.spec && \
    REPO_PATH=$(pwd) CLI_VERSION=$cli_version PYTHON_PACKAGE=python3 PYTHON_CMD=python3 \
    rpmbuild -v -bb --clean scripts/release/rpm/azure-cli.spec && \
    RPM_PATH=$(find /usr/src/azl/RPMS /root/rpmbuild/RPMS -type f -name "azure-cli-${cli_version}-1.*.rpm" 2>/dev/null | head -n 1) || RPM_PATH="" && \
    if [ -z "$RPM_PATH" ]; then echo "ERROR: No RPM found in expected directories. Contents:"; ls -la /usr/src/azl/RPMS 2>/dev/null || echo "  /usr/src/azl/RPMS not found"; ls -la /root/rpmbuild/RPMS 2>/dev/null || echo "  /root/rpmbuild/RPMS not found"; exit 1; fi && \
    cp "$RPM_PATH" /azure-cli-dev.rpm && \
    mkdir /out && cp "$RPM_PATH" /out/

FROM ${image} AS execution-env

RUN tdnf update -y

COPY --from=build-env /azure-cli-dev.rpm ./
RUN tdnf install -y ./azure-cli-dev.rpm && \
    az --version

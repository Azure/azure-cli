ARG base_image=ubuntu:xenial
FROM ${base_image} AS build-env

# Update APT packages
RUN apt-get update
RUN apt-get install -y libssl-dev libffi-dev python3-dev debhelper zlib1g-dev wget

# Download Python source code
ARG python_version="3.10.4"
ENV PYTHON_SRC_DIR=/usr/src/python
RUN mkdir -p ${PYTHON_SRC_DIR} && \
    wget -qO- https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tgz \
    | tar -xz -C "${PYTHON_SRC_DIR}"

WORKDIR /azure-cli
RUN ${PYTHON_SRC_DIR}/*/configure --srcdir ${PYTHON_SRC_DIR}/* --prefix $(pwd)/python_env &&\
    make && \
    make install && \
    ln /azure-cli/python_env/bin/python3 /azure-cli/python_env/bin/python && \
    ln /azure-cli/python_env/bin/pip3 /azure-cli/python_env/bin/pip

ENV PATH=/azure-cli/python_env/bin:$PATH

RUN pip install wheel

COPY . .

RUN mkdir -p ./bin/pypi && \
    BUILD_STAGINGDIRECTORY=/azure-cli/bin/pypi ./scripts/release/pypi/build.sh && \
    if [ -d ./privates ]; then find ./privates -name '*.whl' | xargs pip install; fi && \
    find ./bin/pypi -name '*.whl' | xargs pip install &&

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

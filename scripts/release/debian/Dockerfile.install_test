# This dockerfile is meant to test deb_install.sh
# To execute it, run the following command from the directory containing this file:
#   docker build -t deb-install -f Dockerfile.install_test .
# Optionally, one can test specific version of a Debian based linux distro by providing the "base" argument in the form
# of an image ID or tag.
ARG base=ubuntu
FROM $base AS builder

RUN apt-get update
RUN apt-get install -y dos2unix

ADD . .

RUN dos2unix ./deb_install.sh

FROM $base AS execution

COPY --from=builder ./deb_install.sh ./deb_install.sh

RUN ./deb_install.sh -y

CMD ["/bin/bash", "-c", "az --version && az self-test"]

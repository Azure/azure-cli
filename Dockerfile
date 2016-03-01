FROM ubuntu:14.04

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update -qq && \
    apt-get install -qqy --no-install-recommends\
      build-essential \
      curl \
      ca-certificates \
      git \
      python-pip \
      libffi-dev \
      libssl-dev \
      python-dev \
      vim \
      nano \
      jq && \
    rm -rf /var/lib/apt/lists/* && \
    pip install azure==2.0.0a1 && \
    pip install --upgrade requests && \
    pip install cryptography && \
    pip install pyopenssl ndg-httpsclient pyasn1

ENV AZURECLITEMP /tmp/azure-cli
ENV PYTHONPATH $PYTHONPATH:$AZURECLITEMP/src
ENV PATH $PATH:$AZURECLITEMP

RUN mkdir -p $AZURECLITEMP && \
    cp src $AZURECLITEMP -R

RUN echo '#!/bin/bash'>$AZURECLITEMP/az && \
    echo 'python -m azure.cli "$@"'>>$AZURECLITEMP/az && \
    chmod +x $AZURECLITEMP/az && \
	az

ENV EDITOR vim

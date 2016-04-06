FROM ubuntu:15.10

#install *-dev packages below so cryptography package can install
RUN apt-get update -qq && \
    apt-get install -qqy --no-install-recommends\
      python3-pip \
      vim \
      jq \
      build-essential \
      libssl-dev \
      libffi-dev \
      python3-dev && \
    rm -rf /var/lib/apt/lists/*

ENV AZURECLITEMP /opt/azure-cli
ENV PYTHONPATH $PYTHONPATH:$AZURECLITEMP/src
ENV PATH $PATH:$AZURECLITEMP

RUN mkdir -p $AZURECLITEMP
COPY src $AZURECLITEMP/src
COPY az.completion.sh $AZURECLITEMP/
COPY requirements.txt $AZURECLITEMP/
COPY az $AZURECLITEMP/

RUN pip3 install -r $AZURECLITEMP/requirements.txt

RUN chmod +x $AZURECLITEMP/az
RUN ln /usr/bin/python3 /usr/bin/python
RUN echo "source $AZURECLITEMP/az.completion.sh" >> ~/.bashrc
RUN az --help

ENV EDITOR vim

FROM ubuntu:15.10

RUN apt-get update -qq && \
    apt-get install -qqy --no-install-recommends\
      python3-pip \
      vim \
      jq && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install azure==2.0.0rc1

ENV AZURECLITEMP /opt/azure-cli
ENV PYTHONPATH $PYTHONPATH:$AZURECLITEMP/src
ENV PATH $PATH:$AZURECLITEMP

RUN mkdir -p $AZURECLITEMP
COPY src $AZURECLITEMP/src
COPY az.completion.sh $AZURECLITEMP/
COPY az $AZURECLITEMP/

RUN chmod +x $AZURECLITEMP/az
RUN ln /usr/bin/python3 /usr/bin/python
RUN echo "source $AZURECLITEMP/az.completion.sh" >> ~/.bashrc
RUN az

ENV EDITOR vim
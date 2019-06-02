
FROM ubuntu

RUN apt-get update
RUN apt-get -y install python3.7
RUN apt-get -y install python3-pip
RUN apt-get -y install git
RUN git clone https://github.com/zikalino/azure-cli.git
RUN apt-get -y install python3-venv
RUN cd /azure-cli; python3 -m venv env; chmod 777 /azure-cli/env/bin/activate
RUN /bin/bash -c "source /azure-cli/env/bin/activate; pip3 install azdev; azdev setup --cli /azure-cli" 

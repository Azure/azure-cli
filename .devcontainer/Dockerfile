
# start from Ubuntu 16.04
FROM ubuntu:xenial

# install python 3.6, pip, venv and git
RUN apt-get update
RUN apt-get -y install software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get -y install python3.6 python3-pip python3-venv git

# clone azure cli into /workspaces/azure-cli
RUN mkdir /workspaces; cd /workspaces; git clone https://github.com/Azure/azure-cli.git

# create environment in /env and set up 
RUN python3 -m venv env
RUN /bin/bash -c "source /env/bin/activate; pip3 install azdev; azdev setup --cli /workspaces/azure-cli" 

# remove azure-cli as it will be used 
RUN rm -rf ./workspaces/azure-cli

# add environment activation to .bashrc
RUN echo "source /env/bin/activate" >> ~/.bashrc

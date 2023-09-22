FROM mcr.microsoft.com/devcontainers/python:3.11

USER $USER
ARG HOME="/home/$USER"

RUN cd ${HOME} \
    python -m venv env \
    && . env/bin/activate \
    && python -m pip install --upgrade pip \
    && python -m pip install --upgrade azdev

ENV PATH="${HOME}/env/bin:$PATH"

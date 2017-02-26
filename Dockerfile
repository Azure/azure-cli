#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# This Dockerfile uses the latest code from the Git repo.
#   Clone the repo then run 'docker build' with this Dockerfile file to get the latest versions of
#   *all* CLI modules as in the Git repo.

FROM python:3.5.2-alpine

WORKDIR azure-cli
COPY . /azure-cli
# pip wheel - required for CLI packaging
# jmespath-terminal - we include jpterm as a useful tool
RUN pip install --upgrade pip wheel jmespath-terminal
# bash gcc openssl-dev libffi-dev musl-dev - dependencies required for CLI
# jq - we include jq as a useful tool
# openssh - included for ssh-keygen
# ca-certificates 
# wget - required for installing jp
RUN apk update && apk add bash gcc openssl-dev libffi-dev musl-dev jq openssh ca-certificates wget openssl git && update-ca-certificates
# We also, install jp
RUN wget https://github.com/jmespath/jp/releases/download/0.1.2/jp-linux-amd64 -qO /usr/local/bin/jp && chmod +x /usr/local/bin/jp

# 1. Build packages and store in tmp dir
# 2. Install the cli and the other command modules that weren't included
RUN /bin/bash -c 'TMP_PKG_DIR=$(mktemp -d); \
    for d in src/azure-cli src/azure-cli-core src/azure-cli-nspkg src/command_modules/azure-cli-*/; \
    do cd $d; python setup.py bdist_wheel -d $TMP_PKG_DIR; cd -; \
    done; \
    MODULE_NAMES=""; \
    for m in src/command_modules/azure-cli-*/; \
    do MODULE_NAMES="$MODULE_NAMES $(echo $m | cut -d '/' -f 3)"; \
    done; \
    pip install azure-cli $MODULE_NAMES -f $TMP_PKG_DIR;'

# Tab completion
RUN echo -e "\
_python_argcomplete() {\n\
    local IFS='\v'\n\
    COMPREPLY=( \$(IFS=\"\$IFS\"                   COMP_LINE=\"\$COMP_LINE\"                   COMP_POINT=\"\$COMP_POINT\"                   _ARGCOMPLETE_COMP_WORDBREAKS=\"\$COMP_WORDBREAKS\"                   _ARGCOMPLETE=1                   \"\$1\" 8>&1 9>&2 1>/dev/null 2>/dev/null) )\n\
    if [[ \$? != 0 ]]; then\n\
        unset COMPREPLY\n\
    fi\n\
}\n\
complete -o nospace -F _python_argcomplete \"az\"\n\
" > ~/.bashrc

WORKDIR /

CMD bash

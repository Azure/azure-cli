#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

FROM python:3.5.2-alpine

WORKDIR azure-cli
COPY . /azure-cli
RUN pip install --upgrade pip wheel
RUN apk update && apk add bash gcc openssl-dev libffi-dev musl-dev

# 1. Build packages and store in tmp dir
# 2. Install the cli and the other command modules that weren't included
RUN /bin/bash -c 'TMP_PKG_DIR=$(mktemp -d); \
    for d in src/azure-cli src/azure-cli-core src/command_modules/azure-cli-*/; \
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

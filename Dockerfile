#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

FROM python:3.5

# Set the working directory
WORKDIR azure-cli

# bundle source code
COPY . /azure-cli

RUN pip install --upgrade pip

# 1. Build packages and store in tmp dir
# 2. Install the cli
# 3. Install the other command modules that weren't included
RUN TMP_PKG_DIR=$(mktemp -d); \
    for d in src/azure-cli src/azure-cli-core src/command_modules/azure-cli-*/; \
    do cd $d; python setup.py sdist -d $TMP_PKG_DIR; cd -; \
    done; \
    pip install azure-cli -f $TMP_PKG_DIR;\
    for d in src/command_modules/azure-cli-*/; \
    do MODULE_NAME=$(echo $d | cut -d '/' -f 3); \
    pip install $MODULE_NAME -f $TMP_PKG_DIR; \
    done;

# Enable tab completion
RUN echo "\
_python_argcomplete() {\n\
    local IFS='\v'\n\
    COMPREPLY=( \$(IFS=\"\$IFS\"                   COMP_LINE=\"\$COMP_LINE\"                   COMP_POINT=\"\$COMP_POINT\"                   _ARGCOMPLETE_COMP_WORDBREAKS=\"\$COMP_WORDBREAKS\"                   _ARGCOMPLETE=1                   \"\$1\" 8>&1 9>&2 1>/dev/null 2>/dev/null) )\n\
    if [[ \$? != 0 ]]; then\n\
        unset COMPREPLY\n\
    fi\n\
}\n\
complete -o nospace -F _python_argcomplete \"az\"\n\
" > /etc/az.completion
RUN echo "\nsource '/etc/az.completion'\n" >> /etc/bash.bashrc

WORKDIR /

CMD az; bash

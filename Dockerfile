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

# Build and install CLI
RUN python setup.py sdist
ENV AZURE_CLI_DISABLE_POST_INSTALL 1
RUN pip install -f dist/ azure-cli

# Build and install all command modules
RUN for d in src/command_modules/azure-cli-*/; \
    do MODULE_NAME=$(echo $d | cut -d '/' -f 3); \
    cd $d; python setup.py sdist; \
    pip install -f dist/ $MODULE_NAME; \
    cd -; \
    done

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

CMD az

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

FROM python:3.5.2-alpine

ENV CLI_VERSION 0.1.5
ENV CLI_DOWNLOAD_SHA256 cb65651530544c43343e2c80b0d96a681ad0a07367e288ef9fae261093c497f3
ENV CLI_PATCH1_SHA256 d61ef29ace9bbdfef9a25dfbb1f475225bbca174263c8f863ee70f87d0a78bbe
ENV CLI_PATCH2_SHA256 ea0879280dbb3074d464752c27bfe01a7673da14137a4c4315d1938a0d05a03e

# INSTALL DEPENDENCIES
# pip wheel - required for CLI packaging
# jmespath-terminal - we include jpterm as a useful tool
RUN pip install --upgrade pip wheel jmespath-terminal
# bash gcc openssl-dev libffi-dev musl-dev - dependencies required for CLI
# jq - we include jq as a useful tool
# openssh - included for ssh-keygen
# ca-certificates 
# wget - required for installing jp
RUN apk update \
        && apk add bash gcc openssl-dev libffi-dev musl-dev jq openssh ca-certificates wget openssl \
        && update-ca-certificates
# We also, install jp
RUN wget https://github.com/jmespath/jp/releases/download/0.1.2/jp-linux-amd64 -qO /usr/local/bin/jp \
        && chmod +x /usr/local/bin/jp

# DOWNLOAD, EXTRACT, PATCH, BUILD, INSTALL CLI
# Download and extract
RUN mkdir /cli-src
RUN src_zip=$(mktemp) \
        && wget https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_${CLI_VERSION}.tar.gz -qO $src_zip \
        && echo "$CLI_DOWNLOAD_SHA256  $src_zip" | sha256sum -c - \
        && tar -xvzf $src_zip -C /cli-src \
        && rm $src_zip
# Apply patches
RUN patch1=$(mktemp) \
        && wget https://azurecliprod.blob.core.windows.net/patches/patch_0.1.5_component_custom.diff -qO $patch1 \
        && echo "$CLI_PATCH1_SHA256  $patch1" | sha256sum -c - \
        && patch -p1 /cli-src/*/src/command_modules/azure-cli-component/azure/cli/command_modules/component/custom.py $patch1 \
        && rm $patch1
RUN patch2=$(mktemp) \
        && wget https://azurecliprod.blob.core.windows.net/patches/patch_0.1.5_pkg_util.diff -qO $patch2 \
        && echo "$CLI_PATCH2_SHA256  $patch2" | sha256sum -c - \
        && patch -p1 /cli-src/*/src/azure-cli-core/azure/cli/core/_pkg_util.py $patch2 \
        && rm $patch2
# Build and install
RUN /bin/bash -c 'cd /cli-src/*; tmp_pkg_dir=$(mktemp -d); \
    for d in src/azure-cli src/azure-cli-core src/azure-cli-nspkg src/command_modules/azure-cli-*/; \
    do cd $d; python setup.py bdist_wheel -d $tmp_pkg_dir; cd -; \
    done; \
    pip install azure-cli -f $tmp_pkg_dir;'
RUN rm -rf /cli-src

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

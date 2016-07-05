FROM python:3.5

# Set the working directory
WORKDIR azure-cli

# bundle source code
COPY . /azure-cli

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
RUN eval "$(register-python-argcomplete az)"

CMD az

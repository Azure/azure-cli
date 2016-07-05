FROM python:3.5

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

# TODO Need to enable tab completion

CMD az

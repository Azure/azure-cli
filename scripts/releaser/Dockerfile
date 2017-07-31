# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

FROM python:3.5.2-alpine

RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh gcc make \
    openssl-dev libffi-dev musl-dev ca-certificates openssl && update-ca-certificates

RUN pip install --upgrade pip wheel twine requests virtualenv uritemplate.py azure-cli sh

ADD . /

CMD cat README.md; printf "\n\n** starting bash...\n\n"; bash

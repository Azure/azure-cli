# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

FROM python:3.5.2-alpine

RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh

RUN pip install --upgrade pip gunicorn Flask wheel twine requests uritemplate.py

ADD app.py /

ENV FLASK_APP app.py

CMD gunicorn --log-level DEBUG -w 10 -b 0.0.0.0:80 app:app

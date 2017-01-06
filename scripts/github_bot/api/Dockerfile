# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

FROM python:3.5

RUN pip install gunicorn Flask
RUN pip install wheel twine

ADD app.py /

ENV FLASK_APP app.py

CMD gunicorn --log-level DEBUG -w 10 -b 0.0.0.0:5000 app:app

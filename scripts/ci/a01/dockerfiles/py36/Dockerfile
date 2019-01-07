FROM python:3.6-stretch

LABEL a01.product="azurecli"
LABEL a01.index.schema="v2"

COPY build /tmp/build

RUN rm /usr/bin/python && ln /usr/local/bin/python3.6 /usr/bin/python && \
    apt-get update && apt-get install -y jq

COPY docker_app/collect_tests.py /tmp/collect_tests.py
COPY privates /tmp/privates

RUN find /tmp/build -name '*.whl' | xargs pip install -f /tmp/privates && \
    mkdir /app && \
    python /tmp/collect_tests.py > /app/test_index && \
    rm -rf /tmp

COPY docker_app /app

CMD /app/a01droid

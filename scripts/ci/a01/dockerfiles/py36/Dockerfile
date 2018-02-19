FROM python:3.6-jessie

LABEL a01.product="azurecli"
LABEL a01.index.schema="v2"
LABEL a01.env.A01_SP_USERNAME="secret:sp.username"
LABEL a01.env.A01_SP_PASSWORD="secret:sp.password"
LABEL a01.env.A01_SP_TENANT="secret:sp.tenant"
LABEL a01.env.AZURE_TEST_RUN_LIVE="arg-live:True"
LABEL a01.setting.storage="True"

ADD https://a01tools.blob.core.windows.net/droid/latest/linux/a01droid /app/a01droid 
COPY build /tmp/build
COPY docker_app /app

RUN rm /usr/bin/python && ln /usr/local/bin/python3.6 /usr/bin/python && \
    apt-get update && apt-get install jq && \
    find /tmp/build -name '*.whl' | xargs pip install && \
    rm -rf /tmp/build && \
    python /app/collect_tests.py > /app/test_index && \
    rm /app/collect_tests.py && \
    chmod +x /app/a01droid

CMD /app/a01droid

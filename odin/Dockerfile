FROM python:3.11-slim

# hadolint ignore=DL3008
RUN export DEBIAN_FRONTEND=noninteractive && apt-get update \
    # && apt-get install --no-install-recommends -y git\
    && pip install --no-cache-dir pip==23.1 \
    && rm -rf /tmp/* /usr/share/doc/* /var/cache/* /var/lib/apt/lists/* /var/tmp/*

COPY ./requirements.txt /app/

WORKDIR /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY ./ /app/

ENTRYPOINT [ "/app/startup.sh" ]
FROM python:alpine

RUN apk add --update build-base && \
    pip install -U devpi-server devpi-client devpi-web

EXPOSE 3141

COPY entrypoint.sh /
ENTRYPOINT ["/bin/ash", "/entrypoint.sh"]

FROM python:3.11-alpine

RUN apk add --update build-base && \
    pip install -U devpi-server==6.10.0 devpi-client==7.0.3 devpi-web==4.2.3

EXPOSE 3141

COPY entrypoint.sh /
ENTRYPOINT ["/bin/ash", "/entrypoint.sh"]

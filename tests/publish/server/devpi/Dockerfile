FROM python:alpine

RUN pip install -U devpi-server devpi-client devpi-web

EXPOSE 3141

COPY entrypoint.sh /
ENTRYPOINT ["/bin/ash", "/entrypoint.sh"]

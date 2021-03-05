FROM alpine

ENV LANG C.UTF-8

RUN apk update
RUN apk add python3 py3-cryptography py3-paho-mqtt py3-pip
COPY setup.py /tmp/build/
COPY broadlink_bridge/ /tmp/build/broadlink_bridge/
RUN python3 -m pip install /tmp/build \
    && rm -Rf /tmp/build

RUN mkdir -p /config && touch /config/config.ini
VOLUME [ "/config" ]

USER nobody
EXPOSE 8765 8780
CMD [ "broadlink-bridge", "/config/config.ini" ]

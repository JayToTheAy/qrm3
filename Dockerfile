FROM python:3.13.12-trixie

COPY . /app
WORKDIR /app

ARG PKGS="libcairo2 libjpeg-turbo"
ARG UID 1000
ARG GID 1000

RUN \
    echo "**** update system and install packages ****" && \
    apt-get update && \
    apt-get install -y ${PKGS} && \
    apt-get dist-clean && \
    echo "**** install python packages ****" && \
    python -m venv botenv && \
    botenv/bin/pip install -U pip setuptools wheel && \
    botenv/bin/pip install -r requirements.txt && \
    echo "**** clean up ****" && \
    rm -rf \
        /root/.cache \
        /tmp/* \
        /var/cache/*

ENV PYTHONUNBUFFERED 1

USER $UID:$GID

CMD ["/bin/sh", "run.sh", "--pass-errors"]

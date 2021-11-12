FROM ubuntu:bionic

ENV VERSION=AUTO_STRICT
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gnupg2 && apt-get install -y software-properties-common libsecp256k1-dev libsecp256k1-0
RUN apt-get update && apt-get install -y -q --no-install-recommends \
 python3.8 \
 python3-pip

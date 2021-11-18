FROM ubuntu:bionic

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated -q \
    python3.8 \
    python3-pip \
    python3-setuptools \
    python3-wheel

RUN pip3 install wheel grpcio grpcio-tools
RUN pip3 install --upgrade protobuf 

WORKDIR /supply-chain

ENV PATH $PATH:/supply-chain/bin
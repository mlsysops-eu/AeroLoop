FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
        python3 \
        python3-dev \
        python3-pip \
        build-essential \
        libxml2 \
        libxml2-dev \
        tzdata \
        git


RUN python3 -m pip install --upgrade pip


RUN pip3 install \
        wheel \
        pymavlink \
        mavproxy --user\
        dronekit \
        dataclasses \
        dacite \
        requests \
        dataclass-struct \
        pyzmq \
        pyproj


ENV AEROLOOP_HOME=/home/aeroloop

WORKDIR ${AEROLOOP_HOME}
ENV TZ=Europe/Athens

ENV PYTHONPATH=${AEROLOOP_HOME}
ENV PYTHONPATH=${AEROLOOP_HOME}/core:${PYTHONPATH}

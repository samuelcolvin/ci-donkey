FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y build-essential
RUN apt-get install -y python python-pip python-dev python-setuptools

RUN pip install virtualenv

WORKDIR /ci/

ENV CIDONKEY 1

CMD bash /src/ci-donkey.sh

FROM ubuntu:18.04
LABEL maintainer="UVA Research Computing <uvarc@virginia.edu>"
LABEL org.opencontainers.image.source=https://github.com/uvarc/flask-container

RUN apt-get update
RUN apt-get install -y python3 python3-dev python3-pip nginx

COPY ./ ./app
WORKDIR ./app

RUN pip3 install -r requirements.txt

COPY ./nginx.conf /etc/nginx/sites-enabled/default

CMD service nginx start && uwsgi -s /tmp/uwsgi.sock --chmod-socket=666 --manage-script-name --mount /=app:app

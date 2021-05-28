FROM alpine:3.12.0

RUN apk update
RUN apk add postgresql-dev gcc python3-dev musl-dev libffi-dev make
RUN apk add python3
RUN apk add --update py-pip
RUN pip install --upgrade pip

ARG DBHOST_ARG
ARG DBPORT_ARG
ARG DBUSER_ARG
ARG DBPASSWD_ARG
ARG DB_ARG

ADD monitor /monitor/
ADD common /common/
ADD doc /doc/
COPY requirements.txt .

RUN pip install -r requirements.txt

ENV DBHOST=$DBHOST_ARG
ENV DBPORT=$DBPORT_ARG
ENV DBUSER=$DBUSER_ARG
ENV DBPASSWD=$DBPASSWD_ARG
ENV DB=$DB_ARG
ENV PYTHONPATH "/monitor/:/common/common/:/doc/"
ENTRYPOINT ["python3", "monitor/main.py", "--monitor-config", "doc/monitor-config.yml", "--dev"]

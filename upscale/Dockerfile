FROM ubuntu:latest
ENV TZ=Europe/Minsk
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /upscale

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3-pip
RUN apt-get install -y python3
RUN apt-get install -y libglu1-mesa-dev
RUN apt-get -qq -y install libgtk2.0-dev



COPY ./requirements.txt /upscale
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /upscale

RUN celery -A server.celery worker
RUN python3 server.py
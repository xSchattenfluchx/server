FROM python:3.6

# Apt-install mysql client and cleanup temporary files afterwards
RUN apt-get update && apt-get install --force-yes -y mysql-client git vim liblua5.1-dev libmagickwand-dev && apt-get clean
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN pip install pipenv

ADD . /code/
WORKDIR /code/

# TODO, don't install dev-time requirements in production runtime image
RUN pipenv install -d

# Main entrypoint and the default command that will be run
CMD ["/usr/local/bin/pipenv", "run start"]

# Game server runs on 8000/tcp, lobby server runs on 8001/tcp, nat echo server runs on 30351/udp
EXPOSE 8000 8001 30351

RUN python3.6 -V

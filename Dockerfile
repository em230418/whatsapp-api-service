FROM selenium/standalone-firefox-debug:3.141.59-20210830

USER root

RUN apt-get update && apt-get install -y python3-pip git libmagic1 sqlite3

RUN python3 -m pip install "selenium<4.0"

RUN curl https://raw.githubusercontent.com/itpp-labs/whatsapp-api/master/requirements/base.txt > /tmp/base.txt
RUN python3 -m pip install -r /tmp/base.txt

RUN python3 -m pip install git+https://github.com/itpp-labs/whatsapp-api.git

EXPOSE 5000

RUN python3 -m pip install Flask

COPY ./ /opt/app

USER 1200:1201

RUN mkdir -p /home/seluser/.mozilla/firefox
VOLUME /home/seluser/.mozilla/firefox

CMD ["/opt/app/entrypoint.sh"]

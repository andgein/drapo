FROM python:3.5

ENV PYTHONUNBUFFERED 1

ENV DOCKERIZE_VERSION v0.3.0
RUN wget -q https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN mkdir -p /app
WORKDIR /app

COPY ./src/web/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn psycopg2

COPY ./src/web/ /app
COPY ./docker/web /app

COPY ./docker/web/settings.docker.py /app/drapo/settings.py

ENTRYPOINT ["/app/docker-entrypoint.sh"]

EXPOSE 80

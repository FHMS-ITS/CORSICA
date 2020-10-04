FROM nginx:alpine

COPY apps/web/main/main /app/main/

COPY apps/web/main/manage.py /app/manage.py
COPY apps/web/main/requirements.txt /app/requirements.txt

COPY docker/web/uwsgi.ini /app/uwsgi.ini
COPY docker/web/default.conf /etc/nginx/conf.d/default.conf
COPY docker/web/supervisor.ini /etc/supervisor.d/

RUN apk update && apk add --no-cache python3 python3-dev mariadb-dev g++ linux-headers supervisor
RUN pip3 install uwsgi
RUN pip3 install -r /app/requirements.txt

# Cleanup
RUN apk del g++ mariadb-dev linux-headers
RUN apk add --no-cache mariadb-client-libs

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

WORKDIR /app

VOLUME /app

EXPOSE 80
CMD ["supervisord", "-n"]
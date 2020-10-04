FROM alpine:latest

RUN apk add --no-cache wget ca-certificates

RUN mkdir /crawler/
RUN mkdir /tmp/wget/

RUN echo "wget -m " \
         "--directory-prefix '/tmp/wget/' " \
         "--execute robots=off " \
         "--no-check-certificate "\
         "--timeout=60" \
         "--tries=2" \
         "-D \$1 " \
         "\$2" \
         "2>/crawler/stderr.log >/crawler/stdout.log" > /wget.sh

RUN chmod +x /wget.sh


RUN echo "/wget.sh \$1 \$2; " \
         "mv /tmp/wget/*/ /tmp/wget/www;" \
         "find /tmp/wget/www/ -exec touch -a -m -t 201801010000 {} \;;" \
         "cd /tmp/wget/; tar cf /crawler/result.tar www/;" > /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT  ["sh","/entrypoint.sh"]

FROM ubuntu:latest

RUN apt-get update && apt-get upgrade
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -qq -y \
                                            docker python3 python3-pip sudo zlibc \
                                            libjpeg-dev gcc python3-dev \
                                            linux-headers-generic musl-dev \
                                            libffi-dev libssl-dev \
                                            python \
                                            zip poppler-utils \
                                            upx-ucl unrar \
                                            python-magic  netpbm\
                                            e2tools libxml2-utils\
                                            squashfs-tools \
                                            cabextract unshield \
                                            p7zip-full cpio \
                                            mtd-utils lzip lrzip \
                                            lzop arj ncompress \
                                            icoutils gettext python-pil \
                                            rpm python-rpm vorbis-tools \
                                            ctags python-matplotlib python-pydot \
                                            bsdiff python-reportlab fonts-liberation \
                                            clamav john python-psycopg2 net-tools


COPY ./docker/core/requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r /tmp/requirements.txt

COPY ./docker/core/bat.conf /etc/corsica/bat.conf
COPY ./docker/core/bat/*.deb /tmp/bat/

COPY ./docker/core/bat.sh /tmp/bat/bat.sh
RUN chmod +x /tmp/bat/bat.sh && /tmp/bat/bat.sh


COPY ./ /srv/corsica/
WORKDIR /srv/corsica
RUN chmod +x /srv/corsica/corsica.py
RUN mkdir /tmp/ram_disk

CMD ["./corsica.py"]
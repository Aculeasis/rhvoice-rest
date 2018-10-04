#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

RUNTIME_PACKAGES="libao4 libasound2 libportaudio2 lame python3 python3-pip python3-setuptools locales opus-tools \
locales-all"
BUILD_PACKAGES="git scons build-essential libao-dev pkg-config flite1-dev portaudio19-dev"


apt-get update -y
apt-get -y install --no-install-recommends ${RUNTIME_PACKAGES} ${BUILD_PACKAGES}
sudo -H python3 -m pip install --upgrade pip setuptools wheel
sudo -H pip3 install aiohttp pymorphy2 rhvoice-wrapper

mkdir -p /opt/rhvoice_proxy
cp app.py /opt/rhvoice-rest.py
chmod +x /opt/rhvoice-rest.py

{
echo '[Unit]'
echo 'Description=RHVoice REST API'
echo 'After=network.target'
echo '[Service]'
echo 'ExecStart=/opt/rhvoice-rest.py'
echo 'Restart=always'
echo 'User=root'
echo '[Install]'
echo 'WantedBy=multi-user.target'
} > /etc/systemd/system/rhvoice-rest.service

git clone https://github.com/Olga-Yakovleva/RHVoice.git /opt/RHVoice
cd /opt/RHVoice && git checkout dc36179 && scons && scons install && ldconfig

git clone https://github.com/vantu5z/RHVoice-dictionary.git /opt/RHVoice-dictionary && \
mkdir -p /usr/local/etc/RHVoice/dicts/Russian/ && mkdir -p /opt/data && \
cp /opt/RHVoice-dictionary/*.txt /usr/local/etc/RHVoice/dicts/Russian/ && \
cp -R /opt/RHVoice-dictionary/tools /opt/ && \
cd /opt && rm -rf /opt/RHVoice /opt/RHVoice-dictionary

systemctl enable rhvoice-rest.service
systemctl start rhvoice-rest.service
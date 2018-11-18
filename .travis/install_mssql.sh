#!/usr/bin/env bash

wget http://www.unixodbc.org/unixODBC-2.3.1.tar.gz
tar xvf unixODBC-2.3.1.tar.gz
cd unixODBC-2.3.1/
./configure --disable-gui \
            --disable-drivers \
            --enable-iconv \
            --with-iconv-char-enc=UTF8 \
            --with-iconv-ucode-enc=UTF16LE
make
sudo make install
sudo ldconfig

sudo su <<EOF
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/14.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
EOF

sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install msodbcsql17

docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=Strong!Passw0rd' -p 1433:1433 -d mcr.microsoft.com/mssql/server:2017-latest

#!/bin/sh

if [ ! -f /etc/apt/sources.list.d/microsoft-prod.list ]; then
    curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
    sudo sh -c "curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -r -s)/prod.list > /etc/apt/sources.list.d/mssql-release.list"
fi

sudo apt-get update
sudo ACCEPT_EULA=Y apt-get -y install msodbcsql17 unixodbc

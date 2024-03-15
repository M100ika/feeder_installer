#!/bin/bash

# Обновление списка пакетов и установленных программ
sudo apt update && sudo apt upgrade -y

# Установка необходимых программ
sudo apt install -y python3 python3-pip git teamviewer

# Обновление pip
sudo python3 -m pip install --upgrade pip

# Установка необходимых Python-библиотек
sudo pip3 install loguru requests numpy RPi.GPIO wabson.chafon-rfid pyserial

# Добавление конфигурации в dhcpcd.conf без перезаписи всего файла
CONFIG="nodhcp\n\ninterface eth0\nstatic ip_address=192.168.1.249/24\nstatic routers=192.168.1.1\nstatic domain_name_servers=192.168.1.1 8.8.8.8 fd51:42f8:caae:d92::1"

# Проверяем, содержит ли файл уже эту конфигурацию
if ! grep -q "interface eth0" /etc/dhcpcd.conf; then
    echo -e "$CONFIG" | sudo tee -a /etc/dhcpcd.conf > /dev/null
fi

# Скачивание config.ini в /etc/feeder/
sudo mkdir -p /etc/feeder
sudo curl -o /etc/feeder/config.ini https://raw.githubusercontent.com/M100ika/feeder_installer/main/config/config.ini

# Скачивание feeder.service в /etc/systemd/system/ и его регистрация
sudo curl -o /etc/systemd/system/feeder.service https://raw.githubusercontent.com/M100ika/feeder_installer/main/config/feeder.service
sudo systemctl daemon-reload
# Стартовать сервис пока не требуется

# Клонирование и установка программы
sudo mkdir -p /opt/feeder_project
sudo git clone https://github.com/M100ika/feeder_installer_submodule_src.git /opt/feeder_project
# Последующие шаги для настройки или установки внутри /opt/feeder_project

sudo apt install -y teamviewer

echo "Установка завершена."

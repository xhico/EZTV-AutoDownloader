#!/bin/bash

sudo mv /home/pi/EZTV-AutoDownloader/EZTV-AutoDownloader.service /etc/systemd/system/ && sudo systemctl daemon-reload
python3 -m pip install -r /home/pi/EZTV-AutoDownloader/requirements.txt --no-cache-dir
chmod +x -R /home/pi/EZTV-AutoDownloader/*
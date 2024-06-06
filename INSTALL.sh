#!/bin/bash

python3 -m venv /home/pi/EZTV-AutoDownloader/venv
source /home/pi/EZTV-AutoDownloader/venv/bin/activate
python3 -m pip install -r /home/pi/EZTV-AutoDownloader/requirements.txt --no-cache-dir
chmod +x -R /home/pi/EZTV-AutoDownloader/*
sudo mv /home/pi/EZTV-AutoDownloader/EZTV-AutoDownloader.service /etc/systemd/system/ && sudo systemctl daemon-reload

git clone https://github.com/xhico/Misc.git /home/pi/Misc
rsync -avp --progress /home/pi/Misc/Misc.py /home/pi/EZTV-AutoDownloader/venv/lib/python$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")/site-packages/
rm -rf /home/pi/Misc/
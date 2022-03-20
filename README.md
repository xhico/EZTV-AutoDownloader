# EZTV-AutoDownloader / Transmission Manager

Auto Downloader from EZTV
</br>
Transmission-Remote Manager

## Features
* Automatic download from EZTV
* Check Episode and Season to see if ep is newer
* Remove torrent from Transmission if Completed
* Email notifications on add and complete.


## Config
Loads config from local file (Example bellow)
```
{
  "Bull": {
    "season": 6,
    "episode": 14
  },
  "Chicago Fire": {
    "season": 10,
    "episode": 16
  },
  "Magnum P.I.": {
    "season": 4,
    "episode": 16
  },
  "NCIS": {
    "season": 19,
    "episode": 15
  },
  "NCIS: Los Angeles": {
    "season": 13,
    "episode": 11
  },
  "Young Sheldon": {
    "season": 5,
    "episode": 16
  }
}
```

## Installation
```
python3 -m pip install requests transmission-rpc yagmail
```

## Usage
Manual
```
python3 EZTV-AutoDownloader.py
```
Crontab
```
*/30 * * * * python3 /home/pi/EZTV-AutoDownloader/EZTV-AutoDownloader.py
```

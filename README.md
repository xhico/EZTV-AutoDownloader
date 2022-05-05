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
    "imdb_id": "5827228",
    "season": 6,
    "episode": 19
  },
  "Chicago Fire": {
    "imdb_id": "2261391",
    "season": 10,
    "episode": 19
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

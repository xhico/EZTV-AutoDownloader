# -*- coding: utf-8 -*-
# !/usr/bin/python3

# python3 -m pip install requests transmission-rpc yagmail

import datetime
import json
import os

import requests
import yagmail
from transmission_rpc import Client


def get911(key):
    with open('/home/pi/.911') as f:
        data = json.load(f)
    return data[key]


def getConfig():
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    return data


def isInTitle(title):
    for show in TVSHOWS:
        if title.find(show) != -1:
            return show
    return None


def getLastSeasonEpisode(title):
    try:
        show = CONFIG[title]
        season = show["season"]
        episode = show["episode"]
    except KeyError:
        season = 1
        episode = 1
    return int(season), int(episode)


def getTorrents():
    torrents = {}
    page = 1

    # Infinite Loop, until torrent date is over x minutes
    while True:
        checkEnd = False
        pageURL = API_URL + "?page=" + str(page)

        # Download JSON
        r = requests.get(pageURL)
        jsonTorrents = json.loads(r.text)

        # Iterate over every torrent
        for torrent in jsonTorrents["torrents"]:
            date_released_unix = torrent["date_released_unix"]

            # Check if torrent date is older than x minutes, stop
            FROM_DATE = datetime.datetime.now() + datetime.timedelta(minutes=-30)
            FROM_DATE = int(datetime.datetime.timestamp(FROM_DATE))
            if date_released_unix < FROM_DATE:
                checkEnd = True
                break

            # Check if torrent belong to one of the user's shows
            title = torrent["title"]
            show = isInTitle(title)
            if show is not None and ("1080" in title or "720" in title) and ("x264" in title or "x265" in title):

                # Check if episode is newer than the last
                season, episode = int(torrent["season"]), int(torrent["episode"])
                lastSeason, lastEpisode = getLastSeasonEpisode(show)
                if (season == lastSeason and episode > lastEpisode) or (season > lastSeason):
                    torrents[show] = {
                        "title": title,
                        "magnet_url": torrent["magnet_url"],
                        "season": season,
                        "episode": episode
                    }

        if checkEnd:
            break
        page += 1

    return torrents


def main():
    # Get newest torrent
    torrents = getTorrents()

    # Iterate over every torrent
    for show, torrent in torrents.items():
        title = torrent["title"]
        magnet_url = torrent["magnet_url"]
        season = torrent["season"]
        episode = torrent["episode"]
        print(title)

        # Add torrent to Transmission
        TRANSMISSION.add_torrent(magnet_url)
        YAGMAIL.send(EMAIL_RECEIVER, "Torrent Added - " + show, title)

        # Add to CONFIG
        CONFIG[show] = {"season": season, "episode": episode}

    # Update CONFIG
    with open(CONFIG_FILE, 'w') as outfile:
        json.dump(CONFIG, outfile, indent=4)

    # Remove complete torrent
    torrents = TRANSMISSION.get_torrents()
    for torrent in torrents:
        if torrent.progress == 100.0:
            print("Complete - " + torrent.name)
            TRANSMISSION.remove_torrent(torrent.id, delete_data=False)
            YAGMAIL.send(EMAIL_RECEIVER, "Torrent Complete", torrent.name)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_FILE = "config.json"
    API_URL = "https://eztv.re/api/get-torrents"
    CONFIG = getConfig()
    TVSHOWS = CONFIG.keys()

    # Set Transmission
    TRANSMISSION_USER = get911('TRANSMISSION_USER')
    TRANSMISSION_PASS = get911('TRANSMISSION_PASS')
    TRANSMISSION_HOST = "localhost"
    TRANSMISSION = Client(host=TRANSMISSION_HOST, username=TRANSMISSION_USER, password=TRANSMISSION_PASS)

    # Set email
    EMAIL_USER = get911('EMAIL_USER')
    EMAIL_APPPW = get911('EMAIL_APPPW')
    EMAIL_RECEIVER = get911('EMAIL_RECEIVER')
    YAGMAIL = yagmail.SMTP(EMAIL_USER, EMAIL_APPPW)

    try:
        main()
    except Exception as ex:
        YAGMAIL.send(EMAIL_RECEIVER, "Error - " + os.path.basename(__file__), str(ex))

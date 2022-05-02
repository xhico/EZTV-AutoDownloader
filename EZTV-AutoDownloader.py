# -*- coding: utf-8 -*-
# !/usr/bin/python3

# python3 -m pip install requests transmission-rpc yagmail

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


def getLastSeasonEpisode(show):
    try:
        season = CONFIG[show]["season"]
        episode = CONFIG[show]["episode"]
    except KeyError:
        season = 1
        episode = 1
    return int(season), int(episode)


def getTorrents():
    print("getTorrents")
    newTorrents = {}

    # Iterate over every show
    for show in TVSHOWS:
        # Download last episode JSON
        r = requests.get(API_URL + CONFIG[show]["imdb_id"])
        torrents = json.loads(r.text)["torrents"]
        lastSeason, lastEpisode = getLastSeasonEpisode(show)

        # Iterate over every torrent
        for torrent in reversed(torrents):
            title, season, episode = torrent["title"], int(torrent["season"]), int(torrent["episode"])

            # Check if torrent is valid
            if ("1080" in title or "720" in title) and ("x264" in title or "x265" in title) and ("MeGusta" in title or "CAKES" in title):
                # Check if episode is newer than the last
                if (season == lastSeason and episode > lastEpisode) or (season > lastSeason):
                    newTorrents[torrent["id"]] = {
                        "show": show,
                        "imdb_id": torrent["imdb_id"],
                        "title": title,
                        "magnet_url": torrent["magnet_url"],
                        "season": season,
                        "episode": episode
                    }

                    lastSeason, lastEpisode = season, episode

    return newTorrents


def main():
    # Get newest torrent
    torrents = getTorrents()

    # Iterate over every torrent
    for torrent in torrents.values():
        show = torrent["show"]
        imdb_id = torrent["imdb_id"]
        title = torrent["title"]
        magnet_url = torrent["magnet_url"]
        season = torrent["season"]
        episode = torrent["episode"]
        print(title)

        # Add torrent to Transmission
        TRANSMISSION.add_torrent(magnet_url)
        YAGMAIL.send(EMAIL_RECEIVER, "Torrent Added - " + show, title)

        # Add to CONFIG
        CONFIG[show] = {"imdb_id": imdb_id, "season": season, "episode": episode}

    # Update CONFIG
    with open(CONFIG_FILE, 'w') as outfile:
        json.dump(CONFIG, outfile, indent=2)

    # Remove complete torrent
    torrents = TRANSMISSION.get_torrents()
    for torrent in torrents:
        if torrent.progress == 100.0:
            print("Complete - " + torrent.name)
            TRANSMISSION.remove_torrent(torrent.id, delete_data=False)
            YAGMAIL.send(EMAIL_RECEIVER, "Torrent Complete - " + torrent.name, torrent.name)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_FILE = "config.json"
    API_URL = "https://eztv.re/api/get-torrents?imdb_id="
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
        print(ex)

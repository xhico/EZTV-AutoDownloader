# -*- coding: utf-8 -*-
# !/usr/bin/python3

# python3 -m pip install requests yagmail transmission-rpc yagmail --no-cache-dir

import datetime
import json
import os
import traceback
import requests
import yagmail
import logging
import base64
from transmission_rpc import Client
from Misc import get911
    

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
    logger.info("getTorrents")
    newTorrents = {}

    # Iterate over every show
    for show in TVSHOWS:

        # Download last episode JSON
        try:
            logger.info(API_URL + CONFIG[show]["imdb_id"])
            r = requests.get(API_URL + CONFIG[show]["imdb_id"], timeout=10).json()
            torrents = r["torrents"]
        except Exception as ex:
            logger.error("Failed to download show")
            continue

        # Iterate over every torrent
        lastSeason, lastEpisode = getLastSeasonEpisode(show)
        for torrent in reversed(torrents):
            title, season, episode = torrent["title"], int(torrent["season"]), int(torrent["episode"])

            # Check if torrent is valid
            if ("1080" in title or "720" in title) and ("x265" in title or "x264" in title) and "MeGusta" in title:
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
        logger.info(title)

        # Add torrent to Transmission
        TRANSMISSION.add_torrent(magnet_url)
        try:
            YAGMAIL.send(EMAIL_RECEIVER, "Torrent Added - " + show, title)
        except:
            logger.error("Couldn'not send ADDED email")

        # Add to CONFIG
        CONFIG[show] = {"imdb_id": imdb_id, "season": season, "episode": episode}

    # Update CONFIG
    with open(CONFIG_FILE, 'w') as outfile:
        json.dump(CONFIG, outfile, indent=2)

    # Remove complete torrent
    torrents = TRANSMISSION.get_torrents()
    for torrent in torrents:
        if torrent.progress == 100.0:
            logger.info("Complete - " + torrent.name)
            TRANSMISSION.remove_torrent(torrent.id, delete_data=False)
            YAGMAIL.send(EMAIL_RECEIVER, "Torrent Complete - " + torrent.name, torrent.name)


if __name__ == '__main__':
    # Set Logging
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.abspath(__file__).replace(".py", ".log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
    logger = logging.getLogger()

    logger.info("----------------------------------------------------")

    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    API_URL = "https://eztv.re/api/get-torrents?imdb_id="
    CONFIG = getConfig()
    TVSHOWS = CONFIG.keys()

    # Set Transmission
    TRANSMISSION_USER = get911('TRANSMISSION_USER')
    TRANSMISSION_PASS = get911('TRANSMISSION_PASS')
    TRANSMISSION_HOST = get911('TRANSMISSION_HOST')
    TRANSMISSION_PORT = get911('TRANSMISSION_PORT')
    TRANSMISSION_PATH = get911('TRANSMISSION_PATH')
    TRANSMISSION = Client(host=TRANSMISSION_HOST, port=TRANSMISSION_PORT, path=TRANSMISSION_PATH, username=TRANSMISSION_USER, password=TRANSMISSION_PASS)

    # Set email
    EMAIL_USER = get911('EMAIL_USER')
    EMAIL_APPPW = get911('EMAIL_APPPW')
    EMAIL_RECEIVER = get911('EMAIL_RECEIVER')
    YAGMAIL = yagmail.SMTP(EMAIL_USER, EMAIL_APPPW)

    try:
        main()
    except Exception as ex:
        logger.error(traceback.format_exc())
        yagmail.SMTP(EMAIL_USER, EMAIL_APPPW).send(EMAIL_RECEIVER, "Error - " + os.path.basename(__file__), str(traceback.format_exc()))
    finally:
        logger.info("End")

# -*- coding: utf-8 -*-
# !/usr/bin/python3

import json
import os
import traceback
import requests
import logging
from transmission_rpc import Client
from Misc import get911, sendEmail


def getLastSeasonEpisode(show):
    """
    Get the last watched episode of a given show from a configuration file.

    Args:
    - show (str): The name of the show to retrieve the last watched episode for.

    Returns:
    - tuple: A tuple containing two integers representing the last watched season and episode.
             If the show is not found in the configuration file, the function returns (1, 1) as default.
    """
    try:
        season = SAVED_INFO[show]["season"]  # get the last watched season for the given show
        episode = SAVED_INFO[show]["episode"]  # get the last watched episode for the given show
    except KeyError:  # if the show is not found in the configuration file
        season = 1  # set the default season to 1
        episode = 1  # set the default episode to 1
    return int(season), int(episode)  # return a tuple of two integers representing the last watched season and episode


def getTorrents():
    """
    Downloads the latest torrents for each TV show in the CONFIG.keys() list.

    Returns:
        A dictionary containing information about the new torrents, with each key being the torrent ID.
    """
    logger.info("getTorrents")
    newTorrents = {}
    API_URL = "https://eztv.re/api/get-torrents?imdb_id="

    # Iterate over every show
    for show in CONFIG.keys():

        # Download last episode JSON
        try:
            # Send GET request to API_URL with the imdb_id of the show.
            # Timeout is set to 10 seconds.
            logger.info(API_URL + CONFIG[show]["imdb_id"])
            r = requests.get(API_URL + CONFIG[show]["imdb_id"], timeout=10).json()
            torrents = r["torrents"]
        except Exception as ex:
            # If there is an error, log it and move on to the next show.
            logger.error("Failed to download show")
            logger.error(ex)
            continue

        # Iterate over every torrent
        lastSeason, lastEpisode = getLastSeasonEpisode(show)
        for torrent in reversed(torrents):
            title, season, episode = torrent["title"], int(torrent["season"]), int(torrent["episode"])

            # Check if torrent is valid
            if ("1080" in title or "720" in title) and ("x265" in title or "x264" in title) and "MeGusta" in title:
                # Check if episode is newer than the last
                if (season == lastSeason and episode > lastEpisode) or (season > lastSeason):
                    # If the torrent meets the criteria, add it to the newTorrents dictionary.
                    newTorrents[torrent["id"]] = {
                        "show": show,
                        "imdb_id": torrent["imdb_id"],
                        "title": title,
                        "magnet_url": torrent["magnet_url"],
                        "season": season,
                        "episode": episode
                    }

                    # Update the last season and episode
                    lastSeason, lastEpisode = season, episode

    return newTorrents


def main():
    """
    Adds the newest torrent to Transmission, sends an email notification, updates a config file,
    and removes completed torrents from Transmission.

    Returns:
        None
    """
    # Get newest torrent
    torrents = getTorrents()

    # Iterate over every torrent
    for torrent in torrents.values():
        show = torrent["show"]
        title = torrent["title"]
        magnet_url = torrent["magnet_url"]
        season = torrent["season"]
        episode = torrent["episode"]
        logger.info(title)

        # Add torrent to Transmission
        TRANSMISSION.add_torrent(magnet_url)
        sendEmail("Torrent Added - " + show, title)

        # Add to CONFIG
        SAVED_INFO[show] = {"season": season, "episode": episode}

    # Update SAVED_INFO
    with open(SAVED_INFO_FILE, 'w') as outfile:
        json.dump(SAVED_INFO, outfile, indent=2)

    # Remove complete torrent
    torrents = TRANSMISSION.get_torrents()
    for torrent in torrents:
        if torrent.progress == 100.0:
            logger.info("Complete - " + torrent.name)
            TRANSMISSION.remove_torrent(torrent.id, delete_data=False)
            sendEmail("Torrent Complete - " + torrent.name, torrent.name)


if __name__ == '__main__':
    # Set Logging
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.abspath(__file__).replace(".py", ".log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
    logger = logging.getLogger()

    logger.info("----------------------------------------------------")

    # Open the configuration file in read mode
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    SAVED_INFO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_info.json")
    with open(CONFIG_FILE) as inFile:
        CONFIG = json.load(inFile)
    with open(SAVED_INFO_FILE) as inFile:
        SAVED_INFO = json.load(inFile)

    # Set Transmission
    TRANSMISSION_HOST = get911('TRANSMISSION_HOST')
    TRANSMISSION_PORT = get911('TRANSMISSION_PORT')
    TRANSMISSION_PATH = get911('TRANSMISSION_PATH') + "rpc"
    TRANSMISSION = Client(host=TRANSMISSION_HOST, port=TRANSMISSION_PORT, path=TRANSMISSION_PATH)

    try:
        main()
    except Exception as ex:
        logger.error(traceback.format_exc())
        sendEmail(os.path.basename(__file__), str(traceback.format_exc()))
    finally:
        logger.info("End")

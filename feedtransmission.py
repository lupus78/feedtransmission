#!/usr/bin/python

import sys, os
import feedparser
import transmission_rpc
import argparse
import logging
import re
import requests
from random import random, seed
import json

# files path check/construction
def normalizeFilePath(path, is_exist=True):
    # check if path is absolute
    if os.path.isabs(path):
        filepath = path
    # construct absolute path
    else:
        filepath = os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), path)
    # check if file exist
    if is_exist and not os.path.exists(filepath):
        logging.error(f"Error: file not found:\'{path}\': ")
        exit(0)
    return filepath

# read the added torrents list from the file
def readAddedTorrents():
	addeditems = []
	if os.path.exists(added_torrents_filepath):
		with open(added_torrents_filepath,'r') as f:
			for line in f:
				addeditems.append(line.rstrip('\n'))
	return addeditems

def writeAddedTorrents(torrent):
    with open(added_torrents_filepath, 'a') as f:
        f.write(torrent + '\n')

# Download torrent with python
def downloadTorrent(url):
    # download content
    response = requests.get(url)
    if response.ok:
        return response.content
    else:
        logging.warning(f"Downloading torrent failed for: {url}")
        response.raise_for_status()

# add the link to transmission and appends the link to the added items
def addTorrentToTransmission(item):
    # decide if we download a torent or just pass a url
    if configuration["download_with_python"]:
        url = downloadTorrent(item.link)
    else:
        url = item.link

    if configuration["download_dir"] is not None and configuration["download_dir"] != "":
        tc.add_torrent(url, download_dir = configuration["download_dir"], paused = configuration["add_paused"])
        logging.info(f"Added Torrent: {item.title} ({item.link}) to {configuration["download_dir"]}")
    else:
        tc.add_torrent(url, paused = configuration["add_paused"])
        logging.info(f"Added Torrent: {item.title} ({item.link}) to default directory")

    writeAddedTorrents(item.link)

# search for patterns by selected args
def searchPattern(title):
    if len(search_patterns_list) > 0: 
        for pattern in search_patterns_list:
            if re.search(pattern, title) is not None:
                return True
        return False
    return True

# parses and adds torrents from feed
def parseFeed(feed_url):
    feed = feedparser.parse(feed_url)
    if feed.bozo and feed.bozo_exception:
        logging.error("Error reading feed \'{0}\': ".format(feed_url) + str(feed.bozo_exception).strip())
        return

    addeditems = readAddedTorrents()

    for item in feed.entries:
        if searchPattern(item.title):
            if item.link not in addeditems:
                try:
                    addTorrentToTransmission(item)
                except transmission_rpc.error.TransmissionError as e:
                    logging.error("Error adding item \'{0}\': {1}".format(item.link, e.message))
                #except transmission_rpc.HTTPHandlerError as e:
                #    logging.error("Error adding item \'{0}\': [{1}] {2}".format(item.link, e.code, e.message))
                except:
                    logging.error("Error adding item \'{0}\': {1}".format(item.link, str(sys.exc_info()[0]).strip()))

# parses the arguments and loads the config file
def get_configuration():
    # Parse the arguments, with the defaults
    args = parser.parse_args()
    config = vars(args)

    # Layer config file settings on top of defaults.
    if args.config_file:
        filepath = normalizeFilePath(args.config_file)
        with open(filepath) as config_file:
            file_config = json.load(config_file)
            # Convert keys from kebab-case (in JSON) to snake_case (in Python)
            file_config_converted = {k.replace('-', '_'): v for k, v in file_config.items()}
            # Use the converted dictionary for the update
            config.update(file_config_converted)

    return config

# Generates a list of search patterns from the script's configuration.
def get_search_patterns():
    patterns = []
    # If the single search_pattern argument is present, use it.
    if configuration.get("search_pattern"):
        patterns.append(configuration["search_pattern"])

    # Otherwise, if the search_patterns_file argument is present, read the file.
    elif configuration.get("search_patterns_file"):
        try:
            filepath = normalizeFilePath(configuration["search_patterns_file"])
            with open(filepath, 'r') as f:
                # Read each line, strip whitespace, and add it to the list if it's not empty.
                patterns = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logging.error(f"Could not read search patterns file: {e}")
            # Return an empty list on error to prevent unintended downloads.
            return []

    return patterns


# argparse configuration and argument definitions
parser = argparse.ArgumentParser(
    description='Reads RSS/Atom Feeds and add torrents to Transmission',
    # Allows help text to show default values
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
# --- Group for required settings ---
required_group = parser.add_argument_group('Required Settings', 'Either a config file or feed URLs must be provided.')
required_group.add_argument('--config-file',
                    default=None,
                    metavar='<path>',
                    help='Path to the config JSON file.')
required_group.add_argument('--feed-urls',
                    default=None,
                    metavar='<url>',
                    type=str,
                    nargs='+',
                    help='One or more space-separated Feed URL(s).')

# --- Transmission Connection Settings ---
trans_group = parser.add_argument_group('Transmission Settings')
trans_group.add_argument('--transmission-host',
                    default='localhost',
                    metavar='<host>',
                    help='Host for Transmission RPC.')
trans_group.add_argument('--transmission-port',
                    default=9091,
                    metavar='<port>',
                    type=int,
                    help='Port for Transmission RPC.')
trans_group.add_argument('--transmission-user',
                    default=None,
                    metavar='<user>',
                    help='Username for Transmission RPC.')
trans_group.add_argument('--transmission-password',
                    default=None,
                    metavar='<password>',
                    help='Password for Transmission RPC.')

# --- Torrent Handling Settings ---
torrent_group = parser.add_argument_group('Torrent Settings')
torrent_group.add_argument('--add-paused',
                    action='store_true',
                    help='Disables starting torrents after adding them.')
torrent_group.add_argument('--download-dir',
                    default=None,
                    metavar='<dir>',
                    help='The directory where the downloaded contents will be saved.')
torrent_group.add_argument('--download_with_python',
                    action='store_true',
                    help='If specified, the torrent file is downloaded by this script, not by Transmission.')

# --- Filtering Settings ---
filter_group = parser.add_argument_group('Filtering Settings')
# Create a mutually exclusive group to ensure only one pattern method is used
pattern_group = filter_group.add_mutually_exclusive_group()
pattern_group.add_argument('--search-pattern',
                    default=None,
                    metavar='<pattern>',
                    help='A single regex pattern to filter the feed. Cannot be used with --search-patterns-file.')
pattern_group.add_argument('--search-patterns-file',
                    default=None,
                    metavar='<path>',
                    help='Path to a text file with search patterns. Cannot be used with --search-pattern.')

# --- Other Settings ---
other_group = parser.add_argument_group('Other Settings')
other_group.add_argument('--added-torrents-file',
                    default='added_torrents.txt',
                    metavar='<path>',
                    help='Path to a text file which will be used to track which torrents are already added.')
other_group.add_argument('--clear-added-torrents',
                    action='store_true',
                    help='Deletes the added torrents file and quits.')
other_group.add_argument('--log-file',
                    default=None,
                    metavar='<path>',
                    help='The logging file. If not specified, logs to standard output.')

if __name__ == "__main__":
    # Get the final, consolidated configuration
    configuration = get_configuration()

    # --- Setup Logging ---
    if configuration.get("log_file"):
        filepath = normalizeFilePath(configuration["log_file"], is_exist=False)
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO, filename=filepath)
    else:
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)

    # --- Added Torrents file path ---
    added_torrents_filepath = normalizeFilePath(configuration.get("added_torrents_file"), is_exist=False)

    # --- Clear Added Torrents file if requested ---
    if configuration.get("clear_added_torrents"):
        if os.path.exists(added_torrents_filepath):
            logging.info(f"Clearing added torrents list: {added_torrents_filepath}")
            os.remove(added_torrents_filepath)
        else:
            logging.info(f"Added torrents list missing: {added_torrents_filepath}")
        exit(0)

    # --- Load search patterns using the dedicated function ---
    search_patterns_list = get_search_patterns()
    if len(search_patterns_list) > 0: 
        logging.info(f"Using search patterns: {search_patterns_list}")

    # --- Connecting to Transmission ---
    try:
        logging.info(f"Connecting to Transmission at {configuration['transmission_host']}:{configuration['transmission_port']}")
        tc = transmission_rpc.Client(
            host=configuration["transmission_host"],
            port=configuration["transmission_port"],
            username=configuration["transmission_user"],
            password=configuration["transmission_password"]
        )
    except transmission_rpc.error.TransmissionError as te:
        logging.error(f"Error connecting to Transmission: {str(te).strip()}")
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred while connecting to Transmission: {e}")
        exit(1)

    # --- Process Feeds ---
    if not configuration.get("feed_urls"):
        logging.error("Error: No feed URLs were found in the config file or command-line arguments.")
        exit(1)
        
    for feed_url in configuration["feed_urls"]:
        logging.info(f"Parsing feed: {feed_url}")
        parseFeed(feed_url)




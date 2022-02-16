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
import hashlib

# files path check/construction
def checkFilePath(path):
    # check if path is absolute
    if os.path.isabs(path):
        filepath = path
    # construct absolute path
    else:
        filepath = os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), path)
    # check if file exist
    if not os.path.exists(filepath):
        logging.error("Error: given file not found:\'{0}\': ".format(path))
        exit(0)
    return filepath

# read the added items list from the file
def readItems(filepath):
	addeditems = []
	if os.path.exists(filepath):
		with open(filepath,'r') as f:
			for line in f:
				addeditems.append(line.rstrip('\n'))
	return addeditems

# Download torrent as file
def dlTorrent(url):
    # generate random name
    seed(1)
    name = str(random())[3:10]
    filepath = os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), name + '.torrent')

    # open temporary file
    with open(filepath,'wb') as f:
        # download content
        response = requests.get(url)
        f.write(response.content)
        return str("file://") + str(filepath), filepath

# add the link to transmission and appends the link to the added items
def addItem(item):
    # decide if we download a torent or just pass a url
    if configuration["download-with-python"]:
        url, filepath = dlTorrent(item.link)
    else:
        url = item.link
        filepath = None

    if configuration["download-dir"] is not None:
        logging.info("Adding Torrent: " + item.title + " (" + item.link + ") to " + configuration["download-dir"])
        tc.add_torrent(url, download_dir = configuration["download-dir"], paused = configuration["add-paused"])
    else:
        logging.info("Adding Torrent: " + item.title + " (" + item.link + ") to default directory")
        tc.add_torrent(url, paused = configuration["add-paused"])
    with open(added_items_filepath, 'a') as f:
        f.write(item.link + '\n')

    # remove temporary torrent file
    if filepath is not None:
        os.remove(filepath)

# search for patterns by selected args
def searchPattern(title, searchitems):
	# search in list of patterns
    if configuration["search-patterns-file"] is not None:

        for pattern in searchitems:
            if re.search(pattern, title):
                return True
        return False

	# search for pattern received trough argument
    elif args.search_pattern is not None and re.search(args.search_pattern, title):
        return True

	# if none of above methods selected accept all
    elif args.search_pattern == None:
        return True
	# if pattern not match
    return False

# parses and adds torrents from feed
def parseFeed(feed_url):
    feed = feedparser.parse(feed_url)
    if feed.bozo and feed.bozo_exception:
        logging.error("Error reading feed \'{0}\': ".format(feed_url) + str(feed.bozo_exception).strip())
        return

    addeditems = readItems(added_items_filepath)

    # load pattern list to memory if present
    if configuration["search-patterns-file"] is not None:
        path =configuration["search-patterns-file"]

        # check if given string contain relative or absolute path
        if os.path.isabs(path):
            searchitems = path
        # if not, construct full path
        else:
            filepath = os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), configuration["search-patterns-file"])
            searchitems = readItems(filepath)
    else:
    	searchitems = None

    for item in feed.entries:
        if searchPattern(item.title, searchitems):
            if item.link not in addeditems:
                try:
                    addItem(item)
                except transmission_rpc.error.TransmissionError as e:
                    logging.error("Error adding item \'{0}\': {1}".format(item.link, e.message))
                #except transmission_rpc.HTTPHandlerError as e:
                #    logging.error("Error adding item \'{0}\': [{1}] {2}".format(item.link, e.code, e.message))
                except:
                    logging.error("Error adding item \'{0}\': {1}".format(item.link, str(sys.exc_info()[0]).strip()))

# argparse configuration and argument definitions
parser = argparse.ArgumentParser(description='Reads RSS/Atom Feeds and add torrents to Transmission')
parser.add_argument('--config-file',
					default=None,
					metavar='<configfile path>',
					help='The config json file path, if not specified or partialy set, args are used.')
parser.add_argument('--transmission-host',
					metavar='<host>',
					default='localhost',
					help='Host for Transmission RPC (default: %(default)s)')
parser.add_argument('--transmission-port',
					default='9091',
					metavar='<port>',
					help='Port for Transmission RPC (default: %(default)s)')
parser.add_argument('--transmission-user',
					default=None,
					metavar='<user>',
					help='Port for Transmission RPC (default: %(default)s)')
parser.add_argument('--transmission-password',
					default=None,
					metavar='<password>',
					help='Port for Transmission RPC (default: %(default)s)')
parser.add_argument('--add-paused',
					action='store_true',
					help='Disables starting torrents after adding them')
parser.add_argument('--log-file',
					default=None,
					metavar='<logfile path>',
					help='The logging file, if not specified, prints to output')
parser.add_argument('--clear-added-items',
					action='store_true',
					help='Clears the list of added torrents. You can also do that by deleting the addeditems.txt')
parser.add_argument('--download-dir',
					default=None,
					metavar='<dir>',
					help='The directory where the downloaded contents will be saved in. Optional.')
parser.add_argument('--search-pattern',
					default=None,
					metavar='<pattern>',
					help='The search pattern to filter the feed. Used with re.search() python function. Optional.')
parser.add_argument('--search-patterns-file',
					default=None,
					metavar='<patternsfile path>',
					help='Use search patterns stored in txt file. Used with re.search() python function. Optional.')
parser.add_argument('--download-with-python',
					action='store_true',
					help='If specified the torrent file will be downloaded with Python\'s request module, and not by Transmission. ')
parser.add_argument('--feed-urls', default=None, metavar='<url>', type=str, nargs='+',
				   help='Feed Url(s)')
# parse the arguments
args = parser.parse_args()

# dictionary with default settings
configuration = {"transmission-host" : "", "transmission-port" : "", "transmission-user" : "",
	 "transmission-password" : "", "log-file" : "", "add-paused" : False, "download-dir" : "",
	 "download-with-python" : False, "search-patterns-file" : "", "feed-urls" : [""]}

# get settings from args
for item in configuration:
	configuration[item] = getattr(args, item.replace("-","_"))

# read config file if present
if args.config_file is not None:
    filepath = checkFilePath(args.config_file)

    with open(filepath) as config_file:
        config = json.load(config_file)

        # loop trough items in config
        for item in config:
            # check if value is not empty
            if config[item] != "":
                # handle all types of imput json variables
                if type(config[item]) == list and config[item][0] != "":
                    configuration[item] = config[item]
                if type(config[item]) == bool and config[item] is not None:
                    configuration[item] = config[item]
                if type(config[item]) == str and config[item] != "":
                    configuration[item] = config[item]

        # generate name of additems.txt pased on config name/path
        hash_object = hashlib.sha256(str(args.config_file).encode("utf8"))
        hex_dig = hash_object.hexdigest()
        addeditems_file = "addeditems-" + hex_dig[:8] + ".txt"
else:
	addeditems_file = "addeditems.txt"

# path to the added items list file
added_items_filepath = os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), addeditems_file)

# check if at least one feed url was given
if configuration["feed-urls"][0] == "":
    logging.error("Error: no feed url set")
    exit(0)

if __name__ == "__main__":
	if configuration["log-file"] is not None:
		filepath = checkFilePath(configuration["log_file"])
		logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',level=logging.DEBUG, filename=filepath)
	else:
		logging.basicConfig(format='%(asctime)s: %(message)s',level=logging.DEBUG)


	# clears the added items file if asked for
	if args.clear_added_items:
		os.remove(added_items_filepath)

	# Connecting to Tranmission
	try:
		tc = transmission_rpc.Client(host=configuration["transmission-host"], port=configuration["transmission-port"], username=configuration["transmission-user"], password=configuration["transmission-password"])
	except transmission_rpc.error.TransmissionError as te:
		logging.error("Error connecting to Transmission: " + str(te).strip())
		exit(0)
	except:
		logging.error("Error connecting to Transmission: " + str(sys.exc_info()[0]).strip())
		exit(0)

	# read the feed urls from config
	for feed_url in configuration["feed-urls"]:
		parseFeed(feed_url)


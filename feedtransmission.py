#!/usr/bin/python

import sys, os
import feedparser
import transmissionrpc
import argparse
import logging
import re

# path to the added items list file
added_items_filepath = os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), 'addeditems.txt')

# read the added items list from the file
def readAddedItems():
	addeditems = []
	if os.path.exists(added_items_filepath):
		with open(added_items_filepath,'r') as f:
			for line in f:
				addeditems.append(line.rstrip('\n'))
	return addeditems

# add the link to transmission and appends the link to the added items
def addItem(item):
	if args.download_dir:
		logging.info("Adding Torrent: " + item.title + " (" + item.link + ") to " + args.download_dir)
		tc.add_torrent(item.link, download_dir = args.download_dir, paused = args.add_paused)
	else:
		logging.info("Adding Torrent: " + item.title + " (" + item.link + ") to default directory")
		tc.add_torrent(item.link, paused = args.add_paused)
	with open(added_items_filepath, 'a') as f:
		f.write(item.link + '\n')

# parses and adds torrents from feed
def parseFeed(feed_url):
	feed = feedparser.parse(feed_url)
	if feed.bozo and feed.bozo_exception:
		logging.error("Error reading feed \'{0}\': ".format(feed_url) + str(feed.bozo_exception).strip())
		return

	addeditems = readAddedItems()

	for item in feed.entries:
		if args.search_pattern == None or re.search( args.search_pattern, item.title ):
			if item.link not in addeditems:
				try:
					addItem(item)
				except transmissionrpc.TransmissionError as e:
					logging.error("Error adding item \'{0}\': {1}".format(item.link, e.message))
				except transmissionrpc.HTTPHandlerError as e:
					logging.error("Error adding item \'{0}\': [{1}] {2}".format(item.link, e.code, e.message))
				except:
					logging.error("Error adding item \'{0}\': {1}".format(item.link, str(sys.exc_info()[0]).strip()))

# argparse configuration and argument definitions
parser = argparse.ArgumentParser(description='Reads RSS/Atom Feeds and add torrents to Transmission')
parser.add_argument('feed_urls', metavar='<url>', type=str, nargs='+',
				   help='Feed Url(s)')
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

# parse the arguments
args = parser.parse_args()

if __name__ == "__main__":
	if args.log_file:
		logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',level=logging.DEBUG, filename=args.log_file)
	else:
		logging.basicConfig(format='%(asctime)s: %(message)s',level=logging.DEBUG)


	# clears the added items file if asked for
	if args.clear_added_items:
		os.remove(added_items_filepath)

	# Connecting to Tranmission
	try:
		tc = transmissionrpc.Client(args.transmission_host, port=args.transmission_port, user=args.transmission_user, password=args.transmission_password)
	except transmissionrpc.error.TransmissionError as te:
		logging.error("Error connecting to Transmission: " + str(te).strip())
		exit(0)
	except:
		logging.error("Error connecting to Transmission: " + str(sys.exc_info()[0]).strip())
		exit(0)

	# read the feed urls from config
	for feed_url in args.feed_urls:
		parseFeed(feed_url)

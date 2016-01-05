# feedtransmission
feedtransmission is a python script to read RSS/Atom feeds of torrents and add them to Transmission to download

## Install

You will need two Python packages:
* transmissionrpc (http://pythonhosted.org/transmissionrpc/)
* feedparser (https://pythonhosted.org/feedparser/)

In Linux you can install these by
```
pip install transmissionrpc
pip install feedparser
```
or
```
easy_install transmissionrpc
easy_install feedparser
```

You will need to run Transmission and enable remote access.

## Usage

```
feedtransmission.py http://url.to/torrent/feed.xml http://another.url/to/feed
```

Most probably you want to add feedtransmission to your cron file to regularly monitor a feed.

List of parameters available:
```
  --transmission-host <host>
                        Host for Transmission RPC (default: localhost)
  --transmission-port <port>
                        Port for Transmission RPC (default: 9091)
  --transmission-user <user>
                        Port for Transmission RPC (default: None)
  --transmission-password <password>
                        Port for Transmission RPC (default: None)
  --log-file <logfile path>
                        The logging file, if not specified, prints to output
  --clear-added-items   Clears the list of added torrents. You can also do
                        that by deleting the addeditems.txt
```


The script makes a file called `addeditems.txt` in the folder of the executable. This file stores the torrent links already added to Transmission.
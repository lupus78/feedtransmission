# feedtransmission
feedtransmission is a python script to read RSS/Atom feeds of torrents and add them to Transmission to download

## Install

Install necessary Python modules with:
```
pip install -r requirements.txt 
```

You will need to run Transmission and enable remote access.

## Usage

```
feedtransmission.py http://url.to/torrent/feed.xml http://another.url/to/feed
```

Most probably you want to add feedtransmission to your cron file to regularly monitor a feed.

List of arguments available:
```
  --transmission-host <host>
                        Host for Transmission RPC (default: localhost)
  --transmission-port <port>
                        Port for Transmission RPC (default: 9091)
  --transmission-user <user>
                        Port for Transmission RPC (default: None)
  --transmission-password <password>
                        Port for Transmission RPC (default: None)
  --add-paused          Disables starting torrents after adding them
  --log-file <logfile path>
                        The logging file, if not specified, prints to output
  --clear-added-items   Clears the list of added torrents. You can also do
                        that by deleting the addeditems.txt
  --download-dir <dir>  The directory where the downloaded contents will be
                        saved in. Optional.
  --search-pattern <pattern>
                        The search pattern to filter the feed. Used with 
                        re.search() python function. Optional.
  --search-patterns-file
                        Use search patterns stored in txt file. Used 
                        with re.search() python function. Optional.
  --download-with-python
                        If specified the torrent file will be downloaded with
                        Python's request module, and not by Transmission.

```


The script makes a file called `addeditems.txt` in the folder of the executable. This file stores the torrent links already added to Transmission.

Transmission can fail to download the torrents with urllib2.HTTPError error. If that is the case, use the --download-with-python argument.

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
feedtransmission.py --feed-urls http://url.to/torrent/feed.xml http://another.url/to/feed
```

Most probably you want to add feedtransmission to your cron file to regularly monitor a feed.

List of arguments available:
```
Required Settings:
  Either a config file or feed URLs must be provided.

  --config-file <path>  Path to the config JSON file. (default: None)
  --feed-urls <url> [<url> ...]
                        One or more space-separated Feed URL(s). (default: None)

Transmission Settings:
  --transmission-host <host>
                        Host for Transmission RPC. (default: localhost)
  --transmission-port <port>
                        Port for Transmission RPC. (default: 9091)
  --transmission-user <user>
                        Username for Transmission RPC. (default: None)
  --transmission-password <password>
                        Password for Transmission RPC. (default: None)

Torrent Settings:
  --add-paused          Disables starting torrents after adding them. (default: False)
  --download-dir <dir>  The directory where the downloaded contents will be saved. (default: None)
  --download_with_python
                        If specified, the torrent file is downloaded by this script, not by Transmission. (default: False)

Filtering Settings:
  --search-pattern <pattern>
                        A single regex pattern to filter the feed. Cannot be used with --search-patterns-file. (default: None)
  --search-patterns-file <path>
                        Path to a text file with search patterns. Cannot be used with --search-pattern. (default: None)

Other Settings:
  --added-torrents-file <path>
                        Path to a text file which will be used to track which torrents are already added. (default:
                        added_torrents.txt)
  --clear-added-torrents
                        Deletes the added torrents file and quits. (default: False)
  --log-file <path>     The logging file. If not specified, logs to standard output. (default: None)

```


The script makes a file to store all the torrents added to Transmission, the file can be specified with the  `--added-torrents-file` argument. 

Transmission can fail to download the torrents with urllib2.HTTPError error. If that is the case, use the `--download-with-python` argument.

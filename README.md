zerospider
==========

Small parallel web crawler done in Python and ZeroMQ

See: example.py

Requirements:

- zeromq
- requests
- werkzeug
- lxml

Simply call the `fetch` function and provide:

- `domain`: the base domain to be crawled. Any URL outside this one will be skipped.
- `seed`: sequence of seed paths to start with.
- `save_rules`: list of rules that a URL needs to fit in order to be saved. (See `Werkzeug routing reference <http://werkzeug.pocoo.org/docs/routing/#rule-format>`_)
- `processor`: user defined function that will process the data passed from URLs for saving. Receives arguments `html`, `url` and all the mathed parameters from the `save_rules` as a keyword arguments.
- `crawlers`: number of crawlers, 4 by default
- `status_path`: path to file used for saving the status, None by default. If provided will occasionally save the status of crawling and will proceed at that point if restarted.

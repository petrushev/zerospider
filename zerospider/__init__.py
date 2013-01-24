import json
import zlib
from time import sleep
from sys import stderr
from multiprocessing import Process

import zmq
import requests as rq
from requests.exceptions import ConnectionError
from lxml.html import fromstring
from werkzeug.routing import Rule, Map
from werkzeug.urls import url_unquote
from werkzeug.exceptions import NotFound

def saver(processor):
    ctx = zmq.Context()
    puller = ctx.socket(zmq.PULL)
    puller.bind('tcp://*:5051')

    while True:
        data = puller.recv()
        html, path, kwargs = json.loads(zlib.decompress(data))
        try:
            processor(html, path, **kwargs)
        except Exception, exc:
            stderr.write('saving error: %s at: %s\n' % (exc, path))

def save_status(history, front, path):
    with open(path, 'w') as f:
        f.write(json.dumps([list(history), list(front)]))

def load_status(path):
    try:
        with open(path, 'r') as f:
            history, front = json.loads(f.read())
    except (IOError, ValueError):
        return set(), set()

    return set(history), set(front)

def worker(domain, save_rules):
    ctx = zmq.Context()
    worker_ = ctx.socket(zmq.REQ)
    worker_.connect('tcp://localhost:5050')
    saver = ctx.socket(zmq.PUSH)
    saver.connect('tcp://localhost:5051')
    urlsink = ctx.socket(zmq.PUSH)
    urlsink.connect('tcp://localhost:5052')

    matcher = Map(map(Rule, save_rules)).bind('', '/').match

    while True:
        worker_.send('')
        url = worker_.recv().decode('utf-8')

        try:
            q = rq.get(u'http://%s%s' % (domain, url_unquote(url)),
                       allow_redirects = False)
        except ConnectionError:
            continue

        if q.status_code == 301 or q.status_code == 302:
            redirect = q.headers['location']
            if domain in redirect:
                # only sent to front
                urlsink.send(redirect.split(domain)[1].encode('utf-8'))
            continue

        html = q.content
        try: _, data = matcher(url)
        except NotFound: pass
        else:
            # needs to be saved, sends html, url, data to saver
            data = zlib.compress(json.dumps([html, url, data]))
            saver.send(data)
            del data

        fetched = set()

        for link in fromstring(html).cssselect("a[href]"):
            link = link.attrib['href'].split('#')[0]
            if link.startswith('file://'): continue

            if not link.startswith('http'):
                fetched.add(link)
            elif domain in link:
                fetched.add(link.split(domain)[1])

        for l in fetched:
            urlsink.send(l.encode('utf-8'))

def fetch(domain, seed, save_rules, processor,
          crawlers = 4, status_path = None):
    ctx = zmq.Context()
    dealer = ctx.socket(zmq.REP)
    dealer.bind("tcp://*:5050")
    urlsink = ctx.socket(zmq.PULL)
    urlsink.bind("tcp://*:5052")

    # start saver and crawlers
    Process(target = saver, args = (processor,)).start()
    sleep(2)
    for _ in range(crawlers):
        Process(target = worker, args = (domain, save_rules)).start()

    # set up front and history
    if status_path is None:
        history, front = set(), set()
    else:
        history, front = load_status(status_path)
    front.update(seed)

    # main loop
    while True:
        if len(front) == 0: # update front
            poll_timeout = 30000
            while True: # poll urlsing for new urls
                polled = urlsink.poll(timeout = poll_timeout)
                if polled == 0:
                    break # no urls

                poll_timeout = 200 # cut polling time for next fetch
                url = urlsink.recv().decode('utf-8')
                if url not in history:
                    front.add(url)

            if status_path: # checkpoint: update status
                save_status(history, front, status_path)

        else:
            # next url to crawl
            url = front.pop()
            history.add(url)

            # next available crawler
            _ = dealer.recv()
            dealer.send(url.encode('utf-8'))

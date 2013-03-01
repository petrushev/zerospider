from zerospider import fetch
from lxml.html import fromstring
import requests

def save_to_disk(html, url, comic_id):
    doc = fromstring(html.encode('utf-8'))
    img_src = doc.cssselect('div#comic img[src]')[0].attrib['src']
    img_content = requests.get(img_src).content
    fname = 'xkcd/%d.jpg' % (comic_id)
    with open(fname, 'wb') as f:
        f.write(img_content)

fetch(domain = 'www.xkcd.com',
      seed = ('/',),
      save_rules = ['/<int:comic_id>/'], # http://xkcd.com/513
      processor = save_to_disk,
      crawlers = 10,
      status_path = 'xkcd/status')

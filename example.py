from zerospider import fetch

def save_to_disk(html, url, title):
    fname = title.replace('-', ' ')
    with open(fname, 'w') as f:
        f.write(html.encode('utf-8'))

fetch(domain = 'bpetrushev.appspot.com',
      seed = ('/t',),
      save_rules = ['/t/<string:title>'],
      processor = save_to_disk,
      status_path = 'bpetrushev.status')

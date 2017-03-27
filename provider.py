import feedparser
import os
import urllib.request
from pyquery import PyQuery
import requests
from urllib.parse import urlparse, parse_qs
import re
import oauth2client
import httplib2
from apiclient import discovery

"for command line use"
_storage_directory = "~/.pystatsmpg/"
_client_secret_file_ = 'mtb.json'


def get_feeds():
    f = feedparser.parse('http://statsl1mpg.over-blog.com/rss')
    recaps = []
    for e in f.entries:
        pub = _get_days(e.title)
        if pub is None:
            continue
        pub['entry'] = e
        recaps.append(pub)
    if len(recaps) == 0:
        print("sorry could not find no Tableau Recap at all!!")
        return
    return recaps


def parsefeed():
    """ read the feed """
    recaps = get_feeds()
    latest_l1 = _get_latest(recaps, 'l1')
    latest_pl = _get_latest(recaps, 'pl')
    _download(latest_l1)
    _download(latest_pl)


def _get_hrefs(pub):
    "get the document link for a publication"
    entry = pub['entry']
    p = PyQuery(url=entry.link)
    section = p('.ob-sections')
    li = section('li')
    return [PyQuery(i)('a').attr('href') for i in li]


def _is_l1(name):
    regex = r'.*(Lequipe|MPG)\.xlsx'
    return re.match(regex, name) is not None
    

def _download(latest):
    for href in _get_hrefs(latest):
        c, fname = _content_(href)
        if _is_l1(fname):
            day = latest['l1']
        else:
            day = latest['pl']
        fname = "J{}_{}".format(day, fname)
        _write_file(c, fname)


def _write_file(content, name):
    "name is the downloaded name file"
    filename = _get_storage_path() + name
    with  open(filename, 'wb+') as f:
        f.write(content)
    
            
def _content_(url):
    fileid = _drive_file_id(url)
    service, http = _service_()
    print('url:' + url)
    print('fileid:' + str(fileid))
    file = service.files().get(fileId=fileid).execute()
    filename = file['name']
    url = service.files().get_media(fileId=fileid).uri
    response, content = http.request(url)
    return content, filename

            
def _drive_file_id(url):
    "url redirect to drive: we need to extract the file id"
    r = requests.get(url)
    drive_url = [h.headers['Location'] for h in r.history][0]
    qs = urlparse(drive_url).query
    return parse_qs(qs)['id'][0]

    
def _service_():
    #credits: https://developers.google.com/api-client-library/python/auth/service-accounts
    from oauth2client.service_account import ServiceAccountCredentials
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(_client_secret_file_, scopes)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    return service, http
    
    
def _get_latest(entries, league):
    return sorted([p for p in entries if p[league] is not None], key = lambda x: x[league], reverse=True)[0]

    
def _is_stats(title):
    return re.match(r'.*tableaux?\ recap.*', title, re.I) is not None


def _get_days(title):
    m = re.match(r'.*J([0-9]{2}).*', title)
    if m is None or not _is_stats(title):
        return None
    days = [int(g) for g in m.groups()]
    pl =  _get_premier_league_day(title)
    l1 = None
    if pl is None:
        return {'l1':days[0], 'pl': pl}
    if len(days) > 1:
        if pl == days[0]:
            l1 = days[1]
        else:
            l1 = days[0]
    return {'pl':pl, 'l1':l1}


def _get_premier_league_day(title):
    regex = r'.*Premier[^0-9]*([0-9]{2}).*'
    #    m = re.match(r'.*Premier\ Leagu', title)
    m = re.match(regex, title)
    if m is not None:
        return int(m.group(1))
    return None


def _get_storage_path():
    return os.path.expanduser(_storage_directory)


def _get_files_from_storage():
    "todo check that"
    days = []
    for f in os.listdir(_get_storage_path()):
        if f[:-4] != 'xslx':
            continue
        try:
            day = int(f[1:3])
        except ValueError:
            continue
        days.append((day, f))


def _get_days_from_storage(league):
    "TODO I was here"
    days = []
    for d, f in _get_files_from_storage():
        if _is_l1(f) and league == 'l1':
            days.append(day)
    return days


def _get_latested_in_store():
    "TODO I was here"
    last = {'l1':None, 'pl': None}
    l1_days = []
    for f in os.listdir(_get_storage_path()):
        if f[:-4] != 'xslx':
            continue
        try:
            day = int(f[1:3])
        except ValueError:
            continue
        if _is_l1(f):
            l1_days.append(day)
        else:
            pl_days.append(day)

    
"""
 . finish syncing local storage with the rss
 . implement the worker, with 'clever work load
 . use within pomco
"""

if __name__ == "__main__":
    _storage_path = _get_storage_path()
    if not os.path.isdir(_storage_path):
        os.makedirs(_storage_path)
    get_latested_in_store()
    parsefeed()

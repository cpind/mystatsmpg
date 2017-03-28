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
from enum import Enum

"for command line use"
_storage_directory = "~/.pystatsmpg/"
_client_secret_file_ = 'mtb.json'



class League(Enum):
    L1 = 1
    PL = 2


class Notation(Enum):
    MPG = 1
    LEQUIPE = 2
    
class StatsMPG():

    def __init__(self, day, feedlink, bitly, driveid, content, filename):
        self.day = day
        self.feedlink = feedlink
        self.bitly = bitly
        self.driveid = driveid
        #xlsx file content
        self.content = content
        self.filename = filename

    def get_leaguename(self):
        if _is_l1(self.filename):
            return 'l1'
        return 'pl'

    def get_season(self):
        return _get_season(self.filename)


    def get_notation(self):
        leaguename = self.get_leaguename()
        if leaguename == 'pl' or leaguename is not _is_lequipe(self.filename):
            return "MPG"
        return "Lequipe"


def getstats(greaterthan={}):
    """
    retrives the latest StatsMPG whose days are greater than days specified in greaterthan argument.
    greaterthan argument is provided as follow {'l1':30, 'pl':29}
    """
    feeds = get_feeds(greaterthan=greaterthan)
    stats = []
    for f in feeds:
        stats += _get_stats(f)
    return [stat for stat in stats if _is_greater_than(stat, greaterthan)]


def _is_stat_greater_than(stat, than):
    pub = {stat.leaguename:stat.day}
    return _is_greater_than(pub, than)


def _is_greater_than(feed, than):
    for league in than:
        if than[league] is None:
            continue
        if feed[league] is None:
            continue
        if feed[league] > than[league]:
            return True
        else:
            return False
    return True

def _filterfeeds(feeds, greaterthan={}):
    return [f for f in feeds if _is_greater_than(f, greaterthan)]


        
def get_feeds(greaterthan=None, latest=True, rss = None):
    if rss is None:
        rss = 'http://statsl1mpg.over-blog.com/rss'
    f = feedparser.parse(rss)
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
    if greaterthan is not None:
        recaps = _filterfeeds(recaps, greaterthan)
    if latest:
        recaps = [] + _get_latest(recaps, 'l1') + _get_latest(recaps, 'pl')
    return recaps


def parsefeed(feeds=None):
    if feeds is None:
        feeds = get_feeds()
    """ read the feed """
    recaps = feeds
    _download(feeds[0])
    _download(feeds[1])


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
    

def _is_lequipe(name):
    regex = r'.*Lequipe\.xlsx'
    return re.match(regex,name) is not None


def _get_league(filename):
    if _is_l1(filename):
        return League.L1
    return League.PL


def _get_day(publication, filename):
    if _is_l1(filename):
        return publication['l1']
    else:
        return publication['pl']


def _get_season(filename):
    m = re.match(r'.*saison([0-9]+).*', filename, re.I)
    if m is None:
        return None
    return int(m.group(1))


def _get_stats(publication):
    stats = []
    for href in _get_hrefs(publication):
        driveid = _drive_file_id(href)
        c, fname, driveid = _content(href)
        day = _get_day(publication, fname)
        season = _get_season(fname)
        stats.append(StatsMPG(
            day = _get_day(publication, fname),
            feedlink = publication['entry'].link,
            bitly = href,
            driveid = driveid,
            content = c,
            filename = fname,
        ))
    return stats
        

def _download(publication):
    stats = _get_stats(publication)
    for stat in stats:
        c = stat.content
        fname = stat.filename
        day = _get_day(publication, fname)
        _write_file(c, "J{}_{}".format(day, fname))


def _write_file(content, name):
    "name is the downloaded name file"
    filename = _get_storage_path() + name
    with  open(filename, 'wb+') as f:
        f.write(content)
    
            
def _content(url):
    fileid = _drive_file_id(url)
    service, http = _service_()
    file = service.files().get(fileId=fileid).execute()
    filename = file['name']
    url = service.files().get_media(fileId=fileid).uri
    response, content = http.request(url)
    return content, filename, fileid

            
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
    entries = [p for p in entries if p[league] is not None]
    s = sorted(entries, key = lambda x: x[league], reverse=True)
    if len(s) > 0:
        return [s[0]]
    return []

    
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

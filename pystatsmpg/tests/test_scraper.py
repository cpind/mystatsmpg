from unittest.mock import patch, MagicMock
import feedparser


from pystatsmpg import scraper
from pystatsmpg.tests.helper import _filepath


_rss_xml_file = _filepath("data/rss.xml")
_rss = ""
_hrefs = [{
    'link': 'http://statsl1mpg.over-blog.com/2017/03/tableaux-recap-j30.html?utm_source=flux&utm_medium=flux-rss&utm_campaign=sports',
    'hrefs': ['http://bit.ly/2nVIJbx', 'http://bit.ly/2nD6tVJ']
}, {
        'link': 'http://statsl1mpg.over-blog.com/2017/03/tableau-recap-premier-league-j29.html?utm_source=flux&utm_medium=flux-rss&utm_campaign=sports',
    'hrefs': ['http://bit.ly/2n3Hg3V']
}]

def test_get_feeds():
    entries = scraper.get_feeds()
    assert len(entries) == 2


def test_greater_than():
    assert_greater_than({'pl':None, 'l1':21},{'pl':24, 'l1':20}, True)
    assert_greater_than({'pl':29, 'l1':None},{'pl':29, 'l1':None}, False)
    assert_greater_than({'pl':29, 'l1':None},{'pl':28, 'l1':22}, True)
    assert_greater_than({'pl':29, 'l1':23}, {'pl':28, 'l1':24 }, True)
    assert_greater_than({'pl':28, 'l1':23}, {'pl':28, 'l1':24 }, False)


def test_get_greaterthan():
    entries = scraper.get_feeds(greaterthan={'pl':29})
    assert len(entries) == 1


def test_get_hrefs():
    class Entry():
        pass
    entry = Entry()
    entry.link = _hrefs[0]['link']
    hrefs = scraper._get_hrefs({'entry':entry})
    assert hrefs == _hrefs[0]['hrefs']
    

def _get_stats():
    f = scraper.get_feeds()
    stats = scraper._get_stats(f[0])
    return stats

    
def test__get_stats_should_return_3_stats():
    stats = _get_stats()
    assert type(stats) is list
    assert len(stats) == 2
    assert type(stats[0]) is scraper.StatsMPG


def test__get_stats_greaterthan():
    stats = scraper.getstats(greaterthan={'l1':28})
    

def test__stats_notation():
    stats = _get_stats()
    assert stats[0].get_season() == 4
    assert stats[0].get_leaguename() == "l1"
    assert stats[0].get_notation() == "MPG"
    assert stats[1].get_notation() == "Lequipe"
    
    
def test_getstats_should_return_3_stats():
    stats =  scraper.getstats()
    assert len(stats) == 3
    assert type(stats[0]) is scraper.StatsMPG


    
#asserts
def assert_greater_than(feed, than, result):
    assert scraper._is_greater_than(feed, than) == result
    

def get_hrefs(publication):
    link = publication['entry'].link
    for href in _hrefs:
        if href['link'] == link:
            return href['hrefs']
    return []


def get_content(url):
    drivenames = {
        'http://bit.ly/2nVIJbx': 'Stats MPG-saison4MPG.xlsx',
        'http://bit.ly/2nD6tVJ': 'Stats MPG-saison4Lequipe.xlsx',
        'http://bit.ly/2n3Hg3V': 'Stats MPG-saison1PL.xlsx'}
    return None, drivenames.get(url, ""), None



#setup
#@patch('feedparser.parse', return_value=feedparser.parse(_rss_xml_file))
#@patch('feedparser.parse', return_value="yep")
def setup_module(parsemock):#, get_contentmock):
    global _rss
    with open(_rss_xml_file, 'r') as f:
        _rss = f.read()
    #could not have @patch to actually patch _get_hrefs
    scraper._get_hrefs = get_hrefs
    scraper._content = get_content
    feedparser.parse = MagicMock(return_value=feedparser.parse(_rss_xml_file))

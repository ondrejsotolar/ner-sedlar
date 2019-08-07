#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module provides access to the Freebase database of places and entities.
"""

import shelve
import json
import urllib
from os import path

CACHE_FILE = path.dirname(path.realpath(__file__)) + '/cache/freebase.cache'
SERVICE_URL = 'https://www.googleapis.com/freebase/v1/search'


class Freebase(object):
    """
    Simple interface to Freebase. The is a file backed cache so that the same
    query is not executed again and again.
    """
    def __init__(self):
        self.cache = shelve.open(CACHE_FILE)
        self.params = {'limit': 5, 'spell': 'always', 'lang': 'cs,en'}

    def lookup(self, query):
        """
        Look up a query in Freebase. The query should be a unicode string.
        """
        key = query.encode('utf8')
        if key not in self.cache:
            self.cache[key] = self.fetch(key)
        return self.cache[key]

    def fetch(self, query):
        """
        Do the actual communication with remote API. Query here should be
        already encoded to UTF-8. Returns a triple, first item is the name
        recognized by Freebase, second is a most likely category, the last is
        the score. First two items in returned value are unicode, last item is
        a float.
        """
        self.params['query'] = query
        url = SERVICE_URL + '?' + urllib.urlencode(self.params)
        response = json.loads(urllib.urlopen(url).read())
        for result in response['result'][0:2]:
            if 'notable' in result:
                name = result['name']
                category = result['notable']['name']
                return (name, category, result['score'])
        return None

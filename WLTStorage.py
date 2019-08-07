#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module exports the WLTStorage class. When the file is run as separate
executable, it tests the class on a data file by trying to retrieve some
values.
"""


import argparse
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) +
                '/lib/trie/lib/python2.7/site-packages/')
import libtrie


class WLTStorage(object):
    """
    WLTStorage is a mapping storage that stores a lemma and a tag for words.
    """

    def __init__(self, datafile, delimiter=':'):
        """
        Create new Word-Lemma-Tag storage backed by a `datafile`.
        """
        self.trie = libtrie.Trie(datafile)
        self.logger = logging.getLogger('WLTStorage')
        self.cache = {}
        self.delimiter = delimiter

    def set_log_level(self, level):
        """Set log level for this object."""
        self.logger.setLevel(level)

    def __contains__(self, word):
        """
        Check whether word exists in the storage.
        """
        try:
            self.__getitem__(word)
            return True
        except KeyError:
            return False

    def __getitem__(self, word):
        if word in self.cache:
            return self.cache[word]

        res = self.trie.lookup(word)
        if not res:
            raise KeyError
        self.cache[word] = set(tuple(x.split(self.delimiter)) for x in res)
        return self.cache[word]


def test_main():
    """
    This function creates a storage backed by a file and tests it by retrieving
    a couple of records.
    """
    parser = argparse.ArgumentParser(description='Test WLT Storage')
    parser.add_argument('-v', '--verbose',
                        help='print verbose output of what is happening',
                        action='store_true')
    args = parser.parse_args()
    logging.basicConfig()

    st = WLTStorage('./data/prijmeni-sorted.trie')

    if args.verbose:
        st.set_log_level(logging.DEBUG)

    misses = [u'ahoj', u'neexistující jméno']

    for tok in misses:
        print 'Test "%s":' % tok.encode('utf8'),
        print "Failed: found" if tok in st else "OK"

    hits = [(u'Sedlářovi', 2), (u'Novák', 7), (u'Halyshychovou', 2),
            (u'Mišanović', 6), (u'Žůčku', 2), (u'Aabymu', 1), (u'Tipu', 19),
            (u'Taranu', 19), (u'Robu', 19), (u'Radu', 19), (u'Otu', 19),
            (u'Christu', 19), (u'Borgu', 19), (u'Voicu', 17), (u'Stoicu', 17),
            (u'Sandu', 17), (u'Pashku', 17), (u'Odu', 17), (u'Niku', 17),
            (u'Lungu', 17), (u'Leu', 17), (u'Chou', 18), (u'Heidu', 17),
            (u'Buzu', 17), (u'Begu', 17), (u'Albu', 17), (u'Vladu', 16),
            (u'Šamu', 16), (u'Sahu', 19), (u'Locku', 16), (u'Soimu', 15),
            (u'Shehu', 15), (u'Saiu', 15), (u'Rabacu', 15)]

    for (tok, num) in hits:
        print 'Test "%s":' % tok.encode('utf8'),
        if not tok in st:
            print 'Failed: not found'
        elif len(st[tok]) != num:
            print "Failed: found %d tags, (should be %d)" % (len(st[tok]), num)
        else:
            print "OK"

if __name__ == '__main__':
    test_main()

#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Main access point to the detectors.
"""

import detectors.name
import detectors.abbr
import detectors.address
import detectors.law
import detectors.pattern
import detectors.phrase
import detectors.language
import detectors.organisation as org
import os
import sys

BASEPATH = os.path.dirname(os.path.realpath(__file__)) + '/../data/'
FIRST_NAMES_FILE = BASEPATH + 'jmena.trie'
LAST_NAMES_FILE = BASEPATH + 'prijmeni-sorted.trie'
NAME_DATA = BASEPATH + 'titles.yaml'
IGNORE_FILE = BASEPATH + 'ignored_abbr.txt'
WIKI_LIST = BASEPATH + 'phrase_list.trie'
CATEGORY_LIST = BASEPATH + 'phrase_categories.trie'
WIKI_TUPLE_LIST = BASEPATH + 'phrase_lemmas.trie'
PATTERNS_FILE = BASEPATH + 'patterns.yaml'
NUMERICS_FILE = BASEPATH + 'numerics.yaml'
STREET_FILE = BASEPATH + 'seznam_ulic.trie'
TOWN_FILE = BASEPATH + 'osidleni.trie'
COUNTY_FILE = BASEPATH + 'staty.txt'
LAWS_FILE = BASEPATH + 'law_words.yaml'
LANG_WORDS_DIR = BASEPATH + 'lang-words'
ORG_FILE = BASEPATH + 'organisation-data.yaml'


#: For each key, store tuple with the class name followed by the arguments
#: that should be passed to the ``__init__`` method.
DETECTORS = {'name': (detectors.name.NameDetector,
                      FIRST_NAMES_FILE, LAST_NAMES_FILE, NAME_DATA),
             'abbr': (detectors.abbr.AbbrDetector, IGNORE_FILE),
             'laws': (detectors.law.LawDetector, LAWS_FILE),
             'pattern': (detectors.pattern.PatternDetector,
                         PATTERNS_FILE, NUMERICS_FILE),
             'phrase': (detectors.phrase.PhraseDetector,
                        WIKI_LIST, CATEGORY_LIST,
                        WIKI_TUPLE_LIST, TOWN_FILE),
             'address': (detectors.address.AddressDetector,
                         STREET_FILE, TOWN_FILE, COUNTY_FILE),
             'lang': (detectors.language.LanguageDetector, LANG_WORDS_DIR),
             'organisation': (org.OrganisationDetector, ORG_FILE)}


def create_all():
    """Get a list of all detectors."""
    return [DETECTORS[d][0](*DETECTORS[d][1:]) for d in DETECTORS.keys()]


def create_detector(det):
    """
    Get actual detector for given name or display error if no such detector
    exists.
    """
    if det in DETECTORS:
        args = DETECTORS[det]
        return args[0](*args[1:])
    else:
        sys.stderr.write('Unknown detector "%s"\n' % det)
        exit(1)


def list_detectors():
    """Get a list of all available detectors."""
    dets = sorted((name, create_detector(name).description)
                  for name in DETECTORS)
    dets.insert(0, ('all', 'All available detectors'))
    return dets

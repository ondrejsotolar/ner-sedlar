#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module exports a stream processor that leaves tokens be and adds a
category to named entities.
"""

import Freebase
import logging


class CategoryTagger(object):
    """Stream processor that adds categories to entities."""
    def __init__(self):
        self.logger = logging.getLogger('CategoryTagger')
        self.base = Freebase.Freebase()

    def set_log_level(self, log_level):
        """Set log level for the tagger."""
        self.logger.setLevel(log_level)

    def add_category(self, entity):
        """Try to add a category to the entity."""
        self.logger.debug('Tagging <%s>', entity.word)
        query = ''
        if entity.attrs['lemma']:
            query = entity.attrs['lemma']
        else:
            query = entity.word.replace('\n', ' ')

        self.logger.debug('Query: <%s>', query)

        result = self.base.lookup(query)
        if result and result[1]:
            if entity.attrs['lemma'] and result[0] != entity.attrs['lemma']:
                self.logger.debug('Lemma does not match')
                return
            entity.attrs['ner:category'] = result[1]
            entity.attrs['ner:base_form'] = result[0]
            entity.attrs['ner:category_score'] = result[2]

    def tag(self, inp):
        """Tag entities in input stream with categories, leave tokens be."""
        for t in inp:
            if t.taggable():
                self.add_category(t)
            yield t

#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module exports the base class for named entities. All other modules should
subclass this class.
"""

import StreamItem
import logging

INPUT_ENCODING = "utf-8"    # locale.getpreferredencoding()
OUTPUT_ENCODING = "utf-8"   # locale.getpreferredencoding()


class NamedEntity(StreamItem.StreamItem):
    """Object describing a NE"""

    def __init__(self, word, lemma, typ, tag):
        super(NamedEntity, self).__init__()
        self.attrs = {'typ': typ, 'tag': tag}
        self.word = word
        self.attrs['lemma'] = lemma.replace('_', ' ') if lemma else None
        self.should_tag = True
        self.weight = 1

    def set_position(self, position):
        """Set an offset in input stream of this entity."""
        self.position = position
        self.attrs['ner:position'] = position

    def __repr__(self):
        """Return the NE in format word:lemma:tag:type"""
        r = self.word
        if self.attrs['lemma']:
            r += ':' + self.attrs['lemma'].replace(' ', '_')
        if self.attrs['tag']:
            r += ':' + self.attrs['tag']
        if self.attrs['typ']:
            r += ':' + self.attrs['typ']
        return r.encode(OUTPUT_ENCODING)

    def to_markable(self):
        """Return the NE as markable"""
        self.attrs['mark_src'] = 'ner'
        attrs = ' '.join(['%s="%s"' % (k, v)
                          for (k, v) in sorted(self.attrs.iteritems()) if v])
        return "%s<markable %s>%s</markable>" % (self.whitespace or "",
                                                 attrs,
                                                 self.word.replace('_', ' '))

    def to_json(self):
        """Return the NE as JSON."""
        attrs = ['"%s": "%s"' % (k, v)
                 for (k, v) in self.attrs.iteritems() if v]
        attrs.insert(0, '"text": "%s"' % self.word.replace('_', ' '))
        res = ',\n'.join('    '+line for line in attrs)
        return '{\n' + res + '\n}'

    def set_src(self, src):
        """Set source of the entity."""
        self.attrs['src'] = src

    def to_html(self, escape):
        """Return HTML string."""
        cls = 'ne'
        if self.attrs['typ']:
            cls += ' ' + self.attrs['typ']
        attrs = ' '.join(['data-%s="%s"' % (k.replace(':', '-'), v)
                          for (k, v) in sorted(self.attrs.iteritems()) if v])
        before = escape(self.whitespace or '')
        return '%s<span class="%s" %s>%s</span>' % (before, cls, attrs,
                                                    escape(self.word or ''))


class Detector(object):
    """Base class for all detectors."""

    def __init__(self, description=''):
        self.description = description

    def set_log_level(self, level):
        """Set log level for this detector."""
        logging.getLogger(self.__class__.__name__).setLevel(level)

    def debug(self, *args):
        """Convinience method to access logger for debugging."""
        logging.getLogger(self.__class__.__name__).debug(*args)

    def warning(self, *args):
        """Convinience method to access logger for warnings."""
        logging.getLogger(self.__class__.__name__).warning(*args)

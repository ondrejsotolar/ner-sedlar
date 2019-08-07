#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Token is a piece of input with its preceding whitespace and a type.
"""

import StreamItem


class Token(StreamItem.StreamItem):
    """
    Class representing a single token.
    """

    SGML_TAG = 1
    CLITICS = 2
    WHITESPACE = 3
    URL = 4
    EMAIL = 5
    IP_ADDRESS = 6
    TIME = 7
    DATE = 8
    NUMBER = 9
    ACRONYM = 10
    WORD = 11
    ANY = 12
    ZIP_CODE = 13
    ISBN = 14
    PHONE_NUM = 15
    COORDINATES = 16
    RATIO = 17

    def __init__(self, word, whitespace, position=None, typ=None):
        """
        To create a Token, the actual word is needed with its preceding
        whitespace.
        """
        super(Token, self).__init__()
        self.word = word
        self.whitespace = whitespace
        self.position = position
        self.typ = typ

    def __str__(self):
        return u"%s%s" % (self.whitespace or "", self.word or "")

    def __repr__(self):
        typ_str = ',typ=%s' % self.typ if self.typ else ''
        return "Token(%r,%r,position=%r%s)" % (self.word, self.whitespace,
                                               self.position, typ_str)

    def to_html(self, escape):
        """Return HTML string."""
        return u'%s%s' % (self.whitespace or '', escape(self.word) or '')

    def to_markable(self):
        """Return string suitable for use in markable output."""
        return unicode(self)

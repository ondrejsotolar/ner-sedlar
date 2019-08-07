#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Law reference detection
"""

import detectors.base as ner
import re
from utils import run_helper, load_yaml

LIMIT = 30
NUM_RE = re.compile(ur'\d+')
DOT_NUM_RE = re.compile(ur'\.?(\d+)')
LETTER_RE = re.compile(ur'[a-z]', re.IGNORECASE)


class LawEntity(ner.NamedEntity):
    """Object describing a law NE."""
    def __init__(self):
        ner.NamedEntity.__init__(self, None, None, 'CLawNo', None)
        self.set_src('LawNoNer')
        self.should_tag = False

    def set_attr(self, attr, val):
        """Set an attribute of the entity."""
        self.attrs['law_' + attr] = val

    def is_complete(self):
        """Check whether basic attributes are set."""
        return self.attrs['law_number'] and self.attrs['law_collection']


def remove_leading_word(tokens, options):
    """If tokens start with any word from the set, remove it."""
    if tokens[0].word in options:
        del tokens[0]
        return True
    return False


class LawDetector(ner.Detector):
    """
    Law detector find references to laws.

    It is basically a rewritten regular expression that works on a stream of
    tokens. The regex follows in a comment.
    """
    #(?:(?:§|paragrafu)\ *(?P<par>\d+)\ *[.,]?\ +)?
    #(?:odst(?:\.|avce|avec)\ *(?P<sect>\d+)[.,]?\ +)?
    #(?:písm(?:\.|ena|eno)?\ *(?P<letter>[a-z])[.,)]?\ +)?
    #(?:(?:z[áa]k.?|z[áa]kona|vyhl\.?|vyhl(?:áš|as)ky|na(?:ri|ří)zen[íi])?\ *)?
    #(?:(?:[čc]\.|číslo)\ *)?
    #(?P<num>\d+)[/-](?P<coll>\d{2,4})\ +Sb\ *\.?

    def __init__(self, data_file):
        super(LawDetector, self).__init__('Detect references to laws')
        self.data = load_yaml(data_file)

    def try_para(self, tokens):
        """Try to extract a paragraph specification."""
        self.debug('finding paragraph number <%s>', tokens[0].word)
        if not tokens[0].word.lower() in self.data['para_word']:
            return None

        if NUM_RE.match(tokens[1].word):
            res = tokens[1].word
            self.debug('Found match for para <%s>', res)
            del tokens[0:2]
            remove_leading_word(tokens, self.data['trail_sep'])
            return res
        return None

    def try_sect(self, tokens):
        """Try to extract a section specification."""
        self.debug('finding section number <%s>', tokens[0].word)

        if tokens[0].word.lower() not in self.data['sect_word']:
            self.debug('No introductory word')
            return None
        idx = 1
        if tokens[idx].word == u'.':
            idx += 1

        m2 = DOT_NUM_RE.match(tokens[idx].word)
        if m2:
            self.debug('Found match for sect <%s>', m2.group(1))
            del tokens[0:idx+1]
            remove_leading_word(tokens, self.data['trail_sep'])
            return m2.group(1)
        return None

    def try_letter(self, tokens):
        """Try to extract letter part of law number."""
        self.debug('finding letter <%s>', tokens[0].word)
        lower = tokens[0].word.lower()

        if lower in self.data['letter_word']:
            idx = 1
        elif lower in self.data['letter_abbr'] and tokens[1].word == u'.':
            idx = 2
        else:
            return None

        m2 = LETTER_RE.match(tokens[idx].word)
        if m2:
            self.debug('Found match for letter <%s>', m2.group(0))
            del tokens[0:idx+1]
            remove_leading_word(tokens, self.data['trail_sep'])
            return m2.group(0)
        return None

    def try_dummy(self, tokens, bare, with_dot):
        """
        Try to verify that the stream starts with something that either matches
        `bare`, or matches `with_dot` and is followed by optional period.
        Return value indicates whether there was a match.
        """
        self.debug('finding throwaway text <%s>', tokens[0].word)
        if tokens[0].word.lower() in bare:
            self.debug('found expected bare word')
            del tokens[0]
            return True
        if tokens[0].word.lower() in with_dot:
            self.debug('found word with following dot')
            del tokens[0]
            remove_leading_word(tokens, frozenset({'.'}))
            return True
        self.debug('no match')
        return False

    def try_num(self, tokens):
        """
        Try to extract a number from the stream. It may be optionally preceded
        by a period (without spaces).
        """
        self.debug('finding law number <%s>', tokens[0].word)
        if DOT_NUM_RE.match(tokens[0].word):
            retval = tokens[0].word.lstrip('.')
            del tokens[0]
            self.debug('Found match for number <%s>', retval)
            return retval
        return None

    def try_extract_law(self, future):
        """
        Given input tokens in future, try to extract a law reference. If there
        are less than 4 tokens or there is no slash, bail immediately since
        there can not be one.
        """
        self.debug('Starting parse')
        if len(future) < 4 or not future.has_word(u'/'):
            return None
        tokens = list(future)
        if not tokens[-1].word:
            tokens[-1].word = ""

        ent = LawEntity()

        ent.set_attr('paragraph', self.try_para(tokens))
        ent.set_attr('section', self.try_sect(tokens))
        ent.set_attr('letter', self.try_letter(tokens))

        self.try_dummy(tokens, self.data['law_word'], self.data['law_abbr'])
        self.try_dummy(tokens, self.data['number_word'],
                       self.data['number_abbr'])

        ent.set_attr('number', self.try_num(tokens))
        if not remove_leading_word(tokens, self.data['dashes']):
            self.debug('Separator is missing')
            return None

        ent.set_attr('collection', self.try_num(tokens))
        if not ent.is_complete():
            self.debug('Reference is not complete')
            return None

        if not self.try_dummy(tokens, self.data['coll_word'],
                              self.data['coll_abbr']):
            self.debug('Collection word is missing')
            return None

        self.debug('Everything ok')
        stripped = len(future) - len(tokens)
        self.debug('Removed %d tokens', stripped)
        text = future.popmany(stripped)
        ent.word = "".join([unicode(t) for t in text]).lstrip()
        ent.whitespace = text[0].whitespace
        ent.set_position(text[0].position)
        return ent

    def run(self, inp):
        """
        Process stream of tokens, replacing some tokens with LawEntities.
        """
        def func(_, f):
            """Helper function that catches exceptions."""
            try:
                return self.try_extract_law(f)
            except IndexError as err:
                self.warning(err)
                return None
        for t in run_helper(inp, LIMIT, 0, func):
            yield t

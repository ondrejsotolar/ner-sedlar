#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module implements detectors for common patters.

NOTE: most functions in this module expect the first token in input to match
the FLOAT_RE regex. This check is done from `try_extract_pattern()`.
"""

from utils import run_helper, load_yaml, join_tokens
import detectors.base as ner
import re
import tokenizer as regexes
from Token import Token


FLOAT = ur'(?:\d+(?:[,.]\d+)?)'
FLOAT_RE = re.compile(FLOAT)

DASHES = frozenset([u'-', u'–', u'—'])

LIMIT = 10


class PatternEntity(ner.NamedEntity):
    """Object representing a pattern entity."""
    def __init__(self, word, typ=None, position=None, whitespace=None):
        super(PatternEntity, self).__init__(word, None, typ, None)
        self.set_src('PatternNer')
        self.set_position(position)
        self.whitespace = whitespace
        self.should_tag = False
        self.weight = 2


def build_entity(future, n, typ):
    """Create a pattern entity of type `typ` from `n` tokens."""
    tokens = future.popmany(n)
    whitespace, text = join_tokens(tokens)
    return PatternEntity(text, typ, tokens[0].position, whitespace)


class PatternDetector(ner.Detector):
    """
    This class implements a detector of various patterns.
    """

    def __init__(self, pattern_file, numeric_file):
        super(PatternDetector, self).__init__('Detect patterns')
        self.patterns = load_yaml(pattern_file)
        self.numerics = self.prepare_data(load_yaml(numeric_file,
                                                    to_sets=False))

        self.pat_funcs = [
            lambda f: self.try_by_type(f, Token.EMAIL, 'Aemail'),
            lambda f: self.try_by_type(f, Token.URL, 'Aurl'),
            lambda f: self.try_by_type(f, Token.IP_ADDRESS, 'Anetaddress'),
            lambda f: self.try_by_type(f, Token.ISBN, 'Anumber BISBN'),
            lambda f: self.try_by_type(f, Token.PHONE_NUM, 'Anumber Bphone'),
            lambda f: self.try_by_type(f, Token.COORDINATES,
                                       'Anumber Bcoordinatess'),
            lambda f: self.try_by_type(f, Token.RATIO, 'Anumber Bratio'),
            self.try_year_span,
            self.try_time,
            self.try_date]

        self.measurements = [(self.patterns['currency'], 'Cprice'),
                             (self.patterns['percent'], 'Anumber Bpercent'),
                             (self.patterns['degree'], 'Anumber Bdegree')]

        self.year_word_re = re.compile(ur'ro[ck]..?')

    def try_number_with(self, future, follows, typ):
        """Look for number followed by one word from the set `follows`."""
        self.debug('Trying number with %s', typ)
        if len(future) >= 2 and future[1].word.lower() in follows:
            self.debug('MATCH')
            return build_entity(future, 2, typ)
        return None

    def try_by_type(self, future, expected, typ):
        """If first word matches the regex, it is an entity of given type."""
        self.debug('Trying as %s', typ)
        if future[0].typ == expected:
            return build_entity(future, 1, typ)
        self.debug('try_by_type: no match')
        return None

    def try_time(self, future):
        """Look for time specification."""
        self.debug('Trying time')
        ent = self.try_by_type(future, Token.TIME, 'Chours Aevent')
        if ent and future[0].word == u'hodin':
            ent.word += unicode(future[0])
            next(future)
        return ent

    def prepare_data(self, structure):
        """
        Prepare data loaded from file for use. Add prefixes to units and
        convert lists into sets.
        """
        results = []
        for data in structure:
            pf1 = self.patterns['len_prefixes']
            pf2 = self.patterns['len_prefixes_short']
            if data.get('binary', False):
                pf1 = self.patterns['bin_prefixes']
                pf2 = self.patterns['bin_prefixes_short']

            units = set([p + u for p in pf1 | set(['']) for u in data['long']])
            units_short = set([p + u for p in pf2 | set([''])
                               for u in data['short']])
            data['long'] = units
            data['short'] = units_short
            results.append(data)
        return results

    def try_year_span(self, future):
        """Try to find a year span."""
        if len(future) < 3:
            return None
        if (regexes.YEAR_RE.match(future[0].word) and
                future[1].word in {u'-', u'–', u'—'} and
                regexes.YEAR_RE.match(future[2].word)):
            self.debug('Found year span')
            return build_entity(future, 3, 'Aevent Bperiod')
        return None

    def try_day_mon_year(self, future):
        """Try to detect date in format `DAY. MONTH. YEAR`."""
        if (len(future) >= 5 and future[1].word == u'.' and
                future[3].word == u'.'):
            self.debug('got to checking date')
            day, mon, year = [future[i] for i in range(0, 5, 2)]
            date_str = '%s.%s.%s' % (day.word, mon.word, year.word)
            if regexes.DATE_RE.match(date_str):
                return build_entity(future, 5, 'Aevent Bdate')
        if (len(future) >= 4 and future[1].word == '.' and
                future[2].word.lower() in self.patterns['months'] and
                regexes.YEAR_RE.match(future[3].word)):
            try:
                day = int(future[0].word)
                if day <= 31:
                    return build_entity(future, 4, 'Aevent Bdate')
            except ValueError:
                pass
        return None

    def try_day_mon(self, future):
        """Try to detect date in format `DAY . MONTH .`."""
        self.debug('Trying Day Month scheme')
        if (len(future) >= 4 and future[1].word == '.' and
                future[3].word == '.'):
            day, mon = future[0].word, future[2].word
            date_str = '%s.%s.2000' % (day, mon)
            self.debug('Formatted [%s]', date_str)
            if regexes.DATE_RE.match(date_str):
                return build_entity(future, 4, 'Aevent Bdate')
        if (len(future) >= 3 and future[1].word == '.' and
                future[2].word.lower() in self.patterns['months']):
            try:
                day = int(future[0].word)
                if day <= 31:
                    return build_entity(future, 3, 'Aevent Bdate')
            except ValueError:
                pass
        return None

    def try_date(self, future):
        """
        There are basically four ways dates can be recognized: if written
        without spaces with only numbers, they are tokenized nicely; second way
        is them written with spaces with numbers only; third is with month as a
        word (this has optional year specification). Fourth way is a month as
        word followed by year.

        Month abbreviations are not handled at the time.
        """
        ent = self.try_by_type(future, Token.DATE, 'Aevent Bdate')
        if ent:
            return ent

        ent = self.try_day_mon_year(future)
        if ent:
            self.debug('Found DAY-MONTH-YEAR scheme')
            return ent

        ent = self.try_day_mon(future)
        if ent:
            self.debug('Found DAY-MONTH scheme')
            return ent

        if (len(future) >= 3 and
                regexes.DAY_RE.match(future[0].word) and
                future[1].word == u'.' and
                future[2].word in self.patterns['months']):
            self.debug('Month may be a word')

            length = 3
            if len(future) >= 4 and regexes.YEAR_RE.match(future[3].word):
                length = 4
                self.debug('There is a year')

            return build_entity(future, length, 'Aevent Bdate')
        elif (len(future) >= 2 and
              future[0].word.lower() in self.patterns['months'] and
              regexes.YEAR_RE.match(future[1].word)):
            self.debug('Trying MONTH YEAR')
            return build_entity(future, 2, 'Aevent Bdate')

        self.debug('No match')
        return None

    def try_units(self, future, data):
        """
        Look for number followed by units.
        Arguments:
          data: dict with following keys
              long: set of long unit names
              short: set of unit abbreviations
              class: actual type of the PatternEntity that should be found
              binary: optional, whether to use binary prefixes
        """
        self.debug('Trying units %s', data['class'])
        if len(future) >= 2:
            idx = 1
            prefixes = self.patterns['num_prefixes']
            if len(future) >= 3 and future[idx].word.lower() in prefixes:
                idx += 1

            word = future[idx].word
            if word.lower() in data['long'] or word in data['short']:
                return build_entity(future, idx + 1,
                                    data['class'] + ' Cmeasurement')

        return None

    def try_generic_number(self, future):
        """
        Look for number that is followed by a word specifying amount.
        """
        prefixes = self.patterns['num_prefixes']
        if len(future) >= 2 and future[1].word.lower() in prefixes:
            return build_entity(future, 2, 'Anumber')

    def has_year_word(self, history):
        """Check if there is a year word in given history."""
        for i in history:
            if self.year_word_re.match(i.word):
                return True
        return False

    def try_year(self, history, future):
        """
        Look for a number that may signify a year. The number must be three or
        four digits long and there must be a "rok*" word somewhere close.
        """
        if not regexes.YEAR_RE.match(future[0].word):
            self.debug('Not a possible year')
            return None
        if not self.has_year_word(history):
            self.debug('Missing year context word')
            return None
        return build_entity(future, 1, 'Aevent Byear')

    def try_single_year(self, future):
        """Look for a number that may be a year."""
        if len(future) >= 1 and regexes.YEAR_RE.match(future[0].word):
            self.debug('Found a single year')
            return build_entity(future, 1, 'Aevent Byear')
        return None

    def try_extract_pattern(self, history, future):
        """
        Try to extract a pattern entity. E-mail, URL and IP are always tried as
        they are only one token long. The rest is tried only if the input
        starts with a number.
        """
        self.debug('Starting extraction <%s>', future[0].word)

        if not future[-1].word:
            future[-1].word = ''

        for f in self.pat_funcs:
            ent = f(future)
            if ent:
                return ent

        if not FLOAT_RE.match(future[0].word):
            return None

        for (words, typ) in self.measurements:
            ent = self.try_number_with(future, words, typ)
            if ent:
                return ent

        ent = self.try_year(history, future)
        if ent:
            return ent

        for it in self.numerics:
            ent = self.try_units(future, it)
            if ent:
                return ent

        return self.try_single_year(future) or self.try_generic_number(future)

    def run(self, inp):
        """
        Process stream of tokens, replacing some tokens with PatternEntities.
        """
        for t in run_helper(inp, LIMIT, 10, self.try_extract_pattern):
            yield t

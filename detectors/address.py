#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Detector of addresses in Czech Republic.
"""

from WLTStorage import WLTStorage
from WordSet import WordSet
import detectors.base as ner
from utils import run_helper, join_tokens
from Token import Token
import re

LIMIT = 20
STREET_LIMIT = 7
TOWN_LIMIT = 5


class AddressEntity(ner.NamedEntity):
    """Object representing an address."""
    def __init__(self, text, position=None):
        ner.NamedEntity.__init__(self, text, None, "CAddress", None)
        self.set_position(position)
        self.set_src("AddrNer")
        self.should_tag = False


def is_number(s):
    """Test whether a string contains only digits."""
    return all([c.isdigit() for c in s])


class AddressDetector(ner.Detector):
    """This class implements a detector of Czech addresses."""

    def __init__(self, streets_file, towns_file, country_file):
        super(AddressDetector, self).__init__('Detect addresses')
        self.streets = WLTStorage(streets_file)
        self.towns = WLTStorage(towns_file)
        self.countries = WordSet(country_file)

    def try_street(self, future, idx):
        """
        Try to extract street or town from token stream. The longest option
        will be taken.
        """
        current = []
        longest = 0
        for i in range(min(STREET_LIMIT, len(future) - idx)):
            current.append(future[idx + i])
            i += 1
            _, word = join_tokens(current)
            self.debug('Testing <%s>', word)
            # If there is a period without any spaces around it, add one
            word = re.sub(r'(?<!\s)\.(?!\s)', '. ', word)
            if word in self.streets or word in self.towns:
                longest = i
                self.debug('Found street <%s>', word)
        if future[longest].word == '.':
            longest += 1
        return (longest > 0, idx + longest)

    def try_town(self, future, idx):
        """
        Try to extract town name from stream. It will take the longest
        available name.
        """
        current = []
        longest = 0
        self.debug('Finding town')
        for i in range(min(TOWN_LIMIT, len(future) - idx)):
            current.append(future[idx + i])
            i += 1
            _, word = join_tokens(current)
            self.debug('Testing <%s>', word)
            if word in self.towns:
                longest = i
                self.debug('Found town <%s>', word)
        return (longest > 0, idx + longest)

    def try_country(self, future, idx):
        """
        Try to determine if future starts with any country listed in data file.
        """
        for country in self.countries:
            self.debug('Trying country <%s>', country)
            tokens = country.split(' ')
            if len(future) < len(tokens):
                break
            i = 0
            found = True
            for word in tokens:
                if future[idx + i].word.lower() != word.lower():
                    found = False
                    break
                i += 1
            if found:
                return True, idx + i
        return False, idx

    def try_house_number(self, future, ent, idx):
        """
        Try to recognise house number, optionally with orientation number.
        """
        if not is_number(future[idx].word):
            return False, idx
        if future[idx + 1].word == '/' and is_number(future[idx + 2].word):
            _, num = join_tokens(future[idx:idx + 3])
            ent.attrs['ner:addr:house'] = num
            return True, idx + 3
        self.debug('Found house number <%s>', future[idx].word)
        ent.attrs['ner:addr:house'] = future[idx].word
        return True, idx + 1

    def try_extract(self, _, future):
        """Try to find an address."""
        if not (future[0].word[0].isupper() or future[0].word[0].isdigit()):
            return None

        ent = AddressEntity('', future[0].position)

        ok, idx = self.try_street(future, 0)
        if not ok:
            self.debug('Abort: no street')
            return None
        ent.attrs['ner:addr:street'] = join_tokens(future[:idx])[1]

        ok, idx = self.try_house_number(future, ent, idx)
        if not ok:
            self.debug('Missing house number')
            return None

        if future[idx].word == ',':
            self.debug('Found optional comma')
            idx += 1

        if future[idx].typ == Token.ZIP_CODE:
            ent.attrs['ner:addr:zip_code'] = future[idx].word
            idx += 1
        else:
            self.debug('Missing zip code')

        old_idx = idx
        ok, idx = self.try_town(future, idx)
        if not ok:
            self.debug('Abort: no town')
            return None
        ent.attrs['ner:addr:town'] = join_tokens(future[old_idx:idx])[1]

        found_comma = False
        if future[idx].word == ',':
            self.debug('Found comma after town')
            found_comma = True
            idx += 1

        old_idx = idx
        ok, idx = self.try_country(future, idx)
        if not ok:
            self.debug('No country')
            if found_comma:
                idx -= 1
        else:
            ent.attrs['ner:addr:country'] = join_tokens(future[old_idx:idx])[1]

        tokens = future.popmany(idx)
        ent.whitespace, ent.word = join_tokens(tokens)
        return ent

    def run(self, inp):
        """Runner for this detector."""
        for t in run_helper(inp, LIMIT, 0, self.try_extract):
            yield t

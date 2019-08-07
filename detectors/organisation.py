#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module contains heuristics for extraction of organisation names.
"""

import detectors.base as ner
from utils import run_helper, join_tokens, load_yaml
import Majka


LIMIT = 10


class OrganisationEntity(ner.NamedEntity):
    """Class representing organisation name."""
    def __init__(self, tokens):
        whitespace, text = join_tokens(tokens)
        ner.NamedEntity.__init__(self, text, None, 'COrganisation', None)
        self.whitespace = whitespace
        self.set_position(tokens[0].position)
        self.set_src("OrganisationNer")


class OrganisationDetector(ner.Detector):
    """Class implementing heuristics for organisation name detection."""

    def __init__(self, data_file):
        ner.Detector.__init__(self, 'Detect organisations')
        self.majka = Majka.Majka()
        self.data = load_yaml(data_file)

    def is_pos(self, word, pos):
        """
        Check if `word` is actually has given part-of-speech tag. The last
        argument should be of type `kX`.
        """
        self.debug('Testing <%s> for %s', word, pos)
        for (_, tag) in self.majka.get_lemma_tag(word):
            if pos in tag:
                return True
        return False

    def take_after_prep(self, future):
        """
        Assuming future starts with an abbreviations followed by preposition,
        take a name phrase following it. The name phrase can start with an
        arbitrary number of adjectives followed by a single noun.

        Returns number of tokens the phrase consists of. The preposition is
        included. On failure (bad noun phrase) returns -1.
        """
        taken = 1
        while self.is_pos(future[taken + 1].word.lower(), 'k2'):
            self.debug('Taking adjective <%s>', future[taken + 1].word)
            taken += 1
        if self.is_pos(future[taken + 1].word.lower(), 'k1'):
            self.debug('Finishing nount <%s>', future[taken + 1].word)
            return taken + 1
        return -1

    def try_take(self, future):
        """
        Assuming the future starts with something resembling an abbreviation or
        an organisation generic word, take rest of the organisation name. If
        the abbreviation is followed by a preposition followed by a noun
        phrase, it is accepted. The other option is abbreviation followed by a
        sequence of capitalized words.
        """
        self.debug('Trying after abbr detection from <%s>', future[0].word)
        taken = 0
        if future[1].word.lower() in self.data['prepositions']:
            self.debug('Starts with preposition')
            taken = self.take_after_prep(future)
            if taken < 0:
                self.debug('Ugly words follow, abort')
                return None
        else:
            self.debug('Taking uppercase')
            while future[taken + 1].word[0].isupper():
                taken += 1
            if (self.is_pos(future[taken].word, 'k2') and
                    self.is_pos(future[taken + 1].word, 'k1')):
                self.debug('Adding noun after adjective')
                taken += 1

        if taken >= 1:
            return OrganisationEntity(future.popmany(taken + 1))
        return None

    def take_until(self, future, abbr):
        """Take company name from current position until the `abbr` token.
        The method can abort quickly if the name would contain uppercase word
        following a lowercase one.
        """
        idx = 0
        seen_lower = False
        while idx < len(future) and future[idx].word.lower() != abbr:
            if not future[idx].word:
                self.debug('Abort due to missing word')
                return None
            if seen_lower and future[idx].word[0].isupper():
                self.debug('Abort due to lowercase - uppercase mismatch')
                return None
            if future[idx].word[0].islower():
                seen_lower = True
            idx += 1
        if idx == len(future):
            self.debug('No match')
            return None

        self.debug('Found')
        return OrganisationEntity(future.popmany(idx + 1))

    def try_extract(self, _, future):
        """Try extract organisation name starting at current position."""
        leading = future[0].word

        if not leading[0].isupper():
            return None

        if (all(c.isupper() for c in leading) and
                len(leading) < 4 and
                len(leading) > 1):
            self.debug('Trying with abbreviation')
            ent = self.try_take(future)
            if ent:
                return ent

        if leading.lower() in self.data['names']:
            self.debug('Trying with organisation noun')
            ent = self.try_take(future)
            if ent:
                return ent

        for abbr in self.data['types']:
            self.debug('Trying with suffix %s', abbr)
            ent = self.take_until(future, abbr)
            if ent:
                return ent

        return None

    def run(self, inp):
        """Runner for this detector."""
        for t in run_helper(inp, LIMIT, 0, self.try_extract):
            yield t

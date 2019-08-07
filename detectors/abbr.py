#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Abbreviation detection
"""

from collections import deque
from LazyDeque import LazyDeque
from WordSet import WordSet
import detectors.base as ner
import re

LIMIT = 20

INTERPUNCTION = frozenset(u', . ? !'.split())
DASHES = frozenset(u'- – —'.split())
PARENTHESES = frozenset(['(', ')', '[', ']', '{', '}'])


class AbbrEntity(ner.NamedEntity):
    """Object describing an abbreviation."""
    def __init__(self, word, explanation, whitespace=None, position=None):
        ner.NamedEntity.__init__(self, word, None, "CAbbr", None)
        self.set_position(position)
        self.whitespace = whitespace
        self.attrs['ner:abbr:explanation'] = explanation
        self.set_src("AbbrNer")
        self.should_tag = False


def mk_abbr(abbr, expl):
    """
    Helper function for creating AbbrEntity from actual abbreviation and the
    explanation.
    """
    expl = ' '.join([x.word for x in expl]) if expl else None
    return AbbrEntity(abbr.word, expl,
                      whitespace=abbr.whitespace, position=abbr.position)


class AbbrDetector(ner.Detector):
    """
    This class implements detector of abbreviations. It first looks for
    candidates that have at least two capital letters. Then it looks in local
    context for a token sequence that could be an explanation of the
    abbreviation, i.e. its initials form the abbreviation and it is separated
    by either parentheses or a dash.
    """

    def __init__(self, ignore_list):
        super(AbbrDetector, self).__init__('Detect abbreviations')
        self.ignored_words = WordSet(ignore_list, filt=lambda x: x.lower())
        self.cache = set()

    def try_find(self, tokens, abbr):
        """
        Try to find an explanation for abbreviation 'abbr' in word stream
        'tokens'.
        """

        abbr = [c for c in abbr if c not in DASHES and c != '.']
        self.debug('Stripped dashes <%s>', u"".join(abbr))

        i = 0               # Position in abbreviation
        last_ok = False     # Whether last word was skipped
        match = list()
        for word in tokens:
            if not word.word:
                self.debug('Empty word, abort')
                return None
            # Disallow interpunction inside abbr explanation
            if word in INTERPUNCTION:
                self.debug('No interpunction inside explanation')
                return None

            self.debug('Testing <%s>', word.word)

            initial_match = word.word[0].upper() == abbr[i].upper()
            if not initial_match:
                if word.word in self.ignored_words:
                    i -= 1
                else:
                    return list()
            match.append(word)
            last_ok = initial_match
            i += 1
            # Stop if we have enough words
            if i >= len(abbr):
                break

        # If last word of explanation is in ignored words, try to add one more
        # word if the initials match.
        if (match[-1].word in self.ignored_words and len(tokens) > i and
                abbr[-1].upper() == tokens[i].word[0].upper()):
            match.append(tokens[i])

        # Drop last word if it was skipped
        if len(match) > 0 and not last_ok:
            match.pop()

        return match if i >= len(abbr) and match[0] != abbr else None

    def try_match(self, tokens, abbr):
        """Explore the tokens and try to find an explanation for the abbr.

        First, it skips words until it moves to other parentheses context or
        sees a dash. Should it move inside the same context again, it
        immediately exits.

        Returns a list of words forming the explanation or None.
        """
        tok_list = list(tokens)
        should_check = False
        for i in range(0, len(tokens) - len(abbr) + 1):
            self.debug("Going over <%s>", tok_list[i].word)
            if not should_check and (tok_list[i].word in PARENTHESES or
                                     tok_list[i].word in DASHES):
                self.debug("Entered interesting context")
                should_check = True
                continue
            if should_check and tok_list[i] in PARENTHESES:
                self.debug("Left interesting context")
                break
            if not should_check:
                continue
            self.debug("Trying to find explanation")
            match = self.try_find(tok_list[i:], abbr)
            if match:
                return match
        return None

    def run(self, inp):
        """
        Process stream of tokens, replacing some tokens with AbbrEntities.
        """
        history = deque(list(), LIMIT)
        future = LazyDeque(inp, LIMIT)

        while len(future) > 0:
            token = next(future)
            to_yield = token

            if not token.word:
                yield token
                return

            if len(re.findall(ur"[A-ZÁČĎÉÍNÓŘŠŤÚ]", token.word)) >= 2:
                self.debug('Trying backward match for <%s>', token.word)
                expl = self.try_match(history, token.word[::-1])
                if expl:
                    expl = reversed(expl)
                if not expl:
                    self.debug('Trying forward match for <%s>', token.word)
                    expl = self.try_match(future, token.word)
                if expl:
                    to_yield = mk_abbr(token, expl)
                    self.cache.add(token.word)
                elif token.word in self.cache:
                    self.debug('Found previously mentioned abbreviation')
                    to_yield = mk_abbr(token, None)

            yield to_yield

            history.appendleft(token)

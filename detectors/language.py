#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Module detecting runs of foreign language words in the text.
"""

from WLTStorage import WLTStorage
import detectors.base as ner
from utils import run_helper, join_tokens
from Majka import Majka

import os

LIMIT = 4


class LanguageEntity(ner.NamedEntity):
    """Object describing a phrase named entity."""
    def __init__(self, text, lang, position=None):
        ner.NamedEntity.__init__(self, text, None, 'CLanguage D'+lang, None)
        self.set_position(position)
        self.set_src("LanguageNer")


class LanguageDetector(ner.Detector):
    """
    Detector of phrases in other languages.

    It uses a list of words for each detected language. The constructor needs
    one argument, the directory with word lists. The directory should contain
    the lists compiled as tries, with file names language.trie. Any file with
    different extension will be ignored and all tries will be considered as
    word lists.
    """
    def __init__(self, lang_dir):
        ner.Detector.__init__(self, 'Detect non-Czech phrases')
        self.majka = Majka()

        self.words = {}
        for lang in os.listdir(lang_dir):
            if not lang.endswith('.trie'):
                continue
            self.words[lang.split('.')[0]] = WLTStorage(lang_dir + '/' + lang)

    def is_foreign_word(self, lang, word):
        """Return True if word is a possible word in language lang."""
        if word.lower() not in self.words[lang]:
            self.debug('Not in a dictionary, abort...')
            return False
        if word[0].isupper():
            self.debug('Starts with uppercase, accept')
            return True
        info = self.majka.get_lemma_tag(word.lower())
        self.debug('Check majka: %d', len(info))
        return len(info) == 0

    def try_lang(self, lang, future):
        """Try to detect a phrase in given language."""
        idx = 0
        max_idx = len(future) - 1
        while idx < max_idx and self.is_foreign_word(lang, future[idx].word):
            self.debug('Found possibly foreign word <%s>', future[idx].word)
            idx += 1
        return idx

    def try_extract(self, _, future):
        """Check if future starts with non-Czech phrase."""
        if not future[0].word[0].isalpha():
            return None

        max_len = 0
        max_lang = None

        for lang in self.words.keys():
            self.debug('Trying %s starting from %s', lang, future[0].word)
            length = self.try_lang(lang, future)
            if length > max_len:
                max_len = length
                max_lang = lang

        if max_len < 2:
            self.debug('Ignore short case')
            return None
        if max([len(future[i].word) for i in range(0, max_len)]) < LIMIT:
            self.debug('Too short words')
            return None

        tokens = future.popmany(max_len)

        whitespace, text = join_tokens(tokens)

        ent = LanguageEntity(text, max_lang, tokens[0].position)
        ent.whitespace = whitespace
        return ent

    def run(self, inp):
        """Runner for this detector."""
        for t in run_helper(inp, 10, 0, self.try_extract):
            yield t

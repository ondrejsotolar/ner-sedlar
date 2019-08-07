#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Persons' name detection
"""

from WLTStorage import WLTStorage
import detectors.base as ner
from utils import (run_helper, is_sentence_start, normalize_caps, load_yaml,
                   join_tokens)
from Majka import Majka

LIMIT = 20


def most_frequent(iterable):
    """Find most frequent item in the iterable."""
    counts = dict()
    for item in iterable:
        counts[item] = counts.get(item, 0) + 1
    return max(counts, key=counts.get)


class NameEntity(ner.NamedEntity):
    """Object describing a person's name."""
    def __init__(self):
        ner.NamedEntity.__init__(self, "", None, "CName", None)
        self.possible_tags = set()
        self.set_src("PersonNer")
        self.lemmas = []
        self.have_title = False
        self.words = []

    def append(self, token, lemma_tags=frozenset()):
        """
        Add another word to the name entity. This method also updates the set
        of possible tags (if given).
        """
        tags = set([lt[1] for lt in lemma_tags])
        self.lemmas.append(lemma_tags)
        self.words.append(token)
        if len(self.words) == 1 or not self.possible_tags:
            self.possible_tags = tags
        else:
            self.possible_tags.intersection_update(tags)

    def append_title(self, token):
        """Append title (with no tags or lemmas)."""
        self.append(token)
        self.have_title = True

    def compatible(self, tags):
        """
        Check whether a word with given tags can be part of this name.
        """
        return len(self.possible_tags) == 0 or self.possible_tags & tags

    def get_word(self):
        """Return actual current name."""
        return join_tokens(self.words)[1]

    def finalize(self, is_improper):
        """All names have been added, finalize remaining attributes."""
        self.attrs['tag'] = '|'.join(self.possible_tags)

        tok_num = len(self.words)
        while is_improper(self.words[tok_num - 1].word):
            tok_num -= 1
        self.words = self.words[:tok_num]

        self.set_position(self.words[0].position)
        self.whitespace, self.word = join_tokens(self.words)

        lemma_parts = []
        for name_part in self.lemmas:
            opts = [lt[0] for lt in name_part if lt[1] in self.possible_tags]
            if len(opts) > 0:
                lemma_parts.append(most_frequent(opts))
        self.attrs['lemma'] = ' '.join(lemma_parts)


def is_initial(word):
    """Check if a word may be an initial of a person name."""
    return len(word.rstrip(u'.')) == 1 and word[0].isupper()


class NameDetector(ner.Detector):
    """
    This class implements a detector of personal names. It is based on a list
    of first and last names as well as a list of possible titles in front of
    names.
    """

    def __init__(self, first_names, last_names, data_file):
        super(NameDetector, self).__init__('Detect personal names')
        self.first_names = WLTStorage(first_names)
        self.last_names = WLTStorage(last_names)
        self.data = load_yaml(data_file)
        self.majka = Majka()

    def get_lt(self, w):
        """Get lemmata and tags for a word."""
        if all(c.isupper() for c in w):
            w = normalize_caps(w)
        result = set()
        if w in self.first_names:
            result |= self.first_names[w]
        if w in self.last_names:
            result |= self.last_names[w]
        return result

    def is_title(self, word):
        """Check if a word may be a title."""
        return word.rstrip(u'.') in self.data['titles_before']

    def is_title_after(self, word):
        """Check if a word is a title written after name."""
        return word.rstrip(u'.') in self.data['titles_after']

    def try_after_title(self, future, idx, name):
        """
        Try to extract titles following a name. Append found titles to `name`
        and return updated `idx`.
        """
        if future[idx].word == ',':
            self.debug('Found possible after title')
            comma = True
            idx += 1
            while self.is_title_after(future[idx].word):
                self.debug('Adding title after <%s>', future[idx].word)
                if comma:
                    name.append_title(future[idx-1])
                    comma = False
                name.append_title(future[idx])
                idx += 1
                if future[idx].word == '.':
                    self.debug('Skipping . after title')
                    name.append_title(future[idx])
                    idx += 1
                if future[idx].word == ',':
                    self.debug('Skipping , after title')
                    comma = True
                    idx += 1
            if comma:
                idx -= 1
        elif future[idx].word.lower() in self.data['age_info']:
            self.debug('Found age specifier <%s>', future[idx].word)
            name.append_title(future[idx])
            idx += 1
            if future[idx].word == '.':
                self.debug('Skipping . after age spec')
                name.append_title(future[idx])
                idx += 1
        return idx

    def try_titles(self, future, name):
        """
        Try to find titles in front of name and initials. Found titles are
        appended to `name`. Return number of tokens consumed.
        """
        idx = 0
        while is_initial(future[idx].word) or self.is_title(future[idx].word):
            self.debug('Adding title <%s>', future[idx])
            name.append_title(future[idx])
            idx += 1
            if future[idx].word == '.':
                self.debug('Skipping token <.> after title')
                name.append_title(future[idx])
                idx += 1

        return idx

    def try_extract_name(self, history, future):
        """
        Try to extract name from start of the stream. Return value is
        NameEntity if name is found, None otherwise.

        Input stream is modified only if name was found. In such case all
        tokens that are part of the name are extracted from it.
        """
        self.debug('Starting word <%s>', future[0])

        name = NameEntity()
        name_count = 0

        idx = self.try_titles(future, name)

        while True:
            token = future[idx]
            self.debug('Inspecting token <%s>', token.word)

            if token.word in self.data['prepositions']:
                self.debug('Found preposition <%s>', token.word)
                name.append_title(token)
                idx += 1
                continue

            if len(token.word) == 0 or not token.word[0].isupper():
                self.debug('Does not start with uppercase')
                break

            lemmas_tags = self.get_lt(token.word)
            if lemmas_tags:
                tags = set([lt[1] for lt in lemmas_tags])

                self.debug('have name <%s>', token.word)

                if name.compatible(tags):
                    self.debug('Name compatible')
                    name.append(token, lemma_tags=lemmas_tags)
                    name_count += 1
                    idx += 1
                else:
                    self.debug('Name incompatible')
                    break
            else:
                self.debug('Not a name')
                break

        if name_count == 0:
            self.debug('Found no name')
            return None

        idx = self.try_after_title(future, idx, name)

        if name_count == 1 and not name.have_title:
            if is_sentence_start(history):
                self.debug('Ignoring short name at sentence start')
                return None
            morph_info = self.majka.get_lemma_tag(name.get_word().lower())
            if morph_info:
                self.debug('Discarding short name <%s> known to majka',
                           name.word.lower())
                return None

        self.debug("Collected name %s", name.get_word())
        name.finalize(lambda w: w in self.data['prepositions'])
        future.popmany(idx)
        return name

    def run(self, inp):
        """
        Process stream of tokens, replacing some tokens with NameEntities.
        """
        def func(h, f):
            """Helper function that catches exceptions."""
            try:
                return self.try_extract_name(h, f)
            except IndexError:
                return None
        for t in run_helper(inp, LIMIT, 2, func):
            yield t

#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Detector of phrase named entitites. It detects things with wikipedia page,
films, goods and books.
"""

from WLTStorage import WLTStorage
from Majka import Majka
import detectors.base as ner
from utils import run_helper, join_tokens, is_sentence_start, normalize_caps
from Token import Token

LIMIT = 10
# Maximum number of categories considered before declaring entity ambiguous
CATEGORIES_LIMIT = 15

PUNCTUATION = frozenset(u', ( ) [ ] { }'.split())
FORBIDDEN_COMBOS = [({'telefon', 'tel', 'fax'}, Token.PHONE_NUM),
                    ({'e-mail', 'email'}, Token.EMAIL),
                    ({u'souřadnice'}, Token.COORDINATES)]


class PhraseEntity(ner.NamedEntity):
    """Object describing a phrase named entity."""
    def __init__(self, text, position=None):
        ner.NamedEntity.__init__(self, text, None, "CPhrase", None)
        self.set_position(position)
        self.set_src("PhraseNer")

    def add_categories(self, cats):
        """Add another category to the type tag."""
        if len(cats) > CATEGORIES_LIMIT:
            self.attrs['typ'] += ' Avery_ambiguous'
        elif len(cats) > 0:
            for c in cats:
                self.attrs['typ'] += ' Z' + c


def is_possible_start(word):
    """Entities must start with capital letter or a digit."""
    return word[0].isupper() or word[0].isdigit()


def levenshtein(a, b):
    """Calculates the Levenshtein distance between a and b."""
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a, b = b, a
        n, m = m, n
    current = range(n+1)
    for i in range(1, m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1, n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
    return current[n]


def filter_morph_info(opts):
    """
    Return new list of lemma-tag pairs, such that the tag is a noun.
    """
    return [(lemma, tag) for (lemma, tag) in opts if 'k1' in tag]


def to_join(t):
    """
    Transform token into a form that is amenable to joining. If the token was
    preceded by whitespace, it will be preceded by a single space. Otherwise
    only the token word will be returned.
    """
    return (' ' if t.whitespace else '') + t.word


class PhraseDetector(ner.Detector):
    """
    This class implements a detector of phrases.
    """

    def __init__(self, entry_list_file, categories_file, tuple_file,
                 place_file):
        """
        Arguments:
          entry_list_file: filename of a file with entity list; only entity
                           names
          categories_file: filaname of entity->category mapping
          tuple_file: filename of any_form->lemma of entities
          place_file: whitelist of place names to be accepted as entities
        """
        super(PhraseDetector, self).__init__('Detect phrases')
        self.entries = WLTStorage(entry_list_file)
        self.categories = WLTStorage(categories_file, delimiter='|')
        self.tuples = WLTStorage(tuple_file, delimiter='|')
        self.majka = Majka()
        self.places = WLTStorage(place_file)

    def get_categories(self, sequence):
        """Get all categories associated with a token."""
        self.debug('Finding categories for <%s>', sequence)
        cats = []
        if sequence in self.categories:
            cats.extend(self.categories[sequence])
        if sequence.upper() in self.categories:
            cats.extend(self.categories[sequence.upper()])
        self.debug('Found %r', cats)
        return set(c[0] for c in cats if len(c) > 0)

    def most_similar(self, candidate, options):
        """
        Return the word from options that is the most similar (but not
        containing the string) to the candidate word.
        """
        best = None
        best_dist = 1000
        for lemma in [opt[0] for opt in options if len(opt) > 0]:
            self.debug('Examining lemma <%s>', lemma)
            # candidate is NOT a substring in inflected forms
            if candidate not in lemma:
                dist = levenshtein(candidate, lemma)
                if dist < len(candidate) and dist < best_dist:
                    best = lemma
                    best_dist = dist
        return best or ''

    def find_lemma(self, sequence):
        """Find a lemma for word (or word sequence)."""
        self.debug('Finding inflection for <%s>', sequence)
        lemma = ''
        morpho = filter_morph_info(self.majka.get_lemma_tag(sequence))
        self.debug('Majka returned %r', morpho)
        if morpho:
            lemma = morpho[0][0]
        elif sequence in self.tuples:
            lines = self.tuples[sequence]
            self.debug('Options are %r', lines)
            lemma = self.most_similar(sequence, lines)
            self.debug('Best match is <%s>', lemma)
        return lemma.strip().replace(' ', '_')

    def lookup_sequence(self, sequence):
        """
        Try to find string in dictionary, possibly without capitalization of
        every letter.
        """
        if sequence in self.entries:
            return True
        if normalize_caps(sequence) in self.entries:
            return True
        return sequence.replace(' - ', '-') in self.entries

    def try_extract_entry(self, history, future):
        """
        Try to find a phrase in the future tokens.
        """
        if not is_possible_start(future[0].word):
            return None

        current = []
        last_seq = ''
        longest = 0
        for i in range(0, min(LIMIT, len(future) - 1)):
            current.append(future[i])

            sequence = ''.join([to_join(t) for t in current]).lstrip()
            sequence = sequence.replace(' ,', ',').replace(' .', '.')

            self.debug('current: <%s>', sequence)

            if self.lookup_sequence(sequence):
                longest = i + 1
                last_seq = sequence
                self.debug('Found match of len %d', longest)

        self.debug('Longest match was: %d', longest)
        if not self.check_length(longest, history, future):
            return None

        tokens = future.popmany(longest)

        whitespace, text = join_tokens(tokens)

        ent = PhraseEntity(text, tokens[0].position)
        ent.whitespace = whitespace
        lemma = self.find_lemma(last_seq)
        if lemma:
            ent.attrs['lemma'] = lemma

        ent.add_categories(self.get_categories(last_seq))
        return ent

    def check_tok_type(self, future, tok_type):
        """
        Check if there is a token at the start of the future, only possibly
        preceded by punctuation.
        """
        idx = 0
        while idx < len(future) and future[idx] in {'.', ':'}:
            idx += 1
        self.debug('Skipped %d tokens before checking token type')
        return idx < len(future) and future[idx].typ == tok_type

    def is_known_town(self, morpho):
        """
        Majka knows names of many places. This method checks if the lemma is in
        list of towns.
        """
        for (lemma, _) in morpho:
            if lemma in self.places:
                return True
        return False

    def check_forbidden(self, future):
        """Check if the current word is followed by a forbidden token."""
        for (words, tok_type) in FORBIDDEN_COMBOS:
            if future[0].word.lower() not in words:
                continue
            if not self.check_tok_type(future, tok_type):
                return False
        return True

    def check_morpho(self, future):
        """
        Check if Majka knows the word and handle it. Return True if word is
        entity, False if it is not, and None if indeterminate.
        """
        morpho = self.majka.get_lemma_tag(future[0].word)
        if morpho:      # Only check known words
            if self.is_known_town(morpho):
                return True
            lower = [pair for pair
                     in self.majka.get_lemma_tag(future[0].word.lower())
                     if not pair[0][0].isupper()]
            if len(morpho) > 1 or 'kA' not in morpho[0][1] or lower:
                self.debug('Known word at sentence start -> skip')
                return False
        return None

    def check_one_word(self, history, future):
        """
        Check if found one word entity is acceptable. If the entity would be
        too short, reject it. If it is written in all uppercase, accept it. If
        it is at sentence start and Majka knows it with uppercase capital
        letter as something other than proper name or in all lowercase, reject
        it. If it is a word with following forbidden token, reject it.
        """
        word = future[0].word
        if len(word) == 1:
            self.debug('No one letter entities')
            return False
        elif all(c.isupper() for c in word):
            self.debug('Accept all caps')
            return True
        elif is_sentence_start(history):
            res = self.check_morpho(future)
            if res is not None:
                return res
        elif len(future) > 2:
            return self.check_forbidden(future)
        return True

    def check_length(self, longest, history, future):
        """Check if entity is long enough and nice."""
        if longest == 0:
            self.debug('No possible entity')
            return False
        elif longest == 1:
            return self.check_one_word(history, future)

        only_numbers = True
        length = 0
        for i in range(longest):
            only_numbers &= all([c.isdigit() for c in future[i].word])
            length += len(future[i].word)
        if only_numbers or length < 5:
            self.debug('No short numbers as phrases')
            return False

        return True

    def run(self, inp):
        """Runner for this detector."""
        for t in run_helper(inp, LIMIT, 1, self.try_extract_entry):
            yield t

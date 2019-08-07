#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Useful functions for processing input.
"""

from LazyDeque import LazyDeque
from collections import deque

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


SENTENCE_DELIMITERS = frozenset(u'. ! ? ) ( - – — " \' „ “'.split())


def run_helper(inp, lookahead, lookback, func):
    """
    Helper wrapper that keeps track of history and future. For each interesting
    token, run a given function. Its first argument will be the history, second
    is the future. Current token is the first one in the future.
    """
    future = LazyDeque(inp, lookahead)
    history = deque(list(), lookback)

    while True:
        if len(future) == 0:
            break
        elif len(future) == 1:
            yield next(future)
            break
        res = func(history, future) or next(future)
        yield res
        history.appendleft(res)


def join_tokens(tokens):
    """
    Concatenate tokens to for a string. Returns a pair (whitespace, text),
    where whitespace is what preceded the first token.
    """
    if len(tokens) == 1:
        return tokens[0].whitespace, tokens[0].word
    rest = ''.join([(t.whitespace or '') + t.word for t in tokens[1:]])
    return tokens[0].whitespace, tokens[0].word + rest


def load_yaml(data_file, to_sets=True):
    """Load all data from specified file. If `to_sets` is True (default), all
    values associated with top level keys will be converted to sets.
    """
    with open(data_file, 'r') as f:
        data = yaml.load(f, Loader=Loader)
        if to_sets:
            for (k, v) in data.iteritems():
                data[k] = set(v)
        return data


def is_sentence_start(history):
    """Check whether the history indicates start of sentence."""
    return len(history) == 0 or history[0].word in SENTENCE_DELIMITERS


def is_all_caps(string):
    """Return True if all string is written in with only capital letters."""
    return all(x.isupper() for x in string if x.isalpha())


def normalize_caps(string):
    """
    If string is written in only capital letters, normalize it so that each
    word starts with a single capital. Otherwise do nothing.
    """
    if is_all_caps(string):
        result = ""
        for word in string.split(' '):
            result += word[0] + ''.join([x.lower() for x in word[1:]])
            result += " "
        return unicode(result.rstrip(' '))
    return string
